extends Control

## The park map: an illustrated bird's-eye with the buildings standing up on it.
##
## This is what a park foldout has always actually looked like — Disneyland's own
## maps are drawn exactly this way, a low-angle plan with tiny buildings and ride
## pieces sitting on it rather than a flat floorplan. So the dimensional
## treatment and the paper identity are not in tension: illustrated massing *is*
## the period-correct thing for a printed park map, and it is also what makes the
## screen fun to look at, which is the other reason it is here.
##
## North stays up and nothing is rotated 45°. The plan is squashed vertically as
## if seen from a low angle to the south, and everything with height rises
## straight up the screen — an oblique projection, which is both the cheapest and
## the one that keeps the compass honest. A proper isometric would turn the park
## on the page and make "the gate is south" something you have to work out.
##
## Not to scale, and deliberately. The corner minimap is to scale, rotates, and
## says where you are standing; this one is stylized, fixed, and says what the
## park is. Two readouts, two jobs — see `minimap.gd`.
##
## Everything is in map units on a 100 × 100 sheet, scaled to whatever box it is
## given. Bearings match the park: gate south, boardwalk west, and the four
## scaffolded thresholds at the angles `plaza.tscn` puts them.

const SHEET := 100.0

## The plaza, at the middle, because the design's whole claim is that the park is
## a hub with spokes and a map that does not show that is not showing the park.
const PLAZA_AT := Vector2(52.0, 50.0)
const PLAZA_HALF := 13.0

## The four passages that bend and stop. Derived from `ParkPlan` rather than
## written out: they were a literal `[342.0, 62.0, 121.0, 211.0]` here, which
## was a fourth copy of the same four angles and a drift bug waiting to happen —
## move a passage in the world and this map would have gone on pointing at where
## it used to be, silently and forever.
##
## Cached because `_draw` runs every frame while the tab is up and this does not
## change while the game is running.
var _bearings: Array = []


func _threshold_bearings() -> Array:
	if _bearings.is_empty():
		for threshold in ParkPlan.THRESHOLDS:
			var at: Vector3 = threshold["at"]
			_bearings.append(ParkPlan.bearing_to(Vector2(at.x, at.z)))
	return _bearings

## The obliquity. The plan is flattened to this fraction of its depth and the
## whole thing scaled back up, so the sheet stays filled rather than gaining two
## empty bands. Heights are then drawn straight up the screen, unflattened, which
## is what makes a two-unit building read as taller than a two-unit alley is wide.
const TILT := 0.78
const SPREAD := 1.08

## Ink weights. Three, and no more.
const LINE_HEAVY := 3.0
const LINE_MID := 2.0
const LINE_FINE := 1.0

const MARGIN := 5.0

## Type sizes, as heights on the sheet.
const TYPE_TITLE := 4.6
const TYPE_PLACE := 3.4
const TYPE_SMALL := 2.4

## Paper, ink, and the printed colours. Roofs are lighter than walls by a fixed
## amount rather than per building, so the whole park is lit from one direction
## and nothing has to be re-tinted when a block moves.
const PAPER := Color("f2e6c4")
const PAPER_LINE := Color("7a6a49")
const INK := Color("14110c")
const WATER := Color("9fc9d9")
const GROUND_PLAZA := Color("f0d99a")
const GROUND_STREET := Color("e6d3a8")
const GROUND_DECK := Color("dcbb8c")
const ROOF := Color("d9c197")
const WALL := Color("ab9068")
const ROOF_WARM := Color("d9a97a")
const WALL_WARM := Color("a87b52")
const STEEL := Color("b9bcc0")

## The places the cursor can sit on. Not a fast-travel list and never will be —
## selecting one names it and says what is there. Walking to it is still the game.
##
## The four unmarked ones are the scaffolded thresholds and their note is the
## honest one, for the same reason `park_sections.gd` leaves them out of its
## table: naming them would be inventing park content ahead of the design.
const PLACES := [
	{"id": &"plaza", "at": Vector2(52.0, 50.0), "label": "The Plaza",
		"note": "The hub. Six ways out of it, and the photo hut."},
	{"id": &"boardwalk", "at": Vector2(19.5, 47.0), "label": "The Boardwalk",
		"note": "West, down the stair past the gate. Scaffolding for now."},
	{"id": &"gate", "at": Vector2(52.0, 86.0), "label": "Main Gate",
		"note": "The way in, and the way home."},
	{"id": &"north", "at": Vector2(0.0, 342.0), "label": "Unmarked, north",
		"note": "The passage bends and stops. Nothing built past it yet."},
	{"id": &"east", "at": Vector2(0.0, 62.0), "label": "Unmarked, east",
		"note": "The passage bends and stops. Nothing built past it yet."},
	{"id": &"south_east", "at": Vector2(0.0, 121.0), "label": "Unmarked, south-east",
		"note": "The passage bends and stops. Nothing built past it yet."},
	{"id": &"south_west", "at": Vector2(0.0, 211.0), "label": "Unmarked, south-west",
		"note": "The passage bends and stops. Nothing built past it yet."},
]

## A place whose `at.x` is zero is a bearing from the plaza in `at.y` rather than
## a point — the thresholds are defined that way everywhere else and writing them
## out here by hand would be a fourth copy of the same four angles.
const BEARING_PLACE := 0.0

## The marker over where you are: a pyramid that turns and bobs.
const SPIN_SECONDS := 1.6
const BOB_SECONDS := 2.1
const MARKER_W := 4.0
const MARKER_H := 5.0
const MARKER_LIFT := 9.0
const BOB_AMOUNT := 0.9

## The cursor on the selected place: brackets that breathe. A different shape
## from the marker on purpose — one is where you are, the other is where you are
## pointing, and a screen where those look alike is one you have to think about.
const CURSOR_R := 5.6
const CURSOR_PULSE := 0.55

## The wheel turns. Slowly, because a big wheel does.
const WHEEL_SECONDS := 14.0

signal note_changed(note: String)

var _face: Font
var _selected := 0
var _phase := 0.0


func _ready() -> void:
	if not ParkSections.section_entered.is_connected(_on_section_entered):
		ParkSections.section_entered.connect(_on_section_entered)


func _on_section_entered(_id: StringName) -> void:
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


## The tree is paused while this is up, but the menu runs regardless and this is
## a descendant of it, so the marker keeps turning and the wheel keeps going.
## That is the point: a paused screen with nothing moving on it reads as a hang.
func _process(delta: float) -> void:
	if not is_visible_in_tree():
		return
	_phase += delta
	queue_redraw()


func _input(event: InputEvent) -> void:
	if not is_visible_in_tree():
		return
	var step := 0
	if event.is_action_pressed("ui_right", true) or event.is_action_pressed("ui_down", true):
		step = 1
	elif event.is_action_pressed("ui_left", true) or event.is_action_pressed("ui_up", true):
		step = -1
	if step == 0:
		return
	_selected = wrapi(_selected + step, 0, PLACES.size())
	accept_event()
	_announce()
	queue_redraw()


## Name and note go to the menu's note line rather than onto the sheet, so the
## map keeps its printed lettering and the interface keeps its commentary. A live
## caption in the middle of a paper map would undo both.
func _announce() -> void:
	var place: Dictionary = PLACES[_selected]
	note_changed.emit("%s — %s" % [place["label"], place["note"]])


func _on_shown() -> void:
	# Opening the tab puts the cursor where the player actually is, which is the
	# one selection that never has to be explained.
	for index in PLACES.size():
		if PLACES[index]["id"] == ParkSections.current():
			_selected = index
			break
	_announce()
	queue_redraw()


# --- projection --------------------------------------------------------------

## Sheet to pixels, square and centred. This is the *paper*: the border, the
## cartouche and the compass use it, and they do not tilt, because they are
## printed on the sheet rather than standing on the ground.
func _place() -> Transform2D:
	var box := size
	var scale := minf(box.x, box.y) / SHEET
	var offset := (box - Vector2(SHEET, SHEET) * scale) * 0.5
	return Transform2D(0.0, Vector2(scale, scale), 0.0, offset)


func _at(point: Vector2) -> Vector2:
	return _place() * point


func _len(units: float) -> float:
	return units * _place().get_scale().x


## Ground plane. Squashed towards the sheet's middle and spread back out, which
## is the whole of the oblique projection — everything on the park's floor goes
## through here.
func _ground(point: Vector2) -> Vector2:
	var centre := Vector2(SHEET, SHEET) * 0.5
	return _at(centre + Vector2(
		(point.x - centre.x) * SPREAD,
		(point.y - centre.y) * TILT * SPREAD))


## A point `height` units above the ground at `point`. Straight up the screen and
## not flattened, so height reads as height rather than as depth.
func _rise(point: Vector2, height: float) -> Vector2:
	return _ground(point) - Vector2(0.0, _len(height))


## A point at a compass bearing from the plaza, on the plan before tilting. North
## is up and bearings run clockwise, which is what a compass does and not what
## atan2 does.
func _bearing(degrees: float, distance: float) -> Vector2:
	var radians := deg_to_rad(degrees)
	return PLAZA_AT + Vector2(sin(radians), -cos(radians)) * distance


func _place_at(place: Dictionary) -> Vector2:
	var at: Vector2 = place["at"]
	if is_equal_approx(at.x, BEARING_PLACE):
		return _bearing(at.y, PLAZA_HALF + 9.0)
	return at


# --- drawing -----------------------------------------------------------------

## North to south, so that nearer things overlap farther ones. With an oblique
## projection and no depth buffer, draw order *is* the depth, and getting it
## wrong shows up as a building standing in front of the one south of it.
func _draw() -> void:
	_draw_paper()
	_draw_water()
	_draw_skyline()
	_draw_thresholds()
	_draw_boardwalk()
	_draw_plaza_ground()
	_draw_plaza_pieces()
	_draw_entrance()
	_draw_compass()
	_draw_cartouche()
	# Last, over the printed sheet. The two things here that are not paper.
	_draw_places()


## The stock, with a heavy border and a fold crease. The crease is one line and
## does more than any other mark — it is the difference between a map and a sheet
## that has been in somebody's back pocket.
func _draw_paper() -> void:
	var sheet := Rect2(_at(Vector2.ZERO), _at(Vector2(SHEET, SHEET)) - _at(Vector2.ZERO))
	draw_rect(sheet, PAPER, true)
	draw_rect(sheet, INK, false, LINE_HEAVY)
	draw_line(_at(Vector2(SHEET * 0.5, 0.0)), _at(Vector2(SHEET * 0.5, SHEET)),
		Color(PAPER_LINE, 0.30), LINE_FINE)


func _draw_water() -> void:
	var edge := PackedVector2Array()
	for point in [Vector2(MARGIN, MARGIN), Vector2(15.0, MARGIN), Vector2(13.0, 30.0),
			Vector2(15.0, 62.0), Vector2(12.0, SHEET - MARGIN), Vector2(MARGIN, SHEET - MARGIN)]:
		edge.append(_ground(point))
	draw_colored_polygon(edge, WATER)
	draw_polyline(edge, PAPER_LINE, LINE_FINE)


## The things outside the walls that you can see from inside them and never
## reach: the coaster north-east and the observation tower. They are drawn small
## and pale, at the top of the sheet, because that is where they are and because
## a map that draws them as boldly as the plaza would be promising a ride.
func _draw_skyline() -> void:
	# The coaster: a lift hill and two drops, north-east.
	var track := PackedVector2Array()
	var profile := [
		[Vector2(70.0, 26.0), 0.0], [Vector2(74.0, 26.0), 9.0], [Vector2(78.0, 26.0), 2.0],
		[Vector2(82.0, 26.0), 6.5], [Vector2(86.0, 26.0), 1.0],
	]
	for entry in profile:
		track.append(_rise(entry[0], entry[1]))
	draw_polyline(track, Color(INK, 0.55), LINE_MID)
	for entry in profile:
		draw_line(_ground(entry[0]), _rise(entry[0], entry[1]), Color(INK, 0.28), LINE_FINE)

	# The observation tower, north of the plaza.
	var tower := Vector2(64.0, 20.0)
	draw_line(_ground(tower), _rise(tower, 13.0), Color(INK, 0.55), LINE_MID)
	_disc(tower, 11.0, 2.6, Color(STEEL, 0.75))


## The four passages in the plaza wall that go a little way and stop. Dashed, and
## capped with an open circle rather than a destination.
func _draw_thresholds() -> void:
	for bearing in _threshold_bearings():
		var from := _bearing(bearing, PLAZA_HALF)
		var to := _bearing(bearing, PLAZA_HALF + 9.0)
		_dashed(from, to, PAPER_LINE, LINE_MID)
		_ellipse(to, 1.7, PAPER, PAPER_LINE)


## The boardwalk: the deck, the frontage along its back, the pier out over the
## water, and the wheel. The wheel is the one thing on this map that turns.
func _draw_boardwalk() -> void:
	var standing := ParkSections.current() == &"boardwalk"
	_slab(Vector2(15.0, 30.0), Vector2(24.0, 68.0),
		Color("e8c76a") if standing else GROUND_DECK)

	# The frontage, one building deep along the back of the deck.
	for i in 4:
		var y := 33.0 + float(i) * 8.5
		_block(Vector2(22.0, y), Vector2(25.5, y + 6.0), 3.4 + float(i % 2) * 1.2,
			ROOF_WARM, WALL_WARM)

	# The pier, running out over the water on its legs.
	_slab(Vector2(6.0, 45.5), Vector2(16.0, 48.5), GROUND_DECK)
	for i in 4:
		var leg := Vector2(7.5 + float(i) * 2.4, 48.5)
		draw_line(_ground(leg), _rise(leg, -1.6), Color(INK, 0.4), LINE_FINE)

	# The wheel, standing on its edge and turning. Drawn in the screen plane
	# rather than on the ground — a wheel is vertical, and flattening it with the
	# rest of the plan would lay it down flat like a roundabout.
	var hub := _rise(Vector2(19.5, 38.0), 5.2)
	var radius := _len(5.0)
	draw_line(_ground(Vector2(19.5, 38.0)), hub, INK, LINE_MID)
	draw_arc(hub, radius, 0.0, TAU, 40, INK, LINE_MID)
	var turn := _phase * TAU / WHEEL_SECONDS
	for i in 8:
		var a := turn + float(i) * TAU / 8.0
		var rim := hub + Vector2(cos(a), sin(a)) * radius
		draw_line(hub, rim, Color(INK, 0.5), LINE_FINE)
		draw_circle(rim, _len(0.7), ROOF_WARM)
		draw_arc(rim, _len(0.7), 0.0, TAU, 10, INK, LINE_FINE)

	_label("BOARDWALK", _ground(Vector2(19.5, 72.5)), TYPE_PLACE, INK)


func _draw_plaza_ground() -> void:
	var standing := ParkSections.current() == &"plaza"
	_slab(PLAZA_AT - Vector2(PLAZA_HALF, PLAZA_HALF), PLAZA_AT + Vector2(PLAZA_HALF, PLAZA_HALF),
		Color("f7d98a") if standing else GROUND_PLAZA, LINE_HEAVY)


## The plaza's four landmarks, north to south. These are what the player actually
## navigates by, and the sign tower most of all — it carries the clock, which is
## the only readout the time gets, so leaving it off would be leaving off the one
## thing worth walking towards.
func _draw_plaza_pieces() -> void:
	# The perimeter buildings, as a ring of small blocks with the ways out left
	# as gaps. Drawn before the things in the middle so the middle sits in front.
	for i in 12:
		var a := float(i) * TAU / 12.0 + 0.26
		var at := PLAZA_AT + Vector2(sin(a), -cos(a)) * (PLAZA_HALF + 2.4)
		_block(at - Vector2(2.6, 1.7), at + Vector2(2.6, 1.7), 3.0 + float(i % 3), ROOF, WALL)

	# The bandstand, north-west: a drum with a cone on it.
	var band := PLAZA_AT + Vector2(-7.0, -6.0)
	_ellipse(band, 2.8, ROOF, INK)
	draw_line(_ground(band), _rise(band, 3.2), INK, LINE_FINE)
	_cone(band, 3.2, 3.4, ROOF_WARM)

	# The sign tower, north-east, with the clock face near the top.
	var tower := PLAZA_AT + Vector2(7.5, -7.0)
	_block(tower - Vector2(1.1, 0.8), tower + Vector2(1.1, 0.8), 9.0, ROOF, WALL)
	var face := _rise(tower, 9.6)
	draw_circle(face, _len(1.7), PAPER)
	draw_arc(face, _len(1.7), 0.0, TAU, 20, INK, LINE_MID)
	draw_line(face, face + Vector2(0.0, -_len(1.1)), INK, LINE_FINE)
	draw_line(face, face + Vector2(_len(0.8), 0.0), INK, LINE_FINE)

	# The fountain, in the middle.
	_ellipse(PLAZA_AT, 3.2, WATER, INK)
	draw_line(_ground(PLAZA_AT), _rise(PLAZA_AT, 2.4), Color(WATER.darkened(0.2), 0.9), LINE_MID)

	# The photo hut, south-east. The job, and the only building on this map the
	# player works out of, so it gets the accent.
	var hut := PLAZA_AT + Vector2(6.5, 6.0)
	_block(hut - Vector2(2.4, 1.6), hut + Vector2(2.4, 1.6), 3.2,
		ParkUI.ACCENT, ParkUI.ACCENT.darkened(0.35))
	_label("PHOTO", _ground(hut + Vector2(0.0, 4.6)), TYPE_SMALL, INK)

	_label("THE PLAZA", _ground(PLAZA_AT + Vector2(0.0, -PLAZA_HALF - 8.5)), TYPE_PLACE, INK)


## South to the gate: the street, its shopfronts, the turnstiles, the apron.
func _draw_entrance() -> void:
	_slab(Vector2(PLAZA_AT.x - 5.0, PLAZA_AT.y + PLAZA_HALF), Vector2(PLAZA_AT.x + 5.0, 84.0),
		GROUND_STREET)

	for i in 3:
		var y := 66.0 + float(i) * 6.0
		_block(Vector2(PLAZA_AT.x - 9.0, y), Vector2(PLAZA_AT.x - 5.2, y + 4.4),
			3.0 + float(i % 2), ROOF_WARM, WALL_WARM)
		_block(Vector2(PLAZA_AT.x + 5.2, y), Vector2(PLAZA_AT.x + 9.0, y + 4.4),
			3.4 - float(i % 2), ROOF_WARM, WALL_WARM)

	# The turnstiles, as a row of posts across the foot of the street.
	for step in 5:
		var post := Vector2(PLAZA_AT.x - 4.0 + float(step) * 2.0, 84.5)
		draw_line(_ground(post), _rise(post, 1.8), INK, LINE_MID)

	_label("MAIN GATE", _ground(Vector2(PLAZA_AT.x, 91.0)), TYPE_PLACE, INK)


## North, and the one mark saying the map is not aligned to your heading. It is
## not: a paper map has a fixed north, and turning yourself to match it is the
## small skill it is worth having for.
func _draw_compass() -> void:
	var at := Vector2(SHEET - 13.0, 14.0)
	draw_arc(_at(at), _len(6.0), 0.0, TAU, 32, INK, LINE_MID)
	draw_line(_at(at + Vector2(0, 4.5)), _at(at + Vector2(0, -4.5)), INK, LINE_HEAVY)
	draw_colored_polygon(PackedVector2Array([
		_at(at + Vector2(0.0, -6.0)), _at(at + Vector2(-1.8, -2.6)), _at(at + Vector2(1.8, -2.6)),
	]), INK)
	_label("N", _at(at + Vector2(0.0, -8.6)), TYPE_PLACE, INK)


func _draw_cartouche() -> void:
	var at := Vector2(24.0, 12.0)
	_label("VISITOR MAP", _at(at), TYPE_TITLE, INK)
	_label("KEEP YOUR TICKET", _at(at + Vector2(0.0, 6.0)), TYPE_PLACE, PAPER_LINE)


func _draw_places() -> void:
	_draw_cursor(_place_at(PLACES[_selected]))
	# The marker goes over the section the player is standing in, not their exact
	# position. The corner minimap says where you are standing; this says which
	# part of the park that is.
	for place in PLACES:
		if place["id"] == ParkSections.current():
			_draw_marker(_place_at(place))
			return


func _draw_cursor(at: Vector2) -> void:
	var pulse := 1.0 + sin(_phase * TAU / CURSOR_PULSE) * 0.07
	var radius := _len(CURSOR_R) * pulse
	var centre := _ground(at)
	var arm := radius * 0.52
	for sx in [-1.0, 1.0]:
		for sy in [-1.0, 1.0]:
			var corner := centre + Vector2(sx * radius, sy * radius * TILT)
			draw_line(corner, corner - Vector2(sx * arm, 0.0), INK, LINE_MID)
			draw_line(corner, corner - Vector2(0.0, sy * arm * TILT), INK, LINE_MID)


## The spinning pyramid over where you are.
##
## Nothing rotates. The silhouette of a pyramid turning about its own vertical
## axis is a triangle whose base widens and narrows, split by the near vertical
## edge sliding across it — so two faces either side of a moving seam, one lit
## and one shaded, is the whole trick. It is how these were done at the time and
## it costs four points.
func _draw_marker(at: Vector2) -> void:
	var spin := _phase * TAU / SPIN_SECONDS
	var bob := sin(_phase * TAU / BOB_SECONDS) * _len(BOB_AMOUNT)

	var apex := _rise(at, MARKER_LIFT + MARKER_H) + Vector2(0.0, bob)
	var base_y := apex.y + _len(MARKER_H)
	# Never quite edge-on: a pyramid collapsing to a line every half turn reads
	# as a flicker rather than as a solid.
	var half := _len(MARKER_W) * 0.5 * (0.55 + 0.45 * absf(cos(spin)))
	var seam := Vector2(apex.x + sin(spin) * half, base_y)

	draw_colored_polygon(PackedVector2Array([
		apex, Vector2(apex.x - half, base_y), seam]), ParkUI.ACCENT.darkened(0.34))
	draw_colored_polygon(PackedVector2Array([
		apex, seam, Vector2(apex.x + half, base_y)]), ParkUI.ACCENT)
	draw_polyline(PackedVector2Array([
		apex, Vector2(apex.x - half, base_y), Vector2(apex.x + half, base_y), apex,
	]), INK, LINE_MID)
	draw_line(apex, seam, INK, LINE_FINE)

	# A shadow on the ground, so it reads as hovering over the map rather than as
	# something printed on it.
	_ellipse(at, 1.6, Color(INK, 0.16), Color(INK, 0.0))


# --- primitives --------------------------------------------------------------

## A patch of ground: a tilted rectangle on the plan, no height.
func _slab(from: Vector2, to: Vector2, fill: Color, edge_width := LINE_MID) -> void:
	var quad := PackedVector2Array([
		_ground(Vector2(from.x, from.y)), _ground(Vector2(to.x, from.y)),
		_ground(Vector2(to.x, to.y)), _ground(Vector2(from.x, to.y)),
	])
	draw_colored_polygon(quad, fill)
	quad.append(quad[0])
	draw_polyline(quad, INK, edge_width)


## A building: its south wall and its roof. Only the south face is visible in a
## straight oblique projection with no horizontal shear, which is exactly why
## this projection was chosen — one wall per block, and it still reads as solid.
func _block(from: Vector2, to: Vector2, height: float, roof: Color, wall: Color) -> void:
	var wall_quad := PackedVector2Array([
		_ground(Vector2(from.x, to.y)), _ground(Vector2(to.x, to.y)),
		_rise(Vector2(to.x, to.y), height), _rise(Vector2(from.x, to.y), height),
	])
	draw_colored_polygon(wall_quad, wall)
	wall_quad.append(wall_quad[0])
	draw_polyline(wall_quad, INK, LINE_FINE)

	var roof_quad := PackedVector2Array([
		_rise(Vector2(from.x, from.y), height), _rise(Vector2(to.x, from.y), height),
		_rise(Vector2(to.x, to.y), height), _rise(Vector2(from.x, to.y), height),
	])
	draw_colored_polygon(roof_quad, roof)
	roof_quad.append(roof_quad[0])
	draw_polyline(roof_quad, INK, LINE_FINE)


## A circle lying on the ground, which under the tilt is an ellipse.
func _ellipse(at: Vector2, radius: float, fill: Color, edge: Color) -> void:
	var points := PackedVector2Array()
	for i in 24:
		var a := float(i) * TAU / 24.0
		points.append(_ground(at + Vector2(cos(a), sin(a)) * radius))
	draw_colored_polygon(points, fill)
	if edge.a > 0.0:
		points.append(points[0])
		draw_polyline(points, edge, LINE_FINE)


## A disc held up in the air on nothing — the observation tower's ring.
func _disc(at: Vector2, height: float, radius: float, fill: Color) -> void:
	var points := PackedVector2Array()
	for i in 20:
		var a := float(i) * TAU / 20.0
		var on := at + Vector2(cos(a), sin(a)) * radius
		points.append(_rise(on, height))
	draw_colored_polygon(points, fill)


func _cone(at: Vector2, height: float, radius: float, fill: Color) -> void:
	draw_colored_polygon(PackedVector2Array([
		_rise(at, height + radius * 0.9),
		_ground(at + Vector2(-radius, 0.0)) - Vector2(0.0, _len(height)),
		_ground(at + Vector2(radius, 0.0)) - Vector2(0.0, _len(height)),
	]), fill)


func _dashed(from: Vector2, to: Vector2, colour: Color, width: float) -> void:
	var steps := 6
	for step in steps:
		if step % 2 == 1:
			continue
		draw_line(_ground(from.lerp(to, float(step) / float(steps))),
			_ground(from.lerp(to, float(step + 1) / float(steps))), colour, width)


## Centred on the point, on the paper rather than on the ground — labels are
## printed on the sheet and do not lie down with the plan.
##
## `units` is a height on the sheet, not a pixel size: the map draws at whatever
## size its box is, and type measured in pixels would be a caption on a thumbnail.
func _label(text: String, screen: Vector2, units: float, colour: Color) -> void:
	if _face == null:
		# The display face: everything on this sheet is printed lettering on a
		# park map — a title, four place names and a compass point — and none of
		# it is a sentence.
		_face = ParkUI.display_font()
	var size := maxi(int(round(_len(units))), 8)
	var width := _face.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	var origin := screen - Vector2(width * 0.5, 0.0)

	# A bite of paper behind the type. Names on a drawn map are printed over the
	# artwork, and without this every label has to go where nothing else does —
	# which is not how a map is drawn, and not a constraint the park's layout
	# should be answering to.
	var pad := Vector2(_len(0.9), _len(0.5))
	var ascent := _face.get_ascent(size)
	var descent := _face.get_descent(size)
	draw_rect(Rect2(origin - Vector2(pad.x, ascent + pad.y),
		Vector2(width + pad.x * 2.0, ascent + descent + pad.y * 2.0)), PAPER, true)

	draw_string(_face, origin, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, colour)
