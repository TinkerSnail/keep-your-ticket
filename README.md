# Keep Your Ticket

The park is open, everyone's having fun, and you're on the clock. Take pictures, learn your way around, and stick around after the gates close.

A first-person photography game about working at a local amusement park. You rove the park with a camera, shoot guests, and learn the place well enough to find the shots nobody sent you to take.

## Status

Early. This is a greybox — no art, no audio, no schedule. The first milestone is built and running: a single plaza you can walk around and photograph, which exists to answer whether that alone is enjoyable before anything else gets added.

What's in it:

- A CSG greybox plaza — fountain, bandstand, photo hut, sign tower
- First-person walk and look on a `CharacterBody3D`
- The Instamatic: a viewfinder overlay and a shutter that writes the viewport to a PNG
- An album grid for reviewing what you've shot
- Four guests walking fixed waypoint loops

The camera has fixed focus, fixed exposure, and no zoom, and that is deliberate — the only way to solve a shot is to stand somewhere else or be there at a different time.

## Running it

Requires [Godot 4.7.x](https://godotengine.org/download), standard build. Not the .NET/C# build — this project is GDScript.

Open `project.godot` in the editor and press play, or from the command line:

```bash
godot --path .
```

Photos are written to Godot's user data directory, under `photos/`. On macOS that resolves to `~/Library/Application Support/Godot/app_userdata/Keep Your Ticket/photos`.

## Controls

| | Keyboard / mouse | Gamepad |
|---|---|---|
| Move | `W` `A` `S` `D` | Left stick |
| Look | Mouse | Right stick |
| Jump | `Space` | `A` / `Cross` |
| Raise camera | `F` or right mouse | `L2` |
| Shutter | `Enter` or left mouse | `R2` |
| Album | `Tab` | `Y` / `Triangle` |

Raising the camera is tap-or-hold. A quick tap latches it up until you tap again; holding works as a hold. Both exist so the game is playable on a trackpad, where you can't hold a two-finger press and click at the same time.

Everything routes through named input actions rather than raw device polling, which is what keeps gamepad and a possible mobile build open.

## Layout

```
scenes/
  main/     main.tscn — the scene that runs
  world/    plaza.tscn — the greybox; plaza_props.tscn and plaza_skyline.tscn — generated
  player/   player.gd (walk and look), camera_tool.gd (the Instamatic)
  npc/      npc_walker.gd — waypoint loops
  ui/       viewfinder, album grid, HUD
scripts/
  photo_album.gd — autoloaded as PhotoAlbum, owns capture storage
tools/
  gen_props.gd — rebuilds plaza_props.tscn
  capture.gd — poses the player and saves screenshots
  run.tscn — runs any tool that needs the autoloads
```

The tools are development-only and never run as part of the game, and they
start two different ways depending on what they need.

The generators and `clearance_test` are `MainLoop`s with an `_initialize`, and
run with `--script`:

```bash
godot --headless --path . --script res://tools/gen_props.gd
```

Everything else is a `Node` with a `_ready`, and needs a tree with the autoloads
in it. `--script` compiles before autoloads are registered, so a tool naming
`ParkClock` or `ParkSections` dies at compile without running a line — which is
all of them but the three above. Those go through `run.tscn`, named after a
bare `--`:

```bash
godot --headless --path . tools/run.tscn -- walk_test
godot --path . --rendering-driver vulkan tools/run.tscn -- west_capture
```

Run it with no tool named and it lists what it can start, and which ones want
`--script` instead. Use `--headless` for anything that only reads the scene, and
a real rendering driver for anything that saves a frame: headless selects a
dummy renderer that draws nothing, so a capture pass under it writes grey and
reports success.

`plaza_props.tscn` is generated output — edit `gen_props.gd` and re-run rather than moving props by hand, or the next regeneration discards the change. It builds transforms with `Transform3D.rotated()` and `Basis(axis, angle)` rather than writing basis components, because the `.tscn` format serialises basis *rows* while `basis.x/y/z` are the *columns*, and hand-writing the nine numbers silently yields the transpose.

Scripts live alongside the scenes they belong to. `scripts/` is for shared code only. Files and directories are `snake_case`.

## Built with

Godot 4.7.x (Forward+), GDScript, and Blender for art once there is any.

Note for anyone reading the code with search-engine help: most Godot results target 3.x, where a lot of the API differs. Check against the Godot 4 docs.

## A note on scope

This is a personal project and not looking for contributions, but you're welcome to read, clone, and take anything useful from it.
