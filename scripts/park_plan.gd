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
##
## Since 2026-08-14c this is the outer face of the pool's **coping**, and the
## fountain is generated into `scenes/world/plaza_fountain.tscn` rather than
## typed into `plaza.tscn`. The number did not move and nothing that routes
## around it had to change — which was the point of not moving it. What did
## change is that the ring is now a 52cm kerb you could sit on rather than a
## 90cm drum, so the footprint the crowd avoids and the thing a person meets are
## no longer the same height.
const FOUNTAIN_AT := Vector2(0.0, 0.0)
const FOUNTAIN_RADIUS := 9.0

## The coping, as the two numbers a *person* needs rather than the two a route
## needs. `FOUNTAIN_RADIUS` above is the footprint the crowd walks around; these
## are where somebody sits on it and how high that is.
##
## Here rather than in `gen_props.gd` because both generators need them and
## neither can read the other: `gen_props` builds the coping to this height and
## `gen_crowd` puts nine guests on it, and the two agreeing by having 0.52 typed
## into each is the drift that put the cafe terrace in three places at once.
##
## 0.52 is a decision and not a measurement. What stood here until 2026-08-14c
## was a 0.9m drum, which is a plinth you lean against; a kerb people sit on is
## about half a metre, and this one is fifty-four metres long, in the middle of
## the room, and the first thing the entrance street points at. It is the best
## seat in the plaza and it should look like it.
##
## The seat radius is on the *outer* half of the 0.8m coping, so legs hang over
## open paving rather than over the water.
const FOUNTAIN_RIM_TOP := 0.52
const FOUNTAIN_RIM_SEAT_R := 8.66

## The water, as the three numbers something outside `gen_props.gd` has to know
## in order to *point at* it.
##
## `gen_crowd.gd` aims the crowd's attention at the jets and the pool surface —
## those are the two parts of the fountain a person standing beside it actually
## watches — and it cannot read the generator that builds them. The alternative
## is the radius typed in both files, which is how the fountain's own POI came to
## be aimed at a column that no longer exists.
const FOUNTAIN_JET_R := 6.5
const FOUNTAIN_JET_TOP := 2.2
const FOUNTAIN_POOL_TOP := 0.30

## The bench by the photo hut, local to the hut so it follows if the hut moves.
##
## Here because **three** places want it: `gen_props` builds the bench and ties
## two balloons to its rail, `gen_crowd` seats a guest on it, and the POI list
## points at the balloons. It was typed into the first two separately, which is
## one copy short of the cafe terrace's three and the same failure waiting.
const PHOTO_HUT_BENCH := Vector3(-6.0, 0.0, -4.0)
const PHOTO_HUT_BENCH_YAW := 8.0

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

## The west arch: a straight tube through the wall, on the plaza's own west axis.
##
## **It became a tunnel on 2026-08-14.** 6m wide and 5m clear over 13.5m of
## depth, where it was 9 by 8.9 over 11 — a section nearly square is a hole in a
## wall, and the section swap that happens inside it had only the fade to hide
## behind. The extra depth is a gate house projecting into the plaza rather than
## a thicker wall, because the wall's west face is the terrace's east edge and
## the terrace has only six metres to give.
const ARCH_AT := Vector2(-39.0, -2.0)

## The two ends of the tube, as x. The mouth is the gate house's face, out in the
## plaza; the far end is the wall's west face, on the terrace. Everything that
## has to stop at the arch or start past it reads these rather than measuring
## `plaza.tscn` again.
const ARCH_MOUTH_X := -30.5
const ARCH_FAR_X := -44.0

## The clear opening between the piers, and under the lintel.
const ARCH_WIDTH := 6.0
const ARCH_HEIGHT := 5.0

## The overlook, past the arch and above the boardwalk. The parapet is at
## x −50.5; this stands short of it, where you actually end up walking.
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
const SHORE_TOP := -3.0
const WATER_TOP := -4.5

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
const SHORE_EDGE := -108.0

## The frontage line — the row one building deep, 9m of it, so the buildings
## occupy x -62.5..-53.5. East of them is the back lane against the bluff, west
## of them is the promenade.
const FRONT_X := -86.0
const FRONT_DEPTH := 9.0

## The two bands either side of the frontage, as centre lines.
##
## The back lane is the service side and the side the player arrives on. That is
## not an accident of where the stair lands: coming down off the bluff behind
## the buildings and reaching the water only after passing *through* them is the
## reveal, and it is the same trick the arch and the gap already play at a
## larger scale.
const BACK_LANE_X := -74.0
const PROMENADE_X := -99.2

## The bluff, as its two faces. The west one is the drop the cascade is built
## against; the east one is where the plaza's made ground takes over.
##
## **The drop is three metres, not six, since 2026-08-14b.** The shore came up to
## meet the plaza rather than the descent stretching to reach the shore, and the
## reason is arithmetic: a wheelchair gradient is 1:12, so six metres of drop is
## seventy-two metres of ramp no matter what shape it takes. Three metres is
## thirty-six, which fits one hairpin — and a 3m seawall is a thing you walk
## down rather than a cliff you are let off the side of.
const BLUFF_FACE_X := -58.0
const BLUFF_BACK_X := -51.0

## The cascade: the whole way down, as one monument on the arch's own axis.
##
## Modelled on the Cleveland Cascade in Oakland, which is a straight flight in
## the middle, a wall with an arched niche at its foot, and two wings sweeping
## out and down either side — a shape that reads, from the bottom, unmistakably
## like a ray with its wings spread. **The wings are the wall, not the path.**
## That is what lets one side be a ramp and the other a stair without the thing
## losing its symmetry: the wall follows the same hairpin both ways and only the
## surface riding on it differs.
##
## Three ways down, and nobody has to take a service entrance to use one:
## the central flight for anyone in a hurry, the north wing at 1:12 for a wheel-
## chair, and the south wing as a garden stair of short flights and long
## landings. They start together at the top and land together in the court —
## which is a claim `WING_SPRING_X` had to be rebuilt to make true, and which
## `walk_test` asks about by walking each of the three and checking where it
## came out.
const CASCADE_AXIS_Z := ARCH_AT.y
const CASCADE_TOP_X := BLUFF_FACE_X
const CASCADE_DROP := -SHORE_TOP

## The middle flight: wide, direct, and the whole drop in one go.
const FLIGHT_W := 10.0
const FLIGHT_RISE := 0.25
const FLIGHT_GOING := 0.55

## A wing, as the hairpin it is: out and down along the bluff face, a level
## landing at the turn, then back in and down to the court beside the flight's
## own foot.
##
## **It used to be one straight diagonal spending the whole 36m going away from
## the axis**, out to z ±42.5, and three separate things were wrong with that.
## It landed fourteen metres past the end of the back lane, on bare shore under
## the coaster — so "all three ways down land together in the court" was simply
## false, and a wheelchair taking the north wing arrived eighty-five metres from
## where the flight put everyone it came down with, which is the one thing this
## shape exists to prevent. Nothing in `WALKWAYS` described it, so no part of the
## park except `walk_test` believed the route existed at all. And 3m of fall
## stretched over 36m is a 4.8° slope: from the court the wings read as two low
## walls running off past the frame rather than as a way down.
##
## Doubling back fixes all three at once and costs nothing, because a landing is
## level — it carries none of the fall, so folding the run in half keeps the
## gradient at 1:12 exactly. Same 36m, half the reach, and the silhouette from
## the pier is better for it: two diagonals converging on the turn instead of one
## rail. What the pocket between the legs is for is the planting.
##
## The outbound leg runs true north–south against the bluff face, which is why
## its x never changes. That is not tidiness — it keeps the 0.3m slot between the
## wing's wall and the rock closed for the whole run, and it means the *only*
## sweep in plan is on the way back, aimed at the court.
const WING_SPRING_X := CASCADE_TOP_X - 3.2
const WING_SPRING_Z := FLIGHT_W * 0.5 + 2.6
const WING_TURN_X := WING_SPRING_X
const WING_TURN_Z := 27.0
const WING_SEP := 6.0
const WING_FOOT_X := -69.6
const WING_FOOT_Z := 7.0
const WING_W := 3.6

## The landing is a square the width of the ramp, and both of those numbers are
## the same number on purpose: a turn needs as much room across as the thing
## turning in it is wide, and a wheelchair turning 180° needs all of it.
##
## It is also **what sets `WING_TURN_Z`**, which is why the reach is 27m and not
## the 25 it was drawn at. The legs stop at the landing's inner edge rather than
## running to the turn vertex — anything else has the landing overhanging a ramp,
## and a level slab 20cm over a slope is a step in the middle of the descent. So
## the sloping run is the leg length *less half a landing at each end*, and
## getting 36m of that back out is what pushes the turn a metre and a half
## further out. The landing eats what it needs and the gradient does not move.
const WING_LAND_D := WING_W

## Where the flight lands, and where a body stands there.
const STAIR_FOOT := Vector3(
	CASCADE_TOP_X - FLIGHT_GOING * int(CASCADE_DROP / FLIGHT_RISE) - 1.2,
	SHORE_TOP, CASCADE_AXIS_Z)
const STAIR_FOOT_STAND := Vector3(STAIR_FOOT.x, SHORE_TOP + 0.2, CASCADE_AXIS_Z)

## How far north and south of the arch's axis the bluff top can be walked. The
## terrace's own end walls stand on these lines, and without something on them
## the parapet gap opens onto a seven-metre ledge running the length of the map.
const BLUFF_TOP_FROM_Z := -28.0
const BLUFF_TOP_TO_Z := 9.5


# ---------------------------------------------------------------------------
# The west seam
# ---------------------------------------------------------------------------

## **Moved from the foot of the stair to the arch on 2026-08-14.**
##
## It used to sit in front of a shut gate at the bottom of a turned flight —
## chosen because a load must not begin where the player can watch it, and the
## turn was what took the far side out of shot. An arch is the opposite: you can
## see clean through it from across the plaza, which is the whole reason the
## overlook works.
##
## What makes the arch usable anyway is that the camera stops following. The
## shot cuts to a fixed pose, the player walks out of frame under the arch, and
## only then does the screen go. Nothing the swap changes is on screen when it
## happens, so the cover no longer has to come from the geometry — which is the
## trade: the corridor bought cover with distance, and this buys it with framing.
##
## The gain is that every one of the six ways out can now be the same rule. Four
## of them are scaffolded passages that bend for cover they no longer need, and
## the two that matter are arches you walk under.
## Sized to the opening rather than to a number: a crossing volume narrower than
## the tube is a gap a body can walk through beside it, and the tube went from
## 9m to 6m when the arch became a tunnel.
const ARCH_SEAM_AT := Vector3(-38.5, 1.5, ARCH_AT.y)
const ARCH_SEAM_SIZE := Vector3(2.6, 3.0, ARCH_WIDTH)

## Out on the west spoke, seventeen metres of walking short of the arch. Less
## than the stair gave and enough: the hold adds a couple of seconds of its own
## on the far end, and the preload only has to be *started* before the crossing,
## not finished.
const ARCH_PRELOAD_AT := Vector3(-21.5, 1.5, ARCH_AT.y)
const ARCH_PRELOAD_SIZE := Vector3(4.0, 3.0, 13.0)

## Where the walk resumes, a stride past the tube on each side, still on the
## arch's centre line and still facing the way they were going. Yaw is radians
## and a Node3D looks down −Z, so +PI/2 is west and −PI/2 is east.
##
## The eastern one is measured off `ARCH_MOUTH_X` rather than typed, because it
## used to *be* −30.5 and the gate house then projected out to exactly there —
## which would have put the player down inside the tunnel mouth, in the crossing
## volume's own throat, on the frame after the swap.
const ARCH_ARRIVE_WEST := Vector3(ARCH_FAR_X - 2.0, 0.2, ARCH_AT.y)
const ARCH_ARRIVE_WEST_YAW := PI * 0.5
const ARCH_ARRIVE_EAST := Vector3(ARCH_MOUTH_X + 2.0, 0.2, ARCH_AT.y)
const ARCH_ARRIVE_EAST_YAW := -PI * 0.5

## The held shot, per direction. `from` is where the camera stands and `look` is
## what it points at; both are world coordinates, because a seam's framing is
## layout and belongs with the rest of the layout.
##
## Both stand **on the walkway**, and that is not an aesthetic choice. The first
## pair were set off to one side for a three-quarter view of the arch, and the
## westbound one came out looking at a tree trunk: the plaza's trees are
## scattered by `open_spots` over open ground, so anywhere off the paving is a
## place a tree may be standing this regeneration and not the last. The spokes
## are kept clear of masses and planting by construction, so a camera on the
## spoke's own centre line is the only pose that cannot be photobombed.
##
## What that costs is the crossing shot: the player walks away down the axis and
## recedes into the arch rather than crossing the frame. It reads as leaving,
## which is what they are doing, and the arch swallowing them is the exit.
const ARCH_HOLD_WEST := {
	"from": Vector3(-24.5, 3.5, -1.0),
	"look": Vector3(-42.0, 2.4, -2.2),
}
const ARCH_HOLD_EAST := {
	"from": Vector3(-48.5, 3.4, -2.0),
	"look": Vector3(-36.0, 2.6, -2.0),
}

## How long the player walks before the screen goes. Long enough to be under the
## arch and out of the frame at a walk, short enough that a player who wanted to
## keep playing is not waiting on a cutscene.
const ARCH_HOLD_SECONDS := 2.1


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
const FRONT_FROM_Z := -42.0
const FRONT_TO_Z := 68.0

## The hole in the frontage, aimed at the arch, and the alley through it. The
## whole west composition is this: the arch frames a gap, the gap frames the
## pier. The player walks the same line the composition is built on.
const GAP_FROM := -14.0
const GAP_TO := 10.0
const ALLEY_Z := ARCH_AT.y

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
const WHEEL_AT := Vector2(-103.0, -16.0)
const WHEEL_RADIUS := 13.2
const WHEEL_PLATFORM := Vector2(8.0, 26.0)

## The coaster closes the north end. Out-and-back along the shore, station
## fronting the promenade, structure running away from the player — so it is a
## thing you walk towards and then walk under, rather than a thing you look at.
const COASTER_STATION := Vector2(-94.0, -38.0)
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
	{"nm": "arcade", "from": FRONT_FROM_Z, "to": -30.0, "h": 8.5, "kind": "arcade"},
	{"nm": "gallery", "from": -30.0, "to": -22.0, "h": 6.0, "kind": "games"},
	{"nm": "corndogs", "from": -22.0, "to": GAP_FROM, "h": 5.5, "kind": "food"},
	{"nm": "custard", "from": GAP_TO, "to": 18.0, "h": 5.5, "kind": "food"},
	{"nm": "studio", "from": 18.0, "to": 26.0, "h": 6.5, "kind": "shop"},
	{"nm": "funhouse", "from": 26.0, "to": 38.0, "h": 11.0, "kind": "ride"},
	{"nm": "games", "from": 38.0, "to": 48.0, "h": 6.0, "kind": "games"},
	{"nm": "restrooms", "from": 48.0, "to": 55.0, "h": 4.5, "kind": "plain"},
	{"nm": "shuttered", "from": 55.0, "to": 62.0, "h": 6.0, "kind": "shut"},
	{"nm": "taffy", "from": 62.0, "to": FRONT_TO_Z, "h": 5.5, "kind": "shop"},
]

## Where somebody can sit down, which two different generators have to agree
## about — `gen_props.gd` builds the furniture and `gen_crowd.gd` puts people on
## it. The plaza's equivalents are duplicated between the two tools on purpose,
## with a comment saying a stale copy shows up as guests sitting in mid-air. That
## was the right call when there was nowhere better to put them; there is now.
const TABLES := [
	Vector2(-93.5, -20.0), Vector2(-93.5, -16.5),
	Vector2(-93.5, 12.0), Vector2(-93.5, 15.5),
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
	## Out to the pavilion rather than to the water's edge. The pier is ground
	## the player walks on and it reaches forty-four metres past the shore, so a
	## footprint that stopped at `SHORE_EDGE` had the whole pier outside the
	## section — which the crowd's own validator says out loud as soon as a node
	## is put on it.
	&"boardwalk": {
		"at": Vector2((SHORE_FROM_X + PAVILION_AT.x - 12.0) * 0.5, 0.0),
		"size": Vector2(SHORE_FROM_X - PAVILION_AT.x + 12.0, 340.0),
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

	## West off the ring, in at the mouth of the arch, through the tunnel and out
	## onto the terrace. **One run, and it has to be one run.**
	##
	## The two vertices in the middle are the tunnel's ends, and they are here so
	## that a consumer can tell where it starts and stops without measuring the
	## arch — the paving stops at the piers, because asphalt is the plaza's
	## circulation and a passage under a building is not it, so you cross onto the
	## plaza's own brick to walk through and it picks up again on the far side.
	## That is a fact about the paving and not about the route.
	##
	## Which is worth stating plainly, because it was got wrong on 2026-08-14: the
	## run was cut at the mouth so that the paving would stop there, and the map
	## promptly drew the way west as a stub ending at a wall with the terrace
	## floating thirteen metres beyond it. **`WALKWAYS` is where the player can
	## go. What is paved is `_pave_run`'s business**, and it takes a range for
	## exactly this reason.
	&"spoke_west": [
		Vector2(-16.0, 0.0), Vector2(-26.0, -2.0), Vector2(ARCH_MOUTH_X, ARCH_AT.y),
		Vector2(ARCH_FAR_X, ARCH_AT.y), Vector2(OVERLOOK_AT.x, OVERLOOK_AT.y),
	],

	## Across the terrace to the north end of it, out through the gap in the
	## parapet, and down the bluff in two flights with the turn between them.
	##
	## **It used to start at (−46, −6) and cut the corner diagonally**, which was
	## a line on a minimap and not a route: it left `spoke_west` and the stair as
	## two runs with four metres of nothing between them, so the plan described a
	## walk that stopped at a parapet and a stair that began in mid-air. It starts
	## on the west spoke's own centre line now and turns square, which is also
	## what lets the first two segments be paved — they are the only part of the
	## descent that is ground rather than treads, and they are what tells a player
	## standing under the arch that the way on is to their right.
	## West across the terrace and the bluff top, and straight on down the flight.
	##
	## **Three vertices on one line**, where this was a Z with a doubling-back in
	## it as recently as this afternoon. See `CASCADE_AXIS_Z` for why it could not be a
	## line until the court got wide enough to hold the run.
	##
	## The first segment is ground and is paved; the second is the flight.
	&"west_stair": [
		Vector2(-46.0, CASCADE_AXIS_Z), Vector2(CASCADE_TOP_X, CASCADE_AXIS_Z),
		Vector2(STAIR_FOOT.x, CASCADE_AXIS_Z),
	],

	## The other two ways down, and **they were in no graph at all until the wings
	## were rebuilt.** `west_stair` above described the central flight and nothing
	## described the ramp or the garden stair, so the minimap drew one way off the
	## bluff where there are three, and every rule that reads the park's
	## circulation — where a prop may stand, where the paving goes — was answering
	## about a monument two thirds of which it could not see.
	##
	## Four vertices each, and they are `wing_path`'s four points flattened: the
	## springing, the two ends of the landing, the foot. Written as constants
	## rather than called, because a `const` dictionary cannot hold a function
	## call — so if these and `wing_path` ever disagree it is because somebody
	## edited one, which is what `walk_test` walking the wings is there to catch.
	&"west_wing_north": [
		Vector2(WING_SPRING_X, CASCADE_AXIS_Z - WING_SPRING_Z),
		Vector2(WING_TURN_X, CASCADE_AXIS_Z - WING_TURN_Z),
		Vector2(WING_TURN_X - WING_SEP, CASCADE_AXIS_Z - WING_TURN_Z),
		Vector2(WING_FOOT_X, CASCADE_AXIS_Z - WING_FOOT_Z),
	],
	&"west_wing_south": [
		Vector2(WING_SPRING_X, CASCADE_AXIS_Z + WING_SPRING_Z),
		Vector2(WING_TURN_X, CASCADE_AXIS_Z + WING_TURN_Z),
		Vector2(WING_TURN_X - WING_SEP, CASCADE_AXIS_Z + WING_TURN_Z),
		Vector2(WING_FOOT_X, CASCADE_AXIS_Z + WING_FOOT_Z),
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
	## Off the last tread and straight on west across the court to the entry. One
	## leg and no turn: the flight faces the way you were already going.
	&"boardwalk_arrival": [
		Vector2(STAIR_FOOT.x, CASCADE_AXIS_Z), Vector2(BACK_LANE_X, CASCADE_AXIS_Z),
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
	## Wider than the 6m tunnel it runs into, and deliberately: the last few
	## metres on the plaza side are a forecourt in front of the gate house rather
	## than a throat. Paved into the tunnel at this width it would bury a metre of
	## asphalt in each pier, which is the other half of why the paving stops at
	## the face while the route does not.
	&"spoke_west": 8.0,
	## The width of the flight it leads to.
	&"west_stair": FLIGHT_W,
	## The width of the deck, and no more. These run within a metre of the back
	## lane's own band at the turn, so the default 6m would have the two arguing
	## about ground neither of them is on.
	&"west_wing_north": WING_W,
	&"west_wing_south": WING_W,
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


## The four points a wing turns through, with their heights: the springing on
## the bluff top, the two ends of the landing at the turn, and the foot out in
## the court. `side` is −1 for the north wing and +1 for the south.
##
## Heights are computed from the running length rather than typed, so both legs
## come out at the same gradient and stay there when any of the constants above
## move. The landing is level, which is why it is two points and not one: it
## carries none of the fall and none of the run, and it is the whole reason a
## 36m ramp fits in an 18m reach.
##
## **Up here rather than in `gen_props.gd` because `walk_test.gd` was carrying
## its own copy of the old wing's arithmetic** — a second survey of the same
## geometry, which is the fault CLAUDE.md already records about the cafe tables.
## It meant the test could keep passing against a wing the generator had stopped
## building, which is the worst thing a walk test can do.
static func wing_path(side: float) -> Array:
	var a := Vector2(WING_SPRING_X, CASCADE_AXIS_Z + side * WING_SPRING_Z)
	var p := Vector2(WING_TURN_X, CASCADE_AXIS_Z + side * WING_TURN_Z)
	var q := Vector2(p.x - WING_SEP, p.y)
	var c := Vector2(WING_FOOT_X, CASCADE_AXIS_Z + side * WING_FOOT_Z)
	# Each leg's slope stops half a landing short of its turn vertex, so the fall
	# is shared over that and not over the level part. See `WING_LAND_D`.
	var half_land := WING_LAND_D * 0.5
	var l1 := a.distance_to(p) - half_land
	var l2 := q.distance_to(c) - half_land
	var turn_y := -CASCADE_DROP * l1 / (l1 + l2)
	return [
		Vector3(a.x, 0.0, a.y), Vector3(p.x, turn_y, p.y),
		Vector3(q.x, turn_y, q.y), Vector3(c.x, -CASCADE_DROP, c.y),
	]


## Where a leg's slope actually stops: the landing's inner edge, half a landing
## short of the turn vertex it routes through. `leg` is 0 for the outbound leg
## and 1 for the return. The stretch from here to the vertex is the landing, and
## it is level.
static func wing_leg_end(side: float, leg: int) -> Vector3:
	var path := wing_path(side)
	var from: Vector3 = path[0] if leg == 0 else path[3]
	var to: Vector3 = path[1] if leg == 0 else path[2]
	var d := Vector2(to.x - from.x, to.z - from.z)
	var e := from.lerp(to, 1.0 - (WING_LAND_D * 0.5) / d.length())
	# The height is the turn's, not the lerp's: the leg has finished falling by
	# the time it gets here, which is the whole distinction being drawn.
	return Vector3(e.x, to.y, e.z)


## The gradient a wing actually runs at, as 1 in this.
##
## Worth being able to ask rather than trusting the arithmetic: the ramp wing is
## the park's only wheelchair route off the bluff, 1:12 is the entire reason the
## drop was halved to 3m, and every one of the constants it falls out of is the
## kind of number that gets nudged against a screenshot.
static func wing_gradient() -> float:
	var path := wing_path(-1.0)
	var run := 0.0
	# Leg to leg-end, skipping the turn: the landing is level and is not run. A
	# gradient is fall over the distance that falls, and counting the turn — or
	# the last half-landing of either leg — would flatter it.
	for leg in 2:
		var from: Vector3 = path[0] if leg == 0 else path[3]
		var e := wing_leg_end(-1.0, leg)
		run += Vector2(from.x, from.z).distance_to(Vector2(e.x, e.z))
	return run / CASCADE_DROP


## A point on a wing, `t` of the way along it by distance — landing included, so
## `t` measures walking rather than falling.
static func wing_point(side: float, t: float) -> Vector3:
	var path := wing_path(side)
	var seg := PackedFloat32Array()
	var total := 0.0
	for i in 3:
		var v0: Vector3 = path[i]
		var v1: Vector3 = path[i + 1]
		var d := Vector2(v0.x, v0.z).distance_to(Vector2(v1.x, v1.z))
		seg.append(d)
		total += d
	var want := clampf(t, 0.0, 1.0) * total
	for i in 3:
		if want <= seg[i] or i == 2:
			var v0: Vector3 = path[i]
			var v1: Vector3 = path[i + 1]
			return v0.lerp(v1, 0.0 if seg[i] <= 0.0 else clampf(want / seg[i], 0.0, 1.0))
		want -= seg[i]
	return path[3]


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


## How good a place to stand a prop is: the least of its clearances from the
## paving, from the buildings, and from the fountain.
##
## The fountain is in here and not in `PLAZA_MASSES` because that list is
## axis-aligned rectangles and this one is a circle 18m across — a box round it
## would close the four diagonals of the skirt, which is exactly the ground the
## benches want.
static func stand_score(p: Vector2) -> float:
	return minf(walkway_clearance(p),
		minf(mass_clearance(p), p.length() - FOUNTAIN_RADIUS))


## The nearest place to `p` that is not standing in a walkway, by `clear` metres.
##
## The companion to `open_spots`, and the reason it exists is that the two halves
## of the plaza's furniture were placed by different rules and only one of them
## was checked. What is *scattered* has been rejection-sampled against
## `walkway_clearance` since the plaza grew; what is **hand-placed** — the ring
## benches, the bins, the cart, the a-frames, the flagpoles, the picture-spot
## signs — was typed in the old 80m coordinates and run through `plaza_out`, so
## where it ends up is not where it is written. A coordinate that cleared the
## paving at 80m has no reason to clear it at 104m, and 20-odd of them did not:
## five benches and four bins stood in the ring walkway, the cart and an a-frame
## in a threshold spoke, and a picture-spot sign dead on the entrance axis.
##
## So this keeps the authored position as the *intent* and makes clearing the
## paving a rule, rather than re-typing twenty coordinates against a layout that
## will move again. A prop pinned to a walkway edge stays pinned to it when the
## walkway moves — which is the same bargain `plaza_out` already makes, one level
## further on.
##
## Snap-to-edge and keep the best, rather than a gradient: a prop at a dogleg is
## inside two runs at once and being pushed out of one puts it into the other, so
## the move that matters is the whole way to an edge and the question is only
## which edge. If nowhere clears — a passage mouth has walls at both hands — it
## returns the best it found and leaves `clearance_test.gd` to say so, because a
## prop that cannot be placed by rule is one somebody has to look at.
static func clear_of_walkways(p: Vector2, clear: float) -> Vector2:
	var out := p
	var best := stand_score(out)
	for _pass in 8:
		if best >= clear:
			break
		var from := out
		var moved := false
		for run in walkway_segments():
			var a: Vector2 = run["from"]
			var b: Vector2 = run["to"]
			var d := b - a
			var l2 := d.length_squared()
			var t := 0.0 if l2 < 0.0001 else clampf((from - a).dot(d) / l2, 0.0, 1.0)
			var near := a + d * t
			var off := from - near
			var want := float(run["width"]) * 0.5 + clear
			if off.length() >= want:
				continue
			# Standing on the centre line there is no "away" — take the segment's
			# own normal, which is the direction a path is crossed.
			var axis := off.normalized() if off.length() > 0.01 \
				else Vector2(-d.y, d.x).normalized()
			for side: float in [1.0, -1.0]:
				var cand: Vector2 = near + axis * side * want
				var score := stand_score(cand)
				if score > best + 0.001:
					best = score
					out = cand
					moved = true
		if not moved:
			break
	return out


## An assembly's base: dilated out of the old plaza, then stood clear of the
## paving. `clear` is the prop's own half-footprint plus whatever margin it wants
## — a bench is about 1.2, a bollard nothing at all.
##
## **Both generators call this rather than `plaza_out` alone**, because
## `gen_crowd.gd` routes its guests around these props and a push applied in one
## file and not the other is the same drift the cafe terrace already caused once.
static func plaza_stand(p: Vector2, clear: float) -> Vector2:
	return clear_of_walkways(plaza_out2(p), clear)


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
## `avoid` is whatever is already standing, as `{at, r}` — the plaza's hand-placed
## furniture, which this cannot otherwise see. It matters because the two halves
## run in the wrong order: the hand-placed props go down first and are then
## *pushed* clear of the paving by `clear_of_walkways`, so where they finish is
## not where they were written, and the scatter that follows them was sampling
## against the written positions. That is how a tree came to be growing through
## the bandstand's west bench.
static func open_spots(count: int, salt: int, r_min: float, r_max: float,
		clear: float, apart: float, avoid: Array = []) -> Array:
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
		# Against `avoid` the margin is fixed and small, not `clear`. `clear` is
		# how far this wants to be from a *wall* or a walkway, and a bench is
		# neither: a crown overhanging a bench is a park and a trunk growing
		# through one is not, so the only thing that has to be kept apart is the
		# footprints. Reusing `clear` here cost five of the twenty-eight trees.
		var taken := false
		for o in avoid:
			if p.distance_to(o["at"]) < float(o["r"]) + 0.9:
				taken = true
				break
		if taken:
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


# ---------------------------------------------------------------------------
# The park's own lighting
# ---------------------------------------------------------------------------

## What every artificial light in the park joins, and what `park_lights.gd`
## finds them by. `tools/gen_props.gd` puts them in it.
const LIGHT_GROUP := &"park_light"

## What a light is *for*, which is the only thing that decides what becomes of it
## at ten o'clock when the park shuts.
##
## Here rather than in either of the two files that use them, under the rule at
## the top of this file: the generator writes these numbers into scenes and the
## driver reads them back out, so they are a contract between two programs and
## exactly the kind of thing that drifts when each keeps its own copy. They are
## not layout, which is the one argument against — but a constant that is wrong
## in one file of two is the failure this whole file exists to prevent, and
## `gen_props.gd` already preloads this one.
##
##   FIXTURE  the park lighting itself: lamp standards, festoon runs, the globes
##            under the threshold valances, the glow in the bandstand. On at
##            dusk, and mostly — not entirely — out after close.
##   FEATURE  the uplighting. On at dusk, off at close, and off completely.
##            Floodlit architecture is the park performing for its guests, and
##            after close there are none.
##   SERVICE  the few still on at two in the morning. The back lane, a cart with
##            its light left on. `night.md` wants the shut park to read as
##            powered and awake rather than as switched off at the main, and
##            these are what carry that.
const LIGHT_FIXTURE := 0
const LIGHT_FEATURE := 1
const LIGHT_SERVICE := 2

## Where the park's own lights live on disk. Externalised as their own resources
## — unlike every other material in the park, which is packed per-scene — so that
## one file is one instance and the driver can light 196 fixtures across four
## scenes by writing to a single material. See `_lit_material` in `gen_props.gd`.
const BULB_MATERIAL := "res://assets/materials/bulb.res"
const LAMP_MATERIAL := "res://assets/materials/lamp_glass.res"
const EYE_MATERIAL := "res://assets/materials/cascade_eye.res"

## Architectural edge-lighting: coping and cap stones that glow along their own
## length after dark, rather than being surfaces something else is aimed at.
##
## The fourth lit material and the only one that is not a fitting. It exists
## because the cascade's silhouette is a *line* — the top edge of each wing's
## coping, sweeping out and down — and a line cannot be floodlit into existence.
## Washing the wall under it lights an area and leaves the edge exactly as
## legible as the wall, which is what made the monument read flat in the first
## night capture.
const TRIM_MATERIAL := "res://assets/materials/trim.res"
