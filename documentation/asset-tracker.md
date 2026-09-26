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
| Stage | **model**, integrated 2026-09-25: her set-up blades are the crown on all 34 coastal palms. Leaflets are to come from the texture's cut-out alpha (the perforated bench's route), on plain folded blades |
| Holder | Christina: may keep shaping the six blades; Send puts them on every palm |
| Model | `assets/source/props/palm_crown.blend`. `reference`: the old Godot crown (3,250 triangles) and `trunk_top` at the origin, which it hangs from. `authored/courses`: the 44 Godot Path3Ds as Bezier curves (0.00 mm) plus three `course_dead_*`. `authored/blades`: spear, young, mature, old, stub, dead. `export`: 47 fronds bending their blades along their courses (`kyt_course_blade` geometry nodes) and `heart`; 2,748 triangles, 6 materials. Scene properties `kyt_keep_parts`, `kyt_godot_scene` |
| Game | `assets/props/palm_crown.glb` (one node per frond, kinds as glTF extras), wrapped by `scenes/world/palm_crown.tscn` (`palm_crown.gd`: the seed spreads the chosen mature, old, stub and dead fronds round the trunk and tips each up to 4°; size ±5%; density copy for PRP-PLANT-051). Placed through `scenes/world/coastal_palm.tscn`, one per foot, in the editor-owned `approach_palms.tscn` (26) and `boardwalk_palms.tscn` (8), migrated losslessly from `coastal_palm_replacements.gd` (now unmounted, kept for recovery). Dead fronds: none at the entrance, one on a quarter of the front road, one to three on the Boardwalk. The generator still emits the stick palms; the sets hide them. The catalog specimen and PRP-PLANT-051 still use the old Godot crown |
| Reference | None saved. Her 2026-09-25 picture (a low-poly palm) showed the idea only: a plain folded blade, cuts from the texture |
| Last hand-back | `documentation/screenshots/handbacks/palm_crown-2026-09-25_2038/` (`coastal_palm_test`, `budget_test`, `tree_catalog_test`, `coastal_plant_catalog_test` PASS; lineup of eight palms) |
| Next | On "handed back" after more shaping: Send (the add-on must be reloaded once for keep-parts), `coastal_palm_test`, `budget_test`. Then the texture set-up, needing tools first: a leaflet-mask option in `paint_canvas.py` (along the rachis in each blade's UV), the mask as a layer she paints in the PSD rather than restored by `apply_holes.py`, a far-distance mipmap test on one frond, one UV island per blade kind shared by its fronds (Check must allow it), Make game mesh joining rather than fusing (or skipping it: the crown keeps its parts), plant tests in the hand-back in place of `seat_test`, and a rendered frame-time comparison down the allée once the fronds are cut-out (overdraw). Follow-ups: stop the generator emitting the stick palms; move the catalog specimen and PRP-PLANT-051 onto the Blender crown. Trunk (PRP-COAST-007) is a separate prop, not started. |
