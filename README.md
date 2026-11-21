# read moodle skill

Website: https://forrest404.github.io/read-moodle-skill/

Ask your AI agent about your Moodle: what's due, what an assignment actually asks for, this week's readings, your grades and feedback. It can also write you a daily briefing and turn your deadlines into a plan in your calendar.

It reads Moodle through Moodle's own API (the same one the official Moodle app uses), so there's no browser automation. It only reads: it can't submit, post or change anything.

Built for UCL Moodle. It should work with other universities' Moodle sites if they allow the Moodle app, but that hasn't been tested.

## Install

You need a Mac and an AI agent that can run commands on it, such as [Claude Code](https://claude.com/claude-code) or [Codex](https://developers.openai.com/codex). Open your agent and paste:

```
Install https://github.com/Forrest404/read-moodle-skill for me. Read SETUP.md and follow it step by step.
```

It does the setup. You'll be asked to:
1. log in to Moodle in your browser, as you normally would, and click **Open** when it asks to open MoodleKey;
2. pick your modules from a list and confirm your term dates;
3. optionally, connect Notion.

Takes about five minutes. Restart your agent afterwards so the commands show up.

Chat apps like the ChatGPT or Claude websites can't run this, because they can't run anything on your Mac. Some agents, such as Codex, will ask you to approve a few setup commands because they need the internet or your Keychain.

## Commands

| Command | What it does |
|---|---|
| `/today` | Daily briefing: what's due, what to do today, this week's sessions and readings, new announcements |
| `/deadlines [days]` | Everything due in the next 14 days (or however many you say), submitted or not |
| `/assignments [module]` | All assignments with due dates, status and grades |
| `/brief <assignment>` | Reads the brief, attachments and marking criteria and tells you what you actually have to do |
| `/module <code> [week 7]` | A module's week: sessions, slides, readings, announcements |
| `/grades [module]` | Grades and a summary of written feedback |
| `/plan` | Breaks your deadlines into steps and adds them to your calendar (and Notion, if connected) |
| `/ask <question>` | Anything else on Moodle |

Some agents start commands with `$` instead of `/`, e.g. `$today` or `$brief case study` in Codex.

You can also just ask in normal words, e.g. "what do I need to read for Thursday?"

## How it works

- `moodle.py` calls Moodle's web-service API with your own key. It refuses any API function that could change something (submit, save, post, update, delete and so on).
- The key comes from Moodle's app sign-in. A small helper, `MoodleKey.app`, is built on your Mac during install. When you click Open, it catches the key and saves it in your macOS Keychain. The key is never shown, logged, or sent anywhere except your Moodle site.
- The skills tell your agent how to use it. They go in your agent's skills folder (`~/.claude/skills/` for Claude Code, `~/.agents/skills/` for Codex).
- Your settings (Moodle site, modules, term dates) are in `config.json` in the install folder.
- Downloaded briefs and slides go in `files/` in the install folder.

If you open `https://moodle.ucl.ac.uk/webservice/rest/server.php` in a browser, you'll see "Invalid token". That's normal: it's an address for programs, not a web page.

## Privacy

Everything runs on your Mac. Moodle data goes to your AI agent only when you ask a question, the same as anything else you ask it. Notion is only used if you connect it.

## Problems

Run `python3 -I ~/read-moodle-skill/moodle.py doctor`. It checks each part and tells you how to fix anything that's wrong.

- **"key expired or revoked"**: run `python3 -I ~/read-moodle-skill/moodle.py login` again.
- **The browser never asks to open MoodleKey**: make sure you're logged in to Moodle in that browser, then run `login` again. If you have the official Moodle app installed on your Mac, it may catch the link instead.
- **"/today" says no teaching week**: check `"terms"` in `config.json`.

## Update

```
cd ~/read-moodle-skill && git pull && ./install.sh
```

## Uninstall

```
~/read-moodle-skill/uninstall.sh && rm -rf ~/read-moodle-skill
```

This removes the skills from your agent, MoodleKey.app and the key in Keychain. If the installer moved any skills of your own aside, they're in `~/read-moodle-skill/backups/`: move them back before deleting the folder. You can also revoke the key in Moodle under Preferences → Security keys, if your site shows it.

---

Not affiliated with or endorsed by UCL or Moodle. MIT licence.
