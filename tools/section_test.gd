extends Node

## Dev tool: verifies that the park is one continuous standing world.
##
## It walks the real player straight through both opposed plaza gates and back,
## watching for stalls, falls, transition control, or a frame-sized position
## jump. It also checks the composition itself: every canonical place exists,
## all three crowds are addressable, no section gate is mounted, and the two
## retired far scenes are gone.

const ARRIVE := 0.8
const MAX_SECONDS := 20.0
const STALL_FRAMES := 180
const MAX_FRAME_TRAVEL := 0.75
const FLOOR_LIMIT := -2.5

const ROUTES := [
	{
		"name": "west arch out",
		"from": Vector3(-27.0, 1.2, -2.0),
		"to": Vector3(-48.0, 1.2, -2.0),
	},
	{
		"name": "west arch back",
		"from": Vector3(-48.0, 1.2, -2.0),
		"to": Vector3(-27.0, 1.2, -2.0),
	},
	{
		"name": "east gate out",
		"from": Vector3(27.0, 1.2, -2.0),
		"to": Vector3(51.0, 1.2, -2.0),
		"area": &"terraces",
	},
	{
		"name": "east gate back",
		"from": Vector3(51.0, 1.2, -2.0),
		"to": Vector3(27.0, 1.2, -2.0),
		"area": &"plaza",
	},
]

const REQUIRED := [
	"places/plaza",
	"places/entrance",
	"places/thresholds",
	"places/west_shell",
	"places/west_stair",
	"places/boardwalk",
	"places/east_cascade",
	"shared/skyline",
	"shared/north_sky_ride",
	"shared/park_transit",
	"crowds/plaza_crowd",
	"crowds/boardwalk_crowd",
	"crowds/terraces_crowd",
]

var _player: CharacterBody3D = null
var _world: Node3D = null
var _route := 0
var _elapsed := 0.0
var _still := 0
var _last := Vector3.ZERO
var _max_step := 0.0
var _fails: Array[String] = []
var _notes: Array[String] = []


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in 8:
		await get_tree().physics_frame

	_player = get_tree().get_first_node_in_group("player") as CharacterBody3D
	_world = get_tree().root.find_child("park_world", true, false) as Node3D
	if _player == null:
		_fail("no player in the tree")
	if _world == null:
		_fail("no persistent park_world in the tree")
	if not _fails.is_empty():
		return _report()

	_check_composition()
	_check_area_context()
	_start_route()


func _check_composition() -> void:
	for path in REQUIRED:
		if _world.get_node_or_null(path) == null:
			_fail("park_world is missing %s" % path)

	if ResourceLoader.exists("res://scenes/world/west_far.tscn"):
		_fail("west_far.tscn still exists")
	if ResourceLoader.exists("res://scenes/world/terraces_far.tscn"):
		_fail("terraces_far.tscn still exists")

	var gate_script := load("res://scenes/world/section_gate.gd")
	_check_no_gate(_world, gate_script)

	for id in [&"plaza", &"boardwalk", &"terraces"]:
		var crowd := ParkSections.current_crowd(id)
		if crowd == null:
			_fail("no crowd tagged '%s'" % id)


func _check_no_gate(node: Node, gate_script: Script) -> void:
	if node.get_script() == gate_script:
		_fail("obsolete section gate is mounted at %s" % node.get_path())
	for child in node.get_children():
		_check_no_gate(child, gate_script)


func _check_area_context() -> void:
	var checks := [
		[Vector3.ZERO, &"plaza"],
		[Vector3(-96.0, ParkPlan.SHORE_TOP + 0.2, 0.0), &"boardwalk"],
		[Vector3(ParkPlan.EAST_SEAM_AT.x + 4.0, 0.2, -2.0), &"terraces"],
	]
	for check in checks:
		var got := ParkSections.area_at(check[0])
		if got != check[1]:
			_fail("area at %s is '%s', wanted '%s'" % [check[0], got, check[1]])


func _start_route() -> void:
	if _route >= ROUTES.size():
		return _report()
	var spec: Dictionary = ROUTES[_route]
	_player.global_position = spec["from"]
	_player.velocity = Vector3.ZERO
	var d: Vector3 = spec["to"] - spec["from"]
	_player.rotation.y = atan2(-d.x, -d.z)
	_elapsed = 0.0
	_still = 0
	_last = _player.global_position
	Input.action_press("move_forward")


func _physics_process(delta: float) -> void:
	if _player == null or _route >= ROUTES.size():
		return
	var spec: Dictionary = ROUTES[_route]
	var at := _player.global_position
	var step := at.distance_to(_last)
	_max_step = maxf(_max_step, step)
	if step > MAX_FRAME_TRAVEL:
		_fail("%s jumped %.2fm in one frame at %s" % [spec["name"], step, _fmt(at)])
		return _report()
	if _player.has_method("is_crossing") and _player.is_crossing():
		_fail("%s entered legacy transition control" % spec["name"])
		return _report()
	if at.y < FLOOR_LIMIT:
		_fail("%s fell through the gate floor at %s" % [spec["name"], _fmt(at)])
		return _report()

	_elapsed += delta
	if _elapsed > MAX_SECONDS:
		_fail("%s timed out at %s" % [spec["name"], _fmt(at)])
		return _report()

	if step < 0.004:
		_still += 1
		if _still > STALL_FRAMES:
			_fail("%s stalled at %s" % [spec["name"], _fmt(at)])
			return _report()
	else:
		_still = 0
	_last = at

	var target: Vector3 = spec["to"]
	if Vector2(at.x - target.x, at.z - target.z).length() > ARRIVE:
		return

	_release()
	if spec.has("area") and ParkSections.current() != spec["area"]:
		_fail("%s ended in logical area '%s', wanted '%s'"
			% [spec["name"], ParkSections.current(), spec["area"]])
	_notes.append("%s reached %s" % [spec["name"], _fmt(at)])
	_route += 1
	_start_route()


func _release() -> void:
	if Input.is_action_pressed("move_forward"):
		Input.action_release("move_forward")


func _fail(message: String) -> void:
	_fails.append(message)


func _fmt(v: Vector3) -> String:
	return "(%.1f, %.1f, %.1f)" % [v.x, v.y, v.z]


func _report() -> void:
	_release()
	print("--- continuous park ---")
	for note in _notes:
		print("  . %s" % note)
	print("  . largest one-frame movement: %.2fm" % _max_step)
	if _fails.is_empty():
		print("  ok: both gates are continuous and every canonical place remains standing")
	else:
		for failure in _fails:
			print("  FAIL: %s" % failure)
	get_tree().quit(0 if _fails.is_empty() else 1)
