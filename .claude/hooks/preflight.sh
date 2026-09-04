#!/bin/bash
# Session preflight for Claude Code.
#
# Fires on every SessionStart — a fresh session, a resumed one, a `/clear`, and
# the restart that follows a context compaction — and puts two things in front
# of the model before it does anything else:
#
#   1. The instruction to perform the park preflight in full: reread the
#      continuity packet rather than trusting a summary of it. The procedure
#      is `.agents/skills/park-preflight/SKILL.md`, shared with Codex, and
#      `.claude/skills/park-preflight/SKILL.md` is the Claude Code entry to it.
#   2. A current inventory of the documentation corpus — what exists, how big
#      it is, when it last changed, which journal is newest, and whether the
#      synchronized map copies still agree — so the model reads what is
#      actually on disk and not what it remembers being there.
#
# It prints an inventory and not the documents. The corpus is ~800KB and the
# preflight skill says why streaming all of it into a summarized context is
# the wrong answer; the packet is read by the skill, on demand, in full. Set
# KYT_PREFLIGHT_INLINE=1 to have this hook cat the packet as well.
#
# stdout from a SessionStart hook is added to the model's context. Everything
# here is best-effort: a missing tool or a missing folder is reported, never
# fatal, because a preflight that crashes is a preflight that did not run.
set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$PROJECT_DIR" || exit 0

# Why this hook fired. The harness passes JSON on stdin with a `source` field:
# startup | resume | clear | compact.
SOURCE="unknown"
if [ ! -t 0 ]; then
  INPUT="$(cat 2>/dev/null || true)"
  if [ -n "$INPUT" ]; then
    if command -v jq >/dev/null 2>&1; then
      SOURCE="$(printf '%s' "$INPUT" | jq -r '.source // "unknown"' 2>/dev/null || echo unknown)"
    else
      SOURCE="$(printf '%s' "$INPUT" | sed -n 's/.*"source"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"
      SOURCE="${SOURCE:-unknown}"
    fi
  fi
fi

case "$SOURCE" in
  compact) WHY="context was just summarized/compacted — the summary is not the record" ;;
  resume)  WHY="session resumed — the tree may have moved since it was last read" ;;
  clear)   WHY="context was cleared" ;;
  startup) WHY="new session" ;;
  *)       WHY="session start" ;;
esac

# Portable stat: size and mtime as a date.
finfo() {
  local f="$1"
  if [ -f "$f" ]; then
    local sz
    sz=$(wc -c < "$f" | tr -d ' ')
    local mt
    if stat -f '%Sm' -t '%Y-%m-%d' "$f" >/dev/null 2>&1; then
      mt=$(stat -f '%Sm' -t '%Y-%m-%d' "$f")
    else
      mt=$(stat -c '%y' "$f" 2>/dev/null | cut -d' ' -f1)
    fi
    printf '%s  (%s B, %s)' "$f" "$sz" "$mt"
  else
    printf '%s  (MISSING)' "$f"
  fi
}

hash_of() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 1 "$1" 2>/dev/null | cut -d' ' -f1
  elif command -v md5 >/dev/null 2>&1; then md5 -q "$1" 2>/dev/null
  else cksum "$1" 2>/dev/null | cut -d' ' -f1; fi
}

echo "=== KEEP YOUR TICKET — SESSION PREFLIGHT (${SOURCE}: ${WHY}) ==="
echo
echo "MANDATORY before planning, answering about the park, or editing anything:"
echo "  Invoke the \`park-preflight\` skill (.claude/skills/park-preflight/SKILL.md)"
echo "  and perform it in full. It points at the shared procedure in"
echo "  .agents/skills/park-preflight/SKILL.md. Reread the continuity packet below"
echo "  completely — do not substitute remembered or summarized chat context for"
echo "  the documents. Then say in your first reply that the preflight was done,"
echo "  which handoff controls the task, which anchors are protected, and whether"
echo "  any drift or conflict was found."
echo

if [ ! -d documentation ]; then
  echo "!! documentation/ is NOT PRESENT in this checkout. It is gitignored working"
  echo "!! material and lives only on Christina's machine. The preflight cannot be"
  echo "!! completed here; say so before doing anything that depends on the design."
  echo
fi

echo "Continuity packet — read every one of these completely:"
echo "  CLAUDE.md  (already loaded into context by the harness)"
for f in \
  documentation/design.md \
  documentation/night.md \
  documentation/technical.md \
  documentation/park-rebuild-masterplan.md \
  documentation/district-story-arcs.md \
  documentation/seasonal-missions-and-decor.md \
  documentation/feature-assignments-and-park-legends.md \
  ; do
  echo "  $(finfo "$f")"
done
# The current-build survey is dated in its filename; pick the newest.
CB="$(ls documentation/current-build-*.md 2>/dev/null | sort | tail -1)"
if [ -n "$CB" ]; then echo "  $(finfo "$CB")"; else echo "  documentation/current-build-*.md  (none found)"; fi

# Journals.
if [ -d documentation/journals ]; then
  JCOUNT=$(ls documentation/journals/*.md 2>/dev/null | wc -l | tr -d ' ')
  JFIRST=$(ls documentation/journals/*.md 2>/dev/null | sort | head -1 | xargs -n1 basename 2>/dev/null)
  JLAST=$(ls documentation/journals/*.md 2>/dev/null | sort | tail -1)
  echo "  $(finfo "$JLAST")   <- newest journal; read in full"
  echo
  echo "Journals: ${JCOUNT} files, ${JFIRST} … $(basename "$JLAST"). Older entries are"
  echo "  evidence, not a second packet: search them for the task's nouns, landmarks,"
  echo "  'supersed', 'retired', 'rejected', 'protected', 'must not', and read every"
  echo "  match in full before trusting a decision. Later entries supersede earlier."
  echo "  Newest five:"
  ls documentation/journals/*.md 2>/dev/null | sort | tail -5 | while read -r j; do echo "    $(finfo "$j")"; done
fi
echo

# Other documents in the corpus, so nothing is silently omitted.
echo "Rest of the textual corpus (inventory, not the packet):"
for f in documentation/design-archive.md; do echo "  $(finfo "$f")   <- tone/history reference; honour its supersession markers"; done
for f in documentation/screenshots/*/README.md; do [ -f "$f" ] && echo "  $(finfo "$f")"; done
echo

# Synchronized map copies: documentation/maps/*.html <-> planning/*.html.
echo "Synchronized map copies (byte-compare; read one if identical, both if not):"
DRIFT=0
for m in documentation/maps/*.html; do
  [ -f "$m" ] || continue
  b=$(basename "$m")
  p="planning/$b"
  if [ -f "$p" ]; then
    if [ "$(hash_of "$m")" = "$(hash_of "$p")" ]; then
      echo "  $b  identical"
    else
      echo "  $b  DIFFERS between documentation/maps/ and planning/ — read both, report the drift"
      DRIFT=1
    fi
  else
    echo "  $b  has no planning/ twin"
  fi
done
echo

# CLAUDE.md and AGENTS.md are meant to be the same document apart from the
# preflight block naming each agent and one self-reference. Anything else is
# drift, and the tracked AGENTS.md has been the more current of the two before.
if [ -f AGENTS.md ] && [ -f CLAUDE.md ]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 - <<'PY'
import difflib, re
def norm(p):
    t = open(p, encoding="utf-8", errors="replace").read()
    t = re.sub(r"## Mandatory session preflight.*?(?=\n## |\nFull description:)", "", t, count=1, flags=re.S)
    t = t.replace("`AGENTS.md`", "`INSTRUCTIONS.md`").replace("`CLAUDE.md`", "`INSTRUCTIONS.md`")
    return t.splitlines()
a, c = norm("AGENTS.md"), norm("CLAUDE.md")
d = [l for l in difflib.unified_diff(c, a, "CLAUDE.md", "AGENTS.md", n=0, lineterm="") if l[:1] in "+-" and l[:3] not in ("+++", "---")]
if d:
    print("CLAUDE.md vs AGENTS.md: DRIFT — %d differing lines beyond the preflight block." % len(d))
    print("  Treat the tracked AGENTS.md as the reference and report the difference.")
    for l in d[:8]:
        print("   ", l[:140])
    if len(d) > 8: print("    …")
else:
    print("CLAUDE.md vs AGENTS.md: in sync (only the preflight block differs).")
PY
  fi
  echo
fi

echo "Protected anchors — no direct or indirect change without Christina's approval:"
echo "  NT-1 Cascading Staircases  (scenes/world/west_stair.tscn and its generator)"
echo "  NT-2 Terraced Fountain     (scenes/world/east_cascade.tscn and its generator)"
echo "  Their geometry, approaches, elevations, water, terrain and sightlines are fixed."
echo

# Tree state, because more than one session may hold it.
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  BR=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
  DIRTY=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  HEADLINE=$(git log -1 --format='%h %s' 2>/dev/null)
  echo "Tree: branch ${BR}, HEAD ${HEADLINE}, ${DIRTY} dirty path(s)."
  if [ "$DIRTY" != "0" ]; then
    echo "  Dirty paths may be another session's in-flight work. Check before regenerating"
    echo "  or committing; a generator run publishes whatever the tree holds."
    git status --porcelain 2>/dev/null | head -12 | sed 's/^/    /'
  fi
fi
if command -v pgrep >/dev/null 2>&1; then
  if pgrep -x Godot >/dev/null 2>&1 || pgrep -f 'Godot.app' >/dev/null 2>&1 || pgrep -x godot >/dev/null 2>&1; then
    echo "  A Godot process is running — a capture, test or the editor may hold the tree."
  fi
fi
echo

if [ "${KYT_PREFLIGHT_INLINE:-0}" = "1" ]; then
  echo "=== INLINE CONTINUITY PACKET (KYT_PREFLIGHT_INLINE=1) ==="
  for f in documentation/design.md documentation/night.md documentation/technical.md \
           documentation/park-rebuild-masterplan.md "$CB" "$JLAST"; do
    [ -f "$f" ] || continue
    echo; echo "----- $f -----"; cat "$f"
  done
fi

echo "=== END PREFLIGHT ($DRIFT map-copy drift flag) ==="
exit 0
