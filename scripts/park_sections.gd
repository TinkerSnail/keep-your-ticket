extends Node

## The park's sections and which one is standing, autoloaded as `ParkSections`.
##
## A section is the ground, the props and the crowd of one themed part of the
## park, and only one is in the tree at a time. The player, the HUD and the
## autoloads outlive the swap; everything else is mounted and thrown away.
##
## The park is a hub with spokes. You leave the plaza down a corridor, the
## corridor bends, and behind the bend is a threshold you cannot see through.
## That is where this loads. `documentation/design.md` calls the bend a midway
## and gives it shops on both sides; the bend is also what buys the load its
## cover, so every spoke needs one whether or not it has the shops yet.
##
## Nothing here streams by distance and nothing unloads on a timer. A section is
## mounted when the player crosses into it and dropped when they cross out, which
## means the seams are authored rather than emergent — there are six of them, the
## park knows where they are, and a load can never begin somewhere the player can
## watch it happen.
##
## What does not live here: the guests who have to be the same person twice. A
## section's crowd is generated, anonymous and discarded with the section. The
## people a claim ticket is owed to live in `ParkGuests`, above all of this, and
## get bound onto whichever crowd is standing.

## About to leave `from`. Anything that has to save something before its section
## is dropped — the crowd stowing who was here — hangs off this.
signal section_leaving(from: StringName)

## The new section is mounted and the player is standing in it.
signal section_entered(id: StringName)

## A preload was started for a section the player is walking towards. Not a
## promise they will arrive: turning round in the corridor is allowed and costs
## only the load already done.
signal section_preloading(id: StringName)

## Where sections get mounted. A group rather than a path so that a harness can
## host them somewhere else — `tools/capture.gd` and `tools/walk_test.gd` both
## build their own trees and neither has a `main`.
const HOST_GROUP := &"section_host"

## Sections are mounted into the same group `main` currently puts the plaza and
## the crowd in, so anything already looking for the world keeps finding it.
const WORLD_GROUP := &"world"

## The park, as scenes rather than as places.
##
## `scenes` is a list rather than one path because a section is already more
## than one file — the plaza is its ground and its crowd, generated separately
## and regenerated on different days. Mounting a list means no wrapper scene has
## to exist and be kept in step with the generators.
##
## An empty `scenes` is a section that is planned and not built. The four
## scaffolded thresholds in the plaza wall are exactly that: they are passages
## that bend and stop, and walking to the end of one has to do nothing rather
## than crash. They are not named here because naming them would be inventing
## park content ahead of the design, and `documentation/design.md` has settled
## only the boardwalk.
const SECTIONS := {
	&"plaza": {
		"name": "the plaza",
		"scenes": [
			"res://scenes/world/plaza.tscn",
			"res://scenes/world/plaza_crowd.tscn",
		],
	},
	## The strip below the bluff: promenade, frontage, wheel, coaster, pier.
	##
	## Two scenes, and the first of them is also in the plaza's list. `west_shell`
	## is the water, the bluff and the shore — the ground both sections stand on
	## and the horizon both of them see. It has to be mounted on either side of
	## the seam, because a section swap frees everything the outgoing section
	## owned, and the west used to be owned entirely by the plaza. Crossing the
	## gate therefore deleted the water.
	##
	## Listing it twice is the cheap fix and the right one: sections are already
	## lists of scenes precisely so that a section can be more than one file, and
	## the alternative — a third persistent tier mounted outside sections — buys
	## nothing while exactly one thing is shared.
	&"boardwalk": {
		"name": "the boardwalk",
		"scenes": [
			"res://scenes/world/west_shell.tscn",
			"res://scenes/world/boardwalk.tscn",
			"res://scenes/world/boardwalk_crowd.tscn",
		],
	},
}

## Where the player stands on arriving, per section, keyed by where they came
## from. Read from the section itself when it provides a marker — a child named
## `arrival_from_<id>` anywhere under the mounted scenes — and from here when it
## does not.
##
## The fallbacks exist because the ground is generated and the markers are not
## generated yet. `tools/gen_props.gd` should emit them with the stair, at which
## point these become dead weight and can go.
##
## Until then these are a second copy of the generator's arithmetic, which is
## the thing markers exist to avoid — so they are written out rather than
## asserted. Coming back from the boardwalk puts the player on the foot slab at
## the bottom of the west stair, facing back up it:
##
##   x   `STAIR_TURN_X`, −44.7. Flight B runs straight down the turn's axis.
##   y   the landing is `STAIR_RISE * treads_a` below the terrace, −1.0, and
##       flight B drops `STAIR_RISE * treads_b` more, 5.0, so the slab's walking
##       surface is at −6.0. The player rides 0.2 above their floor, the same
##       clearance `main.tscn` gives them in the plaza.
##   z   `STAIR_TOP_Z + STAIR_W * 0.5` is −8.4, plus `run_b * treads_b` of 12.6,
##       plus half a stair width to the slab's centre: 5.5, less 0.7 to stand
##       behind the crossing volume rather than inside it. The shut gate is a
##       further 1.4 south, so this stands inside it.
##   yaw zero. A Node3D looks down −Z, the stair descends towards +Z, so facing
##       zero is facing back up the flight the player just came down.
##
## If the stair moves, this is wrong and nothing will say so until somebody
## arrives inside the bluff. That is the argument for the markers.
const ARRIVAL_FALLBACK := {
	&"plaza": {
		&"boardwalk": {"position": Vector3(-44.7, -5.8, 4.8), "yaw": 0.0},
	},
}

## Out faster than in. Going dark wants to feel like the threshold taking the
## frame; coming back wants to feel like arriving somewhere, and arriving is the
## slower half of walking through a door.
const FADE_OUT := 0.28
const FADE_IN := 0.36

## Above everything, including the viewfinder overlay. A player who crosses a
## threshold with the Instamatic up should go dark with the rest of the screen.
const FADE_LAYER := 128

var _current: StringName = &""
var _mounted: Array[Node] = []
var _host: Node = null
var _preloading: StringName = &""
var _busy := false
var _fade: ColorRect = null


## Which section is standing. Empty before the first mount, which is a real
## state rather than an error — a harness that never calls `enter` runs with
## whatever its own scene put in the tree.
func current() -> StringName:
	return _current


func section_name(id: StringName) -> String:
	if not SECTIONS.has(id):
		return ""
	return SECTIONS[id]["name"]


## Whether a section is built. The four scaffolded thresholds answer false, and
## every caller has to cope with that rather than assume the park is finished.
func is_built(id: StringName) -> bool:
	if not SECTIONS.has(id):
		return false
	var scenes: Array = SECTIONS[id]["scenes"]
	return not scenes.is_empty()


## Start pulling a section off disk. Called when the player enters the corridor,
## which is the whole reason the corridor is long enough to be worth walking.
##
## Cheap to call repeatedly and cheap to abandon: a preload that is never
## entered leaves the scenes in Godot's resource cache, so turning round in the
## corridor and coming back later costs nothing the second time.
func begin_preload(id: StringName) -> void:
	if not is_built(id) or id == _current or _preloading == id:
		return
	_preloading = id
	for path in SECTIONS[id]["scenes"]:
		# CACHE_MODE_REUSE, the default: a section walked into twice in one
		# session is already in memory the second time. Sections are authored
		# scenes with no per-visit state — the crowd reads the hour off
		# `ParkClock` when it comes up — so reusing them is not stale, it is the
		# same park at a different time of day.
		ResourceLoader.load_threaded_request(path)
	section_preloading.emit(id)


## Whether a preloaded section is ready to be entered without a hitch. Entering
## before this is true is allowed and simply blocks; the gate at the seam uses
## it to decide whether to hold the player for a beat.
func is_ready(id: StringName) -> bool:
	if not is_built(id):
		return false
	for path in SECTIONS[id]["scenes"]:
		if ResourceLoader.load_threaded_get_status(path) != ResourceLoader.THREAD_LOAD_LOADED:
			return false
	return true


## Cross into a section. `from` is where the player came from, and decides where
## in the new section they are put down.
##
## Under a fade, and the fade is not decoration. A threshold that cuts straight
## from one section to the next pops however well the corridor hid the load,
## because the cut itself is the tell. Covering the swap is the older answer —
## Zelda holds the shot at the door, walks the player out of frame and fades —
## and the half of it that survives having a free-look camera is the fade and
## the fact that the player never stops walking. `player.begin_crossing` is what
## keeps the walk going; this only has to make the swap invisible while it does.
##
## The load itself should already be done by here, paid for by the corridor. The
## fade is buying cover, not time — and if it is buying time as well, the
## corridor between the two gates is too short.
func enter(id: StringName, from: StringName = &"") -> void:
	if _busy or id == _current:
		return
	if not is_built(id):
		push_warning("sections: '%s' is not built — the threshold leads nowhere" % id)
		return
	if _find_host() == null:
		push_error("sections: no node in group '%s' to mount into" % HOST_GROUP)
		return

	_busy = true
	var player := get_tree().get_first_node_in_group("player")
	if player != null and player.has_method("begin_crossing"):
		player.call("begin_crossing")

	await _fade_to(1.0, FADE_OUT)
	_swap(id, from)
	await _fade_to(0.0, FADE_IN)

	if player != null and is_instance_valid(player) and player.has_method("end_crossing"):
		player.call("end_crossing")
	_busy = false


## The swap proper, and the order matters. The new ground goes in first, the
## player is moved onto it, and only then is the old section taken out — a
## player moved after the old floor is gone spends a frame falling, and
## `CharacterBody3D` keeps the velocity.
##
## All of this happens under a full black screen, which is worth knowing when
## reading it: nothing here has to look like anything.
func _swap(id: StringName, from: StringName) -> bool:
	var host := _find_host()
	if host == null:
		return false

	if _current != &"":
		section_leaving.emit(_current)

	var arriving: Array[Node] = []
	for path in SECTIONS[id]["scenes"]:
		var packed: PackedScene = _take(path)
		if packed == null:
			push_error("sections: '%s' failed to load" % path)
			_free_all(arriving)
			return false
		var node := packed.instantiate()
		node.add_to_group(WORLD_GROUP)
		arriving.append(node)

	for node in arriving:
		host.add_child(node)

	_place_player(arriving, id, from)

	var leaving := _mounted
	_mounted = arriving
	_current = id
	_preloading = &""
	_free_all(leaving)

	# Emitted here rather than after the fade-in, so that anything reacting to
	# the new section — a crowd binding its roster, a HUD naming the place — has
	# done it while the screen is still black.
	section_entered.emit(id)
	return true


## Take over whatever the host scene already had in it, so that a tree built by
## hand — `main.tscn` with the plaza in it, or a tool harness — counts as
## standing in a section rather than in nothing. Without this the first crossing
## would mount the boardwalk and leave the plaza behind, in the tree, forever.
func adopt(id: StringName) -> void:
	var host := _find_host()
	if host == null:
		return
	_mounted.clear()
	for child in host.get_children():
		_mounted.append(child)
		child.add_to_group(WORLD_GROUP)
	_current = id


## Built here rather than put in the HUD, because it is not the HUD's. The HUD
## owns the viewfinder and the capture and is a thing the player is looking
## through; this is the screen being taken away from them for a third of a
## second, and it belongs to whatever is doing the taking.
func _ensure_fade() -> ColorRect:
	if is_instance_valid(_fade):
		return _fade
	var layer := CanvasLayer.new()
	layer.layer = FADE_LAYER
	add_child(layer)
	_fade = ColorRect.new()
	_fade.color = Color(0.0, 0.0, 0.0, 0.0)
	# Or the black rectangle eats the mouse for the rest of the session.
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(_fade)
	_fade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	return _fade


func _fade_to(alpha: float, seconds: float) -> void:
	var rect := _ensure_fade()
	var tween := create_tween()
	tween.set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_SINE)
	tween.tween_property(rect, "color:a", alpha, seconds)
	await tween.finished


func _find_host() -> Node:
	if is_instance_valid(_host):
		return _host
	_host = get_tree().get_first_node_in_group(HOST_GROUP)
	return _host


## `load_threaded_get` blocks until the load finishes, which is the right
## behaviour at the seam: the player has crossed, and a frame of hitch is better
## than a frame of nothing. If the corridor did its job this returns at once.
func _take(path: String) -> PackedScene:
	var status := ResourceLoader.load_threaded_get_status(path)
	if status == ResourceLoader.THREAD_LOAD_INVALID_RESOURCE:
		# Never requested — crossed a seam nobody preloaded. Legitimate: a dev
		# tool jumping straight into a section has no corridor to walk.
		return load(path) as PackedScene
	return ResourceLoader.load_threaded_get(path) as PackedScene


func _place_player(arriving: Array[Node], id: StringName, from: StringName) -> void:
	var player := get_tree().get_first_node_in_group("player") as Node3D
	if player == null:
		return

	var spot := _arrival(arriving, id, from)
	if spot.is_empty():
		push_warning("sections: '%s' has no arrival from '%s' — player left where they stood"
			% [id, from])
		return

	var at: Vector3 = spot["position"]
	var yaw: float = spot["yaw"]
	# Through the player rather than around it: the walking view is a spring arm
	# and the look is split across the body and the head, so moving the node and
	# hoping is how the camera ends up under the floor.
	if player.has_method("place_at"):
		player.call("place_at", at, yaw)
	else:
		player.global_position = at
		player.rotation.y = yaw
		if player is CharacterBody3D:
			(player as CharacterBody3D).velocity = Vector3.ZERO


## A marker in the section wins over the table, so that the day the generator
## starts emitting them the fallbacks stop being consulted without anything
## having to be deleted first.
func _arrival(arriving: Array[Node], id: StringName, from: StringName) -> Dictionary:
	var marker_name := "arrival_from_%s" % from
	for node in arriving:
		var marker := node.find_child(marker_name, true, false) as Node3D
		if marker != null:
			return {"position": marker.global_position, "yaw": marker.global_rotation.y}

	if ARRIVAL_FALLBACK.has(id) and ARRIVAL_FALLBACK[id].has(from):
		return ARRIVAL_FALLBACK[id][from]
	return {}


## Out of the tree before freed, not merely queued. A `queue_free` alone leaves
## the old crowd in the tree for the rest of the frame, still processing, still
## answering `get_first_node_in_group` — so the incoming crowd and the outgoing
## one are both live at once and the player is found by both.
func _free_all(nodes: Array[Node]) -> void:
	for node in nodes:
		if not is_instance_valid(node):
			continue
		var parent := node.get_parent()
		if parent != null:
			parent.remove_child(node)
		node.queue_free()
