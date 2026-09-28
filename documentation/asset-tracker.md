# Asset tracker

Where each prop stands in `prop-pipeline.md`, who holds it, and what happens
next. Every session reads the row before touching a prop (the `prop-handoff`
skill says how) and updates it after. If a row and the files disagree, the
files win; fix the row and say so. Christina can edit any row. This file is
tracked in git (the rest of `documentation/` is not), and the repository is
public: keep story material out of it.

**Stages** (from `prop-pipeline.md`): maquette → model → game mesh → canvas →
paint → integrated. **Holder** is who has the next move.

## Props

### plaza_bench — PRP-PARK-001, cast-frame slatted park bench

| | |
|---|---|
| Stage | **paint**: first painted pass integrated and committed (`151c715`, gum out `a8c9ca9`; PSD re-saved `b7e536d`, no visible change) |
| Holder | Christina: may keep painting in the PSD |
| Model | `assets/source/props/plaza_bench.blend` (working, one fused mesh); parts in `plaza_bench_source.blend` |
| Paint | `assets/source/textures/plaza_bench/plaza_bench_colour.psd` (layers `paint`, `paint copy`, `gum patch (Claude)`, `gum patch 2 (Claude)`, locked `UV guide`) |
| Game | `assets/props/plaza_bench.glb`, placed ×6 through `scenes/world/park_furniture/plaza_bench.tscn`; random gum by `bench_gum.gd` |
| Canvas options | in `howto/paint-the-plaza-bench.md` (grain, knots on back_0–3, wear on seat_0–5, chips, dings, ground) |
| Last hand-back | `documentation/screenshots/handbacks/plaza_bench-2026-09-25_0120/` (all passed; PSD saved with no visible change) |
| Next | When she says "handed back" or "process it": `python3 tools/prop_handback.py plaza_bench`, report, commit on her word. After any edit to the source parts: Rebuild game mesh first. |

### waste_bin — PRP-PARK-002, waste bin (the phase gate)

| | |
|---|---|
| Stage | **maquette**: still the generated greybox (`tools/gen_props.gd` `_bins`); reusable variant `scenes/world/boardwalk_props/waste_bin.tscn` |
| Holder | Agent, when Christina says to start |
| Next | Stage 1 set-up: reference from the greybox, `new_prop.py -- waste_bin`, the Godot scene, a hand-off card. Per the plan, agents do set-up only. Fix on the way: canvas options per prop and grain along vertical slats (R2/R3), normal and occlusion bakes (M1/M2). |

### perforated_metal_bench — PRP-PARK-018

| | |
|---|---|
| Stage | **paint**: canvas with the 2× perforated mesh handed back 2026-09-25 18:30 (all passed), sent to the game; PSD ready with its hole layers. Model built by Claude at her request from her 2026-09-11 photo, chunkier, with the family's bolts; game mesh 1,964 triangles |
| Holder | Christina: painting in the PSD (each save sends it through the Photoshop hook) |
| Model | `assets/source/props/perforated_metal_bench.blend` (working, one fused mesh); parts in `perforated_metal_bench_source.blend`; `reference` holds only the floor and the seat markers |
| Paint | `assets/source/textures/perforated_metal_bench/perforated_metal_bench_colour.psd` (made again after the holes were re-cut; the holes show as transparency in `paint`, locked `UV guide`); colour 2048 (about 925 px/m) with the holes in its alpha, `_holes.png` (90 × 38 mm diamonds, 11 mm wires, 46% open: her call, twice, for a chunkier, larger mesh), ORM 1024. The PSD also has the two locked hole layers (canvas under `paint`, `UV guide: holes (Claude)` on top), added with her yes and saved by her |
| Game | `assets/props/perforated_metal_bench.glb` (519 KB, alpha-mask holes; textures VRAM-compressed with mipmaps), wrapped by `scenes/world/park_furniture/perforated_metal_bench.tscn` with `seat_l`/`seat_r`; not placed anywhere |
| Canvas options | `--perforate seat_sheet,back_sheet --chips seat_frame,back_frame,pedestal:0.4,back_upright:0.4,seat_support:0.4,foot_l,foot_r --dings foot_l,foot_r --ground foot_l,foot_r,pedestal` (2048) |
| Reference | Her photo (2026-09-11), pasted into a Codex session; not in the project yet |
| Last hand-back | `documentation/screenshots/handbacks/perforated_metal_bench-2026-09-25_1830/` (canvas with the 2× mesh; all passed) |
| Next | Another saved pass ("saved"): `python3 tools/prop_handback.py perforated_metal_bench`, no question; commit on her word. To change the hole pattern: `HOLE_*`, `paint_canvas.py --holes-only --perforate seat_sheet,back_sheet`, then `prop_handback.py perforated_metal_bench --hole-layers`. |

### backless_timber_bench — PRP-PARK-019

| | |
|---|---|
| Stage | **paint**: painted passes integrated and committed 2026-09-25. Model handed back the same day (20 bolts, 16 hers); game mesh 1,394 triangles; 2048 canvas |
| Holder | Christina: may keep painting in the PSD |
| Model | `assets/source/props/backless_timber_bench.blend` (working, one fused mesh); parts in `backless_timber_bench_source.blend`. Its 18 `greybox_` reference parts are hidden, not deleted |
| Paint | `assets/source/textures/backless_timber_bench/backless_timber_bench_colour.psd` (`paint` layer, locked `UV guide`); colour 2048 (about 814 px/m, her choice to match the plaza bench's size), ORM 1024 |
| Game | `assets/props/backless_timber_bench.glb` (her first pass, 1,317 KB; textures VRAM-compressed with mipmaps), wrapped by `scenes/world/park_furniture/backless_timber_bench.tscn` with `seat_l`/`seat_r`; not placed anywhere. The back-side seats are not in the contract |
| Canvas options | `--grain --wear slat --chips pedestal:0.4,foot,top_bracket,under_rail:0.4 --ground foot,pedestal`. No knots and no back-edge wear: hers to paint |
| Last hand-back | `documentation/screenshots/handbacks/backless_timber_bench-2026-09-25_1415/` (her 14:06 pass: wear along the front and back slats' outer edges; all passed). The Photoshop save hook is on, so each save already sends the bench |
| Next | Another saved pass: `python3 tools/prop_handback.py backless_timber_bench`, no question; commit on her word. Before placing it in the park: the back-side seats, if guests are to sit facing the other way. |

### palm_crown — PRP-COAST-006, coastal palm crown (pinnate)

| | |
|---|---|
| Stage | **paint** (2026-09-27): the torn-leaf texture (`CUT_STYLE = "tears"` and her saturated repaint) in the game on all 34 palms and both catalog palms; PSD `assets/source/textures/palm_crown/palm_crown_colour.psd` with its cut-out layer and "shading (Claude)" |
| Holder | Christina: painting. With the save hook on, each PSD save sends the crown to the game |
| Model | `assets/source/props/palm_crown.blend`. `reference`: the old Godot crown (3,250 triangles) and `trunk_top` at the origin, which it hangs from. `authored/courses`: the 44 Godot Path3Ds as Bezier curves (0.00 mm) plus three `course_dead_*`. `authored/blades`: spear, young, mature, old, stub, dead; since 2026-09-27 broad banana-leaf outlines folded 131°, and the 29 mature/extra/old courses in two tiers with a knee in each leaf (script with the 09-27 hand-back). `export`: 47 fronds bending their blades along their courses (`kyt_course_blade` geometry nodes) and `heart`; 2,748 triangles, 6 materials. Scene properties `kyt_keep_parts`, `kyt_godot_scene` |
| Game | `assets/props/palm_crown.glb` (one node per frond, kinds as glTF extras; its material mapped on import to `assets/materials/palm_crown_leaf.tres`, `assets/shaders/palm_leaf.gdshader`, undersides darker and cooler, and each frond leaning slightly yellow or teal by a tone in its vertex colour, and a normal map of the pleated surface, `assets/props/palm_crown_normal.png`, 2026-09-27), wrapped by `scenes/world/palm_crown.tscn` (`palm_crown.gd`: the seed spreads the chosen mature, old, stub and dead fronds round the trunk and tips each up to 4°; size ±5%; since 2026-09-27 it mirrors about half the fronds across their midrib, `mirror_share`, from a mirrored copy of each frond mesh, so the torn leaves don't repeat; density copy for PRP-PLANT-051). Placed through `scenes/world/coastal_palm.tscn`, one per foot, in the editor-owned `approach_palms.tscn` (26) and `boardwalk_palms.tscn` (8), migrated losslessly from `coastal_palm_replacements.gd` (retired 2026-09-25 with the Godot-course crown `coastal_palm_crown.tscn`; git holds both at `58c9ca8`). Dead fronds: none at the entrance, one on a quarter of the front road, one to three on the Boardwalk. The generator no longer emits stick palms (2026-09-25); `coastal_palm_test` holds each foot to a fixed table. The catalog specimen GRP-PARK-012 (13 fronds, 9 stubs) and PRP-PLANT-051 (32 fronds doubled to 64 by the raised second shell, 12 stubs) use it too, with no size variation |
| Reference | `documentation/reference/palm_crown/mario_kart_palms_fringed_masses.webp` (her Mario Kart 7 screenshot, 2026-09-26) and the Models Resource page she linked for the same game's palm (viewed only; its files are Nintendo's and were not downloaded): about ten broad folded leaves in two tiers, painted dark base to pale rim, a fringe of big bites on the outer half, torn tips |
| Last hand-back | `documentation/screenshots/handbacks/palm_crown-2026-09-27_1847/` (her 18:44 save: more tears cut on every kind, the dead fronds' green base at 55%; GLB 1,225 KB; textures match, VRAM-compressed with mipmaps; `coastal_palm_test`, `tree_catalog_test`, `coastal_plant_catalog_test`, `budget_test` PASS; clearance 0 of 87; ground contact known failures only) |
| Next | In the game. Her call: `frond_count` on the 16 arrival palms. Her further passes: each PSD save sends the crown; "handed back" runs `python3 tools/prop_handback.py palm_crown`. Commit on her word (the rebuilt shapes and this pass are uncommitted). The trunk is its own row, `palm_trunk`. |

### palm_trunk — PRP-COAST-007, coastal palm trunk (banded, segmented)

| | |
|---|---|
| Stage | **paint** (2026-09-27): shaped, starting canvas and bump in the game on all 34 palms and both catalog palms; PSD `assets/source/textures/palm_trunk/palm_trunk_colour.psd` made from the canvas (`paint` layer, locked UV guide) and open in Photoshop |
| Holder | Christina: painting. With the save hook on, each PSD save sends the trunk to the game |
| Model | `assets/source/props/palm_trunk.blend`. `export/trunk`: straight and upright, 8.5 m, foot at the origin, top the crown seat; 17 stacked segments (0.65 m at the foot to 0.38 m under the crown), each flaring into a toothed collar (12 teeth, seeded heights) over the next one's base; about 0.34 m across at 1 m, 0.26 m under the crown, 0.55 m at the root swell (the code-built trunk was 0.25, 0.20 and 0.36); 1,596 triangles, `kyt_collision = none`. `reference/greybox_trunk`: the code-built tube, moved losslessly first (36 trunks within 0.20 mm, `tools/_palm_trunk_migration_probe.gd`). Shaping script with the hand-back (`trunk_shape.py`) |
| Paint | `assets/source/textures/palm_trunk/`: `palm_trunk_colour.png` (1024, two bands shared by the segments, about 890 px/m; `paint_canvas.py --bands`), `palm_trunk_bump.png` (greyscale, white raised: hers to paint too), `palm_trunk_normal.png` (made from the bump by `tools/bump_to_normal.py` on every hand-back), `palm_trunk_orm.png`, UV guide |
| Game | `assets/props/palm_trunk.glb`, bent along each trunk's editor-owned Path3D by `scenes/world/coastal_palm_trunk.gd`, in both `coastal_palm_trunk.tscn` (18 palms and the specimen) and `coastal_palm_arrival_trunk.tscn` (16 arrival palms and PRP-PLANT-051); both now wear the model's own material, so the arrival palms lost their greyer trunk colour |
| Reference | `documentation/reference/palm_trunk/banded_chevron_trunk.png` (her first picture, 2026-09-27: dark and tan bands, scalloped edges); her second picture (segments with torn, lighter collars) was pasted in chat and is not saved in the project |
| Last hand-back | `documentation/screenshots/handbacks/palm_trunk-2026-09-27_2022/` (her hand-back with no changes: the PSD's export equals the canvas pixel for pixel; normal made from the bump; GLB 272 KB; textures match, VRAM-compressed with mipmaps; `coastal_palm_test`, `tree_catalog_test`, `coastal_plant_catalog_test`, `budget_test` PASS; clearance 0 of 87; ground contact known failures only). In-game frames of the look: `palm_trunk-2026-09-27_2007/game_*.png` |
| Next | Her passes: each PSD save sends the colour; "handed back" runs `python3 tools/prop_handback.py palm_trunk`, which also makes the normal map from `palm_trunk_bump.png` (painted in Photoshop as its own file; its saves don't trigger the hook). Commit on her word |

## Landmarks

### plaza_fountain — the plaza's centrepiece (ID when catalogued)

| | |
|---|---|
| Stage | **model** (2026-09-27): moved from `gen_props.gd` to Blender losslessly; no reshape yet |
| Holder | Christina: shaping, when she chooses |
| Model | `assets/source/props/plaza_fountain.blend`, made by `tools/blender/parts_from_maquette.py` from the maquette (`reference/plaza_fountain.glb` and `_parts.json`, written by `maquette_export --whole` and `tools/_fountain_migration_probe.gd materials`). `export`: 35 objects from the generator's 208 shapes, one per ring of repeated blocks (`kerb`, `coping`, `lb_rim`, `ub_rim`, `lb_veil`, `ub_veil`, `jet_nozzle`, `jet_a`, `jet_b`) and one per drum; welded, planar faces joined, sharp where the maquette's normals split; 4,728 triangles; 11 materials by the generator's names; `kerb` and `coping` collide, the rest `kyt_collision = none`; water and nozzles `kyt_shadow = off`; scene `kyt_keep_parts`. `reference`: the 208 shapes, hidden |
| Game | `assets/props/plaza_fountain.glb` (272 KB), mounted by `scenes/world/plaza_fountain.tscn` (inherits the GLB, keeps `authored_additions`) at the park's origin. Import settings: materials mapped by name to `assets/materials/plaza_fountain/*.tres` (the generator's own, written out), `tools/kyt_part_import.gd` for `kyt_shadow`, no LODs, no vertex compression (compression moved vertices 0.35 mm) |
| Proof | `_fountain_migration_probe compare`: surfaces within 0.0019 mm both ways, collision likewise, area within 0.00002%, flat normals within 0.006°, materials, shadows and instance settings identical. Drum sides are now radial; the CSG ones leaned up to 10.9°. Cap UVs differ; nothing reads them |
| Card | `documentation/howto/shape-the-plaza-fountain.md`: what binds (radius 9, coping top 0.52, jets, lights, the water materials' heights, the envelope) and the reasoning from the generator's notes |
| Last hand-back | none; starting frames `documentation/screenshots/handbacks/plaza_fountain-start-2026-09-27_2333/` |
| Next | Her shaping: Check, Send to game, Save, "handed back"; then `seat_test`, `ground_contact_test`, `_fountain_probe`, `clearance_test`, `budget_test`, the probe's report of how far it moved. A reshaped lip, ring or basin moves the water `.tres` heights, `_fountain_lights` and the `ParkPlan` fountain numbers with it. Commit on her word |
