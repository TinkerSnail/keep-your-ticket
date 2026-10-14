# The world's ground as one height grid

Stage 1, Bake, of `documentation/terrain-height-grid-plan-2026-10-12.md`, baked 2026-10-12 from the ground frozen at `1926e71`. Godot never imports this folder: `assets/source/.gdignore` keeps it out of all the Blender sources, and `.gdignore` here says so again. What the game uses is derived from it: `tools/ground_mount.gd` makes each tile's colour texture.

- `grid.json`: the spec. Nodes every 2 m; 1 km tiles of 501 × 501 sharing their edges; tiles x −2..3, z −3..7; north up.
- `height/x{tx}_z{tz}.exr`: the master's ground, one float32 channel `Y`, ZIP. Each node holds the height of the highest face over it, exactly as `WorldTerrainSource._top` reads it: faces steeper than about 87° are skipped, of either winding. NaN means no ground.
- `baseline/`: the same, from the frozen copy (`world_terrain_baseline.res`). Wherever the master has not changed, the two are bit-identical.
- `holes.json`: the open edges of the ground the generator still holds (the road corridor, the tunnel lids, NT-2's earth and climb cuts), chained with every corner exact; also the master's open edges that lie on held CSG solids. The master still has ground inside these outlines, so Stage 2 must cut there.
- `colour/x{tx}_z{tz}.png`: the land's colour, 8-bit sRGB RGBA, alpha 0 where there is no ground. Each node holds the albedo the game showed on 2026-10-12, before lighting: the vertex colours with the palette's tint baked in, and the landform materials' own albedo (re-baked 2026-10-13, Christina's choice). Christina paints these; what she paints is what the game shows, since `assets/shaders/ground_grid.gdshader` applies no tint. Made by `tools/ground_colour_bake.py`. `tools/ground_mount.gd` turns each into its tile's texture, `assets/world_ground/colour/x{tx}_z{tz}.res`: premultiplied, mipmapped, lossless, rewritten only when the PNG changed. Run it after a colour edit.

**Re-make** (about 20 s):

```
Godot --headless --path . --script res://tools/_ground_faces_dump.gd -- --out=<abs dir>
python3 tools/ground_bake.py bake --faces <abs dir>
```

The bake is deterministic: the same faces give the same bytes. The proofs are the other commands in `tools/ground_bake.py`'s docstring. Their results are in `documentation/screenshots/height-grid-stage1-2026-10-12/README.md`, under "Heights".
