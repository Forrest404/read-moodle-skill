# Setup steps (for the AI doing the install)

You are installing read-moodle-skill for a student. You are either **Claude Code** or **Codex** (OpenAI's coding agent, part of ChatGPT). The steps are the same for both; where they differ, it says so. Follow the steps in order. After each step, check the result it says to expect. If a step fails, stop, tell the student what happened in plain words, and fix it before going on.

Rules for you:
- Never ask for, type or handle the student's password or Moodle key. The key goes straight from Moodle into their Keychain.
- This tool is read-only. Never submit, post or change anything on Moodle.
- Keep messages to the student short and plain. They may not be technical.
- **Codex only:** most steps need the network, files outside the workspace (`~/Applications`, `~/.agents/skills`) or the macOS Keychain, which the sandbox blocks. Run those commands with escalated permissions (outside the sandbox) and tell the student they'll be asked to approve each one.

## 0. Check the computer

This needs a Mac. Run:

```
uname && python3 --version && git --version
```

Expect `Darwin` and Python 3.9 or newer. If `python3` or `git` is missing, macOS offers to install the Command Line Tools: ask the student to click Install, wait for it to finish, then run the check again.

## 1. Download and install

```
git clone https://github.com/Forrest404/read-moodle-skill ~/read-moodle-skill
cd ~/read-moodle-skill && ./install.sh --agent claude
```

Use `--agent claude` if you are Claude Code and `--agent codex` if you are Codex. If the student uses both, use `--agent both`.

Expect lines starting `ok`, one per agent saying where the skills went, and finally `Next: python3 -I ... login`. If the folder already exists, run `git -C ~/read-moodle-skill pull` and then the install line again.

If it says it moved one of the student's existing skills to `backups/`, tell them.

## 2. Choose the Moodle site

`config.json` points at UCL Moodle (`https://moodle.ucl.ac.uk`). Ask the student which university they're at. If it isn't UCL, ask for their Moodle address, put it in `"site"` in `~/read-moodle-skill/config.json` (no trailing slash), and run the install line again so the key helper uses the new site. Also set `"timezone"` if they're not in the UK (an IANA name like `Europe/Paris`).

## 3. Connect to Moodle (the student does one click)

Tell the student first: "Your browser will open Moodle. Log in as usual if it asks. When the browser asks to open MoodleKey, click Open (or Allow). That's all." Then run:

```
python3 -I ~/read-moodle-skill/moodle.py login
```

It waits up to 3 minutes. Expect `Done: key saved in Keychain and working for <their name>`.

If it times out:
- If the browser showed a login page, they may have logged in after it gave up: run `login` again.
- If the browser never asked about MoodleKey, ask them to try another browser (Safari or Chrome) by copying the address bar of the Moodle page into it, or run `login` again.
- If Moodle says the mobile app service isn't enabled, this university doesn't allow app access and the tool can't work there. Tell the student plainly.

## 4. Pick their modules

```
python3 -I ~/read-moodle-skill/moodle.py courses
```

Show the list and ask which ones are their actual modules (suggest the ones whose first column is a module code; things like careers pages, writing centres and reps pages usually aren't). Write the chosen codes, exactly as shown in the first column, into `"modules"` in `config.json`, e.g. `["CCME0141", "CCME0143"]`.

## 5. Term dates

`today` uses `"terms"` in `config.json` to know which teaching week it is. Each entry is a name and the Monday of week 1 of that term's teaching. The default is UCL 2026/27 (Term 1 from 5 Oct 2026, Term 2 from 11 Jan 2027: check this one). Show the student the dates and ask them to confirm or correct them from their university's term dates page. `"reading_week"` is the week number of reading week (6 at UCL) and `"weeks_per_term"` is how many teaching weeks a term has.

## 6. Check everything

```
python3 -I ~/read-moodle-skill/moodle.py doctor
```

Expect every line to start with `ok` and `All good.` at the end. Fix any PROBLEM line using the fix it prints, then run `doctor` again.

## 7. Optional: Notion

Only if the student uses Notion and Notion tools are connected in this session. Ask if they want:
- a **Today** page that the `today` command overwrites with the daily briefing, and
- a **Coursework Timeline** database that the `plan` command fills, with columns Task (title), Type (select: Deadline, Step), Module (select), Assignment (text), Date (date), Weight (text), Done (checkbox), Moodle (url).

Ask where in their Notion to put them, create them there, and save their ids in `config.json` as `"notion_today_page"` and `"notion_timeline_db"` (the database's data source id or URL). If no Notion tools are available, skip this: everything else works without Notion.

## 8. Optional: fewer permission prompts

Ask if they'd like the Moodle commands to run without asking each time.
- **Claude Code:** add this to `permissions.allow` in `~/.claude/settings.json` (or ask them to add it with `/permissions`):
  ```
  "Bash(python3 -I ~/read-moodle-skill/moodle.py:*)"
  ```
- **Codex:** tell them that when Codex asks to run `moodle.py`, they can choose the option to always allow that command for the session.

## 9. Finish

Run `python3 -I ~/read-moodle-skill/moodle.py deadlines 14` and show the result. Then tell the student:
- The commands work after restarting the app. In **Claude Code** they start with `/`: `/today`, `/deadlines`, `/assignments`, `/brief <assignment>`, `/module <code>`, `/grades`, `/plan`, `/ask <question>`. In **Codex** they start with `$` instead: `$today`, `$deadlines`, `$brief <assignment>` and so on. They can also just ask about Moodle in normal words.
- If anything stops working: `python3 -I ~/read-moodle-skill/moodle.py doctor`.
- If the key stops working (for example after changing their password), run the `login` step again.
- To update later: `cd ~/read-moodle-skill && git pull && ./install.sh`.
