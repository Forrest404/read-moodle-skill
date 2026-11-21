#!/usr/bin/env python3
"""Turn a plan (JSON list of events) into an .ics file any calendar app can import.

  python3 -I ics.py plan.json plan.ics

Each event: {"title", "date": "YYYY-MM-DD", "type": "Step"|"Deadline", "time": "HH:MM" (optional),
             "module", "assignment", "url", "note"}
Steps become all-day events. Deadlines with a time become a 30-minute event ending at the due time,
with a reminder the day before. Event ids come from type + assignment + title (not the date), so when a date moves,
importing the updated plan moves the event instead of copying it in most calendar apps.
Titles must therefore be unique within an assignment.
"""
import hashlib, json, sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


def esc(s):
    return str(s or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line):
    """iCalendar lines are at most 75 octets; longer ones continue on lines starting with a space."""
    out, b = [], line.encode()
    while len(b) > 75:
        cut = 75
        while (b[cut] & 0xC0) == 0x80:      # don't split a UTF-8 character
            cut -= 1
        out.append(b[:cut].decode())
        b = b" " + b[cut:]
    out.append(b.decode())
    return "\r\n".join(out)


def tzid():
    try:
        return json.loads((Path(__file__).resolve().parent / "config.json").read_text())["timezone"]
    except (OSError, ValueError, KeyError):
        return "Europe/London"


def event(e, tz, stamp):
    d = date.fromisoformat(e["date"])
    uid = hashlib.sha1(f"{e.get('type')}|{e.get('assignment')}|{e['title']}".encode()).hexdigest() + "@read-moodle-skill"
    desc = "\n".join(x for x in (e.get("note"), e.get("assignment"), e.get("url")) if x)
    lines = ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{stamp}", f"SUMMARY:{esc(e['title'])}"]
    if e.get("time"):
        # written in UTC so no time-zone definition is needed in the file
        end = datetime.combine(d, datetime.strptime(e["time"], "%H:%M").time(), ZoneInfo(tz)).astimezone(timezone.utc)
        start = end - timedelta(minutes=30)
        lines += [f"DTSTART:{start:%Y%m%dT%H%M%SZ}", f"DTEND:{end:%Y%m%dT%H%M%SZ}"]
    else:
        lines += [f"DTSTART;VALUE=DATE:{d:%Y%m%d}", f"DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}",
                  "TRANSP:TRANSPARENT"]
    if desc:
        lines.append(f"DESCRIPTION:{esc(desc)}")
    if e.get("url"):
        lines.append(f"URL:{e['url']}")
    if e.get("type") == "Deadline":
        lines += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{esc(e['title'])}", "TRIGGER:-P1D", "END:VALARM"]
    lines.append("END:VEVENT")
    return lines


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    events = json.loads(Path(sys.argv[1]).read_text())
    tz = tzid()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//read-moodle-skill//plan//EN", "CALSCALE:GREGORIAN",
             "X-WR-CALNAME:Coursework"]
    for e in events:
        lines += event(e, tz, stamp)
    lines.append("END:VCALENDAR")
    Path(sys.argv[2]).write_text("\r\n".join(fold(l) for l in lines) + "\r\n")
    print(f"Wrote {len(events)} events to {sys.argv[2]}")


if __name__ == "__main__":
    main()
