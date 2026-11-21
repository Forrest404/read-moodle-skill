---
name: assignments
description: List my Moodle assignments with due dates and submission status, for all modules or one module.
argument-hint: "[module code or name, optional]"
disable-model-invocation: true
---
<!-- read-moodle-skill -->

If `$ARGUMENTS` appears below literally (Codex doesn't fill it in), use whatever the user typed after the command instead.

Follow the Rules in `{{SKILLS}}/read-moodle/SKILL.md` (read it if it isn't already in context).

Run `python3 -I {{DIR}}/moodle.py assignments $ARGUMENTS` (no argument means all modules). If it errors, follow "When something fails" in the read-moodle skill.

Reply as one table sorted by due date: Module · Assignment · Due (with "in N days") · Status · Link. Put upcoming items first and past ones in a short "Earlier" list underneath. Bold anything not submitted that's due within 7 days. If a past item shows "not submitted", mention it plainly in one line; it may have been submitted elsewhere or not required. No other commentary.
