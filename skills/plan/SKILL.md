---
name: plan
description: Turn my upcoming Moodle deadlines into a step-by-step plan, added to my calendar (and Notion if set up).
argument-hint: "[days ahead, default 90, or an assignment name]"
disable-model-invocation: true
---
<!-- read-moodle-skill -->

If `$ARGUMENTS` appears below literally (Codex doesn't fill it in), use whatever the user typed after the command instead.

Follow the Rules in `{{SKILLS}}/read-moodle/SKILL.md` (read it if it isn't already in context).

Request: `$ARGUMENTS` (empty means every deadline in the next 90 days).

1. Run `python3 -I {{DIR}}/moodle.py deadlines 90` (or the number of days given). Leave out anything already submitted. If an assignment name was given, keep only that one.
2. For each remaining deadline, run `python3 -I {{DIR}}/moodle.py brief <cmid or name>` and read the brief and marking criteria it downloads, so the steps fit the real task (word count, parts, group work, presentations).
3. Propose a plan: for each deadline, 3 to 6 steps working back from the due date (for example: read the brief and criteria, research and reading, outline or proposal, draft, revise, final check and submit a day early). Space them sensibly and avoid putting several big steps on the same day. Show it as a table: Date · Module · Assignment · Step. Ask the user to confirm or change it before writing anything.
4. When the user confirms, write a JSON list to `{{DIR}}/plan.json`, one object per event:
   `{"title": "CODE: step", "date": "YYYY-MM-DD", "type": "Step", "module": "CODE", "assignment": "name", "url": "moodle link", "note": "one line"}`
   Add one `"type": "Deadline"` event per assignment on its due date, with `"time": "HH:MM"`. Keep each title unique within its assignment (the calendar event id is made from it).
   Then run `python3 -I {{DIR}}/ics.py {{DIR}}/plan.json {{DIR}}/plan.ics` and `open {{DIR}}/plan.ics`. Tell the user that Calendar will ask which calendar to add the events to, and suggest making a new one called "Coursework" first so the plan is easy to hide or delete.
5. If `notion_timeline_db` is set in `{{DIR}}/config.json` and the Notion tools are available, also add each event as a row: Task, Type (Deadline/Step), Module, Assignment, Date, Done (unticked), Moodle (link). Don't add rows that are already there (same Task and Date).

If a date changes later, run /plan again for that assignment and keep the step titles the same: the events keep their ids, so importing again moves them instead of adding copies in most calendar apps. If a step is renamed, the old one stays and has to be deleted by hand: say so.
