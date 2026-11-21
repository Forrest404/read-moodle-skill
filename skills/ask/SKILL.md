---
name: ask
description: Ask anything about my Moodle (courses, assignments, readings, announcements, grades) and get an answer from the live site.
argument-hint: "<your question>"
disable-model-invocation: true
---
<!-- read-moodle-skill -->

If `$ARGUMENTS` appears below literally (Codex doesn't fill it in), use whatever the user typed after the command instead.

Follow `{{SKILLS}}/read-moodle/SKILL.md` (read it if it isn't already in context). It lists the script commands and the Rules.

Question: $ARGUMENTS

Choose the script commands that answer it (`deadlines`, `assignments`, `brief`, `grades`, `module`, `file`, or `call <read-only wsfunction>` for anything else, such as forum posts). Run them with `python3 -I {{DIR}}/moodle.py ...`, read any downloaded files, and answer directly with links. If it can't be answered from Moodle, say so and say where else to look (e.g. the university's assessment platform, email, or student records system).
