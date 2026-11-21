#!/usr/bin/env python3
"""Read-only Moodle client used by the read-moodle-skill commands for Claude Code.

It talks to Moodle's web-service API (the same one the official Moodle app uses).
Key: macOS Keychain item service "read-moodle-skill", account "token" (saved by MoodleKey.app).
HTTP goes through /usr/bin/curl, because Cloudflare in front of some Moodle sites blocks Python's urllib.
Only functions whose names say they read (get/search/list) are allowed; nothing submits or posts.

  moodle.py login                  open the Moodle sign-in that gives this tool its key
  moodle.py doctor                 check everything is set up
  moodle.py courses
  moodle.py today                  what's due, this week's sessions and readings, new announcements
  moodle.py deadlines [DAYS]
  moodle.py assignments [MODULE]
  moodle.py brief QUERY            (assignment name words, or a cmid)
  moodle.py grades [MODULE]
  moodle.py module MODULE [SECTION_WORDS]
  moodle.py file URL               (download a pluginfile URL; prints the local path)
  moodle.py call WSFUNCTION [key=value ...]   (raw read-only call, JSON out)
"""
import html, json, os, re, secrets, subprocess, sys, time
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse
from zoneinfo import ZoneInfo

HOME = Path(__file__).resolve().parent
FILES = HOME / "files"
CONFIG_FILE = HOME / "config.json"
DEFAULTS = {"site": "https://moodle.ucl.ac.uk", "timezone": "Europe/London", "modules": [],
            "terms": [], "weeks_per_term": 11, "reading_week": 6,
            "notion_today_page": None, "notion_timeline_db": None}


def load_config():
    cfg = dict(DEFAULTS)
    try:
        cfg.update(json.loads(CONFIG_FILE.read_text()))
    except FileNotFoundError:
        pass
    except ValueError as e:
        sys.exit(f"ERROR: {CONFIG_FILE} is not valid JSON ({e}). Fix it or copy config.example.json over it.")
    return cfg


CONFIG = load_config()
SITE = CONFIG["site"].rstrip("/")
REST = SITE + "/webservice/rest/server.php"
LONDON = ZoneInfo(CONFIG["timezone"])   # the name is historical: it is the configured time zone
KEYCHAIN = os.environ.get("READ_MOODLE_KEYCHAIN", "read-moodle-skill")   # override is for testing only
README = "https://github.com/Forrest404/read-moodle-skill#readme"
READ_ONLY = re.compile(r"(^|_)(get|search|list)(_|$)")
# Any of these as a whole word in the function name means it changes something: refuse it.
BLOCKED = re.compile(r"(^|_)(save|submit|update|delete|add|create|set|send|post|view|mark|lock|unlock|revert|start|"
                     r"process|copy|move|remove|edit|toggle|record|import|upload)(_|$)", re.I)


class MoodleError(Exception):
    pass


def token():
    try:
        return subprocess.run(["/usr/bin/security", "find-generic-password", "-s", KEYCHAIN, "-a", "token", "-w"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except subprocess.CalledProcessError:
        raise MoodleError("No Moodle key yet. Run `python3 -I moodle.py login` and click Open when the browser asks.")


TOKEN = None


def tok():
    global TOKEN
    if TOKEN is None:
        TOKEN = token()
    return TOKEN


def redact(s):
    return s.replace(TOKEN, "<KEY>") if TOKEN else s


def flatten(prefix, value, out):
    if isinstance(value, dict):
        for k, v in value.items():
            flatten(f"{prefix}[{k}]" if prefix else k, v, out)
    elif isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            flatten(f"{prefix}[{i}]", v, out)
    elif isinstance(value, bool):
        out.append((prefix, "1" if value else "0"))
    else:
        out.append((prefix, str(value)))
    return out


def call(fn, **params):
    if not READ_ONLY.search(fn) or BLOCKED.search(fn):
        raise MoodleError(f"{fn} is not on the read-only list")
    body = urlencode(flatten("", {"wstoken": tok(), "wsfunction": fn, "moodlewsrestformat": "json", **params}, []))
    r = subprocess.run(["/usr/bin/curl", "-sS", "--max-time", "60", "--data", "@-", REST],
                       input=body, capture_output=True, text=True)
    if r.returncode:
        raise MoodleError(redact(f"network error: {r.stderr.strip()}"))
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        snippet = r.stdout[:200]
        if "Just a moment" in snippet:
            raise MoodleError("Moodle's Cloudflare protection blocked the request. Wait a few minutes and try again.")
        raise MoodleError(redact(f"non-JSON reply from Moodle: {snippet!r}"))
    if isinstance(data, dict) and data.get("exception"):
        if data.get("errorcode") == "invalidtoken":
            raise MoodleError("Moodle key expired or revoked. Run `python3 -I moodle.py login` to get a new one.")
        raise MoodleError(f"{fn}: {data.get('errorcode')}: {data.get('message')}")
    return data


# ---------- helpers ----------

class _Text(HTMLParser):
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "table"}

    def __init__(self):
        super().__init__()
        self.out, self.href = [], None

    def handle_starttag(self, tag, attrs):
        if tag in self.BLOCK:
            self.out.append("\n")
        if tag == "li":
            self.out.append("* ")
        if tag == "a":
            href = dict(attrs).get("href") or ""
            self.href = href if href.startswith(("http", "mailto:")) and not href.startswith("mailto:") else None

    def handle_endtag(self, tag):
        if tag == "a" and self.href:
            # text() unescapes the joined output again, so re-escape "&" ("&section" would become "§ion")
            self.out.append(f" <{self.href.replace('&', '&amp;')}>")
            self.href = None
        if tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, d):
        self.out.append(d)


def text(h):
    if not h:
        return ""
    p = _Text()
    p.feed(h)
    s = html.unescape("".join(p.out)).replace("\xa0", " ")
    s = "\n".join(line.strip() for line in s.splitlines())
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def when(ts):
    if not ts:
        return "no date"
    return datetime.fromtimestamp(ts, LONDON).strftime("%a %d %b %Y, %H:%M")


def until(ts):
    d = (datetime.fromtimestamp(ts, LONDON).date() - datetime.now(LONDON).date()).days
    if ts < time.time():
        return "PAST"
    return {0: "today", 1: "tomorrow"}.get(d, f"in {d} days")


_courses = None


def courses():
    global _courses
    if _courses is None:
        uid = call("core_webservice_get_site_info")["userid"]
        _courses = call("core_enrol_get_users_courses", userid=uid)
        for c in _courses:
            c["fullname"] = html.unescape(c.get("fullname", ""))
            c["shortname"] = html.unescape(c.get("shortname", ""))
    return _courses


def code(c):
    m = re.match(r"([A-Z]{4}\d{4})", c.get("shortname") or "") or re.match(r"([A-Z]{4}\d{4})", c.get("fullname") or "")
    return m.group(1) if m else re.sub(r"[_ ]\d\d-\d\d$", "", c.get("shortname") or str(c["id"]))


def find_courses(q):
    cs = courses()
    if not q:
        return cs
    ql = q.lower()
    hits = [c for c in cs if ql in (c.get("shortname", "") + " " + c.get("fullname", "")).lower()]
    if not hits:
        raise MoodleError(f"No course matches {q!r}. Courses: " + ", ".join(f"{code(c)} ({c['fullname']})" for c in cs))
    return hits


SKIPPED = []


_contents = {}


def contents(course_id):
    if course_id not in _contents:
        _contents[course_id] = call("core_course_get_contents", courseid=course_id)
    return _contents[course_id]


def assignments_for(cs):
    # mod_assign_get_assignments returns "invalidresponse" for every UCL course (server-side bug),
    # so assignments are read from the course contents: cmid, instance id, name, dates, description.
    out = []
    for course in cs:
        try:
            secs = contents(course["id"])
        except MoodleError as e:
            SKIPPED.append(f"{code(course)}: {e}")
            continue
        for sec in secs:
            for m in sec.get("modules", []):
                if m.get("modname") != "assign" or not m.get("visible", 1):
                    continue
                dates = {d.get("dataid"): d.get("timestamp") for d in m.get("dates", []) or []}
                out.append({"id": m["instance"], "cmid": m["id"], "name": html.unescape(m.get("name", "")),
                            "duedate": dates.get("duedate") or 0, "cutoffdate": dates.get("cutoffdate") or 0,
                            "intro": m.get("description") or "", "introattachments": [],
                            "_section": sec, "_course": course})
    return out


def status(assign_id):
    try:
        s = call("mod_assign_get_submission_status", assignid=assign_id)
    except MoodleError as e:
        return {"submission": "?", "grade": None, "feedback": str(e), "attachments": []}
    sub = (s.get("lastattempt") or {}).get("submission") or (s.get("lastattempt") or {}).get("teamsubmission") or {}
    fb = s.get("feedback") or {}
    comments = []
    for p in fb.get("plugins", []) or []:
        for ef in p.get("editorfields", []) or []:
            if ef.get("text"):
                comments.append(text(ef["text"]))
    att = []
    for group in ((s.get("assignmentdata") or {}).get("attachments") or {}).values():
        att.extend(group or [])
    return {"submission": sub.get("status", "none"), "grade": fb.get("gradefordisplay"),
            "feedback": "\n".join(comments), "attachments": att}


def with_token(url):
    u = urlparse(url)
    q = [(k, v) for k, v in parse_qsl(u.query) if k != "token"] + [("token", tok())]
    path = u.path
    if "/pluginfile.php" in path and "/webservice/pluginfile.php" not in path:
        path = path.replace("/pluginfile.php", "/webservice/pluginfile.php", 1)
    return urlunparse(u._replace(path=path, query=urlencode(q)))


def download(url, name=None):
    FILES.mkdir(exist_ok=True)
    name = name or Path(urlparse(url).path).name or "file"
    dest = FILES / re.sub(r"[^\w.\- ]", "_", name)
    r = subprocess.run(["/usr/bin/curl", "-sS", "-L", "--max-time", "120", "-o", str(dest), "--config", "-"],
                       input=f'url = "{with_token(url)}"\n', capture_output=True, text=True)
    if r.returncode:
        raise MoodleError(redact(f"download failed: {r.stderr.strip()}"))
    if dest.suffix.lower() in (".docx", ".doc", ".rtf", ".odt"):
        txt = dest.with_suffix(dest.suffix + ".txt")
        subprocess.run(["/usr/bin/textutil", "-convert", "txt", "-output", str(txt), str(dest)], capture_output=True)
        if txt.exists():
            return dest, txt
    return dest, None


# ---------- commands ----------

def cmd_courses(_):
    for c in courses():
        print(f"{code(c):10} id={c['id']:<7} {c['fullname']}")


STATUS = {"submitted": "submitted", "new": "not submitted", "none": "no submission on Moodle",
          "draft": "draft only (not submitted)", "reopened": "reopened"}


def nice_status(st):
    return STATUS.get(st, st)


def course_label(cid):
    for c in courses():
        if c["id"] == cid:
            return code(c)
    return str(cid)


def deadline_items(days, overdue_days=0):
    """(upcoming, overdue): everything due in the next DAYS days, and Moodle assignments due in the last
    OVERDUE_DAYS days that are not submitted. Each item: due, module, name, url, status."""
    now = int(time.time())
    end = now + days * 86400
    items = {}
    ev = call("core_calendar_get_action_events_by_timesort", timesortfrom=now - 3600, timesortto=end, limitnum=50)
    for e in ev.get("events", []):
        url = e.get("url") or f"event:{e['id']}"
        items[url] = {"due": e["timesort"], "module": course_label((e.get("course") or {}).get("id")),
                      "name": html.unescape(e.get("activityname") or e["name"]), "url": e.get("url", ""),
                      "status": "to do" if (e.get("action") or {}).get("actionable") else ""}
    overdue = []
    for a in assignments_for(courses()):
        due = a.get("duedate", 0)
        url = f"{SITE}/mod/assign/view.php?id={a['cmid']}"
        if now - 3600 <= due <= end:
            items[url] = {"due": due, "module": code(a["_course"]), "name": a["name"], "url": url,
                          "status": nice_status(status(a["id"])["submission"])}
        elif overdue_days and now - overdue_days * 86400 <= due < now - 3600:
            st = status(a["id"])["submission"]
            if st != "submitted":
                overdue.append({"due": due, "module": code(a["_course"]), "name": a["name"], "url": url,
                                "status": nice_status(st)})
    return sorted(items.values(), key=lambda x: x["due"]), sorted(overdue, key=lambda x: x["due"])


def deadline_line(it):
    return f"- {when(it['due'])} ({until(it['due'])}) | {it['module']} | {it['name']} | {it['status'] or 'status unknown'} | {it['url']}"


def cmd_deadlines(args):
    days = int(args[0]) if args and args[0].isdigit() else 14
    items, _ = deadline_items(days)
    if not items:
        print(f"Nothing due in the next {days} days.")
        return
    print(f"Deadlines in the next {days} days ({CONFIG['timezone']}), now {when(time.time())}:")
    for it in items:
        print(deadline_line(it))


def cmd_assignments(args):
    cs = find_courses(" ".join(args))
    rows = sorted(assignments_for(cs), key=lambda a: a.get("duedate") or 2**40)
    print("due | module | assignment | status | grade | link")
    for a in rows:
        st = status(a["id"])
        due = a.get("duedate") or 0
        print(f"{when(due)}{' (' + until(due) + ')' if due else ''} | {code(a['_course'])} | {a['name']} | "
              f"{nice_status(st['submission'])} | {st['grade'] or '-'} | {SITE}/mod/assign/view.php?id={a['cmid']}")
    if not rows:
        print("(no Moodle Assignment activities; coursework may be submitted elsewhere, e.g. Turnitin; try `module`)")


def _words(q):
    return [w for w in re.findall(r"\w+", q.lower()) if len(w) > 1 or w.isdigit()]


def matches_all(name, words):
    name = html.unescape(name).lower()
    return all(re.search(rf"\b{re.escape(w)}\b", name) for w in words)


def cmd_brief(args):
    q = " ".join(args)
    if not q:
        raise MoodleError("usage: brief <assignment words or cmid>")
    alla = assignments_for(courses())
    if q.isdigit():
        hits = [a for a in alla if a["cmid"] == int(q) or a["id"] == int(q)]
    else:
        ws = _words(q)
        scored = [(sum(w in (a["name"] + " " + code(a["_course"])).lower() for w in ws), a) for a in alla]
        best = max((s for s, _ in scored), default=0)
        hits = [a for s, a in scored if s == best and s > 0]
    if not hits:
        raise MoodleError(f"No assignment matches {q!r}. Run `assignments` to see names.")
    if len(hits) > 1:
        print("Several assignments match; pick one by cmid:")
        for a in hits:
            print(f"- cmid {a['cmid']}: {code(a['_course'])} | {a['name']} | due {when(a.get('duedate'))}")
        return
    a = hits[0]
    c = a["_course"]
    st = status(a["id"])
    print(f"# {a['name']}\nModule: {code(c)} {c['fullname']}\nDue: {when(a.get('duedate'))}"
          f"{' | cut-off ' + when(a['cutoffdate']) if a.get('cutoffdate') else ''}\n"
          f"Submission: {nice_status(st['submission'])} | Grade: {st['grade'] or '-'}\nLink: {SITE}/mod/assign/view.php?id={a['cmid']}\n")
    if st["feedback"]:
        print("## Feedback\n" + st["feedback"] + "\n")
    print("## Assignment description\n" + (text(a.get("intro")) or "(empty)") + "\n")
    files = list(a.get("introattachments") or []) + list(st.get("attachments") or [])
    secs = contents(c["id"])
    key = [w for w in _words(html.unescape(a["name"])) if len(w) >= 3 and not w.isdigit() and w not in ("the", "and", "for", "with")
           and w not in ("assessment", "submission", "submit", "word", "words", "here", "your", "box")]
    num = re.search(r"assessment\s*(\d+)", a["name"], re.I)
    assessy = re.compile(r"assess|brief|criteria|marking|rubric|coursework|submission", re.I)
    chosen, others = [], []
    for sec in secs:
        sname = html.unescape(sec.get("name", "")).lower()
        holds = any(m.get("id") == a["cmid"] for m in sec.get("modules", []))
        kw = sum(w in sname for w in key)
        by_words = bool(key) and kw >= (len(key) if len(key) <= 2 else len(key) - 1)
        by_num = bool(num) and assessy.search(sname) and re.search(rf"\b{num.group(1)}\b", sname)
        if holds or (assessy.search(sname) and (by_words or by_num)):
            chosen.append(sec)
        elif assessy.search(sname) or "criteria" in sname:
            others.append(sec)
    # If only the submission section matched, the brief is somewhere in the module's assessment area: show it all.
    if all(any(m.get("id") == a["cmid"] for m in s_.get("modules", [])) for s_ in chosen):
        chosen += others
        others = []
    for sec in sorted(chosen, key=lambda x: x.get("section", 0)):
        files += print_section(c["id"], sec)
    if others:
        print("## Other assessment sections in this module (not shown; read with `module "
              f"{code(c)} <section words>`):")
        for sec in others:
            print(f"- {html.unescape(sec.get('name', ''))}")
        print()
    fetch_files(files)


def page_text(course_id, cmid):
    key = ("pages", course_id)
    if key not in _contents:
        try:
            _contents[key] = {p["coursemodule"]: p for p in
                              call("mod_page_get_pages_by_courses", courseids=[course_id]).get("pages", [])}
        except MoodleError:
            _contents[key] = {}
    p = _contents[key].get(cmid)
    return text((p.get("intro") or "") + (p.get("content") or "")) if p else ""


def print_section(course_id, sec, full=True):
    """Print a course section (summary, labels, pages, links) and return its downloadable files."""
    files = []
    print(f"## Section: {html.unescape(sec.get('name', ''))}")
    if full and sec.get("summary"):
        print(text(sec["summary"]))
    for m in sec.get("modules", []):
        mod = m.get("modname")
        if mod == "label":
            print(text(m.get("description")) if full else f"- {m.get('name')}")
            continue
        print(f"- [{mod}] {html.unescape(m.get('name', ''))} {m.get('url', '')}")
        if not full:
            continue
        if mod == "page":
            body = page_text(course_id, m["id"])
            if body:
                print("  " + body.replace("\n", "\n  "))
        elif m.get("description"):
            print("  " + text(m["description"]).replace("\n", "\n  "))
        if mod == "url":
            for f in m.get("contents", []) or []:
                if f.get("fileurl"):
                    print(f"  link: {f['fileurl']}")
        for f in m.get("contents", []) or []:
            if f.get("type") == "file":
                files.append(f)
    print()
    return files


def fetch_files(files):
    if not files:
        return
    print("## Files")
    seen = set()
    for f in files:
        url = f.get("fileurl")
        if not url or url in seen:
            continue
        seen.add(url)
        fname = f.get("filename") or ""
        if not re.search(r"\.(pdf|docx?|pptx?|rtf|odt|txt|md|xlsx?)$", fname, re.I) or (f.get("filesize") or 0) > 30_000_000:
            print(f"- {fname}: not downloaded (not a document, or over 30 MB)")
            continue
        try:
            path, txt = download(url, fname)
            print(f"- {fname}: {path}" + (f" (text: {txt})" if txt else ""))
        except MoodleError as e:
            print(f"- {fname}: {e}")


def cmd_grades(args):
    cs = find_courses(" ".join(args))
    ids = {c["id"] for c in cs}
    uid = call("core_webservice_get_site_info")["userid"]
    overview = {g["courseid"]: g for g in call("gradereport_overview_get_course_grades").get("grades", [])}
    for c in cs:
        print(f"## {code(c)} {c['fullname']}: course total {overview.get(c['id'], {}).get('grade', '-')}")
        try:
            items = call("gradereport_user_get_grade_items", courseid=c["id"], userid=uid)
        except MoodleError as e:
            print(f"  ({e})")
            continue
        for ug in items.get("usergrades", []):
            for gi in ug.get("gradeitems", []):
                if gi.get("itemtype") == "course":
                    continue
                g = gi.get("gradeformatted") or "-"
                fb = text(gi.get("feedback"))
                print(f"- {gi.get('itemname')}: {g}" + (f" | weight {gi['weightformatted']}" if gi.get("weightformatted") else "")
                      + (f" | {when(gi['gradedategraded'])}" if gi.get("gradedategraded") else ""))
                if fb:
                    print("  feedback: " + fb.replace("\n", "\n  "))
    _ = ids


def cmd_module(args):
    if not args:
        cmd_courses(args)
        return
    c = find_courses(args[0])[0]
    focus = _words(" ".join(args[1:]))
    print(f"# {code(c)} {c['fullname']}\n{SITE}/course/view.php?id={c['id']}\n")
    secs = contents(c["id"])
    news = next((m for sec in secs for m in sec.get("modules", [])
                 if m.get("modname") == "forum" and "announce" in m.get("name", "").lower()), None)
    files = []
    if focus:
        picked = [sec for sec in secs if matches_all(sec.get("name", ""), focus)]
        if not picked:
            print(f"No section name contains all of: {' '.join(focus)}")
        for sec in picked:
            files += print_section(c["id"], sec)
        print("## All sections")
        for sec in secs:
            print(f"- [{sec.get('section')}] {html.unescape(sec.get('name', ''))}")
        print()
    else:
        # Overview: every section's name and items; full text only for the current week's section.
        for sec in secs:
            print_section(c["id"], sec, full=False)
    if news:
        try:
            d = call("mod_forum_get_forum_discussions", forumid=news["instance"], sortorder=1, page=0, perpage=5)
            print("## Latest announcements")
            for disc in d.get("discussions", []):
                print(f"- {when(disc.get('created') or disc.get('timemodified'))}: {html.unescape(disc.get('name', ''))}\n  "
                      + text(disc.get("message"))[:800].replace("\n", "\n  "))
            print()
        except MoodleError as e:
            print(f"(announcements unavailable: {e})")
    fetch_files(files)


def cmd_file(args):
    if not args:
        raise MoodleError("usage: file <pluginfile URL>")
    path, txt = download(args[0])
    print(path)
    if txt:
        print(txt)


def cmd_call(args):
    if not args:
        raise MoodleError("usage: call <wsfunction> key=value ...")
    params = {}
    for kv in args[1:]:
        k, _, v = kv.partition("=")
        params[k] = v
    out = []
    for k, v in params.items():  # allow courseids[0]=123 style keys directly
        out.append((k, v))
    fn = args[0]
    if not READ_ONLY.search(fn) or BLOCKED.search(fn):
        raise MoodleError(f"{fn} is not on the read-only list")
    print(json.dumps(call(fn, **dict(out)), indent=1, ensure_ascii=False)[:60000])


# ---------- today ----------

MODULE_CODE = re.compile(r"^[A-Z]{3,5}\d{3,5}")
WEEK_NAME = re.compile(r"^\s*(?:week|wk)\s*(\d+)\b", re.I)


def my_modules():
    """The courses listed in config.json "modules", or every course whose short name starts with a module code."""
    cs = courses()
    if CONFIG["modules"]:
        wanted = [m.upper() for m in CONFIG["modules"]]
        return [c for c in cs if code(c).upper() in wanted]
    return [c for c in cs if MODULE_CODE.match(code(c))]


def teaching_week(day):
    """(term name, week number) for the Monday of a week, or (None, None) outside teaching weeks."""
    for name, start in reversed([(t[0], date.fromisoformat(t[1])) for t in CONFIG["terms"]]):
        if day >= start:
            n = (day - start).days // 7 + 1
            return (name, n) if n <= CONFIG["weeks_per_term"] else (None, None)
    return (None, None)


def find_week_section(secs, term, n):
    hits = [s for s in secs if (m := WEEK_NAME.match(html.unescape(s.get("name", "")))) and int(m.group(1)) == n]
    if len(hits) > 1:
        hits = [s for s in hits if term.lower() in s.get("name", "").lower()] or hits
    return hits[0] if hits else None


def announcements(course, days):
    since = time.time() - days * 86400
    out = []
    for sec in contents(course["id"]):
        for m in sec.get("modules", []):
            name = (m.get("name") or "").lower()
            if m.get("modname") != "forum" or not any(w in name for w in ("announce", "annouce", "news")):
                continue
            try:
                d = call("mod_forum_get_forum_discussions", forumid=m["instance"], sortorder=1, page=0, perpage=5)
            except MoodleError:
                continue
            for disc in d.get("discussions", []):
                ts = disc.get("created") or disc.get("timemodified") or 0
                if ts >= since:
                    body = text(disc.get("message"))
                    out.append((ts, f"{when(ts)} | {html.unescape(disc.get('name', ''))} | "
                                    f"from {disc.get('userfullname', '?')}\n  "
                                    + (body[:1200] + (" …" if len(body) > 1200 else "")).replace("\n", "\n  ")))
    return [t for _, t in sorted(out, reverse=True)]


def cmd_today(_):
    now = datetime.now(LONDON)
    today = now.date()
    monday = today - timedelta(days=today.weekday())
    term, n = teaching_week(monday)
    print(f"# Today: {now:%A %d %B %Y, %H:%M} ({CONFIG['timezone']})")
    print(f"Teaching week: {f'{term}, week {n}' + (' (reading week)' if n == CONFIG['reading_week'] else '') if term else 'none (outside term, or term dates not set in config.json)'}\n")

    upcoming, overdue = deadline_items(14, overdue_days=21)
    print("## Deadlines (next 14 days)")
    print("\n".join(deadline_line(d) for d in upcoming) or "Nothing due.")
    if overdue:
        print("\n## Past due (last 21 days) and NOT submitted on Moodle (may have been handed in elsewhere)")
        print("\n".join(deadline_line(d) for d in overdue))
    print()

    mods = my_modules()
    weeks = [("This week", monday)]
    if today.weekday() >= 4:                      # Friday to Sunday: also show next week, to read ahead
        weeks.append(("Next week", monday + timedelta(days=7)))
    for label, start in weeks:
        t, wk = teaching_week(start)
        if not t:
            print(f"## {label}: no teaching week\n")
            continue
        print(f"## {label}: {t} week {wk}, from Mon {start:%d %b}\n")
        for c in mods:
            try:
                sec = find_week_section(contents(c["id"]), t, wk)
            except MoodleError as e:
                print(f"### {code(c)}: could not read the course ({e})\n")
                continue
            if not sec:
                print(f"### {code(c)}: no section named week {wk}\n")
                continue
            print(f"### {code(c)}")
            print_section(c["id"], sec)

    print("## Announcements (last 7 days, all courses)")
    any_news = False
    for c in courses():
        try:
            news = announcements(c, 7)
        except MoodleError:
            continue
        if news:
            any_news = True
            print(f"### {code(c)}")
            print("\n".join("- " + t for t in news))
    if not any_news:
        print("No announcements.")


# ---------- setup ----------

APP = Path.home() / "Applications/MoodleKey.app"
SKILL_DIRS = {"Claude Code": Path.home() / ".claude/skills", "Codex": Path.home() / ".agents/skills"}


def keychain_token():
    try:
        return token()
    except MoodleError:
        return None


def keychain_stamp():
    """When the Keychain item was last written (Moodle may hand back the same key, so compare this, not the key)."""
    r = subprocess.run(["/usr/bin/security", "find-generic-password", "-s", KEYCHAIN, "-a", "token"],
                       capture_output=True, text=True)
    m = re.search(r'"mdat"<timedate>=\S+\s+"([^"]+)"', r.stdout)
    return m.group(1) if m else None


def cmd_login(_):
    if not APP.exists():
        raise MoodleError(f"{APP} is missing. Run ./install.sh first.")
    before = keychain_stamp()
    url = (f"{SITE}/admin/tool/mobile/launch.php?service=moodle_mobile_app"
           f"&passport={secrets.randbelow(10**9)}&urlscheme=moodlemobile")
    subprocess.run(["/usr/bin/open", url], check=True)
    print("Opened Moodle in your browser.\n"
          "1. Log in to Moodle if it asks (your normal university login).\n"
          "2. When the browser asks to open \"MoodleKey\", click Open (or Allow).\n"
          "Waiting up to 3 minutes for the key...", flush=True)
    for _ in range(90):
        time.sleep(2)
        stamp = keychain_stamp()
        if stamp and stamp != before:
            time.sleep(1)                       # let the helper finish writing
            global TOKEN
            TOKEN = keychain_token()
            info = call("core_webservice_get_site_info")
            print(f"Done: key saved in Keychain and working for {info.get('fullname')} on {info.get('sitename')}.")
            return
    raise MoodleError("No new key arrived. If the browser never asked to open MoodleKey, make sure you're logged in "
                      "to Moodle in that browser, then run `login` again. Log: ~/Library/Logs/read-moodle-skill.log")


def cmd_doctor(_):
    problems = 0

    def check(ok, good, fix):
        nonlocal problems
        print(("ok      " if ok else "PROBLEM ") + (good if ok else fix))
        problems += not ok

    check(sys.version_info >= (3, 9), f"Python {sys.version.split()[0]}", "Python 3.9 or newer is needed.")
    check(CONFIG_FILE.exists(), f"config.json found, site {SITE}", "config.json missing: run ./install.sh")
    check(APP.exists(), "MoodleKey.app installed", "MoodleKey.app missing: run ./install.sh")
    short = "~" + str(HOME)[len(str(Path.home())):] if str(HOME).startswith(str(Path.home())) else str(HOME)
    agents = [name for name, d in SKILL_DIRS.items()
              if (d / "read-moodle/SKILL.md").exists() and f"{short}/moodle.py" in (d / "read-moodle/SKILL.md").read_text()]
    check(bool(agents), "skills installed for " + " and ".join(agents),
          "skills not installed for this folder: run ./install.sh")
    tok_ = keychain_token()
    check(bool(tok_), "Moodle key found in Keychain", "no Moodle key: run `python3 -I moodle.py login`")
    if tok_:
        try:
            info = call("core_webservice_get_site_info")
            cs = courses()
            check(True, f"connected as {info.get('fullname')} on {info.get('sitename')}, {len(cs)} courses", "")
            mods = my_modules()
            check(bool(mods), "modules: " + ", ".join(code(c) for c in mods),
                  "no modules matched: set \"modules\" in config.json to codes from `moodle.py courses`")
        except MoodleError as e:
            check(False, "", f"Moodle call failed: {e}")
    check(bool(CONFIG["terms"]), "term dates set: " + ", ".join(f"{t[0]} from {t[1]}" for t in CONFIG["terms"]),
          "no term dates in config.json, so /today can't tell which week it is")
    print("\nAll good." if not problems else f"\n{problems} problem(s). Fix them in order, then run doctor again.")
    if problems:
        sys.exit(1)


COMMANDS = {"login": cmd_login, "doctor": cmd_doctor, "courses": cmd_courses, "today": cmd_today,
            "deadlines": cmd_deadlines, "assignments": cmd_assignments, "brief": cmd_brief,
            "grades": cmd_grades, "module": cmd_module, "file": cmd_file, "call": cmd_call}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(2)
    try:
        COMMANDS[sys.argv[1]](sys.argv[2:])
        if SKIPPED:
            print("\n(Could not read assignments for: " + "; ".join(SKIPPED) + ")")
    except MoodleError as e:
        print("ERROR:", redact(str(e)), file=sys.stderr)
        sys.exit(1)
