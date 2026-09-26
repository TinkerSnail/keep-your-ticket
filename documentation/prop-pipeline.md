# Prop pipeline

How a prop goes from greybox to painted and placed in the game. Proven end to
end on the plaza bench on 2026-09-24/25 (commits `51ad29b` to `4409fd5` on
`chapter/plaza`). This is the prop section of the studio handbook's Part V,
"Pipeline and technology", written ahead of it; the handbook absorbs it when
Part V is drafted. The plan it follows is `studio-chapter-plan-2026-09-24.md`
(asset stages, tools 1–4, texture standards, working agreement).

**Hand-offs.** When Christina hands a prop over ("handed back", "process it",
"preview", "let's paint", "rebuild", "start the …"), the session follows the
`prop-handoff` skill (`.agents/skills/prop-handoff/SKILL.md`, shared by Claude
and Codex): which tool runs for each phrase, what to report, and what never to
do. Where each prop stands is its row in `asset-tracker.md`, read before and
updated after every hand-off.

Each stage is marked:
- **Working:** done on the bench, with a tool or button, checked.
- **Rough:** done on the bench, but by hand or by an agent's throwaway script;
  it has to become a tool before the next prop.
- **Missing:** in the plan, not built.

## At a glance

| # | Stage | Who | How | Status |
|---|---|---|---|---|
| 1 | Maquette reference | Agent | `maquette_export.gd`, `new_prop.py`, `add_reference.py` | Working |
| 2 | Block-out and model | Christina | Blender, **Show reference**, **Check**, **Send to game** | Working |
| 3 | Unwrap | Agent | `unwrap_parts.py` on `<prop>_source.blend` | Working |
| 4 | Game mesh | Christina or agent | **Make game mesh**, **Rebuild game mesh** | Working |
| 5 | Canvas | Agent | `paint_canvas.py` | Working; re-baking is rough |
| 6 | Paint | Christina | Photoshop PSD (or Blender texture paint); the Blender panel's Photoshop box, `--preview` | Working |
| 7 | Dressing | Agent, Christina's call | decal cut-out, per-prop dressing script | Rough |
| 8 | Integrate | Christina's button or agent | **Hand back** (Blender panel), `tools/prop_handback.py` | Working |
| 9 | Review and commit | Christina decides | renders, the game, commit | Rough |

The plan's asset stages map onto these: maquette (1), block-out and model
(2), UV (3–4), texture (5–7), integrate (8), review (9).

## Who does what: the Blender panel and the agent

The Keep Your Ticket Blender extension (`tools/blender/extensions/kyt_tools/`,
card `howto/install-blender-panel.md`) puts the mechanical steps on buttons,
and the Photoshop save hook runs on every save of a canvas PSD. Most duties
can be done two ways, by Christina's button or by the agent's command.
Whichever ran first did it: before running a command the agent looks for the
evidence, and never repeats a step a button already did (2026-09-25: Make
game mesh, Send to game and the Godot scene were each nearly done twice).

| Duty | Christina's button | The agent's command | Evidence it has run |
|---|---|---|---|
| Check the prop | **Check** | Send runs it first | none needed: cheap, run it freely |
| Send to game | **Send to game** | `prop_handback_blender.py -- send` | `assets/props/<prop>.glb` newer than the saved `.blend` |
| Godot scene wrapping the model | **Write / Replace Godot scene** (offered after a Send) | edit `scenes/world/park_furniture/<prop>.tscn` | the scene instances `res://assets/props/<prop>.glb` and holds its contract markers |
| Unwrap the parts | none yet | `unwrap_parts.py -- --save` on `<prop>_source.blend` | every source part marked `kyt_unwrapped` |
| Make game mesh | **Make game mesh** | `prop_handback_blender.py -- make --save` | `<prop>_source.blend` exists; `export` holds one `kyt_game_mesh` object |
| Rebuild game mesh | **Rebuild game mesh** | `prop_handback_blender.py -- rebuild --save`, only when her Blender doesn't hold the file | the game mesh records `kyt_parts` (it took the parts' own unwrap) |
| Canvas | none | `paint_canvas.py` | `assets/source/textures/<prop>/<prop>_colour.png` exists |
| Open or make the PSD | **Open texture in Photoshop** | `prop_handback.py <prop> --open` | `<prop>_colour.psd` exists |
| A perforated PSD's hole layers | made with the PSD by **Open texture** | `prop_handback.py <prop> --hole-layers` after re-cutting holes | the PSD has "UV guide: holes (Claude)" |
| Texture to the game on each save | the save hook (Photoshop box: **On**) | `prop_handback.py <prop>` covers it | an entry after her save in `~/Library/Logs/Keep Your Ticket/live_send.log`; PNG and GLB newer than the PSD |
| Texture on the model in Blender | **Reload textures on save** | none | the panel's "reloaded … from disk" line |
| Tests and renders (the hand-back) | **Hand back** | `prop_handback.py <prop>` | a `documentation/screenshots/handbacks/<prop>-<time>/` newer than her last save |
| UV guide show/hide, patch layer | the panel's Photoshop box | none | none needed |
| Report, tracker row, journal, commit | none | the agent; commit only on her word | none needed |

- **A pressed button is done.** Read its evidence and carry on from the next
  step. If its lines ended in FAIL, fix the cause and run the command once.
- **Order the buttons don't enforce yet:** unwrap before Make game mesh. If
  she pressed Make game mesh first, don't make it again: unwrap
  `<prop>_source.blend`, then Rebuild game mesh.
- **Her open app holds the file:** when her Blender or Photoshop has the file
  a command would write, work inside her open app and leave the save to her,
  or ask her to save and close it. Never write a file behind her open app;
  she then has to revert, and her next save undoes the work.
- **A new button or command** gets its row here, a line on the card and a row
  in the `prop-handoff` skill's table.

## The stages

### 1. Maquette reference (agent) — working

The greybox the game uses today becomes the prop's starting point.
- `tools/maquette_export.gd` writes the greybox as
  `assets/source/props/reference/<prop>.glb` in the prop's own frame (on the
  ground, at the origin, facing +Z).
- `tools/blender/new_prop.py -- <prop>` makes `assets/source/props/<prop>.blend`
  with the `reference` (locked), `authored` and `export` collections.
- `tools/blender/add_reference.py -- <glb>` puts the reference in, with any
  contract markers (for a bench, `seat_l`/`seat_r`).
- The prop's Godot scene (`scenes/world/park_furniture/<prop>.tscn`, editor-owned)
  wraps the GLB and holds the contract markers the crowd and tests read. The
  first **Send to game** offers **Write Godot scene** when it doesn't wrap the
  GLB yet (the `backless_timber_bench.tscn` pattern, `seat_l`/`seat_r` from the
  blend). An existing scene is replaced only after the panel's confirmation,
  which says what it holds; its description is kept.
- A hand-off card goes to Christina (`documentation/howto/`).

**Done when:** the file opens set up, with the reference locked and the card
written.

### 2. Block-out and model (Christina) — working

Christina shapes the prop from parts in `export`: boxes, cylinders and bent
tubes, each its own object. **Check** (sidebar, N) flags unapplied scale,
floating props, the triangle budget and a drifting seat contract. **Send to
game** writes `assets/props/<prop>.glb`; every copy in the game updates.
**Show reference** hides or shows the greybox copies in `reference`; the floor
and the seat markers stay. Cards: `model-the-plaza-bench.md`, `change-a-prop.md`.

**Done when:** Check is all clear, the prop is sent and saved, and she says
"handed back". The agent runs `seat_test` (for seats), `clearance_test`,
`budget_test` and `ground_contact_test`, and commits.

### 3. Unwrap (agent) — working

```
Blender --background assets/source/props/<prop>_source.blend --python tools/blender/unwrap_parts.py -- --save
```
Runs on the source file, the parts still separate. Each part is laid out
whole, at true scale, long side along U:
- **Boards and boxes:** cut round the ends and along the back-bottom edge, so
  grain wraps over top, front and back.
- **Cylinders:** cut round the caps and down the back.
- **Rings:** cut along the inside (`--ring-seam=inboard` puts it on the side
  facing the seat).

Mirrored by default: a right-hand part shaped like a left-hand one takes its
twin's layout (`--no-mirror` to opt out). Parts it can't classify are cut at
sharp edges and listed for seaming by hand.

**Done when:** every part is classified, twins paired, and stretch measured
exact on flat parts (rings within about ±10%).

### 4. Game mesh (Christina's button, or agent) — working

**Make game mesh** saves `<prop>_source.blend` (every part, editable), then
fuses the parts into one mesh in the working file, deletes hidden faces, keeps
the unwrap and packs it, and records each face's part (`kyt_part`). Card:
`make-the-game-mesh.md`.

**Done when:** the pieces don't overlap (except mirror twins), the stretch
matches the unwrap, and the shape is within 0.5 mm of the parts. Once there is
a game mesh, **Check** measures the first two (R8, `uv_check.py`): pieces
overlapping other than mirror twins, pieces folding over themselves, parts off
the prop's texel density, and the px per metre at the canvas size. A face the
fuse left buried against another, facing the other way, maps to the same
place and is not an overlap. The backless bench: 13 mirror pairs, nothing else
overlapping, 814 px/m at 2048; the plaza bench: 23 pairs, 576 px/m.

**Rebuild game mesh** (2026-09-25) is for after the source parts change. It
fuses them again in the working file and swaps the result into the existing
game-mesh object, which keeps its name and material. Every UV piece whose
shape is unchanged (matched by part name and shape, so a moved part still
matches) goes back exactly where it was, so painting stays aligned. Only new
or reshaped pieces are packed into the space left, and they have no painting
yet. It reports how far the shape and the unwrap moved. Tested on the bench:
with the parts unchanged it renders as before to within 1/255; with a bolt
moved 1 cm, 181 pieces stay put, 5 are repacked, and 99% of the surface lines
up within 0.9 px.

### 5. Canvas (agent) — working, re-bake rough

```
Blender --background assets/source/props/<prop>.blend --python tools/blender/paint_canvas.py -- <options> --save
```
Bakes the starting texture and replaces the prop's materials with one:
- `<prop>_colour.png` (2048)
- `<prop>_orm.png` (1024; roughness and metal)
- `<prop>_uv_guide.png` (piece outlines)

All go in `assets/source/textures/<prop>/`. The options set the starting look:
- `--grain`: timber as solid wood, rings round the length.
- `--knots <parts>`: the hand-placed knots in `KNOTS`.
- `--wear <parts>`: seat edges worn where people sit.
- `--chips <parts:density>`: a few grey-iron chips on edges.
- `--dings <parts>`: chips on sky-facing tops.
- `--ground <parts>`: a dirt band and dark spots at the paving.
- `--weather <parts>`: the full treatment, not used on the bench.
- `--perforate <parts>`: expanded-metal diamond holes through those parts'
  broad faces, into the colour PNG's alpha (glTF alpha mask, Godot alpha
  scissor; collision stays solid) and `<prop>_holes.png`. A flattened PSD has
  no alpha, so `tools/blender/apply_holes.py` puts the holes back after every
  export: in the hand-back and in the Photoshop save hook. The perforated
  bench, 2026-09-25. A perforated prop's PSD carries two locked layers
  (`tools/photoshop/hole_layers.jsx`, added by `--open`): the canvas colour
  under `paint`, so a see-through spot exports as metal, and the holes as a
  translucent "UV guide: holes (Claude)" on top. To change the pattern, edit
  the `HOLE_*` numbers, run `paint_canvas.py --holes-only --perforate <parts>`
  (colour kept, holes cut again), then `prop_handback.py <prop> --hole-layers`
  and she saves the PSD.

Each effect's strength is a number at the top of the script. The bench's full
command is in `howto/paint-the-plaza-bench.md`. A canvas someone has painted
is never rebaked; `--overwrite` is for an unpainted one only.

**Done when:** the baked colours equal the materials' and the bench renders
as before plus the effects. Christina approves the look.

**Rough:** a re-bake needs the three-material mesh put back first (R3), and
the options live in a card rather than on the prop (R2).

### 6. Paint (Christina) — working

**Open texture in Photoshop** (Blender panel), or `python3
tools/prop_handback.py <prop> --open`, opens `<prop>_colour.psd` in Photoshop, making it first if
there isn't one, with her `paint` layer under a
locked `UV guide` layer. An existing PSD is never replaced. She paints on it or on new layers. Blender texture
paint on the model works too. Mirrored parts share paint: a chip on one arm
appears on the other. Card: `howto/paint-the-plaza-bench.md`.

**Saving updates the prop** (2026-09-25). With the save hook on
(`tools/photoshop/live_update.sh on`, which Photoshop keeps across restarts
as a "Save Document" script event), each save of a canvas PSD runs
`tools/photoshop/on_save.jsx`. It writes `<prop>_colour.png` (the hand-back's
own export, about 3 s in which Photoshop waits) and starts a headless Send to
game from the saved `.blend`, logged to
`~/Library/Logs/Keep Your Ticket/live_send.log`. The Blender panel's **Reload
textures on save** reloads the texture a second later without marking the
file modified, and Godot re-imports the prop the next time its window is
focused. The tests and renders still wait for stage 8.

**The Photoshop box** in the Blender panel (2026-09-25, once the prop has a
canvas): **Open texture in Photoshop**; **UV guide Show/Hide** and **Add
patch layer** (a named empty layer, `<name> patch`, under the guide, for
dressing, stage 7 step 3), which act on the open canvas through
`tools/photoshop/canvas_tools.jsx` and never start Photoshop or save the PSD;
and **Save hook: On/Off** with its switch. The state is read from
Photoshop's own settings file (`tw0001.dat`, rewritten as soon as a script
event changes), so showing it never starts Photoshop; switching it runs
`live_update.sh`. A UXP panel inside Photoshop was built first and dropped the
same day at her choice: UXP can't start a process (Adobe's shell API opens
only a file or a URL, with no arguments), and reaching ExtendScript from it
takes batchPlay's undocumented "AdobeScriptAutomation Scripts" event.

Her words:
- **"Preview":** `prop_handback.py <prop> --preview` renders her work in
  progress (saved or not) on the prop from a flattened duplicate. Her
  document, the PNG and the game are untouched.
- **"Process it"**, **"handed back"** or that she saved: stage 8 runs.

### 7. Dressing (agent, Christina decides) — rough

Anything that belongs to one copy of a prop, not every copy, comes out of the
shared texture: gum, stains, litter marks. That's the texture standard's
dressing layer.
1. **Find it:** compare her painting with the baked canvas for compact spots
   that stand out locally. Hue alone misses a tan gum on tan wood.
2. **Cut it out:** as a decal in `assets/source/textures/dressing/`
   (`README.md` lists size and origin). Its transparency is how far each pixel
   differs from the clean wood along the grain on both sides.
3. **Patch it:** on its own layer in her PSD ("gum patch (Claude)"; the
   Blender panel's **Add patch layer** makes one under the guide), from wood
   along the grain on a side free of the spot. She approves before anything is
   saved.
4. **Place it in the game:** by a dressing script on the prop scene. The
   bench's `gum` node (`bench_gum.gd`) gives each bench none to three pieces,
   seeded by where it stands, in spots found by raycasting its own collision.
   `tools/gum_shapes.py` makes tintable grey shapes from her painted ones.

**Rough:** steps 1–3 are throwaway scripts, and step 4 exists for gum on
benches only (R9).

### 8. Integrate (agent) — working

After "process it" or "handed back", or from the Blender panel's **Hand
back** (refused while the `.blend` has unsaved changes), which runs the same
command in the background and shows its lines:

```
python3 tools/prop_handback.py <prop>
```
It runs these steps in order, stops at the first failure, writes a report
with four renders into `documentation/screenshots/handbacks/<prop>-<time>/`,
and never commits:
1. Export the PSD flattened, guide hidden, over `<prop>_colour.png`, and check
   it matches what she approved.
2. `python3 tools/optimize_png.py <png>`: lossless, pixel-identical or it
   leaves the file alone. Blender embeds the PNG's own bytes in the GLB, so a
   smaller PNG means a smaller GLB.
3. Send to game (the panel's code, headless).
4. `Godot --headless --path . --import`, then check that Godot's extracted
   copy (`assets/props/<prop>_<prop>_colour.png`) matches the export pixel for
   pixel and is still VRAM-compressed with mipmaps.
5. Tests: `seat_test.py`, `clearance_test`, `budget_test`,
   `ground_contact_test` (known failures only on the east-wing ramps).

Step 1 refuses a PSD with unsaved changes (`--allow-unsaved` overrides), and
`--no-export` uses a PNG exported by hand. If Blender is open, the send uses
the file as saved. Step 4 puts Godot's import settings right if they aren't,
but only after the first extraction (R6).

### 9. Review and commit (Christina decides) — rough

The agent renders the prop from a few angles (walking distance, close, the
painted details) and she looks in the running game. Commit only on her word;
push when she asks. Her PSD and the decals go into Git LFS.

**Rough:** renders are ad-hoc Blender scripts, not her `review_*` cameras
(R7).

## Standards applied

From the plan's texture standards (2026-09-24):
- **One material per prop:** each placement is one draw.
- **Mirroring on:** left and right parts share texture.
- **Map set:** colour (painted) and a packed ORM; the normal map is not
  baked yet (M1).
- **Texel density:** 256 px per metre by default. The bench is a recorded
  exception at about 576 px per metre on a 2048 colour map (hero props, her
  call per prop).
- **Dressing, not texture,** for anything one copy has and the others don't.

The park furniture trim sheet (`trim_map.py`, `trim_sheet_template.py`) is set
aside, not retired: tiling made no sense for the curved bench, and it may
suit long straight things later.

## Rough and missing

**Rough (turn into tools before the next prop):**
- **R1. Rebuild game mesh.** Done 2026-09-25 (stage 4). Still open: a new or
  reshaped piece gets no painting. A projection bake from the old mesh would
  carry it across.
- **R2. Canvas options on the prop.** Store the `paint_canvas.py` options in
  the working file and re-read them, instead of a command copied into a card.
- **R3. Re-bake without swapping meshes.** `paint_canvas.py` should rebuild
  the per-part materials from `kyt_part` itself, rather than needing the
  three-material mesh put back.
- **R4. Photoshop scripts.** Done for open, export and preview
  (`tools/photoshop/open_canvas.jsx`, `export_canvas.jsx`, run by
  `prop_handback.py`), and a patch layer for dressing (`canvas_tools.jsx`,
  the Blender panel's **Add patch layer**, 2026-09-25).
  Photoshop's Place lands off-target, so every placed layer is moved to its
  known bounds.
- **R5. One hand-back command.** Done 2026-09-25: `tools/prop_handback.py`
  (stage 8).
- **R6. Texture import defaults.** The hand-back now corrects the extracted
  textures' `.import` files after the first extraction. A true default belongs
  with tool 4's post-import script.
- **R7. Review frames.** Render from her `review_*` cameras (tool 10) instead
  of ad-hoc Blender views.
- **R8. UV checks as a tool.** Done 2026-09-25: **Check** (`uv_check.py`)
  reports overlaps other than mirror twins, folds, parts off the texel density
  and the px per metre. Twin pairing is not checked on its own: a right-hand
  part the unwrap didn't pair keeps its own space and passes.
- **R9. A dressing layer.** A general decal library and per-prop dressing
  spots instead of a gum-only bench script. Also a cut-out tool for step 7.
- **R10. Blender extension reload.** Her running Blender keeps the old
  extension code until it reloads. Since 2026-09-25 switching the add-on off
  and on (Preferences › Add-ons) is enough: `__init__.py` reloads its own
  modules, where Blender reloads only `__init__.py`. Say which whenever the
  extension changes.

**Missing (in the plan, not built):**
- **M1. Normal map** baked from `<prop>_source.blend`.
- **M2. Ambient occlusion** into the ORM's red channel (white today).
- **M3. Material library** (tool 4): `assets/materials/`, and a post-import
  script mapping slot names to library materials.
- **M4. The rest of the paint-over kit** (tool 3): curvature and colour-ID
  bakes (`kyt_part` makes colour-ID easy), and a PSD that opens in Procreate
  too.
- **M5. The look test:** the first prop painted over a photo base as well as
  by hand, for Christina to choose the house look.
- **M6. Texture memory in `budget_test`.**
- **M7. Asset tracker** (tool 5). Started 2026-09-25 as `asset-tracker.md`,
  one row per prop.
- **M8. Paint-over capture loop** (tool 6) and review renderer (tool 10).
- **M9. The phase gate:** a second prop (the bin) through this pipeline with
  agents on set-up only.

## Traps found on the bench

Each cost time once. The fix is in the tool unless noted.
- **Exact booleans scramble UVs.** Make game mesh gives each fused face its
  UVs back from the part face it was cut from, and snaps corner UVs equal (the
  packer joins pieces only where UVs are identical).
- **Choosing the source face on a curve by normal picks a neighbour.** Choose
  by distance; normals only break ties.
- **Hand-placed twins aren't exact mirrors.** Pair by shape about each part's
  own centre, not by position.
- **A shiny chip reads as a dark speck.** Chips are dull grey iron.
- **Wear spread over a face reads as mould.** Keep it on the edges.
- **Placing by hand-typed geometry goes stale.** The gum finds its spots on
  the model instead.
- **zsh doesn't split an unquoted `$FLAGS`.** Two bakes silently ran with no
  options. Use `${=FLAGS}` (agent practice).
- **Outlining a spot against one shifted copy counts the copy's own image of
  the spot.** Outline against both sides.
- **Changes made in her open app exist only until she saves.** Put the save
  line last in the report (agent practice).
- **After the canvas, Solid view looks untextured.** Solid shading with colour
  set to Material shows each material's flat viewport colour, and the one
  canvas material's is default grey (the three part materials had theirs
  matching). Set Solid's colour to Texture, or use Material Preview
  (backless bench, 2026-09-25).
- **Blender from the Dock has only the system's python3,** which has no
  Pillow here. The panel's buttons take the first python3 that imports it.
- **A save made by a script fires no script event,** UXP's `save()` included,
  so the save hook only follows her own Save.
- **Asking Photoshop anything over AppleScript starts it,** `live_update.sh
  status` included. The panel reads the hook's state from Photoshop's
  settings file instead.
- **Photoshop's helper LogTransport2 lives inside the app and outlives it,**
  so "is Photoshop running" matches the app's own program, not the bundle.
- **UXP's layer `visible` setter hid the active layer, not the locked guide
  asked for** (Photoshop 27.4). Show and hide by layer id.
- **ExtendScript evaluates an unbracketed nested `?:` wrongly,** calling both
  branches. Use if/else.
