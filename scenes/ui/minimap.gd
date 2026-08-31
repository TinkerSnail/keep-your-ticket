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
##
## **The colour is opaque and the transparency is `BAND_ALPHA`**, applied once
## to the whole network on the way out. See `_band`.
const PATH_BAND := Color(0.94, 0.91, 0.80)

## How far the paving is faded, as one number applied to the finished network
## rather than to each band as it is laid.
##
## It is the same 0.20 the band was drawn at before, and it has to be applied in
## one place: two 20% bands crossing compound to 36%, so paving drawn piece by
## piece puts a bright lozenge wherever two pieces meet. Every joint of every
## run is such a place, and the ring has twelve of them.
const BAND_ALPHA := 0.20

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

## The paving and the ink drawn on top of it, as their own canvases.
##
## **The paving is a `CanvasGroup`**, which is the whole of the fix for the
## segmented look. Its children are composited into one buffer first and the
## group is faded once, so a network of overlapping bands is a ribbon rather
## than a pile of translucent cards with a bright edge at every seam.
##
## Two layers rather than one because a `Control` draws before its children, and
## the ink goes on top of the paving: the ground disc is this node's own `_draw`,
## the paving is the group, and everything else is `_ink` above it.
var _band: CanvasGroup = null
var _band_ink: _Layer = null
var _ink: _Layer = null

## This frame's park, in screen coordinates: the walkways as clipped polylines,
## and whether there is a player to draw them around at all. Worked out once in
## `_process` because both layers want the same answer and neither owns it.
var _runs: Array = []
var _standing := false
var _at := Vector3.ZERO
var _yaw := 0.0


## A bare canvas that paints whatever it is handed.
##
## The minimap is three layers in a fixed order and only the bottom one can be a
## `Control._draw`. One class holding a `Callable` rather than a script file per
## layer — there is no state down here and nothing else will ever want them.
class _Layer extends Node2D:
	var paint: Callable

	func _draw() -> void:
		if paint.is_valid():
			paint.call()


func _ready() -> void:
	custom_minimum_size = Vector2(RADIUS * 2.0, RADIUS * 2.0)
	size = custom_minimum_size
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	ParkSections.section_entered.connect(_on_section_entered)

	_band = CanvasGroup.new()
	# `self_modulate` and not `modulate`: modulate propagates to children, which
	# would fade each band *before* the group composited them and put the
	# compounding straight back.
	_band.self_modulate = Color(1.0, 1.0, 1.0, BAND_ALPHA)
	add_child(_band)
	_band_ink = _Layer.new()
	_band_ink.paint = _paint_band
	_band.add_child(_band_ink)

	_ink = _Layer.new()
	_ink.paint = _paint_ink
	add_child(_ink)


## Redrawn every frame because it turns with the player, and the player turns
## every frame. There is nothing to cache — the transform is the whole drawing.
##
## The alpha is checked as well as the flag: the HUD fades this out rather than
## switching it off, so `visible` stays true the whole time the camera is up and
## a flag-only guard would redraw a fully transparent disc every frame.
func _process(_delta: float) -> void:
	if not (is_visible_in_tree() and modulate.a > 0.001):
		return
	_survey()
	queue_redraw()
	_band_ink.queue_redraw()
	_ink.queue_redraw()


func _on_section_entered(_id: StringName) -> void:
	# All crowds remain standing; the logical area decides which graph supplies
	# nearby points of interest.
	_crowd = null


func _centre() -> Vector2:
	return Vector2(RADIUS, RADIUS)


func _scale() -> float:
	return RADIUS / RANGE_M


## Cached, but re-found whenever the reference has gone stale. Tool harnesses
## may still build their trees in any order.
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
	# The ground only. Everything above it is a layer, because a `Control` draws
	# before its children and the paving has to be composited on its own.
	draw_circle(_centre(), RADIUS, GROUND)


## Where the player is, and the park in screen coordinates around them.
##
## Once a frame, up here, rather than in each layer: the two layers draw the
## same walkways at the same instant and a second projection pass is a second
## chance for them to disagree.
func _survey() -> void:
	_player = _find(&"player", _player) as Node3D
	_standing = _player != null
	_runs = []
	if not _standing:
		return
	if not is_instance_valid(_crowd):
		_crowd = ParkSections.current_crowd()
	_at = _player.global_position
	_yaw = _player.global_rotation.y

	for run in ParkPlan.walkway_runs():
		var points: Array = run["points"]
		var pieces := _clip_run(points)
		if pieces.is_empty():
			continue
		_runs.append({"pieces": pieces, "width": float(run["width"]) * _scale()})


## The park's walkways, as paving.
##
## Drawn at full strength into the `CanvasGroup`, which is what fades it — see
## `BAND_ALPHA`. Inside the buffer the bands may overlap as much as they like,
## so a junction is a junction rather than a bright patch, and a run is laid as
## one polyline with a disc at each joint rather than as a line per segment.
## Both of those were the segmented look: a butt cap notches the outside of
## every bend, and the ring turns twelve times.
##
## The discs are dropped within half a band of the rim. A joint out there is
## under the ring anyway, and a round cap on a fifteen-metre street would bulge
## past the edge of the disc — which is also what keeps the clipped ends square,
## since a clipped end sits exactly on the rim by construction.
func _paint_band() -> void:
	var centre := _centre()
	for run in _runs:
		var width: float = run["width"]
		var inside := RADIUS - width * 0.5
		for piece in run["pieces"]:
			_band_ink.draw_polyline(piece, PATH_BAND, width, true)
			for point in piece:
				if point.distance_to(centre) <= inside:
					_band_ink.draw_circle(point, width * 0.5, PATH_BAND, true, -1.0, true)


## The centre lines, the marks, the compass and you — everything that is drawn
## on the paving rather than being it.
func _paint_ink() -> void:
	for run in _runs:
		for piece in run["pieces"]:
			_ink.draw_polyline(piece, PATH, PATH_WIDTH, true)
	if _standing:
		_draw_pois()
		_draw_compass()
	_ink.draw_arc(_centre(), RADIUS, 0.0, TAU, 96, RING, RING_WIDTH, true)
	_draw_you()


## The things worth looking at, as diamonds. One symbol for all of them: the
## crowd does not distinguish kinds, and inventing kinds here would be a second
## opinion about the park that nothing else shares.
func _draw_pois() -> void:
	if _crowd == null:
		return
	var pois: PackedVector3Array = _crowd.get("pois")
	if pois == null:
		return
	for poi in pois:
		var screen := _project(poi, _at, _yaw)
		if screen.distance_to(_centre()) > RADIUS - POI_SIZE:
			continue
		var diamond := PackedVector2Array([
			screen + Vector2(0.0, -POI_SIZE), screen + Vector2(POI_SIZE, 0.0),
			screen + Vector2(0.0, POI_SIZE), screen + Vector2(-POI_SIZE, 0.0),
			screen + Vector2(0.0, -POI_SIZE),
		])
		_ink.draw_polyline(diamond, POI_COLOUR, 1.5, true)


## North filled, south hollow, both riding on the ring. North in the park is −Z,
## so on a heading-up map it sits at (sin yaw, −cos yaw) from the middle.
func _draw_compass() -> void:
	var north := Vector2(sin(_yaw), -cos(_yaw))
	_marker(north, NORTH_SIZE, ParkUI.ACCENT, true)
	_marker(-north, SOUTH_SIZE, RING, false)


func _marker(direction: Vector2, size: float, colour: Color, filled: bool) -> void:
	var at := _centre() + direction * RADIUS
	var along := direction * size
	var across := Vector2(-direction.y, direction.x) * size * 0.62
	var points := PackedVector2Array([at + along, at - along + across, at - along - across])
	if filled:
		_ink.draw_colored_polygon(points, colour)
	else:
		points.append(points[0])
		_ink.draw_polyline(points, colour, RING_WIDTH, true)


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
	_ink.draw_colored_polygon(points, ParkUI.ACCENT)
	var outline := points.duplicate()
	outline.append(points[0])
	_ink.draw_polyline(outline, ParkUI.INK, 1.5, true)


## One walkway, projected and clipped to the disc, as the polylines that survive.
##
## Per run and not per segment, and contiguous segments kept in one piece: the
## joints are the whole difference between a ribbon and a row of cards, and a
## consumer that is handed loose segments cannot tell which of them meet. A run
## that leaves the disc and comes back — the ring does, from anywhere but the
## middle — arrives as two pieces, which is correct: there is nothing to join
## across the gap.
func _clip_run(points: Array) -> Array:
	var pieces := []
	var piece := PackedVector2Array()
	for i in points.size() - 1:
		var from: Vector2 = points[i]
		var to: Vector2 = points[i + 1]
		var seg := _clip(
			_project(Vector3(from.x, 0.0, from.y), _at, _yaw),
			_project(Vector3(to.x, 0.0, to.y), _at, _yaw))
		if seg.is_empty():
			if piece.size() > 1:
				pieces.append(piece)
			piece = PackedVector2Array()
			continue
		# The previous segment carries on into this one only if it survived the
		# clip whole — a segment cut short at the rim ends there, and the next
		# one starts somewhere else on it.
		if not piece.is_empty() and piece[piece.size() - 1].distance_squared_to(seg[0]) < 0.01:
			piece.append(seg[1])
		else:
			if piece.size() > 1:
				pieces.append(piece)
			piece = PackedVector2Array([seg[0], seg[1]])
	if piece.size() > 1:
		pieces.append(piece)
	return pieces


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
