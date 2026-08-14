class_name ParkPlan
extends RefCounted

## The park's plan, in world coordinates, as the one place it is written down.
##
## Not geometry and not a scene. This is the layout a park has on paper before
## anybody builds it: where the ways through run, where the ground of each
## section sits, and the handful of numbers — the street, the gate, the stair,
## the shoreline — that several different things all have to agree about.
##
## It exists because they had stopped agreeing. `tools/gen_props.gd` held the
## real numbers as constants next to whichever function used them; the corner
## minimap traced the crowd's wander graph because that was the only path-shaped
## thing available to read; the foldout map hand-authored a stylized sheet; and
## `ParkSections.ARRIVAL_FALLBACK` carried a hand-copy of the generator's stair
## arithmetic, which was wrong on all three axes the first time it was written.
## Four descriptions of one park, drifting independently.
##
## So the rule is: **anything that describes where the park is goes here, and
## everything else reads it.** A consumer that wants the park drawn differently
## is welcome to — the foldout is deliberately not to scale and should stay that
## way — but it should stylize *this*, rather than hold a second survey.
##
## Coordinates are Godot's: +X east, +Z south, ground at y = 0. Bearings, where
## they appear, are compass degrees from north, because that is how the design
## documents talk about the thresholds and converting in one place is cheaper
## than converting in four.
##
## **Only scripts can read this. A `.tscn` cannot.** A scene's transforms are
## baked literals with nowhere to put an expression, so anything whose position
## has to live in a scene file rather than be computed at runtime is outside
## what this file can enforce. That is a real limit on "written down once" and
## it is worth choosing deliberately rather than discovering. Three ways out:
##
##   generate the scene from the plan — what `tools/gen_props.gd` does, and the
##       right answer whenever the thing is generated output anyway;
##   place it at `_ready` from a script on the scene root — right when the
##       scene is hand-authored but its position is genuinely plan data;
##   leave the literal and have a test assert it against the plan — right for
##       throwaway scaffolding, and what `tools/section_test.gd` does with the
##       marker in `boardwalk_stub.tscn`.
##
## The third is the one to reach for when the first two cost more than the
## duplication does. Duplication a test enforces is fine. Duplication nothing
## looks at is how the foot of the stair came to be written down as three
## different numbers in a single afternoon.
##
## **Nothing in this file may name an autoload.** `tools/gen_props.gd` runs under
## `--script`, which compiles before the project's autoloads are registered, and
## a script that names one compiles to something that silently is not itself.
## Pure data and pure functions only; that is also why this is a `RefCounted`
## with statics rather than an autoload of its own.


# ---------------------------------------------------------------------------
# The plaza
# ---------------------------------------------------------------------------

## The hub, square with the fountain at the origin. `scenes/world/plaza.tscn`
## builds the ground from these.
##
## **80m to 104m on 2026-08-13, and the hub grew with it.** The reference parks
## put Disneyland's Central Plaza at about 60m, and this is now getting on for
## twice that — a deliberate departure from "the hub is a junction, not a
## destination", made because the plaza has to hold a cast of 56 at peak plus
## the furniture that says what it is, and would not.
##
## Not for looks. Paving the walkways put numbers on how tight it was: measured
## by bearing, the gap between the ring's outer edge and the nearest building
## face was 7.5 to 14 metres all the way round, and *zero* at the photo hut. A
## cafe terrace wants about fourteen of those metres and a walk past it wants
## six, so there was nowhere in the plaza a terrace fitted — which is why the
## one that existed had to be evicted from the south-east and rehoused twice
## before it found ground.
##
## The room went where the shortage was. Everything outside the hub moved out
## 15m and the wall line 12m, so the annulus is 15–18m instead of 8–14. The hub
## itself grew separately and for a different reason: a 10m fountain does not
## hold the middle of a 104m room, and the walk up the entrance street has to
## arrive at something.
const PLAZA_CENTRE := Vector2(0.0, 0.0)
const PLAZA_HALF := 52.0

## The fountain, and its skirt. The ring walkway is set outside this.
##
## 18m across rather than 10. At the old size it was a puddle in the middle of
## the new room and invisible from the gate; this reads from the far end of the
## street, which is the whole job of a thing on an axis.
const FOUNTAIN_AT := Vector2(0.0, 0.0)
const FOUNTAIN_RADIUS := 9.0

## The hub, as one number each. The ring walkway is set outside the fountain's
## skirt and these are what put it there — `WALKWAYS` has the twelve vertices
## written out because a `const` cannot call `sin`, but they are this radius.
const RING_RADIUS := 16.0
const RING_WIDTH := 8.0

## The clock tower, moved onto the gate axis on 2026-08-13.
##
## It stood at (18, −16), off to the north-east, which made it a thing you
## orient by. On the axis it is a thing you walk *at*: gate, street, the mouth of
## the plaza, the fountain, and then the tower behind it, all on x = −1.5. The
## park's one clock becomes the park's landmark, which is the same claim
## `design.md` already makes from the other side — "the time is read off the
## park, not off the screen".
const CLOCK_TOWER_AT := Vector2(-1.5, -32.0)

## The photo hut — the job's anchor, and the one building in the plaza the
## player has business inside.
##
## It used to stand at (9, 8), which is radius 12 — *inside* what is now the
## ring walkway, and against its outer edge even before the plaza grew. It was
## the one bearing where the measured gap between the hub and the nearest
## building was zero. Out at radius 28 it has the walk on one side and open
## ground on the other, which is what a building people queue outside needs.
const PHOTO_HUT_AT := Vector2(21.0, 18.5)

## The cafe terrace: three tables, and where they stand.
##
## Up here rather than in `gen_props.gd` because **two generators have to agree
## about it and they were agreeing by having the same literal typed twice**.
## `gen_crowd.gd::_plaza_chair_spots()` mirrors the props so a guest sits on a
## chair that exists, and its own comment says as much. A shared position that
## two files each declare is a position that drifts the first time one of them
## is edited alone, and this one was about to be — the terrace moved today.
##
## It moved because it was standing in a walkway. It used to sit at (14,3),
## (17,8) and (13,12), which is the eight-metre corridor between the photo hut
## and `building_east` — the only line there is from the ring to the south-east
## threshold. Tables in it meant `spoke_se` had to leave from the south walk
## instead of the ring, and the hub was a spoke short. The corridor is 8.5m and
## the spoke wants 6 of them, so the two could not share it.
##
## **The south-east quadrant then turned out to have nowhere else to put it.**
## Between the photo hut, its queue, the hut's forecourt walk and the new street
## there is no pocket in it wider than three metres — the first two attempts at
## a new address both landed on something, and the crowd's own graph validator
## caught both.
##
## So it crossed the plaza. This is the largest clear pocket the plaza has: six
## by ten metres on the west side, bounded by the ring, the bandstand and
## `building_west_south`, with the west spoke passing north of it. It is a
## better address than the old one on every count except familiarity — it faces
## the fountain across open ground, it has the arch behind it, and it takes the
## afternoon and evening sun, which is when the cafe's own curve says the tables
## fill. It also stops the plaza's whole south-east from being photo hut, queue,
## cafe and street stacked in one quadrant.
## Moved out with everything else when the plaza grew — at the old radius these
## three would now be standing in the ring walkway.
const PLAZA_CAFE := [
	{"at": Vector2(-26.5, 4.0), "theta": 15.0},
	{"at": Vector2(-27.0, 8.5), "theta": -25.0},
	{"at": Vector2(-25.0, 12.5), "theta": 40.0},
]

## Where the two chairs at a table sit, relative to it. Shared for the same
## reason the tables are.
const CAFE_CHAIRS := [Vector3(0.95, 0.0, 0.2), Vector3(-0.9, 0.0, -0.35)]


# ---------------------------------------------------------------------------
# The ways out — six of them, in a 320m perimeter
# ---------------------------------------------------------------------------

## The west arch: a straight tube through the wall at x ≈ −24, its opening
## running z −5.6..1.6 between the two piers.
const ARCH_AT := Vector2(-39.0, -2.0)

## The overlook, past the arch and above the boardwalk. The parapet is at
## x −38.5; this stands short of it, where you actually end up walking.
const OVERLOOK_AT := Vector2(-49.0, -2.0)

## The four scaffolded passages, moved here verbatim from `gen_props.gd`.
##
## Bearings are approximate on purpose. The star is a skeleton — points anchor a
## section's centre line, edges are free — so these sit where the perimeter had
## room rather than on exact rays. From the fountain: roughly 342, 62, 121 and
## 211 degrees, against a west arch at 273 and the entrance street at 182.
## Moved out to the new wall line along the same bearings, so the star the
## design describes is unchanged — 342, 62, 121 and 211 still, to within a
## fraction of a degree. Only the radius grew.
##
## Widened with the plaza. A 12m mouth in a 78m wall and a 12m mouth in a 102m
## wall are not the same opening: the second reads as a crack. These are scaled
## by roughly the same 1.3 the perimeter is.
const THRESHOLDS := [
	{"name": "nnw", "at": Vector3(-16.9, 0.0, -51.5), "theta": PI, "width": 16.0, "turn": 1.0},
	{"name": "ne", "at": Vector3(51.5, 0.0, -27.4), "theta": PI * 0.5, "width": 16.0, "turn": 1.0},
	{"name": "se", "at": Vector3(51.5, 0.0, 31.3), "theta": PI * 0.5, "width": 13.0, "turn": -1.0},
	{"name": "sw", "at": Vector3(-31.3, 0.0, 51.5), "theta": 0.0, "width": 10.0, "turn": -1.0},
]

## How far a passage runs before it bends, and how far it carries after. The
## bend is what buys a section load its cover, so it is plan data rather than a
## detail of the shape — every spoke needs one whether or not it has shops yet.
const REACH := 9.0
const BEND := 7.0


# ---------------------------------------------------------------------------
# The entrance street, south to the gate
# ---------------------------------------------------------------------------

## The street's centre line and half-width, where it leaves the plaza, the
## turnstiles, and the apron outside them. 56m of street, because the reference
## parks all put something between the gate and the hub and going straight from
## one to the other is the arrangement none of them use.
const STREET_X := -1.5
const STREET_HALF := 7.5
const STREET_FROM_Z := 50.0
const GATE_Z := 107.0
const APRON_Z := 123.0


# ---------------------------------------------------------------------------
# The west: the bluff, the stair, and the water
# ---------------------------------------------------------------------------

## The drop off the parapet, and what is below it. The plaza stands on made
## ground; everything west of the parapet falls away here, which is what turns
## the parapet into an overlook rather than a fence.
const SHORE_TOP := -6.0
const WATER_TOP := -7.5

## The shore band, east edge to west edge. The east edge is where the made
## ground of the bluff stops; the west edge is where the planking stops and the
## water starts, and it is where the pier is rooted.
##
## `SHORE_EDGE` was -70 while the west was scenery, which left 7.5m of promenade
## between the frontage and the water — enough to read as a strip at forty
## metres and not enough to stand a wheel on. Widened when the section became
## somewhere the player walks. This is the one number in the west that moved for
## a gameplay reason rather than a compositional one, so it is worth knowing it
## moved: anything that looked right against -70 wants re-checking.
const SHORE_FROM_X := -56.0
const SHORE_EDGE := -92.0

## The frontage line — the row one building deep, 9m of it, so the buildings
## occupy x -62.5..-53.5. East of them is the back lane against the bluff, west
## of them is the promenade.
const FRONT_X := -70.0
const FRONT_DEPTH := 9.0

## The two bands either side of the frontage, as centre lines.
##
## The back lane is the service side and the side the player arrives on. That is
## not an accident of where the stair lands: coming down off the bluff behind
## the buildings and reaching the water only after passing *through* them is the
## reveal, and it is the same trick the arch and the gap already play at a
## larger scale.
const BACK_LANE_X := -61.8
const PROMENADE_X := -83.2

## The stair down the bluff. Two flights with a turn between them, and the turn
## is what makes the gate at the foot a threshold you cannot see through.
##
## **These values are load-bearing outside this file.** `boardwalk_stub.tscn` is
## hardcoded to butt against the stair foot at x −44.7, and `tools/section_test.gd`
## asserts landing coordinates as literals. Moving the stair means moving both,
## and the failure looks like the section loader breaking rather than like this.
const STAIR_W := 2.6
const STAIR_RISE := 0.25
const STAIR_TOP_Z := -9.7
const STAIR_TURN_X := -56.7

## The foot of the stair, as named points, because three things outside this
## file currently hold their own copy of them.
##
## `STAIR_FOOT` is the walking surface at the bottom of the second flight — the
## top of the slab the last tread lands on. The generator computes it rather
## than declaring it, as `foot_z = start_z + horizontal + STAIR_W * 0.5`, which
## is 5.5, and `foot_y = landing_y − vertical`, which is −6.0. Checked against
## the `stair_foot` box in the generated `west_stair.tscn` rather than against
## the arithmetic: it sits at −6.25 with a height of 0.5, so its top is −6.0.
##
## The half-stair-width in that sum is the trap. An earlier version of this
## constant carried 5.2, taken from `capture.gd`'s camera vantage for the
## `stair_foot` screenshot — which is somewhere to stand a camera, not the slab.
## It is exactly the drift this file exists to stop, so it is recorded here
## rather than quietly corrected.
##
## `STAIR_FOOT_STAND` is where a *body* ends up: the same slab, 0.2 up because
## the player rides that far above their floor, and east of the crossing volume
## rather than inside it. That is what `ParkSections` arrives the player on
## coming back from the boardwalk, and it matches the `arrival_from_boardwalk`
## marker in `west_stair.tscn` to the digit.
##
## **The gate at the foot turned west on 2026-08-12.** It faced south, which was
## invisibly wrong for as long as the bluff was the plaza's alone: the section
## swap freed it, so nobody ever saw that the shut gate at the bottom of the
## stair had twelve metres of solid rock behind it and that the arrival on the
## far side stood inside that rock. The stair well is a slot in the bluff open on
## its *west* face — that is where the boardwalk is — so west is where the way
## out has always been. The whole class of error is the same one this file was
## written for, one level up: not two numbers disagreeing, but a number nothing
## was in a position to contradict.
##
## `BOARDWALK_ARRIVAL` is the far side of the same seam — where the player
## stands having gone *out* through the gate, and it is generated now rather
## than hand-placed: `gen_props.gd` emits the `arrival_from_plaza` marker with
## the section, so this is the plan's copy and the test's assertion checks the
## two agree.
##
## It moved when the boardwalk became somewhere to walk. The stub put it 8m
## straight south of the gate, facing nowhere in particular, which was fine for
## a deck with three rails on it. The section puts it west of the gate and turns
## it towards the alley mouth, because the player should arrive already looking
## at the way on. `BOARDWALK_ARRIVAL_YAW` is that turn — north-west, so the
## frontage runs away on the left and the bluff is behind the right shoulder.
const STAIR_FOOT := Vector3(-56.7, -6.0, 5.5)
const STAIR_FOOT_STAND := Vector3(-56.0, -5.8, 5.5)
## Six and a half metres south of the gate rather than level with it, and that
## gap is doing work. Level with the gate is level with the *hole in the
## frontage* — they are at the same z — so the player arrived already looking
## down the alley at the wheel and the water, and the reveal fired during the
## fade. Screenshots caught it; nothing else could have.
##
## From here the custard unit is between the player and the gap, so the walk is
## twelve metres of service lane and then a corner. The gate they came through is
## passed on the right, which nobody notices and which no test can object to.
const BOARDWALK_ARRIVAL := Vector3(-61.5, -5.8, 12.0)
const BOARDWALK_ARRIVAL_YAW := 0.15

## The gate itself, as the plane both sections build against. The well is 2.6m
## wide and its west face is the bluff's, so the gate hangs a hair proud of it.
const FOOT_GATE_X := -58.1


# ---------------------------------------------------------------------------
# The boardwalk
# ---------------------------------------------------------------------------

## The strip, north to south, and where it stops.
##
## Santa Cruz is the reference and has been since the west was scenery: a ribbon
## one building deep, closed at both ends by something, with the rides on the
## water side. Santa Monica supplies the other half — the pier as a second strip
## running out at right angles to the first, with the big silhouette at its head.
##
## The whole section is 160m of promenade against 340m of shore, so most of the
## shore stays scenery. That is deliberate and is what the ends are for: the
## strip is closed at the coaster in the north and at a chain in the south, and
## the shore visibly carries on past both.
const WALK_FROM_Z := -82.0
const WALK_TO_Z := 78.0

## The frontage runs from the coaster's station south. North of `FRONT_FROM_Z`
## there are no buildings, because that is where the coaster stands and it takes
## the full width of the shore.
const FRONT_FROM_Z := -34.0
const FRONT_TO_Z := 64.0

## The hole in the frontage, aimed at the arch, and the alley through it. The
## whole west composition is this: the arch frames a gap, the gap frames the
## pier. The player walks the same line the composition is built on.
const GAP_FROM := -8.0
const GAP_TO := 6.0
const ALLEY_Z := -1.0

## The three anchors, in the order you meet them coming through the alley.
##
## Turn left and there is nothing much; turn right and the strip runs north past
## the wheel to the coaster. That asymmetry is the point — a strip with the
## interest at one end gives the walk a direction, and a strip with it in the
## middle gives the walk two dead ends.
##
## The wheel is 15m north of the alley's axis rather than on it, which is
## inherited from when it was scenery and is still right: from the fountain the
## pier's north rail covers it, and a step or two north uncovers it.
## The wheel's disc stands in the Z–Y plane so that it is face-on from the
## plaza, which means its footprint is 22m along z and about two across — a long
## thin thing, not a circle. Worth stating because the obvious mistake is to
## give it a round platform sized to its radius, and a 13m radius does not fit
## in a 17.5m promenade while a 2m axle fits anywhere.
## Set well west so the promenade passes on the *inland* side of it with room to
## spare — 8.5m against 1m on the water side. A wheel in the middle of a strip
## pinches it twice; a wheel against the rail pinches it once and puts the queue
## where the shops are, which is where a queue belongs.
const WHEEL_AT := Vector2(-87.0, -16.0)
const WHEEL_RADIUS := 13.2
const WHEEL_PLATFORM := Vector2(8.0, 26.0)

## The coaster closes the north end. Out-and-back along the shore, station
## fronting the promenade, structure running away from the player — so it is a
## thing you walk towards and then walk under, rather than a thing you look at.
const COASTER_STATION := Vector2(-78.0, -38.0)
const COASTER_HEADING := 0.0
const COASTER_FROM_Z := -38.0
const COASTER_TO_Z := -82.0

## The pier, rooted at the promenade edge on the alley's axis and running west
## over the water to the pavilion at its head. The pavilion is the section's
## landmark and the reason the boardwalk is west at all: it is what the sun sets
## behind, seen from the plaza, at the hour the light is worth photographing.
const PIER_ROOT := Vector2(SHORE_EDGE, ALLEY_Z)
const PIER_LENGTH := 44.0
const PIER_HALF_W := 4.0
const PAVILION_AT := Vector2(SHORE_EDGE - PIER_LENGTH - 6.0, ALLEY_Z)

## The row, unit by unit, and the one description of it. Three things read this:
## the tableau draws each span as a slab with a lip, the section draws the same
## spans with fronts and awnings and signs, and the crowd hangs a point of
## interest on every sign so that a guest reading one is looking where the sign
## actually is.
##
## Widths and heights are stepped rather than random. A roofline needs to read as
## a set of decisions; noise reads as noise, at forty metres and at four.
##
## The hole is the absence of entries between `GAP_FROM` and `GAP_TO`, not a flag
## on a unit — a gap is where a building is not.
##
## `kind` is the only field here that is content rather than massing, and it is
## deliberately dull and period: an arcade, a shooting gallery, food, a fun house
## front, a photo studio because the job should have somewhere to be down here
## too, and one unit shuttered, because a strip with nothing shut on it is a
## strip nobody works at.
const FRONTAGE_UNITS := [
	{"nm": "arcade", "from": -34.0, "to": -22.0, "h": 8.5, "kind": "arcade"},
	{"nm": "gallery", "from": -22.0, "to": -15.0, "h": 6.0, "kind": "games"},
	{"nm": "corndogs", "from": -15.0, "to": GAP_FROM, "h": 5.5, "kind": "food"},
	{"nm": "custard", "from": GAP_TO, "to": 13.0, "h": 5.5, "kind": "food"},
	{"nm": "studio", "from": 13.0, "to": 21.0, "h": 6.5, "kind": "shop"},
	{"nm": "funhouse", "from": 21.0, "to": 33.0, "h": 11.0, "kind": "ride"},
	{"nm": "games", "from": 33.0, "to": 44.0, "h": 6.0, "kind": "games"},
	{"nm": "restrooms", "from": 44.0, "to": 51.0, "h": 4.5, "kind": "plain"},
	{"nm": "shuttered", "from": 51.0, "to": 58.0, "h": 6.0, "kind": "shut"},
	{"nm": "taffy", "from": 58.0, "to": FRONT_TO_Z, "h": 5.5, "kind": "shop"},
]

## Where somebody can sit down, which two different generators have to agree
## about — `gen_props.gd` builds the furniture and `gen_crowd.gd` puts people on
## it. The plaza's equivalents are duplicated between the two tools on purpose,
## with a comment saying a stale copy shows up as guests sitting in mid-air. That
## was the right call when there was nowhere better to put them; there is now.
const TABLES := [
	Vector2(-77.5, -13.5), Vector2(-77.5, -10.0),
	Vector2(-77.5, 8.0), Vector2(-77.5, 11.5),
]

## The benches along the rail, as a rule rather than a list, because they are
## generated as one. Facing west: a bench with its back to the water on a
## promenade is a bench nobody sits on.
const BENCH_X := SHORE_EDGE + 2.6
const BENCH_FIRST_Z := WALK_FROM_Z + 10.0
const BENCH_STEP := 12.0


## The bench positions, skipping the two places the promenade is not free — the
## pier mouth and the length of the wheel's platform. Built rather than listed so
## the furniture and the people sitting on it cannot drift apart.
static func bench_line() -> Array:
	var out := []
	var z := BENCH_FIRST_Z
	while z < WALK_TO_Z - 8.0:
		if absf(z - PIER_ROOT.y) > 7.0 and absf(z - WHEEL_AT.y) > 9.0:
			out.append(Vector2(BENCH_X, z))
		z += BENCH_STEP
	return out


# ---------------------------------------------------------------------------
# The sections
# ---------------------------------------------------------------------------

## What is behind each of the six ways out, and how much of it exists.
##
## **This table names four places the project deliberately refused to name.**
## `PLACES` below and `ParkSections.SECTIONS` both carried the same rule — that
## naming a section ahead of its design is inventing park content — and it was a
## good rule for as long as nothing needed the park to read as a whole. Christina
## called it on 2026-08-12: the park is to be massed all the way out, which
## cannot be done anonymously, so the four get names now.
##
## What that costs is worth stating rather than discovering. These are footprints
## and a theme, not designs. Anything that treats a name here as settled — a
## sign, a map label, a guest with an errand there — is building on a decision
## that has not been made. What they are for is silhouette: the coaster over the
## north-east wall, the big top over the south-west, so that standing in the
## plaza tells you the park continues in five directions.
##
## `ground` is the footprint's centre and size in x/z, at y = 0 except where
## noted. `floor_y` is there because the boardwalk's is not zero and a consumer
## that assumes it is will place things six metres in the air.
##
## **Nothing here may go west of x -38.** The bluff runs the whole west edge of
## the park, z -170 to +170, and the ground past it is the boardwalk's, six
## metres down. That is why the south-west section is a narrow strip rather than
## the square the other three are: there is nowhere for it to widen into.
const SECTION_GROUND := {
	&"plaza": {"at": Vector2(0.0, 0.0), "size": Vector2(104.0, 104.0), "floor_y": 0.0},
	&"boardwalk": {
		"at": Vector2((SHORE_FROM_X + SHORE_EDGE) * 0.5, 0.0),
		"size": Vector2(SHORE_FROM_X - SHORE_EDGE, 340.0),
		"floor_y": SHORE_TOP,
	},
	# Pushed out along their own bearings by the 12m the wall line moved, so each
	# still sits just beyond its threshold rather than overlapping the bigger
	# plaza. Sizes unchanged — these are footprints for silhouette, and none of
	# them is built.
	&"grove": {"at": Vector2(-9.0, -104.0), "size": Vector2(62.0, 84.0), "floor_y": 0.0},
	&"frontier": {"at": Vector2(106.0, -60.0), "size": Vector2(90.0, 76.0), "floor_y": 0.0},
	&"kiddieland": {"at": Vector2(94.0, 63.0), "size": Vector2(58.0, 58.0), "floor_y": 0.0},
	&"fairground": {"at": Vector2(-29.0, 91.0), "size": Vector2(26.0, 76.0), "floor_y": 0.0},
}

## Which way out leads where. The keys are the threshold names in `THRESHOLDS`
## plus the two that are not thresholds — the west arch, whose seam is really the
## gate at the foot of the stair, and the street south to the gate, which leads
## out of the park rather than into a section.
const SPOKE_LEADS_TO := {
	&"west": &"boardwalk",
	&"nnw": &"grove",
	&"ne": &"frontier",
	&"se": &"kiddieland",
	&"sw": &"fairground",
	&"south": &"",
}

## A one-line theme per section, kept here because massing needs to know what
## shape to make and nothing else does yet. Not sign copy and not a name the
## player ever reads.
const SECTION_THEME := {
	&"plaza": "the hub: fountain, bandstand, photo hut, sign tower",
	&"boardwalk": "seaside strip: wheel, wooden coaster, pier and pavilion",
	&"grove": "shade and water: picnic tables under trees, the log flume",
	&"frontier": "a western street: false fronts one deep, a mine train",
	&"kiddieland": "the runt: small rides, low massing, a miniature train loop",
	&"fairground": "games and a big top, strung out beside the entrance street",
}


# ---------------------------------------------------------------------------
# Places
# ---------------------------------------------------------------------------

## What the park has, and which section each thing belongs to.
##
## The distinction this table exists to hold is between **fact and
## stylization**. That a place exists, what it is called internally, roughly
## where it is, whether it is built, and which section it belongs to are facts,
## and drift in them is a bug — a foldout that keeps pointing at a passage after
## the passage moves is wrong, not stylized. Where it sits on a printed sheet,
## what the sign calls it and what the little note under it says are
## stylization, and belong to whatever is doing the drawing.
##
## So consumers take `id`, `section` and `built` from here and keep their own
## presentation. `map_view.gd`'s sheet coordinates are deliberately not to scale
## and should stay authored; a foldout that is a faithful projection is not a
## foldout. `at` is the true world position for the things that want it — the
## minimap is to scale and the massing model is the park.
##
## **The four thresholds used to be nameless, and now their sections are not.**
## The rule was that naming a section ahead of its design is inventing park
## content, and it held while nothing needed the park to read as a whole. Massing
## the park to its edges needs exactly that, so `SECTION_GROUND` above names all
## six and this table points the passages at them.
##
## What survives of the rule: `built` is still false for all four, the passages
## still bend and stop, `ParkSections.SECTIONS` still has no entry to mount, and
## a name here buys a footprint and a silhouette and nothing else. `id` on a
## `way_` entry is still a bearing mnemonic rather than a place name — the place
## is the section entry beside it.
const PLACES := [
	{"id": &"plaza", "at": Vector2(0.0, 0.0), "section": &"plaza", "built": true},
	{"id": &"photo_hut", "at": PHOTO_HUT_AT, "section": &"plaza", "built": true},
	{"id": &"gate", "at": Vector2(STREET_X, GATE_Z), "section": &"plaza", "built": true},
	{"id": &"apron", "at": Vector2(STREET_X, APRON_Z), "section": &"plaza", "built": true},
	{"id": &"overlook", "at": OVERLOOK_AT, "section": &"plaza", "built": true},

	## Behind the gate at the foot of the stair, and the three things standing on
	## it. `built` on these tracks what the generator has actually emitted, which
	## is the only honest thing for a map to draw.
	{"id": &"boardwalk", "at": Vector2(FRONT_X, ALLEY_Z), "section": &"boardwalk", "built": true},
	{"id": &"wheel", "at": WHEEL_AT, "section": &"boardwalk", "built": false},
	{"id": &"coaster", "at": COASTER_STATION, "section": &"boardwalk", "built": false},
	{"id": &"pier", "at": PIER_ROOT, "section": &"boardwalk", "built": false},
	{"id": &"pavilion", "at": PAVILION_AT, "section": &"boardwalk", "built": false},

	## Passages that bend and stop, and the sections behind them. Massed, not
	## built: there is a shape on the horizon and nothing to walk into.
	{"id": &"way_nnw", "at": Vector2(-13.0, -39.5), "section": &"grove", "built": false},
	{"id": &"way_ne", "at": Vector2(39.5, -21.0), "section": &"frontier", "built": false},
	{"id": &"way_se", "at": Vector2(39.5, 24.0), "section": &"kiddieland", "built": false},
	{"id": &"way_sw", "at": Vector2(-24.0, 39.5), "section": &"fairground", "built": false},

	{"id": &"grove", "at": SECTION_GROUND[&"grove"]["at"], "section": &"grove", "built": false},
	{"id": &"frontier", "at": SECTION_GROUND[&"frontier"]["at"], "section": &"frontier", "built": false},
	{"id": &"kiddieland", "at": SECTION_GROUND[&"kiddieland"]["at"], "section": &"kiddieland", "built": false},
	{"id": &"fairground", "at": SECTION_GROUND[&"fairground"]["at"], "section": &"fairground", "built": false},
]


# ---------------------------------------------------------------------------
# Walkways
# ---------------------------------------------------------------------------

## The park's circulation, as centre lines.
##
## This is the part that did not exist anywhere before. The corner minimap was
## drawing `crowd.nodes`/`crowd.edges` because it was the only path-shaped data
## in the project, but that graph is a *wander* graph — somewhere for a guest to
## meander between — and drawn directly it reads as a wireframe web rather than
## as walkways. The two are genuinely different objects: one is where a body may
## drift, the other is where the paving is.
##
## A park's plan *is* its circulation. Disneyland's plan is a hub and spokes,
## and that is a statement about walkways, not about buildings — so this is the
## first thing in the file that is really the plan rather than a measurement.
##
## Points are 2D, in world x/z, metres. Each entry is a polyline rather than a
## graph: consumers that need a network can join them at their shared endpoints,
## and a list of runs is what a drawn map wants anyway.
## **Re-derived against the 104m perimeter on 2026-08-13.** Every spoke now
## leaves the ring at the vertex nearest its threshold's bearing and doglegs
## once or twice around whatever is in the way, and each is checked to clear
## every colliding structure by at least 1.4m along its centre line. The one
## exception is `spoke_west`, which measures 0.8m — against the overlook coping
## it terminates at, because the parapet is the thing you walk up to.
const WALKWAYS := {
	## Around the fountain, outside its skirt. Twelve segments rather than a
	## circle primitive so that a consumer can draw it with the same code it
	## draws everything else with.
	&"plaza_ring": [
		Vector2(16.0, 0.0), Vector2(13.86, 8.0), Vector2(8.0, 13.86),
		Vector2(0.0, 16.0), Vector2(-8.0, 13.86), Vector2(-13.86, 8.0),
		Vector2(-16.0, 0.0), Vector2(-13.86, -8.0), Vector2(-8.0, -13.86),
		Vector2(0.0, -16.0), Vector2(8.0, -13.86), Vector2(13.86, -8.0),
		Vector2(16.0, 0.0),
	],

	## South out of the plaza and down the street to the gate and the apron.
	## The dogleg is real: the ring is centred on the fountain and the street
	## is not, so the walk bends onto the street's centre line rather than
	## meeting it at an angle.
	##
	## This run is pinched twice and the centre line is threading a gap rather
	## than crossing open ground — `bench_south` at (−5, 19) and `bench_se` at
	## (2, 22) leave about 5m between them, and the two south planters at
	## (−7, 26) and (4, 26) leave about 8m. Hence the narrow width below; a
	## generous spoke here would be paving drawn straight through the furniture.
	##
	## Worth recording because the crowd's wander graph has **no south through
	## route at all** — `gen_crowd.gd` validates at 0.45 clearance and finds no
	## walkable gap, so a guest never crosses here. That is a real fact about
	## the plaza rather than a bug in either description: a person can walk it,
	## a wandering guest is not given it. The two disagree on purpose.
	&"spoke_south": [
		Vector2(0.0, 16.0), Vector2(-1.5, 30.0), Vector2(-1.5, STREET_FROM_Z),
	],
	&"street": [
		Vector2(STREET_X, STREET_FROM_Z), Vector2(STREET_X, GATE_Z),
	],
	&"apron": [
		Vector2(STREET_X, GATE_Z), Vector2(STREET_X, APRON_Z),
	],

	## West, under the arch and out onto the terrace. Straight, and you can see
	## the whole length of it — which is exactly why the section boundary is not
	## here but at the foot of the stair.
	&"spoke_west": [
		Vector2(-16.0, 0.0), Vector2(-30.0, -2.0), Vector2(ARCH_AT.x, ARCH_AT.y),
		Vector2(OVERLOOK_AT.x, OVERLOOK_AT.y),
	],

	## Off the north end of the terrace and down the bluff. Two flights with the
	## turn between them, which is the seam the boardwalk loads behind.
	&"west_stair": [
		Vector2(-46.0, -6.0), Vector2(-50.0, STAIR_TOP_Z),
		Vector2(STAIR_TURN_X, STAIR_TOP_Z), Vector2(STAIR_FOOT.x, STAIR_FOOT.z),
	],

	## The boardwalk, below and west of everything above.
	##
	## Five runs and they are read in order by anybody walking in: off the stair
	## foot, north or south a few metres up the back lane, west through the alley
	## in the frontage, and only then the promenade — which is where the water,
	## the pier and the wheel all arrive at once. The pier is the sixth thing and
	## the only one that goes anywhere new.
	##
	## The back lane is short on purpose. It is a service road with the bluff on
	## one side and the backs of buildings on the other, and its whole job is to
	## be the twenty metres before the reveal rather than somewhere to spend time.
	&"boardwalk_arrival": [
		Vector2(STAIR_FOOT.x, STAIR_FOOT.z), Vector2(BACK_LANE_X, 1.5),
	],
	&"boardwalk_lane": [
		Vector2(BACK_LANE_X, -30.0), Vector2(BACK_LANE_X, 40.0),
	],
	&"boardwalk_alley": [
		Vector2(BACK_LANE_X, ALLEY_Z), Vector2(PROMENADE_X, ALLEY_Z),
	],
	&"boardwalk_promenade": [
		Vector2(PROMENADE_X, WALK_FROM_Z), Vector2(PROMENADE_X, WALK_TO_Z),
	],
	&"boardwalk_pier": [
		PIER_ROOT, Vector2(PIER_ROOT.x - PIER_LENGTH, PIER_ROOT.y),
	],

	## The four spokes to the scaffolded thresholds. Each runs from the ring to
	## the mouth of its passage; what happens past the mouth belongs to the
	## passage, and past the bend belongs to a section that does not exist yet.
	##
	## **These were straight, and three of them ran through buildings.** Written
	## when this file's only consumer was the minimap, they were drawn as rays
	## from the ring to each threshold and never checked against `plaza.tscn`,
	## which is hand-placed and did not agree: `spoke_ne` spent 21m inside
	## `perim_e_north`, `spoke_se` 28m inside `perim_e_south`, `spoke_sw` 11m
	## inside `building_south_west`. On a map at that scale a line through a wall
	## is a few pixels and looks like nothing. Paving them made it visible in one
	## screenshot, which is the whole argument for a plan being built rather than
	## only drawn.
	##
	## So they are doglegs now, and the doglegs are facts about the plaza rather
	## than decoration: every one of them is the way round a building that is
	## already there. Each keeps at least 1.4m of clearance from anything a body
	## collides with, measured along the centre line — enough that the route is
	## walkable, not merely drawable.
	##
	## Two of them start from a different point on the ring than they used to,
	## because the old start was on the wrong side of an obstacle: `spoke_se`
	## from due east rather than the south-east vertex, since the photo hut sits
	## square in the way of the latter, and `spoke_sw` from the south-south-west
	## vertex to get east of the planters.

	## East of the bandstand, then into the twelve-metre corridor between
	## `building_north` and `perim_nw` that the north wall's gap opens onto.
	&"spoke_nnw": [
		Vector2(-8.0, -13.86), Vector2(-14.0, -30.0), Vector2(-16.9, -51.5),
	],

	## North of `perim_e_north`, past the foot of the sign tower, and out through
	## the gap between `wall_east_north` and `wall_east_mid`. The tower is 3.6m
	## off the centre line, which is close, and right: a clock you walk past is
	## worth more than a clock you look at.
	&"spoke_ne": [
		Vector2(13.86, -8.0), Vector2(30.0, -24.0), Vector2(51.5, -27.4),
	],

	## Off the ring due east, south down the eight-metre street between the photo
	## hut and `building_east`, then east again between `perim_e_south` and
	## `building_south_east`.
	##
	## It leaves from the 90° vertex rather than the 120° one that actually
	## points at the threshold, and that is the photo hut's doing: the hut
	## occupies x 6.5..11.5 directly south of the 120° vertex, so every line
	## south-east from there goes through it. Leaving east and bending is the
	## move Disneyland's hub makes anyway — a spoke aims at a land, it does not
	## have to be a ray to it.
	##
	## The street it runs down was already there and had the cafe terrace in it,
	## which is why the terrace moved. See `PLAZA_CAFE`.
	&"spoke_se": [
		Vector2(13.86, 8.0), Vector2(27.0, 13.0), Vector2(34.0, 26.0),
		Vector2(51.5, 31.3),
	],

	## The long way round, and there is no short one. West of
	## `building_south_west` the gap between it and `perim_w_south` is two metres
	## for one metre of depth — a squeeze a person could make and a walkway
	## cannot — so the route goes down its east flank and back west along the
	## south wall.
	&"spoke_sw": [
		Vector2(-8.0, 13.86), Vector2(-28.0, 30.0), Vector2(-31.3, 51.5),
	],
}

## How wide each run is paved, in metres. Kept beside the centre lines rather
## than inside them so a polyline stays a polyline — a consumer that only wants
## the line does not have to skip a field, and one that draws paving looks the
## width up.
const WALKWAY_WIDTH := {
	&"plaza_ring": 8.0,
	## Narrow because of the bench and planter pinch — see `spoke_south` above.
	&"spoke_south": 6.0,
	&"street": 15.0,
	&"apron": 15.0,
	&"spoke_west": 8.0,
	&"west_stair": 2.6,
	&"boardwalk_arrival": 4.0,
	&"boardwalk_lane": 6.0,
	## The alley is the width of the hole in the frontage, which is what makes it
	## an alley rather than a gap you walk past.
	&"boardwalk_alley": 6.0,
	## Wide, because it is the only walkway in the park that has to hold a crowd
	## standing still and looking at something. 17.5m of shore less a little.
	&"boardwalk_promenade": 16.0,
	&"boardwalk_pier": 8.0,
	&"spoke_nnw": 8.0,
	&"spoke_ne": 8.0,
	&"spoke_se": 7.0,
	&"spoke_sw": 6.0,
}


# ---------------------------------------------------------------------------
# Reading it
# ---------------------------------------------------------------------------

## Every walkway as a flat list of (from, to) segment pairs, which is what a
## line-drawing consumer actually wants. Built rather than stored so the
## polylines above stay the single description.
static func walkway_segments() -> Array:
	var out := []
	for id in WALKWAYS:
		var run: Array = WALKWAYS[id]
		for i in run.size() - 1:
			out.append({"id": id, "from": run[i], "to": run[i + 1],
				"width": WALKWAY_WIDTH.get(id, 6.0)})
	return out


## A place by id, or an empty dictionary. Same reasoning as `threshold()`: the
## order of `PLACES` is not part of the plan, so nothing should index it.
static func place(id: StringName) -> Dictionary:
	for p in PLACES:
		if p["id"] == id:
			return p
	return {}


## The places belonging to a section. An empty `of` returns the ones that belong
## to no section — the four passages that bend and stop, which is the set a
## drawing wants when it needs to show the park has more ways out than places.
static func places_in(of: StringName) -> Array:
	var out := []
	for p in PLACES:
		if p["section"] == of:
			out.append(p)
	return out


## A threshold by name, or an empty dictionary. Callers that want to place
## something at a passage mouth should ask for it rather than index `THRESHOLDS`
## by position, because the order of that array is not part of the plan.
static func threshold(nm: String) -> Dictionary:
	for t in THRESHOLDS:
		if t["name"] == nm:
			return t
	return {}


## Everything solid in the plaza, as axis-aligned footprints.
##
## Up here because three things need it and were each holding their own copy:
## `plaza.tscn` has the boxes, `gen_crowd.gd` needs them to know which of its
## wander edges are walkable, and `gen_props.gd` needs them to know where it may
## and may not stand a tree. Two of the three read this now. The scene cannot —
## a `.tscn` has nowhere to put an expression — so it stays the duplicate, and
## the crowd's graph validator is the test that catches them disagreeing. It has
## caught it four times in one day, so it is a test that works.
##
## Order is the order they ring the plaza, so a missing one is visible.
const PLAZA_MASSES := [
	# north side, inner face z = -36
	{"at": Vector2(-36.45, -41.5), "half": Vector2(11.55, 5.5)},
	{"at": Vector2(2.55, -41.5), "half": Vector2(11.45, 5.5)},
	{"at": Vector2(25.0, -41.5), "half": Vector2(11.0, 5.5)},
	# east side, inner face x = 36
	{"at": Vector2(41.5, -41.7), "half": Vector2(5.5, 6.3)},
	{"at": Vector2(41.5, -8.7), "half": Vector2(5.5, 10.7)},
	{"at": Vector2(41.5, 13.4), "half": Vector2(5.5, 11.4)},
	{"at": Vector2(41.5, 42.9), "half": Vector2(5.5, 5.1)},
	# south side, inner face z = 36
	{"at": Vector2(-42.15, 41.5), "half": Vector2(5.85, 5.5)},
	{"at": Vector2(-17.65, 41.5), "half": Vector2(8.65, 5.5)},
	{"at": Vector2(16.5, 41.5), "half": Vector2(10.5, 5.5)},
	{"at": Vector2(37.5, 41.5), "half": Vector2(10.5, 5.5)},
	# west side, inner face x = -33, set in for the overlook terrace
	{"at": Vector2(-38.5, -35.5), "half": Vector2(5.5, 12.5)},
	{"at": Vector2(-38.5, -16.0), "half": Vector2(5.5, 7.0)},
	{"at": Vector2(-38.5, 14.5), "half": Vector2(5.5, 10.5)},
	{"at": Vector2(-38.5, 36.5), "half": Vector2(5.5, 11.5)},
	{"at": Vector2(-38.5, -8.0), "half": Vector2(5.5, 1.5)},
	{"at": Vector2(-38.5, 4.0), "half": Vector2(5.5, 1.5)},
	# inside
	{"at": CLOCK_TOWER_AT, "half": Vector2(2.8, 2.8)},
	{"at": PHOTO_HUT_AT, "half": Vector2(4.0, 3.25)},
	{"at": Vector2(-20.0, -20.0), "half": Vector2(5.5, 5.5)},
	{"at": Vector2(-12.0, 25.0), "half": Vector2(1.8, 1.8)},
	{"at": Vector2(8.0, 29.0), "half": Vector2(1.8, 1.8)},
]


## How far a point is from the nearest of them, 0 if inside one.
static func mass_clearance(p: Vector2) -> float:
	var best := 1e9
	for m in PLAZA_MASSES:
		var at: Vector2 = m["at"]
		var half: Vector2 = m["half"]
		var dx: float = maxf(absf(p.x - at.x) - half.x, 0.0)
		var dz: float = maxf(absf(p.y - at.y) - half.y, 0.0)
		best = minf(best, Vector2(dx, dz).length())
	return best


## How far a point is from the nearest walkway's *paved edge* — negative when it
## is standing in the road.
static func walkway_clearance(p: Vector2) -> float:
	var best := 1e9
	for run in walkway_segments():
		var a: Vector2 = run["from"]
		var b: Vector2 = run["to"]
		var d := b - a
		var l2 := d.length_squared()
		var t := 0.0 if l2 < 0.0001 else clampf((p - a).dot(d) / l2, 0.0, 1.0)
		best = minf(best, (p - (a + d * t)).length() - float(run["width"]) * 0.5)
	return best


## Somewhere in the plaza's outer room to stand something.
##
## Generated by rejection rather than listed, and that is the lesson of the
## afternoon rather than a preference: the plaza had just grown 60% and moved
## every landmark in it, and hand-typing another 150 coordinates against a
## layout that new is how the last four coordinate mistakes happened. A
## candidate is thrown out if it stands in a walkway, inside a building, or on
## top of something already placed — so the rules are stated once and the
## positions fall out of them.
##
## Deterministic: this file is committed, so the same source has to produce the
## same scene or every run is a diff.
##
## Positions come out in *final* coordinates. `gen_props.gd` stands props on
## them and `gen_crowd.gd` asks for the same points with the same arguments so
## its guests route around the ones worth routing around — which is why this is
## here and not in either of them.
static func open_spots(count: int, salt: int, r_min: float, r_max: float,
		clear: float, apart: float) -> Array:
	var rng := RandomNumberGenerator.new()
	rng.seed = 0x5EED0000 + salt
	var out: Array = []
	var tries := 0
	while out.size() < count and tries < count * 400:
		tries += 1
		var a := rng.randf() * TAU
		# Square-rooted so the sample is even by area rather than by radius,
		# which otherwise crowds everything against the inner edge.
		var r := sqrt(lerpf(r_min * r_min, r_max * r_max, rng.randf()))
		var p := Vector2(sin(a) * r, -cos(a) * r)
		if absf(p.x) > PLAZA_HALF - 6.0 or absf(p.y) > PLAZA_HALF - 6.0:
			continue
		if walkway_clearance(p) < clear:
			continue
		if mass_clearance(p) < clear:
			continue
		var ok := true
		for q in out:
			if p.distance_to(q) < apart:
				ok = false
				break
		if ok:
			out.append(p)
	if out.size() < count:
		push_warning("_open_spots: wanted %d, placed %d" % [count, out.size()])
	return out


## Points spaced round the ring walkway's outer verge, skipping wherever a spoke
## leaves it.
##
## Benches went here after being scattered through the open ground first, and
## the reason is the crowd rather than the look: **open ground is what the
## wander graph is made of.** Anything bench-sized dropped into it lands on an
## edge, and the validator threw out four at once. A bench beside the paving is
## both what a park actually does and the only place a 2m obstacle does not
## fight the routes — the graph's ring nodes sit on the centre line, five metres
## inside these.
static func ring_verge(offset: float, clear: float) -> Array:
	var out: Array = []
	var r := RING_RADIUS + RING_WIDTH * 0.5 + offset
	for i in 16:
		var a := TAU * float(i) / 16.0
		var p := Vector2(sin(a) * r, -cos(a) * r)
		if walkway_clearance(p) < clear or mass_clearance(p) < clear:
			continue
		out.append(p)
	return out


## Where a point in the 80m plaza lands in the 104m one.
##
## Not a scale factor, because the plaza did not scale: the hub grew by 1.8, the
## annulus around it by rather more, and the wall line by 1.3. A single
## multiplier would have put the benches inside the fountain. So this is a
## piecewise-linear map on *radius* through the five landmarks that did move —
## the fountain's rim, the ring's centre line, the ring's outer edge, the
## perimeter's inner face, and the wall — and everything between them keeps the
## relative position it held before. A bench 2.5m off the old fountain comes out
## 2.5m off the new one's inner walk.
##
## Here rather than in a generator because **both of them need it**: 214 props
## are placed against the old dimensions in `gen_props.gd`, and `gen_crowd.gd`
## has to know where those props ended up in order to route around them. Two
## copies of this map would be two different plazas.
##
## Apply it to an assembly's *base*, never to its finished parts — the local
## scale factor is up to 1.6, so dilating a bench's four boxes one by one moves
## the legs out from under the seat.
const PLAZA_DILATE := [
	[0.0, 0.0], [5.0, 9.0], [9.5, 16.0], [12.5, 20.0], [21.0, 36.0], [39.0, 51.0],
]


static func plaza_out(p: Vector3) -> Vector3:
	var r := Vector2(p.x, p.z).length()
	if r < 0.001:
		return p
	var out := r + 12.0
	for i in PLAZA_DILATE.size() - 1:
		var a: Array = PLAZA_DILATE[i]
		var b: Array = PLAZA_DILATE[i + 1]
		if r <= b[0]:
			out = lerpf(a[1], b[1], (r - a[0]) / (b[0] - a[0]))
			break
	var k := out / r
	return Vector3(p.x * k, p.y, p.z * k)


## The same, for a point on the ground plane.
static func plaza_out2(p: Vector2) -> Vector2:
	var v := plaza_out(Vector3(p.x, 0.0, p.y))
	return Vector2(v.x, v.z)


## Compass bearing from the fountain to a point, in degrees from north. The
## design documents describe the thresholds this way and `map_view.gd` draws
## them from bearings, so the conversion lives here rather than in each.
static func bearing_to(at: Vector2) -> float:
	var d := at - FOUNTAIN_AT
	return fposmod(rad_to_deg(atan2(d.x, -d.y)), 360.0)
