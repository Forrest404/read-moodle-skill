#!/bin/zsh
# Runs inside MoodleKey.app. Receives moodlemobile://token=BASE64 from Moodle's app sign-in and saves
# the key in Keychain. BASE64 decodes to "sitehash:::TOKEN[:::PRIVATETOKEN]". The key is never printed or logged.
# install.sh fills in __SITE__ and __KEYCHAIN__ when it copies this file into the app.
SITE="__SITE__"
KEYCHAIN="__KEYCHAIN__"
LOG=~/Library/Logs/read-moodle-skill.log
log() { print -r -- "$(date '+%F %T') $1" >> $LOG; }
note() { /usr/bin/osascript -e "display notification \"$1\" with title \"Moodle\""; }
url="$1"
log "called; url length ${#url}; prefix ${url[1,20]}"
b64="${url#*token=}"; b64="${b64%%[&#]*}"
# undo percent-encoding and URL-safe base64, then fix padding
b64=$(printf %s "$b64" | /usr/bin/sed -e 's/%2[Bb]/+/g' -e 's/%2[Ff]/\//g' -e 's/%3[Dd]/=/g' | /usr/bin/tr -- '-_' '+/')
b64="${b64//[[:space:]]/}"
while (( ${#b64} % 4 )); do b64+="="; done
decoded=$(printf %s "$b64" | /usr/bin/base64 -D 2>/dev/null)
tok=$(printf %s "$decoded" | /usr/bin/awk -F':::' '{print $2}')
log "token length ${#tok}; looks valid: $([[ "$tok" =~ '^[0-9a-zA-Z]{32}$' ]] && echo yes || echo no)"
if [[ ! "$tok" =~ '^[0-9a-zA-Z]{32}$' ]]; then note "Couldn't read a key from the Moodle link. See ~/Library/Logs/read-moodle-skill.log."; exit 1; fi
if /usr/bin/security add-generic-password -U -s "$KEYCHAIN" -a token -w "$tok" 2>>$LOG; then log "keychain add ok"; else log "keychain add FAILED"; note "Couldn't save the key to Keychain."; exit 1; fi
name=$(printf 'wstoken=%s&wsfunction=core_webservice_get_site_info&moodlewsrestformat=json' "$tok" \
  | /usr/bin/curl -s --data @- "$SITE/webservice/rest/server.php" \
  | /usr/bin/plutil -extract fullname raw -o - - 2>/dev/null)
log "test call name: ${name:-<none>}"
if [[ -n "$name" ]]; then note "Key saved and working for $name."; else note "Key saved, but the test call failed."; fi
