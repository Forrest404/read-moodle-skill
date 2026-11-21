---
name: module
description: Overview of one Moodle module: this week's materials, readings, announcements and assessments.
argument-hint: "<module code or name> [week or section words, optional]"
disable-model-invocation: true
---
<!-- read-moodle-skill -->

Follow the Rules in `~/.claude/skills/read-moodle/SKILL.md` (read it if it isn't already in context).

Request: `$ARGUMENTS`. If it's empty, run `python3 -I {{DIR}}/moodle.py courses` and ask which module.

1. If a week or topic was given, run `python3 -I {{DIR}}/moodle.py module <CODE> <words>`. Otherwise run `python3 -I {{DIR}}/moodle.py module <CODE>` for the outline and announcements. Then work out the current week from today's date and the section names, and run `python3 -I {{DIR}}/moodle.py module <CODE> week <N>` for this week (and next week if it's useful).
2. Read any downloaded files that matter for the question.
3. If the script errors, follow "When something fails" in the read-moodle skill.

Reply with: **This week** (sessions with time and place, slides and recordings, readings, each linked) · **Next week** · **Recent announcements** (date + one line each) · **Assessments** (name + due). Keep it scannable.
