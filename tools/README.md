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
/Applications/Godot.app/Contents/MacOS/Godot --headless --fixed-fps 60 --path . tools/run.tscn -- walk_test
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

See `.claude/skills/run-the-park/SKILL.md` for the containerised route, which is
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
| `gen_props.gd` | The ground textures and thirteen generated world sources beneath the stable wrappers: props, skyline, west shell, real boardwalk, cascades, entrance, thresholds, paving, frontage, fountain, sky ride and the park-transit layer. It does not write `west_far` or `terraces_far`; the persistent world uses the real places. **The order it writes them in is load-bearing** — each scene gets a seam seed five on from the last, so the two retired seed slots remain until that system is replaced. Run `coplanar_test.py` after touching the order. |
| `gen_crowd.gd` | The plaza, boardwalk and terraces crowds in one run. Each output carries an `area_id`, because all three coexist in `park_world.tscn`. Bodies and placement only; behaviour lives in `scenes/npc/guest.gd` and is hand-written. |

## Tests

These assert. They print a verdict and are the things worth running before a
merge.

| tool | asks | notes |
|---|---|---|
| `walk_test.gd` | Can the player actually walk every route, in both directions, and does every open edge hold? | Hundreds of directed legs. The main defence against coplanar snags, missing step-up and holes behind platforms — none of which a screenshot shows. |
| `transit_test.gd` | Do the Kiddieland railway and Grand Circuit form usable loops, move with riders while open, and park empty after close? | Run at `--fixed-fps 60`; also guards the sampled grades and the five station-to-route alignments. |
| `section_test.gd` | Is the park one continuous standing world, with both plaza gates walkable in both directions and no load, teleport, far stand-in or transition gate? | Also verifies all canonical scenes and all three tagged crowds are present. |
| `day_test.gd` | Does each section's crowd have a day — the curves, the admitting and the sending home? | `--headless --fixed-fps 60`, about ninety seconds. |
| `night_test.gd` | Do the lights come on and go off again? | `park_lights.gd` fails by succeeding: miss the emissive materials and the lights still light. |
| `menu_test.gd` | Does the pause menu respond to real input — tabs, cursor wrap, backing out of quit, and is the park actually stopped? | A still shows a screen draws, not that it works. |
| `inpool_test.gd` | Is anybody standing in the fountain? | Samples over twelve seconds, not one instant — the single-instant version reported three offenders one run and none the next. Guards a 40cm margin: rim sitters at 8.66 against water ending at 8.26. |
| `clearance_test.gd` | Is anything standing in a walkway, or in another prop? | `extends SceneTree`. Hand-placed props have no equivalent of `open_spots`' rejection sampling. |
| `perf_test.gd` | What does the crowd cost per frame, hour by hour? | Measurement, not an assertion. Re-measure before building any tiering scheme. |
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
| `_rim_probe.gd` | Does the east rim stand over the roofline, and does it open up as you back away? |

Godot writes a `.uid` beside every script it imports. Those are tracked — but
delete the throwaway wrapper scene and its `.uid` when you are done.
