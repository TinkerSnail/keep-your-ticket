# Keep Your Ticket

A first-person photography game set at a local amusement park in the late 1990s. The player works there as a photographer, taking pictures of guests by day. After the park closes, the player is still inside.

This file is the agent instruction set for both Codex and Claude Code. `CLAUDE.md` imports it with a single `@AGENTS.md` line and holds nothing else, so there is one copy and nothing to drift; **edit this file only**. It was cut from 31,000 words to a current-state document on 2026-09-05. The incidents behind every rule below are preserved verbatim in `documentation/instructions-archive-2026-09-05.md` and in the journals; read them when a rule's reason matters, not by default.

## Session preflight

Mandatory, and proportional to the task. The procedure is `.agents/skills/park-preflight/SKILL.md`; Claude Code reaches it through `.claude/skills/park-preflight/SKILL.md` and the session-start hook `.claude/hooks/preflight.sh`, which prints the document inventory.

**Tier 1, every session, and again after any compaction, resume or clear:** this file; the newest file in `documentation/journals/`; `git status` and the live-session check under "Running things". Say in the first reply that it was done.

**Tier 2, before touching design, tone, the night, the rebuild atlas, a protected anchor, or any decision you only remember from chat:** the full preflight in the skill: the continuity packet, the task-relevant maps with their embedded plan data, and a search of the journals, `design-archive.md` and the instructions archive for the task's nouns and for `supersed`, `retired`, `rejected`, `protected`, `must not`, reading every match in full.

Do not rely on remembered chat context in place of the documents. When two current-looking sources conflict, stop before editing the disputed area, quote both, and ask Christina which is authoritative.

## Documents

`documentation/` is not tracked by git. It is working material and stays local, synced by Dropbox.

- `documentation/design.md`, `night.md` and `technical.md` govern the game, the night and the platform.
- `documentation/park-rebuild-masterplan.md` and the interactive maps govern the approved rebuild and its order. Maps live in `documentation/maps/` with synchronized copies in `planning/`; byte-compare a pair before reading it, and update both when a plan changes.
- `district-story-arcs.md`, `seasonal-missions-and-decor.md` and `feature-assignments-and-park-legends.md` govern their layers. The newest `current-build-<date>.md` is the visual baseline.
- `design-archive.md` is tone and history, not a spec. Honour its supersession markers.
- `documentation/screenshots/<pass>/README.md` records what each proof pass shot and found.

**Journals.** `documentation/journals/YYYY-MM-DD.md`, one file per day, shared by every concurrent session. `ls` it first; append with `cat >>` or an anchored replace; never create one with `cat >` or a whole-file write, which has erased other sessions' entries. Later entries supersede earlier ones.

**Entries are capped at 300 words** since 2026-09-05, one per session per topic, in three parts: **Changed** (what, in which files), **Evidence** (tests run and their verdicts, frames shot and where they are, numbers measured), **Open** (what is left or was found and not fixed). A decision goes in the design docs; the reasoning behind a shape goes in a comment beside the code that builds it. Neither goes in the journal.

## Stack

Godot 4.7.x standard build, not .NET. GDScript. Forward+. Blender for art, imported as `.blend`. macOS is the primary machine, Windows secondary. Search results for Godot mostly target 3.x; verify against Godot 4 documentation before applying anything found online.

## Current state, 2026-09-05

Greybox: no art, no audio. The first milestone, a plaza you can walk around and photograph, closed on 2026-08-11 with the answer that it is enjoyable on its own.

**One persistent world.** `scenes/world/park_world.tscn` mounts every place, landmark, transit layer and crowd exactly once, and `scenes/main/main.tscn` holds it for the life of the game. Crossing a district loads, frees, fades and teleports nothing. `ParkSections` is logical area context only, for crowd selection and UI; `ParkSections.enter` survives for old tools and changes that context alone, and `section_gate.gd` moves nothing. There are no far tableaux and no massing copies. This superseded section streaming on 2026-08-30.

**Generated sources under editor wrappers.** `tools/gen_props.gd` writes only `scenes/world/generated/*.tscn`. The same-named file one level up, `scenes/world/plaza_frontage.tscn` and so on, is a stable inherited wrapper and is the file to open in Godot: inspector changes become overrides there, and new hand-made objects go under its `authored_additions` node. Runtime code never references `generated/`. `plaza.tscn` and `park_world.tscn` are hand-authored; the three crowd scenes are pure output of `tools/gen_crowd.gd`. A generator run that changes a wrapper is a regression.

**What stands.** The 104m plaza with its fountain at the origin, 40m clock tower, bandstand, photo hut, perimeter frontage on both faces and seven ways out; the entrance street, arcade, turnstiles, apron, parking fields and approach road; the west cascade, arrival court, boardwalk, pier, wheel and wooden coaster; the east gate, forecourt, east cascade, belvedere, basin staircase, hill and shoulders; the Park Promenade; the Grove, Kiddieland, Fairground and Frontier as greybox rooms on real routes; routes A to F and junctions J1 to J9 of the rebuild atlas, with its ride parcels, midway bands, recurring interiors, service spines and Coastal Creek as greybox; the Grand Circuit road train and the Kiddieland railway; the sky ride and the observation tower; night lighting on a schedule. Outside the program envelope: the crescent range with a runtime forest, the coast as a bay, the coast highway (a divided road since 2026-09-06, two lanes each way on their own grades with a median that narrows to a wall where the hillside splits them, in its own cut corridor in the ground, with twin-bore tunnels and the park's diamond interchange over an overpass), the headland with lighthouse and harbour, two towns and a distant city. The player camera's far plane is 400m (`scenes/player/player.tscn`), so the towns, the city and most of the range show only in probes. Raising it is a game decision, not a scenery one.

**Systems.** `ParkClock` runs the day at twelve times real, open ten to ten. `daylight.gd` drives sun, sky and ambient from real solar geometry for latitude 32.75; there is no fog anywhere, so distance is painted. The crowd (`crowd.gd`, `guest.gd`) has per-area headcount curves, groups admitted and sent home through the gate, an attention stack, contagious noticing, posing on request, sitting, wheelchairs and buggies, and step-free routing. `ParkGuests` holds a roster with claim-ticket debts and nothing binds it yet. `PhotoAlbum` writes PNGs to `user://photos`. The HUD owns the capture; the viewfinder, album, pause menu and map are in `scenes/ui/`. `park_lights.gd`, `range_forest.gd` and `ride_vehicle.gd` run the lights, the forest and the trains.

**Protected anchors.** NT-1 Cascading Staircases (`scenes/world/west_stair.tscn`, built by `_cascade` with `ParkPlan.CASCADE_WEST`) and NT-2 Terraced Fountain (`scenes/world/east_cascade.tscn`, `CASCADE_EAST`). Their geometry, elevations, approaches, water, terrain and sightlines do not change without Christina's approval. Compare a normalized hash of each generated scene before and after any regeneration; the 2026-09-03 journal records the baseline. `anchor_walk_test` walks their routes.

**Open, in the order it seems to matter.** The park-section map-to-Godot **source-handoff** gate passed on 2026-09-09. That proves editable sources, ground support, routes, clearances and protected relationships; it does not mean the park maps have reached scenery or spatial fidelity. The standing park remains a colorful greybox except for the protected anchors. Before any further story or mission expansion, audit all nine park-section maps against the running Godot world for missing or under-resolved terrain, structures, frontage, interiors, operations, planting and props, then complete the scenery one spoke at a time under the fidelity gate in the masterplan. Do not resume the Kiddieland story slice until Christina explicitly reopens it. Asking a guest for a copy issues a ticket number and prints nothing. No guest has an errand; the schedule is the crowd's, not the individual's. Nobody queues, and nobody treats the pier as a destination. Rebuild packages 06 to 09 are planned and not built. The world beyond the park has no cars, no far headland and no sea stacks.

## Composition decisions that bind

- You arrive from the south; the boardwalk is west because the sun sets into it. Sunset is azimuth 294° and that bearing stays open water from the pier head and the promenade.
- The plaza is a room with routes crossing it: brick floor, asphalt walkways laid over it, at that polarity on purpose. The boardwalk is a route: the deck is the path, and which way the boards run carries direction. No brick west of the bluff.
- The two plaza gates face each other across the fountain and share `ARCH_HEIGHT` exactly. The west arch's beam soffit is sized against `ParkPlan.WHEEL_TOP`, which is published rather than derived, so the wheel's rim reads whole from `ARCH_RIM_CLEAR_X` inward.
- Both cascades face west and downhill is negative x on both; the east is the west translated, never mirrored. The middle of a cascade is water and its niche is blind; the wings carry the descent, north a ramp and south a garden stair.
- The tower clock is the only readout of the time. The crowd and the cafe tables are the second and third ways to read the hour.
- Sections are hidden horizontally and advertised vertically: a skyline cropped by a roofline, visible from here and not from there.

## Where things are

| | |
|---|---|
| `scripts/park_plan.gd` | `ParkPlan`, the park's layout in world coordinates and the one place positions are written down. A plain `RefCounted` that names no autoload, so it is safe to `preload` from a `--script` run. |
| `scripts/` | The autoloads: `park_clock`, `park_sections`, `park_guests`, `park_settings`, `photo_album`. |
| `scenes/player/` | `player.gd` walks and looks on a spring arm, `camera_tool.gd` is the Instamatic, `interact_tool.gd` asks a guest. Third person to move, first person to shoot. |
| `scenes/npc/` | `crowd.gd` and `guest.gd`, hand-written behaviour over generated bodies. |
| `scenes/world/` | The wrappers, `plaza.tscn`, `park_world.tscn`, `daylight.gd`, `tower_clock.gd`, `park_lights.gd`, `range_forest.gd`. |
| `assets/shaders/` | `water_pool.gdshader` and `water_fall.gdshader`, the only shaders. |
| `assets/textures/` | Written by `gen_props.gd` as `.res`, never `.png`, because a PNG is an import the next `--script` run cannot load. |
| `tools/` | Generators, tests, captures and probes. `tools/README.md` is the index; add a line there when you add a tool. `export_world_source.sh` is how a Blender world source reaches the game. |

## Running things

The generators and `clearance_test.gd` extend `SceneTree` and run with `--script`. Everything else extends `Node` and runs through `tools/run.tscn`, which resolves the tool named after a bare `--` and lists what it can start when given nothing:

```bash
/Applications/Godot.app/Contents/MacOS/Godot --headless --path . --script res://tools/gen_props.gd
/Applications/Godot.app/Contents/MacOS/Godot --headless --fixed-fps 60 --path . tools/run.tscn -- footprint_walk_test
open -n -a /Applications/Godot.app --args --path "$PWD" tools/run.tscn -- west_capture
```

`--headless` selects a dummy renderer: right for tests and generation, blank PNGs for captures. `open` needs an absolute path or Godot falls back to the project manager and idles. Never pass `--quit-after` to a capture. There is no `timeout` on the Mac; cap a run with a poll loop and read its log only after it exits, because headless stdout is buffered until then. Container sessions follow `.agents/skills/run-the-park/SKILL.md`.

**Acceptance set**, run before any commit that touches geometry, routes or crowds: `coplanar_test.py`, `footprint_test`, `footprint_walk_test`, `path_ground_test`, `clearance_test`, `anchor_walk_test`, `boardwalk_edge_test`, `section_test`, `transit_test`, `night_test`, `climb_test`. The measurements and narrower checks (`perf_test`, `day_test`, `inpool_test`, `seat_test.py`, `ground_contact_test`, `menu_test`) run when their subject changes. The legacy `walk_test` was split into the two anchor and edge tests and retired on 2026-09-05.

**Another session may hold the tree.** Christina runs several Codex and Claude sessions at once. Before regenerating or committing, check `git status` and `ls -lT "$HOME/Library/Application Support/Godot/app_userdata/Keep Your Ticket/logs/"` for timestamps that are not yours; `pgrep` is a point sample and proves nothing. A generator run publishes every uncommitted edit in the tree into all of its outputs, so know the node names your own code emits. Never round-trip a shared file through `/tmp`. Report another session's changes; do not revert them.

**A regenerated scene always looks modified**, because Godot rolls `unique_id`, every `[sub_resource]` id and every `[ext_resource]` id on each write. Ask whether anything moved with:

```
git diff -U0 -- scenes/ | grep -E '^[+-]' | grep -vE '^(\+\+\+|---)' | grep -v 'unique_id=' | grep -vE '^[+-]\[(sub_resource|node|ext_resource) .*id="[A-Za-z0-9_]+"\]$' | grep -vE 'SubResource\("|ExtResource\("'
```

Empty means the run was inert. Run it through `rtk proxy` or redirect to a file first: the `rtk` shell hook condenses piped git output into a summary that parses as nothing.

## Game constraints

- **Collecting and exploring are the primary objectives.** Density of things to find beats systems. Job tasks and minigames are texture and stay small.
- **Free aim.** Nothing frames, snaps, aligns or scores a shot, and no shot is confirmed as the right one. The park may point at things through the shot list and picture-spot signs; the game may not compose on the player's behalf.
- **No pointer.** Look-based aiming; flat interfaces are grid-navigable with directional input.
- **Input goes through actions**, never raw device polling. Gamepad and mobile stay open.
- **No meters, scores or currencies.** Nothing counts up or down. Completion is filled and empty album slots.
- **Failure is cheap.** Being caught returns the player to a gate. Nothing is deducted.
- **Camera capability is the progression gate.** The Instamatic has fixed focus and exposure, no zoom, and cannot expose a dark scene. Night opens when the camera does.
- **NPCs and events run on the park's schedule**, and **the time is read off the park**, never a HUD.
- **A section is a three-plaza job**, about 670 props at one per 30m². The park grows one spoke at a time.
- These lists are working notes, not law. When an idea seems to conflict with one, ask what the bullet protects before arguing from its wording.

## Build rules

Each of these cost real time at least once. The incident is in the archive under the same words.

**Human authorship and generators**

- Christina is an active builder, not only a reviewer. Preserve her ability to select, reshape and replace the canonical geometry in Godot or Blender without editing generator code.
- A wrapper and `authored_additions` preserve work around generated geometry; they do **not** make the generated geometry itself human-editable. Never cite them as satisfying an editability requirement for the underlying shape.
- Roads, paths, rivers, shorelines, rails, terrain silhouettes, building footprints and landmark forms default to editor-owned scenes, curves or resources. A generator may derive repetitive construction from those authored sources—surfaces, collision, kerbs, markings, cuts, supports, lights or scatter—but must not own or overwrite their artistic course or form.
- Before moving an editor-owned shape, placement or composition into code or generated output, stop and obtain Christina's explicit approval of that ownership tradeoff. State what becomes harder to edit and why automation is worth it. This approval is required even when generation would be deterministic or easier to test.
- A real handoff names the ordinary source scene or asset, lets Christina make the intended visible change through editor controls, and proves regeneration preserves it. An instruction to edit coordinates in GDScript is not a handoff.
- Collision is derived from the visible object at export, never authored beside it. A `-colonly` twin of an authored object carries no information and turns every move, duplicate and recolour into two edits; on 2026-09-15 the range held 7,554 of them and eight boulders had already drifted from theirs. If an object must not collide, mark it `kyt_collision=none`; if a source needs a different collision shape, derive it in `tools/export_world_source.py`, not in Blender.
- When Christina can establish a shape faster by hand than an agent can reproduce it procedurally, hand that portion over early and automate only its consequences. Treat a large estimate for generated greybox as a prompt to change method or divide the work, not as permission to consume the estimate.
- Existing generator-owned artistic geometry is not precedent. When substantially revising it, offer to migrate its canonical shape to an editor-owned source before extending the generator.

**Layout**

- Anything two generators both need goes in `ParkPlan`. A hand-authored table that shadows generated geometry goes stale silently; ask which consumer would notice if it drifted.
- Apply `ParkPlan.plaza_out` and `rebuild_expand_point` to an assembly's base, never to its finished parts, and never to a position that already moved by decision.
- Every helper that places a part composes position the same way, base plus local offset through `_place`. Assert that a scene's contents lie where that scene lives.
- A route in `ParkPlan` is a claim. It is true once the real player has walked it both ways, centre and both edges, with a probe pushed at every open edge. Aim each leg along the thing it asks about; a waypoint the body can walk past passes and fails on identical geometry.
- Write the relationship, not the number. A setback, a rail length or a landing depth is derived from what it depends on, or it is wrong the next time that thing moves.
- Anything meant to be seen from a standpoint is checked from that standpoint, at the camera's real position: the spring arm hangs it about 2.5m back and pitching up lowers it. A margin is a property of a standpoint, not of a design. Measure the emitted scene, not the constants.

**Geometry**

- Shapes may overlap; they may not share a plane. `_begin_scene` hands each shape a sub-millimetre displacement by build order, wrapping at `SEAM_STEPS`, so a coplanar pair is fixed by changing the shape, footing it or lapping it, never by reordering the build. Hand-authored shapes yield down and inward.
- A tall box may not be tilted: its corners swing by height times the sine of the angle. Build a slope as uprights under a thin cap.
- A flat top under rising ground is set by its low end.
- `CharacterBody3D` has no step-up. A stair is a narrow ramp with treads showing past it, paving sits 12mm proud with no collision, and a centimetre of lip is a wall.
- A material that carries a world position, `water_pool`'s `centre` or `water_fall`'s fade band, is a material for one place. Read a shader's uniforms before reusing it.
- A `vec4` uniform handed a `Plane` saves as `null`; pass a `Vector4`. `PortableCompressedTexture2D` needs `keep_compressed_buffer = true` before `create_from_image` or it saves a valid, empty file.
- If a comment describes a surface, some line of code must emit it. A described-but-unbuilt face looks like scenery nobody has dressed yet.

**Seeing**

- A screenshot cannot show z-fighting, a direction of motion, anything below the knee, or what an opening frames. Each has its own check: `coplanar_test.py`, `flow_probe`, arithmetic over the whole height range, a frame shot through the opening.
- Diagnose a failing composition with a computed section before dressing it. If a feature cannot be seen from the standpoint it exists for, no finish pass fixes it; make one structural change.
- Delete the previous frames before a capture run. A wait on a file the last run left is satisfied instantly and returns the last run's pictures.
- `--script` compiles before autoloads register, so a generator must not `preload` anything that names one, and a tool that needs one runs through `run.tscn`. `--check-only` reports every autoload reference as an error and cannot check such files.
- A parse failure under headless Godot looks exactly like a hang. Kill it and read the log.

**Crowd**

- A guest's height comes off the leg being walked: absolute, from the node behind, measured along the leg. A follower takes it off the leader's trail.
- Kind strings are matched with `begins_with` and `ends_with("kid")`, never `==`. A branch in `gen_crowd.gd` draws the same number of `_rng` values whichever way it goes.
- Do not build a crowd tiering scheme without re-measuring. Separation was bucketed on 2026-08-12 and the per-guest cost is flat at about 16µs; what 150 bodies cost to draw has never been measured.

## Conventions

- `snake_case` for files and directories. Scenes in `scenes/`, scripts beside their scenes, shared code in `scripts/`.
- Signals over direct cross-system calls. Autoloads only for genuinely global state.
- Generated scenes are never edited by hand; edit the generator, or use the wrapper.
- Commit only when asked, after checking the tree for other sessions' work. No attribution lines in commit messages.
