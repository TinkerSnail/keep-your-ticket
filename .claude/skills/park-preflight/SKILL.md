---
name: park-preflight
description: Reconstruct the complete Keep Your Ticket project context before planning, answering about the park, or editing it. Mandatory at the start of every session and again after any conversation summary, compaction, resume or /clear. Use it whenever the session-start hook says to, whenever you are about to act on a design decision you only remember from chat, or when the user asks for a preflight, a re-read, or "what is the current state".
---

# Keep Your Ticket preflight (Claude Code)

The procedure is **one file, shared with Codex**:
`.agents/skills/park-preflight/SKILL.md`. Read it completely and perform every
step in it. It is not summarized here on purpose — two copies of a procedure
is how this project's constants, tests and stand-ins have drifted before, and a
preflight that drifts from its twin is the failure it exists to catch.

Perform it with these substitutions, which are the only things that differ for
a Claude Code session:

- Where it says `AGENTS.md`, that is `CLAUDE.md` here. The harness has already
  loaded `CLAUDE.md` into context; you do not need to open it again, but you do
  need to **byte-compare it against `AGENTS.md`**. The two are meant to be the
  same document apart from the "Mandatory session preflight" block and the
  file's own name. Anything else is drift; the tracked `AGENTS.md` has been the
  more current of the two before (it carried the 2026-08-30 persistent-world
  supersession for days while `CLAUDE.md` did not). Report drift before
  trusting either on the point that differs.
- Its inventory command uses `rg`. In this harness `rg` may be a shim; the
  `Grep` and `Glob` tools, or `find documentation planning -type f`, give the
  same inventory. What matters is that the inventory is complete — the folder
  is gitignored and nothing may be omitted because of it.
- The session-start hook (`.claude/hooks/preflight.sh`) has already printed
  the inventory, the newest journal, the map-copy comparison and the tree
  state into context. Use it as the starting list; it is not a substitute for
  reading the packet.

## What "read completely" means here

Open each packet file with the `Read` tool and read the whole thing — not the
first page, not a grep hit. Files over the read cap come back paginated and say
so; page through them. `documentation/design.md`, `night.md`, `technical.md`,
`park-rebuild-masterplan.md`, the three focused handoffs, the newest
`current-build-*.md` and the newest journal are the packet. Older journals and
`design-archive.md` are searched, and every match is then read in full.

## Before acting

State in the first reply after the preflight, briefly:

- that the preflight was completed and what triggered it;
- which current handoff controls the task;
- which anchors or files are protected (NT-1 Cascading Staircases, NT-2
  Terraced Fountain, and anything the task-relevant documents mark);
- whether any source drift or unresolved conflict was found, and where.

If two current-looking sources conflict, stop before editing the disputed
area, quote both concisely, and ask Christina which is authoritative.

After a compaction, do all of this again before continuing. The summary may
name likely files and anchors; it does not replace reopening them.
