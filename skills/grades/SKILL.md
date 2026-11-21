---
name: grades
description: Show my Moodle grades and feedback, for all modules or one module.
argument-hint: "[module code or name, optional]"
disable-model-invocation: true
---
<!-- read-moodle-skill -->

If `$ARGUMENTS` appears below literally (Codex doesn't fill it in), use whatever the user typed after the command instead.

Follow the Rules in `{{SKILLS}}/read-moodle/SKILL.md` (read it if it isn't already in context).

Run `python3 -I {{DIR}}/moodle.py grades $ARGUMENTS`. If it errors, follow "When something fails" in the read-moodle skill.

Reply as a table: Module · Item · Grade · Date graded. Skip modules with no grade items. Under the table, summarise each piece of written feedback in 2–3 bullets (strengths, what to improve). Say plainly which items aren't marked yet. Don't guess grades.
