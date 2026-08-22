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

## The west arch: a straight cutting through the wall, on the plaza's own west
## axis, open to the sky.
##
## **It became a tunnel on 2026-08-14 and lost its top on 2026-08-16.** 6m wide
## over 13.5m of depth, where it was 9 by 8.9 over 11 — a section nearly square
## is a hole in a wall, so the depth went in and stayed. The lintel did not: a
## soffit over a *deep* opening is limited by its far edge, and 5m of clear
## height at the far edge of 13.5m is a 6.7° ceiling from the ring, which put the
## top half of the wheel behind masonry from everywhere in the plaza. The depth
## is a gate house projecting into the plaza rather than a thicker wall, because
## the wall's west face is the terrace's east edge and the terrace has only six
## metres to give.
const ARCH_AT := Vector2(-39.0, -2.0)

## The two ends of the tube, as x. The mouth is the gate house's face, out in the
## plaza; the far end is the wall's west face, on the terrace. Everything that
## has to stop at the arch or start past it reads these rather than measuring
## `plaza.tscn` again.
const ARCH_MOUTH_X := -30.5
const ARCH_FAR_X := -44.0

## The clear opening between the piers. Clear to the sky above it — what
## `ARCH_HEIGHT` names is the soffit of the beam across the piers' plaza faces,
## which is the *near* plane and so crops far less than the same number did at
## the far end of a tube.
##
## Set by the wheel, and the number is `WHEEL_TOP` — 25.80, and read from there
## rather than typed here, so the arch notices if the wheel ever moves again.
##
## **It has to be read and not reasoned about.** A figure of 21.9 sat in this
## comment, in `CLAUDE.md` and in `west_capture.gd` for part of 2026-08-16 and was
## wrong by 3.9m: it came from assuming the wheel sits 1.5m above `SHORE_TOP` and
## adding two radii, rather than opening the file the generator had already
## written. The soffit had never cleared the rim and every margin quoted off that
## assumption was fiction. `WHEEL_TOP` exists because of it — before that the
## wheel's geometry lived only inside `_wheel` and published nothing, which is
## what made the number derivable in the first place.
##
## **The soffit does not clear the whole rim from the back of the west spoke, and
## that is deliberate.** How much of the wheel shows is a lateral question before
## it is a vertical one — it stands 14m north of the axis, so the 6m slot hides
## most of it from far back and uncovers it as you approach:
##
##     player x   wheel visible laterally   soffit needed to clear the rim
##       −11        12.1m  (46%)              7.19
##       −13        13.1m  (50%)              6.79
##       −16        15.0m  (57%)              6.16
##       −20        18.9m  (72%)              5.24
##       −24        26.4m (100%)              4.23
##
## Built at 6.30, so the rim is clipped at −11 and −13 and whole from −16 in.
## Those two standpoints are the ones showing under half the wheel through a slot;
## buying them costs 0.9m on the beam and pushes the sign up into the crane angle
## that 2026-08-14c took it out of. A gateway that reveals more as you walk into
## it is the behaviour worth having, so this is where it binds.
##
## Distances are to the **camera**, not the player: the spring arm is 2.6m and
## sits it about 2.5m back, which is further from the mouth and so tighter than a
## standing eye. Sizing this off `pos` overstates the clearance.
##
## And the camera's *height* moves with the shot's pitch, so the margin is a
## property of the pose rather than of the geometry. Pitching up swings the arm
## down, and a lower eye needs a lower soffit to clear the same rim: at camera
## y 1.75 the rim would crop by 0.03m, at 1.55 it clears by 0.14m, and at the
## y ≈ 1.2 measured in the running game it clears by 0.39m. All of those are the
## same wall and the same wheel. Quote the pose with the margin or neither means
## anything — which is the third time on 2026-08-16 that a single number turned
## out to be a family of them.
const ARCH_WIDTH := 6.0
const ARCH_HEIGHT := 6.3

## The standpoint the clear height is bound at: the furthest back the whole rim is
## required to show, not the furthest back anybody can stand. Behind this the
## wheel is under half uncovered and its top is allowed to clip — see
## `ARCH_HEIGHT`. Named so `west_capture` shoots the pose that holds the promise.
const ARCH_RIM_CLEAR_X := -16.0

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
## **Six metres again since 2026-08-15**, after eighteen hours at three.
##
## Three was arrived at by arithmetic and it was the right arithmetic for the
## wrong thing: a 1:12 ramp needs twelve metres of run per metre of fall, so six
## metres is seventy-two metres of ramp, and folding that into the bluff looked
## impossible while the ramp had to *be* the wings. Halving the drop halved the
## ramp and the wings fitted.
##
## What it cost was the monument. Oakland's cascade spreads its wings about four
## times the height they fall; at three metres of drop and thirty-six metres of
## ramp ours spread eighteen times, which is not a swept shoulder, it is a
## flyover — and that is exactly how it photographed. The ratio is forced: the
## ramp's length is 12× the rise and the spread is about half of that, so no
## amount of folding gets a wing-borne ramp anywhere near 4:1.
##
## So the ramp comes off the wings and the drop goes back. Six
## is what the site affords rather than a number chosen for the composition:
## there are 23.5m from the bluff face to the backs of the shops, a flight at the
## reference's own steepness spends 9.6 of them, and what is left is a court.
const SHORE_TOP := -6.0

## A metre and a half below the shore, and derived rather than typed — it was
## −4.5 against a −3.0 shore, which is the same relationship written down twice.
const WATER_TOP := SHORE_TOP - 1.5

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
## The drop is six metres. It was halved to three on 2026-08-14b to fit the ramp
## and put back on 2026-08-15 when the ramp moved off the wings; see `SHORE_TOP`
## for what the three cost and why the arithmetic that produced it was sound and
## aimed at the wrong quantity.
const BLUFF_FACE_X := -58.0
const BLUFF_BACK_X := -51.0

## The cascade: the whole way down, as one monument on the arch's own axis.
##
## Modelled on the Cleveland Cascade in Oakland, which is a straight flight in
## the middle, a wall with an arched opening at its foot, and two wings sweeping
## out and down either side — a shape that reads, from the bottom, unmistakably
## like a ray with its wings spread.
##
## **The wings are the wall, and since 2026-08-15 they are only the wall.** They
## used to carry the descent as well, one side a ramp and the other a garden
## stair, on the theory that a single hairpin followed by both surfaces kept the
## thing symmetrical. It did. What it could not keep was the proportion: a wing
## carrying a 1:12 ramp is half as long as the ramp, the ramp is 12× the rise,
## so the spread is stuck at about 6× the rise per side against the reference's
## 2×. Straightening that out by folding more just turns a flyover into a fire
## escape. The wings are masonry now, nobody walks on them, and the 1:12 has its
## own route, which is not built yet — see the journal for 2026-08-15.
##
## Two ways down, then, and neither is a service entrance: the flight on the
## axis, and the ramp beside it. They start within a few strides of each other on
## the bluff top and land within a few strides of each other in the court, which
## is what the shape is *for* and what `walk_test` asks about by walking both and
## checking where each came out.
const CASCADE_AXIS_Z := ARCH_AT.y
const CASCADE_TOP_X := BLUFF_FACE_X
const CASCADE_DROP := -SHORE_TOP

## The middle flight: direct, and the whole drop in one go.
##
## **Narrower and steeper than it was.** Ten metres of width in a monument
## spreading twenty-eight is 36% of the whole, and the reference's flight is
## nearer a quarter — a wide flight makes the wall either side of it a pair of
## offcuts rather than the mass the wings spring from. And 0.55 of going is a
## municipal gradient: 24 risers at that spends 13.2m of the 23.5 available
## between the bluff face and the backs of the shops, which leaves no court to
## land in. 0.40 is the reference's own steepness, spends 9.6, and leaves 12.
const FLIGHT_W := 7.0
const FLIGHT_RISE := 0.25
const FLIGHT_GOING := 0.40

## How many risers, and how far out from the bluff face the last one lands.
## Derived, because three separate places were computing it from the drop.
const FLIGHT_RISERS := int(CASCADE_DROP / FLIGHT_RISE + 0.5)
const FLIGHT_RUN := FLIGHT_GOING * FLIGHT_RISERS

## The wall the wings spring from and the flight runs out through: a mass across
## the foot of the descent, with an arched opening on the axis.
##
## **The arch used to stand five metres clear of this, out in the court, on its
## own pair of piers.** It was put there for an alignment — the boardwalk's entry,
## this, and the plaza's tunnel on one line at rising heights, seen from the head
## of the pier — and the alignment was never once visible, because at a 3m drop
## the frontage cropped the whole monument at that distance. What the freestanding
## version *did* do was stand 6.9m tall in front of a 3m cascade and eclipse every
## part of it from anywhere in the court. An arch is a hole in a mass; ours was a
## mass in front of a hole. It is a hole again.
## **A landing at the head level with the ground above, two flights down from its
## sides, each ending at a landing and hairpinning back towards the centre.**
##
## That is the plan three square-on elevations could not give me, and it settles
## everything. The landing's west face is the trapezoid's middle horizontal — the
## tall flat wall with the niche in it. The outbound flights are the diagonals.
## The return legs are the second, shallower handrail visible *outside* each
## diagonal in the daylight photograph, which I looked straight at for half a day
## without understanding.
##
## Every version before this ran the diagonals *away* along the bluff face. A
## diagonal seen end-on is not a diagonal, which is why none of them read.
##
## **The wall is 7m and not 14m since 2026-08-16.** The whole monument was too
## wide — see `WING_SLOPE_RUN` for the measurement — and it was the middle that
## was wrong, not the wings. Nothing constrains this from inside any more: the
## centre is water and the niche is blind, so it stopped being the width of a
## flight the day the flight came out of it, and 7.0 was left over from when it
## was. It went 7.0 → 5.5 → 4.5 → 3.5 in four passes against the same
## photograph, which is the honest way to do this: the ratio is arithmetic and
## how wide it *looks* is not.
##
## **Narrowing the middle narrows the monument twice over, and that is the point
## of pulling this lever rather than the wings'.** The wings spring from
## `CASCADE_AXIS_Z ± LANDING_HALF_W`, so a metre off the wall takes two off the
## spread and the diagonals keep their own length, angle and proportion — they
## just start closer in. Every other lever trades the wings against the wall.
##
## The floor is the niche, not the flight. At 3.5 there is 2.3m of wall either
## side of a 2.4m niche, and the wall is 29% of the spread against the
## photograph's ~25%. Much under this and the middle horizontal stops being the
## mass the wings spring from and becomes a lintel over a hole.
const LANDING_D := 5.0
const LANDING_HALF_W := 3.5
const CASCADE_WALL_X := CASCADE_TOP_X - LANDING_D
const CASCADE_WALL_THICK := 1.6

## The niche in the middle of that face. Blind — it is where the water comes out
## and nothing walks through it. Making it a doorway was downstream of putting a
## staircase down the middle, and both were the same mistake: the centre is the
## cascade and nobody walks it.
##
## **A metre and a half deep since 2026-08-16, and it was two feet.** At 0.6 the
## recess was a rebate rather than a room: anything set in it stood proud of the
## wall, so the wall fountain the whole niche exists for would have been a lump
## bolted to the facade instead of something the mass was hollowed out for. The
## depth is what buys the shadow, and the shadow is what the arch is drawn round.
##
## It is free, which is why it can be spent. The recess cuts back into
## `landing_fill` — five metres of buried mass between the wall and the bluff
## face — so nothing structural is being thinned. `CASCADE_WALL_THICK` stays where
## it is on purpose: `face` is derived from it, and the wings spring off `face`.
##
## **Wider and taller since 2026-08-18, and the string course coming off is why.**
## At 2.4 × 3.2 in a 7m × 6m face the opening was the reference's own proportion
## and it was sized for a facade that had a pale line running across it. Taking
## that line off left the largest unbroken surface on the monument with exactly
## one feature on it, and the same opening that read as *an* incident on a
## detailed wall reads as a small hole in a blank one. Enlarging is the cheap
## half of restoring the detail, because everything inside the recess is a
## fixed-size object standing on its floor — the trough, the basin, the spout are
## sized to a person and stay where they are — so a bigger opening shows more of
## the fountain and more of the terracotta rather than scaling a picture up.
##
## 3.3 is 47% of the block's width against 34%, and 3.8 puts the crown level with
## the crest globes at `head − 1.95` rather than a metre below them. Level is the
## intent: on the shape this facade reads as, the eyes sit at the corners of the
## head and the mouth is a wide slot between them, so width carries the increase
## and height only follows far enough to keep the arch from squatting. The
## proportion goes 1:1.33 to 1:1.15.
const NICHE_W := 3.3
const NICHE_H := 3.8
const NICHE_DEEP := 1.5

## A wing. The outbound leg runs behind the facade plane and the return leg in
## front of it, which is what puts two rails at two angles on each side — exactly
## what the daylight photograph shows.
##
## **These are stairs, not 1:12.** At 1:12 the same flight would be 36m long and
## its diagonal would fall 4.4°, which is not a diagonal, it is a flat slab. That
## arithmetic has driven every rebuild. The wheelchair route hairpins behind the
## bank instead, out of the court's sight.
##
## **And they are shorter than they were, because the monument was half again as
## wide as it read in the photographs.** The old comment here claimed 26m across
## and 4.3:1 by counting the sloping run and forgetting that a leg also carries a
## turn landing on its far end: the real half-spread is
## `LANDING_HALF_W + WING_SLOPE_RUN + WING_LAND_D`, which was 7 + 6 + 3.2, so the
## trapezoid was 32.4m across the toes and 35m across the turn slabs against a 6m
## fall — **5.8:1**, where the reference photograph is nearer 3:1 and this file
## has been claiming about 4. Measured off the emitted scene rather than off the
## constants, which is the only reason it was ever caught; every number in the
## paragraph it replaced was arithmetic nobody had checked against geometry.
##
## Now 3.5 + 4.8 + 2.0 = 10.3, so 20.6m across the toes and 22m across the turns
## — **3.7:1**, against the photograph's ~3:1 and a claim of 4:1 this file made
## for a day while measuring 5.8. The metre that came off each leg is the
## difference between 1:2 and the *central flight's own* going: 12 risers at
## `FLIGHT_GOING` is 4.8m, which is where the number comes from and what keeps
## the diagonals and the middle at one angle instead of two that nearly match.
##
## **The wings are done and the two numbers below should stay where they are.**
## `WING_SLOPE_RUN` is the gradient, and taking it under 4.8 pushes the diagonals
## past the flight they were just made to agree with; `WING_LAND_D` at 2.0 is a
## hairpin landing for a 3.0m deck, which is as short as a turn gets. Anything
## further comes off `LANDING_HALF_W`, which is the lever that leaves the wings
## alone — see there for why it is worth two of any other.
const WING_W := 3.0
const WING_SEP := 1.0
const WING_LAND_D := 2.0
## Reach is the sloping run *plus* the landing, not the sloping run. The legs
## stop a full landing short of the turn — that is what keeps a level slab off
## the end of a slope — so a reach equal to the slope alone leaves the landing
## nowhere to be, which is what left a slot at the turn. `wing_leg_end` is the
## one description of where a leg stops and both the legs and the landing are
## laid off it.
const WING_SLOPE_RUN := 4.8
const WING_REACH := WING_SLOPE_RUN + WING_LAND_D
const WING_TURN_Z := LANDING_HALF_W + WING_REACH
const WING_RISE := 0.25

## The three broad steps at the foot, on the axis. Levelling the court up to the
## wall and nothing more — they became a plinth under the whole monument once,
## and a 17m riser across where both wings land is a wall, not a step.
const FOOT_STEPS := 3

## The foot of the cascade on the axis, in front of the three steps. Nobody lands
## here any more — the wings land either side of it and the middle is water — but
## plenty of things still ask where the bottom of the descent is.
const STAIR_FOOT := Vector3(CASCADE_WALL_X - WING_SEP - WING_W - 2.5,
	SHORE_TOP, CASCADE_AXIS_Z)
const STAIR_FOOT_STAND := Vector3(STAIR_FOOT.x, SHORE_TOP + 0.2, CASCADE_AXIS_Z)

## The west cascade as a **site**: the handful of numbers that say where a
## cascade is, as opposed to what shape one is.
##
## Everything above this line is shape — `WING_W`, `WING_SEP`, `WING_LAND_D`,
## `WING_SLOPE_RUN`, `LANDING_HALF_W`, `NICHE_*`, `FOOT_STEPS`, `FLIGHT_*` — and
## it is shared by both cascades. These five are position, and there is a second
## set of them in the east section.
##
## `wall_x` and `head_y` are derived and carried anyway, because a site is passed
## around as a whole and a consumer that has to remember to subtract `LANDING_D`
## itself is a consumer that will one day forget.
##
## `tag` is the sixth, and it is not position — it is how a consumer names a
## thing *per site*. The niche fountain needs it: two of its four water materials
## carry a world XZ centre and two carry an absolute world Y fade band, so they
## cannot be shared between sites and each site's set has to be findable by name.
## See the note above `water_niche_*` in `gen_props.gd`.
const CASCADE_WEST := {
	"tag": "west",
	"axis_z": CASCADE_AXIS_Z,
	"top_x": CASCADE_TOP_X,
	"wall_x": CASCADE_WALL_X,
	"floor_y": SHORE_TOP,
	"head_y": SHORE_TOP + CASCADE_DROP,
}

## How far north and south of the arch's axis the bluff top can be walked. The
## terrace's own end walls stand on these lines, and without something on them
## the parapet gap opens onto a seven-metre ledge running the length of the map.
## Widened 2026-08-15 so the bluff top reaches past both wing heads. It used to
## stop at −28/+9.5, which was drawn around a descent that has since become
## ninety-four metres wide.
const BLUFF_TOP_FROM_Z := -34.0
const BLUFF_TOP_TO_Z := 16.0


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


# ---------------------------------------------------------------------------
# The east: the rim, the terraces, and the cascade that climbs to them
# ---------------------------------------------------------------------------

## The park sits in a breached crater. The lagoon fills the west of the bowl and
## the rim rises from the north round to the south-east; it is **open to the
## west**, which is not decoration — the sun sets on that bearing and
## `daylight.gd` computes it from real solar geometry rather than posing it.
## Closing the ring would put land where the boardwalk's best hour is.
##
## So the plaza has water falling away on one side and ground climbing on the
## other, and the two are on one line through the fountain: `ARCH_AT.y`, shared
## by the west arch, the west cascade, the east gap and the east cascade. Stand
## at the fountain, turn west and the ground drops six metres; turn east and it
## climbs six.
##
## **Both arms are built since 2026-08-21.** The east arm runs at `RIM_CREST_X`
## and then turns west behind the grove and comes down to a headland in the water
## north of the pier, so the crater is closed everywhere except the bearing the
## sun sets on. See `RIM_PATH`, which is where the grove, the coaster and the
## sunset are each measured against rather than deferred.

## The first shelf: the head of the east cascade, and the top of the climb the
## player can actually make. Six metres, and the six is not free — it is
## `CASCADE_DROP` reflected, and the monument's proportions were fought for over
## two days of rebuilding against a six metre rise. A different rise here would
## want the whole wing argument re-derived, starting with `WING_SLOPE_RUN`.
const HILL_TOP := 6.0

## Where the scarp stands: plaza ground below and west of it, shelf above and
## east. The east's answer to `BLUFF_FACE_X`, and the same kind of number — the
## line the made ground changes level at.
##
## 70 rather than tighter against the wall, because the monument is about ten
## metres deep and the forecourt in front of it is what makes it a monument
## rather than a retaining wall you walk into. The wall's outer face is at 47 and
## the westmost masonry lands near 61, which leaves a fourteen metre court: a six
## metre face seen from fourteen metres is a 24° elevation, which is about what
## the reference photographs are taken at.
##
## **The belvedere is 8m deep since 2026-08-22, and it was 16.** Measured from
## the fountain's own sightline: the ray that grazes the monument's 6.2m crest
## does not come back to earth until it is most of the way up a staircase that
## starts 16m further back at the crest's own height — so the whole climb, the
## thing the gate axis exists to frame, was hidden behind a flat pause exactly
## as tall as itself and only the top two metres ever showed from anywhere in
## the plaza. The reference is unambiguous here: Cleveland's flights spring
## straight off the head-house. Half the pause puts the first riser 8m behind
## the crest and most of the climb's rise above the crop ray.
const HILL_FACE_X := 70.0
const SHELF_TO_X := 78.0

## How far north and south the shelf is walkable. The wings reach z −14.3..10.3,
## so this is five metres of margin either side and no more — the shelf is a
## belvedere at the head of a climb, not a plateau. Ground past it drops six
## metres to the terrace below, which is why it wants a parapet.
const SHELF_FROM_Z := -20.0
const SHELF_TO_Z := 16.0

## How far the made ground east of the gate runs, and the one place it is
## written down.
##
## **The court and the hill have to end together.** `_east_court` laid its slab
## as literals, and the hill standing on that slab was written afterwards — two
## copies of one extent, which is the cafe-table bug with a bigger footprint: a
## hill half a metre longer than the ground under it is a retaining wall with
## daylight beneath it, and a hill half a metre shorter is a strip of court with
## nothing behind it. Both read as a hole and neither is visible from anywhere a
## screenshot gets taken.
##
## 26m either side of the axis is what the court was already built to. It is
## generous for the court alone and it is the binding number for the hill, which
## is why it moved here rather than staying a literal in the slab that happened
## to be laid first.
const EAST_GROUND_HALF_Z := 26.0
## **Under the gate, not up to it, and 44 → 33 on 2026-08-18 because of the
## seam.** The court used to start a metre outside the wall's outer face, which
## was right while the plaza owned this ground and wrong the moment the east
## became its own section: crossing back west, the player left the forecourt,
## walked into the passage and fell, because the floor under the arch belonged to
## a section that had just been freed.
##
## `west_shell` has always solved the same problem the same way — it is the
## ground *and* the horizon, mounted on both sides of the west seam, which is
## what makes the cut at that gate continuous. This is that, at the other gate:
## `east_cascade.tscn` is in both section lists, so a court that reaches past the
## wall's inner face at 36 gives either section a floor under the passage.
##
## 33 rather than 36 so it laps the plaza's own paving rather than butting it —
## `GROUND_SEAM` keeps the two off one plane.
const EAST_GROUND_FROM_X := 33.0
const EAST_GROUND_TO_X := HILL_FACE_X + 0.5

## The guard on the shelf's open side, and the only one it needs: the notch is
## walled by the hill on its other three sides, so this is a parapet across one
## edge rather than a fence around a plateau.
##
## Height is the drop's, not the fashion's. Six metres onto brick wants a solid
## parapet rather than the crest's three-bar rail — the rail is what you get when
## the thing behind it is the monument you are standing on, and this is what you
## get when the thing in front of it is a courtyard.
const SHELF_PARAPET_H := 1.1
const SHELF_PARAPET_T := 0.5

## The second terrace, and the one the two east sections stand on. Nothing is
## built on it — these are footprints for silhouette, as `SECTION_GROUND` says —
## but the level is a decision and it belongs here rather than being implied by
## whatever gets drawn first. `TERRACE_TWO_FROM_X` follows `SHELF_TO_X`, the
## notch's own back scarp — nothing reads it today, which is exactly the
## condition this file's own comment on `SECTION_GROUND` warns about, so it is
## kept true rather than trusted.
##
## **This is what moved `frontier` and `kiddieland` off y = 0.** They used to sit
## on the flat at the plaza's own level, which was fine while the east was flat.
## An east that climbs has to put them somewhere, and the two honest options were
## to route the rim's foot around them — a ridge with two bays chewed out of it —
## or to put them on the hill. They are on the hill. **The cost is that the `ne`
## and `se` passages now have twelve metres to climb and nothing in them climbs
## yet**, which is real and is written down here rather than discovered later.
const TERRACE_TWO_Y := 12.0
const TERRACE_TWO_FROM_X := SHELF_TO_X
const TERRACE_TWO_TO_X := 120.0

## The basin staircase: the rest of the Cleveland Cascade, cut into the hill
## behind the belvedere.
##
## **The monument at the gate is the head-house, and this is what it is the foot
## of.** In the reference the arched head-house stands at the street with a long
## twin-flight stair climbing the hillside above it, and a chain of basins down
## the middle spilling one into the next. This park had the head-house — the
## facade, the blind niche, the wall fountain in it — and stopped there, so the
## thing was a monument to a climb that did not exist. `_cascade_niche` was
## always the bottom of this.
##
## **Cut into the hill, not standing on it** — but cut as a ravine rather than as
## a slot, which is where the belvedere's own argument stops applying. The notch
## below is a bay with three built walls because it is a room; this is a
## hillside, and a hillside falls into a cut at the angle earth stands at. Every
## reference photograph is mostly *planting*: green banks either side of the
## flights, trees closing over the top of them, masonry emerging from vegetation
## rather than a box cut in stone. Vertical grey walls up both sides would have
## been the notch's logic carried one step past where it was true.
##
## So the sides are battered and planted, at `CLIMB_BANK_BATTER` — **above a
## retaining wall, and that pairing is the whole section rather than a detail.**
## A pure batter cannot work here and the arithmetic says so plainly: 1.4 over
## six metres of depth opens the mouth to 16.4 either side of the axis against a
## belvedere that is 18, which does not cut a doorway in that room's east wall,
## it removes the wall. The pilasters and string course that went onto it are on
## the only face the belvedere has to turn round and look at.
##
## The reference answers this and the photographs are unambiguous once looked at
## for it: the bottom of the real cascade is *masonry*, and planting takes over
## further up where the cut is shallow enough to lay back in the width available.
## A slope that cannot fit stands up as a wall. So the bank lays back from the
## floor edge at its own angle for as much height as `CLIMB_OPEN_HALF` allows —
## 3.57m — and whatever depth is left under it is a retaining wall standing at
## the floor edge. At the mouth that is 2.4m of wall with 3.6m of planting over
## it; by the head there is no wall and no bank, because there is no cut.
##
## The opening is then 26m in a 36m wall, which is a portal with five metres of
## masonry either side of it rather than a missing side.
##
## It also means terrace two barely pays for it. A staircase standing clear of
## the scarp would have eaten the whole depth from 86 to 110 across the notch's
## full width; this takes a slot at the floor and a taper above it.
const CLIMB_FROM_X := SHELF_TO_X
## 94.8 is derived, not chosen: `CLIMB_FROM_X` 78 plus 4 x 6 x `FLIGHT_GOING`
## (9.6) plus 3 x `CLIMB_TERRACE_D` (7.2). It cannot be written as that
## expression because `CLIMB_TERRACE_D` is declared below it; if any of the
## four inputs moves, re-derive this by hand — the exactness note at
## `CLIMB_FLIGHTS` is about precisely this number.
const CLIMB_TO_X := 94.8
## The floor's half-width, and **derived rather than chosen**: the bank has to
## spring from the outer edge of the flight, or the 1.3m strip between them is a
## verge with no floor under it that the walk test finds by falling down it.
const CLIMB_HALF_Z := CLIMB_BED_TO + CLIMB_FLIGHT_W

## How far the bank lies back per metre it climbs. 1.4 is a planted slope rather
## than a revetment — steeper reads as a wall somebody has thrown soil at, and it
## is what sets the mouth's width: 8.0 of floor plus six metres of depth at 1.4
## is 16.4 either side of the axis, against the belvedere's 18. Widening the
## floor or steepening the batter past this puts the ravine's mouth wider than
## the room it opens off, and then the notch's own side walls have a hole in
## them that nothing closes.
const CLIMB_BANK_BATTER := 1.4

## How far the ravine may open at its widest, as a half-width off the axis. This
## is the number that keeps the belvedere's east wall in existence, and it is set
## against `SHELF_FROM_Z`/`SHELF_TO_Z` at 18 rather than against anything the
## climb wants for itself: 13 leaves five metres of wall each side of the mouth,
## which is enough to read as a jamb and enough to carry the pilasters.
##
## It is a *cap on the batter*, not on the cut. Depth the bank cannot lay back
## inside this becomes wall height instead — see `CLIMB_BANK_MAX_D`, which is the
## same fact stated as the quantity the generator actually needs.
const CLIMB_OPEN_HALF := 13.0
const CLIMB_BANK_MAX_D := (CLIMB_OPEN_HALF - CLIMB_HALF_Z) / CLIMB_BANK_BATTER

## Four flights of six risers, three planted terraces between them. Both of these
## are the park's own stair constants rather than new ones, and the two sums
## below are exact rather than nearly: 4 x 6 x `FLIGHT_GOING` plus 3 x
## `CLIMB_TERRACE_D` is 16.8, which is `CLIMB_TO_X - CLIMB_FROM_X`; and
## 4 x 6 x `FLIGHT_RISE` is 6.0, which is `TERRACE_TWO_Y - HILL_TOP`.
##
## They are exact because the terrace depth was solved for after the flights were
## fixed, not chosen. If any of the four moves, re-derive the other three — a
## staircase that arrives half a riser under its own terrace is the kind of thing
## no screenshot shows and every ankle finds.
##
## **The terraces went 4.8 → 2.4 on 2026-08-22, and it is a sightline decision
## rather than a stair one.** At 4.8 the climb ran 24m for its 6m of rise — 1:4,
## which from the fountain 90m away is a surface seen nearly edge-on, and with
## the crest of the monument in front of it the whole feature read as a green
## wall with railings on it. At 2.4 the run is 16.8m and the grade 1:2.8, so the
## flights stack frontally and the rise spends less of itself below the crop
## ray. The rise did not change and must not: six is `CASCADE_DROP` reflected,
## and the monument was fought for against that number.
const CLIMB_FLIGHTS := 4
const CLIMB_FLIGHT_RISERS := 6
const CLIMB_TERRACE_D := 2.4
const CLIMB_RUN := CLIMB_TO_X - CLIMB_FROM_X
const CLIMB_RISE := TERRACE_TWO_Y - HILL_TOP

## The cross-section, as half-widths off the axis: the channel down the middle,
## planting either side of it, then a flight, then the bank against the cut face.
##
## The flights are 2.1 rather than `WING_W`'s 3.0. A wing on the monument below
## carries the whole descent and is the only way down; there are two of these and
## they flank a garden, which is a public stair rather than a route.
const CLIMB_CHANNEL_HALF := 1.1
const CLIMB_BED_TO := 4.6
const CLIMB_FLIGHT_W := 2.1

## The chain, and the one thing here that is not a stair.
##
## **The channel runs at its own constant gradient and the flights step either
## side of it.** That is the historic photograph rather than the modern one: an
## unbroken run of bowls from head to foot, where what is there today is a flat
## runnel across each terrace with a stepped reach between. Following the
## flights' broken profile would have put three basins in a huddle at each flight
## and a dry trough across each terrace, and the beds either side are exactly
## what takes up the difference between a straight chute and a stepped stair.
##
## Eight basins over six metres is three quarters of a metre of fall each, one
## every 2.1m of run — 1:2.8, the whole feature's mean gradient and therefore
## the only slope on the hill that does not need a second number. Eight rather
## than the twelve the chain carried at the old 24m run, for two reasons that
## arrive together: at 16.8m twelve bowls of `BASIN_R` 0.75 would overlap their
## own neighbours, and a 0.75m fall face is half again as much white water per
## lip — which matters, because the falls are the one part of this feature that
## faces the plaza instead of receding from it.
const BASIN_COUNT := 8
const BASIN_FALL := CLIMB_RISE / BASIN_COUNT
const BASIN_STEP := CLIMB_RUN / BASIN_COUNT
const BASIN_R := 0.75

## The collecting pool at the foot, on the belvedere, and the reason the shelf
## was never going to stay a bare deck. The chain discharges into it at the cut's
## mouth and it reads west across the parapet to the plaza beyond.
## Shortened 79 → 81.5 on 2026-08-18: at seven metres it reached most of the way
## across the belvedere toward the parapet, so the shelf read as a pool with a
## walkway round it rather than as a room with a pool at one end of it — and
## derived off the mouth since 2026-08-22, because the belvedere is 8m deep now
## and a literal 81.5 would have put the pool inside the hill. 3.5m of pool
## against an 8m room keeps the same proportion the 2026-08-18 note argued for:
## the *basin* the chain is aimed at, on a floor you see it from.
const POOL_FROM_X := SHELF_TO_X - 3.5
const POOL_HALF_Z := 4.2
const POOL_TOP_Y := HILL_TOP - 0.35

## The landing at the top of the whole feature, between the head of the cutting
## and the rim's toe. Terrace two's own level, so the cutting's banks die into it
## rather than it being a notch of its own.
const CLIMB_HEAD_TO_X := RIM_FOOT_X

## How far each terrace's bay reaches into the hillside, as a depth off the
## floor's edge, lowest first.
##
## **Graduated, because the hill is 12m and the terraces are 1.5m apart.** A bay
## at 7.5 has four and a half metres of hill behind it and can carry a shopfront;
## one at 10.5 has a metre and a half and is a widening with a view. Making all
## three the same would either shrink the lowest to the highest's means or lift a
## ridge over terrace two that the rim's sightlines have never been checked
## against. A real terraced street gets shallower as it nears the crest.
##
## Capped by what is actually there to cut: the floor edge is at `CLIMB_HALF_Z`
## and `SHELF_FROM_Z`/`SHELF_TO_Z` are 18 off the axis, so 11.3m is the whole
## budget before a bay would break into `hill_north`/`hill_south`, which are laid
## at full height across the entire east.
##
## Shallower since the terraces went to 2.4: a bay's mouth is its terrace's own
## span, and a room ten metres deep behind a 2.4m opening is a corridor, not a
## bay. These keep the mouth-to-depth proportion the old 4.8m terraces had.
const CLIMB_BAY_D := [6.0, 4.5, 3.2]

## The reaches of the climb, west to east, as `[x0, x1, y0, y1, is_flight]`.
##
## **The one description of where the stair goes**, for the reason `wing_path`
## is: `gen_props` builds off this and `walk_test` walks it, and the west's wings
## spent a shape change being tested against a copy of their own arithmetic that
## had stopped being true. A straight line between the same two endpoints then
## runs through the planting and reports broken geometry rather than a stale test.
static func climb_reaches() -> Array:
	var out: Array = []
	var x := CLIMB_FROM_X
	var y := HILL_TOP
	var run := CLIMB_FLIGHT_RISERS * FLIGHT_GOING
	var rise := CLIMB_FLIGHT_RISERS * FLIGHT_RISE
	for i in CLIMB_FLIGHTS:
		out.append([x, x + run, y, y + rise, true])
		x += run
		y += rise
		if i < CLIMB_FLIGHTS - 1:
			out.append([x, x + CLIMB_TERRACE_D, y, y, false])
			x += CLIMB_TERRACE_D
	return out


## The walking surface at a station on the climb: flat across a terrace, on the
## nosing line up a flight.
static func climb_floor_y(x: float) -> float:
	for r in climb_reaches():
		if x <= float(r[1]) + 0.001:
			var t := clampf((x - float(r[0])) / maxf(float(r[1]) - float(r[0]), 0.001),
				0.0, 1.0)
			return lerpf(float(r[2]), float(r[3]), t)
	return TERRACE_TWO_Y


## The centre line of a flight strip, as a z offset off the axis.
static func climb_flight_z() -> float:
	return CLIMB_BED_TO + CLIMB_FLIGHT_W * 0.5

## The rim: massing, never reachable, and the only thing out here whose job is to
## be seen from inside the plaza rather than walked on.
##
## **Drawn since 2026-08-18**, by `_rim` in `gen_props.gd`, into
## `plaza_skyline.tscn` — and until that day `rim_crest` had no callers at all,
## so every figure below was a statement about this file rather than about the
## park.
##
## **The crest height is set by the perimeter wall, not by taste.** An eye at 1.7
## in the middle of the plaza clears the east wall's 11.5m top at x 36 on a 0.272
## ray, so anything 150m out has to stand above 42.5 to show at all. A crest at 50
## shows seven metres of itself from the fountain and twenty-four from the plaza's
## west side, which is the right way round — a distant ridge should open up as you
## back away from it.
##
## **Both of those are datums and neither is a standpoint**, which the first run
## of `_rim_probe.gd` established and nothing before it had asked. The slope of
## the clearing ray is set by the eye's distance from the *wall*, not from the
## ridge, so how much shows is a property of where you stand and the two figures
## above are the values at x = 0 and x = -36. Nobody can stand at x = 0: the
## fountain is eighteen metres across and sitting on it. What a player can reach
## on this line, worked from the same ray and then shot:
##
##   x = +11  the fountain's east coping     none of it — the wall has it all
##   x = -11  the west coping                about 15m
##   x = -16  the ring's west vertex         about 17m
##   x = -36  **inside the west gate house**, because the arch is on this axis
##
## So the nearest anyone can stand to the middle sees no ridge at all, and the
## deepest view east in the park is taken from the mouth of the way west. Quote
## these with their x or do not quote them.
##
## Through the gap it is cropped, and that is deliberate. From `EAST_NEAR_STAND_X`
## the beam's soffit puts the ceiling at 29m by the time the ray reaches the
## crest, so the opening frames rising ground and cuts the top off it. **That is
## not the wheel's mistake repeated.** The wheel was visible *only* through the
## west arch, so cropping it lost the thing entirely; the rim stands over the
## whole east roofline from anywhere in the plaza. The gap shows its foot and the
## cascade, the skyline shows its head.
const RIM_FOOT_X := 120.0
const RIM_CREST_X := 150.0

## The rim's crest line, in plan, ordered **headland to north arm to south end**
## — the far end of the breach, round the back of the park, and down the east
## side.
##
## **It was `RIM_PROFILE`, a list of (z, crest) pairs, until 2026-08-21, and a
## list keyed on z can only describe a wall that runs north and south.** That was
## the east arm, which is all there was: one straight ridge at `RIM_CREST_X`, and
## `_rim` swept it along z with every other coordinate held fixed. `_rim`'s own
## docstring called the park "a breached crater" and then built one wall of it,
## which does not read as a crater — it reads as a ridge, and it was the only
## landform on the map.
##
## So this is a *path*: control points the sweep follows, with the cross-section
## taken perpendicular to the local tangent. The east stretch is the old profile
## verbatim, x pinned to `RIM_CREST_X` and the same seven crests, so nothing the
## plan says about what shows over the east roofline has moved. Past z −100 it
## turns west and comes down to a headland in the water north of the pier.
##
## **The order is load-bearing and not cosmetic, and it is written this way round
## because of the winding.** `_rim_strip` winds its triangles assuming the
## columns advance in one particular direction, which the old sweep satisfied by
## running z from −170 up to +170. Authored the other way — south end first, as
## this list was on the first attempt — every triangle comes out backwards and
## the whole ridge is inside out, which does not read as a winding bug at all: it
## reads as the rim having failed to generate. `_rim_mesh` asserts it at the toe
## on the park's axis rather than trusting it, and that assertion is what caught
## it. Inward is the tangent turned to `Vector2(-t.y, t.x)`, which follows from
## the same choice.
##
## `crest` is the top; `foot` is the level the slope arrives at `RIM_RUN` inward,
## and it is what sets the gradient. It stays `TERRACE_TWO_Y` down the east arm,
## because that is the ground the ridge has always risen out of there and every
## documented sightline was measured against it. It comes down through the turn
## to the plaza's own level, and to the water at the headland — a rim that kept a
## twelve metre foot out over the sea would arrive at a nine degree gradient and
## read as a sandbank.
##
## **Where the north arm goes was the decided-nothing that kept it unbuilt.** The
## note this replaces said a wrapping rim "has to decide what it does about the
## grove and about the coaster standing in `plaza_skyline`, and neither of those
## is decided". Measured rather than decided, in the end: the skyline coaster is
## at z −58 and the observation tower at z −40, `SECTION_GROUND[&"grove"]` reaches
## z −146, and the arm's crest runs at −190 to −224 with its foot no further in
## than about −160. Everything built or planned is south of it by twelve metres
## at the tightest, which is the back-of-house strip a section wants anyway.
##
## **And it clears the sunset, which is the one thing it could not be allowed to
## touch.** `daylight.gd` puts the sun at `LATITUDE_DEG` 32.75 and
## `DECLINATION_DEG` 20, so `cos H = -tan d tan phi` = −0.234 and the sunset
## azimuth is 294 degrees — direction (−0.914, −0.407). From the pavilion that
## sightline does not reach z −180 until it is 457m out and past x −568. The
## breach stays open; the crater is closed everywhere the sun is not.
const RIM_PATH := [
	# **Every `foot` down here is well under the water, and that is what keeps the
	# toe short.** The inward offset a column carries is
	# `RIM_RUN + RIM_TOE_BURY / tan(alpha)`, so a shallow gradient makes a long
	# toe — and a long toe on a curve is what folds. Authored against the water
	# line the tail ran at 20-24m of rise over a 30m run, an offset of 53m; at a
	# 30m rise it is 44m, and the headland's own radius of curvature is 58.
	#
	# **The tail, and it is what stops the headland being a cliff of nothing.**
	# The path's far end is a raw cut — the same condition the east arm's ends
	# have always had — and that was free while no standpoint could see either of
	# them. This one is 180m from the pier and dead ahead of the promenade, so
	# the first build put a vertical wall of land across the bay with sky behind
	# it. A headland ends by going under the water, so the crest dives past
	# `WATER_TOP` and the slab hides the rest; the last point's own end is four
	# metres under an opaque surface.
	{"at": Vector2(-170.0, -167.0), "crest": -12.0, "foot": -42.0},
	{"at": Vector2(-155.0, -173.0), "crest": 4.0, "foot": -26.0},
	# The headland. It stands in the water — `_west_shell`'s slab reaches z −200
	# and x −318, so this is inside it — and north of the shore's own end at −170,
	# which is what makes it a promontory rather than more beach. From the
	# pavilion it is 183m off and very nearly due north, which is the bearing the
	# promenade walks.
	{"at": Vector2(-142.0, -177.0), "crest": 16.0, "foot": -14.0},
	{"at": Vector2(-112.0, -193.0), "crest": 19.0, "foot": -11.0},
	# The north arm, running east behind everything.
	{"at": Vector2(-65.0, -210.0), "crest": 21.0, "foot": -9.0},
	{"at": Vector2(-5.0, -221.0), "crest": 23.0, "foot": -7.0},
	# **The turn is an arc of `RIM_TURN_R`, and it is placed rather than drawn.**
	# It was three points eyeballed through the corner, and the offset folded: at
	# 38-43m of radius against a 44m inward offset the toe line crosses itself,
	# which came out as a pleat down the face and a V notch in the silhouette.
	# An arc tangent to both arms has one radius by construction and the radius
	# is a number you can compare with the offset.
	#
	# Centre is `(RIM_CREST_X - R, -222 + R)` — the point equidistant from the
	# east arm's line and the north arm's — so the tangent points are
	# `(RIM_CREST_X - R, -222)` and `(RIM_CREST_X, -222 + R)`, and the three
	# between them are the arc at 22.5 degree steps. At R = 70 that is centre
	# (80, -152), which is why these numbers look arbitrary and are not.
	{"at": Vector2(80.0, -222.0), "crest": 25.0, "foot": -5.0},
	{"at": Vector2(106.8, -216.7), "crest": 28.0, "foot": -2.0},
	{"at": Vector2(129.5, -201.5), "crest": 31.0, "foot": 1.0},
	{"at": Vector2(144.7, -178.8), "crest": 35.0, "foot": 5.0},
	{"at": Vector2(150.0, -152.0), "crest": 38.0, "foot": 8.0},
	# The east arm, which is the old `RIM_PROFILE` verbatim: x pinned to
	# `RIM_CREST_X` and the same crests on the same z, so nothing the plan states
	# about what shows over the east roofline has moved.
	{"at": Vector2(RIM_CREST_X, -100.0), "crest": 42.0, "foot": TERRACE_TWO_Y},
	{"at": Vector2(RIM_CREST_X, -40.0), "crest": 48.0, "foot": TERRACE_TWO_Y},
	{"at": Vector2(RIM_CREST_X, ARCH_AT.y), "crest": 50.0, "foot": TERRACE_TWO_Y},
	{"at": Vector2(RIM_CREST_X, 40.0), "crest": 46.0, "foot": TERRACE_TWO_Y},
	{"at": Vector2(RIM_CREST_X, 100.0), "crest": 40.0, "foot": TERRACE_TWO_Y},
	{"at": Vector2(RIM_CREST_X, 170.0), "crest": 32.0, "foot": TERRACE_TWO_Y},
]

## How far in from the crest the slope's foot stands, and where the jag is zero.
##
## The run is the east arm's own — `RIM_CREST_X` less `RIM_FOOT_X` — carried
## round the turn unchanged, so the ridge keeps one section everywhere and only
## its height and its footing vary.
const RIM_RUN := RIM_CREST_X - RIM_FOOT_X
const RIM_AXIS_AT := Vector2(RIM_CREST_X, ARCH_AT.y)

## The radius of the turn between the two arms, and the reason it is a number
## rather than a shape somebody drew.
##
## **A swept profile folds wherever the sweep curves tighter than the profile
## reaches inward.** The ridge reaches `RIM_RUN` in to its foot and further again
## to its buried toe — 44m in total at a 45 degree gradient — so any part of the
## crest line whose radius of curvature is under that has a toe crossing its own
## neighbours. Measured at 70: the tightest column on the whole path is the
## headland at 58m of radius against 44m of offset, 13.7m in hand.
const RIM_TURN_R := 70.0

## Catmull-Rom exponent and how finely each span is walked before resampling.
##
## **0.5 is centripetal, and uniform is what folded the tail.** The control
## points here are spaced from 16m to 85m apart, and uniform Catmull-Rom on
## unevenly spaced points overshoots: it put a 27m wiggle into a stretch of the
## headland whose control polygon is very nearly straight, and the toe folded
## there for no reason visible in the data. Centripetal is the standard answer to
## exactly that and it costs one `pow` per span.
const RIM_ALPHA := 0.5
const RIM_SUBDIV := 32


# ---------------------------------------------------------------------------
# The east gap, and the gate in it
# ---------------------------------------------------------------------------

## The sixth way out becomes a seventh, and the plan has said six for a year.
##
## It is on the fountain's own east–west line, which is the whole reason for
## cutting a new one rather than using the `ne` or `se` threshold already there.
## Those sit at 62° and 121°; a cascade behind either is a cascade you come
## across, and a cascade due east of the fountain is the west one's answer. The
## plaza reads as a notch between two of them.
##
## **Mirrored in structure and not in coordinate.** The plaza is not symmetric —
## the west wall stands at x −38.5 with faces at −33 and −44, the east at 41.5
## with faces at 36 and 47 — so copying the west's numbers with the sign flipped
## would have put the piers three metres adrift of their own wall. What is
## mirrored is the arrangement: piers the full depth of the wall plus 2.5m proud
## of its inner face, a 6m opening between them, and a beam at the near plane.
const EAST_GAP_AT := Vector2(40.25, ARCH_AT.y)
const EAST_GAP_MOUTH_X := 33.5
const EAST_GAP_FAR_X := 47.0
const EAST_GAP_WIDTH := ARCH_WIDTH

## The beam's soffit, and the same number the west's carries for the same reason:
## it is the clear height, it is what the view through the opening is cropped by,
## and it is the one thing here that must not drift quietly. `_east_gate` asserts
## the scene against it to the centimetre, exactly as `_gate_house` does.
##
## Equal to `ARCH_HEIGHT` by choice rather than by derivation. The two gates face
## each other across the plaza and a player at the fountain sees both at once; a
## centimetre of difference would be invisible and a metre would be a mistake
## nobody could name.
const EAST_GAP_HEIGHT := ARCH_HEIGHT

## The seam, and **it mirrors the west gate rather than sitting anywhere near the
## cascade.** The load point is the passage, full stop: the arch's is at the west
## wall's own centre line and this is at the east wall's, which is
## `EAST_GAP_AT.x`. What stands beyond it — forecourt, monument, belvedere,
## staircase, hill — is scenery the section carries, not a thing the seam is
## sited against.
##
## Neither gate is a true tunnel any more. The west lost its lid on 2026-08-16
## and this one never had one, and both still work as load points for the reason
## `ParkSections` gives: what hides the swap is the *held shot*, not the ceiling.
const EAST_SEAM_AT := Vector3(EAST_GAP_AT.x, 1.5, ARCH_AT.y)
const EAST_SEAM_SIZE := Vector3(2.6, 3.0, EAST_GAP_WIDTH)

## Far enough back down the east spoke that the load has the walk to the mouth to
## finish in, and inside the plaza where the player is always coming from.
const EAST_PRELOAD_AT := Vector3(24.0, 1.5, ARCH_AT.y)
const EAST_PRELOAD_SIZE := Vector3(4.0, 3.0, 13.0)

## The held shot, per direction, and on the spoke's own centre line for the
## reason `ARCH_HOLD_WEST` gives: anywhere off the paving is somewhere a tree may
## be standing this regeneration.
const EAST_HOLD_OUT := {
	"from": Vector3(26.5, 3.5, -1.0),
	"look": Vector3(44.0, 2.4, -2.2),
}
const EAST_HOLD_IN := {
	"from": Vector3(50.5, 3.4, -2.0),
	"look": Vector3(38.0, 2.6, -2.0),
}

## Where the walk resumes, a stride past the gate on each side and on the spoke.
## Never inside the crossing volume, or arriving trips the gate that sent you.
const EAST_ARRIVE_IN := Vector3(30.0, 0.0, ARCH_AT.y)
const EAST_ARRIVE_IN_YAW := 90.0
const EAST_ARRIVE_OUT := Vector3(50.5, 0.0, ARCH_AT.y)
const EAST_ARRIVE_OUT_YAW := -90.0

## The standpoint the crop is measured from: furthest back anyone stands on the
## axis, which is just past the fountain's coping rather than out at the ring.
##
## The west learned this on 2026-08-16 and the arithmetic is the same facing
## either way. Walking *towards* an opening widens the visible band and raises the
## ceiling at once, and the ceiling wins — so the tight case is the near
## standpoint, not the far one. A margin quoted from one standpoint is not a
## margin.
const EAST_NEAR_STAND_X := 11.0


# ---------------------------------------------------------------------------
# The east cascade
# ---------------------------------------------------------------------------

## The same monument as the west's, climbing instead of descending.
##
## **It is a translation, not a mirror**, and that is the fact the whole thing
## turns on. A cascade's face is always on its low side, so both of these face
## west and on both of them downhill is −x. Nothing is reflected; the object is
## picked up and put down somewhere else. So there is one description and two
## sites, and every constant of shape above — `WING_W`, `WING_SEP`,
## `WING_LAND_D`, `WING_SLOPE_RUN`, `LANDING_HALF_W`, `NICHE_*`, `FOOT_STEPS` —
## is shared rather than copied.
##
## |      | top_x | floor | head |
## |------|-------|-------|------|
## | west | −58   | −6    | 0    |
## | east | 70    | 0     | 6    |
##
## **What the east gets that the west never can is the angle.** Every photograph
## of the Cleveland Cascade is taken from below, from the court, because that is
## where a cascade is meant to be seen from. The west one descends, so from inside
## the plaza you arrive at its top and look at its back — its face is only ever
## seen from the boardwalk, on the far side of a section seam. The east one
## presents its face to the plaza permanently, framed by the gap, from the moment
## you come round the fountain.
const CASCADE_EAST := {
	"tag": "east",
	"axis_z": ARCH_AT.y,
	"top_x": HILL_FACE_X,
	"wall_x": HILL_FACE_X - LANDING_D,
	"floor_y": 0.0,
	"head_y": HILL_TOP,
}

## The foot on the axis, in front of the three steps, and a standing point clear
## of them. Nobody arrives here — the wings land either side and the middle is
## water — but the forecourt's paving and the walk test both ask where the bottom
## of the climb is. The west's `STAIR_FOOT` is the same point at the other site.
const EAST_STAIR_FOOT := Vector3(
	HILL_FACE_X - LANDING_D - WING_SEP - WING_W - 2.5, 0.0, ARCH_AT.y)
const EAST_STAIR_FOOT_STAND := Vector3(EAST_STAIR_FOOT.x, 0.2, ARCH_AT.y)


## The rim's crest line, resampled at even spacing along its own length.
##
## **This replaced `rim_crest(z)`, and the old accessor could not survive the
## wrap.** A crest keyed on z is single-valued by construction; the moment the
## ridge turns west there are two crests at most values of z and none at all past
## the headland. Anything still asking "how high is the rim at this z" is asking
## a question the shape no longer answers.
##
## Returns, per sample: `at` (the crest in plan), `crest`, `foot`, `inward` (the
## unit normal pointing at the park) and `arc` (distance along the path from the
## start, which is what the jag is phased on — z would give a constant offset
## along the whole west arm and no variation at all).
##
## Catmull-Rom rather than straight lines between the control points, because a
## polyline's corners are creases and this is land. The dense pass is subdivided
## far finer than `step` and then resampled by arc length, so the spacing is even
## whatever the control points do — a curve parameter is not a distance, and
## sampling one as though it were bunches the columns through every turn.
static func rim_samples(step: float) -> Array:
	# **Reflected phantom ends, not duplicated ones.** Clamping the first span by
	# repeating `RIM_PATH[0]` gives that span a zero-length chord, and a zero
	# chord raised to `RIM_ALPHA` is a zero-width knot interval — every term in
	# the evaluation below divides by one. Reflecting the second point through
	# the first keeps the knots strictly increasing and leaves the end tangent
	# where a straight run wants it.
	var ctrl: Array = [_rim_reflect(RIM_PATH[0], RIM_PATH[1])]
	ctrl.append_array(RIM_PATH)
	ctrl.append(_rim_reflect(RIM_PATH[RIM_PATH.size() - 1],
		RIM_PATH[RIM_PATH.size() - 2]))

	var dense: Array = []
	for i in range(1, ctrl.size() - 2):
		var g: Array = [ctrl[i - 1], ctrl[i], ctrl[i + 1], ctrl[i + 2]]
		var kn := PackedFloat32Array([0.0, 0.0, 0.0, 0.0])
		for j in 3:
			var d: float = maxf((g[j]["at"] as Vector2)
				.distance_to(g[j + 1]["at"]), 0.0001)
			kn[j + 1] = kn[j] + pow(d, RIM_ALPHA)
		for k in RIM_SUBDIV:
			var t: float = kn[1] + (kn[2] - kn[1]) * float(k) / float(RIM_SUBDIV)
			dense.append({
				"at": Vector2(
					_rim_bg(g[0]["at"].x, g[1]["at"].x, g[2]["at"].x, g[3]["at"].x, kn, t),
					_rim_bg(g[0]["at"].y, g[1]["at"].y, g[2]["at"].y, g[3]["at"].y, kn, t)),
				"crest": _rim_bg(g[0]["crest"], g[1]["crest"], g[2]["crest"],
					g[3]["crest"], kn, t),
				"foot": _rim_bg(g[0]["foot"], g[1]["foot"], g[2]["foot"],
					g[3]["foot"], kn, t),
			})
	var last: Dictionary = RIM_PATH[RIM_PATH.size() - 1]
	dense.append({"at": last["at"], "crest": last["crest"], "foot": last["foot"]})

	# Cumulative length, then one pass picking the dense point at each multiple of
	# `step`. Linear between the two straddling it, which is exact enough at 32
	# subdivisions a span.
	var run: PackedFloat32Array = PackedFloat32Array()
	run.append(0.0)
	for i in range(1, dense.size()):
		var a: Vector2 = dense[i - 1]["at"]
		var b: Vector2 = dense[i]["at"]
		run.append(run[i - 1] + a.distance_to(b))
	var total: float = run[run.size() - 1]

	var out: Array = []
	var cols := int(round(total / step)) + 1
	var j := 0
	for c in cols:
		var want: float = minf(float(c) * step, total)
		while j < run.size() - 2 and run[j + 1] < want:
			j += 1
		var span: float = maxf(run[j + 1] - run[j], 0.0001)
		var t: float = clampf((want - run[j]) / span, 0.0, 1.0)
		var a: Dictionary = dense[j]
		var b: Dictionary = dense[j + 1]
		out.append({
			"at": (a["at"] as Vector2).lerp(b["at"], t),
			"crest": lerpf(a["crest"], b["crest"], t),
			"foot": lerpf(a["foot"], b["foot"], t),
			"arc": want,
		})

	# Tangents by central difference on the finished samples, so `inward` is the
	# normal of the line actually built rather than of the curve it came from.
	for i in out.size():
		var prev: Vector2 = out[maxi(i - 1, 0)]["at"]
		var next: Vector2 = out[mini(i + 1, out.size() - 1)]["at"]
		var tan: Vector2 = (next - prev)
		if tan.length() < 0.0001:
			tan = Vector2(0.0, -1.0)
		tan = tan.normalized()
		# Turned one way, and which way is the whole of what keeps the ridge right
		# side out. Down the east arm the tangent is (0, 1) and this is (-1, 0),
		# which points at the park; along the north arm the tangent is (1, 0) and
		# this is (0, 1), which points at the park again. See `RIM_PATH` on why the
		# list is ordered the way it is — the two are one decision.
		out[i]["inward"] = Vector2(-tan.y, tan.x)
	return out


## One control point mirrored through another, for the phantom ends.
static func _rim_reflect(a: Dictionary, b: Dictionary) -> Dictionary:
	return {
		"at": (a["at"] as Vector2) * 2.0 - (b["at"] as Vector2),
		"crest": float(a["crest"]) * 2.0 - float(b["crest"]),
		"foot": float(a["foot"]) * 2.0 - float(b["foot"]),
	}


## Barry-Goldman: a Catmull-Rom span evaluated against arbitrary knots, which is
## what makes the parameterization a choice rather than an assumption. With
## evenly spaced knots it is the uniform spline; with `RIM_ALPHA` at 0.5 it is
## the centripetal one. Three nested lerps and no special cases.
static func _rim_bg(v0: float, v1: float, v2: float, v3: float,
		kn: PackedFloat32Array, t: float) -> float:
	var a1 := ((kn[1] - t) * v0 + (t - kn[0]) * v1) / (kn[1] - kn[0])
	var a2 := ((kn[2] - t) * v1 + (t - kn[1]) * v2) / (kn[2] - kn[1])
	var a3 := ((kn[3] - t) * v2 + (t - kn[2]) * v3) / (kn[3] - kn[2])
	var b1 := ((kn[2] - t) * a1 + (t - kn[0]) * a2) / (kn[2] - kn[0])
	var b2 := ((kn[3] - t) * a2 + (t - kn[1]) * a3) / (kn[3] - kn[1])
	return ((kn[2] - t) * b1 + (t - kn[1]) * b2) / (kn[2] - kn[1])

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
## The wheel is 14m north of the alley's axis rather than on it, which is
## inherited from when it was scenery and is still right — the alley delivers
## you level with the machine rather than under it.
##
## Its platform is the reason the pier is no longer on that axis. 26m of the
## promenade's length, with the south fence at z -3, and the pier's mouth used
## to reach z -6 — three metres *inside* that span rather than short of it. See
## `PIER_Z`. There is 4.94m of clear promenade between them now, and the wheel's
## boarding side is out of the junction.
## The wheel's disc stands in the Z–Y plane so that it is face-on from the
## plaza, which means its footprint is 22m along z and about two across — a long
## thin thing, not a circle. Worth stating because the obvious mistake is to
## give it a round platform sized to its radius, and a 13m radius does not fit
## in a 17.5m promenade while a 2m axle fits anywhere.
## **It stands off the end of the promenade since 2026-08-20, on its own jetty.**
## The platform's east edge *is* `SHORE_EDGE`, so `WHEEL_AT.x` is derived and
## not typed: the whole 8m of it is over the water, and the strip runs past
## behind it at its full 17.5m.
##
## It used to stand on the promenade — axle at x -103, platform -107..-99 —
## which left 8.5m of walking room between it and the shopfronts, and the note
## here called that "room to spare". It is room to spare for *a walk*. It is not
## room for a walk plus a ride's boarding platform plus a ticket booth plus the
## queue for it, which is what was actually in it: the booth alone reached
## x -96.5 and the queue rail stood at -96, so the strip's clear half was 5.5m
## and everything that made the wheel a *ride* was standing in the promenade.
##
## A wheel is 26m across and the strip is 17.5m wide. There was never a position
## on the deck that did not have this problem; the question is only which way it
## faces. So the wheel steps off the boards and the promenade gets all of itself
## back, which is what the reference does too — a big ride on the water side
## goes on a structure of its own, and a wheel on a jetty is what Santa Monica
## has been a photograph of for a century.
##
## What it buys, measured: 14.5m from the queue rail to the shopfronts where
## there were 5.5m, and nothing belonging to the wheel standing on the walk at
## all except the booth and its rail, both of which are now east of the water's
## edge rather than in the middle of the deck.
##
## Two things follow and neither is optional. The platform and the wheel's feet
## are over water, so they carry piles like the pier's. And the promenade's
## edge rail, posts and lamp masts break across the platform's z-span — the
## thing beyond the edge there is the jetty, and a rail along the front of a
## boarding platform is a rail across the ride.
const WHEEL_RADIUS := 13.2
const WHEEL_PLATFORM := Vector2(8.0, 26.0)

## How far the jetty runs back *under* the shore rather than butting against it.
##
## `COASTER_EMBED`'s lesson at the other end of the strip, and it has to be
## stated because the derivation below produces the failure on its own: the
## shore's west face is `SHORE_EDGE` and a platform whose east edge is also
## `SHORE_EDGE` meets it exactly. Emitted, that came out as a one-millimetre
## overlap — which is the coplanar butt the house rule exists to forbid, and a
## zero-width seam is what the capsule catches on. Overlap, never meet.
const JETTY_EMBED := 0.4
const WHEEL_AT := Vector2(
	SHORE_EDGE - WHEEL_PLATFORM.x * 0.5 + JETTY_EMBED, -16.0)

## The platform's own edges, which four things need and none of them should
## re-derive: the jetty's piles, the break in the promenade's rail, the break in
## the lamp masts, and the crowd's obstacle for it.
const WHEEL_FROM_Z := WHEEL_AT.y - WHEEL_PLATFORM.y * 0.5
const WHEEL_TO_Z := WHEEL_AT.y + WHEEL_PLATFORM.y * 0.5
const WHEEL_EAST_X := WHEEL_AT.x + WHEEL_PLATFORM.x * 0.5

## How high the wheel actually stands.
##
## `WHEEL_TOP` is the world height of the rim's crown, and it is here because
## it is the number anything framing the west needs and the only one that could
## not be reached without opening a generated scene. `_wheel` in `gen_props.gd`
## builds the machine *to* these rather than these being a second survey of it:
## the deck is the platform the ring is raised onto, the hub is the axle above
## that deck, and the radius above is the rim.
##
## It was derived from outside once — an assumed 1.5m stand plus two radii —
## and came out 3.9m low, and the beam over the west arch was then sized to
## clear a wheel four metres shorter than the one in the park. Geometry a
## generator owns privately is geometry somebody will eventually guess at, so
## the height a landmark reaches is layout and belongs with the layout.
const WHEEL_DECK := 0.6
const WHEEL_HUB := 18.0
const WHEEL_TOP := SHORE_TOP + WHEEL_DECK + WHEEL_HUB + WHEEL_RADIUS

## The coaster closes the north end. Out-and-back along the shore, station
## fronting the promenade, structure running away from the player — so it is a
## thing you walk towards and then walk under, rather than a thing you look at.
const COASTER_STATION := Vector2(-94.0, -38.0)
const COASTER_HEADING := 0.0
const COASTER_FROM_Z := -38.0
const COASTER_TO_Z := -82.0

## The pier, rooted at the promenade edge and running west over the water to the
## pavilion at its head. The pavilion is the section's landmark and the reason
## the boardwalk is west at all: it is what the sun sets behind, seen from the
## plaza, at the hour the light is worth photographing.
##
## **It came off the alley's axis on 2026-08-20, and the reason is the wheel's
## landing rather than the pier.** Measured off the emitted scene rather than
## off these constants, which is the house rule and the only reason the real
## shape of it turned up: the wheel's platform runs z -29..-3 and the pier's
## mouth ran z -6..+2. They did not nearly meet, they **overlapped by three
## metres** — the pier's north rail stood inside the platform's own span, and
## the platform's south-west corner was the first thing you walked past getting
## onto the deck. So the machine's boarding side and the mouth of the pier were
## the same three metres of promenade, at the one junction where the alley, the
## strip and the pier all arrive at once.
##
## `PIER_Z` is 6.0 and that number is pinned at both ends rather than picked.
## Below it the overlap is only reduced. Above it the pier's south rail passes
## `GAP_TO` and the mouth stops being wholly inside the hole in the frontage —
## and the hole framing the *whole* pier is what the west composition is: the
## arch frames a gap, the gap frames the pier. So the pier goes as far south as
## it can while still being framed, and the junction gets **4.94m of clear
## promenade** — measured, fence face to deck edge — where it had a 3m overlap.
##
## Five metres is a junction rather than a plaza, and it is what the frontage
## allows. If it wants to be more, the lever is the wheel: the platform's south
## fence at z -3 is the other half of every number here.
##
## What it costs is the axis. The pier is no longer the thing you are aimed at
## walking west out of the tunnel; it is 8m off that line, about 4 degrees at
## the pavilion, and the gap still holds all of it from the fountain, the arch
## and the alley mouth. That is a real loss and it was taken deliberately, in
## exchange for the junction being walkable. Anything that assumed the pier was
## on `ALLEY_Z` reads `PIER_ROOT.y` now — the crowd's graph, the sea's corridor,
## `walk_test` and `west_capture` all did, and all had to be told.
const PIER_Z := 6.0
const PIER_ROOT := Vector2(SHORE_EDGE, PIER_Z)
const PIER_LENGTH := 44.0
const PIER_HALF_W := 4.0
const PAVILION_AT := Vector2(SHORE_EDGE - PIER_LENGTH - 6.0, PIER_Z)

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
## pier mouth and the wheel's frontage. Built rather than listed so the furniture
## and the people sitting on it cannot drift apart.
##
## The wheel's skip is its platform's z-span and not a radius any more. It was
## `absf(z - WHEEL_AT.y) > 9.0`, written when the platform stood *on* the
## promenade and the thing to avoid was the platform itself. The wheel moved
## onto its own jetty on 2026-08-20 and what is on the deck now is its
## frontage — the ticket booth at z -17.7..-20.3 and the queue rail running
## back to -28.4 — which the old radius did not cover: it reached -25 and the
## queue reaches -28.4. It produced the right answer anyway, because the bench
## spacing happens to put nothing between them. `BENCH_X` is -105.4 and the
## queue stands at -105.0, so the bench that rule was one step away from
## emitting would have been four centimetres from a queue post.
##
## The span covers both by construction, because the booth and the queue are
## laid out off the platform's own east edge.
static func bench_line() -> Array:
	var out := []
	var z := BENCH_FIRST_Z
	while z < WALK_TO_Z - 8.0:
		var clear_of_wheel := z < WHEEL_FROM_Z - 1.0 or z > WHEEL_TO_Z + 1.0
		if absf(z - PIER_ROOT.y) > 7.0 and clear_of_wheel:
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
## Where the two east sections stop, and it is the landform saying so rather than
## a number picked for them. See `SECTION_GROUND`.
const EAST_SECTION_TO_X := RIM_FOOT_X
const FRONTIER_FROM_X := 61.0
const KIDDIELAND_FROM_X := 65.0
## Its south edge is the east hill's north edge, so the two abut rather than
## claiming the same ground.
const FRONTIER_FROM_Z := ARCH_AT.y - EAST_GROUND_HALF_Z
const FRONTIER_TO_Z := -98.0

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
	# plaza. These are footprints for silhouette and none of them is built.
	#
	# **The two east ones were wrong in three ways at once and none of it could
	# have been noticed**, because `floor_y` here has no code consumer at all —
	# not one — and the `at`/`size` pair is read only by the minimap's markers,
	# which take the centre and ignore the extent. A table nothing reads does not
	# go stale slowly; it is simply never true again after the first thing moves.
	#
	# `floor_y` said 0.0 for `frontier` and `kiddieland` while `TERRACE_TWO_Y`,
	# thirty lines up this file, says in bold that this is what moved those two
	# off y = 0 and onto the hill. The prose was the decision and the table never
	# followed it.
	#
	# `frontier` reached x 151, which is past `RIM_CREST_X`: thirty-one metres of
	# its ground was inside a ridge that rises fifty. `kiddieland` reached 123 and
	# was three metres in. Both stop at `RIM_FOOT_X` now — a section's floor ends
	# where the landform standing on it begins, and the toe buried below that line
	# is exactly what terrace two is there to cover.
	#
	# And `frontier`'s south edge was z −22, six metres inside the east hill's own
	# ground, which is what put part of it under `_hill_roll`'s swell and off
	# level. It starts at the hill's north edge now, so the two describe adjacent
	# ground rather than the same ground twice — the argument
	# `EAST_GROUND_HALF_Z` already makes about the court and the hill, one
	# boundary further out.
	&"grove": {"at": Vector2(-9.0, -104.0), "size": Vector2(62.0, 84.0), "floor_y": 0.0},
	&"frontier": {
		"at": Vector2((FRONTIER_FROM_X + EAST_SECTION_TO_X) * 0.5,
			(FRONTIER_TO_Z + FRONTIER_FROM_Z) * 0.5),
		"size": Vector2(EAST_SECTION_TO_X - FRONTIER_FROM_X,
			FRONTIER_FROM_Z - FRONTIER_TO_Z),
		"floor_y": TERRACE_TWO_Y,
	},
	&"kiddieland": {
		"at": Vector2((KIDDIELAND_FROM_X + EAST_SECTION_TO_X) * 0.5, 63.0),
		"size": Vector2(EAST_SECTION_TO_X - KIDDIELAND_FROM_X, 58.0),
		"floor_y": TERRACE_TWO_Y,
	},
	&"fairground": {"at": Vector2(-29.0, 91.0), "size": Vector2(26.0, 76.0), "floor_y": 0.0},
}

## Which way out leads where. The keys are the threshold names in `THRESHOLDS`
## plus the two that are not thresholds — the west arch, whose seam is really the
## gate at the foot of the stair, and the street south to the gate, which leads
## out of the park rather than into a section.
const SPOKE_LEADS_TO := {
	&"west": &"boardwalk",
	&"east": &"terraces",
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

	## The same walk facing the other way: ring, bend onto the axis, through the
	## gate, and out across the forecourt to the foot of the climb.
	##
	## **Five vertices to the west's five, and the middle three are the same three
	## facts** — the ring's vertex, the gate's plaza face, the gate's far face.
	## What differs is the last one. The west ends at the overlook, which is a
	## place to stand and look at something; this ends at `EAST_STAIR_FOOT`, which
	## is a place the climb starts. Neither is an arrival: nobody walks up the
	## middle of a cascade, because the middle is water and the niche is blind.
	## The wings are the way up and they are their own runs, or will be — see the
	## note under `west_wing_north`, which had to be written the day somebody
	## noticed the descent was in no graph at all.
	##
	## Not in any crowd graph either, and that is deliberate for now: a guest sent
	## east would walk to the foot of a monument and stand there, because there is
	## nothing past it yet.
	&"spoke_east": [
		Vector2(16.0, 0.0), Vector2(26.0, EAST_GAP_AT.y),
		Vector2(EAST_GAP_MOUTH_X, EAST_GAP_AT.y),
		Vector2(EAST_GAP_FAR_X, EAST_GAP_AT.y),
		Vector2(EAST_STAIR_FOOT.x, EAST_GAP_AT.y),
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
	## **It stops at the bluff top now**, because the middle is water and there is
	## nothing down there to walk on. It is the approach across the terrace to the
	## head of the descent, and the descent itself is the two wings below.
	&"west_stair": [
		Vector2(-46.0, CASCADE_AXIS_Z), Vector2(CASCADE_TOP_X + 1.0, CASCADE_AXIS_Z),
	],

	## The two ways down, and **they were in no graph at all until the wings were
	## rebuilt.** Nothing described them, so the minimap drew one way off the bluff
	## where there are two, and every rule that reads the park's circulation was
	## answering about a monument it could not see most of.
	##
	## Four vertices each: the landing's outer corner, both ends of the turn, and
	## the foot. Written out rather than called, because a `const` dictionary
	## cannot hold a function call — but every coordinate is the expression
	## `wing_path` uses, and `walk_test` walks both wings to catch a disagreement.
	&"west_wing_north": [
		Vector2(CASCADE_TOP_X + 1.0, CASCADE_AXIS_Z),
		Vector2(CASCADE_WALL_X + WING_W * 0.5, CASCADE_AXIS_Z - LANDING_HALF_W),
		Vector2(CASCADE_WALL_X + WING_W * 0.5, CASCADE_AXIS_Z - WING_TURN_Z),
		Vector2(CASCADE_WALL_X - WING_SEP - WING_W * 0.5, CASCADE_AXIS_Z - WING_TURN_Z),
		Vector2(CASCADE_WALL_X - WING_SEP - WING_W * 0.5, CASCADE_AXIS_Z - LANDING_HALF_W),
		## And west into the back lane, where the two wings rejoin.
		Vector2(BACK_LANE_X, CASCADE_AXIS_Z - LANDING_HALF_W),
	],
	&"west_wing_south": [
		Vector2(CASCADE_TOP_X + 1.0, CASCADE_AXIS_Z),
		Vector2(CASCADE_WALL_X + WING_W * 0.5, CASCADE_AXIS_Z + LANDING_HALF_W),
		Vector2(CASCADE_WALL_X + WING_W * 0.5, CASCADE_AXIS_Z + WING_TURN_Z),
		Vector2(CASCADE_WALL_X - WING_SEP - WING_W * 0.5, CASCADE_AXIS_Z + WING_TURN_Z),
		Vector2(CASCADE_WALL_X - WING_SEP - WING_W * 0.5, CASCADE_AXIS_Z + LANDING_HALF_W),
		## And west into the back lane, where the two wings rejoin.
		Vector2(BACK_LANE_X, CASCADE_AXIS_Z + LANDING_HALF_W),
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
	## **From the promenade, not from the pier's own root.** `PIER_ROOT` is where
	## the *deck* starts, at `SHORE_EDGE`, and the promenade's line is 8.8m
	## inland of that — so a run written root-to-head drew a pier with no way
	## onto it. It survived while the pier sat on `ALLEY_Z`, because then the
	## alley, the promenade crossing and the pier were all on z -2 and the gap
	## read as one straight line west with a dashed bit in the middle. Off the
	## axis it reads as what it always was: a line floating in the water.
	##
	## A walkway is where the player can go, and the eight metres from the strip
	## to the deck are somewhere they can go.
	&"boardwalk_pier": [
		Vector2(PROMENADE_X, PIER_Z),
		Vector2(PIER_ROOT.x - PIER_LENGTH, PIER_ROOT.y),
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
	## The west spoke's width, for the west spoke's reason: the last few metres
	## on the plaza side are a forecourt in front of the gate rather than a
	## throat, and the 6m opening is narrower than the approach to it on purpose.
	&"spoke_east": 8.0,
	## The width of the flight it leads to.
	&"west_stair": FLIGHT_W,
	## The width of the deck, and no more. The legs run within a metre of each
	## other, so the default 6m would have consecutive legs of one route arguing
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

## Every walkway as the polyline it is, with the width it is paved to.
##
## The companion to `walkway_segments`, and the difference matters to anything
## that draws paving rather than lines: a run's joints are its own business, and
## a consumer handed loose segments has to guess which of them meet. The minimap
## drew the segments and every joint in the park came out as a butt end.
static func walkway_runs() -> Array:
	var out := []
	for id in WALKWAYS:
		out.append({"id": id, "points": WALKWAYS[id],
			"width": WALKWAY_WIDTH.get(id, 6.0)})
	return out


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


## The four points a wing turns through: the landing's outer corner, the two ends
## of the landing at the turn, and the foot back beside the middle. `side` is −1
## for the north wing and +1 for the south.
##
## The turn is level and carries none of the fall, which is why it is two points
## and not one, and it is what makes the hairpin free.
##
## **`site` is which cascade**, and there are two — `CASCADE_WEST`, which falls
## off the bluff to the boardwalk, and `CASCADE_EAST`, which climbs the rim to
## the first terrace. See `CASCADE_EAST` for why one description serves both and
## why that is not a coincidence: a cascade's face is always on its low side, so
## the east one is the west one *translated*, not mirrored. Downhill is −x on
## both, and only `top_x` and `floor_y` differ.
static func wing_path(site: Dictionary, side: float) -> Array:
	var half := WING_W * 0.5
	var wall_x: float = site["wall_x"]
	var axis: float = site["axis_z"]
	var head: float = site["head_y"]
	var out_x := wall_x + half
	var ret_x := wall_x - WING_SEP - half
	var near: float = axis + side * LANDING_HALF_W
	var far: float = axis + side * WING_TURN_Z
	return [
		Vector3(out_x, head, near),
		Vector3(out_x, head - CASCADE_DROP * 0.5, far),
		Vector3(ret_x, head - CASCADE_DROP * 0.5, far),
		Vector3(ret_x, head - CASCADE_DROP, near),
	]


## Where a leg's slope actually stops: a full landing short of the turn it
## touches. The stretch from here to the turn is level, and laying a sloping
## surface over it puts a step in the middle of the descent.
##
## **The legs and the landing are both laid off this**, which is the whole reason
## it exists. They used to be laid off two different assumptions — the legs ran
## to the turn vertex and the landing started at it — so the two agreed only by
## accident, and where they disagreed there was a slot.
static func wing_leg_end(site: Dictionary, side: float, leg: int, end: int) -> Vector3:
	var path := wing_path(site, side)
	var a: Vector3 = path[leg * 2]
	var b: Vector3 = path[leg * 2 + 1]
	var from: Vector3 = a if end == 1 else b
	var to: Vector3 = b if end == 1 else a
	# Only the ends that touch the turn are pulled in. The head of the outbound
	# leg and the foot of the return are where the route starts and stops.
	if (leg == 0 and end == 0) or (leg == 1 and end == 1):
		return to
	var d := absf(to.z - from.z)
	if d < 0.01:
		return to
	var e := from.lerp(to, 1.0 - WING_LAND_D / d)
	# The height is the turn's, not the lerp's: the leg has finished falling by
	# the time it gets here, which is the whole distinction being drawn.
	return Vector3(e.x, to.y, e.z)


## The gradient a wing runs at, as 1 in this. A stair here, so about 2 — asked
## for the same reason a ramp's is: to catch a constant that moved without
## anybody noticing what it moved.
##
## Both sites answer the same, because the two cascades differ only in where they
## are and not in what shape they are. That makes this an equality check as well
## as a measurement, and `walk_test` uses it as one: if the west is ever tuned in
## a way that does not reach the east, this is where it shows.
static func wing_gradient(site: Dictionary) -> float:
	var path := wing_path(site, -1.0)
	var run := 0.0
	for leg in 2:
		var a: Vector3 = path[0] if leg == 0 else path[2]
		var b: Vector3 = path[1] if leg == 0 else path[3]
		run += Vector2(a.x, a.z).distance_to(Vector2(b.x, b.z))
	return run / CASCADE_DROP


## The slope of a wing's sloping legs, as rise over run — **the one derivation of
## it**, and the reason this function exists rather than the expression being
## written out where it is needed.
##
## `(a.y − b.y) / |b.z − a.z|` was computed in three separate places by
## 2026-08-16: inside `_cascade_wing` for the mass's pitch, inside
## `_cascade_crest` for the shoulder's landing tangent, and inside the wing's own
## rail. Three copies of one number is how `WING_SLOPE_RUN` could move and leave
## one of them behind — and the shoulder is laid *tangent* to this, so a stale
## copy would not look broken, it would look very slightly wrong in a way nobody
## could name.
##
## Measured off the outbound leg of the north wing. Both wings and both legs run
## at the same pitch by construction; if they ever stop doing, that is a bug in
## `wing_path` rather than something a caller should be compensating for.
static func wing_slope(site: Dictionary) -> float:
	var a := wing_leg_end(site, -1.0, 0, 0)
	var b := wing_leg_end(site, -1.0, 0, 1)
	return (a.y - b.y) / maxf(0.01, absf(b.z - a.z))


## A point on a wing, `t` along it by distance — the turn included, so `t`
## measures walking rather than falling.
static func wing_point(site: Dictionary, side: float, t: float) -> Vector3:
	var path := wing_path(site, side)
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
	# **These two used to meet at z +2 with no gap between them**, which said the
	# east wall was solid across the very place the gate was cut on 2026-08-17.
	# Nothing noticed for a day because this table is only read by the crowd's
	# walkability check and the crowd's graph stopped eleven metres short of the
	# wall — the first node put out there was blocked by a wall that is not
	# there. The opening is `ARCH_AT.y` ± 3, so the runs stop at −5 and +1.
	{"at": Vector2(41.5, -12.2), "half": Vector2(5.5, 7.2)},
	{"at": Vector2(41.5, 12.9), "half": Vector2(5.5, 11.9)},
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
