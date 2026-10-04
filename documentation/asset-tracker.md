# Asset tracker

Where each prop stands in `prop-pipeline.md`, who holds it, and what happens
next. Every session reads the row before touching a prop (the `prop-handoff`
skill says how) and updates it after. If a row and the files disagree, the
files win; fix the row and say so. Christina can edit any row. This file is
tracked in git (the rest of `documentation/` is not), and the repository is
public: keep story material out of it.

**Stages** (from `prop-pipeline.md`): maquette → model → game mesh → canvas →
paint → integrated. **Holder** is who has the next move.

## Landmarks

### plaza_fountain — the plaza's centrepiece (ID when catalogued)

| | |
|---|---|
| Stage | **model** (2026-09-27): moved from `gen_props.gd` to Blender losslessly; its nine rings made radial arrays and its pedestal and basin undersides four lathes (2026-09-28); no reshape yet |
| Holder | Christina: shaping, when she chooses |
| Model | `assets/source/props/plaza_fountain.blend`, made by `tools/blender/parts_from_maquette.py` from the maquette (`reference/plaza_fountain.glb` and `_parts.json`, written by `maquette_export --whole` and `tools/_fountain_migration_probe.gd materials`). `export`: 35 objects from the generator's 208 shapes, one per ring of repeated blocks (`kerb`, `coping`, `lb_rim`, `ub_rim`, `lb_veil`, `ub_veil`, `jet_nozzle`, `jet_a`, `jet_b`) and one per drum; welded, planar faces joined, sharp where the maquette's normals split; 4,728 triangles; 11 materials by the generator's names; `kerb` and `coping` collide, the rest `kyt_collision = none`; water and nozzles `kyt_shadow = off`; scene `kyt_keep_parts`. Since 2026-09-28 the nine rings are one block each (their `_00`, back on its plan position) with the **Radial array** modifier (node group **KYT radial array**: Count, Lift), made by `tools/blender/radial_array.py`; Lift 0.5 mm on `kerb`, `coping`, `lb_rim`, `ub_rim` (overlapping neighbours), 0 on the falls and jets. The pedestal's and basins' eleven drums are four lathes (`tools/blender/lathe_from_drums.py`): `pedestal_steps` (wet, steps 1–2, 32 sides), `pedestal` (step 3 to the cap, 24), `lb_under` (28), `ub_under` (20); each an outline of points with a Screw ("Lathe") and Smooth by Angle (30°) modifier; plan radii and heights, the nudges out; 4,852 triangles. `reference`: the 208 shapes, hidden |
| Game | `assets/props/plaza_fountain.glb` (259 KB), mounted by `scenes/world/plaza_fountain.tscn` (inherits the GLB, keeps `authored_additions`) at the park's origin. Import settings: materials mapped by name to `assets/materials/plaza_fountain/*.tres` (the generator's own, written out), `tools/kyt_part_import.gd` for `kyt_shadow`, no LODs, no vertex compression (compression moved vertices 0.35 mm) |
| Proof | `_fountain_migration_probe compare`: surfaces within 0.0019 mm both ways, collision likewise, area within 0.00002%, flat normals within 0.006°, materials, shadows and instance settings identical. Drum sides are now radial; the CSG ones leaned up to 10.9°. Cap UVs differ; nothing reads them. Arrays (2026-09-28): with the generator's nudges taken out by its own rule (`FOUNTAIN_ARRAYS`), every ring within 0.0044 mm, collision likewise; the blocks moved at most 8.66 mm (the nudges). In frames the falls' and jets' world-space streaks sit in slightly different places (`handbacks/plaza_fountain-arrays-2026-09-28_0029/`). Lathes (`FOUNTAIN_LATHES`, buried faces skipped): `ub_under` 0.0007 mm; the others within their old facets' depth where drums gained sides (steps 19.2, pedestal 24.0, lower basin 20.8 mm); normals radial (`handbacks/plaza_fountain-lathes-2026-09-28_0045/`) |
| Card | `documentation/howto/shape-the-plaza-fountain.md`: what binds (radius 9, coping top 0.52, jets, lights, the water materials' heights, the envelope) and the reasoning from the generator's notes |
| Last hand-back | none; starting frames `documentation/screenshots/handbacks/plaza_fountain-start-2026-09-27_2333/` |
| Next | Her shaping: Check, Send to game, Save, "handed back"; then `seat_test`, `ground_contact_test`, `_fountain_probe`, `clearance_test`, `budget_test`, the probe's report of how far it moved. A reshaped lip, ring or basin moves the water `.tres` heights, `_fountain_lights` and the `ParkPlan` fountain numbers with it. Commit on her word |

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

### waste_bin — PRP-PARK-002, the bin family and the plaza's placed bin (the phase gate)

| | |
|---|---|
| Stage | **maquette** (2026-09-27): the plaza's placed bin, still the greybox shape; the family's four are modelled (rows below) |
| Holder | Christina: which bin kind (or mix) the plaza gets |
| Family | Her four public bins (her pictures, 2026-09-27, pasted in chat, not saved in the project): the **inner can**, a plain round utility can with handles and a bag, which fits inside the other three and comes out on its own at pick-up time; a **hooded bin**, square plastic body and a hood with an opening each side and a front art panel; a **riveted bin**, an arched metal shell with riveted edges, a dark push opening and a sticker, silver or painted; a **recycling bottle**, bottle-shaped with a shoulder opening and a label band for a made-up brand. Each its own prop file, all four built by Claude on 2026-09-27 (rows below), the shells round the inner can, which each shell file holds in its locked reference |
| Model | `assets/source/props/waste_bin.blend`: the lossless stand-in. `reference` (locked): the plaza greybox (`tools/gen_props.gd` `_bins` until 2026-09-27: 12-sided, body r 0.32 × 0.85 m, lid r 0.36 to 0.92 m) and the Boardwalk's `boardwalk_props/waste_bin.tscn` 2.5 m along +X, from `assets/source/props/reference/waste_bin.glb`; floor 6 × 2 m. `export`: `body` and `lid`, a copy of the greybox (rim vertices within 0.35 mm), 88 triangles, 2 materials |
| Game | `assets/props/waste_bin.glb` (5 KB), wrapped by `scenes/world/park_furniture/waste_bin.tscn`, placed 18 times in the editor-owned `scenes/world/plaza_furniture.tscn`: `bin_0`–`bin_9` (the ring and room bins, which `gen_props` still notes so its trees and outer lamps keep clear) and `bin_o0`–`bin_o7`, at the positions the generator last emitted, 5 mm higher (its cylinder was sunk 5 mm). Not yet: the Boardwalk's 5 (`boardwalk_props/waste_bin.tscn` in `boardwalk_density.tscn`, turned π, opening toward the promenade) and a dozen generated bins in `boardwalk`, `north_sky_ride` and `park_program` |
| Card | `documentation/howto/model-the-bins.md` |
| Last hand-back | Starting state: `documentation/screenshots/handbacks/waste_bin-start-2026-09-27_2031/` |
| Next | Her word on the plaza's kind: `park_furniture/waste_bin.tscn` then wraps that shell's GLB (or the plaza scene instances several), and this blend retires. Fix on the way for the family: canvas options per prop and grain along vertical slats (R2/R3), normal and occlusion bakes (M1/M2) |

### inner_can — PRP-PARK-024, the bins' inner can

| | |
|---|---|
| Stage | **paint** (2026-09-27): her OK on the starting canvas ("fantastic looking"); PSD made and open in Photoshop. Before it: unwrapped (`kyt_unwrap` hints, `unwrap_parts.py`), game mesh made (6,070 triangles), starting canvas baked (plain); waiting for her OK on the look |
| Holder | Christina: painting in the PSD |
| Model | `assets/source/props/inner_can.blend`. `reference` (locked): the plaza greybox bin, the Boardwalk bin, floor. `export`: `can` (hollow, tapered, stepped upper band, rolled rim), `handle_l`/`handle_r`, `liner` (a thin black plastic film pulled over the rim to an uneven, pleated hem held above the grips, bunched round the lip like a scrunchie, stretch lines down the inside) closing on `liner_void`, a pure black disc at 0.40 m, the Sims-style black hole (both `kyt_collision = none`; `add_liner.py`, seeded); 0.50 m across the rim, 0.57 m across the grips; 6,256 triangles; `plastic`, `liner`, `void`. Shaped by `park_bins_shape.py` (kept in `handbacks/inner_can-start-2026-09-27_2138/`) |
| Paint | `assets/source/textures/inner_can/`: `inner_can_colour.png` (2048, 1,005 px/m), `inner_can_orm.png` (1024), `inner_can_uv_guide.png`; PSD `assets/source/textures/inner_can/inner_can_colour.psd` (`paint` layer, locked UV guide) |
| Game | `assets/props/inner_can.glb` (132 KB), wrapped by `scenes/world/park_furniture/inner_can.tscn`; inside `hooded_bin.tscn`; not placed on its own |
| Last hand-back | Canvas: `documentation/screenshots/handbacks/inner_can-canvas-2026-09-27_2308/`; before it `documentation/screenshots/handbacks/inner_can-2026-09-27_2233/` (the scrunchie lip; `liner_close.png`, `looking_in.png`); before it `inner_can-2026-09-27_2228/` (black liner, black hole), `inner_can-2026-09-27_2220/` (first liner); starting state `inner_can-start-2026-09-27_2138/` |
| Next | Her saved passes: with the save hook on, each save sends the bin to the game; "handed back" runs `python3 tools/prop_handback.py inner_can`. A shape change now goes in `assets/source/props/inner_can_source.blend` (the parts), then Rebuild game mesh. Earlier: Her notes on the shape (any part in `export` is hers to reshape; a shell refitted round a changed can: `park_bins_shape.py`'s `can_reference` brings the new can in). Then unwrap, game mesh and canvas. Where it stands: hers, undecided. It comes out of its shell at trash pick-up time: behaviour not built. States (her word, 2026-09-27): empty (the liner), full, overflowing, each fill its own part the scene switches on the park's schedule, added over the liner, which stays: a bit of it shows even full or overflowing (her word); not built. At the texture stage the liner wants a bump for the fine stretch lines (her word), by the painted-bump route (`paint_canvas.py` bump, `bump_to_normal.py`) |

### riveted_bin — PRP-PARK-025, riveted metal bin

| | |
|---|---|
| Stage | **paint** (2026-09-28): her painted pass handed back and in the game, committed at her word ("this looks good, commit and push"). Before it: the flaps work (hinged flaps, `bin_flaps.gd`) and open onto the inner can: the body a hollow shell, the can standing inside; game mesh made again (4,084 triangles) and its canvas and PSD made again on the new layout (the old PSD was untouched canvas) |
| Holder | Christina: may keep painting in the PSD |
| Model | `assets/source/props/riveted_bin.blend`. `reference` (locked): bin greybox and Boardwalk bin, floor, and the inner can (`kyt_reference_can`). `export`: `body` (0.62 × 0.58 m, 1.10 m, top corners rounded 0.15 m, a hollow shell, walls 15 mm, floor 25 mm up, inside a darker `aluminium_inside`; push openings 0.65 to 0.99 m through the front and back walls), `flap_front`/`flap_back`, `trim_front`/`trim_back` (rolled edge, a bolted band's width, 56 mm, 20 mm proud, rounded: chunkier at her word), `bar_front`/`bar_back` (a bolted bar, 42 mm), `kick`, and 38 family bolts (`bolt_trim_*`, `bolt_bar_*`, from the kit, 7 mm proud, in `aluminium_bolts`, the bin's paint 15% darker; `add_family_bolts.py`); 46 parts, 7,620 triangles; `aluminium`, `flap`, `aluminium_bolts`. The can clears its inside by 17 mm |
| Paint | `assets/source/textures/riveted_bin/`: `riveted_bin_colour.png` (2048, 582 px/m), `riveted_bin_orm.png` (1024), `riveted_bin_uv_guide.png`; PSD `riveted_bin_colour.psd` (made again 2026-09-28 on the new layout; `paint`, locked UV guide) |
| Game | `assets/props/riveted_bin.glb` (199 KB): the body with collision, and `flap_front`/`flap_back` as their own nodes hinged on their top edges (Send splits parts marked `kyt_hinge`), wrapped by `scenes/world/park_furniture/riveted_bin.tscn` with the inner can standing inside (`inner_can.tscn`, 0.025 m up) and its `flaps` node, `bin_flaps.gd`: the player walks into a flap or presses interact looking at it, guests passing close now and then swing one, `wedged_open_deg` holds them open (overflowing); a swing peaks about 34 degrees, never past 40 (which keeps the two flaps apart). `tools/bin_flap_test.gd`. Not placed |
| Last hand-back | `documentation/screenshots/handbacks/riveted_bin-2026-09-28_0201/` (her painted pass: export, send, import and verify, seat, clearance 0 of 87, budget, ground contact known failures only; all passed). Before it: `riveted_bin-2026-09-28_0051/` (hollow shell, inner can inside; `flap_swung_in.png`; all passed). Before it: `riveted_bin-2026-09-28_0046/` (working flaps, black chamber); Canvas: `documentation/screenshots/handbacks/riveted_bin-canvas-2026-09-27_2308/`; before it `documentation/screenshots/handbacks/riveted_bin-2026-09-27_2214/` (bolts 15% darker than the bin); before it `riveted_bin-2026-09-27_2211/` (bolts in the bin's paint), `riveted_bin-2026-09-27_2200/` (chunky trim, bolts to the standard), `riveted_bin-2026-09-27_2157/` (bolts, shorter opening) and the starting state `riveted_bin-start-2026-09-27_2138/` |
| Next | Her saved passes: with the save hook on, each save sends the bin to the game; "handed back" runs `python3 tools/prop_handback.py riveted_bin`. A shape change now goes in `assets/source/props/riveted_bin_source.blend` (the parts), then Rebuild game mesh. Earlier: Her notes on the shape (any part in `export` is hers to reshape; a shell refitted round a changed can: `park_bins_shape.py`'s `can_reference` brings the new can in). Then unwrap, game mesh and canvas. Where it stands: hers, undecided. The sticker is texture; the painted (blue) variant is a second material or canvas. States: empty and overflowing, no full state (it is closed; her word, 2026-09-27), each fill its own part the scene switches on the park's schedule, added over the liner, which stays: a bit of it shows even full or overflowing (her word); not built |

### hooded_bin — PRP-PARK-026, square hooded bin

| | |
|---|---|
| Stage | **paint** (2026-09-27): her OK on the starting canvas ("fantastic looking"); PSD made and open in Photoshop. Before it: unwrapped (`kyt_unwrap` hints, `unwrap_parts.py`), game mesh made (950 triangles), starting canvas baked (plain); waiting for her OK on the look |
| Holder | Christina: painting in the PSD |
| Model | `assets/source/props/hooded_bin.blend`. `reference` (locked): as the riveted bin's, with the inner can. `export`: `body` (open-topped 0.60 m square, rounded corners, 0.72 m), `art_panel` (front), `hood` (skirt, flare, a window each side 0.185 m tall, rounded flat top at 1.08 m; windows made taller at her word); 948 triangles; `recycled_plastic`, `panel`. The can clears its inside by 10 mm |
| Paint | `assets/source/textures/hooded_bin/`: `hooded_bin_colour.png` (2048, 642 px/m), `hooded_bin_orm.png` (1024), `hooded_bin_uv_guide.png`; PSD `assets/source/textures/hooded_bin/hooded_bin_colour.psd` (`paint` layer, locked UV guide) |
| Game | `assets/props/hooded_bin.glb` (24 KB), wrapped by `scenes/world/park_furniture/hooded_bin.tscn`, which also instances `inner_can.tscn` inside (the windows show it); not placed |
| Last hand-back | Canvas: `documentation/screenshots/handbacks/hooded_bin-canvas-2026-09-27_2308/`; before it `documentation/screenshots/handbacks/hooded_bin-2026-09-27_2157/` (taller windows); starting state `hooded_bin-start-2026-09-27_2138/`, with `family_lineup.png` |
| Next | Her saved passes: with the save hook on, each save sends the bin to the game; "handed back" runs `python3 tools/prop_handback.py hooded_bin`. A shape change now goes in `assets/source/props/hooded_bin_source.blend` (the parts), then Rebuild game mesh. Earlier: Her notes on the shape (any part in `export` is hers to reshape; a shell refitted round a changed can: `park_bins_shape.py`'s `can_reference` brings the new can in). Then unwrap, game mesh and canvas. Where it stands: hers, undecided. The art panel's picture is texture. States: empty (the inner can's liner, through the windows), full, overflowing (her word, 2026-09-27), each fill its own part the scene switches on the park's schedule, added over the liner, which stays: a bit of it shows even full or overflowing (her word); not built |

### recycling_bottle — PRP-PARK-027, bottle-shaped recycling bin

| | |
|---|---|
| Stage | **paint** (2026-09-27): her OK on the starting canvas ("fantastic looking"); PSD made and open in Photoshop. Before it: unwrapped (`kyt_unwrap` hints, `unwrap_parts.py`), game mesh made (2,950 triangles), starting canvas baked (plain); waiting for her OK on the look |
| Holder | Christina: painting in the PSD |
| Model | `assets/source/props/recycling_bottle.blend`. `reference` (locked): as the riveted bin's, with the inner can. `export`: `body` (0.62 m base, 0.60 m body, 1.75 m to the cap), `label` (its own part and material for the brand), `cap` (32 grooves), `bezel` and `flap` at the mouth, 1.43 m up the shoulder; 2,984 triangles; `black_plastic`, `label`, `flap`. The can clears its inside by 6 mm |
| Paint | `assets/source/textures/recycling_bottle/`: `recycling_bottle_colour.png` (2048, 891 px/m), `recycling_bottle_orm.png` (1024), `recycling_bottle_uv_guide.png`; PSD `assets/source/textures/recycling_bottle/recycling_bottle_colour.psd` (`paint` layer, locked UV guide) |
| Game | `assets/props/recycling_bottle.glb` (92 KB), wrapped by `scenes/world/park_furniture/recycling_bottle.tscn`; not placed |
| Last hand-back | Canvas: `documentation/screenshots/handbacks/recycling_bottle-canvas-2026-09-27_2308/`; before it Starting state: `documentation/screenshots/handbacks/recycling_bottle-start-2026-09-27_2138/` |
| Next | Her saved passes: with the save hook on, each save sends the bin to the game; "handed back" runs `python3 tools/prop_handback.py recycling_bottle`. A shape change now goes in `assets/source/props/recycling_bottle_source.blend` (the parts), then Rebuild game mesh. Earlier: Her notes on the shape (any part in `export` is hers to reshape; a shell refitted round a changed can: `park_bins_shape.py`'s `can_reference` brings the new can in). Then unwrap, game mesh and canvas. Where it stands: hers, undecided. Height is from her picture (about 1.6 times the riveted bin); hers to change. States: empty, full, overflowing (her word, 2026-09-27), each fill its own part the scene switches on the park's schedule, added over the liner, which stays: a bit of it shows even full or overflowing (her word); not built. Recycling liners are clear in this park (her word, 2026-09-27): its fill states show a clear bag, not black |

### street_bin — PRP-TOWN-004, street bin outside the park

| | |
|---|---|
| Stage | **paint** (2026-09-28): her first painted pass handed back and in the game (all passed), committed; unwrapped, game mesh (7,922 triangles), canvas with the quatrefoil lattice and lid-band holes, PSD with its hole layers |
| Holder | Christina: may keep painting in the PSD |
| Model | `assets/source/props/street_bin.blend`. `reference` (locked): the plaza greybox bin and the Boardwalk bin, floor, for scale. `export`: 23 parts from `street_bin_shape.py` (with the start frames): plinth and four feet, bottom band, lattice shell (300°), rim, six flat posts every 60° (three run up to the lid), the door (the back-right 60° sector with rails, stile and two hinges), canopy lid (band and ridged dome), inner can with a black plastic `liner` over its rim, its lip bunched like a scrunchie, closing on `liner_void` at 0.58 m (`kyt_collision = none`; `add_liner.py`), and 21 family bolts (three on each post, one through the lid band into each tall post; from the kit, 7 mm proud, in `painted_steel_bolts`, the bin's paint 15% darker; `add_family_bolts.py`). 0.6 m across, rim 0.8 m, top 1.2 m; 46 parts, 9,748 triangles; `painted_steel`, `plastic`, `painted_steel_bolts`, `liner`, `void` |
| Paint | `assets/source/textures/street_bin/`: `street_bin_colour.png` (2048, 465 px/m; a 20 px fold on the rim), `street_bin_orm.png` (1024), `street_bin_uv_guide.png`, `street_bin_holes.png`; PSD `assets/source/textures/street_bin/street_bin_colour.psd` (`paint` layer, locked UV guide, and the hole layers: metal under the holes, `UV guide: holes (Claude)` on top) |
| Game | `assets/props/street_bin.glb` (1,432 KB; her painting, holes as alpha mask; textures VRAM-compressed with mipmaps), wrapped by `scenes/world/park_furniture/street_bin.tscn`; not placed |
| Reference | `documentation/reference/street_bin/lattice_street_bin_open_door.webp` (her photo, 2026-09-27): dark green lattice bin, quatrefoil perforations, canopy lid with a round hole, diamonds and a recycling mark, door swung open |
| Last hand-back | `documentation/screenshots/handbacks/street_bin-2026-09-28_0019/` (her first pass: export, holes, send, import and verify, seat, clearance 0 of 87, budget, ground contact known failures only; all passed). Before it: Preview `documentation/screenshots/handbacks/street_bin-preview-2026-09-28_0000/`: the old holes' marks gone (grey on the lattice's metal 30.5% → 3.0%) after the under layer was made from her paint (`street_bin-fixpreview-2026-09-27_2358/`, unsaved: her save); bigger holes: `street_bin-holes-2026-09-27_2332/`; canvas: `documentation/screenshots/handbacks/street_bin-canvas-2026-09-27_2308/`; before it `documentation/screenshots/handbacks/street_bin-2026-09-27_2233/` (scrunchie lip); before it `street_bin-2026-09-27_2228/` (black liner, black hole), `street_bin-2026-09-27_2220/` (first liner), `street_bin-2026-09-27_2214/` (bolts 15% darker than the bin), `street_bin-2026-09-27_2211/` (bolts in the bin's paint), `street_bin-bolts-2026-09-27_2156/` (family bolts); starting state `street_bin-start-2026-09-27_2119/` |
| Next | Another saved pass: the save hook sends it; "handed back" runs `python3 tools/prop_handback.py street_bin`; commit on her word (the first pass is committed). Where it stands outside the park: hers. A shape change goes in `street_bin_source.blend`, then Rebuild game mesh |

### perforated_metal_bench — PRP-PARK-018

| | |
|---|---|
| Stage | **paint**: canvas with the 2× perforated mesh handed back 2026-09-25 18:30 (all passed), sent to the game; PSD ready with its hole layers. Model built by Claude at her request from her 2026-09-11 photo, chunkier, with the family's bolts; game mesh 1,964 triangles. Her repainted colour (committed `39d0eae`) shrunk losslessly on 2026-09-29, the source and Godot's extracted copy 1,803 → 1,160 KB each, and sent again: GLB 1.9 → 1.3 MB, geometry and pixels unchanged |
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

### fern_fan — PRP-PLANT-011, coastal fern fan (the palm beds' fern)

| | |
|---|---|
| Stage | **canvas** (2026-09-27): moved from Godot to Blender, then made cartoony at her word, then 0.85× (2026-09-28, her "scale down the ferns a little"): 1.1× its Godot size; starting canvas in the game, not yet painted |
| Holder | Christina: her look at the cartoony fern; "open it in Photoshop" to paint |
| Model | `assets/source/props/fern_fan.blend`. `reference`: the Godot fern (seven fronds, 406 triangles) and `plant_base`, the soil line Check places it by. `authored/courses`: the seven Godot Path3Ds as Bezier curves (within 0.24 mm; resolution 48), scaled 1.3× at the cartoony pass. `authored/blades`: `blade_mature`, `blade_young`, broad outlines (32 triangles each) whose pinnae are cut from the texture. `export`: seven fronds, each bending its blade along its course (`kyt_course_blade`, Width = the frond's own span) with `kyt_frame_normals`; merged on Send. 224 triangles, one material |
| Paint | `assets/source/textures/fern_fan/`: `fern_fan_colour.png` (1024, about 1,000 px/m; round pinnae, about six a side, cut into the alpha and `fern_fan_cutout.png` by `paint_canvas.py --leaflets` from `PROP_LEAFLETS["fern_fan"]`), ORM (256), UV guide. No PSD yet |
| Game | `assets/props/fern_fan.glb`, wrapped by `scenes/world/coastal_palm_fern_fill.tscn` (its old Path3Ds and `coastal_palm_fern_fill.gd` retired; git holds them), so every placement kept its place: the palm beds, arrival curbs, parkway bed and fern bowl, and the arrival rings' doubled ferns (`fern_scale` 2, now 2.6× the old size) |
| Proof | Moved unchanged first: every leaf within 15 mm of Godot's (median 1 mm; the largest where outer tips turn down), in-game frames 1–3% of pixels at pinna edges. Godot's two-tone fishbone (half the pinnae wound the other way) was kept by `kyt_normals_up`, then dropped with the pinnae |
| Last hand-back | `documentation/screenshots/handbacks/fern_fan-2026-09-28_0030/` (0.85×, `plant_resize.py`; all pass); before it `fern_fan-2026-09-27_2331/` (cartoony: tests, clearance 0 of 87, budget, ground contact pass; `game/` frames, `fern_cartoon.py`); the unchanged move `fern_fan-2026-09-27_2314/` |
| Next | Her look. The arrival rings' `fern_scale` is hers if the ferns now bury the bed. To paint: `python3 tools/prop_handback.py fern_fan --open`; to change the pinnae: `PROP_LEAFLETS`, `--leaflets --cutout-only`. Commit on her word |

### hakone_grass — PRP-PLANT-018 to 021, Lemon Zest Hakone grass clump (vA, vB; rows and rings instance it)

| | |
|---|---|
| Stage | **model** (2026-09-27): moved from Godot to Blender, then made cartoony and chubbier at her word, then pulled in and up (2026-09-28, her "looks a little weird in context"), then rebuilt the same night after the stylized clump she pointed to ("this is how we should do our hakone grass"): broad strap leaves arching from the centre, her accepted shape (a one-way flowing version the same night: "the radiating ones are not acceptable at all", "only the hakone grass in the top left is acceptable"; restored); no texture (the stripe is geometry) |
| Holder | Christina: her look |
| Model | `assets/source/props/hakone_grass.blend`. `reference`: the Godot vB clump (72 blades) and `plant_base`. `authored/courses`: 16 Bezier courses, one per leaf (`course_mature_00` to `11`, `course_young_00` to `03`), each rising steeply and bending over more toward its tip, by how far it leans: grab a course's points to reshape its leaf. `authored/blades`: `blade_mature`, `blade_young`, 48 triangles each: green edge strips and the lemon stripe, broad (66 and 56 mm half-width), narrow at the crown, full, then tapering to a point, channelled along the midrib. `export`: one leaf per course (`kyt_course_blade`), shaded by its own faces so the channel reads; the four young upright leaves carry `kyt_merge_group = young`. 0.48 m tall, 0.93 m across. Shaping script `hakone_arch.py` with its hand-back; the previous shape in `assets/source/archive/hakone_grass_checkpoints/`; the rejected flowing shape's script (`hakone_flow.py`) is kept with its hand-back only as a record |
| Game | `assets/props/hakone_grass.glb`: `hakone_grass_visual` (12 leaves) and `hakone_grass_young` (4, vB only), wrapped by `scenes/world/hakone_grass.tscn`, whose small `hakone_grass.gd` keeps `catalog_variant` (vA hides the young mesh; StaticMerge skips hidden meshes). vB 768 triangles (the Godot clump 3,456) |
| Reference | The stylized clump she pasted in chat, 2026-09-28 (not saved in the project): about sixteen broad, smooth pointed leaves, upright in the middle, arching out and drooping at the edge, wider than tall |
| Proof | Moved unchanged first: within 0.9 mm (median 0.14 mm); frames 0.6–1.9% of pixels at blade edges |
| Last hand-back | `documentation/screenshots/handbacks/hakone_grass-2026-09-28_0313/` (the accepted arching shape restored: palm and catalog tests with 12 and 16, clearance 0 of 87, budget, ground contact pass; GLB 36 KB); the rejected flowing shape `hakone_grass-2026-09-28_0305/`; the first arching hand-back `hakone_grass-2026-09-28_0226/` (arching strap leaves, `hakone_arch.py`: palm and catalog tests with the new counts, clearance 0 of 87, budget, ground contact pass; GLB 36 KB); before it `hakone_grass-2026-09-28_0040/` (pulled in and up, `hakone_compact.py`, context frames at eye height; all pass); before it `hakone_grass-2026-09-27_2359/` (tests, clearance, budget, ground contact pass; `game/` frames of all three stages; `hakone_cartoon.py`, `hakone_chubby.py`) |
| Next | Her look. Commit on her word |

### purple_hakone_grass — PRP-PLANT-059 and 060, the Hakone clump in the Purple Heart's purples (vA, vB; not placed)

| | |
|---|---|
| Stage | **model** (2026-09-29): her "maybe instead of purple heart we do a purple version of our hakone grass" (to the other plant session), then "yes do the purple hakone", "create another randomization of the blades on the purple hakone" |
| Holder | Christina: her look; where it goes ("nothing for now" on swapping the Purple Heart's placements) |
| Model | `assets/source/props/purple_hakone_grass.blend`: a copy of `hakone_grass.blend`. Its four materials are the Purple Heart's purples: blade linear (0.126, 0.025, 0.205), edge (0.04, 0.011, 0.095), the young a step lighter. Its 16 courses are re-randomized: each turned up to 14 degrees, leaning up to 8 degrees more or less, 0.9 to 1.1 as long (seed 29). 768 triangles (vB), 0.46 m tall. A Purple Heart plant is 14 sprigs, about 3,390 |
| Game | `assets/props/purple_hakone_grass.glb`, wrapped by `scenes/world/purple_hakone_grass.tscn` and `_tuft_va` / `_tuft_vb`, on `hakone_grass.gd` (it now finds the young mesh by its name's ending). Checked headless: vA 9 blades, vB 12, the lemon Hakone unchanged. Not placed |
| Next | Where it replaces the Purple Heart, when she says |

### purple_heart_sprig — PRP-PLANT-015 to 017, Purple Heart sprig (rows, the cluster, the arrival rings and hanging boxes instance it)

| | |
|---|---|
| Stage | **canvas** (2026-09-28): moved from Godot to Blender, then made cartoony after the prototype she was shown ("looks great"), then 1.15× at her word: 1.5× its Godot size; starting canvas in the game, not yet painted |
| Holder | Christina: her look; "open it in Photoshop" to paint |
| Model | `assets/source/props/purple_heart_sprig.blend`. `reference`: the Godot sprig (6 pairs, flowered) and `plant_base`. `authored/courses`: the stem course (exact), scaled 1.3×. `authored/blades`: `blade_leaf`, `blade_young`, 8-triangle cards 0.36 m long whose leaf is cut from the texture. `export`: `stem` (`kyt_course_stem`: six sides, 18 to 9 mm), `leaves_4` to `leaves_7` (points holding each leaf's share up the stem, turn, rise and length; `kyt_leaves_on_course` places the blades; `kyt_normals_up`; merge groups `pairs_<n>`), `flower` (`kyt_at_course_tip`, 1.6×; merge group `flower`) |
| Paint | `assets/source/textures/purple_heart_sprig/`: colour 512 (about 970 px/m; one full, soft-pointed leaf and a pale midrib per card, `PROP_LEAFLETS["purple_heart_sprig"]`, style "leaf"), cut-out, ORM 128, UV guide. No PSD yet |
| Game | `assets/props/purple_heart_sprig.glb` (stem, four leaf meshes, flower), wrapped by `scenes/world/purple_heart_sprig.tscn`, whose small `purple_heart_sprig.gd` keeps `leaf_pair_count` (4–7) and `flowered` and shows those meshes. `leaf_scale` retired: the two catalog sprigs that set it (row vA 0.92, row vB 1.08) lost the line. A 6-pair sprig: 96 leaf triangles (was 192) |
| Proof | Moved unchanged first: stem 1.0 mm, leaves 0.1–0.7 mm across the four variants, flower exact; frames 0.15–0.3% of pixels |
| Last hand-back | `documentation/screenshots/handbacks/purple_heart_sprig-2026-09-28_0031/` (1.15×, `plant_resize.py`; all pass); before it `purple_heart_sprig-2026-09-28_0012/` (tests, clearance 0 of 87, budget, ground contact pass; `game/`, `prototype/`, `ph_cartoon.py`) |
| Next | Her look (it reads lighter purple than the old, whose leaves half caught the light from below). To paint: `python3 tools/prop_handback.py purple_heart_sprig --open`. Commit on her word |

### The approach landscaping kit (2026-09-28): palm_planter PRP-PLANT-066, scallop_edging PRP-FENCE-006, azalea_bush PRP-PLANT-053, azalea_tree PRP-PLANT-055, hibiscus_shrub PRP-PLANT-057, their sphere versions azalea_bush_sphere PRP-PLANT-054, azalea_tree_sphere PRP-PLANT-056, hibiscus_shrub_sphere PRP-PLANT-058, the hibiscus trees hibiscus_tree PRP-PLANT-061 and hibiscus_tree_sphere PRP-PLANT-062, box_shrub (ID when catalogued)

| | |
|---|---|
| Stage | `hibiscus_tree` and `hibiscus_tree_sphere` (2026-09-29, her "give the hibiscus tree the bark too", then "build both versions" when there was none): **model**, with Christina for review, sent and wrapped, not placed; made from the hibiscus as the azalea tree is from its bush (`SPECIES["hibiscus_tree"]`, `_grow`), on the azalea tree's crown size, sizes and barked trunk, their own generated canvases (her hibiscus painting doesn't carry over: its own UVs); `plant-lineup-2026-09-28/hibiscus_trees.png`. `hibiscus_shrub` and `hibiscus_shrub_sphere`: **paint** since 2026-09-29, with Christina: PSDs made by `prop_handback.py --open` (paint over the generated canvas, UV guide on top, the leaves' cut-out at Multiply, the leaf colour under the paint); the top row holds each flower 12 times (four colourways, three shades) and the game reads every copy. Remade the same day after her leaf and flower changes (the first PSDs, unpainted, set aside): midribs short of the tips, lighter leaf rims and drop shadows, the same on the petals; flowers all round the bush and the leaf clusters spread (`hibiscus_flowers_all_sides_trial.png`, `hibiscus_leaves_petals_trial.png`, identical to the build). Medium 11 / 10 everyday flowers, 214 / 192 triangles. From here their canvases are hers: no `paint_canvas.py --overwrite` or `unwrap_blades.py --overwrite` on either, so a shape change must keep the islands where they are. The rest: **model** (2026-09-28), **unplaced**: shaped by Claude at her direction and tried along the approach (planters at the palms, scalloped strips); she called that "a big step backwards, the layout of the beds and roads dont make any sense", and it was taken back out the same hour. The approach is as committed; the pieces stay for later |
| Holder | Christina. Her direction meanwhile: "focus on getting each plant right" (azalea and hibiscus are plants in that queue) |
| Model | `assets/source/props/hibiscus_tree.blend` and `hibiscus_tree_sphere.blend` (new_prop.py, then `leaf_skin.py`): medium 2.75 / 2.27 m tall, small 2.15 / 1.79, large 3.49 / 2.96; medium 368 / 276 triangles everyday, 820 / 550 in High Summer, 162 / 146 in winter. `assets/source/props/palm_planter.blend` (rounded concrete rim 2.07 m across, 0.4 m high, collides; mulch 0.3 m up, an opening for the trunk; 1,120 triangles), `scallop_edging.blend` (a 1.32 m run of six half-discs 0.16 m high, visual only; 192), `azalea_bush.blend`, `azalea_tree.blend`, `hibiscus_shrub.blend`, built by `tools/blender/leaf_skin.py` around textures (her "way too many triangles", "needs to be optimized for using textures", and the Mario Kart trees: "lots of painted on leaves layered in shaped sections"): `authored/blades/blade_leaf`, a domed section card of 8 triangles with some 30 painted leaves shingled on it; `authored/blades/blade_bloom`, a hexagon card whose texture paints the flowers, every colourway side by side on the canvas (`kyt_slots`); `export/bush`, the base (azalea a gumdrop 1.1 by 1.2 m; hibiscus `BOXY`, her "a bit more boxy and round, but just as tall", 1.2 by 1.3 m; the tree `EGG` on a trunk, 2.86 m) whose `kyt_leaf_skin` modifier shingles the section over it (83, 111, 159 sections; anchored under their middles, more on the crown); `export/blooms/blooms`, points each carrying a turn and a size (`kyt_turn`, `kyt_size`), the bloom card placed on each by `kyt_blooms_on_points` (move a point to move a bloom), each set just above the leaves under it, measured by rays cast onto the built skin (her "the blooms on the hibiscus are being occluded by leaves"; flowers seen, leaves against none, six views: hibiscus 82%, bush 83%, tree 84%, the rest at the edges seen past their neighbours, `bloom_probe.py`): azalea trusses painted as rounded bunches of six to eight mixed blooms (her "azalea blooms need to be clustered together" "more intensely and more densely", "the clusters are a little funny", "should have varying sizes": 0.6 to 1.3 times; 10 on the bush, 24 on the tree), hibiscus flowers in close twos and threes (13); sections vary in size by 28%. Through the year (her words: "the clusters should be increased three fold" at the flower's peak, "during winter we will treat these as evergreen shrubs"): `blooms` is the baseline and `blooms_peak` twice as many clusters again, each a merge group; the wrappers' `season` shows the baseline outside Winter Lights and both in the peak chapter (azaleas Spring Reopening, hibiscus High Summer; `seasonal-missions-and-decor.md`, "Planting through the year"). Triangles baseline / peak / winter: bush 952 / 1,072 / 892, tree 1,688 / 1,976 / 1,544, hibiscus 1,194 / 1,422 / 1,116. Sizes (her "one smaller and one larger (flowers stay the same size)"): the bush and the hibiscus each come small (0.75x), medium and large (1.3x) in one file, the base scaled and the sections and flowers not (flower clusters by the surface), each size its own merge groups `<size>`, `<size>_blooms`, `<size>_blooms_peak` on the one canvas; `size_small` and `size_large` sit at the origin, hidden in the viewport; the wrappers' `size` picks one. The tree too (her "do the same for the azalea tree"), its trunk and lift scaled with the crown: 2.18 / 2.87 / 3.67 m, about 1,080 / 1,660 / 2,690 triangles at baseline (3,210 large at peak). Azalea 1.07 / 1.36 / 1.69 m, 648 / 952 / 1,338 triangles at baseline; hibiscus 1.13 / 1.43 / 1.79 m, 794 / 1,194 / 1,880. Triangles: bush 952 (was 2,361), tree 1,688 (4,486), hibiscus 1,194 (2,132). Core showing 0.5, 0.9 and 2.5% (`bald_probe.py`). The hibiscus's shape and flowers are hers ("the hibiscus look good"). Earlier shapes in `assets/source/archive/landscape_kit_checkpoints/`  **Triangle cut** (her "all of these use way too many triangles"): sections now 4-triangle cards about 0.84 m across with some 35 painted leaves, a third as many; cores 8-sided on every other ring; flower cards 4 triangles; the tree's trunk 6-sided; crown sections 0.7 the size facing straight up, a closer crown scatter; the hibiscus's sections droop more over its shoulders. The large tree reproportioned (her "the largest one looks weird"): 1.3 across, 1.12 tall, the trunk 1.6. Triangles, small / medium / large at baseline (winter; peak): azalea 192 / 272 / 404 (168 / 232 / 336; 240 / 352 / 540), hibiscus 204 / 296 / 500 (184 / 244 / 396; 268 / 448 / 740), tree 324 / 488 / 708 (268 / 392 / 568; 436 / 680 / 988). Coverage was then found measured wrongly: since the sizes went in, the probes saw all three sizes and the peak flowers at once, the large hiding the medium's gaps. Measured on the medium alone: azalea 2.1%, hibiscus 7.5%, tree 1.5%. Denser since (azalea and tree spacing 0.31 m, hibiscus 0.28 m, anchor 0.2 m on all three): azalea 0.9%, hibiscus 2.3%, tree 1.1% (with its bigger leaves); flowers seen 82, 85, 84%. Medium at baseline now azalea 308, hibiscus 364, tree 556 triangles (tree small / large 348 / 788) (small / large: azalea 208 / 456, hibiscus 244 / 632). Flower cards are lifted so none dips under the soil. **Semi-domes** (her Mario Kart tree, "our shrubs will be assembled from a series of these types of shapes"): `leaf_skin.py` now builds greenery from one painted dome per plant file (`DOME_SHAPES`). **Half spheres** (her "think of the shape of an ice cap vs a half sphere", "the dome segments are too small", and a second Mario Kart tree, "the leaves are different on the example but the formfactor is the same"): the three shrubs rebuilt from big half spheres of 24 triangles, a crown dome sunk among one course round a base well inside them (`authored/domes`, `kyt_dome_skin`, a 6-sided core on every third ring): azalea base 0.8 by 1.15 m, dome reach 0.94 m, domes small / medium / large 4 / 5 / 10, 1.08 / 1.37 / 1.71 m tall; hibiscus base 0.78 by 1.2 m, 4 / 5 / 12, 1.15 / 1.45 / 1.81 m; tree egg 1.1 by 1.75 m, reach 1.0 m, 7 / 13 / 16, 2.24 / 2.81 / 3.52 m. Triangles without flowers, small / medium / large: azalea 138 / 162 / 282 (sections 168 / 268 / 388), hibiscus 138 / 162 / 330 (224 / 312 / 528), tree 204 / 348 / 420 (292 / 460 / 648), trunks aside. Core showing (medium, eye height): azalea 0.6%, hibiscus 1.2%, tree 0.2%. The flowers are unchanged and still placed from the base, so some stand off the domes' edges (her "dont worry about the flowers yet"). The section build is archived with its canvases and tools: `archive/landscape_kit_checkpoints/sections_2026-09-28/`. **One egg and one crown dome** (her "the base of each shrub can be one singular sphere or egg shape", "the goal is to simplify", "its like an unshelled boiled egg shape", "start with just one on the crown", "it needs to be almost flush", "maybe rotated counterclockwise a bit" meaning turned round its upright axis, "right is good"): each shrub is now `authored/blades/blade_body`, a peeled egg (`egg_shape`, 56 triangles) standing on its broad end, its leaves hanging from the top and their tips its hem on the soil, and one half sphere (24 triangles) on its crown, sunk almost flush (`crown_sink`) and turned 15 degrees (`crown_turn`); both grow with the size. No core. Egg across by high, medium: azalea 1.0 by 1.15 m (crown reach 0.8, sunk 0.48), hibiscus 1.21 by 1.38 (0.96, 0.575), tree 1.64 by 1.87 on its trunk (1.3, 0.78). Heights small / medium / large: azalea 0.90 / 1.20 / 1.56 m, hibiscus 1.08 / 1.43 / 1.86, tree 2.18 / 2.79 / 3.68. **80 triangles without flowers at every size** (the tree 92 with its trunk). Then the crown a saucer (her "the bowl of the upside down dome segment on top of the egg is too deep, again think polar ice cap, or saucer"; "the right i good, but needs to be rotated a litte"; a deep bowl with the saucer over it was tried and not kept, "lets stick with the left one"): the egg's own outline from its top 60 degrees round, 1.04 times the egg and 2 cm off it (`crown_cap`, `cap_down` 60), turned 22.5 degrees from the egg's facets (`crown_turn`), sized with the egg across and up at every size. Heights small / medium / large: azalea 0.88 / 1.17 / 1.53 m, hibiscus 1.05 / 1.40 / 1.82, tree 2.14 / 2.74 / 3.48. Still 80 triangles. The egg's hat since brought down to 72 degrees like the sphere's (her "the egg's hat could use the same increase in depth that we gave to the one on the sphere"), `shrubs_egg_hat72_sizes.png`, then its brim flared 5% past the egg's widest as the sphere's is (her "good size, now make it flare a bit"), `shrubs_egg_hat_flare_sizes.png`. **Fluffier eggs** (her "should hte egg shaped ones hae an additional tier", "try it on the eggs", "lets flare the new tier", "lets give them a little like two or three leaf topper", "still too sprouty", "right row looks good", "our tiers need to be offset on their horizontal rotation", "the offset rotations need to be a bit more random", "in general the leaves look a bit too droopy", "flair the other tiers more", "we like a fluffier shrub", "flair hibiscus a bit more", "azalea looks good"): each egg shrub now also wears a second tier (`blade_tier`, `body_tier`: a band of leaves from 64 to 100 degrees round the egg, 5 cm off it, its hem flared 20%, the hibiscus 25%, 16 triangles) and a topper (`blade_topper`, `body_topper`: three leaf cards lying 100 degrees from upright over the hat, the hibiscus's 110 (her "lay down the top most sprouts on the hibiscus a little more", `hibiscus_topper_110.png`; a tiny second hat in its place was tried and not kept, "no lets skip this new hat"; her "just make the top tier a little shorter", "not the sprouts": the hibiscus's hat to 64 degrees and its band's top to 56, `hibiscus_shorter_hat.png`; then "perfect do the same ot the azaleas": the azalea bush and tree too, `azaleas_shorter_hat.png`; the sphere versions keep 72), 0.28 / 0.3 / 0.38 m, 6 triangles); the hat flares 15% (hibiscus 20%); the layers turn irregularly (egg 0, hat 22.5, band 36.8, topper 71.4 degrees); every shrub's painted leaves splay 25 degrees alternately in a herringbone (`splay` in `PROP_LEAFLETS`, the sphere versions too). 102 triangles without flowers (the tree 114 with its trunk); the sphere versions stay 80. Canvas 413 / 345 / 255 px/m (five islands). `plant-lineup-2026-09-28/shrubs_egg_fluffy_sizes.png`; trials `eggs_second_tier_trials.png`, `eggs_tier_flare.png`, `eggs_leaf_topper*.png`, `eggs_leaves_less_droopy.png`, `eggs_turns_and_leaves.png`, `eggs_fluffier.png`, `hibiscus_more_flare.png`. The flowers on all six seated on the leaves as built: each carried in to the egg or hat it meets, facing as that face does, lifted only to clear its card (they had been lifted off the base's ideal outline and stood off the egg's flat faces), `flowers_seated_trials.png`. `plant-lineup-2026-09-28/shrubs_egg_saucer_sizes.png`; the trials `azalea_egg_polar_cap.png`, `azalea_egg_cap_turns.png`, `azalea_egg_bowl_and_saucer.png`. The painted leaves on the egg and crown grow and shrink with the size (0.75 / 1.3 times). The second version, her "a sphere instead of a egg, and smaller" (`DOME_SHAPES["sphere"]`): tried, not built into the files: medium azalea sphere reach 1.2 with crown 0.68 sunk 0.4 (0.93 m tall), hibiscus 1.35 / 0.76 / 0.45 (1.04 m), tree 1.9 / 1.07 / 0.64 (2.30 m), `plant-lineup-2026-09-28/shrubs_sphere_crown_trials.png`; with the saucer, spheres of reach 1.2 / 1.35 / 1.9 (0.90 / 1.01 / 2.26 m tall medium), `shrubs_sphere_saucer_trials.png`; the hat brought down to 72 degrees round the ball on the spheres (her "on the sphere versions, the hat can come down a little further"; `cap_down` 72; "it looks good because it hits around the top third of the sphere"), `shrubs_sphere_saucer_72.png`; its brim flared 2% wider than the ball (her "have the hat flare out be larger than the base sphere by like 2%"; `cap_flare` 0.02), `shrubs_sphere_saucer_flare.png`. **Sphere versions as their own files** (her "it oculd be a bit more pronounced, and yes they can be their own files"): `azalea_bush_sphere.blend`, `hibiscus_shrub_sphere.blend`, `azalea_tree_sphere.blend` (`SPECIES["<shrub>_sphere"]`: the egg version's leaf, flowers and sizes, a ball of reach 1.2 / 1.35 / 1.9, the hat 72 degrees down with its brim flared 5%). Heights small / medium / large: azalea 0.68 / 0.90 / 1.17 m, hibiscus 0.76 / 1.01 / 1.31, tree 1.78 / 2.26 / 2.94. 80 triangles without flowers, as the eggs. Check clear. `plant-lineup-2026-09-28/shrubs_sphere_sizes.png`. The ice-cap trials of the azalea are kept at her word ("keep these for future use"): `archive/landscape_kit_checkpoints/icecap_domes_2026-09-28/`. **Box shrub** (her "a small box shrub that is just a singular one of these domes"): `box_shrub.blend`, one ice cap (`single`), 0.75 m across and 0.32 m high, 24 triangles, no core, no flowers, evergreen, one size (merge group `medium`). **Flowers, buds, leaf clusters, the ideal egg (2026-09-28/29)**, each at her word (the journals quote her): flowers rest on the leaves by their own shape, sunk 6 mm; the hibiscus a six-sided cone (`sides`, `dome` -0.07); the azaleas one six-sided trumpet per card, 0.21 m across (`radius` 0.105), in trusses of 7 to 11 round a main one, every other one small (`group`, `small`), a truss left under 60% dropped (`keep`); the azaleas' trusses gathered in clumps (`clump`, `clump_at`) spread over the body's smooth outline (`envelope_spots`), their flowers free to cross a brim onto leaves up to `behind` below (bush 0.15, tree 0.3 m), the peak's clumps free to overlap the baseline's; the sphere bush and tree seated out from the body's middle (`envelope`), dealt where their season's flowers are furthest off (`spread_seasons`), kept off a brim's rim, the sphere bush's clumps 2 to 4; buds, an 8-triangle spindle (`bud_card`, `cut_bud`), in clusters of 2 to 3 against a placed flower, at most one per group, azalea 0.171 m long and hibiscus 0.257 m, on the azaleas at most one light green unopened bud per cluster (`blade_bud_green`), none through a flower's middle, none standing off the leaves; leaf clusters, 3-leaf fans lying on the leaves (`sprig_card`, `strays`), 5 / 5 / 8; the ideal egg, her reference `documentation/reference/azalea_bush/egg_topiary_ideal_shape.png` measured into `EGG_IDEAL`, 0.75 of its height across, widest two thirds down, cut at 140 degrees for a broad base, heights kept; leaves painted in the dome's own proportions, widened only round its girth (`stroke` `warp`), so the egg's lower leaves are no longer stretched; the hibiscus topper 0.42 m; the spheres' hat brim flares 15% and they have the topper. Medium triangles, baseline / peak: azalea bush 606 / 1,424, hibiscus 234 / 436, azalea tree 1,574 / 4,086, sphere bush 582 / 1,394, sphere hibiscus 204 / 418, sphere tree 1,252 / 3,416. Screenshots in `plant-lineup-2026-09-28/`. **Shades (2026-09-29)**, her "vary the lightness and darkness of the flower blooms", "on the azaleas the lightest will be a light pink almost white, the dark will be almost fushia, and every shade in between", hibiscus "some blooms just being a slightly darker shade of red, by maybe 2%", "vary the leaves in darkness on each bush by about 3%": each colourway painted again in 5 shades (azaleas: near-white pink to near-fuchsia through the pink; the magenta and white round their own colour) or 3 (hibiscus: the colourway, 1% and 2% darker), side by side in its slot; each truss or group takes a shade, each of its flowers that or one step either way (`kyt_shade`); each dome leaf painted 0 to 3% darker. Then her "make the contrast a little less severe between the lightest and darkest flowers": the azaleas' shades reach three quarters of the way out (`spread` 0.75), pale pink to deep hot pink (`azalea_shades_softer.png`). Flowers, buds and leaves where they were; triangles unchanged. `shrub_bloom_shades.png`, `shrub_bloom_shades_before_after.png`, `azalea_bloom_shade_strip.png`, `hibiscus_bloom_shade_strip.png`. |
| Paint | `hibiscus_tree/`, `hibiscus_tree_sphere/`: colour 2048 (266 / 333 px/m) in the hibiscus's leaves and flowers (`PROP_LEAFLETS`, the shrub's), cut-out, ORM 256, UV guide, bark (`BARK`, as the azalea trees'), optimized. No PSD. `assets/source/textures/azalea_bush/`, `azalea_tree/`, `hibiscus_shrub/`: colour 1024 (about 800 px/m): the section's leaves (on the two shrubs 1.4 times bigger since her "on both shrubs scale up the leaves": azalea 0.22 m, hibiscus 0.22 m; the tree's too since her "scale up the leaves on the azalea tree too", 0.22 m; the hibiscus's leaf since her "the shape of the hibiscus leaves isnt right" a hardy hibiscus's, after her photos: palmate, three pointed lobes, saw-toothed, `lobes` and `teeth` style "saw" in `PROP_LEAFLETS`) (azalea fresh green pointed ovals, hibiscus dark blue-green scalloped, each dark at its stalk to light at its tip, overlap shadows, pale midribs, the section darker to its rim; `PROP_LEAFLETS` style `section`) and across the top the bloom card's colourways (`slots`: azalea pink, magenta, white; hibiscus red, pink, yellow-red, pink-white), cut-out, ORM 256, UV guide. No PSD yet. Since the half spheres (style `dome`, `cut_dome`): the dome's leaves in rings round its apex over a shaded fill, widened toward the rim by the dome's girth (`kyt_rings`), about 430 px/m (the dome is 1.9 m across flat); the bloom slots as before. Since the egg: colour 2048 (the egg's own island beside the crown dome's), the colour PNGs through `optimize_png.py`; with the saucer, azalea 501, hibiscus 419, tree 310 px/m. The sphere versions' canvases `textures/azalea_bush_sphere/`, `hibiscus_shrub_sphere/`, `azalea_tree_sphere/`: 2048, 537 / 478 / 339 px/m, the same leaves and flower slots, optimized. No PSD. `box_shrub/`: colour 512 (461 px/m), boxwood leaves 0.13 m, pointed ovals in rings round the apex over a shaded fill, a faint midrib (`PROP_LEAFLETS`, style `dome`; rounder leaves read as fish scales, bigger ones as an azalea: `plant-lineup-2026-09-28/box_shrub_leaves.png`), cut-out, ORM 128, UV guide. No PSD. The azalea trees' trunks (2026-09-29, her "give the same treatment to the texture of the shrub trees", after the coast live oak's bark): `azalea_tree_bark.png` and `azalea_tree_sphere_bark.png`, the oak's wavy vertical grain, red-brown highlights and 0.1 grooves over their own bark colour, no knots (`paint_canvas.py --bark`, `BARK`), the trunks unwrapped as the oak's limbs (`add_trunk` `tile`: one tile round, eight ridges); leaves, flowers and canvases unchanged (0 pixels; their ORMs kept as committed: today's paint code makes the flowers up to 10% rougher); `plant-lineup-2026-09-28/azalea_trees_bark.png` |
| Reference | `documentation/reference/azalea_bush/animal_crossing_azalea_bushes.webp` (her picture: AC azaleas, a hedge behind). Two more were pasted in chat and not saved: AC bushes on paving (hibiscus, holly, plumeria) and two AC hibiscus bushes. What they show: the same shingled greenery on every bush and hedge, darker broader leaves for the hibiscus, a few big flowers over the leaves |
| Game | The hibiscus trees: `hibiscus_tree.tscn`, `hibiscus_tree_sphere.tscn` on `hibiscus_shrub.gd`; sent (1,996, 1,721 KB), imported, probed headless: each size and season shows its own meshes (peak in High Summer, no flowers in winter), `bloom` slides the four colourways, the trunk wears its bark; catalog cards PRP-PLANT-061, 062. Not placed. `scenes/world/landscape_kit/`: a wrapper per piece; `azalea_bush.gd` (the bush and `azalea_tree.tscn`) and `hibiscus_shrub.gd` pick a colourway with `bloom`, sliding the `<prop>_bloom` material's UVs (`uv1_offset`) by a slot's width, worked out from the texture's; checked headless for all colourways. The tried arrangements `palm_planter_bed.tscn`, `strip_module_azalea.tscn`, `strip_module_hibiscus.tscn`, none placed; `strip_kit.gd` kept as text in the start folder. All three sent (GLBs 269 to 299 KB); as half spheres sent again (479, 571, 532 KB), imported, and checked headless: each size and season shows its own meshes (baseline, peak, bare in winter). As eggs sent again (763, 970, 1,078 KB) and checked the same way; with the saucer (764, 956, 1,092 KB), checked again. The sphere versions: `azalea_bush_sphere.tscn`, `hibiscus_shrub_sphere.tscn`, `azalea_tree_sphere.tscn`, each on its egg version's script; sent (738, 893, 1,043 KB), imported, and checked headless: every size and season shows its own meshes and `bloom` slides the flowers to each colourway. Not placed. The trees sent again with their bark (2026-09-29: 2,023 and 1,792 KB; nodes and triangles as before, the bark image added), imported; catalog cards PRP-PLANT-055, 056 re-captured. Every wrapper starts in High Summer (`season` 1; her "lets do summer and have the campaign start there"). `box_shrub.tscn` wraps its GLB, no script (one size, no flowers); sent (183 KB), imported, loads headless: one mesh, 24 triangles, double-sided, alpha-clipped. Not placed |
| Last hand-back | none; start folder `documentation/screenshots/handbacks/landscape_kit-start-2026-09-28/` (concepts, game frames); Blender renders of the reshape in `documentation/screenshots/plant-lineup-2026-09-28/` with `plant_lineup.blend` (the five plants linked side by side, a 1.7 m figure) |
| Next | Her look at the hibiscus trees (`hibiscus_trees.png`). Since 2026-09-29: the azaleas' triangle cost at peak (tree 4,086 medium). The hibiscus's flowers sit mostly round its hat. Before that: her look at the egg-and-saucer shrubs (`plant-lineup-2026-09-28/shrubs_egg_saucer_sizes.png`) and the sphere versions (`shrubs_sphere_sizes.png`, brim flared 5%). The tree's canvas is the thinnest (310 px/m). Then the flowers seated on the egg, when she turns to them. The box shrub is paused: she paused the session that made it (her "i didnt love what the other session came up with", "your direction is winning"); its files stay as they are. The hibiscus: her "the hibiscus look good" (boxy base, 12 flowers, four colourways). A hedge and a holly are the same skin with another base or leaf. A layout for the approach beds and roads that makes sense in plan comes before any planting revamp |

### coastal_live_oak — PRP-PLANT-049, California coast live oak (not placed)

| | |
|---|---|
| Stage | **game** (2026-09-29, her "send the oak to godot and swap it in"): sent and wrapped by `scenes/world/coastal_live_oak.tscn` in place of the Path3D oak (git `240d30f`), not placed. Three variants (her "we need to randomize the branches and stuff", choosing a few oaks from seeds that the game picks between): `a` as approved, `b` (seed 41, 3 major limbs, leaning 0.7 m, drooping toward 60 degrees) and `c` (seed 61, 5 major limbs, leaning 0.5 m, toward 250), each its own hat places, spins, tier bearings, leaf clusters, acorns, buds, litter and knots (`variants`, `variant_spec`; `oak_v27_variants.png`); a is unchanged point for point but fall's litter, which now rests on the soil (it dipped 1 to 4 cm under and Send's ground check refused it). The campaign opens in High Summer (her "lets do summer and have the campaign start there"): the wrapper, and the shrubs', start there. Before that, **model**, with Christina for review: a new Blender source to replace the catalog's Path3D oak (`scenes/world/coastal_live_oak.tscn`, unchanged so far). Her "replace our live oaks with a new model in our signature cartoony style. using the spherical shrubs we made, create a simplified version of a mature oak", then "they skip the main 'ball' base of the sphere and just keep the 'stack of hats'", no hat floating ("the tree greenery just floats with no branches ... we however can do better"), keyholes ("where you can see through the leafs"), "the dark green patches under the leaves should be defined as leves". Built by `tools/blender/leaf_skin.py -- coastal_live_oak` (`crown`): 19 segments, each the sphere shrub's hat with a second tier over it (her "i meant the top tier on each segment", "can we add another tier to each segment?", "under the sprout": the hat's shape at 0.6 as its own card and island, `blade_upper`, so its leaves are full size (her "yeah make that fix"), turned 36.9° more, its brim 0.15 m proud of the hat's leaves (0.3 until her "lets move the new tier down a little on each segment"), `upper`; the sprout on it; a raise of the tree's top hat, from reading "top tier" as the tree's, was undone); 72° down, turned 22.5°, with its three-leaf topper; the brim flared 30%, the shrubs' 15%, her "the top tier but not the sprout on the top of each dome needs to be flared more"; then her "flare the top most tier and sprouts too": the top hat 45% (`flare`, spread per hat by `kyt_clump_skin`); the sprouts flared up (her "flare means up", "right now they lay down too much", "they can tilt up a little bit"): 65° from upright, the shrubs' 100°, after trials at 100, 85, 72 and 60, `oak_sprout_up_trials.png`); 24 stray leaf clusters (her "can we add the random leaf clusters like how we added to the shrubs": the shrubs' `sprig_card` fans, 0.7 m leaves, spread evenly, only where a hat slopes 35° or more (`steep`), off the sprouts; `oak_v9_clusters_marked.png`); acorns (her "lets use the same base we used for the flower buds and make acorns", "some green some brown", "green in summer and brown in fall, fall can have a few acorns and leaves on the ground under the tree"): the buds' spindle, 0.36 by 0.2 m, 37 in clusters of 1 to 3 hanging from the brims on the crown's outside, green in merge group `summer_acorns`, the same places brown in `fall_acorns`; fall's litter, 10 acorns on their sides and 30 leaves (three single-leaf cards) under the tree, `fall_ground`; the fall foliage a second canvas (her "in fall the foliage needs to change color"); winter and spring the leafy tree too (her "its kind of unsettling... maybe we go back to the fall tree as a baseline, in winter it just gets more sparse ... just more see through parts in the leaves and the leaves maybe turn red-brown instead of yellow-red", "spring uses the same setup but makes the foliage bright green and the acorns become buds and there are more buds"; a bare tree of twigs, branchlets and hanging leaves, v15 to v17, was dropped): winter 3 of the brown acorns (`winter_acorns`), spring 89 leaf buds (`blade_leaf_bud`) in small groups scattered over the hats round the acorns' brim places and more, each standing out of the leaves (`spring_buds`, 712 triangles; her "the buds on spring are kind of in a line", when they sat side by side on the rims). Seasons: spring `spring_buds` on the spring canvas, summer `summer_acorns`, fall `fall_acorns` + `fall_ground` on the fall canvas, winter `winter_acorns` on the winter canvas; the foliage, sprouts and leaf clusters all year; `oak_v18_four_seasons.png` in four tiers (1, 4, 6, 8), leaning out 45% of the way, drooping lower on the photo's left; each hat on its own branch turning up into it (`hat_branches`: a leader, four major limbs forking into eight scaffold limbs, branches off them) from a short flared trunk (1.15 m radius at the foot, forking at 2 m). 10.43 m tall, 12.9 m across; 1,026 triangles of hats, 144 of leaf clusters, 1,140 of wood (the wood is the larger share: fewer sides or segments would cut it). Renders v1 (balls) to v10 in `documentation/screenshots/coastal-live-oak-2026-09-29/` (v9 "this works"; v10 two tiers a segment; v11 the upper tier's own leaves; v12 it 0.15 m lower; v13 acorns and fall, `oak_v13_summer_*`, `oak_v13_fall_*`; v14 fall as radial gradients, `oak_v14_fall_*`; v15 winter and spring, `oak_v15_*`; v16 branchlets, `oak_v16_*`; v17 their leaves, `oak_v17_*`, all dropped; v18 the leafy tree all year, `oak_v18_*`; v19 fall's holes, `oak_v19_*`; v20 the holes in winter only, `oak_v20_*`; v21 spring as winter in green, `oak_v21_*`; v22 the buds scattered, `oak_v22_*`; v23 bark and knots, `oak_v23_*`; v24 grain by girth at full strength, knot stubs, `oak_v24_*`; v25 aged knots, `oak_v25_*`; v26 knots in the bark's colours, `oak_v26_*`) |
| Holder | Christina: her look at the variants (`oak_v27_variants.png`), the lighter grooves (`oak_v28_groove_trials.png`) and the oak in Godot |
| Model | `assets/source/props/coastal_live_oak.blend`: `export/crown` (the core, not shown, wearing the hats through `kyt_clump_skin`), `export/trunk/trunk` (bark and knots, collides; after any `leaf_skin.py` rebuild run `paint_canvas.py --bark` again, as `--leaflets`); each variant's parts in `export` (a) and `export/variant_b`, `variant_c` (hidden in the viewport), named `_b`, `_c`, marked `kyt_variant`, `export/sprigs/sprigs` (the leaf clusters, a point each), `authored/blades/blade_leaf` (the hat), `blade_upper` (the tier over it), `blade_topper`, `blade_sprig`, `blade_acorn`, `blade_acorn_green`, `blade_fallen_a` to `_c`, `blade_leaf_bud`, `authored/domes/clumps` (a point per hat: move one and its branch follows on the next build); the old oak in `reference` (from `maquette_export --whole`, `reference/coastal_live_oak.glb`) |
| Paint | Bark (her "lets add a little subtle texture to the trunk and branches, a vertical grain similar to this", "the highlights should be a subtle red brown"): `coastal_live_oak_bark.png`, 512 by 1024 (a 1 by 2 m tile, 512 px/m) of wavy vertical ridges, their lit flanks red-brown, at full strength (her "the texture on the trunk can be full opacity"), its grooves shaded 0.1, from 0.33 (her "the dark grooves of the trunk grain is too dark and looks a little unsettling"; `oak_v28_groove_trials.png`), made by `paint_canvas.py --bark` (`BARK`) and put on `oak_trunk`; the limbs unwrapped round and along at that tile, grown with each limb's girth (her "lets enlarge the pattern on the larger branches and even more on the central trunk": `tile_grow`, twigs 1×, major limbs about 1.8×, the trunk about 2.5×). Knots (her "add a few large knots where a branch might have detached a long time ago", then "the holes should have a knot inside kind of like this" with four photographs, saved in `documentation/reference/coastal_live_oak/knot_*`): five on the trunk, leader and major limbs, each a raised oval lip round the stub of the old branch, its end grain `coastal_live_oak_knot.png` (256 px: wavy growth rings, a pith, radial cracks, a thin crack at its rim; aged and darker, weathered with blotches, the rim dark, her "the new knot themselves can be darker and aged", "that can be just a dark grey brown"; in the bark's own colours, her "use the existing bark colors" "on the knot": the wood its red-brown highlight, the rings its grey-brown, the rim and cracks that darkened, `from_bark`) on `oak_knot` (one more surface), 280 triangles (`knot_spots`, `knot_faces`, `knot_disc`). Leaves: `assets/source/textures/coastal_live_oak/`: colour 2048, 189 px/m since the upper tier's own island (289 before; the two hats side by side use 51% of the square canvas); a canvas per season (`paint_canvas.py` `seasons`, one gradient place per leaf): `coastal_live_oak_colour_spring.png` bright lime to spring green with winter's see-through leaves (her "lets use this same one for spring but change the leaf color and make the acorns buds and have more buds"), `_winter.png` rust to deep red-brown with a sixth of the hats' leaves cut through (`drop` 0.15; her "holes move from fall to late winter" after trying 15% on fall and 35% on winter; spring shares them), and `coastal_live_oak_colour_fall.png`, fall's canvas, each segment a radial gradient (her "lets make the colors more of a radial gradient", "more yellow in the center/top and getting more orange and red as it gets wider"; a first try with random colours per leaf was dropped): the upper tier yellow to golden, the wide hat golden to orange to red at its brim, each leaf the colour where it starts (`fall` `crown` `stops`, `ranges`), the sprouts yellow, the leaf clusters orange, pale gold midribs; the fallen leaves `ground`'s tan, brown, ochre; the acorns painted by `cut_acorn` (a scaly cap, the nut below, green or brown); olive leaves 0.65 m with small spiny teeth, a darker course under them at half their number (`under` 0.68, `under_apart` 1.8), every gap between them open (`keyholes` "all"; her "more visual negative spaces between the leaves"), the leaves scattered off their rings (`scatter`; her "the visual gaps are too linear"); 80% leaf; `PROP_LEAFLETS["coastal_live_oak"]` in `paint_canvas.py`. No PSD |
| Reference | `documentation/reference/coastal_live_oak/coast_live_oak_mature_hillside.webp` (her photo). Her live oak sketch and Mario Kart trees screenshot were pasted in chat and not saved |
| Game | `assets/props/coastal_live_oak.glb` (1,352 KB): per variant `coastal_live_oak_<v>-col` (trunk and limbs, collides), `_visual` (hats and leaf clusters), `_summer_acorns`, `_fall_acorns`, `_fall_ground`, `_winter_acorns`, `_spring_buds`; the season canvases `coastal_live_oak_colour_spring.png`, `_fall`, `_winter` beside it (Send copies them; imported lossless with mipmaps as the extracted colour). `scenes/world/coastal_live_oak.tscn` wraps it (`coastal_live_oak.gd`, replacing the Path3D builder): `variant` shows one oak and turns the others' collision off; `season` (spring, summer, harvest, winter; default summer) shows the chapter's groups and puts its canvas on the leaves (their material, `coastal_live_oak`; one shared material per chapter), in `seasonal_planting` with `set_season`. `coastal_live_oak_catalog_test` rewritten: PASS for 3 variants by 4 chapters. Catalog card PRP-PLANT-049 re-captured (`documentation/images/prop-library/raw/prp-plant-049.png`) and its entry rewritten. Not placed |
| Last hand-back | 2026-09-29, Send headless (`prop_handback_blender.py -- send`: ok, 33 parts, one set per variant), `--import`, `coastal_live_oak_catalog_test` PASS, `budget_test` PASS (the oak unplaced, so uncounted) |
| Next | Her look at the variants and the oak in Godot. Placing oaks is hers (editor); `budget_test` counts it once placed (variant a 2,890 triangles in summer to 3,310 in spring; four or five surfaces: bark, knots, leaves and the chapter's groups) |

### elephant_ear — PRP-PLANT-063, upright elephant ear (Alocasia) clump, green and red, the clump and the mature clump (not placed)

| | |
|---|---|
| Stage | **game** (2026-09-30, her "looks good" on the plum tint): sent in four variants and wrapped by `scenes/world/landscape_kit/elephant_ear.tscn`, not placed. Before: **model** (2026-09-29, her "using the same principles from our hakone grass and our palm crowns, lets make one of these - it should be shoulder height at the most and thigh height at the least"): new, no greybox. Built the Hakone's and the crown's way: a course per leaf, a blade per kind, each leaf bending its blade along its course |
| Holder | Christina: placing it (the green, mature and red plants and the plum tint approved: "love it", "love", "looks good", 2026-09-30) |
| Model | `assets/source/props/elephant_ear.blend`. `authored/courses`: eight Bezier curves (`course_mature_00` to `05`, `course_young_00`, `01`), five points each: foot, mid-stalk, the notch where stalk meets leaf, mid-leaf, tip. `authored/blades`: `blade_mature` (stalk 0.70 m, leaf 0.66 m notch to tip, 0.76 m wide, lobes hanging 0.26 m back past the notch) and `blade_young` (0.74, 0.50, 0.56 m wide), each a six-sided stalk and an arrowhead leaf with a raised midrib that narrows from halfway and stops short of the tip (the bird of paradise's `RIB_*`), wearing the leaf's material, halves swept back from it, lobes curled back; each carries its `kyt_leaf_*` measurements (notch, length, half-width, lobe, midrib) for its texture. `export`: one leaf per course (`kyt_course_blade`, Width = its size). `reference`: `plant_base`, a 1.7 m figure, rings at 0.70 m (thigh) and 1.40 m (shoulder). 1,536 triangles, 3 materials (leaf, young leaf, stalk; near matte, 0.9, as the bird of paradise), 1.27 m tall, 2.15 m across. Seeded by `documentation/screenshots/handbacks/elephant_ear-start-2026-09-29/elephant_ear_start.py`; the .blend owns the shape from here. **Variants** (2026-09-30, her "lets make a mature version in addition to this one", "then make a redder varietal"; added by `documentation/screenshots/elephant-ear-2026-09-30/elephant_ear_variants.py`), each part `kyt_variant`: `green`, the approved clump, in `export`; `green_mature` in `export/variant_green_mature` (courses in `authored/courses/variant_mature_courses`, both hidden in the viewport): `mc_trunk` (a ringed stem 0.24 m tall, `elephant_ear_trunk`), eight big leaves (1.12 to 1.2 the size, leaning further out, two drooping) and two young, 2,050 triangles, 1.384 m tall, 2.97 m across; `red` and `red_mature` in `export/variant_red`, `variant_red_mature` (hidden): copies of the green parts bending the same blades along the same courses, through `elephant_ear_red` (geometry nodes replacing each green material by its red twin: `elephant_ear_red_leaf`, `_red_young_leaf`, `_red_stalk`, `_red_trunk`). Pups at the mature clump's foot were tried and taken out (lone leaves on bare stalks) |
| Reference | `documentation/reference/elephant_ear/her_elephant_ear_photo.png` (her photo) |
| Paint | Drawn, not painted (2026-09-30, her "take the example of the leaves from the bird of paradise in the other session and apply that to these leaves"): `tools/blender/elephant_ear_leaves.py` lays each leaf's UVs (U across, V along) and writes `assets/source/textures/elephant_ear/elephant_ear_<mature|young>_colour.png` and `_normal.png` (512 px square, 532 and 712 px/m along) with the bird of paradise's values: side veins 90 mm apart at about 60 degrees bending toward the tip, soft rib lines 6% lighter blurred 12%, a 1.2 mm ripple between them shaded 1.5%, stopping 15 to 40 mm short of the edge; the edge 40% toward pale green over 30 mm; the midrib painted 0.88 of its pale green, edge blurred 1.5 mm, fading out between 60 and 86% of the leaf; here also a basal vein from the notch into each lobe, with its own side veins, the first vein out from the notch dividing the two sets. Before and after: `documentation/screenshots/elephant-ear-2026-09-30/v2_bop_leaves.png`. Her photo's veins are much bolder than the bird of paradise's (`VEIN_LIGHT` 6%). Then her "scallop the edges a bit more to enhance the ripples": the edge cut into a shallow arc between each pair of side veins, a cusp 15 mm in where a vein meets it (`SCALLOP_M`), none at the tip, round the notch or at the lobes' ends; the two sets of side veins shifted to end together where the dividing vein meets the edge; cut into the colour PNG's alpha, clipped (Round, so glTF alpha mask and Godot alpha scissor), the rim and the ripples' stop following the cut edge (`v3_scalloped_edges.png`). Then her "soften the central vein a bit more": the midrib's edge blurred 4 mm (`MIDRIB_BLUR`; the bird of paradise's 1.5 mm before), the basal veins unchanged (`v4_softer_midrib.png`). Then her "maybe lets do the reverse where the leaf starts light in the center and gets darker towards the edges": the bright rim replaced by a shading across the whole leaf, from its middle line (the midrib; a lobe's basal vein) 30% toward the pale green to its edge 20% darker, evenly (`CENTRE_LIGHT`, `EDGE_DARK`; `v5_light_centre.png`); approved ("love it"). The red leaves: their own colour maps, `elephant_ear_red_mature_colour.png` and `_red_young_colour.png` (burgundy to copper in the middle, rose veins; the young coral), sharing the green normal maps (`v7_mature_and_red.png`); then her "love, give the darker parts a purply tint": toward the edge, as a red leaf darkens, a per-channel tint toward plum, 60% of the way at the edge and none in the copper middle (`PURPLE`, `PURPLE_TINT`; `v8_purple_tint.png`); the green textures unchanged |
| Game | `assets/props/elephant_ear.glb` (575 KB; the six textures through `optimize_png.py` first, pixel-identical, 36 to 47% smaller): `elephant_ear_green_visual` and `elephant_ear_red_visual` (1,536 triangles, three surfaces each), `elephant_ear_green_mature_visual` and `elephant_ear_red_mature_visual` (2,050, four with the trunk); the leaf materials carry colour and normal textures and alpha scissor (the scallops), the stalks and trunks flat. Wrapped by `scenes/world/landscape_kit/elephant_ear.tscn` (`elephant_ear.gd`, visual only): `variant` (green, green_mature, red, red_mature) shows its mesh and hides the rest; `height` (0.70 to 1.40 m, thigh to shoulder, clamped) scales the model child from the shown mesh's own top, so a reshaped plant needs no number changed. Probed headless: each variant shows only its mesh with the materials above; 0.70 and 1.40 m land exactly for all four, 2.0 clamps to 1.40 |
| Last hand-back | `documentation/screenshots/handbacks/elephant_ear-2026-09-30_0126/` (`prop_handback.py elephant_ear --no-export`: send ok, 38 parts merged into one per variant; import ok; seat_test PASS; clearance 0 of 87; budget_test PASS; ground contact known failures only (75); renders of the green clump); then re-sent with the optimized textures (837 KB to 575 KB), imported, probed again, Godot's extracted textures pixel-identical to the source |
| Next | Placing it is hers (editor): `scenes/world/landscape_kit/elephant_ear.tscn`, `variant` and `height`; `budget_test` counts it once placed. Rerun `elephant_ear_leaves.py` and Send after any blade reshaping. Commit on her word |

### bird_of_paradise — PRP-PLANT-064, bird of paradise (Strelitzia reginae) clump, variants a and b (not placed)

| | |
|---|---|
| Stage | **game** (2026-09-29): her "lets use the same principles from our hakone grass and our palm crowns to make some bird of paradise plants"; shown a few-and-big clump and a fuller one, "keep both, and add the low drooping outer leaves"; then "send it to godot", "the vein shouldnt go all the way to the tip of the leaf", "give the leaves this subtle rippling/ribbing" (with a close photo of the leaves) and "make the edges a little brighter", then "way too plasticy, these need to be larger and fewer" (the ripples), "still too much", "and they shouldnt reach the edge of the leaves", "closer but continue to make them fewer". New, no greybox; a course per leaf and a blade per kind, as the Hakone and the crown. Sent and wrapped, not placed |
| Holder | Christina: the textured, matte flowers committed at her "commit and push" (2026-09-30); placing it is hers |
| Model | `assets/source/props/bird_of_paradise.blend`, built by `tools/blender/bird_of_paradise.py` (`VARIANTS`). `authored/blades`, shared by both: `blade_mature` (a three-sided stalk, flat on top, for 46% of the leaf, then a round-based paddle 0.30 m wide to a soft point, halves folded up off a pale midrib that narrows from halfway and stops at 84% of the paddle, `RIB_*`), `blade_young` (0.20 m wide, folded tighter), `blade_flower` (the beak, green with a red-mauve band, three orange sepals, a blue arrow; stalk tip at the origin, beak +Y). **a**, few and big, in `export` (courses in `authored/courses`): 13 leaves, 2 young, 5 drooping (`droop_<i>`, arching to about 0.6 m and 0.9 m out), 4 flowers (`stalk_<i>` by `kyt_course_stem`, `head_<i>` by `kyt_head_at_course_tip`: Turn, Tilt, Scale), `sheath`; 1.65 m tall, 2.01 m across, 1,662 triangles. **b**, fuller like her photo, in `export/variant_b` (courses in `authored/courses/variant_b_courses`), both hidden in the viewport, names ending `_b`: 18 leaves 0.87 as wide, 3 young, 7 drooping, 7 flowers; 1.70 m tall, 2.05 m across, 2,508 triangles. Every part `kyt_variant` and `kyt_collision = none`. `reference`: `plant_base`. 10 materials |
| Reference | `documentation/reference/bird_of_paradise/park_bed_clump_with_bench.webp`, `house_bed_clump_flowers.webp` (her two photos). Her third, a close photo of the leaves' fine side veins and two flowers, was pasted in chat and is not saved in the project |
| Paint | `assets/source/textures/bird_of_paradise/`: per leaf kind a colour and a normal map, 256 by 512, in the paddle's own UVs (U across, V along), written by the builder (`leaf_textures`, `LEAF_TEX`): side veins about 60 degrees off the midrib curving toward the tip, 90 mm apart, their rib lines lighter (6%; 2.5% before her "the ridges slightly lighter", `v9_vein_darker_ridges_lighter.png`) and soft-edged (her "blur those lines 12%": a Gaussian of 12% of the spacing, `VEIN_BLUR`, the middle kept at 6%, `v10_lines_blurred.png`); a soft 1.2 mm corrugation between them in the normal map, faintly shaded (1.5%), both fading out 15 to 40 mm in from the edge (`RIPPLE_STOP`). Her notes on it: "way too plasticy, these need to be larger and fewer", "the ripples" (22 mm apart, 1.2 mm and creased at first; then 3 mm, `v6_ripples_fewer.png`), "still too much", "and they shouldnt reach the edge of the leaves" (`v7_ripples_softer.png`), "closer but continue to make them fewer" (55 mm apart before, `v8_ripples_fewer.png`); the margin lightened 40% toward pale green, fading on a soft curve over 30 mm into the leaf (12 mm and a steeper curve before her "blur and extend the bright edge of the leaf further into the body"); the central vein painted in the texture since her "ever so slightly blur the central vein" (its strip in the geometry now wears the leaf's material): the same width and taper and its darker pale green, edge blurred 5 mm (`RIB_BLUR`; 1.5 mm before her "not blurry enough", `v12_vein_blurrier.png`), fading into the leaf from 60% to 86% of the paddle (her "have it kind of fade at the tip of the vein", `RIB_FADE`), `v11_edge_and_vein.png`. On `bop_leaf` and `bop_young` (`bop_midrib` and `bop_young_midrib` are paint colours only). The flower head (2026-09-30, her "make the flowers matte and give them textures too"): one fully matte material `bop_flower` (roughness 1.0) wearing `bird_of_paradise_flower_colour.png`, 512 square, the beak, sepals and arrow's petals side by side (`FLOWER_REGIONS`, each laid out across and along the piece); the beak's green hull blending softly into its red-mauve band, pinker at the heel, darker toward the tip, faint lines along it, a thin golden line along the opening; the sepals pale yellow at the base to orange, a darker midline, lighter edges; the petals whitish at the base to deep blue, a darker midline (`flower_texture`, the four earlier flower colours as paint), `v13_flowers_textured.png`. Leaves, stalks and sheath near matte (0.9 to 0.95; 0.5 to 0.7 at first). The stalks and sheath keep flat colours. Not yet a canvas for her to paint (no UV guide or PSD): the palm's way (`unwrap_blades.py`, `paint_canvas.py`) is still to come |
| Game | `assets/props/bird_of_paradise.glb` (401 KB): `bird_of_paradise_a_visual` (1,662 triangles) and `_b_visual` (2,508), 5 surfaces each, the four leaf textures extracted beside it (mipmapped). Wrapped by `scenes/world/landscape_kit/bird_of_paradise.tscn` (`bird_of_paradise.gd`: `variant` a or b shows its mesh, hides the other; visual only). Probed headless: each variant shows its own mesh, the leaf materials carry their colour and normal textures, double-sided. Not placed |
| Last hand-back | `documentation/screenshots/handbacks/bird_of_paradise-2026-09-30_0159/` (the textured, matte flowers: all pass as below; GLB 401 KB; Godot: 5 surfaces a variant, `bop_flower` at roughness 1.0 with its texture); before it `documentation/screenshots/handbacks/bird_of_paradise-2026-09-30_0055/` (central vein blurred 5 mm: all pass as below; GLB 336 KB); before it `_0019/` (the wider soft edge and the painted, fading central vein; 8 surfaces a variant, was 10), `_2352/` (rib lines blurred), `_2349/` (darker central vein, lighter rib lines), `_2345/` (ripples 90 mm apart), `_2343/` (fainter ripples stopping short of the edge), `_2337/` (larger, fewer ripples and matte; Godot's leaf materials at roughness 0.90 with their textures), `_2334/` (`prop_handback.py --no-export`: send ok, import ok, seat, clearance 0 of 87, budget PASS, ground contact known failures only; renders of variant a, since the render step now shows a variant prop's first variant only); before it `_2327` (the shorter midrib) and `_2324` (first send). Blender renders `documentation/screenshots/bird-of-paradise-2026-09-29/`: `v3_variants_drooping.png`, `v4_midrib_short.png`, `v5_leaf_ribbing.png` |
| Next | Her look. Placing it is hers (editor); `budget_test` counts it once placed. Later: the flowers' and stalks' textures and a canvas she can paint. Commit on her word |

### date_palm — PRP-PLANT-068, giant Canary Island date palm, the centerpiece (not PRP-PLANT-051, the catalog's coastal-crown date palm; not placed)

| | |
|---|---|
| Stage | **game** (2026-10-01): her "date palm and hedge are approved" approved v9. Sent (1,221 KB), imported, wrapped in `scenes/world/date_palm.tscn`; `seat_test`, `clearance_test` and `budget_test` pass. Earlier, in order: **model** (2026-09-30): v9 built by `tools/blender/date_palm.py`, her look pending. v5: her "let the crown start further down the trunk a little like the example so it makes more of a spray": the fronds leave the trunk from 0.35 m over the seat down to 1.3 m under it (`ATTACH`; it was 0.7 m tall), on the trunk's surface; the stubs moved under the lowest fronds; 14.5 m across, lowest tip 1.2 m (a snapped frond) |
| Holder | Christina: where it stands (hers to place). v9 approved 2026-10-01. Earlier note: Christina: her look at v9. v9 (2026-09-30): her "lets do fewer fronds but larger" and "make the leaflets on the texture fewer but bigger also": 40 fronds (2 spear, 6 young, 22 mature, 10 old; were 69), each a quarter longer and wider (mature 8.5 m, 1.02 m half-width); leaflets about 1.8 times as far apart and 1.7 times as wide (mature 0.27 m apart, 0.22 wide), rachis thicker. 5,178 triangles; 13.0 m tall, 17.6 m across; a snapped frond's tip 0.13 m over the soil; canvas 218 px/m, old fronds 39% leaf. v8: her "shadow under the bulge ledge": painted, not lit, so it holds whatever the sun does: the neck darkest (times warm (0.34, 0.27, 0.22)) right under the ledge at 3.62 m, lifting over 0.75 m down (`SHADOW`); the bulge's underside boots darker the more they face down (`BOOT_SHADE`). Each shadowed row has a tile of its own: the trunk island is now a 4 by 4 grid (4 plain, 8 neck, 4 bulge tiles; `kyt_trunk_tiles` on the object records it for `--paint`), which took the canvas from 278 to 266 px/m. v7: her "it needs this bulge thing" (photo `documentation/reference/date_palm/pineapple_bulge.webp`): a pineapple knob under the crown, 2.2 m across over a 1.3 m neck, from 3.6 to 5.5 m, full and tucked in at its foot, rounding up into the fronds (`BULGE`); its own ring of 16 cut boots round (the shaft has 10), standing 0.16 m proud and pointing down on its underside, all fresh tiles; shaft rows it covers left out; the trunk under it all weathered. 6,918 triangles |
| Model | `assets/source/props/date_palm.blend` (`new_prop.py`). `authored/courses`: 81 Bezier courses (3 spear, 10 young, 38 mature, 18 old in a golden-angle spiral, three of the oldest snapped; 12 stubs round the nut). `authored/blades`: spear, young, mature, old, stub, each V-folded up from the midrib. `export`: the fronds (`kyt_course_blade`), `trunk` (diamond leaf scars as low pyramids, 10 round, 0.14 m rows, the only part that collides), `heart`. 6,358 triangles; 11.8 m tall, 14 m across, crown seat 6.5 m, trunk 1.3 m across. `plant_base` in `reference`. `--replace` rebuilds it all; it refuses once a PSD exists |
| Paint | `assets/source/textures/date_palm/`: colour 2048 (about 260 px/m) from `paint_canvas.py --leaflets` (`PROP_LEAFLETS["date_palm"]`: leaflets from a straw rachis, spines at the base; mature 53% leaf, old 44%), then `date_palm.py --paint`: the trunk's four diamond tiles (two fresh tan, two weathered grey-brown, fresh toward the nut) and each feather blade dark at the rachis to light at the tips. Cut-out, ORM, UV guide. Unpainted; no PSD |
| Game | Sent 2026-10-01 (1,221 KB, 54 parts merged), imported. `scenes/world/date_palm.tscn` (editor-owned) instances `res://assets/props/date_palm.glb`; the collision mesh `date_palm-col` is the trunk only (about 6.5 m, 1.3 m across), the trunk on the origin and the crown's spread centred 0.56 m off it. Not placed. Earlier note: Not sent. `kyt_godot_scene` names `scenes/world/date_palm.tscn`, to be written at the hand-back |
| Reference | `documentation/reference/date_palm/canary_date_palm_front_yard.webp` (her photo) |
| Last hand-back | `documentation/screenshots/handbacks/date_palm-2026-10-01_2242` (model hand-back, `--no-export`: three_quarter, front, back_low, close_top). Earlier: None. Renders `documentation/screenshots/date-palm-2026-09-29/` (`render_palm.py`): `v4_sheet.png` beside her photo; v0 to v3 the steps before |
| Next | Where it stands (hers to place). The catalog card shows a placeholder until `build_prop_catalog.py --capture` is run. Earlier: Her look. Then the model hand-back (Send, the wrapper, `budget_test`), a catalog ID, and where it stands (hers to place) |

### boxwood_hedge — PRP-PLANT-065, boxwood hedge kit, three heights, eleven pieces (not placed)

| | |
|---|---|
| Stage | **model** (2026-09-29, her "lets make some boxy hedges so we can make shapes like this" with a knot-garden photo, "this will be the standard height but lets also have waist height and a taller than people version one for privacy", then "the tiers are good for visual interest but also bad because they are so linear ... can we put it only on the very top of the hedges like a lid?", "then add random clusters of leaves", "the top tier is still to long, it needs to be almost flat on top", "pull those edges in a little bit, a few millimeters", "bring it in even more", "the clusters are kind of weird", her pick of B, "lets put a few random clusters on the top of the lid", "can the bottom edges be shaped like the edge of the lid instead of flat", "bring the lid in just a little bit more", "vary the lightness and darkness of hte leaf clusters a bit too", "no lighter shades", "restore the last lid shape but lower it down", "clusters still a little too light in some places", "make it a few mm larger", "lower it like a mm", then after the commit "the edge of the lid is a little too light", "make the lid like another mm wide", "make it another mm wider", "now lower the lid another mm", "like the whole thing", "not jus the hem right?"): v18 built by `tools/blender/hedge_kit.py`, her look pending |
| Holder | Christina: where hedges go. v18 approved 2026-10-01 ("date palm and hedge are approved"). Earlier note: Christina: her look at v18 (v14 committed, `ec062ef`) |
| Model | `assets/source/props/boxwood_hedge.blend`. Heights: standard 0.495 m tall, 0.45 m wide; waist 0.993 by 0.6; privacy 2.192 by 0.8 (0.5, 1.0 and 2.2 until the whole lid was lowered a step in v18). Pieces on the 1 m grid, origin mid first cell: `straight`, `straight_2`, `straight_4`, `corner`, `tee`, `cross`, `end`, `post`, `bend` (0.5 m radius), `curve` (1.5 m, four make a 3 m ring), `curve_large` (2.5 m, a 5 m ring). Each in `export/<height>`: the body (collides), the lid `_hat` (since v6 almost flat: a flat top rolling over its edge to a hem of leaf tips 0.095 / 0.126 / 0.158 m below the top (0.06 / 0.08 / 0.10 until v12, 0.09 / 0.12 / 0.15 in v12 and v13), 20 mm past the body's side since v17 (`OVERHANG`; 1 cm in v13 to v15, 15 mm in v16; 3 mm in v8, v9 and v12; it overhung 46 mm on the knee-high hedge until v7; v10 and v11 set it 1 cm inside the side with the side rounding in under it, taken back); v5's skirt hung 0.23 m down the knee-high side), three cluster scatterings `_clusters_a` to `_c`: since v8 small three-leaf fans, one or two together, lying almost flat in nearly the hedge's green, each in one of three shades (`CLUSTER_SHADES` 0.76, 0.85, 0.94 of `CLUSTER_LIGHT`: her "no lighter shades", "still a little too light in some places"), on the sides and a few on the lid's flat top (bent cards 0.22 m, 4 triangles each; the standard's at 0.75 size); trials `lid_overhang_trials.png`, `cluster_trials.png` (A long pale sprigs in clumps, B fans, C round tufts). Body and lid 20 to 300 triangles; 0 to 60 sprigs a scattering. `authored/sample_parterre`: a sample garden of linked duplicates; `export` hidden in the viewport. Tiers down the taller sides were built (v1, v2) and taken off at her word |
| Reference | `documentation/reference/boxwood_hedge/knot_garden_parterre.webp` (her photo) |
| Paint | `assets/source/textures/boxwood_hedge/`: colour 512 by 2048 (optimized, 622 KB), 512 px/m, repeating every metre along the hedge: the lids' band (the hem at its foot for every height; its last 10 cm, the roll over the edge, darker, `HEM_DARK` 0.32 over `HEM_REACH`, since v15), a row of three painted sprigs, the bodies' band (the ground at its foot, since v9 a hem of leaf tips on the soil like the lid's, gaps between them; the side clusters keep above the gaps); the box shrub's leaf. Cut-out, ORM, UV guide. No PSD |
| Game | Sent (1,156 KB), imported. `scenes/world/landscape_kit/boxwood_hedge.tscn` on `boxwood_hedge.gd`: `height`, `piece`, `leaf_clusters` (by grid square, or a, b, c); each placement one merged mesh (body, lid, its scattering) and the body's collision, not saved in the scene. `boxwood_hedge_test` PASS, `budget_test` PASS. Not placed |
| Last hand-back | None. Renders `documentation/screenshots/boxwood-hedge-2026-09-29/v1` to `v18` (`hedge_kit.py --render`) |
| Next | Where hedges go is hers. v18 is in the working tree, uncommitted; say "commit" and it goes in with the date palm. Earlier: Her look at v18 (the lid's edge darker, 10 mm wider and lowered a step since the commit); the clusters' size and number). Then a catalog ID and card; where hedges go is hers |

### hardscape_kit — little brick and concrete walls with piers, iron railings and fences, curbs (PRP-FENCE-003 walls, PRP-FENCE-004 iron fence, PRP-FENCE-005 bed edging, PRP-ROAD-005 curb and gutter; not placed)

| | |
|---|---|
| Stage | **model**, approved look (2026-09-30: her "time for fences and little retaining walls and curbs" with a photo of a brick front-garden wall; through v11, her "perfect"; then the iron weathered a little, the bricks softened and weathered for the beach town, "lets keep this, though in the park itself it will be a different kind of weathering", "mostly just a little darker towards the bottom, maybe all of them can have some rain streaks under the ledge at the top", "i like this direction in general", "bird poop on the ledges", "and iron railings", "can the iron have segments and have a little ball on the top of the segment post", "yeah just echo the free standing fence segments", then "the non free standing iron segments are weird so lets revert those"; "why are the freestanding fence segments so random", then with her photo, "for this version, see how the segments are right next to the brick towers and then one in the middle"; "can they have a ball on top", then "actually cancell that", "balls on the freestanding fence are fine"; "give the freestanding fence a post every 2 metres or whatever segment length makes the most sense"): v18 built by `tools/blender/hardscape_kit.py`; sent and wrapped, not placed |
| Holder | Christina: v18 committed at her word (the fence's posts every 2 m); where it goes is hers |
| Model | `assets/source/props/hardscape_kit.blend`, one prop in kinds, each piece a `kyt_variant` `<kind>_<size>_<piece>` on the hedge kit's 1 m grid (origin mid first cell, the run along the cells' middles). Walls, sizes `seat` (coping top 0.475 m) and `garden` (0.70, her photo): `wall_*` (the park's brick: softened, a little darker toward the ground), `town_wall_*` (the beach town's: sun-bleached, salt and sand at the foot, patched and chipped), `concrete_wall_*` (warm grey poured concrete); 0.30 m thick, 0.2 m below grade, coping 0.42 by 0.10 m; `straight`, `straight_2`, `straight_4`, `corner`, `tee`, `cross`, `end`, `bend`, `curve`, `curve_large`, and `pier` (0.45 m under a 0.57 m cap, brick tops 1.05 / 1.275 m) standing over whichever wall piece is in its cell. Every coping and cap one solid light grey, 197, 195, 189, chipped along its edges and weathered a tad, the coping seamed every metre; rain streaks under every ledge. `railing_wall` (on the coping, 0.55 m) and `railing_fence` (on the ground, 1.10 m, posts with ball finials): 22 mm square pickets eight to the metre, a section across the top (`TOP_SECTION`), `pier` (posts just off a pier's faces), `post` (the fence's with its ball; the wall railing's plain and flat-topped, the one in the middle between two piers, v17; a ball on it tried and taken out); the fence's own posts every 2 m (`FENCE_PANEL`), on every even grid square (x + y) however a run is pieced, and at every corner, tee and cross, curves spacing theirs evenly (`fence_posts`, v18): its straights and curves built twice, `_even` and `_odd`, for the square the first cell is on; the fence's posts built by `fence_post` (the wall railing's segment posts, that post at four fifths every two metres, were tried in v15 and taken out); the iron lightly weathered (faded patches, rust spots, chips to primer); rails and posts collide, pickets don't. `curb_road`, `curb_road_red`: curb and gutter (0.15 m reveal, 0.4 m pan), straights, bends and curves either way (`_in`: road inside), `end`, `cut`; `curb_edging`, 0.09 m proud; curbs don't collide. Bird droppings: three scatterings a wall and railing piece (`droppings_a` to `_c`, cut-out cards on copings, caps and top rails; none collide). Triangles: wall straight 36, pier 68, railing 88 a metre, curb straight 20, a dropping 8. Built through the photo's twisted bars, a double scroll and rock-faced stone, each taken out at her word. `ground_line` in `reference` (Check: a prop set into the ground). `authored/sample_street`: a beach-town street, a wall railing post in the middle of each four-metre bay |
| Reference | `documentation/reference/hardscape_kit/brick_wall_iron_railing.webp` (her photo); her second photo (a black fence on a curved stone wall) is not on disk |
| Paint | `assets/source/textures/hardscape_kit/`: colour 512 by 8192, 512 px/m, repeating every metre along a run: for each body (park brick, town brick, concrete) a band by height from the ground and two streak bands measured down from a ledge (`STREAK_M`), coping and cap, iron, road curb, red curb (its painted top and face only), edging, droppings (cut out). Bump (hers to paint) and the normal map from it (`bump_to_normal.py`, 4 px, wrapping), ORM, cut-out, UV guide. No PSD |
| Game | `assets/props/hardscape_kit.glb`; `scenes/world/landscape_kit/hardscape_kit.tscn` on `hardscape_kit.gd`: `kind`, `piece`, `pier` and `railing` (a wall with its pier and railing as one placement), `post` (v17: on a straight, the railing's middle post), a fence taking its `_even` or `_odd` piece by the square it stands on (`_key_for`, again when moved), `droppings` (by grid square, a, b, c, none); each placement one merged mesh and its layers' collision, not saved in the scene. Not placed |
| Last hand-back | `hardscape_kit-2026-09-30_1633` (`prop_handback.py --no-export`): send (GLB 5,141 KB), import, textures pixel for pixel and VRAM-compressed, `hardscape_kit_test` PASS, clearance 0 of 87, `budget_test` PASS, ground contact known failures only. Renders `documentation/screenshots/hardscape-kit-2026-09-30/v1` to `v18` (`hardscape_kit.py --render`) |
| Next | Placing it is hers |

### concrete_picnic_table — PRP-PARK-028, concrete trestle picnic table (not placed)

| | |
|---|---|
| Stage | **canvas** (2026-10-02): her "i like it" on the model (trestles 3 in in, top 3 in longer each end, the trestles leaning feet-in); model hand-back run, game mesh made, unwrapped, starting canvas baked; **waiting on her OK of the starting look**, then paint. |
| Holder | Christina: the starting look (renders `documentation/screenshots/handbacks/concrete_picnic_table-canvas-2026-10-02/`) |
| Model | `assets/source/props/concrete_picnic_table.blend` (`new_prop.py`, then `add_reference.py` with `assets/source/props/reference/concrete_picnic_table_greybox.glb`, made by `maquette_export.gd res://scenes/world/generated/plaza_props.tscn picnic_0 concrete_picnic_table_greybox --floor 4 3`). `export` holds the model pass of 1-2 Oct 2026, measured off her photo by solving its camera and the table together from 27 points: top 2.10 by 0.74 m (upper face 0.79 m; the photo's 1.94 m, 3 in longer at each end at her word on 2 Oct), two trestles 0.24 m thick, their tops at x = ±0.56 (the photo's ±0.64, brought 3 in toward the middle at her word on 2 Oct; set in 0.37 m from the top's ends) and leaning, feet set in a further 0.11 m (8.9°) so the top overhangs them 0.48 m at the floor (her "feet move in, tops stay where they are", 2 Oct; a shear, so tops stay flat to the top and feet flat on the ground; the bench bolts and discs follow), each a footing with horns, a 0.12 m waist between two round cut-outs 0.42 m across, and a brass disc; on each long side one bench of three timber slats as long as the photo's top (1.94 m, so their ends sit 3 in inside the top's now, running 0.29 m past each trestle, 0.31 m wide, upper face 0.45 m) lying on the horns, a family bolt through each slat into each horn; 23 parts, 4,570 faces. The photo beside the model: `documentation/screenshots/handbacks/concrete_picnic_table-model-2026-10-01/concrete_picnic_table_vs_photo.png`; `..._over_photo.png` is the overlay of the measured version, before the trestles moved in. |
| Reference | `documentation/reference/concrete_picnic_table/concrete_trestle_picnic_table.webp` (her photo) |
| Paint | `assets/source/textures/concrete_picnic_table/`: colour 1024 (256 px/m, the standard), ORM 512, UV guide; `paint_canvas.py --size 1024 --orm-size 512 --grain`: pale concrete flat, the slats timber with grain along their length, brass discs, dark bolts. No PSD yet. The photograph's surfaces to paint: pale exposed aggregate, faint slat lines on the top, dark stained timber |
| Game | `assets/props/concrete_picnic_table.glb` (sent at the model hand-back, the parts version; the game mesh and canvas go at the painted hand-back); `scenes/world/park_furniture/concrete_picnic_table.tscn` wraps it, no seat markers. Not placed |
| Last hand-back | `concrete_picnic_table-2026-10-02_0156` (`prop_handback.py --no-export`, model): send 189 KB, import, `seat_test` PASS, clearance 0 of 87, `budget_test` PASS, ground contact known failures only. Then Make game mesh (`concrete_picnic_table_source.blend` holds the parts; 6,248 triangles), `unwrap_parts.py` (all parts `facets`), Check: 8 mirror pairs, nothing else overlapping, no folds, 512 px/m at 2048 |
| Next | Her OK of the starting look, then `prop_handback.py concrete_picnic_table --open` and she paints. Reshaping now means running `picnic_tables.py` on `concrete_picnic_table_source.blend`, then Rebuild game mesh. Access at the ends: 0.48 m under the top at the floor, 0.37 m at knee height |

### round_picnic_table — PRP-PARK-029, round concrete picnic and café table (not placed)

| | |
|---|---|
| Stage | **model** (2026-10-01): her photograph of a round concrete picnic table, "this will be our 'round' picnic/cafe table - note the space for wheelchairs to pull up on either side", "different table", "both have wheelchair access", and "the second one [has it] but only because its thoughtfully designed by a civil engineer": its clearances are deliberate, so measure them against the photo. Stage 1 set-up done: the granite circle table (`granite_circle_picnic_table.tscn`, PRP-PARK-022) exported as the greybox and put in `reference`; nothing modelled yet. |
| Holder | Christina: first model pass built by Claude 2026-10-01 at her "continue converting our props" (`tools/blender/picnic_tables.py`, 7 parts (top, pedestal with its round hole, medallion disc, two crescent benches with supports), 2,594 faces); hers to reshape, then "handed back". Renders `documentation/screenshots/handbacks/round_picnic_table-model-2026-10-01/`; starting frames in `...round_picnic_table-start-2026-10-01/` |
| Model | `assets/source/props/round_picnic_table.blend` (`new_prop.py`, then `add_reference.py` with `assets/source/props/reference/round_picnic_table_greybox.glb`, made by `maquette_export.gd res://scenes/world/park_furniture/granite_circle_picnic_table.tscn - round_picnic_table_greybox --whole --floor 4 4`). `export` is empty. |
| Reference | `documentation/reference/round_picnic_table/round_concrete_picnic_table.webp` (her photo) |
| Paint | Not started. The photograph's surfaces: pale tan aggregate concrete, a round medallion decal on the pedestal (a city seal in the photo; the park's own emblem later) |
| Game | Not sent. No scene yet: the first Send offers "Write Godot scene" |
| Last hand-back | None |
| Next | Her model (the two open sides stay open for wheelchairs), then "handed back". No seat contract exists for round tables; decide at the first Send. Card: `documentation/howto/model-the-round-picnic-table.md` |

### drive_in_picnic_table_set — PRP-PARK-020, drive-in picnic table set with umbrella (not placed)

| | |
|---|---|
| Stage | **model** (2026-10-02): first pass from the catalog note (no photograph of hers), built by an agent with `tools/blender/drive_in_tables.py`; hers to reshape |
| Holder | Christina: review the renders, reshape, then "handed back" |
| Model | `assets/source/props/drive_in_picnic_table_set.blend`; greybox from `scenes/world/park_furniture/drive_in_picnic_table_set.tscn` in `reference`. `export`: 38 parts, 6,396 triangles: solid perforated plates in rounded band frames (top 1.78 by 0.96 m at 0.77 m; benches 1.78 by 0.42 m, tops 0.51 m), two H trestles with a spine and pole sleeve, bolted round feet, pole, collar, one 8-panel canopy 2.68 m across (rim 2.15 m, apex 2.55 m), finial; 14 family bolts. No seat markers in the scene; seats measured 0.510 m. Renders `documentation/screenshots/handbacks/drive_in_picnic_table_set-model-2026-10-02/` (with `greybox_*.png` from the same cameras) |
| Reference | None of hers; the catalog note and the greybox |
| Paint | Not started. Surfaces: turquoise painted metal with the perforations as a cut-out, black frame, canopy in three colourways (solid red, red/cream panels, sun-faded yellow) on one form |
| Game | Not sent; `scenes/world/park_furniture/drive_in_picnic_table_set.tscn` and its `_red_cream`, `_sun_yellow` siblings stand as the greybox |
| Last hand-back | None |
| Next | Her model, then "handed back". Open: the pole on a spine vs a low socket; bolts on the top; ribs under the canopy. Card: `documentation/howto/model-the-drive-in-picnic-table-set.md` |

### circular_drive_in_picnic_table_set — PRP-PARK-021, circular drive-in picnic table set (not placed)

| | |
|---|---|
| Stage | **model** (2026-10-02): first pass from the catalog note, by an agent with `tools/blender/drive_in_tables.py`; hers to reshape |
| Holder | Christina: review, reshape, "handed back" |
| Model | `assets/source/props/circular_drive_in_picnic_table_set.blend`; greybox from `circular_drive_in_picnic_table_set.tscn` in `reference`. `export`: 39 parts, 7,272 triangles: round plate in a rolled rim (1.49 m across, plate 0.763 m), pedestal, four benches 0.92 by 0.42 m at 1.0 m out (tops 0.51 m) on arms, legs and bolted feet, the same umbrella as PRP-PARK-020; 12 family bolts. No seat markers; seats measured 0.510 m. Renders `documentation/screenshots/handbacks/circular_drive_in_picnic_table_set-model-2026-10-02/` |
| Reference | None of hers; the catalog note and the greybox |
| Paint | Not started. Surfaces as PRP-PARK-020 |
| Game | Not sent; `circular_drive_in_picnic_table_set.tscn` and siblings stand as the greybox |
| Last hand-back | None |
| Next | Her model, then "handed back". Open: the bench bolt at each bench's centre. Card: `documentation/howto/model-the-circular-drive-in-picnic-table-set.md` |

### granite_circle_picnic_table — PRP-PARK-022, granite-block circular picnic table (not placed)

| | |
|---|---|
| Stage | **model** (2026-10-02): first pass from the catalog note, by an agent with `tools/blender/drive_in_tables.py`; hers to reshape |
| Holder | Christina: review, reshape, "handed back" |
| Model | `assets/source/props/granite_circle_picnic_table.blend`; greybox from `granite_circle_picnic_table.tscn` in `reference`. `export`: 10 parts, 2,384 triangles: dark solid plate (1.97 m across at 0.794 m) in a blue-green rolled rim to 0.83 m, one steel pedestal with a bolted flange and spreader, three rough granite blocks with flat sawn tops at 0.51 m at the greybox's places (NW, NE, S); 4 family bolt anchors. No seat markers; seats measured 0.510 m. Renders `documentation/screenshots/handbacks/granite_circle_picnic_table-model-2026-10-02/` |
| Reference | None of hers; the catalog note and the greybox |
| Paint | Not started. Surfaces: dark perforated metal (cut-out), weathered blue-green rim, dark steel, granite |
| Game | Not sent; `granite_circle_picnic_table.tscn` stands as the greybox |
| Last hand-back | None |
| Next | Her model (boulder vs quarry-block seats; their distance from the top), then "handed back". Card: `documentation/howto/model-the-granite-circle-picnic-table.md` |

### color_block_information_panel — PRP-PARK-023, color-block information panel (not placed)

| | |
|---|---|
| Stage | **model** (2026-10-02): first pass from the catalog note, by an agent with `tools/blender/drive_in_tables.py`; hers to reshape |
| Holder | Christina: review, reshape, "handed back" |
| Model | `assets/source/props/color_block_information_panel.blend`; greybox from `color_block_information_panel.tscn` in `reference`. `export`: 5 parts, 1,292 triangles: one dark slab frame 1.04 by 1.58 by 0.11 m from 0.39 to 1.97 m, header field 0.90 by 0.74 m and information field 0.90 by 0.38 m 3 cm proud, two round posts; the type bars are paint; no bolts. No markers. Renders `documentation/screenshots/handbacks/color_block_information_panel-model-2026-10-02/` |
| Reference | None of hers; the catalog note and the greybox |
| Paint | Not started. Surfaces: dark frame, pale field, header in cyan with magenta, green, orange and blue overrides, abstract type bars |
| Game | Not sent; `color_block_information_panel.tscn` stands as the greybox |
| Last hand-back | None |
| Next | Her model (posts into the bottom edge vs behind the panel with face bolts), then "handed back". Card: `documentation/howto/model-the-color-block-information-panel.md` |

### flagpole_banner — PRP-PARK-006, flagpole and vertical banner (placed as the generated pair in the plaza)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes" on catalog props without a photograph. Stage 1 set-up by Claude: the generated `flagpole_0` (pole and banner) exported as the greybox and put in `reference` |
| Holder | Christina: review the first pass (built by an agent with `tools/blender/plaza_dressing.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/flagpole_banner-model-2026-10-02/` |
| Model | `assets/source/props/flagpole_banner.blend`. `export`: 18 parts, 2,436 triangles: footing 0.44 m across with four anchor bolts, tapered pole 6.0 m (0.14 m to 0.10 m), brass ball finial, two clamp bands 56 mm (1.6 heads) with a bolt each, two arms 42 mm (1.2 heads) with ball caps, fabric sleeves, a blank banner 0.68 by 2.2 m from 3.5 m, bellying 5 cm, hung toward −Y with its faces to ±X as the greybox's. The pole stands at the origin; the greybox pole stands 0.32 m toward +Y (the export centred the footprint) |
| Reference | None of hers; the catalog note and the greybox |
| Paint | Not started. Stand-ins: painted metal, fabric, brass. The banner graphic is painting; the plaza pair differ by colour in the greybox |
| Game | Not sent. No scene yet: the first Send offers "Write Godot scene". In the greybox the pole collides, the banner does not |
| Last hand-back | None |
| Next | Her review: the pole at the origin, the banner's side and facing, one banner or two for the pair. Card: `documentation/howto/model-the-flagpole-banner.md` |

### balloon_cluster — PRP-PARK-010, tied balloon pair (placed as the generated pair at the photo hut bench)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes". Stage 1 set-up by Claude: the generated balloons and strings exported as the greybox and put in `reference` |
| Holder | Christina: review the first pass (`tools/blender/plaza_dressing.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/balloon_cluster-model-2026-10-02/` |
| Model | `assets/source/props/balloon_cluster.blend`. `export` holds the pass of 2 Oct 2026, rebuilt the same day on the rail tie at her word ("tie the balloons to the bench rail"): 6 parts, 1,496 triangles, nothing collides: balloons 0.42 m across and 0.59 m tall, centres at the greybox's (±0.215, ∓0.025) and 1.07 / 1.36 m above the origin, each leaning along its 16 mm string; both strings leave one knot on a loop of string wrapped (3 mm slack) round the plaza bench's top back slat `back_3` (5 cm thick, 9 cm tall, along the bench's X); the loop's lowest point is the origin. The centres sit 0.96 and 1.25 m above the slat's top, 11 cm less than the generator's above `HUT_BENCH_RAIL` |
| Reference | None of hers; the catalog note and the greybox |
| Paint | Not started. One latex stand-in; the pair's two colours (red and yellow in the greybox) are painting |
| Game | Not sent. No scene yet. The tie is the photo hut bench's back rail: `_balloons` in `gen_props.gd` hangs the pair off `bench_hut` (`scenes/world/plaza_furniture.tscn`) with strings from `HUT_BENCH_RAIL` 0.98 m at 0.84 and 0.42 m along the bench; on the modelled bench the rail is the top slat `back_3`, 0.33 m behind the centre line, its top at 1.005 m. The placement puts the prop's origin at the slat's underside (0.915 m up, 0.33 m back, about 0.84 m along the bench, turned with it); the balloons then float 1.985 and 2.275 m above the bench's base, 6.5 cm below the generator's 2.05 and 2.34 |
| Last hand-back | None |
| Next | Her review of the rail tie: one knot for both strings (the generator ties each string 0.42 m apart), and whether to raise the balloons 0.11 m (`B_CENTRES`) to float as high above the rail as the generator's. Then "handed back". Card: `documentation/howto/model-the-balloon-cluster.md` |

### park_litter — PRP-PARK-011, park litter kit (placed as 30 generated pieces in the plaza)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes". No greybox: the plaza's litter is thirty CSG nodes; `reference` is empty |
| Holder | Christina: review the first pass (`tools/blender/plaza_dressing.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/park_litter-model-2026-10-02/` (the kit in a row) |
| Model | `assets/source/props/park_litter.blend`. `export`: five variants (`kyt_variant`), every one at the origin, none colliding, 1,020 triangles in all: `cup_lidded` (crushed, lid and straw, lying), `cup_upright`, `napkin`, `ticket_stub`, `wrapper`; cups 9.6 cm across, the wrapper 22 by 16 cm. No piece lies flat on the ground |
| Reference | None |
| Paint | Not started. Stand-ins: paper, plastic. Print, stains and folds are painting; nothing branded |
| Game | Not sent. No scene yet. Which piece goes to which of the 30 spots is a placement decision at the first Send |
| Last hand-back | None |
| Next | Her review: the five pieces, whether the upright cup stays, whether the napkin reads folded. Card: `documentation/howto/model-the-park-litter.md` |

### service_cart — PRP-PARK-007, general service cart (placed as the generated cart in the plaza)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes". Stage 1 set-up by Claude: the generated cart exported as the greybox and put in `reference` |
| Holder | Christina: review the first pass (`tools/blender/plaza_dressing.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/service_cart-model-2026-10-02/` |
| Model | `assets/source/props/service_cart.blend`. `export`: 32 parts, 5,172 triangles: body 1.80 by 0.96 m with a lipped lid at 1.04 m, two 0.60 m wheels on an axle (axle-nut bolts), a swivel castor, a U push handle at 0.92 m on bolted flanges, four posts under a barrel-vaulted canopy (eaves 1.90 m, crown 2.07 m, raised from the greybox's 1.6 m so a pusher sees under it), a lamp hanging under it with its bulb at 1.80 m where the scene's `cart_lamp` light is. 2.33 by 1.44 by 2.07 m |
| Reference | None of hers; the catalog note and the greybox |
| Paint | Not started. Stand-ins: painted metal, rubber, bare metal, bulb. Nothing on it says its job |
| Game | Not sent. No scene yet. `cart_lamp` stays a light node in the scene |
| Last hand-back | None |
| Next | Her review: the raised canopy, the castor, the body a little smaller than the greybox. Card: `documentation/howto/model-the-service-cart.md` |

### picture_spot_sign — PRP-PARK-003, picture-spot sign (placed as three generated signs in the plaza)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph. Stage 1 set-up by Claude: the generated `photospot_0` exported as the greybox and put in `reference` |
| Holder | Christina: review the first pass (built by an agent with `tools/blender/plaza_signs.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/picture_spot_sign-model-2026-10-02/` |
| Model | `assets/source/props/picture_spot_sign.blend`. `export`: 12 parts, 2,132 triangles: a 130 mm round post on a 0.32 m base plate with four ground bolts, behind a 0.84 by 0.56 by 0.05 m rounded board (1.07 to 1.63 m) bolted through its face with two family bolts; a raised camera pictogram 0.34 by 0.24 m (one silhouette, a 150 mm lens ring, a glass lens), no text, no frame. 0.84 by 0.32 by 1.63 m |
| Reference | None of hers; the catalog note and the greybox |
| Paint | Not started. Board paint, pictogram colour, any wording |
| Game | Not sent. No scene yet: the first Send offers "Write Godot scene" |
| Last hand-back | None |
| Next | Her review: is 1.63 m "low" enough; the post behind the board or the greybox's lollipop; the lens as glass or paint. Card: `documentation/howto/model-the-picture-spot-sign.md` |

### a_frame_sign — PRP-PARK-004, A-frame notice sign (placed as three generated signs in the plaza)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph. Greybox `aframe_0` in `reference` |
| Holder | Christina: review the first pass (`tools/blender/plaza_signs.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/a_frame_sign-model-2026-10-02/` |
| Model | `assets/source/props/a_frame_sign.blend`. `export`: 11 parts, 2,652 triangles: two 0.90 by 1.10 m panels leaning 11° (the greybox's size), each a 56 mm painted frame round a blank board recessed 12 mm, feet cut flat, a 48 mm hinge rod along the ridge, a flat stay each side at 0.40 m with a family bolt through each end. 0.94 by 0.51 by 1.10 m |
| Reference | None of hers; the catalog note and the greybox |
| Paint | Not started. Frame paint and the two notices |
| Game | Not sent. No scene yet |
| Last hand-back | None |
| Next | Her review: the greybox's size or the common 0.6 by 0.9 m board; stays or chains. Card: `documentation/howto/model-the-a-frame-sign.md` |

### newspaper_box — PRP-PARK-005, newspaper box (placed as the generated pair in the plaza; the Boardwalk's is a separate scene)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph. Greybox `newsbox_0` in `reference` |
| Holder | Christina: review the first pass (`tools/blender/plaza_signs.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/newspaper_box-model-2026-10-02/` |
| Model | `assets/source/props/newspaper_box.blend`. `export`: 15 parts, 2,480 triangles: a 1990s honour box sized between the greybox and the Boardwalk box: cabinet 0.50 by 0.46 by 0.62 m (0.56 to 1.18 m) under a lid to 1.22 m, on a 0.14 m square pedestal and a 0.36 m plate with four ground bolts; a glazed pull-down door 0.42 by 0.40 m (56 mm frame, 0.31 by 0.29 m window over a 50 mm pocket, hinge rod, D-pull) and a 0.12 m coin box below it at the right. 0.54 by 0.55 by 1.22 m. `scenes/world/boardwalk_props/newspaper_box.tscn` untouched |
| Reference | None of hers; the catalog note, the greybox and the Boardwalk scene's sizes |
| Paint | Not started. Cabinet paint, the front page behind the glass, price, coin slot |
| Game | Not sent. No scene yet |
| Last hand-back | None |
| Next | Her review: the pedestal kind or the greybox's floor-standing box; the window's size; where the coin box goes. Card: `documentation/howto/model-the-newspaper-box.md` |

### poster_case — PRP-PARK-016, framed poster case (generated, on promenade and frontage walls)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", from the catalog note and a context frame; no photograph, no greybox of its own |
| Holder | Christina: review the first pass (`tools/blender/plaza_signs.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/poster_case-model-2026-10-02/` |
| Model | `assets/source/props/poster_case.blend`. `export`: 3 parts, 792 triangles: a 56 mm frame 0.09 m deep round a US one-sheet (27 by 40 in), a back panel for the poster, glass 14 mm behind the front; 0.82 by 1.15 m outside; no hood or lamp (the context frame shows none). Bottom edge on z = 0, back on y = 0, face −Y: the placement scene lifts it onto its wall |
| Reference | `documentation/screenshots/boardwalk-density-2026-09-09/02_cafe_arcade_amenities.png` (context frame only) |
| Paint | Not started. Frame paint; the poster is the swappable layer |
| Game | Not sent. No scene yet; needs a wall-mount placement |
| Last hand-back | None |
| Next | Her review: one-sheet size or the 2 m-plus wall panels; mounting height; a lamp for the night later. Card: `documentation/howto/model-the-poster-case.md` |

### queue_stanchion — PRP-PARK-014, rope queue stanchion (placed as the generated queue at the photo hut)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph; two variants, `post` and `rope` (`kyt_variant`) |
| Holder | Christina: review the first pass (built by an agent with `tools/blender/plaza_street.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/queue_stanchion-model-2026-10-02/` (`span` shows two posts with the rope) |
| Model | `assets/source/props/queue_stanchion.blend`. `export`: `post` (weighted domed base 0.34 m, 60 mm post, collar, four rope rings, ball cap; 1.00 m; 1,804 triangles) and `rope` (velvet rope, two ferrules, two snap hooks; the plaza's 1.4 m pitch, clips at 0.86 m sagging to 0.80 m; 1,112 triangles; does not collide). No greybox in `reference` |
| Reference | None (the catalog note; the generated `stanchion_0..4`, `rope_0..3` in `plaza_props.tscn`) |
| Paint | Not started. Stand-ins: paint, brass, rope |
| Game | Not sent. No scene yet; a Send writes the `post` and `rope` sets |
| Last hand-back | None |
| Next | Her review: four-way rings or two, ball or flat cap, base size and rope thickness. Card: `documentation/howto/model-the-queue-stanchion.md` |

### bollard — PRP-PARK-015, protective bollard (placed as the generated north plaza row)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/plaza_street.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/bollard-model-2026-10-02/` |
| Model | `assets/source/props/bollard.blend`. `export`: round plate 0.36 m with four ground bolts, a cast post 0.22 m across with a flared foot, a 56 mm band (1.6 heads) under a domed cap; 0.90 m; 1,814 triangles. No greybox in `reference` (the generated `bollard_n_0..4` are 0.26 by 0.9 m) |
| Reference | None (the catalog note and the generated row's size) |
| Paint | Not started. Stand-ins: paint, brass |
| Game | Not sent. No scene yet |
| Last hand-back | None |
| Next | Her review: on a plate or set into the paving, one band or two. Card: `documentation/howto/model-the-bollard.md` |

### park_lamp — PRP-LITE-001, park lamp standard (placed as the generated plaza lamps)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", then her "we want more than one" and two photographs: a family of three variants, `globe` (the plaza's), `acorn` (her second photo, which did not reach disk; built from the lead's description) and `pier` (her photo of a gooseneck pier lamp) |
| Holder | Christina: review the first pass (`tools/blender/plaza_street.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/park_lamp-model-2026-10-02/` |
| Model | `assets/source/props/park_lamp.blend`, built by `tools/blender/plaza_street.py`. Three `kyt_variant`s sharing one bolted plate (plate and four bolts built for `globe`, linked copies for the others): **globe** (cast bell base, tapered pole to 3.50 m, cup fitter, a 0.50 m globe centred on the light at 3.98 m; 4.23 m; 9 parts, 2,688 triangles); **acorn** (`export/variant_acorn`: slim 90 mm pole on a provisional plain ring foot, a collar, a post-top head 0.75 m tall and 0.35 m across (neck, teardrop glass, crown, pointed finial), tip 4.47 m, light 4.05 m; 13 parts, 2,656 triangles); **pier** (`export/variant_pier`: 140 mm pole to 5.5 m, a shepherd's crook with a curl, a bell shade 0.60 m across hanging 0.84 m out, bulb at 4.66 m, two banded banner arms and a blank 0.60 by 1.38 m banner at 2.61 to 3.99 m; 5.96 m to the crook; 19 parts, 3,584 triangles; sized to a standard 24 by 54 in pole banner; the photo's small box and knob left out). Check: 8,928 triangles, 4 materials, ok. Greybox pole and head in `reference`. Renders `documentation/screenshots/handbacks/park_lamp-model-2026-10-02/` (each variant, the three in a row, the pier beside her photo) |
| Reference | `documentation/reference/park_lamp/pier_gooseneck_lamp.png` (her photo, the pier lamp); her acorn photo is not on disk; `assets/source/props/reference/park_lamp_greybox.glb` |
| Paint | Not started. Stand-ins: paint, glass |
| Game | Not sent. No scene yet; it should carry a light per variant at 3.98, 4.05 and 4.66 m. Send writes `park_lamp_globe`, `park_lamp_acorn`, `park_lamp_pier` |
| Last hand-back | None |
| Next | Her review of the three: the acorn's base (how it differs from the globe's; the foot and ring are provisional), its crown a smooth dome or cut ornament; the pier's box and knob in or out, its pole height if she knows it, and whether its banner shares the flagpole banner's painting. Then its scene with the lights, and `night_test`. Card: `documentation/howto/model-the-park-lamp.md` |

### cafe_table_set — PRP-PARK-013, café table set (placed as the generated plaza terrace sets)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph. Greybox table in `reference`, and the chair's at the generator's two places and yaws |
| Holder | Christina: review the first pass (`tools/blender/plaza_street.py`), reshape, then "handed back" |
| Model | `assets/source/props/cafe_table_set.blend`. `export`: 24 parts, 6,126 triangles: a 1.2 m round top at 0.76 m on a weighted pedestal, an open 8-panel umbrella 3.0 m across (rim 2.15 m, hub 2.55 m, finial 2.67 m; canopy, ribs and hub don't collide), two bent-tube chairs at `ParkPlan.CAFE_CHAIRS` facing the table (the generator's yaws leave one with its back to the table), seat tops 0.51 m, 12 family bolts. The generator adds the chair offsets in world axes, so the set is placed unturned to match |
| Reference | `reference/cafe_table_set_greybox.glb`, `reference/cafe_chair_greybox.glb` |
| Paint | Not started. Stand-ins: paint, top, fabric, seat |
| Game | Not sent. No scene yet; `gen_crowd.gd` seats guests from `CAFE_CHAIRS` at 0.51 m, not from the prop |
| Last hand-back | None |
| Next | Her review of the pass. It stays one prop: her "disregard that original note about the chairs" (2026-10-02) retires the catalog's "arrangement and hour-state carry the story"; the chairs face the table. Card: `documentation/howto/model-the-cafe-table-set.md` |

### sky_ride_gondola — PRP-PARK-030, the sky ride's car (placed as ten generated `sky_cabin_*` in `north_sky_ride.tscn`)

| | |
|---|---|
| Stage | **model** (2026-10-02): her Santa Cruz Sky Glider photo and "this midway gondola is vital"; first pass by an agent from the lead's reading of the photo, which is not on disk. Greybox `sky_cabin_0` in `reference` (re-exported with `--frame sky_cabin_0_bucket`: the first export took the hanger strut's yaw and turned it 93°) |
| Holder | Christina: review the first pass (`tools/blender/sky_ride_gondola.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/sky_ride_gondola-model-2026-10-02/` (`below` is the player's view) |
| Model | `assets/source/props/sky_ride_gondola.blend`. `export`: 20 parts, 4,504 triangles: a rounded tub 1.45 by 1.18 by 0.72 m with a floor at 0.07 m and a bench for two (seat 0.55 m, backrest to 1.05 m), two flat strap uprights bolted outside the walls, a domed hood 1.65 by 1.38 m from 1.76 to 2.11 m with a pale underside, a bolted plate, a 70 by 120 mm hanger and a grip housing centred on the cable at 2.71 m, a 50 mm bar across the front at 0.30 m. 1.65 by 1.38 by 2.79 m |
| Reference | None of hers on disk; `documentation/reference/sky_ride_gondola/` waits for the photo |
| Paint | Not started. Four colourways (blue, teal-green, red, orange), pale underside, yellow inside, the white car number on the front's flat |
| Game | Not sent. No scene yet; the generated cars hang 2.35 m under the cable by their middle. The striped towers are a later prop |
| Last hand-back | None |
| Next | Her review: legs inside the tub or hanging out as on a chairlift; the bar's place (low footrest or lap bar); uprights outside the walls or on the rim; the hood's crown; a light on the car or none. Card: `documentation/howto/model-the-sky-ride-gondola.md` |

### arcade_cabinet — PRP-GAME-001, arcade cabinet (placed as the six authored boxes in I2)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/midway_games.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/arcade_cabinet-model-2026-10-02/` (`set` is a bank of three at the game's 2.15 m pitch) |
| Model | `assets/source/props/arcade_cabinet.blend`. `export`: 14 parts, 2,560 triangles, 7 stand-ins: a classic upright body (coin door 0.26 by 0.30 m, control-panel lip at 0.80–0.88 m, bezel leaning 9°, marquee 0.70 by 0.16 m at the top), a 0.58 by 0.48 m screen glass centred at 1.20 m, a one-player panel with a ball-top stick and six buttons; 0.82 by 0.80 by 1.72 m; faces −Y |
| Reference | `reference/arcade_cabinet_greybox.glb`: both I2 banks, a quarter turn from the prop (the booth's public side is −X there) |
| Paint | Not started. Stand-ins: cabinet, screen, marquee, black, panel, steel, button; screen and marquee to be lit; side art is paint |
| Game | Not sent. No scene yet |
| Last hand-back | None |
| Next | Her review: a one- or two-player panel; the six game faces as painted variants of one cabinet, or shape variants (trackball, cocktail, driving). Card: `documentation/howto/model-the-arcade-cabinet.md` |

### derby_race_lane — PRP-GAME-002, derby-race lane and horse target (placed as B1's five authored lanes and horses)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph; two variants, `alley` and `horse` |
| Holder | Christina: review the first pass (`tools/blender/midway_games.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/derby_race_lane-model-2026-10-02/` (`set` is five alleys mid-race, `horse_side` the horse broadside) |
| Model | `assets/source/props/derby_race_lane.blend`. `export`: 6 parts, 2,746 triangles, 3 stand-ins. `alley`, 3.70 by 0.42 by 0.155 m: a bed, two sunk side rails, a backstop, four blind 100 mm ball holes near the far end (1,790 triangles). `horse`: a flat tin horse-and-jockey cut-out 60 mm thick on a sled riding the bed, 0.56 m long, 0.50 m tall (956; does not collide). The race runs toward +Y, the player at −Y |
| Reference | `reference/derby_race_lane_greybox.glb`: B1's five lanes and horse blocks, a quarter turn from the prop (the booth's public side is −X there) |
| Paint | Not started. Stand-ins: cream laminate, dark trim, painted tin; lane numbers, lines and hole scores are paint |
| Game | Not sent. No scene yet; the alley sits on the booth counter at 1.19 m, and each horse's progress is its placement |
| Last hand-back | None |
| Next | Her review: a roll-ball lane with holes (as built) or a squirt target; the horses on the alleys (the greybox) or on a track above them, as on real derby games; the flat tin cut-out or a fuller horse. Card: `documentation/howto/model-the-derby-race-lane.md` |

### derby_prize_display — PRP-GAME-003, derby prize display (placed as B1's authored rail and four prizes)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/midway_games.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/derby_prize_display-model-2026-10-02/` (`set` on a wall at the game height, `plush` close) |
| Model | `assets/source/props/derby_prize_display.blend`. `export`: 50 parts, 7,236 triangles, 6 stand-ins: a 70 mm pipe rail 3.55 m long on three bolted wall brackets 0.33 m off the wall (the same code as `prize_rail_shelf`'s rail), and four generic plush (bear, bunny, pup, bear) at the greybox's widths and heights, hanging plumb by ring clips at 0.9 m pitch; plush and clips do not collide. Wall-hung: back on y = 0, the tallest plush's foot on z = 0; 3.55 by 0.585 by 0.945 m |
| Reference | `reference/derby_prize_display_greybox.glb`, a quarter turn from the prop (the booth's public side is −X there) |
| Paint | Not started. Stand-ins: dark metal, plush blue, mustard, coral, green |
| Game | Not sent. No scene yet; origin 2.56 m over the deck, the rail's middle at 3.45 m |
| Last hand-back | None |
| Next | Her review: the plush alone, hung on `prize_rail_shelf`'s rail, or the rail kept here too; generic animals or abstract shapes; more kinds. Card: `documentation/howto/model-the-derby-prize-display.md` |

### coin_pitch_table — PRP-GAME-004, coin-pitch table and plates (placed as B2's authored slab and nine plates)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/midway_games.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/coin_pitch_table-model-2026-10-02/` |
| Model | `assets/source/props/coin_pitch_table.blend`. `export`: 11 parts, 3,328 triangles, 5 stand-ins: a slab 3.75 by 3.45 by 0.18 m with a rolled edge and a 70 by 50 mm coin lip; nine glass dishes, five wide plates 0.42–0.46 m and four deep dishes 0.32–0.34 m, sitting on the slab at the greybox's 3 by 3 grid (the greybox floated them 2 cm); the dishes do not collide. 0.258 m tall, its bottom on z = 0 |
| Reference | `reference/coin_pitch_table_greybox.glb`, a quarter turn from the prop (the booth's public side is −X there) |
| Paint | Not started. Stand-ins: slab, lip, glass cream, mustard, coral |
| Game | Not sent. No scene yet; it sits on the booth counter, its top at 1.37 m |
| Last hand-back | None |
| Next | Her review: a counter-top slab (as built) or a table with its own legs or skirt to the deck; the plates' heights. Card: `documentation/howto/model-the-coin-pitch-table.md` |

### basket_toss — PRP-GAME-005, basket-toss basket, ball and rack (placed as B3's authored hoops and balls, and the finish layer's rack)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph; three variants, `basket`, `ball`, `rack` |
| Holder | Christina: review the first pass (`tools/blender/midway_games.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/basket_toss-model-2026-10-02/` (`set` is three baskets, the rack and balls on a wall) |
| Model | `assets/source/props/basket_toss.blend`. `export`: 16 parts, 3,988 triangles, 6 stand-ins. `basket`: a horizontal rim 0.62 m outside and 0.52 m inside, a net, a 42 mm arm, a 0.36 by 0.30 m backplate with four bolts; back on y = 0, the net's bottom on z = 0 (1,496 triangles; the net does not collide). `ball`: 0.46 m, the authored size (440). `rack`: a galvanized column stand 0.55 by 0.56 by 1.65 m holding three balls (2,052) |
| Reference | `reference/basket_toss_greybox.glb`, a quarter turn from the prop (the booth's public side is −X there). In the authored scene `B3_ball_rack` overlaps `hoop_s`; the `set` render stands it clear |
| Paint | Not started. Stand-ins: rim, backplate, net, ball, galvanized |
| Game | Not sent. No scene yet; the rims at 1.30, 1.65 and 1.30 m over the counter |
| Last hand-back | None |
| Next | Her review: a horizontal rim with a net (a hoop shot, as built) or the greybox's upright ring (a toss-through); the ball's size (0.46 m is nearly twice a basketball); the rack standing or wall-hung. Card: `documentation/howto/model-the-basket-toss.md` |

### prize_rail_shelf — PRP-GAME-006, midway prize rail and shelf (placed as B1's authored rail and B2's authored shelf)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph; two variants, `rail` and `shelf` |
| Holder | Christina: review the first pass (`tools/blender/midway_games.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/prize_rail_shelf-model-2026-10-02/` (`set` shows both on one wall) |
| Model | `assets/source/props/prize_rail_shelf.blend`. `export`: 14 parts, 2,068 triangles, 3 stand-ins. `rail`: a 70 mm pipe 3.55 m long on three wall plates with two bolts each and 42 mm arms, 0.33 m off the wall (1,364 triangles); `shelf`: a 3.20 by 0.55 by 0.10 m plank with a rolled edge on three knee gussets (704). Wall-hung: backs on y = 0, feet on z = 0. B2's three hanging prize tubes are prizes, not the fixture, and are left out |
| Reference | `reference/prize_rail_shelf_greybox.glb`, a quarter turn from the prop (the booth's public side is −X there) |
| Paint | Not started. Stand-ins: dark metal, bleached timber |
| Game | Not sent. No scene yet; the rail's middle at 3.45 m, the shelf's top at 2.85 m |
| Last hand-back | None |
| Next | Her review: round pipe (as built) or the greybox's square bar; wall brackets or hangers from the booth's ceiling; a front lip on the shelf. Card: `documentation/howto/model-the-prize-rail-shelf.md` |

### menu_board — PRP-FOOD-001, service-window menu board (placed as I3's two authored boards)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph; two variants, `wide` and `narrow` |
| Holder | Christina: review the first pass (`tools/blender/food_service.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/menu_board-model-2026-10-02/` |
| Model | `assets/source/props/menu_board.blend`. `export`: 16 parts, 2,768 triangles (1,440 of them the ten family bolts), 3 stand-ins. `wide` 3.90 by 1.35 m in three bays on two mullions, six bolts; `narrow` 1.60 by 1.35 m, four bolts; both 0.107 m deep: an 8 cm frame round a dark panel 2.5 cm behind its face, bolted through the frame's face. Standing on its bottom edge at the origin, facing −Y; nothing collides |
| Reference | `reference/menu_board_greybox.glb` (I3's `menu_board_w` and `_e`) |
| Paint | Not started. Stand-ins: frame, panel, bolts; the menu is paint, a swappable state |
| Game | Not sent. No scene yet; I3 hangs them at 2.025 m facing the windows, turned half round from the prop |
| Last hand-back | None |
| Next | Her review: one pane or three on the wide board; a third size for B4's two 0.9 by 1.2 m menus (`menu_n`, `menu_s`). Card: `documentation/howto/model-the-menu-board.md` |

### pie_display_case — PRP-FOOD-002, pie display case (placed as I3's authored case)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/food_service.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/pie_display_case-model-2026-10-02/` |
| Model | `assets/source/props/pie_display_case.blend`. `export`: 17 parts, 2,676 triangles (1,960 the pies), 4 stand-ins: a 7 cm steel base, solid ends, one glass shell over the front and top rolling over in a 16 cm quarter round, two sliding back doors, a glass shelf at 0.30 m, five pies 0.26 m across and 11 cm tall (three on the deck, two on the shelf); 1.80 by 0.75 by 0.55 m, z = 0 the counter top; the pies do not collide |
| Reference | `reference/pie_display_case_greybox.glb` |
| Paint | Not started. Stand-ins: steel, glass (see-through in Blender), foil, pastry |
| Game | Not sent. No scene yet; it stands on the café counter at (−4.1, 2.55) in I3's frame, the customer side toward the windows |
| Last hand-back | None |
| Next | Her review: a straight front with solid ends (as built) or curved glass; how many pies, and a cut one. Card: `documentation/howto/model-the-pie-display-case.md` |

### concession_equipment — PRP-FOOD-003, concession counter equipment (placed as B4's authored service window and three taffy jars)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph; two variants, `counter` and `taffy_jar` |
| Holder | Christina: review the first pass (`tools/blender/food_service.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/concession_equipment-model-2026-10-02/` |
| Model | `assets/source/props/concession_equipment.blend`. `export`: 7 parts, 2,092 triangles, 5 stand-ins. `counter`: a 3.90 by 0.45 m laminate slab 6 cm thick with a rounded nose on three steel gussets, standing on the gussets' feet with its top 0.40 m up (788 triangles; collides). `taffy_jar`: a glass jar 0.42 m across and 0.72 m tall with a chrome domed lid and a lumpy taffy fill, the authored size, about twice a real one (1,304; does not collide) |
| Reference | `reference/concession_equipment_greybox.glb` (B4's `service_window` and `taffy_jar_*`) |
| Paint | Not started. Stand-ins: laminate, steel, glass, chrome, taffy |
| Game | Not sent. No scene yet; the counter hangs with its top at about 1.1 m and its back edge +Y; the jars are placed three times |
| Last hand-back | None |
| Next | Her review: which other counter tools join the family (a fryer, sugar shaker, register, taffy puller); the jars at real size; the counter's length (B4's window is 3.9 m, I3's 3.65 m). Card: `documentation/howto/model-the-concession-equipment.md` |

### service_freezer — PRP-FOOD-004, service freezer box (placed as I3's authored freezer)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/food_service.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/service_freezer-model-2026-10-02/` |
| Model | `assets/source/props/service_freezer.blend`. `export`: 14 parts, 2,140 triangles, 5 stand-ins: a hollow chest 0.95 m tall on a recessed kick, a dark lid frame 2.10 by 0.80 m with two sliding glass lids and flat pulls, and a header panel from 1.00 to 1.45 m at the back on two short posts, bolted through its face (the greybox is 1.45 m tall, and a chest that tall could not be reached into); it all collides |
| Reference | `reference/service_freezer_greybox.glb` |
| Paint | Not started. Stand-ins: shell, trim, glass, plastic; the header's graphic is paint |
| Game | Not sent. No scene yet; it stands at (7.45, 1.5) in I3's frame, under `I3_freezer_work_light` |
| Last hand-back | None |
| Next | Her review: the header or a plain chest (one panel, two posts and four bolts to delete); stock inside or empty. Card: `documentation/howto/model-the-service-freezer.md` |

### delivery_crate — PRP-FOOD-005, delivery crate (placed as I3's two stacked boxes)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph; two variants, `large` and `small` |
| Holder | Christina: review the first pass (`tools/blender/food_service.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/delivery_crate-model-2026-10-02/` |
| Model | `assets/source/props/delivery_crate.blend`. `export`: 38 parts, 1,672 triangles, one stand-in (timber). `large` 0.75 by 0.90 by 0.65 m and `small` 0.70 by 0.75 by 0.50 m, 19 parts each: four 5 cm corner posts, three 2 cm slats a side with 4 cm gaps, three floor boards, an open top; both collide. The authored sizes, about twice a real produce crate |
| Reference | `reference/delivery_crate_greybox.glb` |
| Paint | Not started; stencils are paint |
| Game | Not sent. No scene yet; a stack is two placements |
| Last hand-back | None |
| Next | Her review: plastic milk crates or bread trays as well; real size or the authored size. Card: `documentation/howto/model-the-delivery-crate.md` |

### condiment_set — PRP-FOOD-006, condiment and napkin set (placed in the café finish layer)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph; four variants, `bottle_red`, `bottle_yellow`, `napkin_dispenser`, `straw_holder` |
| Holder | Christina: review the first pass (`tools/blender/food_service.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/condiment_set-model-2026-10-02/` |
| Model | `assets/source/props/condiment_set.blend`. `export`: 11 parts, 1,332 triangles, 4 stand-ins, nothing colliding: two squeeze bottles of one shape, 9 by 25.5 cm (320 triangles each); an upright chrome two-faced napkin dispenser 16 by 11 by 20 cm with a napkin's tongue showing (392); a chrome cup 9 by 11 cm with seven straws to 22 cm (300). Real size: the greybox's bottles are 22 by 62 cm and its napkin stack 42 by 50 cm, two to three times real |
| Reference | `reference/condiment_set_greybox.glb` |
| Paint | Not started. Stand-ins: plastic, chrome, paper, straw; the labels and the bottles' colours are paint |
| Game | Not sent. No scene yet |
| Last hand-back | None |
| Next | Her review: real size (as built) or the greybox's; a push-button straw dispenser. At the unwrap the two bottles need `--no-mirror`, or they share one texture space. Card: `documentation/howto/model-the-condiment-set.md` |

### used_tray — PRP-FOOD-007, used tray and funnel-cake remnant (placed on a café terrace table)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/food_service.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/used_tray-model-2026-10-02/` |
| Model | `assets/source/props/used_tray.blend`. `export`: 3 parts, 2,344 triangles (1,556 the cake), 3 stand-ins, nothing colliding: a flared tray 0.46 by 0.36 m and 3 cm deep with a recessed underside, a 24 cm paper plate off-centre, and the funnel cake, two spirals of batter with its front third eaten. Real size: the greybox's tray is 0.72 by 0.90 m |
| Reference | `reference/used_tray_greybox.glb` |
| Paint | Not started. Stand-ins: plastic, paper, batter; the sugar is paint |
| Game | Not sent. No scene yet; it lies on a terrace table at (−86.1, −55.1), turned 10° |
| Last hand-back | None |
| Next | Her review: real size or the greybox's; more clues (a fork, a napkin, a cup). Card: `documentation/howto/model-the-used-tray.md` |

### refill_cup — PRP-FOOD-008, park refill cup (placed as the café residue's two cups)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/food_service.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/refill_cup-model-2026-10-02/` |
| Model | `assets/source/props/refill_cup.blend`. `export`: 3 parts, 540 triangles, 3 stand-ins, nothing colliding: a 44 oz tapered cup 10 cm at the rim and 21.5 cm tall, hollow, a domed lid to 25.4 cm with a straw collar, a straw to 34 cm leaning 6°. Real size: the greybox's cups are 18 by 42 cm |
| Reference | `reference/refill_cup_greybox.glb` |
| Paint | Not started. Stand-ins: cup, lid, straw; the logo is paint. `PRP-STORY-006` is the same cup with the old logo |
| Game | Not sent. No scene yet |
| Last hand-back | None |
| Next | Her review: size; a stacked-cups variant (the scene calls its two "stacked cups"). Card: `documentation/howto/model-the-refill-cup.md` |

### boarding_gate — PRP-OPS-001, boarding/load/exit gate (placed as the authored gates at the wheel, coaster and funhouse)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/ride_operations.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/boarding_gate-model-2026-10-02/` |
| Model | `assets/source/props/boarding_gate.blend`. `export`: 21 parts, 2,908 triangles, 4 stand-ins: two 0.16 m posts 1.25 m tall and 2.0 m apart on base plates with two anchor bolts each, capped; one leaf hinged on the +Y post, a welded 42 mm tube loop round a 3 cm panel, its top rail at the greybox's 0.675 m and its bottom at 0.14 m; two strap hinges, a slide-bolt latch into a bolted keeper. 0.28 by 2.26 by 1.29 m |
| Reference | `reference/boarding_gate_greybox.glb` |
| Paint | Not started; LOAD and EXIT are paint on the panel |
| Game | Not sent. No scene yet; the composition's boxes in `boardwalk_operations.tscn` stay placed until the first Send |
| Last hand-back | None |
| Next | Her review: the leaf's height (0.675 m is hip height; 1.0 m is usual, `G_RAIL_Z`); whether the coaster's 3.6 m rail and the funhouse's gates become variants. Card: `documentation/howto/model-the-boarding-gate.md` |

### wheel_operator_control — PRP-OPS-002, wheel operator control (placed as R1's authored control)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/ride_operations.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/wheel_operator_control-model-2026-10-02/` (they look at the panel's side) |
| Model | `assets/source/props/wheel_operator_control.blend`. `export`: 15 parts, 2,314 triangles, 7 stand-ins: a plinth and a rounded cabinet 1.15 by 0.72 m, 1.18 m tall, with a lipped top; a cream panel 45 mm proud on its +X face with four corner bolts, a 0.10 m green dome lamp in a bezel, a 0.13 m red mushroom stop on a yellow legend plate and three push buttons, at the greybox's places. The panel faces +X, as the composition places it. 1.29 by 0.76 by 1.18 m |
| Reference | `reference/wheel_operator_control_greybox.glb` |
| Paint | Not started; the legends are paint |
| Game | Not sent. No scene yet; the composition's boxes in `boardwalk_operations.tscn` stay placed until the first Send |
| Last hand-back | None |
| Next | Her review of the pass. The composition's stool stands at the end away from the panel: move it when the control is placed. Card: `documentation/howto/model-the-wheel-operator-control.md` |

### wheel_boarding_lift — PRP-OPS-003, wheel step-free boarding lift (placed as R1's authored lift)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/ride_operations.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/wheel_boarding_lift-model-2026-10-02/` |
| Model | `assets/source/props/wheel_boarding_lift.blend`. `export`: 23 parts, 4,988 triangles, 6 stand-ins, the greybox's 1.28 m platform and every height kept: a 1.5 m shaft plinth 0.18 m tall on four ground bolts, four 0.12 m posts to 4.30 m, a header at 4.33–4.49 m; the car (floor at 0.27 m, three walls to 0.90 m, a capping rail at 0.93 m, a hinged gate on +X); the bridge, 1.1 m wide, out to x 1.815 at 4.05–4.29 m, with a solid-panel rail and capping tube on each edge to 5.48 m; a blank sign board bolted between the south posts at 2.29 m. The bridge is centred on the car's opening (the greybox's met only 0.69 m of it); the south rail is added. 3.63 by 1.58 by 5.48 m |
| Reference | `reference/wheel_boarding_lift_greybox.glb` |
| Paint | Not started |
| Game | Not sent. No scene yet; the composition's boxes in `boardwalk_operations.tscn` stay placed until the first Send. Kept clear as operating equipment |
| Last hand-back | None |
| Next | Her review: keep the added south rail; at the top the car's walls would reach 4.95 m, past the header at 4.33 m: raise the mast about 0.6 m or lower the walls. Card: `documentation/howto/model-the-wheel-boarding-lift.md` |

### maintenance_locker — PRP-OPS-004, maintenance locker and storage (placed as R1's authored chest; R2's upright locker not built)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/ride_operations.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/maintenance_locker-model-2026-10-02/` |
| Model | `assets/source/props/maintenance_locker.blend`. `export`: 14 parts, 2,352 triangles, 3 stand-ins: a rounded body 1.6 by 0.78 by 0.80 m under a crowned lid 1.68 by 0.86 m to 0.92 m, a piano hinge along +Y, a hasp (a staple on a plate and a slotted strap) at the front, chunky D pulls on bolted plates at each end; closed, no padlock. 1.79 by 0.89 by 0.92 m |
| Reference | `reference/maintenance_locker_greybox.glb` |
| Paint | Not started |
| Game | Not sent. No scene yet; the composition's boxes in `boardwalk_operations.tscn` stay placed until the first Send |
| Last hand-back | None |
| Next | Her review; R2's upright locker (0.8 by 1.4 by 2.05 m) as a variant here or a prop of its own. Card: `documentation/howto/model-the-maintenance-locker.md` |

### coaster_brake_console — PRP-OPS-005, coaster brake console (placed as R2's authored console)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/ride_operations.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/coaster_brake_console-model-2026-10-02/` (they look at the panel's side) |
| Model | `assets/source/props/coaster_brake_console.blend`. `export`: 21 parts, 2,854 triangles, 6 stand-ins: a plinth and a cabinet 0.82 by 1.25 by 1.32 m with a lipped top; a cream panel 60 mm proud on its −X face with four bolts, two gauges with cream dials and three buttons; on the top's front edge the brake lever, a tube with a red ball grip at 1.71 m, between two quadrant plates, pivoting on a bolt through each. 1.02 by 1.29 by 1.76 m |
| Reference | `reference/coaster_brake_console_greybox.glb` |
| Paint | Not started; "BRAKE" is paint |
| Game | Not sent. No scene yet; the composition's boxes in `boardwalk_operations.tscn` stay placed until the first Send |
| Last hand-back | None |
| Next | Her review: an e-stop on the console as well (the composition's lamp and stop on this panel are `block_lamp_estop` now, on a post). Card: `documentation/howto/model-the-coaster-brake-console.md` |

### block_lamp_estop — PRP-OPS-006, block lamp and emergency stop (placed as the two spheres on R2's brake panel)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/ride_operations.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/block_lamp_estop-model-2026-10-02/` |
| Model | `assets/source/props/block_lamp_estop.blend`. `export`: 15 parts, 2,320 triangles, 5 stand-ins: a round plate on four ground bolts, a 90 mm post, a signal head at 1.92 m (drum, hood, bezel, a 0.10 m green dome toward −Y) and an e-stop station on a bolted band at 1.05 m (box, yellow legend plate, a 0.12 m red mushroom toward −Y). One aspect. 0.26 by 0.33 by 2.03 m |
| Reference | `reference/block_lamp_estop_greybox.glb`, a size reference only: the export dropped the composition's two spheres to the floor |
| Paint | Not started |
| Game | Not sent. No scene yet; the composition's boxes in `boardwalk_operations.tscn` stay placed until the first Send |
| Last hand-back | None |
| Next | Her review of the pass: one aspect, and the heights. Card: `documentation/howto/model-the-block-lamp-estop.md` |

### hose_reel — PRP-OPS-007, maintenance hose and reel (placed as R2's `brake_hose` and the pier service face's ring)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/ride_operations.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/hose_reel-model-2026-10-02/` |
| Model | `assets/source/props/hose_reel.blend`. `export`: 18 parts, 3,124 triangles, 6 stand-ins: a floor-standing standpipe reel against a wall at y = +0.05: a bolted plate, a 1.35 m post with a cap, a hub between two open five-spoked flanges 0.62 m across at 0.95 m, the hose as one scalloped coil of three 47 mm turns, a crank with a bolted axle nut and a knob, the hose's tail looping to a brass nozzle in a clip on the post. 0.62 by 0.54 by 1.38 m |
| Reference | `reference/hose_reel_greybox.glb` |
| Paint | Not started |
| Game | Not sent. No scene yet; the composition's boxes in `boardwalk_operations.tscn` stay placed until the first Send |
| Last hand-back | None |
| Next | Her review: floor-standing (the composition hangs its ring at 2.75 m, out of reach); this reel in place of R2's `brake_hose` ring. Card: `documentation/howto/model-the-hose-reel.md` |

### specialist_work_cart — PRP-OPS-008, specialist work cart (placed as SH1's work cart)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/ride_operations.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/specialist_work_cart-model-2026-10-02/` |
| Model | `assets/source/props/specialist_work_cart.blend`. `export`: 36 parts, 4,824 triangles, 8 stand-ins: a two-deck tray cart (a lipped tray at 0.62 m, a shelf at 0.30 m, four tube posts), two 0.25 m fixed wheels on an axle at −X, two swivel castors at +X, a 42 mm tongue pinned with a bolt and rising 15° to a T grip; on the tray a red toolbox, a brass oil can, a grease gun and a coiled cable, so the load names the job. 2.03 by 0.82 by 0.93 m |
| Reference | `reference/specialist_work_cart_greybox.glb` |
| Paint | Not started |
| Game | Not sent. No scene yet; the composition's boxes in `boardwalk_operations.tscn` stay placed until the first Send |
| Last hand-back | None |
| Next | Her review: the load. Card: `documentation/howto/model-the-specialist-work-cart.md` |

### funhouse_turnstile — PRP-OPS-009, funhouse entry turnstile (placed as P2's authored turnstile)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/service_operations.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/funhouse_turnstile-model-2026-10-02/` |
| Model | `assets/source/props/funhouse_turnstile.blend`. `export`: 13 parts, 1,748 triangles, 3 stand-ins: a 0.54 m pedestal with four anchor bolts and a collar, a 0.22 m post to 1.55 m with a domed cap, a hub drum at 0.98 m, three 70 mm arms with 110 mm ball ends 1.0 m from the axis at 120°, one toward −Y. Faces −Y, a quarter turn from the greybox; the post on the origin. 1.84 by 1.61 by 1.55 m |
| Reference | `reference/funhouse_turnstile_greybox.glb` |
| Paint | Not started |
| Game | Not sent. No scene yet; it stands in P2's entry at (−82.85, 27.0), approached from −X |
| Last hand-back | None |
| Next | Her review: the arms' reach (the greybox's 1.0 m; a real one is 0.6 to 0.75 m); the exit's push gate as a variant of this or of `boarding_gate`. Card: `documentation/howto/model-the-funhouse-turnstile.md` |

### funhouse_operator_box — PRP-OPS-010, funhouse operator box and show stop (placed as P2's authored box)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/service_operations.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/funhouse_operator_box-model-2026-10-02/` |
| Model | `assets/source/props/funhouse_operator_box.blend`. `export`: 10 parts, 1,600 triangles, 5 stand-ins: a kick plinth, a rounded cabinet 1.25 m across the front and 1.0 m deep with a lipped cap at 1.48 m, a blank 1.0 by 0.72 m panel 6 cm proud with four bolts, and the show stop, a yellow collar and a red 0.13 m mushroom head, at x −0.2 and 1.09 m up. Faces −Y. 1.29 by 1.17 by 1.48 m |
| Reference | `reference/funhouse_operator_box_greybox.glb` |
| Paint | Not started; the controls are paint |
| Game | Not sent. No scene yet; it stands at (−81.55, 28.55), the panel toward −X |
| Last hand-back | None |
| Next | Her review: a vertical panel (as built) or a sloped desk. Card: `documentation/howto/model-the-funhouse-operator-box.md` |

### service_door — PRP-OPS-011, service door and operating notice (placed at P2 and the service connections)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/service_operations.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/service_door-model-2026-10-02/` |
| Model | `assets/source/props/service_door.blend`. `export`: 12 parts, 1,536 triangles, 5 stand-ins: a frame 2.20 by 4.35 m, 7 cm proud of the wall plane y = 0, its feet on z = 0, nothing in the wall; two 0.97 by 4.17 m leaves with kick plates and 42 mm pull bars at 0.95–1.55 m; a blank 0.42 by 0.30 m notice at 1.65 m with four bolts. 2.20 by 0.16 by 4.35 m |
| Reference | `reference/service_door_greybox.glb` |
| Paint | Not started; the notice's words and the hinges are paint |
| Game | Not sent. No scene yet; it stands at (−70.82, 32.0) facing +X, under P2's service light |
| Last hand-back | None |
| Next | Her decision: the greybox's 4.35 m as a tall hinged pair (as built), a roller shutter, or a 2.4 m pair under a fixed panel; S1 and S2's stock doors, as tall and 1.55 m wide, as a width variant. Card: `documentation/howto/model-the-service-door.md` |

### fish_cleaning_sink — PRP-OPS-012, fish-cleaning sink and cutting board (placed at the pier's fishing service face)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/service_operations.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/fish_cleaning_sink-model-2026-10-02/` |
| Model | `assets/source/props/fish_cleaning_sink.blend`. `export`: 20 parts, 2,628 triangles, 5 stand-ins: a counter 2.45 by 1.05 m at 0.98 m on four 9 cm legs, the back two rising to 2.0 m as posts; a 2.12 by 0.78 m trough let in (floor 0.76 m) with a drain and a pipe to the deck; side stretchers; a back board 2.65 m wide from 0.90 to 2.085 m bolted to the posts; a gooseneck faucet with a lever; a 0.52 by 0.72 m board across the trough. 2.65 by 1.08 by 2.085 m. The greybox's counter is 1.35 m, chest high |
| Reference | `reference/fish_cleaning_sink_greybox.glb` |
| Paint | Not started; the sign is paint |
| Game | Not sent. No scene yet; it stands at (−161.0, 13.1), its back to the pavilion wall |
| Last hand-back | None |
| Next | Her review: the work height (0.98 m against the greybox's 1.35 m); one faucet or two along the trough. Card: `documentation/howto/model-the-fish-cleaning-sink.md` |

### tackle_cart — PRP-OPS-013, tackle cart (placed at the pier)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/service_operations.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/tackle_cart-model-2026-10-02/` |
| Model | `assets/source/props/tackle_cart.blend`. `export`: 21 parts, 2,772 triangles, 7 stand-ins: a rounded chest 2.10 by 1.00 m from 0.18 m up with a lipped lid at 1.08 m, two 0.42 m wheels with tyres on an axle at x −0.98, two stub legs with pads, a 42 mm U handle at 0.69 m welded on two bosses; on the lid a tackle box and a bait cooler; nothing branded. The greybox's frame (wheels −X, handle +X). 2.94 by 1.45 by 1.47 m |
| Reference | `reference/tackle_cart_greybox.glb` |
| Paint | Not started |
| Game | Not sent. No scene yet; it stands at (−155.5, 13.25), the handle toward +X |
| Last hand-back | None |
| Next | Her decision: the composition's 2.2 m, or about half, a cart one person pulls along the pier (the catalog note calls it small). Card: `documentation/howto/model-the-tackle-cart.md` |

### rod_rack — PRP-OPS-014, rod rack and fishing rods (placed at the pier)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/service_operations.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/rod_rack-model-2026-10-02/` |
| Model | `assets/source/props/rod_rack.blend`. `export`: 33 parts, 2,748 triangles, 5 stand-ins: a foot board, two 10 cm posts to 3.0 m, two rails at 1.45 and 2.80 m with holes, bolted at their ends, three rods 3.70, 4.00 and 3.85 m long (a cork grip and reel seat, the blank tapering from 4.4 to 2.2 cm, two guides, a spinning reel each) standing 0.21 m apart. 0.72 by 0.30 by 4.12 m |
| Reference | `reference/rod_rack_greybox.glb` |
| Paint | Not started; the line and wraps are paint |
| Game | Not sent. No scene yet; it stands at (−164.15, 2.1), where the greybox's base is about 0.6 m above the pier deck: check the deck when it is placed |
| Last hand-back | None |
| Next | Her review: the rods' thickness, the reels' size, three rods. Card: `documentation/howto/model-the-rod-rack.md` |

### cleanup_bin — PRP-OPS-015, cleanup bin and drain bucket (placed at the pier)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph |
| Holder | Christina: review the first pass (`tools/blender/service_operations.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/cleanup_bin-model-2026-10-02/` |
| Model | `assets/source/props/cleanup_bin.blend`. `export`: 5 parts, 1,240 triangles, 3 stand-ins: an open galvanised bin 0.82 m across and 1.40 m tall at x +0.25 (a rolled rim, two swage bands, a recessed floor) and an open tapered bucket 0.52 m across and 0.72 m tall at (−0.40, −0.05) with two ears and a dropped wire bail. 1.37 by 0.86 by 1.40 m |
| Reference | `reference/cleanup_bin_greybox.glb` |
| Paint | Not started |
| Game | Not sent. No scene yet; they stand at (−158.6, 13.2) and (−159.25, 13.25) |
| Last hand-back | None |
| Next | Her review: a lid on the bin; the bucket's 0.72 m. Card: `documentation/howto/model-the-cleanup-bin.md` |

### folded_stock_cart — PRP-OPS-016, folded stock cart and empty crate (placed at the S1 and S2 service connections)

| | |
|---|---|
| Stage | **model** (2026-10-02): her "first pass from notes", no photograph; no greybox, sizes from the scene's `S1_folded_cart` and `S2_empty_crate`; two variants, `cart` and `crate` |
| Holder | Christina: review the first pass (`tools/blender/service_operations.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/folded_stock_cart-model-2026-10-02/` (both variants in a row) |
| Model | `assets/source/props/folded_stock_cart.blend`. `export`: 27 parts, 2,116 triangles, 5 stand-ins. `cart` (1,632 triangles): a 1.25 by 0.90 m platform truck stood on its long edge against a wall, leaning 4°, its underside out with two chassis rails and four 13 cm castors, its handle folded over the deck on two bolted pivots; 1.25 by 0.32 by 0.91 m. `crate` (484): an open timber box 0.92 m square and 0.72 m tall on two skids with four corner battens |
| Reference | None: the scene's two boxes could not be isolated |
| Paint | Not started; the slats are paint |
| Game | Not sent. No scene yet; the cart by S1 at (−82.95, −13.55) and the crate by S2 at (−82.92, 13.65), both against the back-of-house wall |
| Last hand-back | None |
| Next | Her review: the cart leaning (as built) or standing square (`F_LEAN_DEG`). Card: `documentation/howto/model-the-folded-stock-cart.md` |

## Wildlife

Ambient and unscored, models only: how each moves is a separate decision. First
passes built 2026-10-03 by agents from the catalog notes, no photographs, each
species an assumption for her to confirm. Every animal faces −Y with its own
left at +X (the gull faces +Y, its left at −X: the rule is the animal's own
side), its lowest point on z = 0, every part `kyt_collision = none`, moving
parts on pivot empties named as the gull's (`head_pivot`, `upper_pivot`,
`lower_pivot`, `wing_left`, `leg_left` on the birds, which `bird.gd` looks up).
Send to game today merges the parts into one still mesh and drops the pivots,
so the joints reach the game only when Send changes, once motion is decided.
Renders `documentation/screenshots/handbacks/<animal>-model-2026-10-03/`,
group lineups `documentation/screenshots/wildlife-lineup-2026-10-03/`.

### Fliers — PRP-WILD-006 to 009: bee, fly, hummingbird, butterfly

| | |
|---|---|
| Stage | **model**, first pass (2026-10-03, an agent, `tools/blender/wildlife_fliers.py`) |
| Holder | Christina: her review |
| Model | `assets/source/props/{bee,fly,hummingbird,butterfly}.blend`, real size. `bee` honey bee worker, wings spread, 384 triangles; `fly` house fly, under 8 mm, wings folded, 392; `hummingbird` male Anna's, hovering (root pitched 40°, head 25°), 756; `butterfly` monarch, wings open flat, body chunkier than life, 372 |
| Paint | Not started. Stand-ins; wings double-sided |
| Game | Not sent. A readable game scale for the insects is her call |
| Next | Her review. Card: `documentation/howto/model-the-fliers.md` |

### Coast animals — PRP-WILD-010, 011, 012, 023, 024: pelican, sea lion, sea otter, whale, dolphin

| | |
|---|---|
| Stage | **model**, first pass (2026-10-03, an agent, `tools/blender/wildlife_coast.py`) |
| Holder | Christina: her review |
| Model | `assets/source/props/{pelican,sea_lion,sea_otter,whale,dolphin}.blend`. `pelican` brown, standing hunched as on a piling, 2,178 triangles; `sea_lion` California, adult female, propped on its fore flippers, hind flippers turned forward, 2,150; `sea_otter` southern, floating on its back, 1,762; `whale` gray, about 13 m, 2,578; `dolphin` bottlenose, 2.7 m, 2,022. A `waterline` empty in `reference`: otter z = 0.12, whale 2.2, dolphin 0.45 |
| Paint | Not started. Stand-ins |
| Game | Not sent |
| Next | Her review. Card: `documentation/howto/model-the-coast-animals.md` |

### Tide pool and sea — PRP-WILD-013 to 016, 022, 025: crab, starfish, sea urchin, scallop, jellyfish, octopus

| | |
|---|---|
| Stage | **model**, first pass (2026-10-03, an agent, `tools/blender/wildlife_invertebrates.py`) |
| Holder | Christina: her review |
| Model | `assets/source/props/{crab,starfish,sea_urchin,scallop,jellyfish,octopus}.blend`. `crab` red rock crab, 1,224 triangles; `starfish` ochre star, 600; `sea_urchin` purple, 37 fat spines, 594; `scallop` rock scallop, 0.14 m, top valve open 12°, 708; `octopus` two-spot, 0.65 m across, 2,080; `jellyfish` four `kyt_variant`s: `moon` 832, `sea_nettle` (tentacles 0.85 m) 1,032, `velella` by-the-wind sailor floating 236 (`waterline_velella` in `reference`), `velella_stranded` 284. No Physalia bluebottle (her "lets not use bluebottle") |
| Paint | Not started. Stand-ins |
| Game | Not sent |
| Next | Her review. Card: `documentation/howto/model-the-tidepool-animals.md` |

### Fish — PRP-WILD-017 to 021, 026 to 028: salmon, trout, striped bass, halibut, surf perch, tuna, rockfish, eel

| | |
|---|---|
| Stage | **model**, first pass (2026-10-03, an agent, `tools/blender/wildlife_fish.py`, one lofted body from per-species sections) |
| Holder | Christina: her review |
| Model | `assets/source/props/{salmon,trout,striped_bass,halibut,surf_perch,tuna,rockfish,eel}.blend`, swimming level. Chinook salmon 0.90 m, 1,080 triangles; rainbow trout 0.45 m, 1,080; striped bass 0.75 m, 1,092; California halibut (left-eyed, lying flat) 0.70 m, 1,016; barred surfperch 0.30 m, 1,084; yellowfin tuna 1.40 m, 1,412; vermilion rockfish 0.50 m, 1,164; California moray as the eel, 1.00 m, mouth closed, four body segments, 1,366 |
| Paint | Not started. Stand-ins |
| Game | Not sent |
| Next | Her review. Card: `documentation/howto/model-the-fish.md` |

### Town animals — PRP-WILD-029 to 033: raccoon, cat, mouse, rat, dog

| | |
|---|---|
| Stage | **model**, first pass (2026-10-03, an agent, `tools/blender/wildlife_town.py`, one quadruped kit) |
| Holder | Christina: her review |
| Model | `assets/source/props/{raccoon,cat,mouse,rat,dog}.blend`, standing on all fours. `raccoon` back arched, head low, 2,364 triangles; `cat` domestic shorthair, tail up, 2,424; `mouse` house mouse, 1,112; `rat` Norway rat, 1,176; `dog` medium mixed breed, tan, drop ears, 2,732. Centred on the bounding box, tail included |
| Paint | Not started. Stand-ins; the raccoon's mask and rings and the cat's coat (per placement) are paint |
| Game | Not sent |
| Next | Her review. Card: `documentation/howto/model-the-town-animals.md` |

### Lagoon swimmers — PRP-WILD-034, 038, 039: harbor seal, leopard shark, bat ray

| | |
|---|---|
| Stage | **model**, first pass (2026-10-03, an agent, `tools/blender/wildlife_lagoon_swimmers.py`), for the tidal lagoon in `documentation/maps/entrance-landscaping.html` |
| Holder | Christina: her review |
| Model | `assets/source/props/{harbor_seal,leopard_shark,bat_ray}.blend`. `harbor_seal` Pacific, hauled out on its belly, hind flippers nearly flat, 1.73 m, 1,800 triangles (`harbor_seal_beside_sea_lion.png` in its renders); `leopard_shark` 1.40 m, 1,456; `bat_ray` 1.20 m across, no sting, 976 |
| Paint | Not started. Stand-ins |
| Game | Not sent |
| Next | Her review. Card: `documentation/howto/model-the-lagoon-swimmers.md` |

### Lagoon birds — PRP-WILD-035 to 037: heron, egret, shorebird

| | |
|---|---|
| Stage | **model**, first pass (2026-10-03, an agent, `tools/blender/wildlife_lagoon_birds.py`), for the tidal lagoon |
| Holder | Christina: her review |
| Model | `assets/source/props/{heron,egret,shorebird}.blend`, standing, legs two to three times real thickness. `heron` great blue, 1.04 m, S-neck, 1,852 triangles; `egret` two `kyt_variant`s, `great` 0.95 m 1,412 and `snowy` 0.60 m with three chunky plumes 1,472; `shorebird` two, `sandpiper` (western) 0.11 m 1,300 and `godwit` (marbled) 0.33 m 1,348 |
| Paint | Not started. Stand-ins; the godwit's black bill tip is paint |
| Game | Not sent |
| Next | Her review. Card: `documentation/howto/model-the-lagoon-birds.md` |

## Beach town buildings

First block-outs, 2026-10-02 (her "lets go ahead and build some of them", sites not final). Each in `assets/source/props/` from `new_prop.py`, built by its own script in `tools/blender/`; front on Blender −Y; floor (threshold) at z = 0; `ground_line` in `reference`; renders in `documentation/screenshots/beach-town-buildings-2026-10-02/<name>/`. Town look: `documentation/reference/beach_town/` (her two Avila Beach photos). None sent, placed or committed.

### fishing_shack — the plaza's three older fishing shacks (beach town plan, zone C)

| | |
|---|---|
| Stage | **model**, block-out (massing only; no shack photo yet) |
| Holder | Christina: her review and a shack photo |
| Model | `assets/source/props/fishing_shack.blend`, `tools/blender/fishing_shack.py` (`--tenant bait|market|smokehouse`). 5.5 × 7 m, eave 2.70, roof top 4.00, gable and sign to the plaza; customer door, counter hatch and awning in front, service door behind, each a real opening with its own leaf; 1,240 triangles; 0 coplanar pairs |
| Next | Her photo (`documentation/reference/fishing_shack/`). Open: there is no back street (bins behind face the strand's steps); the mounted greybox shacks in `coastal_fast_pass.tscn` stand at the old bank |

### pier_seafood_restaurant — seafood restaurant 2 on the ferry plaza (zone C)

| | |
|---|---|
| Stage | **model**, block-out |
| Holder | Christina: her review |
| Model | `assets/source/props/pier_seafood_restaurant.blend`, `tools/blender/pier_seafood_restaurant.py`. The plan's 18 × 10 m is building (12.5 × 10, kitchen east) plus a 5.5 m sunset deck; pale blue, white trim, grey gable, porthole in each gable (the Avila pier-root building); plaza doors, deck doors, service and kitchen doors as real openings with leaves (`kyt_hinge_edge = side`, which Send does not yet read); 3,052 triangles; 0 coplanar pairs |
| Next | Her call on the beach ramp behind the back wall (only a 2 m service strip) and deliveries crossing the plaza; pitch, door glazing, deck railing |

### surf_shop — D2, the surf shop on the main drag

| | |
|---|---|
| Stage | **model**, block-out pass 2 (2026-10-02): built from her photo (`documentation/reference/surf_shop/good_surf_shop.webp`, "this is a good surf shop"); the greybox's height, roof and floor do not bind (her "why do we care if the current grey box is one story") |
| Holder | Christina: her review |
| Model | `assets/source/props/surf_shop.blend`, `tools/blender/surf_shop.py` (`--form photo|parapet|gable`; photo saved). D2's lot, 8.95 × 8.10 m, turned 15° to Beach Road; two storeys (3.3 + 2.7 m), (roof corrected 2026-10-03, see Next) a single-pitch tin roof high at the street, falling to the back, with a bracketed cornice at 7.38-7.90 m, three round louvred vents in the band below it and a pent roof over the upstairs windows, sash windows upstairs, maroon siding with yellow trim; a rust-red tin porch 2.5 m over the sidewalk on five posts, leaving a 2.0 m walk and 2.4 m parking to the kerb; display window, door (a real opening, flush at the sidewalk), boards, rack, A-frame as non-colliding dressing; 2,654 triangles. Renders `documentation/screenshots/beach-town-buildings-2026-10-02/surf_shop/pass2/` |
| Next | Her review. The yard behind is dug down 1.1–1.3 m at the back wall (the ground rises inland), not yet modelled. The photo's one-storey yellow wing is noted for D1 or D3. Its place: the beach town plan's pass 12 moves the lot 4.07 m inland to (−51.49, 422.51), same yaw, so the sidewalk and parking fit (the standing building is only 2.83 m from today's kerb); the model's street reference (centreline 9.9 m out) already matches that position Her "the surf shop is cute, looks like its missing its single story part" (2026-10-03): `photo_wing` in `export/variant_photo_wing`, the photo's one-storey yellow wing, 8.2 × 8.13 m, front flush with the block, walls 3.50 m falling to 2.82 m under a 1:12 shed, two big display windows, a poster box, a back service door, a bench; 17.15 m of frontage in all, so it needs more than D2's 8.95 m (D3, the skate shop, is next door); 3,190 triangles. The existing form is `photo`, its geometry and materials hash-identical; `apply_modifiers()`'s slot bug fixed. Check ok (5,844 triangles, the lead's run too; warning: 4.22 m off the origin, the wing). The agent's coplanar scan counts 47 pairs in the existing block, where its first build reported 0 (a different scanner; not checked) Her "for the surf shop, save a varient without the second wing and recolor it, it can become a different thing somewhere else maybe" (an Opus agent): `block` in `export/variant_block`, the two-storey block without the wing or the surf dressing (boards, stand, rack, sandwich board; to be added back per use), deep sea-green siding, cream trim, a faded red tin roof and porch, a dark green door, on its own materials; 2,234 triangles; `photo` and `photo_wing` hash-identical (Check ok, 8,078 triangles, the lead's run too). Coplanar by this scanner: photo 47, photo_wing 48, block 35, all the existing building's own Her "see the roof" (2026-10-03, an Opus agent): the photo looks along the long side, so the street face is an eave, not a gable; and the end wall is a right triangle, so the roof is single-pitch (the building's National Register nomination calls it a pent roof): a 1.0 m pent roof at 6.00 → 5.60 m, the vent band 6.00-7.38 m with 0.8 m vents, a 12-bracket cornice 7.38-7.90 m, the roof falling at 0.21 to 5.96 m at the back wall with a 0.55 m rake, shingled triangles at the ends; on all three variants; 247 of 316 parts unchanged; triangles photo 2,952, photo_wing 3,488, block 2,520; coplanar now 35 / 36 / 23 (the new parts add none). Check ok (the lead's run too). `documentation/reference/surf_shop/README.md` corrected |

### beach_cottage — the court's seven and the hillside's ~50 cottages (zone H)

| | |
|---|---|
| Stage | **model**, block-out (no cottage photo yet) |
| Holder | Christina: her review and a cottage photo |
| Model | `assets/source/props/beach_cottage.blend`, `tools/blender/beach_cottage.py`. Court cottage in `export`: 6 m to the lane × 8 m deep, gable to the lane, half-width shed porch, eave 3.15, ridge 4.92, 1,536 triangles. Hillside cottage in `authored/hillside_variant`: the same over a garage storey at the street, deck to the view, 2,480 triangles. Steps per the stair rule; 0 coplanar pairs; Check warns the origin is 1.14 m off the bounding box (the porch) |
| Next | Her photo (`documentation/reference/beach_cottage/`). Open: hillside lots are 8 × 7 m, not 8 × 6; court cottages 1 m apart (eaves 0.1 m apart); porch past the 2.5 m setback by 0.3 m; garage side on the hillside |

### cottage_kit — the town's everyday one-storey houses (South Shore family B, the court and the streets)

| | |
|---|---|
| Stage | **model**, block-out (2026-10-02, an agent, from eight of her photos in `documentation/reference/houses/`; built beside `beach_cottage`, which is untouched and still awaits her review) |
| Holder | Christina: her review |
| Model | `assets/source/props/cottage_kit.blend`, `tools/blender/cottage_kit.py`. One 6 × 8 m body, eight variants at the origin: `classic` in `export` (`classic_little_cottage.png`: 42° shingle roof, eave 2.55 m, sunburst, brick chimney, side door under a shed hood), 1,628 triangles; in `export/variant_<name>`: `bungalow` (`teal_trim_bungalow.png`), 1,904; `hip` (`blue_hip_roof_cottage.png`, ridge front to back), 1,512, and `hip_garage`, 536; `glass_gable` (`glass_gable_shingle_cottage.webp`), 1,344; `porch` (`pink_hammock_cottage.webp`, the hammock a non-colliding ribbon), 1,652; `log` (`log_cabin_cottage.webp`, compressed from about 10 m to the 6 m body), 2,560; `l_ranch` (`blue_l_shaped_ranch.png`, 8 m, the wing inset 0.5 m), 1,700. Round windows and plaques are applied discs, not holes. Check ok, one warning: 1.25 m off the origin (all the porches together). 0 coplanar pairs. Renders `documentation/screenshots/houses-2026-10-02/cottage_kit/`. Card `documentation/howto/model-the-cottage-kit.md` |
| Next | Her review. Answered 2026-10-02: "log cabin - go wide", "ranch wing flush", the hip roof side-gabled with its ridge along the front (done). Her rule for houses (2026-10-03): the either/or questions are variations, not decisions. Her "we want this AND that" (2026-10-03); built: `classic_gable`, the classic with its front door on the street gable between two tall windows under a hood, the side door moved back, 1,956 triangles (Check ok, 15,308 in all, the lead's run too; 0 coplanar). `classic` already had its gable to the street with the door on its long side (the lead's earlier note, "long side to the street", was wrong). Left for placement: mirrored versions for the driveway side, any of the plan's colours on any house. Placement: `log` needs a 13 m lot, `l_ranch` 11 m `classic_gable` recoloured on its own materials (her "on the variations lets change the colors", "can the doors be different colors too"): butter yellow, white trim, coral doors. Check ok after the recolour (the lead's run on all five, 2026-10-03). |

### carriage_house — a carriage house with rooms over, the hillside's garage-under house, and the beach house on stilts (PRP-HOUSE-029 to 031, 038)

| | |
|---|---|
| Stage | **model**, block-out (2026-10-03, an agent, from her photo `documentation/reference/houses/carriage_house_cottage.png`; her "build the carriage house and flared tower next") |
| Holder | Christina: her review |
| Model | `assets/source/props/carriage_house.blend`, `tools/blender/carriage_house.py`. A 5.2 × 10 m body read off the photo (lower storey 3.25 m, knee 1.35 m, 45°, ridge 7.48 m), 2.4 × 2.5 m carriage doors, a 4.86 × 1.0 m balcony on struts, a cross-gable; fits a 9 m lot with a 2.4 m drive. Three variants at the origin: `photo` in `export` (pale blue lap, grey-blue board-and-batten, white trim), 2,384 triangles; `plain` (sectional garage door, short balcony with French doors, no cross-gable; butter yellow, sage, slate trim, teal doors), 2,264; `hillside` (set into a 35 % slope, entry beside the carriage doors, a back door onto a deck; sand, olive, parchment, barn red), 2,260. Check ok (6,908 triangles, the lead's run too; warning: 0.71 m off the origin, the hillside deck); 0 coplanar pairs. Renders `documentation/screenshots/houses-2026-10-03/carriage_house/`. Card `documentation/howto/model-the-carriage-house.md` |
| Next | Her review. Her "the carriage houses are a good base for creating an elevated beach house on stilts" (2026-10-03): `stilts` in `export/variant_stilts`, the upper body raised on 26 eight-sided timber piles, floor at 2.9 m, the outer rows X-braced, the storey built full height (the knee wall over the void read as a hat on legs), decks 2.4 m across the sea-side gable and 1.5 m along the east with white rails, two nine-riser flights with a landing by the stair rule; weathered grey shingle, white trim, sky-blue door, driftwood decks, 4,352 triangles; the other three unchanged (Check ok, 11,260 triangles, the lead's run too; 0 coplanar) Then her "that staircase doesnt need that grey mass under it" (an Opus agent): each flight's treads had been one solid stepped block to the ground; `stilts` now uses `Kit.open_stair`, 6 cm treads on two cut stringers (non-colliding) and the walking ramp a 10 cm board hidden between them, the same 57.5 % grade, 0.75 m width and landing height; the landing was already a plate on posts. 4,728 triangles; 594 of 598 objects unchanged (Check ok, 11,636 triangles, the lead's run too; 0 coplanar) |

### flared_tower — the tiny house whose walls flare out (PRP-HOUSE-032 to 034)

| | |
|---|---|
| Stage | **model**, block-out (2026-10-03, an agent, from her photos `documentation/reference/houses/flared_tower_cottage.webp` and `flared_tower_cottage_side.png`; her "build the carriage house and flared tower next") |
| Holder | Christina: her review |
| Model | `assets/source/props/flared_tower.blend`, `tools/blender/flared_tower.py`. The tower is one tapered shell leaning inward going up, like a windmill (no tilted boxes), openings cut square to the leaning wall; eave 4.8 m, a metre-deep cornice with a 20° shingled pediment, hooded side windows, a flat-roofed wing, a back balcony. Three variants at the origin (ground → eave): `photo` in `export` (5°, 3.2 × 4.0 → 2.36 × 3.16 m, wing left; grey-blue, white trim), 1,600 triangles; `bell` (8°, 3.4 × 4.2 → 2.05 × 2.85 m, wing right, a hip cap; sage, cream, brick-red door), 1,552; `gentle` (3°, 3.0 × 3.8 → 2.50 × 3.30 m, a two-storey wing; butter yellow, teal door), 1,728. The player's capsule meets the wall's foot first. Check ok (4,880 triangles, the lead's run too); 0 coplanar pairs. Renders `documentation/screenshots/houses-2026-10-03/flared_tower/`. Card `documentation/howto/model-the-flared-tower.md` |
| Next | Her review. Her "lol the taper is upside down on these", "its supposed to resemble a wind mill" (2026-10-03): the lead's brief had the walls leaning out; inverted on all three the same day Then her "lets put a window, circular, on the front of the tower", "yellow needs its windows fixed", "window awning things are colliding", "upper hood runs into roof" (an Opus agent): a round window centred on each tower's front 3.64 m up (photo 0.80 m glass, bell 0.74, gentle 0.82, a 0.1 m white frame); `gentle`'s three-light window showed wall because its 3° tower wall stood in front of the glass, now cut through on all three, with a builder check that rays reach every pane; the side windows re-spaced (glass 1.4 → 1.2 m, smaller hoods), every hood 22-24 cm clear of what is above it; `bell`'s tower walls were inside out and are flipped. Triangles photo 2,432, bell 2,384, gentle 2,464; everything else hash-identical. Check ok (7,280 triangles, the lead's run too); 0 coplanar |

### storybook_cottage — the wide storybook cottage (PRP-HOUSE-035 to 037)

| | |
|---|---|
| Stage | **model**, block-out (2026-10-03, an agent, from her photo `documentation/reference/houses/black_pearl_cottage.webp`, her "black pearl cottage"; the real rental's name stays off the asset; her "build the black pearl cottage too") |
| Holder | Christina: her review |
| Model | `assets/source/props/storybook_cottage.blend`, `tools/blender/storybook_cottage.py`. Three variants at the origin, each on its own materials: `photo` in `export` (20.5 × 11.6 m eave to eave: a 13 × 7.5 m body under a hipped roof with round rolled eaves, an eyebrow bonnet over an arched cream door, a big bay and a lower corner bay, a 5.5 × 10 m gabled wing with a glazed porch side, an upper green gable, brick and stone chimneys, skylights; dark stain, dark-green trim), 4,208 triangles, needs a 24 × 20 m lot; `narrow` (no wing, 12.3 m, fits a 13 m lot; silvered cedar, cream trim, barn-red door), 3,328; `bungalow` (wing kept, one storey, a bay each side of the entry; honey stain, navy trim, sunflower door), 3,976. Check ok (11,512 triangles, the lead's run too); 0 coplanar pairs. Renders `documentation/screenshots/houses-2026-10-03/storybook_cottage/`. Card `documentation/howto/model-the-storybook-cottage.md` |
| Next | Her review. Placement: `photo` needs about two and a half of the plans' 9 m lots |

### victorian_cottage — the town's Victorian worker's cottages (showpieces on ordinary 9 m lots)

| | |
|---|---|
| Stage | **model**, block-out (2026-10-02, an agent, from her photos `documentation/reference/houses/victorian_blue_cottage.webp` and `purple_painted_lady.png`) |
| Holder | Christina: her review |
| Model | `assets/source/props/victorian_cottage.blend`, `tools/blender/victorian_cottage.py`. One 6 × 10.5 m two-storey shell, gable to the street at 48°, floor to eave 3.0 m; two variants at the origin: `blue` in `export`, floor 1.55 m up ten risers, balcony on brackets, sunburst, red bargeboards, a 2.17 × 1.25 m glazed corner porch, 4,420 triangles; `purple` in `export/variant_purple`, floor 0.60 m, full-width porch on turned posts, pediment hoods, spindle fan, 3,000 triangles. A plain back door and stoop on both (not in the photos). Check ok (the lead's run too); 0 coplanar pairs. Renders `documentation/screenshots/houses-2026-10-02/victorian_cottage/`. Card `documentation/howto/model-the-victorian-cottage.md` |
| Next | Her review. Her "we want this AND that" (2026-10-03); built in `export/variant_<name>`: `blue_b` (the corner porch wrapping under one L lean-to, which loses the little porch gable; a side door with a landing and flight; a brick chimney), 4,440 triangles; `purple_b` (38° over a 1.2 m knee wall, a 0.5 m sunburst, a railed porch, a brick chimney), 3,188; `blue` and `purple` fingerprints unchanged (Check ok, 15,048 triangles, the lead's run too; 0 coplanar) Recoloured on their own materials (her "on the variations lets change the colors", "can the doors be different colors too"): `blue_b` sage green, cream trim, deep red bargeboards, navy door; `purple_b` bright pink, teal trim, gold accents, gold door. Check ok after the recolour (the lead's run on all five, 2026-10-03). |

### streetcar_house — the beach house that was a streetcar

| | |
|---|---|
| Stage | **model**, block-out (2026-10-02, an agent, from her photo `documentation/reference/houses/streetcar_beach_house.webp`: "this was a streetcar turned into a beach house") |
| Holder | Christina: her review |
| Model | `assets/source/props/streetcar_house.blend`, `tools/blender/streetcar_house.py`. A 9.6 m single-truck car body 2.7 m wide (the door as scale) with a 2.9 m room added behind under one 5° hip roof, so 9.6 × 5.6 m; the car's window row and door on the long side, a tin-roofed porch on magenta posts, yellow and teal steps; suits a 9 m lot turned lengthwise along the street. Two variants at the origin: `photo` in `export`, 1,572 triangles; `tell` in `export/variant_tell`, the car's rounded end with three curved windows showing at the side, the addition stopping short under a roofed nook on one post, 2,256 triangles. Check ok, one warning: 0.88 m off the origin (the porch; the origin stays at the footprint's centre). 0 coplanar pairs. Renders `documentation/screenshots/houses-2026-10-02/streetcar_house/`. Card `documentation/howto/model-the-streetcar-house.md` |
| Next | Her review. Her "we want this AND that" (2026-10-03); built: `big`, a 14 m car with windows on its 1.2 m rhythm, one rounded end showing, a lean-to behind under its own tin roof (no post), 3,008 triangles; suits a lot turned lengthwise, the roof 15.3 m long; `photo` and `tell` hash-identical before and after (Check ok, 6,836 triangles, the lead's run too; 0 coplanar). The salmon strip and the rain chain are paint by default `big` recoloured on its own materials (her "on the variations lets change the colors", "can the doors be different colors too"): turquoise, cream trim, coral posts and rails, white fascia, navy skirt, yellow door. Check ok after the recolour (the lead's run on all five, 2026-10-03). Her "add the square-ended big streetcar too" (2026-10-03): `big_square`, the 14 m car and lean-to with both ends square and braced overhangs as her photo, coral-pink, white trim, teal posts and rails, cobalt door, on its own materials, 2,584 triangles; `photo`, `tell` and `big` hash-identical (Check ok, 9,420 triangles, the lead's run too; 0 coplanar). |

### stucco_row — the Capitola row, built as houses

| | |
|---|---|
| Stage | **model**, block-out (2026-10-02, an agent, from her photos `documentation/reference/houses/stucco_row_houses.webp` and `capitola_inner_lane.png`, and the README's notes on her two Capitola photos that did not reach disk; her "actually those are houses"). Her word on the first renders: "SO CUTE" |
| Holder | Christina: her review |
| Model | `assets/source/props/stucco_row.blend`, `tools/blender/stucco_row.py`. Four terrace units, each a variant at the origin, a 6 × 9 m shell (the front from the 1.4 × 2.1 m French doors; the depth unseen), storeys 2.9 m, party walls lapping 2 cm: `one_storey` (stepped parapet, tile run, corner chimney to 5.1 m, ornament and medallion over French doors, bay), 1,380 triangles; `one_storey_corner` (a square corner turret with a pyramid tile roof, a blue door up two red steps, a planter), 1,096; `two_storey` (timber balcony on brackets), 2,232; `three_storey` (arched recess, striped awning), 2,416. Wall tops cant 2 cm inward so lapped neighbours never share a plane; neighbours must still be staggered. A row of eight in nine colours in `authored/demo_row`. Check ok (the lead's run too); 0 coplanar pairs; each shell watertight. Renders `documentation/screenshots/houses-2026-10-02/stucco_row/`. Card `documentation/howto/model-the-stucco-row.md` |
| Next | Her review. Answered: "end units can get side windows" (2026-10-02): every unit has `<type>_end_west` and `<type>_end_east` with one 0.7 × 1.35 m sash per storey in two bays in its exposed side wall, nothing else mirrored, so twelve variants (23,884 triangles in all; Check ok, the lead's run too); the demo row ends in `one_storey_corner_end_west` and `three_storey_end_east`, whose windows the builder asserts are exposed. The arched recess is round (the lane render's close wide angle makes it look pointed). Her "we want this AND that" (2026-10-03); built: `one_storey_hipped` (a hipped red tile roof over the whole unit), 648 triangles, ends 832; `two_storey_iron` (the blue iron balcony), 2,424, ends 2,776; eighteen variants, both in the demo row (Check ok, 34,172 triangles, the lead's run too; 0 coplanar, shells watertight). Left for placement: mirrored units; other depths by the builder's `D` constant New types recoloured on their own materials (her "on the variations lets change the colors", "can the doors be different colors too"): `one_storey_hipped` turquoise with coral doors, `two_storey_iron` sunflower with cobalt doors, the balcony still blue. Check ok after the recolour (the lead's run on all five, 2026-10-03). Her word (2026-10-03): "i really like the built in planters at the bottom of some of the stucco ones" (the corner, two-storey and hipped units carry them, `planter()` in the builder). |

### lowrise_condos — the colony's and the hillside's old condo blocks (South Shore plan, the colony; beach town plan, zone H)

| | |
|---|---|
| Stage | **model**, block-out (2026-10-02, an agent, from her aerial `documentation/reference/houses/beach_lot_aerial.webp`: "one of the rows should be like that chunky repeating lowrises in the top left of this pic, others should be like the ones in the forground") |
| Holder | Christina: her review |
| Model | `assets/source/props/lowrise_condos.blend`, `tools/blender/lowrise_condos.py`. Two variants at the origin: `bluff_block` (the colony's sea-side row, three of them), 23 × 11 m, three storeys at 2.75 m, a 0.65 m white roof slab, 1.8 m recessed balconies behind 1.1 m solid fronts to the sea, two 11.5 m units joined by a fin, a garage and entry per unit to the street; 1,972 triangles. `street_block` (the colony's land-side block and the hillside's two), 23 × 11 m (`--street 26x11`, `26x9` for the hillside), two storeys, four 5.75 m units with a teal door and paired windows each, tuck-under carports at the back; 1,480 triangles. Check ok (the lead's run too); 0 coplanar pairs. Demo of the row in `authored/demo`. Renders `documentation/screenshots/houses-2026-10-02/lowrise_condos/`. Card `documentation/howto/model-the-lowrise-condos.md` |
| Next | Her review. Her rule (2026-10-03): "we want this AND that"; built: `bluff_block_b` in `export/variant_bluff_block_b`, three 7.67 m units, white balcony fronts, garage doors in the wall colour, no roof boxes, 2,656 triangles; the demo's middle block (Check ok, 6,108 triangles, the lead's run too; 0 coplanar). Placement: the street block's parking (a back drive or garages to the street) and the South Shore plan's colony unit count (20 in 4 blocks; two units per bluff block as built) are settled when the blocks are sited `bluff_block_b` recoloured on its own materials (her "on the variations lets change the colors", "can the doors be different colors too"): sand stucco and garage doors, white slab and fronts, terracotta entry doors. Check ok after the recolour (the lead's run on all five, 2026-10-03). |

## Other buildings

Buildings modelled ahead of a site, through the same steps as a prop.

### waterfront_restaurant — a restaurant over the water, for any use (ID when catalogued)

| | |
|---|---|
| Stage | **model** (2026-10-02): her photo of a restaurant on the water, "it can be for anything", "we can always build another pier in town"; first pass by an agent from the lead's reading of the photo, which is not on disk. Her word on the renders: "the restaurant is very cute" |
| Holder | Christina: review the first pass (`tools/blender/waterfront_restaurant.py`), reshape, then "handed back". Renders `documentation/screenshots/handbacks/waterfront_restaurant-model-2026-10-02/` (`figure` beside a 1.7 m figure, `dusk` lit) |
| Model | `assets/source/props/waterfront_restaurant.blend`. `export`: 65 parts, 7,747 triangles, 8 stand-in materials `waterfront_<surface>`. A 26 by 14 m deck 2 m over the water (z = 0, origin mid-deck) on 28 X-braced piles going 2.5 m into it; a two-storey dark timber block 18 by 8.5 m, eave 6.4 m, ridge 11.4 m (48°); on the front a cross-gable with an arched window; a lantern with a weathervane on the ridge (14.6 m); a pyramid-roofed tower at the front right (13.8 m); a catwalk stair up the roof to the lantern; a glass dining room on a 0.9 m wall round the front and both ends; double doors and a 1 m gangway stub on +X, flush with the deck; a blank banner by the door. Front −Y. Piles are cylinders, the rest `kyt_unwrap = facets`. `reference`: `ground_line`, outlines, the 1.7 m figure. Check ok (the lead's run too); 0 coplanar pairs (the agent's scan) |
| Reference | None of hers on disk; `documentation/reference/waterfront_restaurant/` waits for the photo |
| Paint | Not started. Dark stain, shingles, cream trim, warm glass |
| Game | Not sent; no scene, no site |
| Last hand-back | None |
| Next | Her review: a railing round the deck (its edge is open, 2 m over the water; only the stub has a rail start); how the roof stair's foot is reached (it starts on the roof); the gangway (a stub, so the origin stays at the deck's middle; the pier it joins comes with a site). Card: `documentation/howto/model-the-waterfront-restaurant.md` |
