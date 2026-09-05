---
name: park-preflight
description: Reconstruct the Keep Your Ticket project context in proportion to the task. Tier 1 at every session start and after any summary, compaction, resume or clear; Tier 2, the full continuity packet and history search, before touching design, tone, the night, the rebuild atlas, a protected anchor, or any decision remembered only from chat. Use it whenever the session-start hook says to, or when Christina asks for a preflight, a re-read, or "what is the current state".
---

# Keep Your Ticket preflight (Claude Code)

The procedure is **one file, shared with Codex**:
`.agents/skills/park-preflight/SKILL.md`. Read it and perform the tier the task
calls for. It is not repeated here on purpose: two copies of a procedure is how
this project's constants, tests and stand-ins drifted before.

What differs for a Claude Code session, and it is little:

- `CLAUDE.md` is a one-line import of `AGENTS.md`, so `AGENTS.md` is already in
  context. There is nothing to byte-compare any more; if `CLAUDE.md` ever holds
  anything but that import, report it.
- The session-start hook `.claude/hooks/preflight.sh` has printed the document
  inventory, the newest journal's name, the map-copy comparison and the tree
  state. That is the starting list for Tier 2, not the packet itself.
- `rg` may be a shim here; `Grep`, `Glob` or `find documentation planning -type f`
  give the same inventory.
- Open each Tier 2 packet file with `Read` and page through anything over the
  cap. A grep hit is not a read.

After a compaction, do the tier again before continuing. The summary may name
files and anchors; it does not replace reopening them.
