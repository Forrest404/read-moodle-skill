---
name: brief
description: Read a Moodle assignment's brief, attachments and marking criteria, and summarise what I actually have to do.
argument-hint: "<assignment name or module, or a cmid>"
disable-model-invocation: true
---
<!-- read-moodle-skill -->

Follow the Rules in `~/.claude/skills/read-moodle/SKILL.md` (read it if it isn't already in context).

Assignment: `$ARGUMENTS`. If it's empty, run `python3 -I {{DIR}}/moodle.py assignments` and ask which one.

1. Run `python3 -I {{DIR}}/moodle.py brief $ARGUMENTS`. If it lists several matches, ask which one (or pick the obvious one if only one is upcoming).
2. Read every document it downloaded (PDFs with Read; for .docx read the `.docx.txt`). If it lists "Other assessment sections" that look relevant (marking criteria, rubric), run `python3 -I {{DIR}}/moodle.py module <CODE> <section words>` for them.
3. If the script errors, follow "When something fails" in the read-moodle skill.

Reply with:
- **Task:** what to produce, in 2–3 sentences
- **Due / length / format:** due date and time, word count or length, file type and naming, where and how to submit (who submits, cover sheets)
- **Marking criteria:** the criteria and weightings, as given
- **Must-dos and gotchas:** required readings, referencing style, no-extension rules, anything easy to miss
- **Status:** submitted or not
- **Sources:** links to the pages and files used

Quote the brief exactly where wording matters. Don't write the assignment unless I ask.
