#!/usr/bin/env bash
# Install the dayprint skill for Claude Code and/or Codex.
#   ./install.sh            both, copied
#   ./install.sh --claude   Claude Code only  (~/.claude/skills/dayprint)
#   ./install.sh --codex    Codex only        (~/.agents/skills/dayprint)
#   ./install.sh --link     symlink instead of copy (updates follow this folder)
#   ./install.sh --zip      build dist/dayprint.zip for the Claude and ChatGPT apps
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
src="$here/skills/dayprint"
targets=() mode=copy zip=0
for a in "$@"; do
  case "$a" in
    --claude) targets+=("$HOME/.claude/skills") ;;
    --codex) targets+=("$HOME/.agents/skills") ;;
    --link) mode=link ;;
    --zip) zip=1 ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done
if [ "$zip" = 1 ]; then
  mkdir -p "$here/dist"
  rm -f "$here/dist/dayprint.zip"
  (cd "$here/skills" && zip -qr "$here/dist/dayprint.zip" dayprint -x '*/__pycache__/*' '*/.DS_Store' '*/evals/*')
  echo "built dist/dayprint.zip"
  [ ${#targets[@]} -eq 0 ] && exit 0
fi
[ ${#targets[@]} -eq 0 ] && targets=("$HOME/.claude/skills" "$HOME/.agents/skills")
for t in "${targets[@]}"; do
  mkdir -p "$t"
  dest="$t/dayprint"
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    echo "replacing $dest"
    rm -rf "$dest"
  fi
  if [ "$mode" = link ]; then ln -s "$src" "$dest"; else cp -R "$src" "$dest"; rm -rf "$dest/evals"; fi
  echo "installed: $dest"
done
echo "Restart Claude Code or Codex, then ask: \"Plan my Cavion workspace from my work\" (Codex: \$dayprint)."
