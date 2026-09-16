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
| `gen_props.gd` | The ground textures and eighteen generated world sources beneath the stable wrappers: established props/places plus groundworks, circulation, routes, program and landscape. It does not write `west_far` or `terraces_far`; the persistent world uses the real places. **The order it writes them in is load-bearing** — each scene gets a seam seed five on from the last, so the two retired seed slots remain until that system is replaced. Run `coplanar_test.py` after touching the order. |
| `export_world_source.py` / `.sh` | A mounted world GLB from its Blender master, `assets/source/<name>.blend` to `assets/<name>.glb`; the range by default, the city when named. Meshes exported under its own name with the `-col` hint, boulders baked into one mesh per 250m cell with a surface per material, collision derived from the visible meshes. Runs through Blender, never saves the master, and refuses a master that still holds a `-colonly` object. |
| `strip_collision_twins.py` | One-time removal of authored `_collision-colonly` twin objects from a Blender master, marking twinless objects `kyt_collision=none` and moving boulder materials onto the object. Dry run by default; `-- --save` applies. Run through Blender. |
| `gen_crowd.gd` | The plaza, boardwalk and terraces crowds in one run. Each output carries an `area_id`, because all three coexist in `park_world.tscn`. Bodies and placement only; behaviour lives in `scenes/npc/guest.gd` and is hand-written. |

## Tests

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
| `boardwalk_edge_test.gd` | Does the pier walk both ways, and do the water, jetty, bluff, shop backs, yard and coaster fence all stop the player? | Split from `walk_test.gd` the same day, minus its pre-expansion strip-end probes. |
| `wheel_test.gd` | Does R1 retain its fixed rim crown, true hub-to-rim structural spokes and light tubes, twenty roofed gondolas, open-hour indexed motion, upright cabins and after-close stop? | Focused acceptance for the editor-owned wheel form and its visual-only motion script. |
| `path_ground_test.gd` | Does every programmed access path, road and street stand on the ground it was laid over, neither floating nor buried? | Prints per-path float and bury counts. |
| `climb_test.gd` | Is every guest standing on the floor of the area they are in? | Reads the floor off the crowd's own graph. |
| `ground_contact_test.gd` | Does every moving guest have real collision immediately underfoot? | |
| `transit_test.gd` | Do the Kiddieland railway and Grand Circuit form usable loops, move with riders while open, and park empty after close? | Run at `--fixed-fps 60`; also guards the sampled grades and the five station-to-route alignments. |
| `kiddieland_layout_test.gd` | Does the first published editor-owned district source still reproduce the accepted Route D, R5–R7, R14, P4, support, S3, Q4 and NT-2 records? | `extends SceneTree`; run with `--script`. It compile-checks the generator’s Route D consumer and moves both one instantiated R14 control and the whole ride in memory, proving the reader follows editor-owned transforms; it rewrites nothing. |
| `park_section_layouts_test.gd` | Do the other eight park sections preserve their accepted horizontal records as ordinary editor-owned Godot scenes and feed every plan consumer in the established order? | `extends SceneTree`; run with `--script`. It checks lossless migration from ParkPlan and moves an R10 queue control and its parent in memory to prove live editor ownership; it rewrites nothing. |
| `park_vertical_controls_test.gd` | Does the published editor-owned vertical handoff preserve all fifty map levels, four editable drainage rims, the localized P1 constraint, NT-2 output separation and every held-fixed relationship while responding to editor transforms? | `extends SceneTree`; run with `--script`. It generates no terrain, rewrites nothing and checks the generated terrain ownership. |
| `terrain_handoff_capture.gd` | Do D3-D6 read as localized terrain folds in the real park while the Terraced Fountain remains compositionally separate? | Metal/Forward+ proof of the 2026-09-09 map-to-Godot terrain publication; writes five frames under `documentation/screenshots/terrain-handoff-2026-09-09/`. |
| `boardwalk_scenery_capture.gd` | Are I2, I3 and B1-B4 distinct player-readable places while Q3 remains open? | Eight Metal/Forward+ frames under `documentation/screenshots/boardwalk-fidelity-2026-09-09/`. |
| `boardwalk_operations_capture.gd` | Do R1, R2, P2 and the pier landing read as operated places by day and recently vacated places after close? | Eight Metal/Forward+ frames under `documentation/screenshots/boardwalk-operations-2026-09-09/`. |
| `boardwalk_water_edges_capture.gd` | Do D2, its culvert, rain pond, crossings and controlled outfall read as one planted drainage landscape while protected water remains open? | Eight Metal/Forward+ frames under `documentation/screenshots/boardwalk-water-edges-2026-09-09/`. |
| `boardwalk_density_capture.gd` | Do Boardwalk planting, period fixtures and pier safety hardware add middle-scale density without narrowing Q3 or public circulation? | Eight Metal/Forward+ frames under `documentation/screenshots/boardwalk-density-2026-09-09/`. |
| `boardwalk_finish_capture.gd` | Do restrained materials, merchandise, caused wear and one public practical finish the Boardwalk without cluttering routes or protected views? | Eight Metal/Forward+ frames under `documentation/screenshots/boardwalk-finish-2026-09-09/`. |
| `pier_head_capture.gd` | Does the editor-owned pavilion T-head separate the fishing work from a complete public loop while preserving its support, west-arch reveal and sunset composition? | Nine Metal/Forward+ frames under `documentation/screenshots/pier-head-2026-09-10/`. |
| `pier_pavilion_capture.gd` | Does the editor-owned Pier House read as finished coastal architecture on every public face while preserving circulation, the west-arch reveal, sunset silhouette and after-close light handoff? | Nine Metal/Forward+ frames under `documentation/screenshots/pier-pavilion-2026-09-10/`. |
| `boardwalk_architecture_capture.gd` | Do I2, I3 and B1-B4 read as one varied, editor-owned streetwall rather than six generic shells while Q3 and the lighting schedule remain intact? | Ten Metal/Forward+ frames under `documentation/screenshots/boardwalk-architecture-2026-09-10/`. |
| `boardwalk_wheel_capture.gd` | Does R1 read from the supplied Santa Monica day and night references while its platform, west-arch reveal, fixed rim crown and light schedule remain intact? | Twelve Metal/Forward+ frames under `documentation/screenshots/boardwalk-wheel-2026-09-10/`. |
| `boardwalk_coaster_capture.gd` | Does R2 read as a complete wooden coaster from its public station, route B, pier and night standpoints while Q3 and the west-arch reveal remain intact? | Twelve Metal/Forward+ frames under `documentation/screenshots/boardwalk-coaster-2026-09-10/`. |
| `boardwalk_coaster_test.gd` | Does R2 preserve its map parcel and operating address while the editor-owned circuit derives full track, timber bents and lift catwalk and fully retires the single-line greybox? | Focused scene-tree acceptance; runs through `tools/run.tscn`. |
| `lighthouse_regrade_test.gd` | Does the approved editor-owned P1 curve drive a localized cut-or-fill terrain ribbon and densely sampled paving while preserving its endpoints, 1:8 cap and shoreline gap? | `extends SceneTree`; run with `--script`. It rewrites nothing and proves cross-section edits are read live. |
| `photo_exposure_test.gd` | Does a shutter press preserve an immutable, JSON-safe record of park time, camera pose, flash and objective scene facts without a score or composition judgment? | `extends SceneTree`; run with `--script`. It writes no photographs. |
| `kiddieland_story_test.gd` | Does Three Jumps and a Birthday keep its five approved beats, three returning cast, factual developed evidence, after-close residue and pavilion keepsake without scoring a photograph? | `extends SceneTree`; run with `--script`. It writes no photographs and changes no story state. |
| `footprint_test.gd` | Does the expanded developed park remain one connected hierarchy inside genuinely larger world geography? | Guards the 434x450m program envelope, 2km-plus land reserve, nearly 4km western ocean reserve, every primary handoff, the four crossing records and the retirement of the old NNW dead end. |
| `footprint_walk_test.gd` | Can the real Player traverse every rebuilt public path in both directions? | Current A–F release gate: center and both operating edges of all generated segments, including shared junction floors and expanded-datum handoffs. |
| `section_test.gd` | Is the park one continuous standing world, with both plaza gates walkable in both directions and no load, teleport, far stand-in or transition gate? | Also verifies all canonical scenes and all three tagged crowds are present. |
| `day_test.gd` | Does each section's crowd have a day — the curves, the admitting and the sending home? | `--headless --fixed-fps 60`, about ninety seconds. |
| `night_test.gd` | Do the lights come on and go off again? | `park_lights.gd` fails by succeeding: miss the emissive materials and the lights still light. |
| `menu_test.gd` | Does the pause menu respond to real input — tabs, cursor wrap, backing out of quit, and is the park actually stopped? | A still shows a screen draws, not that it works. |
| `inpool_test.gd` | Is anybody standing in the fountain? | Samples over twelve seconds, not one instant — the single-instant version reported three offenders one run and none the next. Guards a 40cm margin: rim sitters at 8.66 against water ending at 8.26. |
| `clearance_test.gd` | Is anything standing in a walkway, or in another prop? | `extends SceneTree`. Hand-placed props have no equivalent of `open_spots`' rejection sampling. |
| `perf_test.gd` | What does the crowd cost per frame, hour by hour? | Measurement, not an assertion. Re-measure before building any tiering scheme. |
| `park_height_audit.gd` | What vertical datum, route-control levels, maximum grades, site floors and drainage-ground heights does the accepted build currently assign to the section atlas? | Read-only planning audit; `extends SceneTree`, runs with `--script`, writes no scene and is not a construction source. |
| `coplanar_test.py` | Which surfaces will z-fight? | Seconds, no Godot needed. Reads CSG *and* meshes, so it covers guests as well as the world. |
| `seat_test.py` | Is every seated guest sitting on something? | Wheelchair users excluded — they bring their own. |
| `flow_probe.py` | Which way did the water actually move? | Analyses frames from `flow_probe.gd`. A still cannot show a direction and will look correct either way. |

## Capture tools

These pose a camera and save PNGs. All need a real renderer.

| tool | shoots |
|---|---|
| `capture.gd` | The plaza from a list of vantages, including passes across the day for both the light and the crowd. Ships `capture.tscn`. |
| `west_capture.gd` | The plaza-to-boardwalk walk in order, crossing the seam mid-run. Ships `west_capture.tscn`. |
| `menu_capture.gd` | The HUD and all four pause-menu tabs, stacking consecutive frames of a tab change and a cursor move into strips — a still cannot show that either animates. |
| `night_capture.gd` | The park through the evening, measuring what the lights cost while it does it. |
| `footprint_capture.gd` | Ten real-world aerials covering the complete A–F hierarchy, arrival, Headland, west/east anchors, Plaza branches and the coastal, family and northern ride circuits. |

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
| `_forest_perf_probe.gd` | What the range forest costs to draw at several densities. |
| `range_perf_probe.gd` | What the mounted range costs: wrapper and `main.tscn` load times, node counts and collision triangles under the mount, ray and sphere query grids over the rock field, a walked CharacterBody3D on the beach, and rendered frame times from three standpoints with the range hidden and visible. Writes `user://range_perf_<driver>.txt`; run with `--disable-vsync` for the render block. |
| `_range_import_dump.gd` | What Godot made of the exported range GLB: every child with its class, what sits under it, and each concave shape's triangle count. |
| `_range_handoff_probe.gd` | Did a boulder edited in Blender reach Godot as mesh, material and collision? Takes a JSON of the boulder's bounds before and after the edit. |
| `_hole_probe.gd` | Rain rays over the whole east and dump what they hit. |
| `_ledge_probe.gd` | The walkable profile where the climb meets the head landing. |
| `_lot_probe.gd` | Does the coast highway show from the parking lots? |
| `_prom_probe.gd` | Rain rays over the promontory walk and dump what they hit. |
| `_lighthouse_walk_probe.gd` | The emitted P1 contour climb from the real Player at five stations, its shore side and one oblique overview; pairs with filtered `footprint_walk_test` traversal and `path_ground_test` contact. |
| `_range_probe.gd` | The crescent range from far enough away to see its shape. |
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
| `_coastal_fast_probe.gd` | The one-hour coastal breadth pass from eight inspection cameras: beach town, north town, watersheds, harbour, park fishing deck, scenic railway and city. |

Godot writes a `.uid` beside every script it imports. Those are tracked — but
delete the throwaway wrapper scene and its `.uid` when you are done.
