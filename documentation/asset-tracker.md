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
| Stage | **model**: handed to Christina 2026-09-25 (card `howto/model-the-benches.md`); the hand-built bench is in `export`, reference locked, seat markers in place, Check clear; not sent |
| Holder | Christina: her model pass |
| Model | `assets/source/props/perforated_metal_bench.blend` |
| Game | Not placed anywhere. `scenes/world/park_furniture/perforated_metal_bench.tscn` is still hand-built meshes with the `perforated_metal.gdshader`, no seat markers |
| Starting frames | `documentation/screenshots/handbacks/perforated_metal_bench-start-2026-09-25_0142/` |
| Next | On "handed back": model hand-back (skill): tests, then switch its Godot scene to wrap `assets/props/perforated_metal_bench.glb` with `seat_l`/`seat_r` markers from the blend, then texture set-up. **Decide before its canvas:** how the diamond perforations survive (painted with alpha cut-out, real holes, or the shader); her panels are flat for now. |

### backless_timber_bench — PRP-PARK-019

| | |
|---|---|
| Stage | **model**: handed to Christina 2026-09-25 (card `howto/model-the-benches.md`); the hand-built bench is in `export`, reference locked, seat markers in place, Check clear; not sent |
| Holder | Christina: her model pass |
| Model | `assets/source/props/backless_timber_bench.blend` |
| Game | Not placed anywhere. `scenes/world/park_furniture/backless_timber_bench.tscn` is still hand-built meshes, no seat markers |
| Starting frames | `documentation/screenshots/handbacks/backless_timber_bench-start-2026-09-25_0142/` |
| Next | On "handed back": model hand-back (skill): tests, then switch its Godot scene to wrap `assets/props/backless_timber_bench.glb` with `seat_l`/`seat_r` markers from the blend, then texture set-up (timber grain along x, as the plaza bench). Sat on from either side. |
