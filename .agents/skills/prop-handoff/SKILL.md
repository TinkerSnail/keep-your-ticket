---
name: prop-handoff
description: What to do when Christina hands over a prop (bench, bin, lamp, any furniture or small asset) — she says "handed back", "process it", "preview", "open it in Photoshop", "let's paint", "rebuild", "new prop", "start the <prop>", or asks where a prop stands. Also for any work on a prop between greybox and painted-in-game. Tells the session exactly which tool runs for each phrase, what to report, and what never to do, so no hand-off depends on remembering a past session.
---

# Prop hand-offs

Christina owns modelling and painting and does them by hand. Everything
mechanical between those is a button or a command, and this skill says which,
for each thing she says. The stages, tools and standards are in
`documentation/prop-pipeline.md`; where each prop stands is its row in
`documentation/asset-tracker.md`. **Read both before acting.** They, not
memory of an earlier session, say what happens next.

## 0. Orient (every time)

1. Tier 1 preflight, as `AGENTS.md` requires.
2. Read `documentation/prop-pipeline.md`, then the prop's row in
   `documentation/asset-tracker.md`.
3. If she didn't name the prop and more than one row is with her, ask which.
4. Check the files against the row: modification times of
   `assets/source/props/<prop>.blend`, `<prop>_source.blend`,
   `assets/source/textures/<prop>/<prop>_colour.psd` and `_colour.png`, and
   `assets/props/<prop>.glb`; `git status`. If the files and the row disagree,
   believe the files and say what differs.
5. Is her Blender or Photoshop open (`pgrep -x Blender`, `pgrep -f "Adobe Photoshop"`)?
   Commands read files **as saved**; unsaved work in an open app is not seen.
6. What have her buttons already done? Most steps are one duty with two ways
   to do it, her Blender panel button or your command. `prop-pipeline.md`,
   "Who does what", lists each with the evidence that it has run. Never
   repeat a step whose evidence is there; carry on from the next one.

## 1. What each phrase means

**Never ask her what to do next.** The row's stage and the files decide it;
the table below says what each stage's next step is. Any hand-over in her own
words ("saved", "done", "finished the pass", "I saved the psd") is the
hand-back for the row's stage: run it. Ask only when two props could be
meant, or when a step would change something of hers the table doesn't
cover (2026-09-25: she saved her first paint pass and was asked "preview or
handed back?"; the pipeline exists so that question never comes up).

| She says | Do |
|---|---|
| "new prop …", "start the …" | Stage 1 set-up (below), then the hand-off package. |
| "handed back", or that she saved, after modelling (row: model) | Model hand-back (below). |
| "open it in Photoshop", "let's paint" | `python3 tools/prop_handback.py <prop> --open` (the Blender panel's **Open texture in Photoshop** runs the same). |
| "preview" | `python3 tools/prop_handback.py <prop> --preview`; show her the renders. Her document and the game are untouched. |
| "handed back", "process it", or that she saved the PSD (row: paint) | `python3 tools/prop_handback.py <prop>`. With the save hook on (`tools/photoshop/live_update.sh status`) her save already sent the prop; the hand-back adds the tests and renders. If it refuses because the PSD has unsaved changes, ask her to save; never use `--allow-unsaved` unasked. |
| "I pressed Hand back", "handed back from the panel", or a hand-back folder newer than her last save | She ran it herself with the Blender panel's **Hand back**: **don't run it again.** Read the newest `documentation/screenshots/handbacks/<prop>-*/README.md` and report from it. If it stopped at a FAIL, fix that and run `prop_handback.py <prop>` once. |
| "rebuild", or `<prop>_source.blend` is newer than the working file | Rebuild game mesh (below), then the painted hand-back if there is a painting. |
| "commit" / "push" | Only then. Check `git status` for other sessions' work first; commit only this prop's files. |

**Stage 1 set-up** (`prop-pipeline.md` stage 1): `tools/maquette_export.gd` for
the greybox reference, `tools/blender/new_prop.py -- <prop>`,
`tools/blender/add_reference.py -- <glb>`, the prop's Godot scene wrapping the
GLB with any contract markers, and a card in `documentation/howto/`. The
hand-off package (working agreement in the studio chapter plan) is: one file to
open, set up, reference locked; one sentence on what to shape and what done
means; the constraints that bind; the card; frames of the starting state. Add
the tracker row: stage **model**, with **Christina**.

**Model hand-back:**
1. The prop sent after its last save? If `assets/props/<prop>.glb` is older
   than `<prop>.blend`, send it: `Blender --background <blend> --python
   tools/blender/prop_handback_blender.py -- send`.
2. Tests: `python3 tools/prop_handback.py <prop> --no-export` runs send,
   import, the tests and renders, without needing a PSD.
   The Godot scene: her first **Send to game** offers **Write Godot scene**
   when `scenes/world/park_furniture/<prop>.tscn` doesn't wrap the GLB. If it
   still doesn't, write it the same way (the `backless_timber_bench.tscn`
   pattern, markers from the blend), and ask before replacing a scene that
   exists: it is editor-owned.
3. Then the texture set-up, each step shown to her before the next:
   - **Make game mesh**, if there is no `<prop>_source.blend` yet: her button,
     or headless when her Blender doesn't hold the file: `Blender --background
     <prop>.blend --python tools/blender/prop_handback_blender.py -- make --save`.
   - **Unwrap** the source: `Blender --background <prop>_source.blend --python
     tools/blender/unwrap_parts.py -- --save`. Report any parts it couldn't
     classify: they need seams by hand. After the Rebuild, Check reports the
     UVs (overlaps other than mirror twins, folds, texel density, px/m):
     `Blender --background <prop>.blend --python
     tools/blender/prop_handback_blender.py -- check`; quote its UV line.
   - **Rebuild game mesh** (below), so the working file takes the unwrap.
   - **Canvas:** `tools/blender/paint_canvas.py` with the options for this prop
     (the bench's are its model; `--grain` assumes timber runs along x).
     Render it and let her approve the starting look before she paints.
   - Row: stage **paint**, with **Christina**. Then `--open`.

**Rebuild game mesh:** her panel button, or headless when her Blender doesn't
hold the working file: `Blender --background <prop>.blend --python
tools/blender/prop_handback_blender.py -- rebuild --save`. Report
its lines as they are: how far the shape moved, how many UV pieces kept their
place, and any "no painting yet" pieces (she paints those). Then Send to game
or the painted hand-back.

## 2. Never

- Commit or push without her word.
- Act in her open Blender or Photoshop without a yes for that task, except
  what only reads it: `--preview` and the hand-back export work on a
  duplicate and close it.
- Re-bake a painted canvas. `paint_canvas.py --overwrite` is for a canvas
  nobody has painted.
- Change anything visible she didn't ask for. If her painting holds something
  that belongs to one copy only (gum, a stain, a sticker), point it out and
  ask. The dressing route is `prop-pipeline.md` stage 7.
- Edit her PSD beyond adding a clearly named layer she approved (e.g. "gum
  patch (Claude)"), and never save it before she has seen the result.

## 3. The report

After every hand-off, in this order:
1. What ran: the tool's `ok`/`FAIL` lines, or a summary of them.
2. What changed that she can see, measured: for a painting, pixels changed
   since the last commit and where.
3. The renders folder (`documentation/screenshots/handbacks/<prop>-…`); send
   the images.
4. Anything of hers altered: normally "nothing".
5. Decisions for her, if any.
6. Last line: if you touched a file she has open, what to save. Otherwise
   "Say 'commit' when it's right."

Then update the prop's tracker row (stage, holder, last hand-back, next step)
and append the journal entry (`AGENTS.md`: at most 300 words).
