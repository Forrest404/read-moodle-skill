---
name: deadlines
description: Show my upcoming Moodle deadlines across all modules for the next N days (default 14).
argument-hint: "[days, default 14]"
disable-model-invocation: true
---
<!-- read-moodle-skill -->

Follow the Rules in `~/.claude/skills/read-moodle/SKILL.md` (read it if it isn't already in context).

Days requested: `$ARGUMENTS` (if empty, use 14).

Run `python3 -I {{DIR}}/moodle.py deadlines <days>`. If it errors, follow "When something fails" in the read-moodle skill.

Reply as a short list grouped by day (e.g. "Mon 16 Nov"): time · module · what · status · link. Mark anything not submitted that's due within 3 days in **bold**. End with one line: how many deadlines are in the window, and the nearest one.
