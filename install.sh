#!/usr/bin/env bash
# install.sh — wire websupport-skill into your toolchain + Claude Code skills.
#   command  ->  ~/bin/websupport   (alias: ~/bin/ws-api)
#   skill    ->  ~/.claude/skills/websupport
set -euo pipefail
ROOT="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
BIN="${WS_BIN_DIR:-$HOME/bin}"
SKILLS="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"

mkdir -p "$BIN" "$SKILLS"
chmod +x "$ROOT/bin/websupport" "$ROOT/skills/websupport/scripts/ws_api.py"

ln -sf "$ROOT/bin/websupport" "$BIN/websupport"
ln -sf "$ROOT/bin/websupport" "$BIN/ws-api"

# If a real (non-symlink) skill dir is already there, back it up before linking.
DEST="$SKILLS/websupport"
if [ -e "$DEST" ] && [ ! -L "$DEST" ]; then
  BAK="$DEST.bak-$(date +%s)"
  mv "$DEST" "$BAK"
  echo "Backed up existing skill dir -> $BAK"
fi
ln -sfn "$ROOT/skills/websupport" "$DEST"

echo "Installed:"
echo "  command: websupport  (alias: ws-api)   in $BIN"
echo "  skill:   $DEST"
echo
echo "Next:"
echo "  1) ensure $BIN is on your PATH"
echo "  2) export your keys (e.g. in ~/.zshenv or ~/.bashrc):"
echo "       export WEBSUPPORT_API_KEY=...   export WEBSUPPORT_API_SECRET=..."
echo "  3) smoke test:  websupport whoami"
