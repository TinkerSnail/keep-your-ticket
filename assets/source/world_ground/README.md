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

## Editing in Blender

Height-grid Stage 3, 2026-10-14. The Keep Your Ticket panel's **Ground** box, in the 3D view's sidebar under the Keep Your Ticket tab (`tools/blender/extensions/kyt_tools/ground.py`; each button's tooltip says what it does).

- **Load tiles**, by name (`x0_z0, x1_z0`), **Under cursor** or **Under selection**, up to 25. Each tile becomes an object in the open file's `Ground tiles` collection. It has one vertex per node with ground, at its world place (Blender x, y = Godot x, −z; z the stored height exactly), and no face where there is no ground. It wears its colour PNG, each node on its own pixel. Loading a tile again reloads it, unless it has unsaved sculpting.
- **Sculpt** with any brush. On a tile the panel keeps Lock X and Y on, and dynamic topology and symmetry off. A brush stops at a tile's edge.
- **Save tiles**, with a short **Name** and a line of **Why**, records one edit through `ground_grid_edit.apply_values`, logged in `edits.json` like G1–G7 and undoable.
  - It writes only the nodes moved more than 1 mm. An edge node goes into every tile that holds it.
  - It writes nothing if a vertex moved sideways, vertices were added or removed, a tile was moved or given modifiers, an edge was sculpted two ways, or a node's file changed since it was loaded.
- **Undo last ground edit** takes back the newest edit, if Save tiles or a Photoshop save made it.
- **Send ground to game** runs `tools/ground_send.py` in the background, about eight minutes: the changed tiles' build, the follow step, the import, the mount and its check, `world_terrain_delta`, then `gen_props` and `gen_crowd`.

**How many tiles.** Measured 2026-10-14 on her M1 Pro (16 GB), Blender 5.1.1:

| Tiles loaded | Vertices | Load | Frame, all in view | A stroke and its frame |
|---|---|---|---|---|
| 1 | 0.25 M | 0.2 s | 9 ms | 15 ms |
| 9 | 2.2 M | 1.8 s | 10 ms | 16 ms |
| 25 | 4.6 M | 3.9 s | 11 ms | 17 ms |

- **Speed.** A brush works on the active tile alone, at most 251,001 vertices, so all 25 sculpted at 60 frames a second.
- **Memory.** Blender held 0.5 GB with one tile and 2.2 GB with 25.
- **Files.** A saved .blend takes about 11 MB a tile. Saving every node of two tiles took 6.5 s.

**Proofs** (2026-10-14):
- **No-op.** All 50 tiles were loaded and saved unchanged: no edit, all 211 files bit-exact.
- **Refusals,** on a copy: each refusal case wrote nothing.
- **Edges.** Edges reached loaded and unloaded neighbours and stayed bit-equal.
- **Undo.** Undo restored every file's bytes.
- **The test bump.** A 20 m hill, 3 m high, at (2500, 500) on range middle.
  - Saved from the panel as G8 (69 nodes) and sent with the panel's button in 6:48. x2_z0 alone was rebuilt.
  - `delta_y` read 3.000 m at the centre and 0 from 10 m out. The generator ran, and its scenes matched HEAD, since nothing generated stands there.
  - `ground_grid_edit.py --undo` and a second Send put everything back. Every ground file and tile GLB is back to its bytes (x2_z0 rebuilt bit-identical), and the generated scenes match HEAD by content.
  - Send's follow step came after this run. It was checked against a stand-in.

## Painting the ground in Photoshop

Height-grid Stage 3, 2026-10-14. She paints a region's height and colour in Photoshop, and each save becomes one recorded, undoable grid edit. The tools: `tools/ground_paint.py` and the save hook (`tools/photoshop/on_save.jsx`, which hands a ground painting to `ground_save.jsx`).

**Open.** `python3 tools/ground_paint.py open --tiles x0_z-1,x1_z-1` (the tiles' whole squares) or `--area X0,Z0,X1,Z1` (world metres), `--name beach_cove` (short snake_case; a default is made from the region), `--show` to open it in Photoshop. It writes `paint/<name>/<name>.psd` here. `paint/` is git-ignored (its own `.gitignore`), Godot ignores all of `assets/source/`, and Dropbox syncs it. An existing painting is never replaced; `--replace` moves it to `paint/<name>/replaced/`.

**The document.** RGB, 16 bits, sRGB, one pixel per 2 m node, north up, as the tiles are. Two groups:
- `colour`, on top: the region's colour from `colour/`, each 8-bit value held exactly.
- `height`: the heights as grey, black at the window's foot and white at its top. Photoshop's 16-bit mode has 32,769 levels. The window is `--window land`, −20..480 m, by default: 1.53 cm a level. `seabed` is −640..0 m (1.95 cm). `fit` is the region's own lowest and highest ground with a margin (finer). `LO,HI` gives one directly. A preset is widened to hold all the region's ground; a given window that does not is refused. The height layer's name carries the window and the step.
- Nodes with no ground are transparent in both. Both base layers have their transparency locked, so a stroke on them can't add ground by accident. New ground is painted on a layer of her own.
- Paint on any layers, with adjustment layers or masks, inside each group. What counts is each group's look on its own, whatever her view of it. A top-level layer outside the two groups is ignored. Hiding the colour group to paint height changes nothing in the export.

**Save.** Her ⌘S. The hook writes each group alone, as Photoshop composites it, to `paint/<name>/exports/`. Then `ground_paint.py save` runs in the background and records the edit (log: `~/Library/Logs/Keep Your Ticket/ground_paint.log`; the result also goes in `<name>.json`'s `last_save`).
- **Height.** A node changes only where its level moved by more than one, about 3 cm on land. The change is applied in metres to the height it had, so every untouched node keeps its exact bytes, and a node painted back to where it was gets its old value exactly. A transparent node she paints opaque becomes new ground. A node with ground that she erases keeps its ground: ground is never removed from Photoshop.
- **Colour.** Only nodes whose 8-bit colour changed are written, and only on ground. New ground she didn't colour takes its neighbours' colour.
- **The edit.** One per save, `paint_<name>_<n>`, through `ground_grid_edit.apply_values`. Shared tile edges are written in every tile. `python3 tools/ground_grid_edit.py --undo` takes it back bit for bit. Undoing one only in the grid leaves the painting showing it: open the region again under a new name before painting those nodes again. If the grid changed under nodes she painted, the save refuses and writes nothing.
- The game's tiles are not rebuilt: the Blender panel's **Send ground to game** does that.
- With the hook off, `python3 tools/ground_paint.py save paint/<name>/<name>.psd` asks Photoshop for the export (`tools/photoshop/ground_export.jsx`), which starts Photoshop.

**Precision.** A node she touches is written within half a level of what she painted: 0.76 cm in the land window. A faint brush edge under 1.5 levels (2.3 cm) is left alone.

**Proofs.** `python3 tools/ground_paint.py prove --scratch <dir>` works on a copy of this folder with Photoshop simulated. It shows:
- open and save untouched is bit-exact, under two Photoshop rounding conventions;
- a 2 m, 30 m brush stroke and a colour stroke change exactly their nodes, and their undos are bit-exact;
- both kinds of change go in one edit, and painting back is bit-exact;
- painting into the transparency works as above, and a save is refused after an undo behind its back.

`node tools/photoshop/hook_dry_run.js --compare <old hook> tools/photoshop/on_save.jsx <saved path>` runs the hook against a fake Photoshop and shows the two hooks act the same.
