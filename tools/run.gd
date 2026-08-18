extends Node

## Dev tool: runs any of the `_ready`-style tools in `tools/`, in a tree that has
## the autoloads up.
##
## **Why this has to exist.** `godot --script res://tools/<x>.gd` compiles the
## script before the project's autoloads are registered, so any tool naming
## `ParkClock`, `ParkSections`, `ParkGuests`, `ParkSettings` or `PhotoAlbum`
## dies at compile with "Identifier not found" and never runs a line. Nineteen of
## the twenty-two tools in this directory do exactly that, which means the
## documented way to run them worked for three of them.
##
## `gen_props.gd` documents the same trap from the other side and dodges it by
## `load`-ing late; that works because it only needs a *script* at runtime. A
## tool that names an autoload in its own body cannot dodge it, because the name
## has to resolve at compile time. The fix is not to rewrite nineteen tools, it
## is to stop compiling them before the tree exists — which is what running a
## scene does.
##
## The split is exactly the entry point they use, and that is not a coincidence:
##
##   `_initialize`  a `MainLoop`, run with `--script`, no tree and no autoloads.
##                  `gen_props`, `gen_crowd`, `clearance_test`.
##   `_ready`       a `Node`, needs a tree. Everything else.
##
## **One runner rather than a scene per tool.** Each tool could have its own
## two-line `.tscn` and two of them used to, but half the directory is
## deliberately throwaway — the `_*_probe.gd` files say so in their own headers,
## and they are written for one question, answered, and left in the history. A
## permanent scene file per throwaway probe enshrines the scratch work; a runner
## that takes the tool's name enshrines nothing and covers the ones not written
## yet.
##
## Usage, with the tool named after a bare `--`:
##
##     godot --headless --path . tools/run.tscn -- walk_test
##     godot --path . --rendering-driver vulkan tools/run.tscn -- west_capture
##
## `--headless` for anything that only reads the scene, and a real driver for
## anything that saves a frame: headless selects a dummy renderer that draws
## nothing, so a capture run under it writes fifty grey PNGs and reports success.

## What to say when the name does not resolve, rather than failing silently the
## way the old `--script` invocation did.
const USAGE := "usage: godot --path . tools/run.tscn -- <tool>   (e.g. walk_test)"


func _ready() -> void:
	# Everything after a bare `--` on the command line. `get_cmdline_args` would
	# also carry Godot's own flags, which is not what a tool name is.
	var args := OS.get_cmdline_user_args()
	if args.is_empty():
		push_error(USAGE)
		_list()
		get_tree().quit(2)
		return

	var path := _resolve(args[0])
	if path.is_empty():
		push_error("no such tool: %s\n%s" % [args[0], USAGE])
		_list()
		get_tree().quit(2)
		return

	var script: Script = load(path)
	if script == null:
		push_error("could not load %s" % path)
		get_tree().quit(1)
		return

	# The tool's own remaining arguments are left on the command line for it to
	# read, so this stays a launcher rather than becoming a parser.
	print("run: %s" % path)
	var tool_node := Node.new()
	tool_node.name = path.get_file().get_basename()
	tool_node.set_script(script)
	# Added to the scene root rather than kept aside, because `_ready` is what
	# every one of these tools does its work in and `_ready` needs a tree.
	add_child(tool_node)


## Accepts `walk_test`, `walk_test.gd`, `tools/walk_test.gd` or a full `res://`
## path, and answers empty if none of them is a file.
func _resolve(name: String) -> String:
	var tries: Array[String] = []
	if name.begins_with("res://"):
		tries.append(name)
	else:
		var base := name.trim_suffix(".gd")
		tries.append("res://tools/%s.gd" % base)
		tries.append("res://%s.gd" % base.trim_suffix(".gd"))
	for t in tries:
		if ResourceLoader.exists(t):
			return t
	return ""


## What is here, so a mistyped name answers with the list rather than with
## nothing. `_initialize` tools are named as the ones this cannot run: handing
## `gen_props` to the runner would put a `MainLoop` in a tree and do nothing.
func _list() -> void:
	var scene_tools: Array[String] = []
	var script_tools: Array[String] = []
	var dir := DirAccess.open("res://tools")
	if dir == null:
		return
	for f in dir.get_files():
		if not f.ends_with(".gd") or f == "run.gd":
			continue
		var src := FileAccess.get_file_as_string("res://tools/" + f)
		if src.contains("func _initialize("):
			script_tools.append(f.trim_suffix(".gd"))
		else:
			scene_tools.append(f.trim_suffix(".gd"))
	scene_tools.sort()
	script_tools.sort()
	print("tools this runs:")
	for t in scene_tools:
		print("  ", t)
	print("tools that take --script instead (they are MainLoops):")
	for t in script_tools:
		print("  godot --headless --path . --script res://tools/%s.gd" % t)
