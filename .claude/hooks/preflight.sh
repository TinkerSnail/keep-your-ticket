#!/bin/bash
# Session preflight for Claude Code.
#
# Fires on every SessionStart — a fresh session, a resumed one, a `/clear`, and
# the restart that follows a context compaction — and puts two things in front
# of the model before it does anything else:
#
#   1. The instruction to perform the park preflight at the tier the task
#      calls for: Tier 1 (AGENTS.md, newest journal, tree state) always, and
#      Tier 2 (the full continuity packet and a history search) before touching
#      design, the night, the atlas, a protected anchor, or a decision that is
#      only remembered from chat. The procedure is
#      `.agents/skills/park-preflight/SKILL.md`, shared with Codex, and
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
echo "MANDATORY, in proportion to the task (procedure: .claude/skills/park-preflight/SKILL.md,"
echo "which points at the shared .agents/skills/park-preflight/SKILL.md):"
echo "  Tier 1, now and after every compaction: AGENTS.md (already in context through"
echo "    CLAUDE.md's @AGENTS.md import), the newest journal named below in full, and"
echo "    the tree state at the bottom. Say in the first reply that it was done."
echo "  Tier 2, before touching design, tone, the night, the rebuild atlas, a protected"
echo "    anchor, or any decision you only remember from chat: the full packet below,"
echo "    the task-relevant maps, and a search of the journals and archives for the"
echo "    task's nouns and for supersed/retired/rejected/protected/must not. Then say"
echo "    which handoff controls the task, what is protected, and whether any drift"
echo "    or conflict was found."
echo "  Do not substitute remembered or summarized chat context for the documents."
echo

if [ ! -d documentation ]; then
  echo "!! documentation/ is NOT PRESENT in this checkout. It is gitignored working"
  echo "!! material and lives only on Christina's machine. The preflight cannot be"
  echo "!! completed here; say so before doing anything that depends on the design."
  echo
fi

echo "Tier 2 continuity packet (read completely when the task qualifies):"
echo "  AGENTS.md  (already in context: CLAUDE.md imports it)"
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
for f in documentation/design-archive.md documentation/instructions-archive-*.md; do [ -f "$f" ] && echo "  $(finfo "$f")   <- history and reasoning, not spec; honour supersession markers"; done
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

# CLAUDE.md is a one-line import of AGENTS.md since 2026-09-05, so there is one
# instruction file and nothing to drift. Check that it is still only that.
if [ -f AGENTS.md ]; then
  if [ ! -f CLAUDE.md ]; then
    echo "CLAUDE.md: MISSING — it should hold the single line '@AGENTS.md'."
  elif ! grep -qx '@AGENTS.md' CLAUDE.md; then
    echo "CLAUDE.md: does NOT import AGENTS.md — Claude Code is reading a different"
    echo "  instruction file from Codex. Restore the '@AGENTS.md' line and move any"
    echo "  other content into AGENTS.md; report this."
  else
    EXTRA=$(grep -cvE '^\s*$|^@AGENTS\.md$|^#|^The instruction set is|^shared with Codex|^Edit ' CLAUDE.md)
    if [ "${EXTRA:-0}" != "0" ]; then
      echo "CLAUDE.md: imports AGENTS.md but carries ${EXTRA} other line(s) — content"
      echo "  belongs in AGENTS.md; report it."
    else
      echo "CLAUDE.md: imports AGENTS.md (one instruction file, in sync by construction)."
    fi
  fi
  AW=$(wc -w < AGENTS.md | tr -d ' ')
  echo "AGENTS.md: ${AW} words (kept under 5,000 since 2026-09-05; history lives in the archive)."
else
  echo "AGENTS.md: MISSING."
fi
echo

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
