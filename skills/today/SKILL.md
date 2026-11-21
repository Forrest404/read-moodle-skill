---
name: today
description: My daily Moodle briefing - what's due, what to do today, this week's sessions and readings, and new announcements.
disable-model-invocation: true
---
<!-- read-moodle-skill -->

Follow the Rules in `~/.claude/skills/read-moodle/SKILL.md` (read it if it isn't already in context).

1. Run `python3 -I {{DIR}}/moodle.py today`. If it errors, follow "When something fails" in the read-moodle skill.
2. Read `{{DIR}}/config.json`. If `notion_timeline_db` is set and the Notion tools are available, also get from that database: Steps dated today, Steps before today with Done unticked (overdue), and Steps in the next 3 days.
3. Write the briefing with these sections, leaving out any that are empty:
   - **First line:** weekday and date, the teaching week (e.g. "Term 1, week 8"), and the single most urgent thing.
   - **Due soon:** deadlines in the next 14 days, soonest first: date, time, "in N days" / "tomorrow" / "TODAY", module, name, Moodle status, link. Bold anything due within 3 days.
   - **Do today:** only if the coursework timeline was read. Today's steps, then overdue steps (how many days late), then the next 3 days briefly.
   - **This week:** per module, the session(s) with day, time and room if Moodle gives them; readings to do before class (author, short title, pages if given); any pre-class task. From Friday, also next week's readings so they can be done in advance.
   - **New on Moodle:** announcements from the last 2 days, one line each (date, from whom, what to do, any deadline). Older ones only if they mention a deadline still ahead.
   - **Heads-up:** anything that needs action or doesn't add up: a past-due item not submitted on Moodle (it may have been handed in elsewhere), a deadline mentioned in an announcement, a changed time or room, a timeline date that differs from Moodle.
4. Show the briefing here. If `notion_today_page` is set in config.json and the Notion tools are available, also replace that page's content with the briefing (keep the page title). Write nowhere else.

Style: plain and short, no emoji, no motivational lines, one-line bullets where possible. Link Moodle items. Don't invent anything that isn't in the script output or the timeline. Use exact wording for word counts, file formats and deadlines.
