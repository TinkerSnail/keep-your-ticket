extends Node

## Logical area context for the continuously loaded park.
##
## The first version of the park used an area name as a scene-ownership rule:
## crossing a seam mounted one list of scenes, teleported the player, then freed
## the previous list. That stopped matching the map as soon as two public routes
## reached the same district. The physical park now stands for the whole session
## under `park_world.tscn`; this autoload only answers where in that park the
## player is.
##
## Keeping the existing signals and query methods lets the map, crowds, lights
## and development tools retain useful area context without giving any of them
## authority to create or destroy geometry.

const Plan := preload("res://scripts/park_plan.gd")

## The player has left one logical area. Nothing is freed.
signal section_leaving(from: StringName)

## The player is now in another logical area. Nothing is loaded or teleported.
signal section_entered(id: StringName)

## Compatibility signal for old corridor probes. Every built area is already
## resident, so this reports intent rather than beginning disk work.
signal section_preloading(id: StringName)

const SECTIONS := {
	&"plaza": {"name": "the plaza", "built": true},
	&"boardwalk": {"name": "the boardwalk", "built": true},
	&"terraces": {"name": "the terraces", "built": true},
}

## Area boundaries have hysteresis: crossing into a district takes a little
## more movement than remaining in it. Without that, standing on the midpoint
## of the west descent or east gate can emit an area change every other frame as
## the character capsule settles.
const BOARDWALK_ENTER_Y := (Plan.SHORE_TOP + 0.0) * 0.5
const BOARDWALK_LEAVE_Y := BOARDWALK_ENTER_Y + 0.75
const TERRACES_ENTER_X := Plan.EAST_SEAM_AT.x + 1.0
const TERRACES_LEAVE_X := Plan.EAST_SEAM_AT.x - 1.0

var _current: StringName = &"plaza"
var _player: Node3D = null
var _last_preload: StringName = &""


func _process(_delta: float) -> void:
	if not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as Node3D
	if _player == null:
		return
	_set_current(area_at(_player.global_position, _current))


## Which logical area contains the player.
func current() -> StringName:
	return _current


func section_name(id: StringName) -> String:
	if not SECTIONS.has(id):
		return ""
	return SECTIONS[id]["name"]


func is_built(id: StringName) -> bool:
	return SECTIONS.has(id) and bool(SECTIONS[id]["built"])


## The geometry is already in memory. Kept so an old preload trigger remains a
## harmless notification if a generated scene from before this conversion is
## opened on its own.
func begin_preload(id: StringName) -> void:
	if not is_built(id) or id == _current or id == _last_preload:
		return
	_last_preload = id
	section_preloading.emit(id)


func is_ready(id: StringName) -> bool:
	return is_built(id)


## Compatibility entry point for tools that used to request a scene swap.
## `from` and `hold` no longer affect the world: a direct call changes logical
## context only, with no fade, forced walk, teleport, mount or free.
func enter(id: StringName, _from: StringName = &"", _hold: Dictionary = {}) -> void:
	if not is_built(id):
		push_warning("areas: '%s' is not built" % id)
		return
	_set_current(id)


## Establish initial context for a hand-authored tree or a test harness.
func adopt(id: StringName) -> void:
	if not is_built(id):
		return
	_current = id
	_last_preload = &""


## Classify a point without mutating global state. Public because continuity
## tests and future audio/crowd zoning need the same boundary as the HUD.
func area_at(at: Vector3, previous: StringName = &"") -> StringName:
	if previous == &"boardwalk":
		if at.y < BOARDWALK_LEAVE_Y:
			return &"boardwalk"
	elif at.y < BOARDWALK_ENTER_Y:
		return &"boardwalk"

	if previous == &"terraces":
		if at.x > TERRACES_LEAVE_X:
			return &"terraces"
	elif at.x > TERRACES_ENTER_X:
		return &"terraces"

	return &"plaza"


## The crowd serving an area. All crowds now coexist, so callers must select by
## identity rather than taking whichever group member entered the tree first.
## Passing an id is useful to tests; ordinary play follows `current()`.
func current_crowd(id: StringName = &"") -> Node:
	var wanted := _current if id == &"" else id
	for crowd in get_tree().get_nodes_in_group("crowd"):
		if StringName(crowd.get("area_id")) == wanted:
			return crowd
	return null


func _set_current(id: StringName) -> void:
	if id == &"" or id == _current or not is_built(id):
		return
	var leaving := _current
	if leaving != &"":
		section_leaving.emit(leaving)
	_current = id
	_last_preload = &""
	section_entered.emit(id)
