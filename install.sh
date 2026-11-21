#!/bin/zsh
# Install read-moodle-skill: builds MoodleKey.app (catches the Moodle key), installs the skills for
# Claude Code and/or Codex (ChatGPT), and creates config.json. Safe to run again. No password needed.
#
#   ./install.sh                     install for every agent found (Claude Code, Codex)
#   ./install.sh --agent claude      only Claude Code   (skills in ~/.claude/skills)
#   ./install.sh --agent codex       only Codex         (skills in ~/.agents/skills)
#   ./install.sh --skills-dir DIR    put the skills somewhere else (for testing; needs --agent)
#   ./install.sh --app-dir DIR       build MoodleKey.app somewhere else (for testing; not registered)
set -e
DIR="${0:A:h}"
AGENT=auto
SKILLS_DIR=""
APP_DIR="$HOME/Applications"
REGISTER=1
while (( $# )); do
  case "$1" in
    --agent) AGENT="$2"; shift 2 ;;
    --skills-dir) SKILLS_DIR="$2"; shift 2 ;;
    --app-dir) APP_DIR="$2"; REGISTER=0; shift 2 ;;
    *) echo "Unknown option: $1"; exit 2 ;;
  esac
done
KEYCHAIN="read-moodle-skill"
APP="$APP_DIR/MoodleKey.app"

say() { print -r -- "$1"; }
fail() { print -r -- "STOP: $1"; exit 1; }

# 1. Checks
[[ "$(uname)" == Darwin ]] || fail "this only works on macOS."
command -v python3 >/dev/null || fail "python3 not found. Run: xcode-select --install"
python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null \
  || fail "Python 3.9 or newer is needed (found $(python3 --version 2>&1)). Run: xcode-select --install"
[[ -x /usr/bin/curl ]] || fail "curl not found."
say "ok   macOS, $(python3 --version), curl"

# 2. Config
if [[ ! -f "$DIR/config.json" ]]; then
  cp "$DIR/config.example.json" "$DIR/config.json"
  say "ok   created config.json (UCL Moodle by default)"
else
  say "ok   kept your existing config.json"
fi
SITE=$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["site"].rstrip("/"))' "$DIR/config.json")

# 3. MoodleKey.app: a tiny helper for moodlemobile:// links, built here so macOS trusts it
mkdir -p "$APP_DIR"
rm -rf "$APP"
/usr/bin/osacompile -o "$APP" "$DIR/key/handler.applescript" 2>/dev/null || fail "couldn't build MoodleKey.app."
PB=/usr/libexec/PlistBuddy
PLIST="$APP/Contents/Info.plist"
$PB -c "Set :CFBundleIdentifier io.github.forrest404.moodlekey" "$PLIST" 2>/dev/null \
  || $PB -c "Add :CFBundleIdentifier string io.github.forrest404.moodlekey" "$PLIST"
$PB -c "Add :LSUIElement bool true" "$PLIST" 2>/dev/null || $PB -c "Set :LSUIElement true" "$PLIST"
$PB -c "Delete :CFBundleURLTypes" "$PLIST" 2>/dev/null || true
$PB -c "Add :CFBundleURLTypes array" \
    -c "Add :CFBundleURLTypes:0 dict" \
    -c "Add :CFBundleURLTypes:0:CFBundleURLName string Moodle key catcher" \
    -c "Add :CFBundleURLTypes:0:CFBundleURLSchemes array" \
    -c "Add :CFBundleURLTypes:0:CFBundleURLSchemes:0 string moodlemobile" "$PLIST"
sed -e "s|__SITE__|$SITE|" -e "s|__KEYCHAIN__|$KEYCHAIN|" "$DIR/key/store_token.sh" > "$APP/Contents/Resources/store_token.sh"
/usr/bin/codesign --force --deep -s - "$APP" >/dev/null 2>&1
if (( REGISTER )); then
  /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$APP"
fi
say "ok   built $APP"

# 4. Skills, for each agent. A skill folder with the same name that isn't ours is moved into
#    backups/ in this folder, never overwritten.
case "$AGENT" in
  claude) AGENTS=(claude) ;;
  codex) AGENTS=(codex) ;;
  both) AGENTS=(claude codex) ;;
  auto)
    AGENTS=()
    { command -v claude >/dev/null || [[ -d "$HOME/.claude" ]] } && AGENTS+=(claude)
    { command -v codex >/dev/null || [[ -d "$HOME/.codex" ]] } && AGENTS+=(codex)
    (( ${#AGENTS} )) || fail "found neither Claude Code nor Codex. Install one, or pass --agent claude or --agent codex."
    ;;
  *) fail "--agent must be claude, codex or both." ;;
esac
[[ -n "$SKILLS_DIR" && ${#AGENTS} -gt 1 ]] && fail "--skills-dir needs a single --agent."
SHOWDIR="${DIR/#$HOME/~}"     # ~/read-moodle-skill, so a permission rule written with ~ matches
STAMP=$(date +%Y%m%d-%H%M%S)
for agent in $AGENTS; do
  if [[ -n "$SKILLS_DIR" ]]; then target="$SKILLS_DIR"
  elif [[ $agent == claude ]]; then target="$HOME/.claude/skills"
  else target="$HOME/.agents/skills"; fi
  mkdir -p "$target"
  showtarget="${target/#$HOME/~}"
  for src in "$DIR"/skills/*(/); do
    name="${src:t}"
    dest="$target/$name"
    if [[ -e "$dest" ]] && ! grep -q "read-moodle-skill" "$dest/SKILL.md" 2>/dev/null; then
      mkdir -p "$DIR/backups/$agent-$STAMP"
      mv "$dest" "$DIR/backups/$agent-$STAMP/"
      say "note you already had a skill called '$name'; moved it to $DIR/backups/$agent-$STAMP/"
    fi
    rm -rf "$dest"
    cp -R "$src" "$dest"
    sed -e "s|{{DIR}}|$SHOWDIR|g" -e "s|{{SKILLS}}|$showtarget|g" "$src/SKILL.md" > "$dest/SKILL.md"
  done
  if [[ $agent == claude ]]; then say "ok   Claude Code: skills in $showtarget (commands like /today)"
  else say "ok   Codex: skills in $showtarget (commands like \$today)"; fi
done

say ""
say "Next: python3 -I \"$DIR/moodle.py\" login"
