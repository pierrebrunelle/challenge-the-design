#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Install the Challenge the Design skill from this checkout.

Usage: ./install.sh --platform <name> [--destination /path/to/skill]

Platforms:
  codex-skill   ~/.agents/skills/challenge-the-design
  cursor-skill  ~/.cursor/skills/challenge-the-design
  claude-code   ./.claude/skills/challenge-the-design
  antigravity   ~/.gemini/antigravity/skills/challenge-the-design

An explicit destination is the skill directory itself. Existing destinations are
left untouched. To install from GitHub, use:
  npx skills add pierrebrunelle/challenge-the-design
EOF
}

platform=''
destination=''
while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform|--destination)
      if [[ $# -lt 2 || -z "$2" || "$2" == --* ]]; then
        echo "Missing value for $1" >&2
        exit 2
      fi
      if [[ "$1" == '--platform' ]]; then platform="$2"; else destination="$2"; fi
      shift 2
      ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

case "$platform" in
  codex-skill) default_destination="$HOME/.agents/skills/challenge-the-design" ;;
  cursor-skill) default_destination="$HOME/.cursor/skills/challenge-the-design" ;;
  claude-code) default_destination="$PWD/.claude/skills/challenge-the-design" ;;
  antigravity) default_destination="$HOME/.gemini/antigravity/skills/challenge-the-design" ;;
  *) echo 'Choose a supported --platform; use --help for the list.' >&2; exit 2 ;;
esac
destination="${destination:-$default_destination}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_dir="$script_dir/skills/challenge-the-design"
if [[ ! -f "$source_dir/SKILL.md" || ! -f "$source_dir/agents/openai.yaml" ]]; then
  echo 'Run install.sh from a complete cloned checkout.' >&2
  exit 1
fi
parent="$(dirname "$destination")"
mkdir -p "$parent"
# mkdir claims the destination without overwriting an existing or concurrent install.
if ! mkdir "$destination"; then
  echo "Could not create a new destination; left untouched: $destination" >&2
  exit 1
fi
cp -R "$source_dir/." "$destination/"
echo "Installed skill: $destination"
