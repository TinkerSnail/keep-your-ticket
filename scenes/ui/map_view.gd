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
## Everything is in map units on a 100 × 100 plan, scaled to whatever box it is
## given. Bearings match the park: gate south, boardwalk west, and the four
## scaffolded thresholds at the angles `plaza.tscn` puts them.

## The plan the park is drawn on: a hundred units square, and square on purpose.
## The bearings on this map are meant to survive being read — the gate is south,
## the boardwalk is west — so the drawing keeps its own proportions and is never
## stretched to whatever shape the window happens to be.
##
## The *paper* is a separate thing and is not square. It runs out to the edges of
## the well, and whatever is left over around the plan is margin. That is what a
## foldout actually is: a drawing with a great deal of paper around it, with the
## title block, the key and the compass printed in the paper rather than on the
## park. They used to be printed on the park, because a square sheet fitted to a
## landscape well has no margin to put them in — the compass sat over the skyline
## and the cartouche over the water, and half the tab was empty field.
const PLAN := 100.0

## How tall the sheet is, in the same units the plan is drawn in.
##
## Fewer than the plan has, and that is the whole of how big the park comes out.
## The plan's outermost band is empty on all four sides — nothing is drawn north
## of the coaster or south of the gate — so sizing the paper to the full hundred
## leaves the drawing floating in the middle of it at about half height, which is
## the same fault as a square sheet in a landscape well one level further in. At
## 82 the park runs nearly the full height of the sheet and what is left at the
## sides is margin rather than gap.
const SHEET_HEIGHT := 82.0

## What the sheet needs across before it gives up and shrinks the drawing instead
## of the margins. A narrow window loses its title block long before it loses any
## of the park.
const SHEET_WIDTH_MIN := 150.0

## Where the plan sits across the paper. Left of centre, because the title block
## and the key stack up in one margin while the compass is a single object in the
## other, and a map with two equal margins has nothing printed in either.
const PLAN_BIAS := 0.56

## The field showing around the sheet. Small — enough for the tab's own colour to
## frame the paper, and for the sheet to have something to throw its shadow onto.
## Without it the paper covers the field completely and the map is the one tab
## with no colour-coding on it.
const PAPER_INSET := 14.0

## Where everything on the drawing stands, in plan units, and the one place to
## edit it.
##
## **The park's layout is not settled, so nothing here is written twice and
## nothing is written inline.** These are the numbers; the drawing functions
## below only ever read them. Moving the boardwalk out three units to make room
## for the west cost six separate literals scattered through `_draw_boardwalk`
## the first time, which is exactly the tax a layout still being argued about
## should not be paying.
##
## They are *not* derived from `ParkPlan`, and that is deliberate rather than
## laziness: this map is not to scale and says so on its face — the plaza is drawn
## far larger against the bluff than it stands, because a map drawn to scale would
## be a plaza the size of a stamp. A straight transform of the world would put the
## terrace inside the plaza wall. What the drawing owes the park is the *order and
## the shape* of the route, not its measurements.
##
## The one thing that is derived is the four threshold bearings, because those are
## angles rather than distances and an angle read off the wrong copy points at
## nothing. See `_threshold_bearings`.

## The plaza, at the middle, because the design's whole claim is that the park is
## a hub with spokes and a map that does not show that is not showing the park.
const PLAZA_AT := Vector2(52.0, 50.0)
const PLAZA_HALF := 13.0

## The boardwalk: the deck, the frontage along its back, the pier and the wheel.
const DECK := Rect2(12.0, 30.0, 9.0, 38.0)
const LIT_DECK := Color("e8c76a")
## The frontage's near and far edge — deck side and bluff side.
const FRONTAGE := Vector2(19.0, 22.5)
const FRONT_FROM := 33.0
const FRONT_STEP := 8.5
const FRONT_DEPTH := 6.0
const PIER := Rect2(5.0, 45.5, 8.0, 3.0)
const WHEEL_AT := Vector2(16.5, 38.0)

## The west, between the plaza wall and the boardwalk: the terrace, the parapet,
## the drop, and the two flights down it.
##
## The terrace runs east until it disappears under the plaza's west buildings, and
## the passage under the arch is not drawn separately. It was, and it was
## invisible: in a straight oblique projection a building south of a westward
## opening always covers it, because the roof is drawn upward from the block's
## south face — a five-unit building hides everything within five units north of
## it, and the gap in the wall is under four. That is the same rule the draw order
## is sorted by and it has no exception; lowering the two flanking blocks enough
## to clear it would have made them one unit tall. A shelf tucking behind the
## buildings is the true relationship anyway, and it needs no special case.
##
## The turn in the stair is the one part that has to survive being drawn this
## small. It is what makes the gate at the foot a threshold you cannot see
## through, and so the reason the boardwalk can load behind it.
const TERRACE := Rect2(29.0, 45.6, 6.6, 7.2)
const PARAPET_H := 1.3

const STAIR_HEAD := Vector2(29.0, 46.4)
const STAIR_TURN := Vector2(26.2, 46.4)
const STAIR_FOOT := Vector2(26.2, 52.1)
const STAIR_GATE := Vector2(25.2, 52.1)
const STAIR_WIDTH := 1.7
const TREAD_STEP := 0.85

## The bluff, as a hachured scarp. Ticks on the downhill side, which is the
## convention every printed map uses and the only mark on a flat plan that says
## one side of a line is lower than the other.
##
## The ticks are long and close together: short ones left the band between the
## scarp and the backs of the shops as blank paper, and that band is the drop.
const SCARP_X := 29.0
const SCARP_FROM := 27.0
const SCARP_TO := 70.0
const SCARP_TICK := 2.9
const SCARP_STEP := 3.0

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
	{"id": &"plaza", "at": PLAZA_AT, "label": "The Plaza",
		"note": "The hub. Six ways out of it, and the photo hut."},
	{"id": &"overlook", "at": Vector2(TERRACE.position.x + TERRACE.size.x * 0.5, 49.2),
		"label": "The Overlook",
		"note": "Through the arch. The boardwalk, from above it."},
	{"id": &"boardwalk", "at": Vector2(WHEEL_AT.x, 47.0), "label": "The Boardwalk",
		"note": "West, down the stair. The promenade, the pier and the wheel."},
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

## One unit in pixels. Uniform, and that is the point — the paper is not square
## but its grid is, or the compass printed in the margin would come out an oval.
func _scale() -> float:
	return minf((size.y - PAPER_INSET * 2.0) / SHEET_HEIGHT,
		(size.x - PAPER_INSET * 2.0) / SHEET_WIDTH_MIN)


## The sheet in pixels: the well, inset far enough for the field to show around
## it.
func _sheet() -> Rect2:
	var inset := Vector2(PAPER_INSET, PAPER_INSET)
	return Rect2(inset, size - inset * 2.0)


## How much paper there is, in units. Depends on the window, which is the whole
## difference between the paper and the plan: the plan is a fixed hundred units
## square and the paper is however much of it the well can show.
func _paper() -> Vector2:
	return _sheet().size / _scale()


## Paper to pixels. The border, the creases, the cartouche, the key and the
## compass use this, and none of them tilts — they are printed on the sheet
## rather than standing on the ground.
func _at(point: Vector2) -> Vector2:
	return _sheet().position + point * _scale()


func _len(units: float) -> float:
	return units * _scale()


## How far the drawing actually reaches either side of the plan's centre, in plan
## units before the spread. Not the plan's own half width, and the difference
## matters: the water stops at 5 and the coaster at 86, so the plan's nominal
## right-hand band is fifteen units of paper nothing is ever drawn on. Measuring
## the margin from there gives that paper to the margin and then leaves the
## compass sitting in the middle of it.
const DRAWN_LEFT := 47.0
const DRAWN_RIGHT := 40.0


## Where the drawing's left and right edges fall on the paper. The margins are
## what is left outside them, and everything printed in a margin measures itself
## against these rather than against a hand-written column — move `PLAN_BIAS` and
## the title block follows.
func _drawn_left() -> float:
	return _paper().x * PLAN_BIAS - DRAWN_LEFT * SPREAD


func _drawn_right() -> float:
	return _paper().x * PLAN_BIAS + DRAWN_RIGHT * SPREAD


## Ground plane. Squashed towards the plan's middle and spread back out, which is
## the whole of the oblique projection — everything on the park's floor goes
## through here. The plan is then placed on the paper, which is the one line that
## keeps the drawing off the margins.
func _ground(point: Vector2) -> Vector2:
	var centre := Vector2(PLAN, PLAN) * 0.5
	var origin := Vector2(_paper().x * PLAN_BIAS, _paper().y * 0.5)
	return _at(origin + Vector2(
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
	if _scale() <= 0.0:
		return
	_draw_paper()
	_draw_water()
	_draw_skyline()
	_draw_thresholds()
	_draw_boardwalk()
	_draw_west()
	_draw_plaza_ground()
	_draw_plaza_pieces()
	_draw_entrance()
	_draw_west_name()
	_draw_compass()
	_draw_hours()
	_draw_cartouche()
	_draw_key()
	# Last, over the printed sheet. The two things here that are not paper.
	_draw_places()


## The stock, with a heavy border and the folds. The creases do more than any
## other mark on the sheet — they are the difference between a map and a piece of
## paper that has never been anywhere.
##
## Three of them, because this is a landscape foldout and a landscape foldout
## folds in three and then in half. One crease down the middle was what a square
## sheet could carry; it also ran straight through the plaza, which is the one
## place on the drawing a line has no business crossing.
func _draw_paper() -> void:
	var sheet := _sheet()

	# The same hard shadow every plate in the menu throws, down and to the right.
	# Without it the sheet is not lying on the field, it is merely occupying it —
	# and it was the one object on the pause screen with nothing under it.
	draw_rect(Rect2(sheet.position + Vector2(ParkUI.SHADOW_OFFSET), sheet.size),
		ParkUI.SHADOW_COLOUR, true)
	draw_rect(sheet, PAPER, true)
	draw_rect(sheet, INK, false, LINE_HEAVY)

	var paper := _paper()
	for across in [1.0 / 3.0, 2.0 / 3.0]:
		draw_line(_at(Vector2(paper.x * across, 0.0)),
			_at(Vector2(paper.x * across, paper.y)), Color(PAPER_LINE, 0.26), LINE_FINE)
	# The half fold is fainter than the thirds. It is the crease a map spends
	# least of its life folded along, and it is the one that crosses the park.
	draw_line(_at(Vector2(0.0, paper.y * 0.5)), _at(Vector2(paper.x, paper.y * 0.5)),
		Color(PAPER_LINE, 0.13), LINE_FINE)


func _draw_water() -> void:
	var edge := PackedVector2Array()
	for point in [Vector2(MARGIN, MARGIN), Vector2(12.0, MARGIN), Vector2(10.0, 30.0),
			Vector2(12.0, 62.0), Vector2(9.0, PLAN - MARGIN), Vector2(MARGIN, PLAN - MARGIN)]:
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
	_slab(DECK.position, DECK.end, LIT_DECK if standing else GROUND_DECK)

	# The frontage, one building deep along the back of the deck.
	for i in 4:
		var y := FRONT_FROM + float(i) * FRONT_STEP
		_block(Vector2(FRONTAGE.x, y), Vector2(FRONTAGE.y, y + FRONT_DEPTH),
			3.4 + float(i % 2) * 1.2, ROOF_WARM, WALL_WARM)

	# The pier, running out over the water on its legs.
	_slab(PIER.position, PIER.end, GROUND_DECK)
	for i in 4:
		var leg := Vector2(PIER.position.x + 1.0 + float(i) * 2.0, PIER.end.y)
		draw_line(_ground(leg), _rise(leg, -1.6), Color(INK, 0.4), LINE_FINE)

	# The wheel, standing on its edge and turning. Drawn in the screen plane
	# rather than on the ground — a wheel is vertical, and flattening it with the
	# rest of the plan would lay it down flat like a roundabout.
	var hub := _rise(WHEEL_AT, 5.2)
	var radius := _len(5.0)
	draw_line(_ground(WHEEL_AT), hub, INK, LINE_MID)
	draw_arc(hub, radius, 0.0, TAU, 40, INK, LINE_MID)
	var turn := _phase * TAU / WHEEL_SECONDS
	for i in 8:
		var a := turn + float(i) * TAU / 8.0
		var rim := hub + Vector2(cos(a), sin(a)) * radius
		draw_line(hub, rim, Color(INK, 0.5), LINE_FINE)
		draw_circle(rim, _len(0.7), ROOF_WARM)
		draw_arc(rim, _len(0.7), 0.0, TAU, 10, INK, LINE_FINE)

	_label("BOARDWALK", _ground(Vector2(WHEEL_AT.x, DECK.end.y + 4.5)), TYPE_PLACE, INK)


## The west: the arch, the terrace, the parapet, the drop and the stair.
##
## This was the one walkable part of the park that the map left out. It went
## unnoticed while the drawing was small enough that the band between the plaza
## and the boardwalk read as margin; at the size the paper gives it now, that band
## reads as two places with nothing between them — which is the opposite of what
## the west is. The whole point of the arch and the stair is that the boardwalk is
## somewhere you walk *to*, past an overlook that shows you it first.
func _draw_west() -> void:
	_draw_scarp()

	# The plaza's own paving, not the street's, because that is what it is: the
	# plaza stands on made ground and the terrace is the last of it before the
	# drop. In the plaza's colour it reads as the hub running out through its own
	# wall rather than as a separate pale slab laid against it — and it takes the
	# plaza's lit tint with it, because the terrace belongs to that section and a
	# section that lights up except for its far end has a seam in it that is not
	# there.
	_slab(TERRACE.position, TERRACE.end,
		Color("f7d98a") if ParkSections.current() == &"plaza" else GROUND_PLAZA)

	_draw_stair()

	# The parapet, along the terrace's west edge, and drawn with height because
	# that is the whole difference between an overlook and a path that carries on.
	# It stops short of the north end: the stair goes through it there, and a
	# parapet running unbroken past the head of its own stair would be a wall.
	_block(Vector2(TERRACE.position.x - 0.5, STAIR_HEAD.y + 1.2),
		Vector2(TERRACE.position.x + 0.4, TERRACE.end.y), PARAPET_H, ROOF, WALL)


## The overlook's name, and the reason it is not drawn with the rest of the west.
##
## The terrace sits in the one band on this sheet with something drawn hard
## against both sides of it, and the name lost a letter to the plaza's perimeter
## whichever end of the terrace it went — the roof of a block is drawn upward from
## its south face, so the buildings reach several units further across the paper
## than their footprints do, north and south both.
##
## Moving the name until it fitted was the wrong instinct and `_label` already
## says so: a name on a drawn map is *printed over* the artwork on a bite of
## paper, and the alternative is a park laid out to leave room for its own
## labels. So the name goes on last, where a printed name belongs, and can sit
## where it reads best.
func _draw_west_name() -> void:
	_label("OVERLOOK", _ground(Vector2(TERRACE.position.x + 2.4, TERRACE.end.y + 4.0)),
		TYPE_SMALL, INK)


## The bluff. Hachures on the downhill side — the plaza and the terrace stand on
## made ground and everything west of the parapet falls away, and until this went
## in the map drew the boardwalk and the plaza as though they were on one level
## with a gap between them.
##
## Broken where the stair cuts in, because the well is a slot in the bluff rather
## than a stair leaning against it, and the edge genuinely stops there.
func _draw_scarp() -> void:
	var notch_from := STAIR_HEAD.y - 1.2
	var notch_to := STAIR_FOOT.y + 1.2
	for run in [[SCARP_FROM, notch_from], [notch_to, SCARP_TO]]:
		draw_line(_ground(Vector2(SCARP_X, run[0])), _ground(Vector2(SCARP_X, run[1])),
			PAPER_LINE, LINE_MID)

	var at := SCARP_FROM
	while at < SCARP_TO:
		if at < notch_from or at > notch_to:
			draw_line(_ground(Vector2(SCARP_X, at)),
				_ground(Vector2(SCARP_X - SCARP_TICK, at)), PAPER_LINE, LINE_FINE)
		at += SCARP_STEP


## Two flights and a turn, drawn as treads.
##
## A staircase on a printed map is a ladder of short parallel lines and has been
## for as long as maps have been printed. It reads as a change of level at a size
## where nothing else does, and the lines run across the way you walk rather than
## along it — a ladder the other way round is a fence.
func _draw_stair() -> void:
	var half := STAIR_WIDTH * 0.5

	# Both flights and the landing as one shape, so the turn is a corner rather
	# than two strips that happen to meet at one.
	_slab(Vector2(STAIR_TURN.x - half, STAIR_HEAD.y - half),
		Vector2(STAIR_HEAD.x, STAIR_HEAD.y + half), GROUND_DECK, LINE_FINE)
	_slab(Vector2(STAIR_TURN.x - half, STAIR_TURN.y - half),
		Vector2(STAIR_TURN.x + half, STAIR_FOOT.y), GROUND_DECK, LINE_FINE)

	var across := STAIR_HEAD.x - TREAD_STEP
	while across > STAIR_TURN.x + half:
		draw_line(_ground(Vector2(across, STAIR_HEAD.y - half)),
			_ground(Vector2(across, STAIR_HEAD.y + half)), Color(INK, 0.5), LINE_FINE)
		across -= TREAD_STEP

	var down := STAIR_TURN.y + half + TREAD_STEP
	while down < STAIR_FOOT.y:
		draw_line(_ground(Vector2(STAIR_TURN.x - half, down)),
			_ground(Vector2(STAIR_TURN.x + half, down)), Color(INK, 0.5), LINE_FINE)
		down += TREAD_STEP

	# The gate at the foot, shut, and the reason none of the boardwalk is visible
	# from the stair. A bar across the way out, which is what it is.
	draw_line(_ground(STAIR_GATE + Vector2(0.0, -half)),
		_ground(STAIR_GATE + Vector2(0.0, half)), INK, LINE_HEAVY)


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
##
## In the right margin, measured off the plan's own edge rather than off the
## paper's. It used to be at a fixed corner of a square sheet, which put it over
## the coaster — the compass and the skyline were competing for the same inch of
## paper, and the compass is the one that has to be read cold.
func _draw_compass() -> void:
	var block := _right_margin()
	var at := Vector2(block.position.x + block.size.x * 0.5, block.position.y + 13.0)
	draw_arc(_at(at), _len(6.0), 0.0, TAU, 32, INK, LINE_MID)
	draw_line(_at(at + Vector2(0, 4.5)), _at(at + Vector2(0, -4.5)), INK, LINE_HEAVY)
	draw_colored_polygon(PackedVector2Array([
		_at(at + Vector2(0.0, -6.0)), _at(at + Vector2(-1.8, -2.6)), _at(at + Vector2(1.8, -2.6)),
	]), INK)
	_label("N", _at(at + Vector2(0.0, -8.6)), TYPE_PLACE, INK)


## The title block, in the left margin and ruled. The double rule is most of what
## makes a block of type on a map read as printed rather than as a caption
## somebody put there afterwards.
func _draw_cartouche() -> void:
	var block := _margin()
	var box := Rect2(block.position, Vector2(block.size.x, 20.0))
	_rule(box, PAPER_LINE)
	_rule(box.grow(-1.7), Color(PAPER_LINE, 0.55))
	var middle := box.position.x + box.size.x * 0.5
	_label("VISITOR MAP", _at(Vector2(middle, box.position.y + 8.4)), TYPE_TITLE, INK)
	_label("KEEP YOUR TICKET", _at(Vector2(middle, box.position.y + 15.4)),
		TYPE_PLACE, PAPER_LINE)


## What the printed marks mean, under the title block.
##
## Only printed ones. The pyramid and the brackets are the two things on this
## screen that are not paper, and a key explaining them would be the sheet
## annotating the interface drawn over it. These three are ink.
##
## The clock is in here for a reason beyond completeness. The time is read off
## the tower and nowhere else, which is a rule the player has to discover, and a
## park's own map printing a clock symbol against the tower is the one place that
## can be said out loud without a tutorial saying it.
const KEY := [
	{"mark": &"closed", "text": "UNDER CONSTRUCTION"},
	{"mark": &"photo", "text": "PHOTO SERVICE"},
	{"mark": &"clock", "text": "PARK CLOCK"},
]

const KEY_ROW := 9.0


func _draw_key() -> void:
	var block := _margin()
	var top := block.position.y + 28.0
	_label("KEY", _at(Vector2(block.position.x, top)), TYPE_PLACE, PAPER_LINE, false)
	draw_line(_at(Vector2(block.position.x, top + 2.6)),
		_at(Vector2(block.position.x + block.size.x, top + 2.6)),
		Color(PAPER_LINE, 0.6), LINE_FINE)

	var row := top + 12.0
	for entry in KEY:
		_key_mark(entry["mark"], Vector2(block.position.x + 4.6, row - 1.3))
		_label(entry["text"], _at(Vector2(block.position.x + 11.5, row)),
			TYPE_SMALL, INK, false)
		row += KEY_ROW

	# The disclaimer every park map has ever carried, and here it is true — this
	# drawing is stylized and the corner minimap is the one that is to scale. It
	# is printed rather than explained because the sheet is the right voice for it.
	_label("NOT DRAWN TO SCALE",
		_at(Vector2(block.position.x, block.position.y + block.size.y - 1.0)),
		TYPE_SMALL, Color(PAPER_LINE, 0.75), false)


## When the park is open, printed in the right margin under the compass.
##
## Hours are not the time and this is not the tower's job. The rule is that you
## find out what o'clock it is by looking at the clock face in the plaza, and
## nothing about a printed opening time tells you that — it tells you when the
## park shuts, which is a thing the park would put on its own map and a thing
## this game in particular wants the player to know early.
##
## Read off `ParkClock` rather than written out, so a park that changes its hours
## does not go on advertising the old ones.
func _draw_hours() -> void:
	var block := _right_margin()
	var box := Rect2(block.position + Vector2(0.0, 26.0), Vector2(block.size.x, 16.0))
	_rule(box, PAPER_LINE)
	var middle := box.position.x + box.size.x * 0.5
	_label("PARK HOURS", _at(Vector2(middle, box.position.y + 6.6)),
		TYPE_SMALL, PAPER_LINE)
	_label("%s — %s" % [_oclock(ParkClock.OPEN_HOUR), _oclock(ParkClock.CLOSE_HOUR)],
		_at(Vector2(middle, box.position.y + 13.2)), TYPE_PLACE, INK)


func _oclock(hour: float) -> String:
	var whole := int(hour) % 24
	var shown := whole % 12
	if shown == 0:
		shown = 12
	return "%d %s" % [shown, "AM" if whole < 12 else "PM"]


## The left margin's usable column, in paper units. Everything printed there is
## laid out against this, so the whole block moves together when the window
## changes shape.
func _margin() -> Rect2:
	var left := 6.0
	return Rect2(Vector2(left, 9.0),
		Vector2(maxf(_drawn_left() - 5.0 - left, 26.0), _paper().y - 18.0))


## And the right one, which holds the compass and the hours.
func _right_margin() -> Rect2:
	var left := _drawn_right() + 5.0
	return Rect2(Vector2(left, 9.0),
		Vector2(maxf(_paper().x - 6.0 - left, 20.0), _paper().y - 18.0))


## One key symbol, drawn on the paper rather than on the ground — these are
## printed marks and do not lie down with the plan.
func _key_mark(kind: StringName, at: Vector2) -> void:
	match kind:
		&"closed":
			var from := _at(at - Vector2(3.6, 0.0))
			var to := _at(at + Vector2(0.8, 0.0))
			for step in 3:
				draw_line(from.lerp(to, float(step) / 3.0),
					from.lerp(to, (float(step) + 0.6) / 3.0), PAPER_LINE, LINE_MID)
			var stop := _at(at + Vector2(2.3, 0.0))
			draw_circle(stop, _len(1.4), PAPER)
			draw_arc(stop, _len(1.4), 0.0, TAU, 14, PAPER_LINE, LINE_FINE)
		&"photo":
			var box := Rect2(_at(at - Vector2(2.8, 2.0)), Vector2(_len(5.6), _len(4.0)))
			draw_rect(box, ParkUI.ACCENT, true)
			draw_rect(box, INK, false, LINE_FINE)
		&"clock":
			var face := _at(at)
			draw_circle(face, _len(2.2), PAPER)
			draw_arc(face, _len(2.2), 0.0, TAU, 20, INK, LINE_MID)
			draw_line(face, face + Vector2(0.0, -_len(1.5)), INK, LINE_FINE)
			draw_line(face, face + Vector2(_len(1.1), 0.0), INK, LINE_FINE)


## A ruled box in paper units.
func _rule(box: Rect2, colour: Color) -> void:
	draw_rect(Rect2(_at(box.position), box.size * _scale()), colour, false, LINE_FINE)


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
## `centred` is off for anything in a margin: a title block centres, a key does
## not, and a key whose three rows each start somewhere different is a list that
## has to be read one line at a time.
func _label(text: String, screen: Vector2, units: float, colour: Color,
		centred: bool = true) -> void:
	if _face == null:
		# The display face: everything on this sheet is printed lettering on a
		# park map — a title, four place names and a compass point — and none of
		# it is a sentence.
		_face = ParkUI.display_font()
	var size := maxi(int(round(_len(units))), 8)
	var width := _face.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	var origin := screen - Vector2(width * 0.5 if centred else 0.0, 0.0)

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
