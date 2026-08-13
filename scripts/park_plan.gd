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

## The hub, 80m square with the fountain at the origin. `scenes/world/plaza.tscn`
## builds the ground from these; the reference parks put Disneyland's Central
## Plaza at about 60m, and the extra 20 is what carries Knott's density.
const PLAZA_CENTRE := Vector2(0.0, 0.0)
const PLAZA_HALF := 40.0

## The fountain, and its skirt. The ring walkway is set outside this.
const FOUNTAIN_AT := Vector2(0.0, 0.0)
const FOUNTAIN_RADIUS := 5.0

## The photo hut — the job's anchor, and the one building in the plaza the
## player has business inside. Occupies x 6.5..11.5, z 6..10.
const PHOTO_HUT_AT := Vector2(9.0, 8.0)


# ---------------------------------------------------------------------------
# The ways out — six of them, in a 320m perimeter
# ---------------------------------------------------------------------------

## The west arch: a straight tube through the wall at x ≈ −24, its opening
## running z −5.6..1.6 between the two piers.
const ARCH_AT := Vector2(-24.0, -2.0)

## The overlook, past the arch and above the boardwalk. The parapet is at
## x −38.5; this stands short of it, where you actually end up walking.
const OVERLOOK_AT := Vector2(-37.0, -2.0)

## The four scaffolded passages, moved here verbatim from `gen_props.gd`.
##
## Bearings are approximate on purpose. The star is a skeleton — points anchor a
## section's centre line, edges are free — so these sit where the perimeter had
## room rather than on exact rays. From the fountain: roughly 342, 62, 121 and
## 211 degrees, against a west arch at 273 and the entrance street at 182.
const THRESHOLDS := [
	{"name": "nnw", "at": Vector3(-13.0, 0.0, -39.5), "theta": PI, "width": 12.0, "turn": 1.0},
	{"name": "ne", "at": Vector3(39.5, 0.0, -21.0), "theta": PI * 0.5, "width": 12.0, "turn": 1.0},
	{"name": "se", "at": Vector3(39.5, 0.0, 24.0), "theta": PI * 0.5, "width": 10.0, "turn": -1.0},
	{"name": "sw", "at": Vector3(-24.0, 0.0, 39.5), "theta": 0.0, "width": 8.0, "turn": -1.0},
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
const STREET_FROM_Z := 38.0
const GATE_Z := 95.0
const APRON_Z := 111.0


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
const SHORE_FROM_X := -44.0
const SHORE_EDGE := -80.0

## The frontage line — the row one building deep, 9m of it, so the buildings
## occupy x -62.5..-53.5. East of them is the back lane against the bluff, west
## of them is the promenade.
const FRONT_X := -58.0
const FRONT_DEPTH := 9.0

## The two bands either side of the frontage, as centre lines.
##
## The back lane is the service side and the side the player arrives on. That is
## not an accident of where the stair lands: coming down off the bluff behind
## the buildings and reaching the water only after passing *through* them is the
## reveal, and it is the same trick the arch and the gap already play at a
## larger scale.
const BACK_LANE_X := -49.8
const PROMENADE_X := -71.2

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
const STAIR_TURN_X := -44.7

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
const STAIR_FOOT := Vector3(-44.7, -6.0, 5.5)
const STAIR_FOOT_STAND := Vector3(-44.0, -5.8, 5.5)
## Six and a half metres south of the gate rather than level with it, and that
## gap is doing work. Level with the gate is level with the *hole in the
## frontage* — they are at the same z — so the player arrived already looking
## down the alley at the wheel and the water, and the reveal fired during the
## fade. Screenshots caught it; nothing else could have.
##
## From here the custard unit is between the player and the gap, so the walk is
## twelve metres of service lane and then a corner. The gate they came through is
## passed on the right, which nobody notices and which no test can object to.
const BOARDWALK_ARRIVAL := Vector3(-49.5, -5.8, 12.0)
const BOARDWALK_ARRIVAL_YAW := 0.15

## The gate itself, as the plane both sections build against. The well is 2.6m
## wide and its west face is the bluff's, so the gate hangs a hair proud of it.
const FOOT_GATE_X := -46.1


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
const WHEEL_AT := Vector2(-75.0, -16.0)
const WHEEL_RADIUS := 13.2
const WHEEL_PLATFORM := Vector2(8.0, 26.0)

## The coaster closes the north end. Out-and-back along the shore, station
## fronting the promenade, structure running away from the player — so it is a
## thing you walk towards and then walk under, rather than a thing you look at.
const COASTER_STATION := Vector2(-66.0, -38.0)
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
	Vector2(-65.5, -13.5), Vector2(-65.5, -10.0),
	Vector2(-65.5, 8.0), Vector2(-65.5, 11.5),
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
	&"plaza": {"at": Vector2(0.0, 0.0), "size": Vector2(80.0, 80.0), "floor_y": 0.0},
	&"boardwalk": {
		"at": Vector2((SHORE_FROM_X + SHORE_EDGE) * 0.5, 0.0),
		"size": Vector2(SHORE_FROM_X - SHORE_EDGE, 340.0),
		"floor_y": SHORE_TOP,
	},
	&"grove": {"at": Vector2(-8.0, -92.0), "size": Vector2(62.0, 84.0), "floor_y": 0.0},
	&"frontier": {"at": Vector2(96.0, -54.0), "size": Vector2(90.0, 76.0), "floor_y": 0.0},
	&"kiddieland": {"at": Vector2(84.0, 56.0), "size": Vector2(58.0, 58.0), "floor_y": 0.0},
	&"fairground": {"at": Vector2(-25.0, 80.0), "size": Vector2(26.0, 76.0), "floor_y": 0.0},
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
const WALKWAYS := {
	## Around the fountain, outside its skirt. Twelve segments rather than a
	## circle primitive so that a consumer can draw it with the same code it
	## draws everything else with.
	&"plaza_ring": [
		Vector2(9.5, 0.0), Vector2(8.2, 4.75), Vector2(4.75, 8.2),
		Vector2(0.0, 9.5), Vector2(-4.75, 8.2), Vector2(-8.2, 4.75),
		Vector2(-9.5, 0.0), Vector2(-8.2, -4.75), Vector2(-4.75, -8.2),
		Vector2(0.0, -9.5), Vector2(4.75, -8.2), Vector2(8.2, -4.75),
		Vector2(9.5, 0.0),
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
		Vector2(0.0, 9.5), Vector2(-1.5, 20.0), Vector2(-1.5, STREET_FROM_Z),
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
		Vector2(-9.5, 0.0), Vector2(-16.0, -2.0), Vector2(ARCH_AT.x, ARCH_AT.y),
		Vector2(OVERLOOK_AT.x, OVERLOOK_AT.y),
	],

	## Off the north end of the terrace and down the bluff. Two flights with the
	## turn between them, which is the seam the boardwalk loads behind.
	&"west_stair": [
		Vector2(-34.0, -6.0), Vector2(-40.0, STAIR_TOP_Z),
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
	&"spoke_nnw": [
		Vector2(-4.75, -8.2), Vector2(-11.0, -22.0), Vector2(-13.0, -39.5),
	],
	&"spoke_ne": [
		Vector2(8.2, -4.75), Vector2(24.0, -12.0), Vector2(39.5, -21.0),
	],
	&"spoke_se": [
		Vector2(8.2, 4.75), Vector2(24.0, 13.0), Vector2(39.5, 24.0),
	],
	&"spoke_sw": [
		Vector2(-8.2, 4.75), Vector2(-17.0, 22.0), Vector2(-24.0, 39.5),
	],
}

## How wide each run is paved, in metres. Kept beside the centre lines rather
## than inside them so a polyline stays a polyline — a consumer that only wants
## the line does not have to skip a field, and one that draws paving looks the
## width up.
const WALKWAY_WIDTH := {
	&"plaza_ring": 6.0,
	## Narrow because of the bench and planter pinch — see `spoke_south` above.
	&"spoke_south": 5.0,
	&"street": 15.0,
	&"apron": 15.0,
	&"spoke_west": 7.0,
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
	&"spoke_nnw": 7.0,
	&"spoke_ne": 7.0,
	&"spoke_se": 6.0,
	&"spoke_sw": 5.0,
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


## Compass bearing from the fountain to a point, in degrees from north. The
## design documents describe the thresholds this way and `map_view.gd` draws
## them from bearings, so the conversion lives here rather than in each.
static func bearing_to(at: Vector2) -> float:
	var d := at - FOUNTAIN_AT
	return fposmod(rad_to_deg(atan2(d.x, -d.y)), 360.0)
