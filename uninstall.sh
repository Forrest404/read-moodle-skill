#!/bin/zsh
# Remove read-moodle-skill: the skills, MoodleKey.app and the Moodle key in Keychain.
# Leaves this folder (delete it yourself) and anything in Notion or your calendar.
DIR="${0:A:h}"
for target in "$HOME/.claude/skills" "$HOME/.agents/skills"; do
  for src in "$DIR"/skills/*(/); do
    dest="$target/${src:t}"
    grep -q "read-moodle-skill" "$dest/SKILL.md" 2>/dev/null && rm -rf "$dest"
  done
done
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister \
  -u "$HOME/Applications/MoodleKey.app" 2>/dev/null
rm -rf "$HOME/Applications/MoodleKey.app"
/usr/bin/security delete-generic-password -s read-moodle-skill -a token >/dev/null 2>&1
echo "Removed the skills, MoodleKey.app and the Moodle key."
echo "Any skills of your own that install.sh moved aside are in $DIR/backups/ (move them back before deleting the folder)."
echo "To finish: delete $DIR, and optionally revoke the key in Moodle (Preferences > Security keys)."
