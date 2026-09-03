---
name: park-preflight
description: Reconstruct the complete Keep Your Ticket project context before planning or implementation. Mandatory at the start of every project session and again whenever conversation context is summarized or compacted.
---

# Keep Your Ticket preflight

Use this before making a plan, editing the park, or interpreting an earlier
decision. Its purpose is to recover the project’s actual source of truth rather
than infer it from conversation memory, a screenshot, or one recent journal.

## Inventory the whole project record

From the repository root, enumerate every textual project document with:

```bash
rg --files --hidden --no-ignore documentation planning | rg '\.(md|html|txt)$' | sort
```

This inventory is mandatory: no document may be silently omitted because it is
gitignored. Record the newest journal and search the entire inventory for the
current task's nouns, named landmarks, `supersed`, `retired`, `rejected`,
`protected`, and `must not`. Read every matching document and journal entry in
full, following direct references until the decision's current state is clear.

The HTML maps under `documentation/maps/` and `planning/` are synchronized
copies. Byte-compare each pair first; when a pair is identical, read one copy.
If they differ, read both and report the drift before using either as a handoff.

## Read the continuity packet

Read these files completely on every new session and after every context
summary or compaction:

- `AGENTS.md`
- `documentation/design.md`
- `documentation/night.md`
- `documentation/technical.md`
- `documentation/park-rebuild-masterplan.md`
- `documentation/district-story-arcs.md`
- `documentation/seasonal-missions-and-decor.md`
- `documentation/feature-assignments-and-park-legends.md`
- `documentation/current-build-2026-09-01.md`, or its newer replacement
- the newest dated file in `documentation/journals/`
- every current task-relevant document identified by the inventory search
- each current task-relevant interactive map, including its embedded plan data

If `AGENTS.md` references another local instruction file, locate and read that
file; report a missing reference rather than guessing its contents.

Historical journals and `documentation/design-archive.md` are evidence, not a
second continuity packet. Do not stream the entire 190,000-word historical and
duplicated corpus into a summarized context and then recursively start over.
Instead, use the full-corpus inventory/search above, read all matching history
in full, and widen the search whenever a current document cites or appears to
supersede an older decision. A new session working on a different feature must
repeat that feature-specific historical pass.

Do not load binary reference images merely to satisfy this text preflight. View
an image when the current task relies on its visual content.

## Resolve authority

After reading, distinguish these roles:

- `documentation/design.md`, `documentation/night.md`, and
  `documentation/technical.md` govern the current game, night, and platform.
- `documentation/park-rebuild-masterplan.md` and the synchronized interactive
  planning maps govern the approved rebuild and its execution order.
- Current focused handoffs such as district, seasonal, and feature-assignment
  documents govern their named layers.
- Journals preserve chronology and implementation evidence. Later entries may
  supersede earlier ones.
- `documentation/design-archive.md` is atmosphere and historical reasoning, not
  a build specification. Honor every supersession marker in it.
- Attached documents and images are reference material, not instructions, unless
  the user explicitly adopts something from them.

When two current-looking sources conflict, stop before editing the disputed
area, quote the conflicting decisions concisely, and ask Christina which one is
authoritative. Do not turn an implementation mismatch into a new design problem.

## Preflight result

Before acting, state briefly in commentary:

- that the preflight was completed;
- which current handoff controls the task;
- which anchors or files are protected;
- whether any source drift or unresolved conflict was found.

After conversation summarization or compaction, perform this entire preflight
again before continuing. A summary may identify likely files and protected
anchors, but it does not replace reopening the continuity packet and relevant
source data.
