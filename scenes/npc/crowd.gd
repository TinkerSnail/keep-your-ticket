extends Node3D

## The plaza's crowd: a walkable graph, a list of things worth looking at, and
## the guests standing on both.
##
## This exists so that a guest does not have to know about the plaza and the
## plaza does not have to know about guests. Guests ask it where they may walk
## and what is worth a glance; it watches the player on their behalf, once,
## instead of thirty times a frame.
##
## The graph and the guests below it are generated — see `tools/gen_crowd.gd`.

## Flat pairs of node indices. Every edge is walkable in both directions, and
## the generator has already checked that nothing stands on it.
@export var nodes: PackedVector3Array = PackedVector3Array()
@export var edges: PackedInt32Array = PackedInt32Array()
## Points a guest might plausibly look at: the fountain, the sign, the
## bandstand, a lamp they are standing under. Height is part of the point —
## looking up at the sign tower is a different photograph than looking across.
@export var pois: PackedVector3Array = PackedVector3Array()

@export var route_hops := Vector2i(2, 5)

## How long a guest who has just noticed the camera stays worth noticing. The
## signal a neighbour picks up is the turn, not the staring that follows, so a
## chain can only hop while the last hop is still recent. That is what makes
## contagion a ripple that dies out rather than an alarm the whole plaza joins.
const ALERT_FRESHNESS := 1.3

var guests: Array = []
var camera_raised := false
var player_position := Vector3.ZERO
var player_eye := Vector3.ZERO

var _adjacency: Array[PackedInt32Array] = []
var _groups: Dictionary = {}
## Guests who noticed the camera recently enough to still be catching eyes,
## each with how long ago. Short — usually nobody, briefly a handful.
var _alerts: Array = []
var _player: Node3D = null
var _player_camera: Node3D = null
var _rng := RandomNumberGenerator.new()


## In `_enter_tree`, not `_ready`. Children run `_ready` before their parent, so
## a guest looking for the crowd in its own `_ready` finds nothing — every guest
## comes up with a null router, stands still forever, and looks like it is
## working because the generator scattered them across the plaza to begin with.
## `_enter_tree` runs parent-first, which is the order this needs.
func _enter_tree() -> void:
	add_to_group("crowd")


func _ready() -> void:
	_build_adjacency()
	call_deferred("_connect_player")


func _build_adjacency() -> void:
	_adjacency.resize(nodes.size())
	for i in nodes.size():
		_adjacency[i] = PackedInt32Array()
	var pairs := edges.size() / 2
	for p in pairs:
		var a := edges[p * 2]
		var b := edges[p * 2 + 1]
		if a < 0 or b < 0 or a >= nodes.size() or b >= nodes.size():
			push_warning("crowd: edge %d references a node that does not exist" % p)
			continue
		_adjacency[a].append(b)
		_adjacency[b].append(a)


func _connect_player() -> void:
	_player = get_tree().get_first_node_in_group("player") as Node3D
	if _player != null:
		_player_camera = _player.get_node_or_null("head/camera") as Node3D

	var camera_tool := get_tree().get_first_node_in_group("camera_tool")
	if camera_tool == null:
		push_warning("crowd: no camera_tool found — guests will never notice the camera")
		return
	camera_tool.raised_changed.connect(_on_camera_raised_changed)


func _on_camera_raised_changed(raised: bool) -> void:
	camera_raised = raised
	if not raised:
		_alerts.clear()


func _physics_process(_delta: float) -> void:
	_age_alerts(_delta)
	if _player == null:
		return
	player_position = _player.global_position
	player_eye = _player_camera.global_position if _player_camera != null \
		else player_position + Vector3.UP * 1.6


# --- the graph --------------------------------------------------------------


func node_position(index: int) -> Vector3:
	if index < 0 or index >= nodes.size():
		return Vector3.INF
	return nodes[index]


func nearest_node(point: Vector3) -> int:
	var best := -1
	var best_distance := INF
	for i in nodes.size():
		var d := point.distance_squared_to(nodes[i])
		if d < best_distance:
			best_distance = d
			best = i
	return best


## A wander rather than a path: pick a start, walk a few edges without doubling
## straight back. Guests are not going anywhere, so pathfinding would be a lie
## about their intentions as well as an expense.
func route_from(point: Vector3, route_seed: int) -> PackedInt32Array:
	var route := PackedInt32Array()
	var current := nearest_node(point)
	if current < 0:
		return route

	_rng.seed = route_seed
	var previous := -1
	var hops := _rng.randi_range(route_hops.x, route_hops.y)
	for _i in hops:
		var options := _adjacency[current]
		if options.is_empty():
			break
		var choices := PackedInt32Array()
		for option in options:
			if option != previous:
				choices.append(option)
		if choices.is_empty():
			choices = options
		var next := choices[_rng.randi_range(0, choices.size() - 1)]
		route.append(next)
		previous = current
		current = next
	return route


func poi_near(point: Vector3, radius: float) -> Vector3:
	var best := Vector3.INF
	var best_distance := radius * radius
	for poi in pois:
		var flat := Vector3(poi.x - point.x, 0.0, poi.z - point.z)
		var d := flat.length_squared()
		# Directly underfoot is not something anyone looks at.
		if d < 1.5 or d > best_distance:
			continue
		best_distance = d
		best = poi
	return best


# --- guests -----------------------------------------------------------------


func register(guest: Node) -> void:
	if guest in guests:
		return
	guests.append(guest)
	var id: int = guest.group_id
	if not _groups.has(id):
		_groups[id] = []
	_groups[id].append(guest)


func unregister(guest: Node) -> void:
	guests.erase(guest)
	var id: int = guest.group_id
	if _groups.has(id):
		_groups[id].erase(guest)


## Everyone in the same group except the guest asking. Singles get an empty
## list, which is the point of them.
func companions(guest: Node) -> Array:
	var group: Array = _groups.get(guest.group_id, [])
	var result: Array = []
	for other in group:
		if other != guest and is_instance_valid(other):
			result.append(other)
	return result


# --- noticing ---------------------------------------------------------------


## A guest reporting that they have just clocked the camera, whether they saw
## it themselves or caught it off somebody else. Both spread it onward — that
## is what makes it a chain rather than a single ring.
func report_notice(guest: Node) -> void:
	_alerts.append({"guest": guest, "age": 0.0})


func _age_alerts(delta: float) -> void:
	for i in range(_alerts.size() - 1, -1, -1):
		var alert: Dictionary = _alerts[i]
		alert.age += delta
		if alert.age > ALERT_FRESHNESS or not is_instance_valid(alert.guest):
			_alerts.remove_at(i)


## The nearest guest within `radius` who noticed recently enough to be worth
## noticing in turn, skipping any the asker has already shrugged off.
func fresh_alert_near(asker: Node3D, radius: float, declined: Array) -> Node:
	var best: Node = null
	var best_distance := radius * radius
	for alert in _alerts:
		var guest := alert.guest as Node3D
		if guest == null or guest == asker or not is_instance_valid(guest):
			continue
		if guest.get_instance_id() in declined:
			continue
		var d := asker.global_position.distance_squared_to(guest.global_position)
		if d > best_distance:
			continue
		best_distance = d
		best = guest
	return best


# --- interaction ------------------------------------------------------------


## The guest nearest the centre of the view, close enough to talk to. Look is
## the pointer: there is no cursor and no highlight, and the only feedback that
## someone is reachable is that they look back at you.
func interaction_candidate(from: Vector3, forward: Vector3, max_distance := 3.6,
		max_angle := deg_to_rad(28.0)) -> Node:
	var best: Node = null
	var best_angle := max_angle
	for entry in guests:
		var guest := entry as Node3D
		if guest == null or not is_instance_valid(guest):
			continue
		var to_guest := guest.global_position - from
		to_guest.y = 0.0
		var distance := to_guest.length()
		if distance > max_distance or distance < 0.01:
			continue
		var angle := forward.normalized().angle_to(to_guest / distance)
		if angle < best_angle:
			best_angle = angle
			best = guest
	return best


## Asking one guest asks the group they came with. Nobody in a park is
## photographed alone by accident.
func ask_to_pose(guest: Node, anchor: Vector3) -> int:
	if guest == null or not is_instance_valid(guest):
		return 0
	var asked := 1
	guest.ask_to_pose(anchor)
	for companion in companions(guest):
		if companion.global_position.distance_to(guest.global_position) > 9.0:
			continue
		companion.ask_to_pose(anchor)
		asked += 1
	return asked
