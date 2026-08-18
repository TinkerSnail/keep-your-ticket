---
name: run-the-park
description: Launch and drive Keep Your Ticket in a headless Linux container — walk the player, raise the Instamatic, fire the shutter, and collect screenshots. Use this whenever you need to see a change working in the real game rather than in a test: "run it", "start the game", "screenshot the fountain", "does this actually look right", "check it in game". Also the prerequisite for re-running `tools/gen_props.gd` or any `tools/_*_probe.gd`, because it is what puts a matching Godot binary and a working renderer on the box. Do not try to launch Godot without reading this first — the two failures that eat the most time (a dummy renderer that saves blank PNGs, and a scene that will not load because the class registry was never built) both look like something else.
---

# Running the park

The game is Godot 4.7.x, Forward+, GDScript. A container has no GPU and no
display, so "run it" means three things that are easy to get wrong
separately: a renderer that actually rasterises, an X server for it to talk
to, and an imported project so `class_name` resolves.

## Setup, once per container

```bash
eval "$(.claude/skills/run-the-park/scripts/setup_headless.sh | tail -1)"   # sets $GODOT
```

`drive.sh` calls it for you, so this line is only needed when you want `$GODOT`
in your own hand — to run the generator, say. It is idempotent — re-running it is cheap, so just run it rather than
checking. It does four things, and each one is load-bearing:

1. **Fetches the Godot binary** into the scratchpad, matching the version in
   `project.godot`'s `config/features`. A different minor version will open
   the project but reshuffle every `unique_id` when a generator writes a
   scene, which turns a two-line change into a four-thousand-line diff.
2. **Installs `mesa-vulkan-drivers`** for lavapipe, the software Vulkan ICD.
   Without an ICD, `libvulkan` is present but has no driver behind it.
3. **Installs `xvfb`.** `--headless` is not an option here: it forces the
   *dummy* rendering driver, so the game runs, the script completes, and
   every screenshot is a blank 4KB PNG. Rendering needs a display, so it
   needs a virtual one.
4. **Runs an import pass** (`--editor --quit`). A fresh clone has no
   `.godot/global_script_class_cache.cfg`, so the `class_name` registry is
   empty and anything referencing a global class fails to parse. The symptom
   is misleading: `main.tscn` fails to load with *"Identifier "ParkUI" not
   declared in the current scope"* pointing at `park_menu.gd`, which reads
   like a code error in a file nobody touched.

## Driving it

Write a driver scene — a `Node` that instantiates `main.tscn` as a child and
then plays the game. Start from `assets/driver_template.gd`, edit the middle,
and run it:

```bash
.claude/skills/run-the-park/scripts/drive.sh /path/to/your_driver.gd
```

`drive.sh` also takes a `.tscn` and runs it as-is, which is what the tools that
already carry their own scene need — `tools/capture.tscn`, `tools/west_capture.tscn`.

Screenshots and anything the game writes to `user://` land in
`~/.local/share/godot/app_userdata/Keep Your Ticket/`; the Instamatic's photos
go in `photos/` under that. **Look at the PNGs.** A blank or black frame means
the launch failed, not that the scene is empty.

A run takes several minutes under software rendering — the full `west_capture`
pass and its 50 shots takes the best part of ten. Give the Bash tool a timeout
well past its 120s default or it will be killed mid-run, and a killed run can
leave an X lock behind — `drive.sh` clears stale locks on the way in, because
the symptom otherwise is a bare `exit 144` with no message.

Do not clear those locks by typing `pkill -f Xvfb` at a prompt. `pkill -f`
matches whole command lines, so a shell running a command that mentions Xvfb
matches its own argv and kills itself; the symptom is a command that stops dead
part-way through with no error, which reads like the *game* having crashed. It
is safe inside `drive.sh` because a script's argv is just its path.

### Input: two mechanisms, and using the wrong one fails silently

Movement is polled in `_physics_process`, so `Input.action_press("move_forward")`
drives it. The Instamatic is not: `camera_tool.gd` and `player.gd` read
`_unhandled_input`, and the actions bind to **physical** keycodes. A
synthesised `InputEventAction` will not do — send a real `InputEventKey` with
`physical_keycode` set, via `Input.parse_input_event`.

| Action | Key | How to send it |
|---|---|---|
| walk | `move_forward` etc. | `Input.action_press` / `action_release` |
| raise the Instamatic | `F` (70) | `InputEventKey`, `physical_keycode = KEY_F` |
| shutter | `Enter` (also LMB) | `InputEventKey`, `physical_keycode = KEY_ENTER` |
| first/third person | `V` (86) | `InputEventKey`, `physical_keycode = KEY_V` |

The silent-failure shape is worth recognising: the player walks, so input
*looks* fine, while every event-driven action is ignored. Movement polls
global action state and never touches the event pipeline, so it keeps working
when nothing else does.

### Hold the camera, do not tap it

Raising the Instamatic is tap-or-hold, and `TAP_SECONDS` is 0.25. Under
lavapipe a frame is long enough that a scripted press-then-release lands past
that threshold, so the game reads it as a hold and drops the camera the moment
you release — correct behaviour, useless timing. Press `F`, leave it down
through the shot, release afterwards.

## Where to stand

The player spawns at `(0, 0.2, 24)` facing `-Z`, and the fountain is at the
origin, so holding `move_forward` walks straight at it and the kerb stops the
capsule around `z = 11`. Six seconds of settling before the first frame is
about right — CSG has to build and the crowd has to spawn.

`ParkClock.running = false` then `ParkClock.set_clock(h, m)` freezes the hour,
which is the only way to compare two runs of the same shot. 15:00 is the
daylight standpoint; 21:15 is after dark, which is when anything emissive or
lamp-lit is worth checking.

## The other tools

`tools/` holds the generator and a drawer of probes, all run with the same
binary this skill installs — `$GODOT` below is what `setup_headless.sh` prints:

```bash
"$GODOT" --headless --path . --script res://tools/gen_props.gd   # rebuild the scenes
python3 tools/coplanar_test.py                                   # z-fight check, seconds
```

The probes (`tools/_*_probe.gd`) are bare scripts that need the scene wrapper,
so hand them to `drive.sh` and it does that for you. `--headless` is right for
the generator, which writes `.tscn` files and never renders; it is wrong for
anything that saves a PNG.

Two of the capture tools ship their own scene rather than borrowing a wrapper,
and the reason is worth knowing before you write a third: `--script` compiles a
file *before* the project's autoloads register, so any tool that names
`ParkClock` or `ParkSections` at the top level dies at compile with "Identifier
not found" before drawing a frame. `gen_props.gd` dodges it by loading late;
a tool whose whole job is to drive the clock across a section boundary cannot,
so it runs as a scene instead.

Godot writes a `.uid` beside every script it imports. The repo tracks those,
but do not commit ones for throwaway drivers — delete the driver and its
`.uid` when you are done.
