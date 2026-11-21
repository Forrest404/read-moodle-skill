# read-moodle-skill

If you've been asked to install or set this up for someone, follow [SETUP.md](SETUP.md) step by step.

What's here: `moodle.py` is a read-only Moodle API client (Python standard library plus curl), `skills/` holds the skills for Claude Code and Codex, `install.sh` and `uninstall.sh` set them up, and `docs/` is the website. Never add anything that writes to Moodle: `moodle.py` refuses any API function that isn't a read, and that check must stay.

The website lives in a separate repo, github.com/readmoodle/readmoodle.github.io (served at https://readmoodle.github.io). `docs/` here only redirects the old address.
