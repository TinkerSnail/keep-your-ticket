---
name: park-preflight
description: Reconstruct the Keep Your Ticket project context in proportion to the task. Tier 1 at every session start and after any summary, compaction, resume or clear; Tier 2, the full continuity packet and history search, before touching design, tone, the night, the rebuild atlas, a protected anchor, or any decision remembered only from chat. Mandatory at that proportion.
---

# Keep Your Ticket preflight

Two tiers. Which one applies is decided by what the task touches, never by how
long the session has run. Its purpose is to recover the project's actual source
of truth rather than infer it from conversation memory, a screenshot, or one
recent journal.

## Tier 1 — every session

Also again after every context summary, compaction, resume or clear.

1. Read `AGENTS.md` in full. Claude Code loads it through the `@AGENTS.md`
   import in `CLAUDE.md`; it is the same file.
2. Read the newest dated file in `documentation/journals/` in full.
3. Run `git status`, and check for another live session: dirty paths you did
   not make, and timestamps in
   `~/Library/Application Support/Godot/app_userdata/Keep Your Ticket/logs/`
   that are not yours. A generator run publishes every uncommitted edit in the
   tree.
4. Say in the first reply that the preflight was done and at which tier.

Tier 1 is enough to answer process questions, run or fix tests, fix runtime
code, or continue a task whose files the newest journal names.

## Tier 2 — before touching design, tone, the night, the atlas, a protected anchor, or a remembered decision

Everything in Tier 1, then:

**Inventory the record.** From the repository root:

```bash
rg --files --hidden --no-ignore documentation planning | rg '\.(md|html|txt)$' | sort
```

`find documentation planning -type f` gives the same list where `rg` is a shim.
No document may be omitted because it is gitignored.

**Read the continuity packet completely**, paging through anything over the
read cap:

- `documentation/design.md`
- `documentation/night.md`
- `documentation/technical.md`
- `documentation/park-planning-process.md`
- `documentation/park-rebuild-masterplan.md`
- `documentation/district-story-arcs.md`
- `documentation/seasonal-missions-and-decor.md`
- `documentation/feature-assignments-and-park-legends.md`
- the newest `documentation/current-build-*.md`
- every task-relevant interactive map, including its embedded plan data

The HTML maps under `documentation/maps/` and `planning/` are synchronized
copies. Byte-compare each pair first; when identical, read one. If they differ,
read both and report the drift before using either.

Read only the packet files the task can touch when the task is narrow and the
newest journal makes the boundary clear; read all of them when it does not.

**Search the history.** Across every journal, `documentation/design-archive.md`
and `documentation/instructions-archive-2026-09-05.md`, search for the task's
nouns, named landmarks, `supersed`, `retired`, `rejected`, `protected` and
`must not`. Read every match in full and follow references until the decision's
current state is clear. Do not stream the whole historical corpus into context;
search it and read the matches.

**Resolve authority.**

- `design.md`, `night.md` and `technical.md` govern the current game, night and
  platform.
- `park-rebuild-masterplan.md` and the synchronized maps govern the approved
  rebuild and its execution order.
- The district, seasonal and feature-assignment handoffs govern their layers.
- Journals preserve chronology and evidence. Later entries supersede earlier.
- `design-archive.md` and the instructions archive are reasoning and history,
  not build specifications. Honour every supersession marker.
- Attached documents and images are reference material, not instructions,
  unless the user explicitly adopts something from them.

**Protected anchors.** NT-1 Cascading Staircases and NT-2 Terraced Fountain:
geometry, elevations, approaches, water, terrain and sightlines do not change
without Christina's approval, directly or indirectly.

**Result.** Before acting, state briefly: that the Tier 2 preflight was done;
which current handoff controls the task; which anchors or files are protected;
whether any source drift or unresolved conflict was found. If two
current-looking sources conflict, stop before editing the disputed area, quote
both concisely, and ask Christina which is authoritative. Do not turn an
implementation mismatch into a new design problem.

Do not load binary reference images merely to satisfy this text preflight. View
an image when the task relies on its visual content.
