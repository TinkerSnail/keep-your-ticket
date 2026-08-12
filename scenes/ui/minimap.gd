extends Control

## The corner minimap: paths, a few symbols, and which way is north.
##
## Heading-up rather than north-up. The player sits at the middle pointing at
## the top of the screen and the park turns underneath them, which is why the
## compass needle on the ring is not decoration — it is the only thing telling
## you which way you are facing, and it is the piece that keeps the minimap from
## quietly replacing the skill of knowing the park. You still have to look up to
## find the sign tower; this tells you the paths are there.
##
## Symbolic and deliberately thin. Outlines for the ways through, a mark for the
## things worth looking at, a wedge for you. No labels, no icons per building,
## no guests — a dot per guest would turn photographing people into reading a
## radar, which is the failure mode this shape has.
##
## **The geometry is not authored here.** The walkways come from `ParkPlan`,
## which is the park's own layout — centre lines and paved widths in metres,
## derived from the built geometry rather than from anything's opinion of it.
## The marks come off the section's crowd, which carries the list of things
## worth looking at.
##
## This drew the crowd's walkable graph first and it was wrong: that graph is
## authored as a *wander* graph for guests to meander along, not as a drawable
## path network, and it read as a wireframe web. Worth keeping in mind — the
## routes people take and the paving they take them on are different objects,
## and they disagree in at least one place on purpose. There is no through-route
## on the plaza's south side in the crowd graph, because the benches and
## planters leave no gap wide enough for a guest to be routed through; a person
## can walk it. So the minimap showing paving where guests never go is correct.

## How much park is inside the ring, as a radius in metres. The plaza is 80m
## across, so this shows most of it and not all: enough to see where the ways
## out are from the middle, not enough to make walking to one unnecessary.
const RANGE_M := 21.0

## Drawn at a fixed size rather than scaling with the window. A minimap that
## grows on a big monitor shows more park for free.
const RADIUS := 92.0
const MARGIN := 10.0

## The ring, the ground inside it, and the ink on it. Deliberately close to the
## foldout's paper so the two read as the same park drawn twice — but darker and
## more transparent, because this one sits over the game rather than replacing
## it and a bright disc in the corner would pull the eye off the photograph.
const GROUND := Color(0.09, 0.12, 0.20, 0.72)
const RING := Color(0.85, 0.80, 0.66, 0.95)

## The paths are the bright thing, and everything else defers to them. This is
## the lesson off the PS1 racing minimaps: the route is drawn like a lit track
## and the rest of the disc is almost empty, so it reads in the quarter-second
## it actually gets looked at. The first pass had the marks brighter than the
## paths and it was a field of diamonds with some lines behind them.
const PATH := Color(0.94, 0.91, 0.80, 0.92)
const PATH_WIDTH := 2.2

## Every route is drawn twice: a wide dim band first, then the bright hairline
## down the middle of it. That is what turns a wireframe into something that
## reads as ground you can walk on — one line per edge is a diagram of a graph,
## and a band with a centre line is a path. Straight off the racing minimaps,
## where the track is a lit ribbon rather than a polyline.
## The band is drawn at the run's real paved width rather than at a fixed
## thickness, so a pinched route looks pinched. `spoke_south` is narrowed to
## five metres where it threads between the benches, and that should read as
## tight on here rather than as the same corridor as everything else.
const PATH_BAND := Color(0.94, 0.91, 0.80, 0.20)

const RING_WIDTH := 2.0

## North is a filled wedge on the ring; south is a hollow tick opposite it. Two
## marks rather than one, because a single needle is ambiguous the moment the
## player turns far enough that it is near the bottom.
const NORTH_SIZE := 7.0
const SOUTH_SIZE := 4.5

## The player, at the middle, always pointing at the top. The only other thing
## on the disc allowed to be gold, and bigger than the marks so it survives
## standing on top of one.
const YOU_SIZE := 8.5

## Things worth looking at, as small hollow diamonds. Hollow and dim rather than
## filled and gold: there are two dozen of them in the plaza and at full
## strength they were the whole minimap. They are a texture that says "there is
## something over there", not a set of destinations.
const POI_SIZE := 3.0
const POI_COLOUR := Color(0.94, 0.91, 0.80, 0.5)

var _crowd: Node = null
var _player: Node3D = null


func _ready() -> void:
	custom_minimum_size = Vector2(RADIUS * 2.0, RADIUS * 2.0)
	size = custom_minimum_size
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	ParkSections.section_entered.connect(_on_section_entered)


## Redrawn every frame because it turns with the player, and the player turns
## every frame. There is nothing to cache — the transform is the whole drawing.
##
## The alpha is checked as well as the flag: the HUD fades this out rather than
## switching it off, so `visible` stays true the whole time the camera is up and
## a flag-only guard would redraw a fully transparent disc every frame.
func _process(_delta: float) -> void:
	if is_visible_in_tree() and modulate.a > 0.001:
		queue_redraw()


func _on_section_entered(_id: StringName) -> void:
	# The crowd belongs to the section and is thrown away with it, so the cached
	# reference has to go at the seam rather than being checked for validity
	# every frame forever.
	_crowd = null


func _centre() -> Vector2:
	return Vector2(RADIUS, RADIUS)


func _scale() -> float:
	return RADIUS / RANGE_M


## Cached, but re-found whenever the reference has gone stale — a section swap
## frees the old crowd, and a tool harness may build its tree in any order.
func _find(group: StringName, cached: Node) -> Node:
	if is_instance_valid(cached):
		return cached
	return get_tree().get_first_node_in_group(group)


## World to minimap. Heading-up: the player's facing becomes screen-up, so the
## whole park rotates by the negative of their yaw.
##
## A `Node3D` looks down its own −Z, so forward is (−sin y, −cos y) in the
## ground plane and right is (cos y, −sin y). Screen y runs down, hence the
## negated forward component.
func _project(point: Vector3, at: Vector3, yaw: float) -> Vector2:
	var d := Vector2(point.x - at.x, point.z - at.z)
	var forward := Vector2(-sin(yaw), -cos(yaw))
	var right := Vector2(cos(yaw), -sin(yaw))
	return _centre() + Vector2(d.dot(right), -d.dot(forward)) * _scale()


func _draw() -> void:
	var centre := _centre()
	draw_circle(centre, RADIUS, GROUND)

	_player = _find(&"player", _player) as Node3D
	if _player != null:
		_crowd = _find(&"crowd", _crowd)
		var at := _player.global_position
		var yaw := _player.global_rotation.y
		_draw_paths(at, yaw)
		_draw_pois(at, yaw)
		_draw_compass(yaw)

	draw_arc(centre, RADIUS, 0.0, TAU, 64, RING, RING_WIDTH)
	_draw_you()


## The park's walkways, as paving with a centre line down it.
##
## Collected once and drawn in two full passes rather than banding and lining
## each run as it is found — otherwise a later run's paving paints over an
## earlier run's centre line and every junction comes out with a hole in it.
func _draw_paths(at: Vector3, yaw: float) -> void:
	var paving: Array = []
	for run in ParkPlan.walkway_segments():
		var from: Vector2 = run["from"]
		var to: Vector2 = run["to"]
		var clipped := _clip(
			_project(Vector3(from.x, 0.0, from.y), at, yaw),
			_project(Vector3(to.x, 0.0, to.y), at, yaw))
		if clipped.is_empty():
			continue
		paving.append({"seg": clipped, "width": float(run["width"]) * _scale()})

	for run in paving:
		var seg: PackedVector2Array = run["seg"]
		draw_line(seg[0], seg[1], PATH_BAND, run["width"])
	for run in paving:
		var seg: PackedVector2Array = run["seg"]
		draw_line(seg[0], seg[1], PATH, PATH_WIDTH)


## The things worth looking at, as diamonds. One symbol for all of them: the
## crowd does not distinguish kinds, and inventing kinds here would be a second
## opinion about the park that nothing else shares.
func _draw_pois(at: Vector3, yaw: float) -> void:
	if _crowd == null:
		return
	var pois: PackedVector3Array = _crowd.get("pois")
	if pois == null:
		return
	for poi in pois:
		var screen := _project(poi, at, yaw)
		if screen.distance_to(_centre()) > RADIUS - POI_SIZE:
			continue
		var diamond := PackedVector2Array([
			screen + Vector2(0.0, -POI_SIZE), screen + Vector2(POI_SIZE, 0.0),
			screen + Vector2(0.0, POI_SIZE), screen + Vector2(-POI_SIZE, 0.0),
			screen + Vector2(0.0, -POI_SIZE),
		])
		draw_polyline(diamond, POI_COLOUR, 1.5)


## North filled, south hollow, both riding on the ring. North in the park is −Z,
## so on a heading-up map it sits at (sin yaw, −cos yaw) from the middle.
func _draw_compass(yaw: float) -> void:
	var north := Vector2(sin(yaw), -cos(yaw))
	_marker(north, NORTH_SIZE, ParkUI.ACCENT, true)
	_marker(-north, SOUTH_SIZE, RING, false)


func _marker(direction: Vector2, size: float, colour: Color, filled: bool) -> void:
	var at := _centre() + direction * RADIUS
	var along := direction * size
	var across := Vector2(-direction.y, direction.x) * size * 0.62
	var points := PackedVector2Array([at + along, at - along + across, at - along - across])
	if filled:
		draw_colored_polygon(points, colour)
	else:
		points.append(points[0])
		draw_polyline(points, colour, RING_WIDTH)


## You, at the middle, always pointing up. Drawn last so nothing overlaps it,
## and outlined in ink so it survives sitting on top of a path.
func _draw_you() -> void:
	var centre := _centre()
	var points := PackedVector2Array([
		centre + Vector2(0.0, -YOU_SIZE * 1.25),
		centre + Vector2(YOU_SIZE * 0.8, YOU_SIZE * 0.9),
		centre + Vector2(0.0, YOU_SIZE * 0.35),
		centre + Vector2(-YOU_SIZE * 0.8, YOU_SIZE * 0.9),
	])
	draw_colored_polygon(points, ParkUI.ACCENT)
	var outline := points.duplicate()
	outline.append(points[0])
	draw_polyline(outline, ParkUI.INK, 1.5)


## Clip a segment to the disc, so a path running out of range stops at the ring
## instead of being drawn across the game or dropped entirely. Returns the two
## surviving endpoints, or nothing if the segment misses the disc.
##
## Solving |a + t(b − a) − c|² = r² for t and keeping the part of [0, 1] inside.
func _clip(a: Vector2, b: Vector2) -> PackedVector2Array:
	var centre := _centre()
	var d := b - a
	var f := a - centre
	var aa := d.dot(d)
	if aa < 0.0001:
		# A zero-length edge. Two graph nodes at the same place is a generator
		# bug rather than something to draw, but it must not divide by zero.
		return PackedVector2Array()

	var bb := 2.0 * f.dot(d)
	var cc := f.dot(f) - RADIUS * RADIUS
	var disc := bb * bb - 4.0 * aa * cc
	if disc < 0.0:
		return PackedVector2Array()

	var root := sqrt(disc)
	var t0 := maxf((-bb - root) / (2.0 * aa), 0.0)
	var t1 := minf((-bb + root) / (2.0 * aa), 1.0)
	if t0 >= t1:
		return PackedVector2Array()
	return PackedVector2Array([a + d * t0, a + d * t1])
