# tools

Everything in here is development only. None of it ships, none of it runs as
part of the game, and nothing in `scenes/` or `scripts/` may import from it.

This file exists because the list of what these are lived in `CLAUDE.md`, which
is gitignored — so it was per-machine, and by the time anyone noticed, ten of
the twenty-eight scripts here had never been written down anywhere. If you add
a tool, add its line here. `CLAUDE.md` explains *why* each one exists and what
it caught; this is the index.

## Two ways to run, and picking the wrong one fails silently

**`extends SceneTree` → `--script`.** The generators and `clearance_test.gd`.
Wrapping one of these in a scene does nothing at all: `_initialize` never fires
and the process sits there looking like a hang.

```bash
/Applications/Godot.app/Contents/MacOS/Godot --headless --path . --script res://tools/gen_props.gd
```

**`extends Node` → `tools/run.tscn`.** Everything else — this directory turns
over, so it is named as "everything but the three above" rather than counted. Godot can only run a scene, and a tool that names an autoload at the
top level *must* have one, because `--script` compiles before autoloads
register — so `ParkClock` or `ParkSections` dies at compile without running a
line. `run.tscn` is that scene. Name the tool after a bare `--`:

```bash
/Applications/Godot.app/Contents/MacOS/Godot --headless --fixed-fps 60 --path . tools/run.tscn -- footprint_walk_test
```

Run it with no tool named and it lists what it can start, and which ones want
`--script` instead. `capture.tscn` and `west_capture.tscn` still ship their own
wrappers and need no argument.

This replaced writing a one-node wrapper by hand and deleting it afterwards. If
you find a stray `_*.tscn` at the repository root, it is left over from that
and is not tracked.

**`--headless` forces the dummy renderer.** Fine for anything that only asserts
or writes `.tscn`. Fatal for anything that saves a PNG — the run completes, the
script reports success, and every image is a blank few-KB file. Capture tools
and probes need a real renderer:

```bash
open -n -a /Applications/Godot.app --args --path "$PWD" tools/run.tscn -- west_capture
```

The path must be absolute: `open` goes through LaunchServices and the child does
not inherit the shell's working directory. Do not pass `--quit-after` to a
capture run — it counts frames and will cut the settle timer short. Output lands
in `~/Library/Application Support/Godot/app_userdata/Keep Your Ticket/`.

Piped stdout from headless Godot is buffered until the process exits, so reading
the log of a run still in progress tells you nothing. Redirect and read after.

See `.agents/skills/run-the-park/SKILL.md` for the containerised route, which is
the same rules with Xvfb and a fetched binary.

## Generators

Generated output is checked in, but it is no longer the scene you edit. The
familiar scenes in `scenes/world/` are stable, editor-owned wrappers. Each one
inherits a replaceable source with the same name from
`scenes/world/generated/`, and `gen_props.gd` writes only those nested sources.

For a visual edit, open the familiar wrapper — for example
`scenes/world/plaza_skyline.tscn`, never the copy under `generated/`:

1. Move, rotate or change a generated child in the inspector. Godot records a
   property override in the wrapper, so regeneration can rebuild the source
   without undoing the change.
2. Put new hand-authored nodes under `authored_additions`. That node and its
   children belong wholly to the wrapper and are never generated.
3. Delete a hand-authored node normally. An inherited generated node cannot be
   safely removed from the wrapper; hide it and disable its collision there, or
   promote/remove that object in the generator when the deletion should become
   structural.

`plaza.tscn` and `park_world.tscn` are hand-authored directly. The three crowd
scenes remain pure derived output and are not visual-authoring surfaces. A
generator run is expected to change files only inside `scenes/world/generated/`
plus those crowd scenes; a familiar world wrapper changing is a regression.

| tool | what it builds |
|---|---|
| `gen_props.gd` | The ground textures and eighteen generated world sources beneath the stable wrappers: established props/places plus groundworks, circulation, routes, program and landscape. Pass `--groundworks-only` after Godot's bare `--` to rebuild only `park_groundworks.tscn` when a terrain consequence changes. Everything is still built in the usual order, because the seam ordinal depends on how many scenes have begun and groundworks also needs work staged much earlier; only the other scenes' writes are skipped, which is what makes the groundworks it produces identical to a full run's. Textures and materials are still written. It does not write `west_far` or `terraces_far`; the persistent world uses the real places. **The full-run order is load-bearing** — each scene gets a seam seed five on from the last, so the two retired seed slots remain until that system is replaced. Run `coplanar_test.py` after touching the order. |
| `export_world_source.py` / `.sh` | A mounted world GLB from its Blender master, `assets/source/<name>.blend` to `assets/<name>.glb`; the range by default, the city when named. Meshes exported under its own name with the `-col` hint, boulders baked into one mesh per 250m cell with a surface per material, collision derived from the visible meshes. Runs through Blender, never saves the master, and refuses a master that still holds a `-colonly` object. |
| `blender/extensions/kyt_tools/` | The Keep Your Ticket Blender extension: a sidebar panel with **Show reference** (the locked greybox copies in `reference` on or off; the floor and the seat markers stay; `reference.py`), **Open texture in Photoshop** (`prop_handback.py <prop> --open`) and **Hand back** (`prop_handback.py <prop>`), both in the background with each `ok`/`FAIL` line and the renders folder shown in the panel, Hand back refusing a file with unsaved changes (`handback.py`, which picks a python3 that has Pillow: Blender started from the Dock sees only `/usr/bin/python3`), a Photoshop box once the prop has a canvas (**UV guide** Show/Hide and **Add patch layer** on the canvas open in Photoshop through `photoshop/canvas_tools.jsx`, and **Save hook** On/Off, its state read from Photoshop's settings file so showing it never starts Photoshop, switched through `photoshop/live_update.sh`; `photoshop.py`), **Reload textures on save** (on by default: the prop's textures reload a second after their files change, as when the canvas PSD is saved with the Photoshop save hook on; the file isn't marked modified), **Check** (scale, ground contact, materials, the per-placement budget from `budget_test`, and the seat contract when `seat_l`/`seat_r` markers exist; once there is a game mesh, its UVs too: pieces overlapping other than mirror twins, pieces folding over themselves, parts off the prop's texel density, and a note of the px per metre at the canvas size, from `uv_check.py`) **Rebuild game mesh** (after the source parts change: fuses them again, keeps the object and its material, puts every unchanged UV piece back where it was so painting stays aligned, packs only new or reshaped pieces, and reports how far the shape and the unwrap moved), **Make game mesh** (the first time only: saves the file as `<name>_source.blend`, the original with every part, then fuses this file's parts with an exact self-union, deletes faces inside other parts and on the floor, dissolves the union's flat slivers, unwraps, and sets the Stage to Texture; the file keeps its name so it still sends to the same GLB), and **Send to game**, which writes `assets/source/props/<name>.blend` to `assets/props/<name>.glb` with every part in `export` merged into one object (modifiers applied, one surface per material, UVs kept), collision derived through its `-col` name (parts marked `kyt_collision=none` go into a separate `_visual` object), and never saves the .blend; if `scenes/world/park_furniture/<name>.tscn` doesn't wrap the GLB yet, it offers **Write Godot scene** (the `backless_timber_bench.tscn` pattern, `seat_l`/`seat_r` from the blend), and an existing editor-owned scene is replaced only after a confirmation that says what it holds (`godot_scene.py`). Installed once as a Blender local repository pointing at `tools/blender/extensions`; `documentation/howto/install-blender-panel.md` walks through it. |
| `blender/new_prop.py` | A new prop file from the template: `assets/source/props/<name>.blend` with metric units and the `reference` (locked, never exported), `authored` (never exported) and `export` collections. Refuses to overwrite. Run through Blender with `-- <name>`. |
| `blender/add_reference.py` | Puts a maquette reference GLB into a prop file's locked `reference` collection, replacing an earlier import; contract markers such as `seat_l`/`seat_r` keep their names so Check finds them. Saves the prop file, so only for files an agent prepared. Run through Blender on the prop file with `-- <glb>`. |
| `maquette_export.gd` | One greybox prop handed to Blender: the top-level parts of a scene whose names start with a prefix, CSG baked to meshes, moved into the prop's own frame (on the ground, at the origin, facing +Z) and written as `assets/source/props/reference/<name>.glb`. `--whole` takes every mesh of an already hand-built prop scene instead (its own frame kept, instance material overrides baked onto the meshes so they survive glTF), `--markers <scene>` brings that scene's Marker3Ds as named empties, `--also <scene>` an existing version 2.5 m along +X, `--floor W D` a floor plane, `--set <property>=<value>` (repeatable) sets the scene root's exports before it builds, `--courses` writes its Path3Ds to `<name>_courses.json`, `--mount <name>` an empty at the origin for a hanging prop (a palm crown's `trunk_top`, which Check reads). Through `run.tscn`. |
| `blender/add_courses.py` | A scene's Godot courses (from `maquette_export --courses`) as Bezier curves in a prop file's `authored/courses`, same points and handles, shared curve data kept shared; reports each curve's distance from Godot's baked points. `--blades` (palm crown): one blank blade per frond kind in `authored/blades` and one frond per course in `export`, bent along it by the `kyt_course_blade` geometry-nodes group, plus the `heart`. `--dead N` adds N brown dead fronds hanging from `course_old_0`'s curve (works on a file that has its courses). Marks the crown non-colliding, `kyt_keep_parts` (Send keeps each part its own node, with its custom properties as glTF extras) and `kyt_godot_scene`. Never replaces her curves, blades or fronds. Run through Blender on the prop file with `-- <json> [--blades] [--dead N]`. |
| `_palm_placement_migration.gd` | One-off, run 2026-09-25: turned what `coastal_palm_replacements.gd` built at the 34 generated palm feet into editor-owned `coastal_palm.tscn` placements in `approach_palms.tscn` and `boardwalk_palms.tscn`, and checked each trunk, crown seat and bed landed within 0.1 mm. The controller was retired the same day (in git at `58c9ca8`), so it cannot run again. Through `run.tscn`. |
| `trim_sheet_template.py` | A trim sheet's painting template from its layout file (`assets/source/textures/<sheet>/<sheet>.layout.json`, the one source for where every strip is): `<sheet>_base.png` with each strip's starting colour, never overwritten once it exists, and `<sheet>_guide.png`, a transparent layer of strip boundaries, notes, metre ticks, bleed margins and tiling seam markers. Plain Python with Pillow. |
| `blender/unwrap_parts.py` | Unwraps a prop's source parts for its own painted texture, each part whole: seams on the hidden side by shape (a box cut round its ends and along its lowest-backmost long edge, a capped cylinder round its caps and down its back, a ring along its inside and across where it meets another part), laid flat by Blender's unwrap at true scale with the long side along U, and marked `kyt_unwrapped` so Make game mesh keeps the unwrap through the fuse. Mirrored by default: a right-hand part whose shape mirrors a left-hand one's takes its twin's layout (`--no-mirror` to opt out). Run through Blender on `<prop>_source.blend` with `-- [--ring-seam=inside|inboard] [--no-mirror] [--save]`. |
| `blender/paint_canvas.py` | A prop's paint canvas and its one material, on the game-ready working file: bakes each material's colour into `assets/source/textures/<prop>/<prop>_colour.png` (default 2048) and its roughness and metalness into `<prop>_orm.png` (default 1024, occlusion/roughness/metal in R/G/B), draws `<prop>_uv_guide.png` (piece outlines, transparent), then replaces the prop's materials with one that reads both. `--grain` bakes timber as solid wood (rings round x); `--knots part` lets those parts carry the hand-placed knots in `KNOTS`, rings bending round them; `--wear part` wears seat boards' top edges pale where people sit, most on the front edge; `--chips part,part:0.4` puts a few grey-iron chips on the edges of those parts' painted iron (`:0.4` thins them); `--dings part` adds chips across their sky-facing tops; `--ground part,part` adds rust and dirt climbing 5 cm from the paving, with a few near-black dirt spots below 12 cm; `--weather part,part:0.4` is the full treatment (faded tops, hand wear, chips, rust, ground-line rust and dirt, crevice grime; `:0.4` scales a part's rust streaks), found through the `kyt_part` face record Make game mesh leaves. `--holes-only --perforate …` cuts them again on an existing canvas (after a change to `HOLE_*`), colour kept. `--perforate part,part` cuts expanded-metal diamond holes through those parts' broad faces into the colour PNG's alpha (clipped: glTF alpha mask) and writes `<prop>_holes.png`. The metal effects apply to any material but timber, where the part lists say. Refuses to overwrite a colour or ORM PNG unless `--overwrite` (an unpainted canvas only); `--guide-only` redraws the guide. `-- [--size N] [--orm-size N] [--grain] [--knots …] [--wear …] [--chips …] [--dings …] [--ground …] [--weather …] [--perforate …] [--overwrite] [--guide-only] [--save]`. |
| `gum_shapes.py` | Neutral gum shapes for the bench gum dressing: reads Christina's painted `assets/source/textures/dressing/gum_*.png` and writes `assets/props/dressing/gum_shape_*.png`, the same shape, shading and shadow in light grey so the game can tint them any colour. Run after repainting or adding a gum. `python3 tools/gum_shapes.py` |
| `prop_handback.py` | One hand-back for a painted prop (stage 8 of `documentation/prop-pipeline.md`): exports the saved PSD through Photoshop (flattened, guide hidden; refuses unsaved changes), shrinks the PNGs, sends the saved `.blend` headless, imports in Godot, checks Godot's extracted textures match pixel for pixel and are VRAM-compressed with mipmaps (putting the import setting right if not), runs `seat_test`, `clearance_test`, `budget_test` and `ground_contact_test` (known east-wing failures pass), and renders four views into `documentation/screenshots/handbacks/<prop>-<time>/` with the report as README. Never commits. `--open` opens (or makes) the prop's canvas PSD in Photoshop; `--preview` renders the open PSD's work in progress into `handbacks/<prop>-preview-<time>/` without sending anything. `--hole-layers` refreshes a perforated prop's hole layers in its PSD. `python3 tools/prop_handback.py <prop> [--no-export] [--allow-unsaved] [--no-tests] [--no-renders] | --open | --preview | --hole-layers` |
| `blender/apply_holes.py` | Puts a perforated prop's holes back into its colour PNG after an export (a flattened PSD has no alpha): alpha from `<prop>_holes.png`, each hole's colour carried in from the metal round it, metal pixels unchanged; does nothing without a holes image. Run by `prop_handback.py` and the Photoshop save hook: Blender `--background --factory-startup --python tools/blender/apply_holes.py -- <colour.png> [<holes.png>]`. |
| `blender/prop_handback_blender.py` | Blender's half of a hand-back: `-- check` (the panel's Check findings, one per line, UVs included), `-- send` (the panel's Send to game, headless), `-- render <folder> [--colour <png>]` (four views from the prop's own size), `-- make [--save]` and `-- rebuild [--save]` (the panel's Make and Rebuild game mesh). |
| `photoshop/open_canvas.jsx` | Opens a prop's canvas PSD in Photoshop, or makes it from the colour PNG with a locked UV guide layer; never replaces an existing PSD. Run by `prop_handback.py --open`. |
| `photoshop/export_canvas.jsx` | Photoshop's half: exports a prop's PSD as a flattened PNG with every "UV guide" layer hidden, refusing unsaved changes unless told. Run through AppleScript by `prop_handback.py`. |
| `photoshop/canvas_export.jsxinc` | The flattened, guide-hidden PNG export itself, included by `export_canvas.jsx` and `on_save.jsx` so the two can't drift. |
| `photoshop/live_update.sh` | Turns the Photoshop save hook on, off or reports it (`status`, the default): while on, saving `assets/source/textures/<prop>/<prop>_colour.psd` writes its PNG and sends the prop to the game in the background, and the Blender panel reloads the texture. Photoshop keeps it across restarts. `tools/photoshop/live_update.sh [on\|off\|status]` |
| `photoshop/on_save.jsx` | The save hook itself (Photoshop's "Save Document" script event): exports a saved prop canvas PSD to its PNG, then runs `prop_handback_blender.py -- send` headless in the background, logging to `~/Library/Logs/Keep Your Ticket/live_send.log`. Any other save does nothing. |
| `photoshop/hole_layers.jsx` | Gives a perforated prop's PSD its two locked hole layers, replacing earlier ones: the canvas colour under everything (a see-through spot in the paint exports as metal, not white) and the holes as a translucent "UV guide: holes (Claude)" on top, hidden on export. Run by `prop_handback.py --open` and `--hole-layers`. |
| `photoshop/install_on_save.jsx` | Adds or removes `on_save.jsx` on Photoshop's "Save Document" event, leaving any other script event alone. Run by `live_update.sh`. |
| `photoshop/canvas_tools.jsx` | The Blender panel's buttons for a canvas open in Photoshop, run through AppleScript: `guide show\|hide` (every "UV guide" layer, by layer id, which a locked layer allows; the selection stays) and `patch <name>` (an empty `<name> patch` layer, numbered if taken, under the guide and selected). Never opens, starts or saves anything; `NOTOPEN` when the canvas isn't open. |
| `optimize_png.py` | Makes PNGs smaller without changing a pixel: drops channels that carry nothing, strips metadata (keeps a colour profile), re-encodes at maximum lossless compression, and replaces a file only if the result decodes identically and is smaller. Run on a painted texture after export and before Send to game: Blender embeds the PNG's own bytes in the GLB. `python3 tools/optimize_png.py <file.png> …` |
| `blender/trim_map.py` | Maps a game mesh onto a trim sheet: a first UV map `trim` (the old unwrap kept second as `unique`, for baked shading). Faces go to the strip their material names, projected along the axis they face with the prop's long axis along the strip, at the sheet's `px_per_metre`; faces of one material in one plane that touch are one board and share an offset; timber faces looking along the prop's length take end grain; detail-cell materials (fixings) fill their cell per connected piece. Run through Blender with `-- <layout.json> [material=strip…] [--save]`. |
| `strip_collision_twins.py` | One-time removal of authored `_collision-colonly` twin objects from a Blender master, marking twinless objects `kyt_collision=none` and moving boulder materials onto the object. Dry run by default; `-- --save` applies. Run through Blender. |
| `gen_crowd.gd` | The plaza, boardwalk and terraces crowds in one run. Each output carries an `area_id`, because all three coexist in `park_world.tscn`. Bodies and placement only; behaviour lives in `scenes/npc/guest.gd` and is hand-written. |

## Tests

- `range_geography_audit` — read-only mounted-coordinate inventory of every
  generated, range-source and city-source terrain owner implicated in the
  2026-09-12 recovery gate; prints machine-readable JSON and moves no geometry.
- `render_range_geography_audit.py` — turns that JSON into the synchronized,
  self-contained owner-plan, cross-section and inventory review map.
These assert. They print a verdict.

**The acceptance set**, run before any commit that touches geometry, routes or
crowds: `coplanar_test.py`, `footprint_test`, `footprint_walk_test`,
`path_ground_test`, `clearance_test`, `anchor_walk_test`, `boardwalk_edge_test`,
`section_test`, `transit_test`, `night_test`, `climb_test`. The rest are
measurements or narrower checks and run when their subject changes. The legacy
`walk_test.gd`, which named retired section routes and pre-expansion boundaries
and reported 77 failures against the persistent park, was split into the two
anchor and edge tests and deleted on 2026-09-05.

| tool | asks | notes |
|---|---|---|
| `anchor_walk_test.gd` | Do both protected anchors walk? NT-1's wings, court and approach; NT-2's gate, forecourt, wings, belvedere, basin staircase, bays and notch edges. | Split from the retired `walk_test.gd` on 2026-09-05. Legs come off `ParkPlan.wing_path` and `climb_reaches`, never a copy. A failure is reported to Christina, not fixed in passing. Takes leg-label filters after the tool name. |
| `boardwalk_edge_test.gd` | Do the pier and north ride loop walk both ways—including centre and both edges—and do the water, jetty, bluff, shop backs, yard, coaster fence and outer rails stop the player? | Split from `walk_test.gd` the same day, minus its pre-expansion strip-end probes. |
| `wheel_test.gd` | Does R1 retain its fixed rim crown, true hub-to-rim structural spokes and light tubes, twenty roofed gondolas, open-hour indexed motion, upright cabins and after-close stop? | Focused acceptance for the editor-owned wheel form and its visual-only motion script. |
| `path_ground_test.gd` | Does every programmed access path, road and street stand on the ground it was laid over, neither floating nor buried? | Prints per-path float and bury counts. |
| `climb_test.gd` | Is every guest standing on the floor of the area they are in? | Reads the floor off the crowd's own graph. |
| `ground_contact_test.gd` | Does every moving guest have real collision immediately underfoot? | |
| `tunnel_drive_test.gd` | Can a car drive the coast highway's five tunnels — every bore, both directions — without meeting terrain in the road, and is there headroom over each carriageway? | Passes clean since dd7ccc6; found 18 blocked segments at every mouth on 2026-09-22. Rays each station to the next at a driver's eye (1.5m) and a lorry's roof (4.2m), on the centre line and a metre inside each lane edge: direction matters, since a ray stops on ground rising ahead of it and one direction alone finds only the entries. Headroom is sampled every metre across the same three lines, and a roof under 4.6m fails. The lorry height exists because a portal face once hung 2.5m over the upper bore — a vertical curtain that an upward ray and an eye-height drive both pass. Nothing else in the set drives a bore — `path_ground_test` rays downward, which a tunnel passes by construction. |
| `transit_test.gd` | Do the Kiddieland railway and Grand Circuit form usable loops, move with riders while open, and park empty after close? | Run at `--fixed-fps 60`; also guards the sampled grades and the five station-to-route alignments. |
| `kiddieland_layout_test.gd` | Does the first published editor-owned district source still reproduce the accepted Route D, R5–R7, R14, P4, support, S3, Q4 and NT-2 records? | `extends SceneTree`; run with `--script`. It compile-checks the generator’s Route D consumer and moves both one instantiated R14 control and the whole ride in memory, proving the reader follows editor-owned transforms; it rewrites nothing. |
| `park_section_layouts_test.gd` | Do the other eight park sections preserve their accepted horizontal records as ordinary editor-owned Godot scenes and feed every plan consumer in the established order? | `extends SceneTree`; run with `--script`. It checks lossless migration from ParkPlan and moves an R10 queue control and its parent in memory to prove live editor ownership; it rewrites nothing. |
| `park_vertical_controls_test.gd` | Does the published editor-owned vertical handoff preserve all fifty map levels, four editable drainage rims, the localized P1 constraint, NT-2 output separation and every held-fixed relationship while responding to editor transforms? | `extends SceneTree`; run with `--script`. It generates no terrain, rewrites nothing and checks the generated terrain ownership. |
| `terrain_handoff_capture.gd` | Do D3-D6 read as localized terrain folds in the real park while the Terraced Fountain remains compositionally separate? | Metal/Forward+ proof of the 2026-09-09 map-to-Godot terrain publication; writes five frames under `documentation/screenshots/terrain-handoff-2026-09-09/`. |
| `boardwalk_scenery_capture.gd` | Are I2, I3 and B1-B4 distinct player-readable places while Q3 remains open? | Eight Metal/Forward+ frames under `documentation/screenshots/boardwalk-fidelity-2026-09-09/`. |
| `boardwalk_operations_capture.gd` | Do R1, R2, P2 and the pier landing read as operated places by day and recently vacated places after close? | Eight Metal/Forward+ frames under `documentation/screenshots/boardwalk-operations-2026-09-09/`. |
| `boardwalk_water_edges_capture.gd` | Do D2, its culvert, rain pond, crossings and controlled outfall read as one planted drainage landscape while protected water remains open? | Eight Metal/Forward+ frames under `documentation/screenshots/boardwalk-water-edges-2026-09-09/`. |
| `_open_face_capture.gd` | Where does `footprint_test` count its open faces, and which of them can you actually see? | Eleven Metal/Forward+ frames to `documentation/screenshots/open-faces-2026-09-21/`. The answer was that the corridor's majority are invisible and outside the envelope, while the coast seam and the city handoff are real to the eye. `open -n -a Godot`, never `--headless`. |
| `_ground_audit_capture.gd` | Does the 2026-09-21 ground audit look the way its numbers read — the east climb's slot, the shoulder toes and a tunnel portal, beside what was fixed in F's north arc and B's ramp bed? | Frames to `documentation/screenshots/ground-audit-2026-09-21/`. Metal/Forward+, so `open -n -a Godot`, never `--headless`. |
| `boardwalk_density_capture.gd` | Do Boardwalk period fixtures and pier safety hardware add middle-scale density without narrowing Q3 or public circulation, after retiring the crowded planter rhythm? | Eight Metal/Forward+ frames under `documentation/screenshots/boardwalk-density-2026-09-09/`. |
| `boardwalk_finish_capture.gd` | Do restrained materials, merchandise, caused wear and one public practical finish the Boardwalk without cluttering routes or protected views? | Eight Metal/Forward+ frames under `documentation/screenshots/boardwalk-finish-2026-09-09/`. |
| `pier_head_capture.gd` | Does the editor-owned pavilion T-head separate the fishing work from a complete public loop while preserving its support, west-arch reveal and sunset composition? | Nine Metal/Forward+ frames under `documentation/screenshots/pier-head-2026-09-10/`. |
| `pier_pavilion_capture.gd` | Does the editor-owned Pier House read as finished coastal architecture on every public face while preserving circulation, the west-arch reveal, sunset silhouette and after-close light handoff? | Nine Metal/Forward+ frames under `documentation/screenshots/pier-pavilion-2026-09-10/`. |
| `boardwalk_architecture_capture.gd` | Do I2, I3 and B1-B4 read as one varied, editor-owned streetwall rather than six generic shells while Q3 and the lighting schedule remain intact? | Ten Metal/Forward+ frames under `documentation/screenshots/boardwalk-architecture-2026-09-10/`. |
| `boardwalk_wheel_capture.gd` | Does R1 read from the supplied Santa Monica day and night references while its platform, west-arch reveal, fixed rim crown and light schedule remain intact? | Twelve Metal/Forward+ frames under `documentation/screenshots/boardwalk-wheel-2026-09-10/`. |
| `boardwalk_coaster_capture.gd` | Does R2 read as a complete, uncramped wooden coaster from its public station, route B, pier and night standpoints while Q3 and the west-arch reveal remain intact? | Twelve Metal/Forward+ frames under `documentation/screenshots/boardwalk-coaster-breathing-2026-09-11/`. |
| `boardwalk_coaster_test.gd` | Does R2 preserve its map parcel and operating address while the editor-owned circuit derives full track, timber bents and lift catwalk and fully retires the single-line greybox? | Focused scene-tree acceptance; runs through `tools/run.tscn`. |
| `boardwalk_north_ride_park_test.gd` | Does the 8m Boardwalk continue past the old chain into an open waterfront extension, join a separate land return, give R15 and R16 one continuous timber forecourt, keep R2's single public flyover at 4.0m fixed clearance with catch protection, and occupy one safely roofed high bay? | Focused editor-source, deck-face, terrain-bed, grade, clearance and scene-tree acceptance; runs through `tools/run.tscn`. |
| `boardwalk_north_ride_park_capture.gd` | Does the expanded north Boardwalk read as a continuous Santa Monica-inspired pier field around a smooth larger R2, four rides and visible under-coaster midway uses, with the cove, Q3 and west-arch views intact? | Fifteen Metal/Forward+ player-eye frames under `documentation/screenshots/boardwalk-open-air-redesign-2026-09-11/`, including the named Grand Circuit overpass. |
| `coastal_palm_test.gd` | Do all 34 coastal palms keep fixed feet while editor-owned trunks, crowns and layered footings stay inside the approved limits; do the sixteen arrival trees preserve their approved density while catalog copy `PRP-PLANT-051` uses sixty-four interleaved classic-California pinnate fronds; do both former fan forms remain outside the standing world; and do all planting rings and crossings remain intact? | Focused scene-tree acceptance for the Boardwalk, arrival approach and both catalog palm forms; runs through `tools/run.tscn`. |
| `coastal_palm_capture.gd` | Do the sixteen entrance palms read as dense, layered classic-California feather palms from both directions and below while the lighter road/Boardwalk crowns, allée arch and planting compositions remain legible? | Sixteen Metal/Forward+ frames under `documentation/screenshots/arrival-dense-california-palms-2026-09-11/`. |
| `parking_lot_test.gd` | Do eight editor-owned bay courses preserve the approved density while deriving marked bays, dressed vehicles, planted islands, pedestrian collectors and sightline-safe banners? | Focused scene-tree acceptance for the rebuilt parking fields; runs through `tools/run.tscn`. |
| `parking_lot_capture.gd` | Do the rebuilt fields and landscaped road approach read as one legible late-1990s arrival while Q0 and every vehicle opening stay open? | Eleven Metal/Forward+ player-eye frames under `documentation/screenshots/parking-lot-2026-09-11/`. |
| `coastal_plant_catalog_test.gd` | Do banana-tree, Red Sensation, Purple Heart, lemon-zest Hakone grass, delphinium, hanging-planter and petunia promenade catalog variants preserve their editor-owned surfaced courses, distinct silhouettes, selectable recipes and reusable footing relationships—including the dark coir basket finish, fern bowl's 175-frond mature cascade and mixed-petunia basket's domed flower scoop? | Focused scene-tree source acceptance; runs through `tools/run.tscn`. |
| `tree_catalog_test.gd` | Do the current Plaza and mature park trees and every detailed range-tree candidate retain editable sources while the mounted southern massif and eastern connection remain broad closed terrain bodies with collision, and the generated primary range retains its integrated summit? | Focused source, topology and mounted-coordinate range acceptance; runs through `tools/run.tscn`. |
| `coastal_live_oak_catalog_test.gd` | Does the California coast live oak retain five selectable low-forking trunks, twenty-three broad crown courses, dense individual foliage and no sphere/capsule canopy masses? | Focused catalog-only source acceptance; runs through `tools/run.tscn` and makes no placement claim. |
| `shaded_promenade_catalog_test.gd` | Do the white-bark tree, clipped hedge, dark lilyturf, color-block information panel, rough-granite table, reclined water-view bench and plain guardrail remain reusable editor-owned catalog families, and does their catalog-only waterfront vignette retain the complete recipe? | Focused source acceptance; runs through `tools/run.tscn` and makes no park-placement claim. |
| `strap_leaf_catalog_test.gd` | Do Lily of the Nile and lilyturf share the editable six-point pointed arch while preserving broad/fine proportions and distinct deep-green and yellow-green catalog siblings; and do all six Lily of the Nile stalks retain editable bends that meet their globes? | Focused source acceptance; runs through `tools/run.tscn` and makes no park-placement claim. |
| `cordyline_catalog_test.gd` | Do Torbay Dazzler and Electric Pink retain selectable five-point sword-leaf courses, surfaced folded ribbons, cultivar-specific striping and Electric Pink's three-shoot clump? | Focused source acceptance; runs through `tools/run.tscn` and makes no park-placement claim. |
| `arrival_walk_paving_test.gd` | Does one continuous editor-owned brick skin cover the arrival walk while its material bends the actual brick bond into repeated inspector-adjustable surf fronts and the original support remains present? | Focused source and live-scene acceptance; runs through `tools/run.tscn`. |
| `lighthouse_regrade_test.gd` | Does the approved editor-owned P1 curve drive a localized cut-or-fill terrain ribbon and densely sampled paving while preserving its endpoints, 1:8 cap and shoreline gap? | `extends SceneTree`; run with `--script`. It rewrites nothing and proves cross-section edits are read live. |
| `photo_exposure_test.gd` | Does a shutter press preserve an immutable, JSON-safe record of park time, camera pose, flash and objective scene facts without a score or composition judgment? | `extends SceneTree`; run with `--script`. It writes no photographs. |
| `kiddieland_story_test.gd` | Does Three Jumps and a Birthday keep its five approved beats, three returning cast, factual developed evidence, after-close residue and pavilion keepsake without scoring a photograph? | `extends SceneTree`; run with `--script`. It writes no photographs and changes no story state. |
| `footprint_test.gd` | Does the expanded developed park remain one connected hierarchy inside genuinely larger world geography? | Guards the 434x450m program envelope, 2km-plus land reserve, nearly 4km western ocean reserve, every primary handoff, the four crossing records and the retirement of the old NNW dead end. |
| `footprint_walk_test.gd` | Can the real Player traverse every rebuilt public path in both directions? | Current A–F release gate: center and both operating edges of all generated segments, including shared junction floors and expanded-datum handoffs. |
| `section_test.gd` | Is the park one continuous standing world, with both plaza gates walkable in both directions and no load, teleport, far stand-in or transition gate? | Also verifies all canonical scenes and all three tagged crowds are present. |
| `day_test.gd` | Does each section's crowd have a day — the curves, the admitting and the sending home? | `--headless --fixed-fps 60`, about ninety seconds. |
| `weather_test.gd` | Does the authored coastal shower arrive after opening, leave a wet reflective Boardwalk behind and clear before the protected western sunset while daylight clamps its input? | `extends SceneTree`; run with `--script`. It uses no renderer and rewrites nothing. |
| `wildlife_test.gd` | Do the persistent editor-owned gull and pigeon scenes keep both species, the juvenile gull and waterfront flight pair outside protected-anchor placement; does every northern-rock roost retain a resident gull while commuters range across the park and both north and south beaches; do their separate upper/lower bill pivots open correctly; and does every ordinary grounded bird retain its non-collectible flush response? | Focused scene-tree acceptance; runs through `tools/run.tscn`. |
| `rock_dove_test.gd` | Does the rock-dove handoff remain one editable Blender model with no primitive-sphere construction, a packed UV atlas on every surface, distinct neck/wing-top/wing-underside/tail regions, articulated bill and unchanged flush response? | Isolated source and behavior acceptance; runs through `tools/run.tscn` without touching the concurrent gull refinement. |
| `shiny_pigeon_test.gd` | Does the special white shiny pigeon remain an independent mission-only subject, absent from ordinary wildlife placement, with its articulated form, warm-white packed textures and closed/open wing-state handoff intact? | Isolated source, behavior and mission-boundary acceptance for `shiny_pigeon.tscn`. |
| `ash_red_pigeon_test.gd` | Does the ash-red/cream rock-dove morph retain the supplied reference's cinnamon-to-pale body, warm-gray head, buff wing shield, rose feet, red iris and pink bill while preserving the shared authored pigeon form and ordinary flush behavior? | Isolated source, palette and behavior acceptance for `ash_red_pigeon.tscn`; it does not place the bird in the ambient flock. |
| `wildlife_capture.gd` | Do the adult gull, mottled juvenile, ground pigeons, articulated open bills, flush response and circling waterfront pair read in the mounted runtime world? | Eleven Metal/Forward+ frames under `documentation/screenshots/wildlife-proof-2026-09-13/`; the close bill poses and consecutive flush/circle frames carry the evidence. |
| `night_test.gd` | Do the lights come on and go off again? | `park_lights.gd` fails by succeeding: miss the emissive materials and the lights still light. |
| `menu_test.gd` | Does the pause menu respond to real input — tabs, cursor wrap, backing out of quit, and is the park actually stopped? | A still shows a screen draws, not that it works. |
| `fly_test.gd` | Does the dev flight leave the ground on `dev_fly`, travel along the look and through a floor, and land on ground when switched off underneath it? | Driven by actions: the toggle is an `_unhandled_input` handler on an action the player registers only in a debug build, and calling `set_flying` would pass without either. |
| `inpool_test.gd` | Is anybody standing in the fountain? | Samples over twelve seconds, not one instant — the single-instant version reported three offenders one run and none the next. Guards a 40cm margin: rim sitters at 8.66 against water ending at 8.26. |
| `clearance_test.gd` | Is anything standing in a walkway, or in another prop? | `extends SceneTree`. Hand-placed props have no equivalent of `open_spots`' rejection sampling. |
| `budget_test.gd` | Does what the park draws stay inside a budget, and what does each placed scene cost? Headless counts from five standpoints and eight headings through the player's frustum: surfaces and triangles a view, triangles in the world, and surfaces and triangles a placement for any scene placed three times or more. Prints the heaviest views, owners and placed scenes every run. | Acceptance set since 2026-09-18. Raising a ceiling is Christina's decision, against a frame time from `player_motion_perf_probe`. `KYT_NO_STATIC_MERGE=1` shows the failure it was written for. |
| `perf_test.gd` | What does the crowd cost per frame, hour by hour? | Measurement, not an assertion. Re-measure before building any tiering scheme. |
| `park_height_audit.gd` | What vertical datum, route-control levels, maximum grades, site floors and drainage-ground heights does the accepted build currently assign to the section atlas? | Read-only planning audit; `extends SceneTree`, runs with `--script`, writes no scene and is not a construction source. |
| `coplanar_test.py` | Which surfaces will z-fight? | Seconds, no Godot needed. Reads CSG *and* meshes, so it covers guests as well as the world. |
| `seat_test.py` | Is every seated guest sitting on something? | Wheelchair users excluded — they bring their own. |
| `flow_probe.py` | Which way did the water actually move? | Analyses frames from `flow_probe.gd`. A still cannot show a direction and will look correct either way. |

## Capture tools

These belong to Christina's visual-review workflow. Run, add, move or edit them
only when she explicitly asks. Agent geometry acceptance does not use them.
All need a real renderer.

| tool | shoots |
|---|---|
| `capture.gd` | The plaza from a list of vantages, including passes across the day for both the light and the crowd. Ships `capture.tscn`. |
| `west_capture.gd` | The plaza-to-boardwalk walk in order, crossing the seam mid-run. Ships `west_capture.tscn`. |
| `menu_capture.gd` | The HUD and all four pause-menu tabs, stacking consecutive frames of a tab change and a cursor move into strips — a still cannot show that either animates. |
| `night_capture.gd` | The park through the evening, measuring what the lights cost while it does it. |
| `footprint_capture.gd` | Ten real-world aerials covering the complete A–F hierarchy, arrival, Headland, west/east anchors, Plaza branches and the coastal, family and northern ride circuits. |
| `visual_catalog_capture.gd` | Live 16:9 reference cards for every mounted building, facility, ride and attraction in the two roster documents. Run the complete refresh with `tools/update_visual_catalog.sh`; `python3 tools/visual_catalog.py check` reports stale catalogs. |
| `prop_catalog_capture.gd` | Neutral isolated renders of the prop families that have a source recipe in `documentation/prop-catalog.json`; invoked by `python3 tools/build_prop_catalog.py --capture`. |
| `arrival_walk_paving_capture.gd` | The arrival promenade in both directions, a long reading of its wavy brick courses, a close material view and the full field between the palm beds. |

`build_prop_catalog.py` is the prop browser's complete refresh and drift check.
It reads labels, names and statuses from `documentation/prop-library.md`, builds
the cards and category sheets in that same document, and generates the matching
`PropCatalogIds` constants for Godot. Use `--capture` to refresh source renders
first or `--check` in validation and CI.

## Probes

Narrow, throwaway, and tracked anyway — each was written to answer one question
nothing else could, and the question tends to come back. They need a scene
wrapper and, where they save images, a real renderer.

| probe | question |
|---|---|
| `_arch_crop_probe.gd` | Is the wheel's top rim cropped by the west arch's beam? |
| `_balloon_probe.gd` | Is every balloon standing over the person holding it? |
| `_cascade_probe.gd` | The west cascade square-on against the reference — a view no player standpoint can take. |
| `_east_probe.gd` | The east gate at seven distances, both sides, off-axis and after dark. |
| `_festoon_probe.gd` | Do the street's festoons actually meet the frontage they hang off? |
| `flow_probe.gd` | Captures the consecutive frames `flow_probe.py` measures. |
| `_front_probe.gd` | The perimeter's upper storeys, from the fountain and from close enough to count them. |
| `_fountain_probe.gd` | Walks into the fountain's kerb from sixteen bearings. |
| `_glow_probe.gd` | The water's night glow, always paired against the same frame by day. |
| `_hill_probe.gd` | The east hill: the scarp from the court, the climb, and the belvedere at the top of it. |
| `_niche_probe.gd` | The wall fountain in the west cascade's niche, from the court. |
| `_pfoam_probe.gd` | The plaza fountain's froth, shot low at the waterline. |
| `_drive_probe.gd` | The coast highway's three reveals from the car's own eye. |
| `_forest_perf_probe.gd` | What the approved background-only range mass costs to draw, hidden versus visible, from its three established performance standpoints. |
| `range_perf_probe.gd` | What the mounted range costs: wrapper and `main.tscn` load times, node counts and collision triangles under the mount, ray and sphere query grids over the rock field, a walked CharacterBody3D on the beach, and rendered frame times from three standpoints with the range hidden and visible. Writes `user://range_perf_<driver>.txt`; run with `--disable-vsync` for the render block. |
| `far_plane_perf_probe.gd` | What the player's far plane costs: a player-lens camera at five reachable standpoints, eight headings each, at 400m and 4200m; frame, GPU time, objects, primitives, draw calls. Windowed with `--disable-vsync`, frontmost, and with no other Godot instance rendering, or the numbers are contention. Writes `user://far_plane_perf.txt`. |
| `frame_cost_probe.gd` | Where a frame goes: the same player-lens views with one thing switched off at a time (sun shadows, shadow distance, splits, small CSG casting, small CSG, all CSG, positional lights, crowd, MSAA, SSAO and glow, haze, range/city/towns), baseline first and last. `FRAME_COST_ONLY="baseline,sun shadows off"` runs a short list. Same launch rules as `far_plane_perf_probe`; the counts are trustworthy under GPU contention, the times are not. Writes `user://frame_cost.txt`. |
| `player_motion_perf_probe.gd` | Does the frame get worse when the real player looks and walks? Mounts `main.tscn` as the game does and drives the player through its input actions: still, look, walk, walk and look, still. One line a second: frame, worst frame, physics ticks per frame, process, physics, render CPU, draw calls, position. Same launch rules as `far_plane_perf_probe`. Writes `user://player_motion_perf.txt`. |
| `_view_draws_probe.gd` | From the player's spawn, which of sixteen headings is heavy, and which child of `park_world` owns the draw calls there? `VIEW_DRAWS_UNDER="park_world/places/park_approach/authored_additions"` asks about that node's children instead. Counts only. Writes `user://view_draws.txt`. |
| `_palm_inventory_probe.gd` | What the coastal palm sets and the arrival and roadside landscaping leave visible at runtime: mesh nodes, surfaces, distinct meshes and materials for each set's trunks, crowns and beds, for one palm, and for each landscaping output group. Headless. Shows whether `scripts/static_merge.gd` ran; `KYT_NO_STATIC_MERGE=1` gives the counts before it. |
| `_generated_compare_probe.gd` | Is every generated scene the same scene as a snapshot of it, by content? Instantiates both and compares each node's class, stored properties and the full contents of every resource, meshes and collision included, which the text filter cannot do once a sub_resource has become an ext_resource. `GENERATED_SNAPSHOT=/absolute/dir` names the copies. Headless; proven to fail on a bench widened by 25cm. |
| `_load_time_probe.gd` | What is the `main.tscn` load made of? Loads each scene `main.tscn` and `park_world.tscn` instance, one at a time, and prints load and instantiate times, node counts and file sizes, slowest first. Headless. |
| `_binary_load_probe.gd` | How much of a generated scene's load is parsing text? Times `generated/park_groundworks.tscn` and `park_approach.tscn` as they are against a binary `.scn` copy saved to `user://` and deleted; writes nothing in the project. Headless. |
| `_launch_stall_probe.gd` | How long does launch block? Times `main.tscn` load, `add_child`, and every frame over 50ms in the first 300. Headless. `KYT_NO_STATIC_MERGE=1` runs it without the load-time merge. |
| `_triangle_census_probe.gd` | Where the world's triangles are, without drawing: faces of every visible mesh and CSG root by `park_world` child, and the coastal planting by material. Headless, so it runs while a game window holds the GPU. |
| `_range_import_dump.gd` | What Godot made of the exported range GLB: every child with its class, what sits under it, and each concave shape's triangle count. |
| `_range_handoff_probe.gd` | Did a boulder edited in Blender reach Godot as mesh, material and collision? Takes a JSON of the boulder's bounds before and after the edit. |
| `_notch_ground_probe.gd` | What ground stands in the north massif's highway notch: the first collision under a 20m grid across it and along tunnel 1, and which node owns it. |
| `_hole_probe.gd` | Rain rays over the whole east and dump what they hit. |
| `_seam_gap_probe.gd` | What is just outside every open edge of the generated ground, the developed envelope and T2/T3/T6/shoulders included: rays 5 to 60cm outside each edge, `VOID` where nothing is below (a seam the Player falls through), `drop` where ground is over 0.6m down. Clustered to 40m cells. |
| `_world_hole_probe.gd` | Rain rays two metres apart over the whole land against the ground owners: no ground with dry land on three sides, or a slot over 1.5m deep. Finds missing ground, not seams narrower than the grid. |
| `_flipped_face_probe.gd` | Generated terrain triangles wound to face down, by mesh and 50m cell with their area. `--script`. |
| `_float_path_probe.gd` | `path_ground_test`'s ray under every ribbon in the world, not only the three layers that test reads, summarised per ribbon: floating and buried samples, the worst of each and over what. |
| `_ground_field_probe.gd` | How much of the park's ground is decided by cache state rather than design, and how far one composed entry point stands from what was built. Samples a 4m plan grid over the envelope plus the embankment region's 60m pad under six generator configurations, then raycasts the standing world. A0 fingerprints the graded routes first, so a flat zero cannot be mistaken for a result, and A3 asks each surface's own function to reproduce the surface the ray actually landed on. Pass a step in metres after the tool name. Prints; returns 0. |
| `_float_profile_probe.gd` | The centreline gap under the ribbons named after the tool, every ten metres: where along a route it leaves the land. |
| `_open_faces_all_probe.gd` | Every open face `footprint_test` counts, in full, grouped by mesh and 40m cell, so what remains after a stitch can be read by place. A copy of that test's check with its printing changed. |
| `_vertical_section_probe.gd` | Every drawn surface and every collider on a vertical line through each `x,z` given after the tool name. |
| `_ledge_probe.gd` | The walkable profile where the climb meets the head landing. |
| `_lot_probe.gd` | Does the coast highway show from the parking lots? |
| `_prom_probe.gd` | Rain rays over the promontory walk and dump what they hit. |
| `_lighthouse_walk_probe.gd` | The emitted P1 contour climb from the real Player at five stations, its shore side and one oblique overview; pairs with filtered `footprint_walk_test` traversal and `path_ground_test` contact. |
| `_range_probe.gd` | The crescent range from far enough away to see its shape. |
| `_ground_range_background_ends.py` | Rebuild the reviewed distinct massif from its pre-north-correction Blender backup, preserving the already-grounded south end while tapering the exposed north coastal end into sea-level ground and exporting the mounted GLB. Run through Blender, not Godot. |
| `_seam_probe.gd` | The heights the coast meshes and the mainland reserve each give along their seam. |
| `_sight_probe.gd` | What a standpoint is actually looking at. |
| `_terrace_probe.gd` | The east climb's walled courts, banks and basin chain. |
| `_terraces_probe.gd` | The terraces district, seen from inside itself. |
| `_town_probe.gd` | The three towns of package 02B from the standpoints they are built for. |
| `_town_site_probe.gd` | The natural ground along the coast highway and across the town sites, read off the generator without regenerating. |
| `_tunnel_probe.gd` | The highway's five twin-bore locations as a car drives them: seconds at speed, each carriageway's segmented grade and turn, and the heading past each portal. Reads the generator's stations; regenerates nothing. |
| `_road_profile_probe.gd` | The highway's and the approach road's section along their whole length, off the generator's height functions: cut depth, drop, dips, the plan lines after their fillets, the carriageways' split, the ramps, the corridor mesh's cost. `--script`; regenerates nothing. |
| `_open_face_probe.gd` | The terrain's open edges by mesh, each with its nearest edge on another mesh: what a crack between the road corridor and the lattice is. `--script`; loads the groundworks scene. |
| `_road_probe.gd` | The roads of 2026-09-05/06 from their standpoints: the interchange by day and night, the split-level coast, a walled cut, a portal, the towns' main streets, the beach road's bend. |
| `range_interchange_proof_capture.gd` | Compare the background-only baseline with two unmounted forest constructions in the road-sensitive interchange/south-highway segment, from identical plan, road and park cameras. |
| `range_interchange_proof_test.gd` | Do the two unmounted interchange forest experiments remain collision-free, outside every live highway/ramp/approach centreline by 30m, and absent from the persistent world? |
| `far_shore_city_test.gd` | Guard the mounted editable city package, retired flat fan, bridge junction, city bypass, broad closed foothills, closed road earthworks, ≤2% grades, ≤0.35m centreline-to-ground gaps and continuous plan overlap without consulting a camera. |
| `_coastal_fast_probe.gd` | The one-hour coastal breadth pass from eight inspection cameras: beach town, north town, watersheds, harbour, park fishing deck, scenic railway and city. |

Godot writes a `.uid` beside every script it imports. Those are tracked — but
delete the throwaway wrapper scene and its `.uid` when you are done.
