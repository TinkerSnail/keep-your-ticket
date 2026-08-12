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
const SHORE_EDGE := -70.0
const FRONT_X := -58.0

## The hole in the boardwalk frontage, aimed at the arch. The whole west
## composition is this: the arch frames a gap, the gap frames the pier.
const GAP_FROM := -8.0
const GAP_TO := 6.0

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
## the player rides that far above their floor, and `foot_z − 0.7` so they stand
## behind the crossing volume rather than inside it. That is what `ParkSections`
## arrives the player on coming back from the boardwalk, and it matches the
## `arrival_from_boardwalk` marker in `west_stair.tscn` to the digit.
##
## `BOARDWALK_ARRIVAL` is the far side of the same seam — where the player
## stands having gone *out* through the gate. Matches the `arrival_from_plaza`
## marker in `boardwalk_stub.tscn`, which is also what `tools/section_test.gd`
## currently asserts as a literal.
const STAIR_FOOT := Vector3(-44.7, -6.0, 5.5)
const STAIR_FOOT_STAND := Vector3(-44.7, -5.8, 4.8)
const BOARDWALK_ARRIVAL := Vector3(-44.7, -5.8, 14.0)


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
