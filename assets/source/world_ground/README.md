# The world's ground as one height grid

Stage 1, Bake, of `documentation/terrain-height-grid-plan-2026-10-12.md`, baked 2026-10-12 from the ground frozen at `1926e71`. Nothing in the game reads this folder yet; `.gdignore` keeps Godot from importing it.

- `grid.json`: the spec. Nodes every 2 m; 1 km tiles of 501 × 501 sharing their edges; tiles x −2..3, z −3..7; north up.
- `height/x{tx}_z{tz}.exr`: the master's ground, one float32 channel `Y`, ZIP. Each node holds the height of the highest face over it, exactly as `WorldTerrainSource._top` reads it: faces steeper than about 87° are skipped, of either winding. NaN means no ground.
- `baseline/`: the same, from the frozen copy (`world_terrain_baseline.res`). Wherever the master has not changed, the two are bit-identical.
- `holes.json`: the open edges of the ground the generator still holds (the road corridor, the tunnel lids, NT-2's earth and climb cuts), chained with every corner exact; also the master's open edges that lie on held CSG solids. The master still has ground inside these outlines, so Stage 2 must cut there.
- `colour/`: from the colour bake, `tools/ground_colour_bake.py`.

**Re-make** (about 20 s):

```
Godot --headless --path . --script res://tools/_ground_faces_dump.gd -- --out=<abs dir>
python3 tools/ground_bake.py bake --faces <abs dir>
```

The bake is deterministic: the same faces give the same bytes. The proofs are the other commands in `tools/ground_bake.py`'s docstring. Their results are in `documentation/screenshots/height-grid-stage1-2026-10-12/README.md`, under "Heights".
