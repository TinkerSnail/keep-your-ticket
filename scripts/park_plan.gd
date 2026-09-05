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

## The clock tower sits beside the ceremonial boulevard, not in it.
##
## The rebuild's reference plan makes the entrance–plaza–headland line the one
## route that never apologises for itself. Keeping the tower on that centreline
## would force the new 11m trunk into two narrow doglegs before it even left the
## hub — exactly the inherited-path habit the rebuild removes. At (20, −28) the
## clock keeps its full plaza silhouette, reads from the entrance as a landmark
## on the right of the axis, and leaves the boulevard and its north portal open.
## It is still the park's timepiece; it is now something you orient by rather
## than an obstacle you route around.
const CLOCK_TOWER_AT := Vector2(20.0, -28.0)

## The photo hut — the job's anchor, and the one building in the plaza the
## player has business inside.
##
## It used to stand at (9, 8), which is radius 12 — *inside* what became the
## first ring walkway — and then moved to (21, 18.5). Package 04 exposed that
## second address as another version of the same mistake: the approved 18m hub
## ring covered its western corner and D's ten-metre Plaza return ran through
## the building itself. The Player hit the south wall at (21.9, 21.0), slid
## along it, and reached the fountain instead of the named J7→hub connection.
##
## The rebuild's instruction is unambiguous when a suggested building position
## conflicts with its circulation: the path controls. At (-25, 25) the hut
## occupies the open southwest edge, still faces the fountain, and has more than
## four metres beyond both the hub ring and C's Plaza return. Its inward queue
## stands between the kiosk and the fountain rather than across a through-route.
const PHOTO_HUT_AT := Vector2(-25.0, 25.0)
const PHOTO_HUT_QUEUE_X_OFFSET := 6.0

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
	# Shifted out and south of B's westbound monument route. This remains one
	# coherent terrace against the west frontage; no chair projects into either
	# the nine-metre connector or the broad hub ring.
	{"at": Vector2(-31.0, 6.0), "theta": 15.0},
	{"at": Vector2(-29.0, 10.5), "theta": -25.0},
	{"at": Vector2(-27.0, 15.0), "theta": 40.0},
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

## The three threshold mouths, moved here verbatim from `gen_props.gd`.
##
## Bearings are approximate on purpose. The star is a skeleton — points anchor a
## section's centre line, edges are free — so these sit where the perimeter had
## room rather than on exact rays. From the fountain: roughly 342, 121 and 211
## degrees, against a west arch at 273 and the entrance street at 182.
##
## The old north-east passage at 62 degrees came out on 2026-08-25. Once the
## due-east gate opened onto a real section, a second east opening no longer
## clarified the park: it competed with the gate, led to an unbuilt land twelve
## metres above it and exposed the retaining work below the north shoulder. Its
## old opening is occupied by the indoor dark ride at `PLAZA_DARK_RIDE_AT`;
## the future northern land belongs off the upper terrace instead of through a
## second ground-level hole in the same wall.
##
## Widened with the plaza. A 12m mouth in a 78m wall and a 12m mouth in a 102m
## wall are not the same opening: the second reads as a crack. These are scaled
## by roughly the same 1.3 the perimeter is.
const THRESHOLDS := [
	{"name": "nnw", "at": Vector3(-16.9, 0.0, -51.5), "theta": PI, "width": 16.0, "turn": 1.0},
	# Kiddieland is built enough to be a destination. Its threshold is an open
	# public gateway, not one of the concealed placeholder passages.
	{"name": "se", "at": Vector3(51.5, 0.0, 31.3), "theta": PI * 0.5,
		"width": 13.0, "turn": -1.0, "open": true},
	{"name": "sw", "at": Vector3(-31.3, 0.0, 51.5), "theta": 0.0, "width": 10.0, "turn": -1.0},
]

## The indoor dark ride's plaza entrance. The building's inner face is x 36;
## this stands half a metre in front of its loading mouth so map markers, crowd
## attention and tests all point at the same entrance. It is a plaza place, not
## the destination of a spoke: the surrounding brick is its forecourt.
const PLAZA_DARK_RIDE_AT := Vector2(35.5, -27.4)

## How far an unopened passage runs before it bends, and how far it carries
## after. The bend buys a future section load its cover. It no longer applies to
## the SE gateway: keeping that placeholder baffle after Kiddieland opened made
## a connected route read as a chain of walls and service alleys.
const REACH := 9.0
const BEND := 7.0

## The first piece of Kiddieland, beginning on the plaza face of the south-east
## gateway. The entrance-street breezeway is the land's primary arrival:
## families can turn into Kiddieland before being forced through the plaza. The
## open gateway is the secondary link back to the hub. Both routes meet on one
## level commons rather than at an attraction queue, and the shared family spine
## begins at that junction.
##
## From that junction the family spine makes one long, shallow S across the
## south shoulder. This is the stroller route, so its steepest published segment
## stays under 1:12; the old diagonal climbed at 1:8.6, crossed the miniature
## railway almost immediately, then aimed its unfinished gate at the parking
## lot. The new line spends horizontal distance instead, and its last segment
## points north-east toward the carousel and the eventual south-crest loop.
##
## The railway station and photo bay are short branches inside the S. The track
## stays on their side of the promenade and never crosses the through route.
## They are published with it because generated ground and walking tests must
## agree on every public centreline. The final spine point is still a temporary
## seam, not the eventual section entrance.
const KIDDIE_ARRIVAL_POINTS: Array[Vector3] = [
	# Straight through the arch before making the one visible turn outside it.
	Vector3(51.5, 0.0, 31.3),
	Vector3(58.0, 0.0, 31.3),
	Vector3(58.0, 0.0, 44.0),
	Vector3(55.0, 0.0, 55.0),
	Vector3(49.0, 0.05, 67.0),
	# The primary entrance route arrives dead straight on this commons junction.
	Vector3(43.0, 0.20, 81.0),
	Vector3(54.0, 0.80, 88.0),
	Vector3(68.0, 1.75, 91.0),
	Vector3(82.0, 2.85, 88.0),
	Vector3(93.0, 3.85, 79.0),
	Vector3(101.0, 4.75, 67.0),
]
## Points zero through two are the broad gateway itself. Its width matches the
## architectural opening: a thirteen-metre arch over an eight-metre path left
## two strips of the apparent public way hanging over open world, and made the
## retaining return beside it look as though it stood in the route. Points two
## through five are the quieter plaza return; point five is the commons junction
## and every point after it is the primary family spine shared by both arrivals.
const KIDDIE_GATEWAY_INDEX := 2
const KIDDIE_COMMONS_INDEX := 5
const KIDDIE_GATEWAY_W := 13.0
const KIDDIE_PLAZA_LINK_W := 5.5
const KIDDIE_PRIMARY_PATH_W := 8.0
const KIDDIE_ARRIVAL_BANK_W := 12.0
## A broad planted valley, not a path-width trench through the shoulder.
const KIDDIE_ARRIVAL_GRADE_RUN := 12.0
const KIDDIE_ARRIVAL_PATH_LIFT := 0.16
## The entrance-street leg. Its first point is the clear opening through the east
## frontage; it stays on one sightline all the way to the family spine.
const KIDDIE_ENTRANCE_LINK: Array[Vector3] = [
	Vector3(6.0, 0.0, 81.0),
	Vector3(18.0, 0.0, 81.0),
	Vector3(30.0, 0.05, 81.0),
	Vector3(43.0, 0.20, 81.0),
]
const KIDDIE_ENTRANCE_LINK_W := 7.5
const KIDDIE_ENTRANCE_PORTAL_Z := 81.0
const KIDDIE_ENTRANCE_PORTAL_W := 9.5

## A quiet garden link across the family commons. Together with the primary
## entrance route and the plaza return it makes a complete walking loop, so the
## support lawn is useful circulation rather than a rectangle guests enter and
## have to back out of. It is deliberately narrower than either public arrival.
const KIDDIE_COMMONS_GARDEN_LINK: Array[Vector3] = [
	Vector3(26.0, 0.0, 81.0),
	Vector3(26.0, 0.0, 70.0),
	Vector3(31.0, 0.0, 63.0),
	Vector3(42.0, 0.0, 63.0),
	Vector3(49.0, 0.05, 67.0),
]
const KIDDIE_COMMONS_GARDEN_W := 3.8

const KIDDIE_STATION_AT := Vector3(54.0, 0.25, 69.5)
const KIDDIE_STATION_SPUR: Array[Vector3] = [
	Vector3(49.0, 0.05, 67.0),
	Vector3(47.0, 0.12, 69.0),
	Vector3(51.0, 0.25, 69.5),
]
const KIDDIE_STATION_SPUR_W := 3.8
const KIDDIE_STATION_GRADE_RUN := 4.0
## A ride, not a decorative length of rail. The west tangent stays exactly where
## the first platform was built; the rest closes into a small oval inside the S
## of the family route. It has no public crossing. The east side rises by 45cm
## metre over half a circuit — 3.0% at the steepest sampled chord — which is
## enough to belong to the shoulder without asking a miniature locomotive to
## climb the land's full grade.
const KIDDIE_RAIL_CENTRE := Vector2(69.5, 69.5)
const KIDDIE_RAIL_RADIUS := Vector2(11.0, 7.5)
const KIDDIE_RAIL_WEST_Y := 0.35
const KIDDIE_RAIL_EAST_Y := 0.80
const KIDDIE_RAIL_STEPS := 48
const KIDDIE_RAIL_GAUGE := 1.24
const KIDDIE_TRACK_GRADE_RUN := 3.0


static func kiddie_rail_loop() -> Array[Vector3]:
	var out: Array[Vector3] = []
	# Begin on the west tangent beside the platform and run clockwise. Repeating
	# the first point at the end makes both track emission and distance sampling
	# ordinary open-polyline work with a closed result.
	for i in KIDDIE_RAIL_STEPS + 1:
		var a := PI + TAU * float(i) / float(KIDDIE_RAIL_STEPS)
		var x := KIDDIE_RAIL_CENTRE.x + cos(a) * KIDDIE_RAIL_RADIUS.x
		var z := KIDDIE_RAIL_CENTRE.y + sin(a) * KIDDIE_RAIL_RADIUS.y
		var across := (x - (KIDDIE_RAIL_CENTRE.x - KIDDIE_RAIL_RADIUS.x)) \
			/ (KIDDIE_RAIL_RADIUS.x * 2.0)
		var y := lerpf(KIDDIE_RAIL_WEST_Y, KIDDIE_RAIL_EAST_Y, across)
		out.append(Vector3(x, y, z))
	return out


## The whole-park transport line. This is a rubber-tyred road train rather than
## a second railway: the park falls from +20m on the east shoulder to -6m on the
## boardwalk, and a train-sized rail grade would either consume a land in loops
## or force structures through both protected cascades. A road train can take
## the long outer gradients and still read as the local park's answer to a grand
## circle railroad.
##
## The route is persistent park infrastructure. It stays outside the pedestrian
## spines, dives under the east highland, descends behind the boardwalk frontage,
## and uses the parking-edge void for its main station. Future lands inherit this
## right-of-way; they do not get to build over it and solve transport afterwards.
##
## **Moved to the expanded reserve on 2026-09-02.** The compact loop was drawn
## before the rebuild had an outer envelope. It consequently shared metres of
## route A at the Headland, ran almost tangent to B's south return, and crossed
## the Cascading Staircases construction envelope on the Boardwalk back lane.
## The new line is the perimeter decision: north and south have the extra land
## the approved footprint gives them, the eastern reach is below the highland,
## and the Boardwalk chord holds at x=-78, 1.3m clear of NT-1 even after the
## lane's full width is counted. Where it crosses B it does so transversely and
## outside the monument, never by sharing a centreline.
const GRAND_TRAM_LANE_W := 5.4
const GRAND_TRAM_ENTRY_ACCESS: Array[Vector3] = [
	Vector3(37.0, 0.0, 106.0),
	Vector3(44.0, 0.14, 167.1),
]
const GRAND_TRAM_ENTRY_ACCESS_W := 5.2
const GRAND_TRAM_CONTROLS: Array[Vector3] = [
	Vector3(0.0, 0.0, 174.0),
	Vector3(44.0, 0.0, 172.0), # entry / Kiddieland station
	Vector3(92.0, 2.0, 160.0),
	Vector3(146.0, 4.0, 136.0),
	Vector3(188.0, 6.0, 96.0),
	Vector3(208.0, 5.0, 45.0),
	Vector3(210.0, 5.0, -24.0),
	Vector3(196.0, 7.0, -91.0),
	Vector3(166.0, 7.2, -145.0), # east-highland station
	Vector3(120.0, 6.0, -185.0),
	Vector3(62.0, 0.0, -214.0), # Grove station
	Vector3(-12.0, 0.0, -220.0),
	Vector3(-62.0, -2.0, -204.0),
	Vector3(-88.0, -4.5, -170.0),
	Vector3(-78.0, -6.0, -82.0),
	Vector3(-78.0, -6.0, -20.0),
	Vector3(-78.0, -6.0, 24.0), # boardwalk station
	Vector3(-78.0, -6.0, 44.0),
	Vector3(-104.0, -5.0, 72.0),
	Vector3(-104.0, -2.0, 130.0),
	Vector3(-80.0, -0.5, 155.0),
	Vector3(-48.0, 0.0, 166.0), # fairground station
]
const GRAND_TRAM_STATIONS := [
	{"id": &"entry", "at": Vector3(44.0, 0.0, 172.0), "theta": 0.0},
	{"id": &"east", "at": Vector3(166.0, 7.2, -145.0), "theta": 2.08},
	# The northern loop runs east-west here and the public land is to its south.
	# Facing the stop through PI keeps the platform on that inside edge; at zero
	# it stood north of the lane and any Grove access had to cross the vehicles.
	{"id": &"grove", "at": Vector3(62.0, 0.0, -214.0), "theta": PI},
	# East-facing platform: its twenty-metre length remains south of NT-1 and
	# its public side occupies the open service lane, not the shop backs.
	{"id": &"boardwalk", "at": Vector3(-78.0, -6.0, 24.0), "theta": -PI * 0.5},
	{"id": &"fairground", "at": Vector3(-48.0, 0.0, 166.0), "theta": -0.20},
]

## Every place a public pedestrian trunk crosses the Grand Circuit. These are
## authored decisions, not incidental overlaps: the transit generator marks
## them, and `footprint_test.gd` proves each marker remains on both routes. The
## arrival crossing is dressed by `entrance.tscn`; the three boardwalk-side
## crossings belong to persistent transit infrastructure.
const GRAND_TRAM_CROSSINGS := [
	{"id": &"entry", "at": Vector3(0.0, 0.0, 174.0),
		"pedestrian": &"a_parking_arrival", "owner": &"entrance"},
	{"id": &"boardwalk_north", "at": Vector3(-77.3, -4.2, -64.3),
		"pedestrian": &"b_north_return", "owner": &"park_transit"},
	{"id": &"boardwalk_monument", "at": Vector3(-78.0, -6.0, -2.0),
		"pedestrian": &"b_monument_return", "owner": &"park_transit"},
	{"id": &"boardwalk_south", "at": Vector3(-96.0, -6.0, 60.0),
		"pedestrian": &"b_waterfront",
		"captures": [&"b_waterfront", &"b_south_return"],
		"owner": &"park_transit"},
]


## Smooth enough for the articulated vehicles to turn continuously, sampled
## densely enough that the generated lane can use straight chords without
## showing corners. Uniform Catmull-Rom is safe here because the controls are
## deliberately kept within one order of spacing; this is a transport reserve,
## not the rim's irregular survey where centripetal knots are load-bearing.
static func grand_tram_loop(samples_per_span := 8) -> Array[Vector3]:
	var out: Array[Vector3] = []
	var n := GRAND_TRAM_CONTROLS.size()
	for i in n:
		var p0: Vector3 = GRAND_TRAM_CONTROLS[posmod(i - 1, n)]
		var p1: Vector3 = GRAND_TRAM_CONTROLS[i]
		var p2: Vector3 = GRAND_TRAM_CONTROLS[(i + 1) % n]
		var p3: Vector3 = GRAND_TRAM_CONTROLS[(i + 2) % n]
		for j in samples_per_span:
			var t := float(j) / float(samples_per_span)
			var t2 := t * t
			var t3 := t2 * t
			out.append(0.5 * ((2.0 * p1)
				+ (-p0 + p2) * t
				+ (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2
				+ (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3))
	if not out.is_empty():
		out.append(out[0])
	return out


const KIDDIE_PHOTO_SPUR: Array[Vector3] = [
	Vector3(68.0, 1.75, 91.0),
	Vector3(63.0, 1.40, 84.0),
	Vector3(60.0, 1.05, 80.5),
]
const KIDDIE_PHOTO_SPUR_W := 3.2
const KIDDIE_PHOTO_AT := Vector3(60.0, 1.05, 79.2)
const KIDDIE_PHOTO_GRADE_RUN := 3.0

## The first piece of the fairground, beginning at the west-facing end of the
## south-west passage. This is a midway in the literal sense: one continuous
## public route with things to do along it, not a sequence of attractions the
## through-crowd has to cross. The first bend gets the route clear of the
## threshold, then the spine runs south between game aprons and the big-top
## court. Its last point is a temporary seam for the later western sunset loop.
const FAIR_ARRIVAL_POINTS: Array[Vector3] = [
	Vector3(-43.5, 0.0, 55.5),
	Vector3(-43.5, 0.0, 62.0),
	Vector3(-40.0, 0.0, 68.0),
	Vector3(-40.0, 0.0, 81.0),
	Vector3(-40.0, 0.0, 94.0),
	Vector3(-37.0, 0.0, 104.0),
]
const FAIR_ARRIVAL_PATH_W := 7.5
const FAIR_ARRIVAL_PATH_LIFT := 0.018
const FAIR_BIG_TOP_AT := Vector3(-28.5, 0.0, 91.0)
const FAIR_BIG_TOP_SPUR: Array[Vector3] = [
	Vector3(-40.0, 0.0, 89.0),
	Vector3(-35.5, 0.0, 91.0),
]
const FAIR_BIG_TOP_SPUR_W := 3.8
## The existing walk-in arcade is the fairground's second public door. Its rear
## exit turns the first build into a loop through the entrance street instead
## of making every guest return through the southwest passage.
const FAIR_ARCADE_SPUR: Array[Vector3] = [
	Vector3(-40.0, 0.0, 78.0),
	Vector3(-34.0, 0.0, 78.0),
	Vector3(-29.5, 0.0, 78.0),
]
const FAIR_ARCADE_SPUR_W := 4.5
const FAIR_PHOTO_AT := Vector3(-46.0, 0.0, 98.0)
const FAIR_PHOTO_SPUR: Array[Vector3] = [
	Vector3(-39.0, 0.0, 97.3),
	Vector3(-44.5, 0.0, 98.0),
]
const FAIR_PHOTO_SPUR_W := 3.2


## The first public room in the Grove. The north-north-west passage turns west
## before it opens, so the route begins on that heading and then spends one
## broad movement turning north-east toward the sky-ride pavilion. From the
## arrival court the pavilion is the near landmark and the Grand Circuit canopy
## is the far one; neither attraction sits on the through centreline.
##
## The main spine stops at a tee behind the transit platform. Its west branch is
## a quieter garden loop, its short centre branch is the sky ride, and its east
## spur reserves the eventual climb through Frontier. That last route remains a
## gate because the eighteen-metre grade belongs to the full northern land, not
## to a short connector improvised at this boundary.
const GROVE_ARRIVAL_POINTS: Array[Vector3] = [
	# Through the north side of the west-facing header, then one continuous
	# clockwise turn into the land. The old centre-header point at z −52.5 aimed
	# the reveal out across the bluff before doubling back north; this curve keeps
	# the first thing beyond the passage inside the Grove arrival pocket.
	Vector3(-32.45, 0.0, -58.0),
	Vector3(-36.0, 0.0, -62.0),
	Vector3(-35.5, 0.0, -68.0),
	Vector3(-30.0, 0.0, -75.0),
	Vector3(-18.0, 0.0, -84.0),
	Vector3(-7.0, 0.0, -89.0),
	Vector3(2.0, 0.0, -99.0),
	Vector3(7.0, 0.0, -111.0),
	Vector3(6.0, 0.0, -122.0),
	Vector3(3.0, 0.0, -130.0),
]
const GROVE_ARRIVAL_PATH_W := 8.0

## A second route round the shaded side of the land. It rejoins the primary
## spine before the tram court, so picnic groups and photographers never have
## to reverse through the arrival passage.
const GROVE_GARDEN_LOOP: Array[Vector3] = [
	Vector3(-30.0, 0.0, -75.0),
	Vector3(-36.0, 0.0, -83.0),
	Vector3(-36.0, 0.0, -96.0),
	Vector3(-34.0, 0.0, -109.0),
	Vector3(-31.0, 0.0, -122.0),
	Vector3(-20.0, 0.0, -129.0),
	Vector3(-8.0, 0.0, -127.0),
	Vector3(6.0, 0.0, -122.0),
]
const GROVE_GARDEN_PATH_W := 4.8

## Side destinations leave the through flow before anyone queues or stops. The
## sky-ride spur meets the clear south face of its octagonal platform; the tram
## approach rises fifteen centimetres into the back of its inward-facing court.
const GROVE_SKY_RIDE_SPUR: Array[Vector3] = [
	Vector3(-18.0, 0.0, -84.0),
	Vector3(-18.0, 0.0, -91.0),
	Vector3(-18.0, 0.07, -97.7),
]
const GROVE_SKY_RIDE_SPUR_W := 4.8
const GROVE_TRAM_ACCESS: Array[Vector3] = [
	Vector3(3.0, 0.0, -130.0),
	# A real continuation through the expanded northern reserve. It stays east of
	# the Headland loop, then arrives on the public half of the new inward-facing
	# platform without crossing the vehicle lane.
	Vector3(15.0, 0.0, -145.0),
	Vector3(27.0, 0.0, -166.0),
	Vector3(42.0, 0.0, -188.0),
	Vector3(58.0, 0.14, -209.1),
]
const GROVE_TRAM_ACCESS_W := 5.2

const GROVE_FRONTIER_HANDOFF: Array[Vector3] = [
	Vector3(7.0, 0.0, -111.0),
	Vector3(13.0, 0.0, -109.0),
	# Stop a walking-width short of the boundary gate. The ribbon's cap reaches
	# it, while a test/player placed at the published endpoint begins clear of
	# the collision instead of being depenetrated through it.
	Vector3(20.4, 0.0, -104.1),
]
const GROVE_FRONTIER_HANDOFF_W := 5.2
const GROVE_FRONTIER_GATE_AT := Vector3(22.0, 0.0, -103.0)
const GROVE_FRONTIER_GATE_W := 6.0

const GROVE_PHOTO_SPUR: Array[Vector3] = [
	Vector3(-31.0, 0.0, -122.0),
	Vector3(-28.2, 0.0, -120.5),
	Vector3(-26.8, 0.0, -118.8),
]
const GROVE_PHOTO_SPUR_W := 3.2
const GROVE_PHOTO_AT := Vector3(-26.2, 0.0, -118.2)
const GROVE_POND_AT := Vector3(-19.5, 0.0, -118.0)
const GROVE_POND_R := 5.4


# ---------------------------------------------------------------------------
# The entrance street, south to the gate
# ---------------------------------------------------------------------------

## The street's centre line and half-width, where it leaves the plaza, the
## turnstiles, and the apron outside them.
##
## **Lengthened with the park footprint on 2026-09-02.** The gate and apron are
## the southern instances of the approved 1.55 expansion, measured from z=52 so
## the plaza wall and its protected core do not move. Buildings retain their
## real widths; the extra thirty metres becomes more frontage rather than
## stretched architecture. The clear arrival continues beyond the apron through
## two parking fields to the outer boundary.
const STREET_X := -1.5
const STREET_HALF := 7.5
const STREET_FROM_Z := 50.0
const GATE_Z := 137.25
const APRON_Z := 162.05

const PARKING_FROM_Z := 181.0
const PARKING_TO_Z := 215.0
const PARKING_INNER_X := 13.0
const PARKING_OUTER_X := 68.0
const PARKING_AXIS_HALF_W := 7.0
const ARRIVAL_AXIS_TO_Z := 219.0
const ARRIVAL_TRAM_CROSSING_Z := 174.0


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

## The first built piece of the Park Promenade: outside the plaza buildings,
## inside the themed lands, and connecting the spokes without making the hub the
## price of every move. The old safety wall at x 51.5 made the eleven-metre-deep
## perimeter blocks look like stage flats with a back lot behind them. Removing
## only the obsolete north-east runs reveals their real outer faces at x 47 and
## z -47; those become public fronts on a street rather than dressed backs.
##
## The east leg begins north of the protected cascade forecourt, turns on level
## ground around the dark ride and follows the north frontage to the Grove mouth.
## It does not move or support the east cascade, its terraces, the fountain climb
## or their terrain. The eventual junction at the east gate remains a protected
## design decision; this first segment simply arrives beside it.
const PROMENADE_EAST_FROM_X := 47.0
const PROMENADE_EAST_TO_X := 60.7
const PROMENADE_EAST_FROM_Z := -18.4
const PROMENADE_EAST_TURN_Z := -43.6
const PROMENADE_EAST_X := 53.8
const PROMENADE_WIDTH := 6.4
const PROMENADE_NORTH_Z := -50.0

## Ground under the north walk. It used to support only the half outside the old
## 104m plaza slab, which worked while the plaza stood and became a hole when the
## terraces section replaced it. The strip now carries the centreline and full
## public width itself; its inner half simply sits below the plaza floor when
## that section is mounted. Its west end stops on the east side of the NNW
## passage, whose own floor carries the Grove approach.
const PROMENADE_NORTH_GROUND_FROM_X := -8.7
const PROMENADE_NORTH_GROUND_TO_X := 60.7
const PROMENADE_NORTH_GROUND_FROM_Z := -46.8
const PROMENADE_NORTH_GROUND_TO_Z := -59.0
const PROMENADE_WATERWORKS_AT := Vector2(43.0, -56.0)


## The public centreline through the first segment. One broad ribbon handles the
## bend; a narrower final link passes south of the NNW mouth's east pier before
## turning into its opening. The pinch is architectural, not a routing accident.
const PROMENADE_NE_POINTS := [
	Vector2(PROMENADE_EAST_X, PROMENADE_EAST_FROM_Z),
	Vector2(PROMENADE_EAST_X, -39.2),
	Vector2(55.0, -46.0),
	Vector2(49.0, PROMENADE_NORTH_Z),
	Vector2(24.0, PROMENADE_NORTH_Z),
	Vector2(-4.0, PROMENADE_NORTH_Z),
]
const PROMENADE_NNW_LINK_POINTS := [
	Vector2(-4.0, PROMENADE_NORTH_Z),
	Vector2(-6.8, -48.6),
	Vector2(-16.9, -48.6),
]


static func promenade_ne_path() -> Array[Vector3]:
	var out: Array[Vector3] = []
	for p in PROMENADE_NE_POINTS:
		out.append(Vector3(p.x, 0.0, p.y))
	return out


static func promenade_nnw_link() -> Array[Vector3]:
	var out: Array[Vector3] = []
	for p in PROMENADE_NNW_LINK_POINTS:
		out.append(Vector3(p.x, 0.0, p.y))
	return out

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
## or to put them on the hill. They are on the hill. **The cost is that the `se`
## passage now has twelve metres to climb and nothing in it climbs yet**, which
## is real and is written down here rather than discovered later. The north-east
## passage no longer exists; `frontier` will branch from the upper terrace.
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
## 108.0 is derived, not chosen: `CLIMB_FROM_X` 78 plus 6 x 8 x `FLIGHT_GOING`
## (19.2) plus the sum of `CLIMB_TERRACE_DS` (10.8). It cannot be written as
## that expression because `CLIMB_TERRACE_DS` is declared below it; if any of
## the four inputs moves, re-derive this by hand — the exactness note at
## `CLIMB_FLIGHTS` is about precisely this number.
const CLIMB_TO_X := 108.0
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

## Six flights of eight risers, five landings between them — three pauses and
## two garden terraces. The sums are exact rather than nearly: 6 x 8 x
## `FLIGHT_GOING` (19.2) plus the sum of `CLIMB_TERRACE_DS` (10.8) is 30.0,
## which is `CLIMB_TO_X - CLIMB_FROM_X`; and 6 x 8 x `FLIGHT_RISE` is 12.0,
## which is `CLIMB_HEAD_Y - HILL_TOP`.
##
## They are exact because the landing depth was solved for after the flights were
## fixed, not chosen. If any of the four moves, re-derive the other three — a
## staircase that arrives half a riser under its own terrace is the kind of thing
## no screenshot shows and every ankle finds.
##
## **These numbers are measured off the reference photograph, and that is the
## whole 2026-08-22 story in one line.** The historic plate of the Cleveland
## Cascade — shown as the spec repeatedly before anyone measured against it —
## has the hillside rising about three times the head-house's height behind it,
## as a near-continuous ribbon whose landings are pauses rather than shelves.
## This climb rose exactly 1.0 times its own monument at 1:4, then 1:2.8, and
## no run compression could fix what was a *rise* deficit: from the court, the
## photograph's own standpoint, a 6m climb can never show over a 6m crest. So:
## twelve metres of rise — monument 6, climb 12, three heights stacked — at
## 1:2.1 overall with every landing a 1.2m pause.
##
## **The garden terraces came back the same day the rise proved itself.** All
## pauses was the plate's ribbon at its purest, and it cost the climb the
## terrace moments the east is named for — so the second and fourth landings
## widened to 3.6, at the one-third and two-thirds heights, and both pass
## `CLIMB_BAY_MIN_T` again: the walled courts stand off their flanks at y 10
## and y 14, with the crest terraces above and the belvedere below making it
## a room every three metres of rise. 1:2.5 overall now, which the 12m rise
## can afford: from the court the head still clears the crest's crop ray by
## half a metre, checked before the width went in.
##
## The rise above the belvedere is `CLIMB_HEAD_Y - HILL_TOP`, and `HILL_TOP`
## is still `CASCADE_DROP` reflected — the monument did not move. What grew is
## the hill behind it: the east's ground ramps from `TERRACE_TWO_Y` at the
## shoulder bench up to `CLIMB_HEAD_Y` at the head — see `east_ground_base` —
## so the climb stays a cut in rising land rather than a stair on a spur.
const CLIMB_FLIGHTS := 6
const CLIMB_FLIGHT_RISERS := 8
const CLIMB_TERRACE_DS := [1.2, 3.6, 1.2, 3.6, 1.2]
const CLIMB_HEAD_Y := 18.0
const CLIMB_RUN := CLIMB_TO_X - CLIMB_FROM_X
const CLIMB_RISE := CLIMB_HEAD_Y - HILL_TOP

## Where the east's ground starts rising off the shoulder bench toward the
## head. West of this the shelf is `TERRACE_TWO_Y` — the bench the shoulders'
## west face was derived against, which is why that face's arithmetic did not
## move when the hill grew.
const EAST_RAMP_FROM_X := 82.0


## The east hill's base level at a station: the bench, the ramp behind the
## scarp, and the head's own level. **In the plan because three files stand on
## it** — `gen_props` builds the ground and the ravine's banks off it,
## `gen_crowd` sets graph node heights on it, `walk_test` walks it — and the
## cafe-table rule is that anything two generators need is written down once.
static func east_ground_base(x: float) -> float:
	var t := clampf((x - EAST_RAMP_FROM_X) / (CLIMB_TO_X - EAST_RAMP_FROM_X),
		0.0, 1.0)
	t = t * t * (3.0 - 2.0 * t)
	return TERRACE_TWO_Y + (CLIMB_HEAD_Y - TERRACE_TWO_Y) * t

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
## Twelve basins over twelve metres is a full metre of fall each, one every
## 2.1m of run — 1:2.1, the whole feature's mean gradient and therefore the
## only slope on the hill that does not need a second number. The spacing is
## the one the eight-bowl chain proved at the shorter run; the count grew with
## the rise and the fall grew to a metre, which is the reference plate's own
## reading — a torrent of white lips stacked up the hill, and the falls are
## the one part of this feature that faces the plaza instead of receding.
##
## **The radius is direct-pour arithmetic, not a look.** Each bowl reads as a
## half-round because its uphill cap is buried in the pedestal carrying the
## bowl above — the plate's own construction — and the water leaves the lip at
## the bowl's downhill-most point, `BASIN_STEP - BASIN_R` uphill of the next
## bowl's centre. That point is only over the lower bowl's open water when
## `BASIN_R > BASIN_STEP / 2`; at the old 0.75 every lip stood a metre of dry
## plinth short of the next bowl and the water had to cross it as a chute. At
## 2.0 on the 2.5 spacing the lip overhangs the next bowl by a metre and a
## half, the fall lands in water a hand in front of the flat back, and the
## chain pours lip to bowl the whole way down, which is what the plate is a
## photograph of.
const BASIN_COUNT := 12
const BASIN_FALL := CLIMB_RISE / BASIN_COUNT
const BASIN_STEP := CLIMB_RUN / BASIN_COUNT
const BASIN_R := 2.0

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

## The two small courts at the crest of the climb. Their walls and dressing both
## need the same footprint, and the crowd needs destinations inside them rather
## than stopping at the centre line. Distances are off the cascade axis.
const CREST_COURT_X0 := 109.6
const CREST_COURT_X1 := 115.6
const CREST_COURT_FROM_D := 7.5
const CREST_COURT_TO_D := 12.6

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
## **One scalar since the terraces went unequal, and one bay per side with it.**
## Three graduated bays made sense on three 4.8m terraces; on 1.2m landings a
## bay of any depth is a slot, so only a terrace at least `CLIMB_BAY_MIN_T`
## deep carries one — which today is the two garden terraces. The narrow
## landings keep their banks unbroken instead, which is most of what
## un-cluttered the flanks: fewer cuts is fewer walls, fewer caps and fewer
## corners.
##
## 9.5 since 2026-08-23 — extended back into the greenery: at 6.5 a bay was a
## niche you stepped aside into, and the meadow behind its wall was most of
## five metres of hill nothing used. At 9.5 it is a garden court pushed into
## the hillside, back wall at 16.2 off the axis, with 1.8m of hill still
## standing between the wall and the blocks — inside the 11.3m budget above,
## and enough that the back reads as a cut face rather than a shell over
## `hill_north`/`hill_south`.
const CLIMB_BAY_D := 9.5
const CLIMB_BAY_MIN_T := 3.0

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
			var d: float = CLIMB_TERRACE_DS[i]
			out.append([x, x + d, y, y, false])
			x += d
	return out


## The walking surface at a station on the climb: flat across a terrace, on the
## nosing line up a flight.
static func climb_floor_y(x: float) -> float:
	for r in climb_reaches():
		if x <= float(r[1]) + 0.001:
			var t := clampf((x - float(r[0])) / maxf(float(r[1]) - float(r[0]), 0.001),
				0.0, 1.0)
			return lerpf(float(r[2]), float(r[3]), t)
	return CLIMB_HEAD_Y


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
## **Package 02A, 2026-09-03.** There is no separate rim any more. The swept
## ridge that stood outside the park from August was retired the same day it
## was re-planned: the crescent range surface in `park_groundworks` is the
## landform, and its first ridge is the foothill the rim used to be. One height
## function, one material, one description — these constants and the accessors
## below them. `footprint_test` checks the toe line against every route, the
## Grand Circuit, both parking fields and every program parcel by
## `RIM_CLEARANCE`; the atlas checks the same rule on the footprint map. The
## August rim arguments in `AGENTS.md` are history.
const RIM_CLEARANCE := 12.0

## The crescent about `RIM_RANGE_CENTRE`, open to the sea. Bearings are degrees
## from the centre, 0 due east, negative north, positive south. Full height
## from north round to the south-east; each arm lowers to nothing as it comes
## down to the coast, past the headland in the north-west and past the parking
## in the south-west. The inner edge is `RIM_RANGE_INNER_R` plus a swell on
## the north–south axis; the profile's first knot stands `RIM_RANGE_TOE_D`
## inside it, and that is the toe line the clearance rule is measured from.
const RIM_RANGE_CENTRE := Vector2(40.0, 0.0)
const RIM_RANGE_INNER_R := 290.0
## Seventy-five, not forty-five: the toe circle dips closer on the diagonals
## than a straight arm would, and at 45 it touched the Grand Circuit's
## north-west corner at (-61, -207) and came within 5m of the arrival road's
## end. Measured by `footprint_test`, not guessed.
const RIM_RANGE_INNER_SWELL := 75.0
const RIM_RANGE_FULL_FROM_DEG := -110.0
const RIM_RANGE_FULL_TO_DEG := 60.0
const RIM_RANGE_END_NORTH_DEG := -160.0
const RIM_RANGE_END_SOUTH_DEG := 120.0

## The range as (distance, height) knots from the inner edge, cosine-eased:
## toe, first ridge (the foothill), saddle, second ridge, dip, third ridge,
## dip, summit ridge, and higher ground beyond. Laguna Verde's "highest
## elevation 1,000 ft" is the summit. On the east the plateau hands over at
## its own 12m, so the foothill there stands 32; on the north it stands 20.
const RIM_RANGE_PROFILE := [
	[-100.0, 0.0], [-45.0, 20.0], [0.0, 10.0], [280.0, 120.0], [400.0, 95.0],
	[620.0, 200.0], [760.0, 175.0], [900.0, 330.0], [1300.0, 280.0],
	[2200.0, 360.0],
]
## The shape brief (02A, 2026-09-03). Three unequal summits set the summit
## line's height by bearing — the profile's far knots are scaled to it — and
## five spurs run down toward the park with valleys between them. Roughness is
## a seeded noise, deterministic across regeneration; a fixed seed is not the
## randomness the generator forbids.
const RIM_RANGE_SUMMIT_LINE := [
	[-160.0, 120.0], [-100.0, 260.0], [-60.0, 170.0], [-20.0, 330.0],
	[18.0, 190.0], [55.0, 240.0], [120.0, 150.0],
]
const RIM_RANGE_SUMMIT_REF := 330.0
const RIM_RANGE_SUMMITS := [
	{"name": "Saddleback", "bearing": -20.0, "dist": 1000.0, "height": 330.0},
	{"name": "The Lookout", "bearing": -100.0, "dist": 900.0, "height": 260.0},
	{"name": "Kiln Hill", "bearing": 55.0, "dist": 950.0, "height": 240.0},
]
const RIM_RANGE_SPURS := [-135.0, -70.0, -10.0, 40.0, 95.0]
const RIM_RANGE_SPUR_RELIEF := 0.35
const RIM_RANGE_NOISE_SEED := 2026
const RIM_RANGE_NOISE := [[400.0, 0.12], [120.0, 0.05]]

## The approach road (parking clause): down the +75° valley at no more than
## 1:12, curving into the front road at z 236 behind both parking fields.
## Since the highway (2026-09-04) the road ends at the trough junction where
## it meets the highway, rather than climbing on up the ridge flank.
const APPROACH_ROAD := [
	Vector2(204.0, 322.0), Vector2(190.0, 300.0),
	Vector2(130.0, 262.0), Vector2(80.0, 236.0),
]
const APPROACH_ROAD_W := 7.0
const APPROACH_ROAD_MAX_GRADE := 1.0 / 12.0
const FRONT_ROAD_Z := 236.0
const FRONT_ROAD_HALF_X := 80.0
const FRONT_ROAD_W := 7.0
const LOT_ENTRY_XS := [-60.0, -20.0, 20.0, 60.0]
const DROP_OFF := Rect2(4.0, 228.0, 20.0, 4.0)
const ARRIVAL_WALK_EXTEND_TO_Z := 228.0
const BERM_Z := Vector2(160.0, 170.0)
const BERM_X := Vector2(13.0, 80.0)
const BERM_HEIGHT := 2.5
const HEDGE_Z := 222.0
const TURNING_CIRCLE := Vector3(-80.0, 236.0, 10.0)

## The coast, modelled on Half Moon Bay (2026-09-03): a headland juts out at
## the north end of a crescent bay, a harbour cove sits in its lee, and the
## shore runs on south in one concave arc backed by hills. Here the cove bites
## in north of the Boardwalk between the wooden coaster and the lighthouse's
## headland, the promontory runs west from that headland's root to a cliffed
## point, and the south shore is the rest of the crescent. The working shore
## either side of the Boardwalk, z ±70, is protected as built. Both outlines
## run from the working shore outward and are the one description the coast
## meshes, the range's shore fade and the toe line all read.
##
## **Reshaped on 2026-09-04, because the first outlines were a V.** Both arms
## ran out to sea south-west and north-west at about sixteen degrees, so the
## park stood at the tip of a cape and the promontory was a tab on it; Half
## Moon Bay is the opposite figure — a coast trending north-west to south-east
## with Pillar Point standing out of it and the harbour in the point's lee.
## So the coast north of the point now recedes north-north-west and stays
## east of the point's x for four hundred metres, which is what lets the
## promontory lead the coast rather than run parallel to it; and the south
## shore holds x about −125 past the parking's front road, then sweeps
## south-east across the mainland reserve's west edge and on to (700, 2200),
## so from the pier the bay's far side recedes into the hills. The south
## outline crossing `SHORE_FROM_X` is what makes the reserve carry a shore
## (`coast_south_crossing_z`), and the sea under that corner is
## `BAY_WATER_*`. Nothing in the developed envelope moved: the shore is 34m
## from the front road's turning circle and the bluff south of the parking
## keeps its cove.
const COAST_NORTH_OUTLINE := [
	Vector2(-108.0, -70.0), Vector2(-112.0, -130.0), Vector2(-108.0, -165.0),
	Vector2(-100.0, -185.0), Vector2(-80.0, -205.0), Vector2(-72.0, -218.0),
	Vector2(-90.0, -232.0), Vector2(-130.0, -240.0), Vector2(-170.0, -246.0),
	Vector2(-205.0, -252.0), Vector2(-218.0, -262.0), Vector2(-205.0, -280.0),
	Vector2(-170.0, -290.0), Vector2(-140.0, -296.0), Vector2(-132.0, -330.0),
	Vector2(-128.0, -400.0), Vector2(-140.0, -520.0), Vector2(-180.0, -700.0),
	Vector2(-270.0, -1000.0), Vector2(-420.0, -1500.0), Vector2(-600.0, -2200.0),
]
const COAST_SOUTH_OUTLINE := [
	Vector2(-108.0, 70.0), Vector2(-116.0, 140.0), Vector2(-124.0, 210.0),
	Vector2(-126.0, 270.0), Vector2(-118.0, 340.0), Vector2(-100.0, 410.0),
	Vector2(-72.0, 490.0), Vector2(-36.0, 580.0), Vector2(10.0, 680.0),
	Vector2(70.0, 800.0), Vector2(140.0, 950.0), Vector2(230.0, 1150.0),
	Vector2(340.0, 1400.0), Vector2(500.0, 1750.0), Vector2(700.0, 2200.0),
]
## The sea under the bay's far shore, where the south outline has crossed the
## mainland reserve's west edge: a second sheet from the ocean's east edge out
## to past the outline's eastmost point, rather than a wider ocean, so that no
## hole in the developed ground north of it can show water through it. It
## starts well north of the crossing and is under land there.
const BAY_WATER_FROM_Z := 300.0
const BAY_WATER_TO_X := 800.0

## The coast highway (package 02B, 2026-09-04): the Pacific Coast Highway
## equivalent, and the road the character drives to work. The park fills the
## shelf from the water to the range's toe, so a through road cannot pass it
## along the shore; it goes behind the first ridge instead, in the trough the
## range profile leaves at its inner edge — a level saddle about ten metres up
## with almost no spur relief, all the way round the crescent. **The first
## alignment looped the second ridge's dip valley 770m out and was rejected
## by the generator the same day**: the spurs stand sixty to ninety metres
## over the valleys between them right down to the foothill, so that loop
## was seven tunnels totalling 2.7km, and the road could not climb the second
## ridge at 1:12 fast enough to top it, so the crest turnout was buried.
##
## In drive order, north to south: down the north coast on the range's
## shore-fade face about 90m inland, forty to ninety metres up, forest above
## and the sea below through the trees; an oblique descent to 45m inland
## round the arm's foot, where the bay and the park open beneath the road;
## behind the headland into the trough; round the trough behind the park,
## hidden by the foothill; the junction at the foothill's back where the
## park's road, the built approach road, leaves it; on round behind the
## parking; then out to the bay's far shore at 60m inland and on south-east.
## This is the plan in XZ only. Heights come from the terrain in the
## generator, held to `HIGHWAY_MAX_GRADE` by lowering, so the road is on the
## surface where the ground allows it and in a cutting where it does not; a
## stretch buried deeper than `HIGHWAY_TUNNEL_COVER` for longer than
## `HIGHWAY_TUNNEL_MIN_LEN` is a tunnel. Every number here is a target the
## reveal frames judge.
const HIGHWAY_W := 8.0
const HIGHWAY_MAX_GRADE := 1.0 / 12.0
const HIGHWAY_STATION := 20.0
const HIGHWAY_TUNNEL_COVER := 9.0
const HIGHWAY_TUNNEL_MIN_LEN := 40.0
## The trough: this far outside the range's inner edge, on every bearing.
const HIGHWAY_TROUGH_D := 5.0
## Where the wide view opens on the descent, and where the park's road leaves.
const HIGHWAY_VIEW := Vector2(-118.0, -640.0)
const HIGHWAY_JUNCTION := Vector2(204.0, 322.0)
## Forest clearings on the road: the view bend, seaward, and two glimpse
## bends on the high coast. [centre, radius].
const HIGHWAY_CLEARINGS := [
	[Vector2(-150.0, -620.0), 45.0],
	[Vector2(-235.0, -1050.0), 28.0],
	[Vector2(-360.0, -1400.0), 28.0],
]


## The highway's plan line, north to south.
static func highway_path() -> Array[Vector2]:
	var pts: Array[Vector2] = []
	# The north coast: 60m inland on the mountain face, which the shore fade
	# puts thirty to fifty metres up — at 90m inland it was over a hundred
	# and the road was a 512m tunnel — easing to 45m inland by the headland's
	# back so the road comes down round the arm's foot at about 1:12.
	for q in [Vector2(-480.0, -2000.0), Vector2(-420.0, -1700.0),
			Vector2(-330.0, -1400.0), Vector2(-270.0, -1200.0),
			Vector2(-210.0, -1000.0), Vector2(-170.0, -900.0),
			Vector2(-152.0, -800.0), Vector2(-135.0, -700.0),
			Vector2(-115.0, -600.0), Vector2(-95.0, -520.0),
			Vector2(-85.0, -450.0)]:
		pts.append(q)
	# Round the crescent in the trough behind the first ridge, from the
	# headland's back to the parking's, and on to where the far shore begins.
	var theta := -110.0
	while theta <= 95.0 + 0.001:
		var r := range_inner(theta) + HIGHWAY_TROUGH_D
		pts.append(RIM_RANGE_CENTRE + Vector2(cos(deg_to_rad(theta)),
			sin(deg_to_rad(theta))) * r)
		theta += 5.0
	# Out to the bay's far shore, 60m inland, and on south-east.
	for q in [Vector2(0.0, 520.0), Vector2(60.0, 640.0), Vector2(115.0, 760.0),
			Vector2(200.0, 950.0), Vector2(290.0, 1150.0), Vector2(400.0, 1400.0),
			Vector2(560.0, 1750.0), Vector2(670.0, 2000.0), Vector2(740.0, 2150.0),
			Vector2(820.0, 2350.0)]:
		pts.append(q)
	return pts
## The promontory is the land the north outline draws between the cove head
## and the point, and `PROMONTORY_SPINE` runs up the middle of that land from
## the headland pad to the point. It was one segment, (-44,-212) to
## (-200,-262), which is the cove-side shoreline to within a few metres: the
## walk, the forecourt and the keeper's exhibit were all laid on the cliff
## edge with their seaward halves over the skirt (2026-09-04, from play).
## The height climbs along the spine from the pad's level, held flat under
## the pad's own polygon, to `PROMONTORY_HEIGHT` at the point. Across the
## land the crown is set by `coast_inland`, distance to the shoreline, and
## not by distance to the spine: full height `PROMONTORY_EDGE_RUN` inland,
## easing to `PROMONTORY_EDGE_FRACTION` of it at the cliff edge, so the top
## is a table the walk can use and the sea-cliff skirt makes the cliff.
## `PROMONTORY_HALF_W` only bounds the feature on the mainland side.
const PROMONTORY_SPINE := [
	# The turn west is five bends of under thirty degrees: `along` is measured
	# to the nearest segment, so on the inside of a sharp corner it jumps by
	# the corner's own depth and the height field folds a step there, which
	# buried the walk's edge a third of a metre. The turn also crosses the
	# coast mesh's inland seam at x -56 near z -252, where the coast base has
	# all but closed on the reserve's; crossing at z -246 it stepped half a
	# metre.
	Vector2(-37.0, -172.0), Vector2(-50.0, -234.0), Vector2(-53.0, -244.0),
	Vector2(-57.0, -252.0), Vector2(-64.0, -257.0), Vector2(-74.0, -258.5),
	Vector2(-100.0, -258.0), Vector2(-150.0, -268.0), Vector2(-218.0, -262.0),
]
const PROMONTORY_ROOT_Y := 4.0
const PROMONTORY_HEIGHT := 22.0
const PROMONTORY_HALF_W := 34.0
## The climb waits until the spine is clear of the T3 pad's outer polygon and
## finishes short of the tip, so the point itself is level.
const PROMONTORY_CLIMB_FROM := 45.0
const PROMONTORY_CLIMB_TAIL := 30.0
const PROMONTORY_EDGE_RUN := 14.0
const PROMONTORY_EDGE_FRACTION := 0.6
## The walk's centreline, the forecourt and the exhibit stand at least this
## far inland of the shoreline; `footprint_test` measures it.
const PROMONTORY_SHORE_CLEARANCE := 8.0
## Cliffed coast with coves north of the point, a bluff with one cove south
## of the parking. Nothing above 10m in the sunset sector from the pier head.
const NORTH_CLIFF_Z := Vector2(-420.0, -300.0)
const NORTH_CLIFF_HEIGHT := 20.0
const NORTH_COVES := [-340.0, -390.0]
const SOUTH_BLUFF_Z := Vector2(240.0, 300.0)
const SOUTH_BLUFF_HEIGHT := 20.0
const SOUTH_BLUFF_TO_X := -100.0
const SOUTH_COVE_Z := 270.0
const COVE_HALF_W := 25.0
const RIM_RANGE_TOE_D := -100.0
## Ground colour bands on the range, by rise above the meadow and by height:
## forest once the ground has risen this much, bare rock above the treeline.
const RIM_RANGE_FOREST_RISE := 15.0
const RIM_RANGE_TREELINE_Y := 260.0


## How much of the range stands on a bearing: all of it from north round to
## the south-east, lowering to nothing where each arm reaches the sea.
static func range_weight(theta_deg: float) -> float:
	if theta_deg >= RIM_RANGE_FULL_FROM_DEG and theta_deg <= RIM_RANGE_FULL_TO_DEG:
		return 1.0
	var t := 0.0
	if theta_deg < RIM_RANGE_FULL_FROM_DEG:
		t = (theta_deg - RIM_RANGE_END_NORTH_DEG) \
			/ (RIM_RANGE_FULL_FROM_DEG - RIM_RANGE_END_NORTH_DEG)
	else:
		t = (RIM_RANGE_END_SOUTH_DEG - theta_deg) \
			/ (RIM_RANGE_END_SOUTH_DEG - RIM_RANGE_FULL_TO_DEG)
	t = clampf(t, 0.0, 1.0)
	return t * t * (3.0 - 2.0 * t)


## The crescent's inner edge on a bearing: the profile's zero.
static func range_inner(theta_deg: float) -> float:
	return RIM_RANGE_INNER_R + RIM_RANGE_INNER_SWELL * absf(sin(deg_to_rad(theta_deg)))


## The profile's height at a distance from the inner edge, before weighting.
static func range_profile_y(d: float) -> float:
	var knots: Array = RIM_RANGE_PROFILE
	if d <= float(knots[0][0]):
		return 0.0
	for i in range(1, knots.size()):
		if d <= float(knots[i][0]):
			var t := (d - float(knots[i - 1][0])) \
				/ (float(knots[i][0]) - float(knots[i - 1][0]))
			t = 0.5 - 0.5 * cos(t * PI)
			return lerpf(float(knots[i - 1][1]), float(knots[i][1]), t)
	return float(knots[knots.size() - 1][1])


## Where the south outline first reaches `xc` heading east — the far shore of
## the bay recedes inland as it runs south, so past this z the land east of
## the outline belongs to the mainland reserve rather than the coast mesh.
## INF if it never gets there.
static func coast_south_crossing_z(xc: float) -> float:
	var outline: Array = COAST_SOUTH_OUTLINE
	for i in outline.size() - 1:
		var a: Vector2 = outline[i]
		var b: Vector2 = outline[i + 1]
		if a.x < xc and b.x >= xc:
			return lerpf(a.y, b.y, (xc - a.x) / (b.x - a.x))
	return INF


## Distance from a point on land to the sea: the nearest segment of the coast
## outline on that side of the working strip, or the strip's own shore edge.
## The promontory's crown and the P1 shore-clearance check both read it.
static func coast_inland(p: Vector2) -> float:
	var best := INF
	if absf(p.y) <= 70.0:
		best = p.x - SHORE_EDGE
	var outline: Array = COAST_NORTH_OUTLINE if p.y < 0.0 else COAST_SOUTH_OUTLINE
	for i in outline.size() - 1:
		var q := Geometry2D.get_closest_point_to_segment(p, outline[i], outline[i + 1])
		best = minf(best, p.distance_to(q))
	return best


## Where a point stands relative to the promontory's spine: x is the arc
## length along the spine to the nearest point on it, y the distance across
## to that point. Before the root the along is zero and the across grows.
static func promontory_station(p: Vector2) -> Vector2:
	var best_across := INF
	var best_along := 0.0
	var run := 0.0
	for i in PROMONTORY_SPINE.size() - 1:
		var a: Vector2 = PROMONTORY_SPINE[i]
		var b: Vector2 = PROMONTORY_SPINE[i + 1]
		var q := Geometry2D.get_closest_point_to_segment(p, a, b)
		var d := p.distance_to(q)
		if d < best_across:
			best_across = d
			best_along = run + a.distance_to(q)
		run += a.distance_to(b)
	return Vector2(best_along, best_across)


static func promontory_length() -> float:
	var run := 0.0
	for i in PROMONTORY_SPINE.size() - 1:
		run += (PROMONTORY_SPINE[i] as Vector2).distance_to(PROMONTORY_SPINE[i + 1])
	return run


## The promontory's own height at a point, before the coast base and the
## range are added: zero off the feature. One description for the coast
## meshes, the mainland reserve's root and every site placed on it.
static func promontory_y(p: Vector2) -> float:
	var st := promontory_station(p)
	var along := st.x
	var across := st.y
	if across >= PROMONTORY_HALF_W:
		return 0.0
	var length := promontory_length()
	if along > length + 30.0:
		return 0.0
	var climb := clampf((along - PROMONTORY_CLIMB_FROM) /
		(length - PROMONTORY_CLIMB_TAIL - PROMONTORY_CLIMB_FROM), 0.0, 1.0)
	climb = climb * climb * (3.0 - 2.0 * climb)
	var h := lerpf(PROMONTORY_ROOT_Y, PROMONTORY_HEIGHT, climb)
	var edge := clampf(coast_inland(p) / PROMONTORY_EDGE_RUN, 0.0, 1.0)
	edge = edge * edge * (3.0 - 2.0 * edge)
	var crown := lerpf(PROMONTORY_EDGE_FRACTION, 1.0, edge)
	var side := clampf((across - (PROMONTORY_HALF_W - 10.0)) / 10.0, 0.0, 1.0)
	side = 1.0 - side * side * (3.0 - 2.0 * side)
	return h * crown * side


## Where the sea is at a given z: the westmost point of the coast outline on
## that line, so a cove behind a point does not count as the shore for the
## range's fade or the toe line. Inside the working strip it is `SHORE_EDGE`.
static func shore_x(z: float) -> float:
	if absf(z) <= 70.0:
		return SHORE_EDGE
	var outline: Array = COAST_NORTH_OUTLINE if z < 0.0 else COAST_SOUTH_OUTLINE
	var best := INF
	for i in outline.size() - 1:
		var a: Vector2 = outline[i]
		var b: Vector2 = outline[i + 1]
		if (z - a.y) * (z - b.y) > 0.0:
			continue
		var t := (z - a.y) / (b.y - a.y) if absf(b.y - a.y) > 0.001 else 0.0
		best = minf(best, lerpf(a.x, b.x, t))
	if best == INF:
		var last: Vector2 = outline[outline.size() - 1]
		return last.x
	return best


## The summit line's height on a bearing, cosine-eased between the brief's
## knots; the profile's far knots are scaled by this over RIM_RANGE_SUMMIT_REF.
static func range_summit_line(theta_deg: float) -> float:
	var knots: Array = RIM_RANGE_SUMMIT_LINE
	if theta_deg <= float(knots[0][0]):
		return float(knots[0][1])
	for i in range(1, knots.size()):
		if theta_deg <= float(knots[i][0]):
			var t := (theta_deg - float(knots[i - 1][0])) \
				/ (float(knots[i][0]) - float(knots[i - 1][0]))
			t = 0.5 - 0.5 * cos(t * PI)
			return lerpf(float(knots[i - 1][1]), float(knots[i][1]), t)
	return float(knots[knots.size() - 1][1])


## One on a spur's crest, zero in the valley between two spurs, cosine-shaped
## across each spur's half of the gap to its neighbour.
static func range_spur(theta_deg: float) -> float:
	var spurs: Array = RIM_RANGE_SPURS
	var best := 0.0
	for i in spurs.size():
		var sdeg := float(spurs[i])
		var left := float(spurs[i - 1]) if i > 0 else sdeg - 50.0
		var right := float(spurs[i + 1]) if i + 1 < spurs.size() else sdeg + 50.0
		var half := (sdeg - left) * 0.5 if theta_deg < sdeg else (right - sdeg) * 0.5
		var u := absf(theta_deg - sdeg) / maxf(half, 1.0)
		if u < 1.0:
			var c := cos(u * PI * 0.5)
			best = maxf(best, c * c)
	return best


## The approach road's height by chainage from the front road, at the
## brief's grade, and its 3D line.
static func approach_road_points() -> Array[Vector3]:
	var pts: Array[Vector3] = []
	var order: Array = APPROACH_ROAD.duplicate()
	order.reverse()
	var chain := 0.0
	for i in order.size():
		if i > 0:
			chain += (order[i] as Vector2).distance_to(order[i - 1])
		pts.append(Vector3(order[i].x, chain * APPROACH_ROAD_MAX_GRADE, order[i].y))
	return pts


## The toe line in plan: where the range begins to rise, on every bearing that
## carries at least `min_weight` of it and on land — a toe out past the shore
## is water, and the range fades to nothing there anyway. This is the line the
## clearance rule is measured from.
static func range_toe_line(step_deg := 2.0, min_weight := 0.1) -> Array[Vector2]:
	var out: Array[Vector2] = []
	var theta := RIM_RANGE_END_NORTH_DEG
	while theta <= RIM_RANGE_END_SOUTH_DEG + 0.001:
		# Below `min_weight` the arm is under two metres high and its toe is
		# not a landform anybody has to keep clear of.
		if range_weight(theta) >= min_weight:
			var r := range_inner(theta) + RIM_RANGE_TOE_D
			var p := RIM_RANGE_CENTRE + Vector2(cos(deg_to_rad(theta)),
				sin(deg_to_rad(theta))) * r
			if p.x >= shore_x(p.y):
				out.append(p)
		theta += step_deg
	return out


# ---------------------------------------------------------------------------
# The east gap, and the gate in it
# ---------------------------------------------------------------------------

## The due-east way made seven; retiring the north-east threshold brings the
## plaza back to six without giving up this axis.
##
## It is on the fountain's own east–west line, which is the whole reason for
## cutting a new one rather than using the `se` threshold already there. That
## sits at 121°; a cascade behind it is a cascade you come across, and a cascade
## due east of the fountain is the west one's answer. The plaza reads as a notch
## between two of them.
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

## The two small seating groves in the court below the east cascade. These are
## in the plan because the props generator builds them and the crowd generator
## has to route around the same footprints. Distances are off the gate/cascade
## axis, so the whole arrangement follows that line if the east ever moves.
##
## One tree anchors each grove at its outer edge. The first arrangement stepped
## freestanding benches and directory boards inward from it, directly into the
## desire line from the gate to the north promenade. Seating now stays with the
## grove beyond the public edge, while route information is mounted on the
## attraction wall and has no ground footprint at all.
const EAST_ARRIVAL_TREE_XS := [59.0]
const EAST_ARRIVAL_TREE_D := 13.0
const EAST_ARRIVAL_BENCH_X := 58.9
const EAST_ARRIVAL_BENCH_D := 9.8
const EAST_ARRIVAL_BOARD_X := 47.25
const EAST_ARRIVAL_BOARD_D := 16.5

## The furniture on the six-metre belvedere between the two east climbs. The
## viewer sits close to the west parapet, the bench behind it and farther out,
## and the lamp against the back corner. This keeps the pool-side routes at
## `climb_flight_z()` open while making both broad side strips into overlooks.
const EAST_BELVEDERE_VIEWER_X := 71.35
const EAST_BELVEDERE_VIEWER_D := 9.4
const EAST_BELVEDERE_BENCH_X := 74.2
const EAST_BELVEDERE_BENCH_D := 13.2
const EAST_BELVEDERE_LAMP_X := 76.2
const EAST_BELVEDERE_LAMP_D := 15.3

## The two attraction courts beyond the crest gardens. They share a promenade
## and a footprint, but not a ride: the north court takes the taller swing ride
## that announces the frontier side, while the south stays low for kiddieland.
##
## The shoulder is rolling ground, not a level slab. The promenade therefore
## rises from the head landing's 18m floor to a 20m ride court over its first
## eight metres. Props, crowd nodes and walk probes all read the same profile so
## nobody is posed under the meadow or sent through a retaining bank.
const EAST_END_PATH_X := 108.4
const EAST_END_PATH_HALF_W := 1.8
const EAST_END_PATH_FROM_D := 22.2
const EAST_END_PATH_RISE_TO_D := 30.0
const EAST_END_PATH_TO_D := 60.0
const EAST_END_FLOOR_Y := 20.0
const EAST_END_RIDE_X := 114.0
const EAST_END_RIDE_D := 52.0
const EAST_END_RIDE_PAD_R := 5.4
const EAST_END_QUEUE_X := 105.6
const EAST_END_QUEUE_HALF := Vector2(2.4, 5.5)
const EAST_END_GRADE_RUN := 3.0


static func east_end_path_y(dist: float) -> float:
	var t := clampf((dist - EAST_END_PATH_FROM_D) /
		(EAST_END_PATH_RISE_TO_D - EAST_END_PATH_FROM_D), 0.0, 1.0)
	t = t * t * (3.0 - 2.0 * t)
	return lerpf(CLIMB_HEAD_Y, EAST_END_FLOOR_Y, t)


## From the central head landing, round the west side of a crest court and out
## to the ride gate. `side` is -1 north and +1 south.
static func east_end_path(side: float) -> Array[Vector3]:
	var axis: float = ARCH_AT.y
	var ds := [6.0, 16.0, EAST_END_PATH_FROM_D, EAST_END_PATH_RISE_TO_D,
		42.0, EAST_END_RIDE_D]
	var out: Array[Vector3] = []
	for d in ds:
		out.append(Vector3(EAST_END_PATH_X, east_end_path_y(float(d)),
			axis + side * float(d)))
	return out


## The observation tower's real site, beyond the north ride court and before
## the shoulder rolls down. Its old skyline-only origin was `(54, 0, -40)`: at
## the foot of the hill beside the north-east threshold, with no path, no base
## and no collision. `(104, 20, -84)` is almost exactly the same ray from the
## fountain, so the landmark keeps its place in the plaza composition while its
## footing moves onto the highest public ground in the east. Its x position is
## eight metres west of the climb's head, enough that its mast and the chair
## swing's mast do not merge into one object from the central landing.
##
## The approach forks west before the swing queue, passes its booth on the
## outside, then bends back to the tower gate. That bend is not dressing. A
## straight continuation of `EAST_END_PATH_X` runs through the swing's gate
## post, so props, crowd and walk tests all read this one route.
const EAST_TOWER_X := 104.0
const EAST_TOWER_D := 82.0
const EAST_TOWER_FLOOR_Y := EAST_END_FLOOR_Y
const EAST_TOWER_PAD_R := 7.0
const EAST_TOWER_BASE_R := 2.65
const EAST_TOWER_GRADE_RUN := 3.5

## The tower is a destination beside this route, not the route's terminus.
## Guests fork before its gate, skirt the outside of the fenced court and arrive
## at the first built piece of Frontier. **The route and street stand on the
## north shoulder now, not on a guest trestle.** The first build held this same
## 18.5m datum above the shoulder on timber piers, postponing the difference
## between the tower's 20m court and Frontier's old 12m footprint until somewhere
## behind a closure. It solved one approach and made the land look detached from
## the park carrying it.
##
## Frontier begins on the high contour instead. The ground is graded to this
## route and the whole future land spends its length descending toward the grove;
## no short threshold structure is asked to swallow that descent. Timber trestle
## is reserved for the mine train, where it says what it is. The built route
## still loses only 1.5m over roughly 27m, and the unbuilt continuation begins
## beyond the western closure on the street's own axis.
const EAST_FRONTIER_PATH_W := 4.6
const EAST_FRONTIER_FLOOR_Y := 18.5
const EAST_FRONTIER_PATH_GRADE_RUN := 7.5
const EAST_FRONTIER_STREET_GRADE_RUN := 9.0
const EAST_FRONTIER_STREET_FROM_X := 73.0
const EAST_FRONTIER_STREET_TO_X := 94.0
const EAST_FRONTIER_STREET_Z := -93.0
const EAST_FRONTIER_STREET_HALF_Z := 4.0
const EAST_FRONTIER_CLOSURE_X := 73.8
const EAST_FRONTIER_FRONT_Z := -97.05

## Two shallow tenants facing the street. Widths and centres are plan data
## because the crowd routes to their fronts and treats the bodies as obstacles.
const EAST_FRONTIER_BUILDINGS := [
	{"tag": "games", "x0": 74.8, "x1": 82.4, "h": 6.1},
	{"tag": "food", "x0": 83.6, "x1": 92.2, "h": 5.3},
]

## The park's north-rim sky ride, from the high Frontier shoulder to the future
## Grove. It is deliberately not a chord through the hub. Both terminals and
## the whole line stay around z = -100, so the fountain and the two cascade axes
## remain free of cables and towers; from the plaza the clock hides the middle
## of the line while cabins appear on either side of it.
##
## The two stations speak their districts and the line speaks for the whole
## park. Frontier gets a timber depot on the same high contour as its street;
## Grove gets a green-roofed picnic pavilion on the low ground. Red, yellow and
## blue open buckets travel between them as a shared classic-park attraction.
## The ride is static at this milestone, like every ride except the crowd.
const SKY_RIDE_FRONTIER_AT := Vector3(108.0, EAST_END_FLOOR_Y, -97.5)
const SKY_RIDE_GROVE_AT := Vector3(-18.0, 0.0, -104.0)
const SKY_RIDE_FRONTIER_CABLE_Y := 27.4
const SKY_RIDE_GROVE_CABLE_Y := 8.1
const SKY_RIDE_LANE_HALF := 1.65
const SKY_RIDE_ACCESS_W := 4.2
const SKY_RIDE_ACCESS_GRADE_RUN := 5.5
const SKY_RIDE_STATION_GRADE_RUN := 6.0

## Intermediate supports only where a themed section can explain their feet.
## The long middle span crosses the unbuilt transition without putting another
## isolated structure in the void between Frontier and Grove.
const SKY_RIDE_TOWERS := [
	{"t": 0.82, "ground_y": 0.0, "cable_y": 12.2},
]


static func east_tower_center() -> Vector3:
	return Vector3(EAST_TOWER_X, EAST_TOWER_FLOOR_Y, ARCH_AT.y - EAST_TOWER_D)


## Centreline from the existing north promenade to the tower court. The first
## point is shared with `east_end_path(-1)[4]`; consumers adding graph nodes skip
## it so the fork does not become a zero-length edge.
static func east_tower_path() -> Array[Vector3]:
	var axis: float = ARCH_AT.y
	return [
		Vector3(EAST_END_PATH_X, EAST_TOWER_FLOOR_Y, axis - 42.0),
		Vector3(101.3, EAST_TOWER_FLOOR_Y, axis - 46.0),
		Vector3(101.3, EAST_TOWER_FLOOR_Y, axis - 62.0),
		Vector3(103.2, EAST_TOWER_FLOOR_Y, axis - 68.0),
		Vector3(106.0, EAST_TOWER_FLOOR_Y, axis - 72.0),
		Vector3(107.6, EAST_TOWER_FLOOR_Y, axis - 76.0),
	]


## The through-route branches at the penultimate tower-path point. Starting at
## the tower gate would send the first segment back through the fenced circle;
## this point is ten metres from the mast, so a 4.6m path keeps its whole width
## outside the rail. The descent is a steady 1.5m over roughly 27m.
static func east_frontier_path() -> Array[Vector3]:
	var axis: float = ARCH_AT.y
	return [
		Vector3(106.0, EAST_TOWER_FLOOR_Y, axis - 72.0),
		Vector3(99.0, 19.72, axis - 72.3),
		Vector3(94.2, 19.32, axis - 76.4),
		Vector3(93.3, 18.92, axis - 84.0),
		Vector3(94.0, 18.68, axis - 88.0),
		Vector3(EAST_FRONTIER_STREET_TO_X, EAST_FRONTIER_FLOOR_Y,
			EAST_FRONTIER_STREET_Z),
	]


## A short branch from Frontier's arrival mouth to the sky-ride depot. It stays
## on the shoulder and passes north of the observation-tower court; the final
## point is outside the station gate rather than under the cable machinery.
static func sky_ride_access_path() -> Array[Vector3]:
	return [
		Vector3(EAST_FRONTIER_STREET_TO_X, EAST_FRONTIER_FLOOR_Y,
			EAST_FRONTIER_STREET_Z),
		Vector3(98.6, 18.85, -92.8),
		Vector3(103.2, 19.40, -92.6),
		Vector3(107.8, EAST_END_FLOOR_Y, -92.8),
	]


static func sky_ride_plan_at(t: float) -> Vector2:
	return Vector2(SKY_RIDE_FRONTIER_AT.x, SKY_RIDE_FRONTIER_AT.z).lerp(
		Vector2(SKY_RIDE_GROVE_AT.x, SKY_RIDE_GROVE_AT.z), t)


## Outward from the tower centre toward the promenade gate, in plan.
static func east_tower_gate_dir() -> Vector2:
	var gate: Vector3 = east_tower_path()[-1]
	var center := east_tower_center()
	return Vector2(gate.x - center.x, gate.z - center.z).normalized()


## A point on the tower court in the gate's own frame: `radial` is outward
## toward the approach and `lateral` is across it. The operator booth, bench and
## crowd obstacles use this so they cannot drift apart when the gate turns.
static func east_tower_point(radial: float, lateral: float) -> Vector3:
	var center := east_tower_center()
	var gate := east_tower_gate_dir()
	var tangent := Vector2(-gate.y, gate.x)
	var p := Vector2(center.x, center.z) + gate * radial + tangent * lateral
	return Vector3(p.x, EAST_TOWER_FLOOR_Y, p.y)


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
## The atlas puts R2's first public queue point at (-94,-55). The old station
## remained seventeen metres south at z=-38 after the outer map expanded,
## occupying I3's exact café parcel. Move the whole canonical ride—not I3—to
## its approved northern address; this also uses the reserve added for R2.
const COASTER_STATION := Vector2(-94.0, -55.0)
const COASTER_HEADING := 0.0
const COASTER_FROM_Z := COASTER_STATION.y - 2.0
const COASTER_TO_Z := COASTER_FROM_Z - 98.0

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
	# Route B's south return crosses the frontage between z 55 and 68. This is a
	# real gateway now, not a path drawn through the shuttered and taffy units
	# that occupied the same thirteen metres. Their eventual replacements belong
	# in the approved MW-B frontage band, outside the through-route.
]

## Package 04F/G replaces the legacy Boardwalk row everywhere it overlaps the
## approved recurring-interior, midway and funhouse parcels. Keep the names in
## one shared set so the world generator, distant tableau and crowd avoidance
## cannot disagree about which old shells still exist. `restrooms` is the only
## surviving unit: it stands south of P2 and north of B's return opening.
const REBUILD_RETIRED_BOARDWALK_SHOPS := {
	&"arcade": true,
	&"gallery": true,
	&"corndogs": true,
	&"custard": true,
	&"studio": true,
	&"funhouse": true,
	&"games": true,
}

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
## **Nothing public here may go west of `BLUFF_BACK_X`.** The bluff runs the
## whole west edge of the park, z -170 to +170, and the ground past its west face
## is the boardwalk's, six metres down. That is why the south-west section is a
## narrow strip rather than the square the other three are: there is nowhere for
## it to widen into. The old x -38 limit predated the bluff's move to -58 and
## contradicted both the threshold at -43.5 and the footprint below.
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
	# Pushed out along their own bearings by the 12m the wall line moved. Grove,
	# kiddieland and fairground still sit beyond their thresholds; frontier starts
	# at the north shoulder and will be entered from the upper east promenade.
	# These are footprints for silhouette and none of them is built.
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
	&"fairground": {"at": Vector2(-38.0, 91.0), "size": Vector2(26.0, 76.0), "floor_y": 0.0},
}

## Which way out leads where. The keys are the threshold names in `THRESHOLDS`
## plus the two that are not thresholds — the west arch, whose seam is really the
## gate at the foot of the stair, and the street south to the gate, which leads
## out of the park rather than into a section.
const SPOKE_LEADS_TO := {
	&"west": &"boardwalk",
	&"east": &"terraces",
	&"nnw": &"grove",
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
## **The scaffolded thresholds used to be nameless, and now their sections are
## not.**
## The rule was that naming a section ahead of its design is inventing park
## content, and it held while nothing needed the park to read as a whole. Massing
## the park to its edges needs exactly that, so `SECTION_GROUND` above names all
## six and this table points the passages at them.
##
## What survives of the rule: `built` is still false for all three, the passages
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
	{"id": &"dark_ride", "at": PLAZA_DARK_RIDE_AT, "section": &"plaza", "built": true},

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
	{"id": &"way_se", "at": Vector2(39.5, 24.0), "section": &"kiddieland", "built": false},
	{"id": &"way_sw", "at": Vector2(-24.0, 39.5), "section": &"fairground", "built": false},

	{"id": &"grove", "at": SECTION_GROUND[&"grove"]["at"], "section": &"grove", "built": false},
	{"id": &"frontier", "at": SECTION_GROUND[&"frontier"]["at"], "section": &"frontier", "built": false},
	{"id": &"kiddieland", "at": SECTION_GROUND[&"kiddieland"]["at"], "section": &"kiddieland", "built": false},
	{"id": &"fairground", "at": SECTION_GROUND[&"fairground"]["at"], "section": &"fairground", "built": false},
]


# ---------------------------------------------------------------------------
# Park rebuild atlas
# ---------------------------------------------------------------------------

## The approved DEVELOPED PARK envelope. The central 104m plaza and both
## protected monuments are fixed; only coordinates outside the core are
## remapped. These four extents locate the paths, rides and buildings; they are
## not the edge of the island, the terrain, the ocean, or the renderable world.
## Path widths, ride envelopes and buildings keep their physical dimensions.
const REBUILD_FOOTPRINT_MIN_X := -212.0
const REBUILD_FOOTPRINT_MAX_X := 222.0
const REBUILD_FOOTPRINT_MIN_Z := -230.0
const REBUILD_FOOTPRINT_MAX_Z := 220.0

## The world around the developed park. These deliberately do not participate
## in `rebuild_expand_point`: enlarging the scenery must never move a route or
## attraction. The developed envelope has more than two kilometres of ordinary
## land to the north, south and east, and nearly four kilometres of ocean to the
## west. These are deliberately landscape-scale reserves: even the diagnostic
## aerial cameras must not turn a terrain asset into the edge of the island.
## That is the distinction the first footprint implementation missed when it
## turned the atlas outline into a visible tabletop edge.
const REBUILD_WORLD_LAND_FROM_X := SHORE_FROM_X
const REBUILD_WORLD_LAND_TO_X := 2400.0
const REBUILD_WORLD_LAND_FROM_Z := -2400.0
const REBUILD_WORLD_LAND_TO_Z := 2400.0
const REBUILD_WORLD_WATER_FROM_X := -4200.0
const REBUILD_WORLD_WATER_TO_X := -70.0
const REBUILD_WORLD_WATER_FROM_Z := -3200.0
const REBUILD_WORLD_WATER_TO_Z := 3200.0
const REBUILD_WORLD_COAST_FROM_Z := -2200.0
const REBUILD_WORLD_COAST_TO_Z := 2200.0
const REBUILD_WORLD_MIN_PROGRAM_MARGIN := 2000.0
const REBUILD_FOOTPRINT_NORTH_ANCHOR_Z := -52.0
const REBUILD_FOOTPRINT_SOUTH_ANCHOR_Z := 52.0
const REBUILD_FOOTPRINT_EAST_ANCHOR_X := 128.0
const REBUILD_FOOTPRINT_WEST_ANCHOR_X := -112.0
# Exactly maps the old z=-160 water edge to the approved z=-230 boundary.
const REBUILD_FOOTPRINT_NORTH_SCALE := 178.0 / 108.0
const REBUILD_FOOTPRINT_SOUTH_SCALE := 1.55
const REBUILD_FOOTPRINT_EAST_SCALE := 2.50
const REBUILD_FOOTPRINT_WEST_SCALE := 1.50
const REBUILD_FOOTPRINT_NE_SCALE := 1.35
const REBUILD_FOOTPRINT_SE_SCALE := 1.45


## Move an atlas coordinate into the expanded footprint while holding the core.
## North/south are evaluated first because the east shoulder deliberately fans
## by a smaller factor there; the central east edge receives the full expansion.
## This is the same measured transform shown in the approved comparison map.
static func rebuild_expand_point(p: Vector2) -> Vector2:
	var q := p
	if p.y > REBUILD_FOOTPRINT_SOUTH_ANCHOR_Z:
		q.y = REBUILD_FOOTPRINT_SOUTH_ANCHOR_Z \
			+ (p.y - REBUILD_FOOTPRINT_SOUTH_ANCHOR_Z) \
			* REBUILD_FOOTPRINT_SOUTH_SCALE
		if p.x > 49.0:
			q.x = 49.0 + (p.x - 49.0) * REBUILD_FOOTPRINT_SE_SCALE
	elif p.y < REBUILD_FOOTPRINT_NORTH_ANCHOR_Z:
		q.y = REBUILD_FOOTPRINT_NORTH_ANCHOR_Z \
			+ (p.y - REBUILD_FOOTPRINT_NORTH_ANCHOR_Z) \
			* REBUILD_FOOTPRINT_NORTH_SCALE
		if p.x > 20.0:
			q.x = 20.0 + (p.x - 20.0) * REBUILD_FOOTPRINT_NE_SCALE
	elif p.x > REBUILD_FOOTPRINT_EAST_ANCHOR_X:
		q.x = REBUILD_FOOTPRINT_EAST_ANCHOR_X \
			+ (p.x - REBUILD_FOOTPRINT_EAST_ANCHOR_X) \
			* REBUILD_FOOTPRINT_EAST_SCALE
	if p.x < REBUILD_FOOTPRINT_WEST_ANCHOR_X:
		q.x = REBUILD_FOOTPRINT_WEST_ANCHOR_X \
			+ (p.x - REBUILD_FOOTPRINT_WEST_ANCHOR_X) \
			* REBUILD_FOOTPRINT_WEST_SCALE
	return q


static func rebuild_expand_position(p: Vector3) -> Vector3:
	var q := rebuild_expand_point(Vector2(p.x, p.z))
	return Vector3(q.x, p.y, q.y)


static func _rebuild_expanded_points(points: Array) -> Array:
	var out := []
	for p in points:
		out.append(rebuild_expand_position(p))
	return out


static func _rebuild_expanded_run(run: Dictionary) -> Dictionary:
	var out := run.duplicate(true)
	out["points"] = _rebuild_expanded_points(run["points"])
	return out


## The measured overlay is now executable plan data rather than a picture the
## world is expected to imitate by eye. The coordinates below remain the
## measured source atlas so every old-to-new relationship is reviewable;
## `rebuild_terrain_shape`, `rebuild_route_runs` and `rebuild_build_runs` expose
## only the expanded coordinates to world builders. Existing assemblies own T0,
## T1 and T4–T7; the rebuild groundworks scene supplies the missing T2 lowland
## and T3 headland without duplicating those established surfaces.
const REBUILD_TERRAIN_BANDS := {
	&"T0": {"owner": &"west_shell", "shapes": [[
		Vector2(-178, -160), Vector2(-112, -160), Vector2(-112, 142),
		Vector2(-178, 160),
	]]},
	&"T1": {"owner": &"west_shell", "shapes": [[
		Vector2(-112, -150), Vector2(-58, -150), Vector2(-58, -14),
		Vector2(-57, -12), Vector2(-57, 8), Vector2(-58, 14),
		Vector2(-58, 60), Vector2(-67, 73), Vector2(-78, 90),
		Vector2(-84, 109), Vector2(-95, 128), Vector2(-112, 136),
	]]},
	&"T2": {"owner": &"park_groundworks", "shapes": [[
		Vector2(-58, -151), Vector2(25, -153), Vector2(72, -142),
		Vector2(112, -126), Vector2(136, -103), Vector2(143, -62),
		Vector2(144, 20), Vector2(141, 84), Vector2(129, 127),
		Vector2(101, 145), Vector2(26, 151), Vector2(-20, 145),
		Vector2(-50, 132), Vector2(-70, 110), Vector2(-78, 90),
		Vector2(-67, 73), Vector2(-58, 60),
	]]},
	&"T3": {"owner": &"park_groundworks", "shapes": [[
		Vector2(-45, -109), Vector2(-50, -126), Vector2(-43, -145),
		Vector2(-25, -156), Vector2(-3, -154), Vector2(13, -141),
		Vector2(15, -121), Vector2(4, -105), Vector2(-20, -100),
	]]},
	&"T4": {"owner": &"east_cascade", "shapes": [[
		Vector2(33, -132), Vector2(30, -116), Vector2(37, -96),
		Vector2(45, -80), Vector2(52, -62), Vector2(55, -42),
		Vector2(51, -22), Vector2(52, -5), Vector2(55, 15),
		Vector2(58, 35), Vector2(60, 55), Vector2(64, 72),
		Vector2(58, 91), Vector2(58, 110), Vector2(70, 128),
		Vector2(105, 136), Vector2(128, 123), Vector2(138, 100),
		Vector2(141, 60), Vector2(142, 15), Vector2(140, -40),
		Vector2(136, -82), Vector2(122, -112), Vector2(92, -130),
		Vector2(58, -139),
	]]},
	&"T5": {"owner": &"east_cascade", "shapes": [[
		Vector2(58, -137), Vector2(56, -122), Vector2(63, -106),
		Vector2(70, -91), Vector2(78, -73), Vector2(77, -54),
		Vector2(70, -35), Vector2(68, -16), Vector2(72, 3),
		Vector2(75, 25), Vector2(75, 48), Vector2(84, 60),
		Vector2(88, 78), Vector2(80, 99), Vector2(74, 116),
		Vector2(90, 130), Vector2(115, 130), Vector2(132, 112),
		Vector2(137, 78), Vector2(138, 35), Vector2(136, -15),
		Vector2(132, -60), Vector2(122, -97), Vector2(103, -120),
		Vector2(80, -133),
	]]},
	&"T6": {"owner": &"east_cascade", "shapes": [[
		Vector2(80, -132), Vector2(77, -117), Vector2(72, -104),
		Vector2(70, -92), Vector2(78, -79), Vector2(86, -66),
		Vector2(94, -56), Vector2(99, -41), Vector2(106, -25),
		Vector2(114, -8), Vector2(120, 12), Vector2(128, 31),
		Vector2(138, 40), Vector2(141, -10), Vector2(139, -54),
		Vector2(132, -88), Vector2(119, -112), Vector2(101, -126),
	]]},
	# T7, the perimeter rim, left this table on 2026-09-03: the landform outside
	# the park is the crescent range, described once by RIM_RANGE_PROFILE and its
	# accessors and planned as package 02A in world coordinates.
}

## The two immutable construction envelopes. New ground and paving are rejected
## if they enter either one; the only circulation inside NT-1 and NT-2 remains
## the geometry already owned by the corresponding monument scene.
const REBUILD_PROTECTED_ZONES := {
	&"NT-1": {
		"name": "Cascading Staircases",
		"kind": &"rect",
		"min": Vector2(-74.0, -15.0),
		"max": Vector2(-55.0, 12.0),
	},
	&"NT-2": {
		"name": "Terraced Fountain",
		"kind": &"ellipse",
		"centre": Vector2(86.0, 0.0),
		"radii": Vector2(42.0, 36.0),
	},
}

## Junctions stay named from the first trunk pass onward so later district
## loops connect to an existing place rather than inventing nearby endpoints.
const REBUILD_JUNCTIONS := {
	&"J1": Vector2(0, 104.7),
	&"J2": Vector2(0, 0),
	&"J3": Vector2(-6, -78.4),
	&"J4": Vector2(-16, -151.0),
	&"J5": Vector2(-52, -2),
	&"J6": Vector2(-48, 92.3),
	&"J7": Vector2(49, 76.8),
	&"J8": Vector2(74, 48),
	&"J9": Vector2(119.9, -61.9),
}

## Routes A and B are the first permanent circulation. The x/z coordinates and
## widths are the approved overlay's; y is the built grade added here. `build`
## is false only where an inherited amber core already supplies the exact walk:
## the boardwalk deck and the protected Cascading Staircases handoff. Those runs
## still belong in this table because the minimap and future mission routing need
## one unbroken description of the network.
const REBUILD_PRIMARY_ROUTE_RUNS := [
	# Final-world z=219 to the apron. The first point is expressed in source-atlas
	# coordinates because this table passes through `rebuild_expand_point`;
	# widths remain real metres and are never scaled.
	{"id": &"a_parking_arrival", "route": &"A", "width": 14.0,
		"build": false, "owner": &"entrance", "points": [
			Vector3(0, 0, REBUILD_FOOTPRINT_SOUTH_ANCHOR_Z
				+ (ARRIVAL_AXIS_TO_Z - REBUILD_FOOTPRINT_SOUTH_ANCHOR_Z)
				/ REBUILD_FOOTPRINT_SOUTH_SCALE),
			Vector3(0, 0, 123),
		]},
	{"id": &"a_entrance", "route": &"A", "width": 11.0, "build": true,
		"points": [
			Vector3(0, 0, 123), Vector3(0, 0, 107), Vector3(0, 0, 86),
			Vector3(0, 0, 62), Vector3(0, 0, 34), Vector3(0, 0, 18),
		]},
	{"id": &"a_headland", "route": &"A", "width": 11.0, "build": true,
		"points": [
			Vector3(0, 0, -18), Vector3(-1, 0, -35),
			Vector3(-3, 0, -52), Vector3(-6, 0, -68),
			Vector3(-10, 1.0, -84), Vector3(-13, 2.8, -101),
			# Same approved centreline, with one grade break at the outside edge
			# of the lighthouse loop so the climb reaches its four-metre table
			# before the two paving ribbons overlap.
			Vector3(-14.64, 4.0, -107),
			Vector3(-16, 4.0, -112),
		]},
	{"id": &"a_lighthouse_loop", "route": &"A", "width": 10.0,
		"build": true, "closed": true, "points": [
			Vector3(-16, 4, -112), Vector3(-30, 4, -114),
			Vector3(-37, 4, -125), Vector3(-31, 4, -138),
			Vector3(-16, 4, -144), Vector3(0, 4, -139),
			Vector3(6, 4, -126), Vector3(1, 4, -115),
			Vector3(-16, 4, -112),
		]},
	{"id": &"a_hub_ring", "route": &"A", "width": 18.0,
		"build": true, "closed": true, "points": [
			Vector3(0, 0, 18), Vector3(9, 0, 15), Vector3(16, 0, 8),
			Vector3(18, 0, 0), Vector3(16, 0, -8), Vector3(9, 0, -15),
			Vector3(0, 0, -18), Vector3(-9, 0, -15), Vector3(-16, 0, -8),
			Vector3(-18, 0, 0), Vector3(-16, 0, 8), Vector3(-9, 0, 15),
			Vector3(0, 0, 18),
		]},
	{"id": &"b_waterfront", "route": &"B", "width": 10.0,
		"build": false, "owner": &"boardwalk", "points": [
			Vector3(-96, SHORE_TOP, -62), Vector3(-96, SHORE_TOP, -40),
			Vector3(-96, SHORE_TOP, -15), Vector3(-96, SHORE_TOP, 10),
			Vector3(-96, SHORE_TOP, 35), Vector3(-96, SHORE_TOP, 60),
		]},
	{"id": &"b_north_return", "route": &"B", "width": 8.0,
		"build": true, "retained": true, "points": [
			# The full approach now carries the six-metre descent. Keeping the
			# first fifty metres level compressed the same fall into one short
			# chord at the bluff and produced a 21.7% break in an otherwise broad
			# return. These are grade changes only; the approved atlas centreline
			# and its eight-metre operating width remain untouched.
			Vector3(-6, 0, -68), Vector3(-22, 0, -66),
			Vector3(-40, -0.4, -62), Vector3(-58, -1.85, -58),
			Vector3(-75, -4.1, -59), Vector3(-90, SHORE_TOP, -62),
			Vector3(-96, SHORE_TOP, -62),
		]},
	{"id": &"b_monument_return", "route": &"B", "width": 9.0,
		"build": false, "owner": &"west_stair", "points": [
			Vector3(-18, 0, 0), Vector3(-32, 0, -1), Vector3(-45, 0, -2),
			Vector3(-52, 0, -2), Vector3(-58, 0, -2),
			Vector3(-72, SHORE_TOP, -2), Vector3(-84, SHORE_TOP, -2),
			Vector3(-96, SHORE_TOP, -2),
		]},
	{"id": &"b_south_return", "route": &"B", "width": 8.0,
		"build": true, "retained": true, "points": [
			# The whole outer sweep is the climb. Holding the first nineteen metres
			# level forced the final approach into a 1:5 pitch and made the path read
			# as a flyover meeting a cliff. These elevations distribute the same six
			# metres over the full 56m run and reach the bluff crest before its face.
			Vector3(-96, SHORE_TOP, 60), Vector3(-88, -4.90, 64),
			Vector3(-82, -3.67, 72),
			# C crosses this chord exactly where the approved atlas draws it.  The
			# two controls carry one shared gentle grade so the crossing is a
			# junction, not one public route colliding with a bridge above it.
			Vector3(-80, -2.17, 84), Vector3(-75, -1.07, 95),
			# The shallow crown keeps paving and the inherited bluff cap from
			# depth-fighting without changing the route's perceived grade.
			Vector3(-64, 0.08, 101), Vector3(-53, 0.08, 98),
			Vector3(-47, 0, 90),
			Vector3(-48, 0, 78),
		]},
]

## The route-B monument line is continuous in the plan, but its middle belongs
## to NT-1 and therefore cannot be regenerated. These two short surfaces take
## the new nine-metre hub branch down to the existing six-metre arch throat;
## the tunnel, terrace, monument and boardwalk arrival remain their established
## scenes from that point on.
const REBUILD_PRIMARY_CONNECTORS := [
	{"id": &"b_hub_west", "route": &"B", "width": 9.0, "points": [
		Vector3(-18, 0, 0), Vector3(-25, 0, -0.5),
	]},
	{"id": &"b_west_throat", "route": &"B", "width": ARCH_WIDTH, "points": [
		Vector3(-25, 0, -0.5), Vector3(ARCH_MOUTH_X, 0, ARCH_AT.y),
	]},
]

## Routes C-F transcribed from the approved rebuild atlas.  These stay as
## source-atlas Vector2s so the footprint transform is applied once to their
## centre lines while widths remain literal metres.  A run with `build=false`
## is still part of the public network, but its paving belongs to an existing
## protected assembly.  In particular, the two E approaches around NT-2 are
## descriptions of the Terraced Fountain's established walks, not permission
## to draw a second surface over them.
const REBUILD_DISTRICT_ROUTE_RUNS := [
	{"id": &"c_coastal_loop", "route": &"C", "width": 8.0,
		"build": true, "closed": true, "points": [
			Vector2(-48, 78), Vector2(-58, 70), Vector2(-72, 76),
			Vector2(-78, 90), Vector2(-70, 108), Vector2(-52, 116),
			Vector2(-32, 112), Vector2(-18, 101), Vector2(-10, 88),
			Vector2(-22, 77), Vector2(-48, 78),
		]},
	{"id": &"c_entrance_link", "route": &"C", "width": 9.0,
		"build": true, "points": [
			Vector2(-10, 88), Vector2(-4, 87), Vector2(0, 86),
		]},
	{"id": &"c_plaza_link", "route": &"C", "width": 9.0,
		"build": true, "points": [
			Vector2(-22, 77), Vector2(-18, 62), Vector2(-13, 44),
			Vector2(-10, 28), Vector2(-12, 14),
		]},

	{"id": &"d_arrival", "route": &"D", "width": 9.0,
		"build": true, "points": [
			Vector2(0, 86), Vector2(12, 82), Vector2(25, 76),
			Vector2(38, 70), Vector2(49, 68),
		]},
	{"id": &"d_family_loop", "route": &"D", "width": 8.0,
		"build": true, "closed": true, "points": [
			Vector2(49, 68), Vector2(58, 55), Vector2(75, 51),
			Vector2(91, 56), Vector2(105, 69), Vector2(108, 86),
			Vector2(98, 103), Vector2(80, 111), Vector2(61, 108),
			Vector2(46, 96), Vector2(42, 82), Vector2(49, 68),
		]},
	{"id": &"d_plaza_return", "route": &"D", "width": 10.0,
		"build": true, "points": [
			Vector2(49, 68), Vector2(42, 54), Vector2(34, 39),
			Vector2(25, 25), Vector2(15, 14),
		]},
	{"id": &"d_terrace_link", "route": &"D", "width": 9.0,
		"build": false, "owner": &"east_cascade", "points": [
			Vector2(58, 55), Vector2(66, 44), Vector2(72, 32),
			Vector2(72, 22),
		]},

	{"id": &"e_south_protected", "route": &"E", "width": 8.5,
		"build": false, "owner": &"east_cascade", "points": [
			Vector2(46, 0), Vector2(48, -18), Vector2(55, -30),
			Vector2(70, -42), Vector2(90, -50),
		]},
	{"id": &"e_outer_orbit", "route": &"E", "width": 8.5,
		"build": false, "owner": &"east_cascade", "points": [
			Vector2(90, -50), Vector2(108, -52), Vector2(118, -40),
			Vector2(122, -20), Vector2(112, 0), Vector2(120, 14),
			Vector2(119, 30), Vector2(108, 43), Vector2(91, 50),
			Vector2(74, 48),
		]},
	{"id": &"e_north_protected", "route": &"E", "width": 8.5,
		"build": false, "owner": &"east_cascade", "points": [
			Vector2(74, 48), Vector2(58, 40), Vector2(49, 26),
			Vector2(46, 0),
		]},
	{"id": &"e_axis", "route": &"E", "width": 9.0,
		"build": false, "owner": &"east_cascade", "points": [
			Vector2(18, 0), Vector2(32, 0), Vector2(46, 0),
		]},
	{"id": &"e_family_link", "route": &"E", "width": 9.0,
		"build": false, "owner": &"east_cascade", "points": [
			Vector2(72, 32), Vector2(74, 40), Vector2(74, 48),
		]},
	{"id": &"e_junction_nine", "route": &"E", "width": 9.0,
		"build": true, "points": [Vector2(90, -50), Vector2(94, -58)]},

	{"id": &"f_outer_arc", "route": &"F", "width": 9.0,
		"build": true, "points": [
			Vector2(-6, -68), Vector2(4, -82), Vector2(20, -100),
			Vector2(40, -113), Vector2(63, -120), Vector2(86, -116),
			Vector2(106, -104), Vector2(120, -86), Vector2(124, -62),
			Vector2(118, -42),
		]},
	{"id": &"f_terrace_protected", "route": &"F", "width": 9.0,
		"build": false, "owner": &"east_cascade", "points": [
			Vector2(118, -42), Vector2(107, -30), Vector2(94, -50),
		]},
	{"id": &"f_inner_return", "route": &"F", "width": 9.0,
		"build": true, "points": [
			# Begin at named J9, after the twelve-metre terrace link. Starting at
			# the protected (94,-50) handoff made the discontinuous north expansion
			# pull the next control east, folding this return back across the link.
			Vector2(94, -58),
			Vector2(78, -65), Vector2(58, -70), Vector2(39, -64),
			Vector2(20, -55), Vector2(-1, -58), Vector2(-6, -68),
		]},
	{"id": &"f_terrace_link", "route": &"F", "width": 12.0,
		"build": true, "points": [Vector2(94, -50), Vector2(94, -58)]},
	{"id": &"f_headland_link", "route": &"F", "width": 12.0,
		"build": true, "points": [Vector2(-6, -68), Vector2(-3, -52)]},
]

## Package 04 program sites.  The atlas decides position, envelope and access;
## the generator decides how a greybox ride or building depicts that record.
## Existing R1/R2/R3 are deliberately absent because their canonical
## Boardwalk scene already owns them. P5 is a programmed attraction below:
## package 04E replaces the obsolete hand-authored Plaza bandstand outright.
const REBUILD_RIDE_SITES := [
	{"id": &"R4", "kind": &"ship", "at": Vector2(-56, 90),
		"size": Vector2(26, 10), "queue": [Vector2(-70, 78), Vector2(-66, 80),
			Vector2(-69, 83), Vector2(-66, 85), Vector2(-68, 87),
			Vector2(-64, 89), Vector2(-61, 87)]},
	{"id": &"R5", "kind": &"mini_rail", "at": Vector2(68, 88),
		"radii": Vector2(17, 12), "queue": [Vector2(46, 88), Vector2(52, 88)]},
	{"id": &"R6", "kind": &"tubs", "at": Vector2(95, 96), "radius": 7.0,
		"queue": [Vector2(104, 88), Vector2(101, 92), Vector2(99, 95)]},
	{"id": &"R7", "kind": &"carousel", "at": Vector2(109, 62), "radius": 7.0,
		"queue": [Vector2(102, 70), Vector2(104, 66), Vector2(106, 63)]},
	# Moved 2026-09-04: at (116, -57) the expanded court shared the coaster's
	# footprint corner, its seats 8.9m from the rails. Clear of R13, F and R11
	# by 16m or more now.
	{"id": &"R8", "kind": &"chair_swing", "at": Vector2(104, -66),
		"radius": 7.5, "queue": [Vector2(96, -53), Vector2(99, -56),
			Vector2(101, -60), Vector2(103, -63)]},
	{"id": &"R9", "kind": &"water_ride", "points": [
		Vector2(9, -72), Vector2(15, -85), Vector2(27, -100),
		Vector2(41, -103), Vector2(48, -92), Vector2(39, -77),
		Vector2(28, -67), Vector2(16, -65),
	], "queue": [Vector2(20, -56), Vector2(22, -64), Vector2(25, -71)]},
	{"id": &"R10", "kind": &"mine_train", "points": [
		Vector2(58, -80), Vector2(57, -102), Vector2(70, -116),
		Vector2(90, -114), Vector2(101, -101), Vector2(98, -83),
		Vector2(83, -72), Vector2(66, -72),
	], "queue": [Vector2(67, -69), Vector2(69, -75), Vector2(71, -80)]},
	{"id": &"R11", "kind": &"observation", "at": Vector2(111, -87),
		"radius": 8.0, "queue": [Vector2(119, -82), Vector2(114, -86)]},
	{"id": &"R12", "kind": &"sky_ride", "terminals": [
		Vector2(-18, -104), Vector2(112, -106),
	]},
	{"id": &"R13", "kind": &"steel_coaster", "track": [
		Vector2(129, -41), Vector2(139, -46), Vector2(150, -38),
		Vector2(153, -20), Vector2(150, -2), Vector2(146, 17),
		Vector2(148, 34), Vector2(141, 44), Vector2(132, 42),
		Vector2(137, 29), Vector2(140, 12), Vector2(140, -5),
		Vector2(143, -22), Vector2(139, -35), Vector2(129, -41),
	# Route F owns this edge. `track_anchor` keeps the ride geometry fixed and,
	# since 2026-09-04, the station rides with the track as an open shed on
	# posts; the earlier east shift of the station alone put the rails over its
	# roof. `clearance_test` is what says whether its west end clears F.
	], "track_anchor": Vector2(129, -41),
		"station": Vector2(135, -41), "station_size": Vector2(14, 8),
		"queue": [Vector2(118, -40), Vector2(124, -40),
			Vector2(129, -41), Vector2(132.2, -41)]},
	{"id": &"R14", "kind": &"junior_coaster", "track": [
		Vector2(107, 110), Vector2(111, 104), Vector2(118, 98),
		Vector2(125, 89), Vector2(126, 79), Vector2(121, 72),
		Vector2(115, 75), Vector2(117, 86), Vector2(113, 96),
		Vector2(108, 104), Vector2(107, 110),
	], "station": Vector2(107, 111), "station_size": Vector2(10, 8),
		"queue": [Vector2(98, 103), Vector2(100, 105), Vector2(102, 108.5)]},
]


## The package-04G+ miniature railway's horizontal centreline. Its atlas centre
## is expanded exactly once while the approved 17m x 12m ride envelope keeps
## its real size. Height belongs to the generated family terrain, so callers
## lift this closed plan loop to the local rail datum.
static func rebuild_kiddie_rail_loop() -> Array[Vector3]:
	var site: Dictionary = {}
	for candidate in REBUILD_RIDE_SITES:
		if StringName(candidate["id"]) == &"R5":
			site = candidate
			break
	assert(not site.is_empty(), "package 04G+ has no R5 miniature railway site")
	var centre := rebuild_expand_point(Vector2(site["at"]))
	var radii: Vector2 = site["radii"]
	var out: Array[Vector3] = []
	# Start on the west tangent beside the station and repeat it at the end so
	# both rail emission and vehicle sampling see an ordinary closed polyline.
	for i in KIDDIE_RAIL_STEPS + 1:
		var angle := PI + TAU * float(i) / float(KIDDIE_RAIL_STEPS)
		out.append(Vector3(
			centre.x + cos(angle) * radii.x,
			0.0,
			centre.y + sin(angle) * radii.y))
	return out


const REBUILD_ATTRACTION_SITES := [
	# P1 stands on the point since 2026-09-04 (04B): world (-153, -268) on the
	# promontory's spine, the keeper's exhibit ten metres north of the walk,
	# reached by the promontory walk from the headland loop's west vertex up
	# the middle of the land. It stood at world (-153, -247) for a day, which
	# is the cove-side cliff edge. Source coordinates, as this table passes
	# through `rebuild_expand_point`; the tower is the one program element
	# outside the developed envelope, by decision.
	{"id": &"P1", "kind": &"lighthouse", "at": Vector2(-139.3, -183.1),
		"keeper": Vector2(-122.7, -186.7), "keeper_size": Vector2(8, 6),
		# The walk ends at the forecourt's rim, not at the tower's centre: the
		# controller walk of the last leg ran into the lighthouse base.
		# The turn west at the seam is five gentle bends rather than one of
		# 72 degrees: at a sharp corner the outer edge's mitre leaves the
		# collision prisms and the capsule stalls on their side face.
		"access": [Vector2(-37, -125), Vector2(-50, -162.4),
			Vector2(-53, -168.5), Vector2(-57, -173.3), Vector2(-64, -176.4),
			Vector2(-74, -177.3), Vector2(-100, -177.0), Vector2(-120.7, -180.0),
			Vector2(-134.3, -182.3)]},
	{"id": &"P2", "kind": &"funhouse", "at": Vector2(-77, 32),
		"size": Vector2(12, 14), "access": [Vector2(-96, 27),
			Vector2(-90, 27), Vector2(-87, 25), Vector2(-84, 27), Vector2(-83, 27)],
		"exit": [Vector2(-83, 37), Vector2(-88, 37), Vector2(-91, 40), Vector2(-96, 40)]},
	{"id": &"P3", "kind": &"big_top", "at": Vector2(-32, 92),
		"radii": Vector2(9, 6), "access": [Vector2(-35, 77.5),
			Vector2(-35, 80.5), Vector2(-40, 80.5), Vector2(-40, 83),
			Vector2(-35.5, 83), Vector2(-35.5, 85.5), Vector2(-32, 86)]},
	{"id": &"P4", "kind": &"play_garden", "at": Vector2(27, 93),
		"radii": Vector2(9, 7), "access": [Vector2(12, 82),
			Vector2(17, 84), Vector2(21.5, 87.5)]},
	# P5 is inside the fixed Plaza datum, so these coordinates deliberately pass
	# through the expansion map unchanged. This is the complete 04E parcel from
	# the atlas, not the old bandstand that happened to stand at (-20, -20).
	{"id": &"P5", "kind": &"bandstand", "at": Vector2(-42, -32),
		"radius": 6.2,
		"audience": Vector2(-31, -23.5), "audience_radii": Vector2(7, 10),
		"audience_rotation": 37.3,
		# The intermediate dogleg clears the protected west-arch north pier at its
		# full three-metre operating width; start, holding point and lawn handoff
		# remain the atlas' established P5 decisions.
		"access": [Vector2(-32, -1), Vector2(-28, -3),
			Vector2(-28, -12), Vector2(-35, -13), Vector2(-37.1, -15.5)],
		"exit": [Vector2(-25.4, -19.3), Vector2(-21, -18),
			Vector2(-16, -16), Vector2(-9, -15)],
		"photo": Vector2(-20, -28),
		"photo_access": [Vector2(-25, -20), Vector2(-22, -23),
			Vector2(-20, -28)],
		"service": [Vector2(-62, -38), Vector2(-58, -38),
			Vector2(-58, -39)],
		"backstage": Vector2(-53, -39), "backstage_size": Vector2(10, 6),
		"host": Vector2(-36, -16.5), "host2": Vector2(-27, -20.5)},
]

const REBUILD_INTERIOR_SITES := [
	{"id": &"I1", "at": Vector2(-35, 68), "size": Vector2(16, 10),
		"district": &"fairground", "access": [Vector2(-35, 77), Vector2(-35, 73)]},
	{"id": &"I2", "at": Vector2(-83, -29), "size": Vector2(16, 10),
		"district": &"boardwalk", "access": [Vector2(-96, -29), Vector2(-91, -29)]},
	{"id": &"I3", "at": Vector2(-81, -48), "size": Vector2(14, 8),
		"district": &"boardwalk", "access": [Vector2(-82, -60), Vector2(-82, -52)]},
	# The atlas' first I4 address put the west return wall inside route F after
	# expansion. Move the complete café parcel east; its threshold remains a
	# short branch from the same point on F rather than making the path bend.
	{"id": &"I4", "at": Vector2(136, -73), "size": Vector2(14, 8),
		"district": &"highland", "access": [Vector2(124, -62),
			Vector2(128, -67), Vector2(129, -73)]},
	{"id": &"I5", "at": Vector2(-16, 116), "size": Vector2(12, 8),
		"district": &"entrance", "access": [Vector2(0, 116), Vector2(-10, 116)]},
	{"id": &"I6", "at": Vector2(16, 116), "size": Vector2(12, 8),
		"district": &"entrance", "access": [Vector2(0, 116), Vector2(10, 116)]},
]

const REBUILD_MIDWAY_UNITS := [
	{"id": &"F1", "at": Vector2(-22.5, 24), "front": &"east"},
	{"id": &"F2", "at": Vector2(-21.5, 31), "front": &"east"},
	{"id": &"F3", "at": Vector2(-22, 38), "front": &"east"},
	{"id": &"F4", "at": Vector2(-23.5, 45), "front": &"east"},
	{"id": &"F5", "at": Vector2(-25.5, 52), "front": &"east"},
	{"id": &"F6", "at": Vector2(-27.5, 59), "front": &"east"},
	{"id": &"B1", "at": Vector2(-86.5, -19), "front": &"west"},
	{"id": &"B2", "at": Vector2(-86.5, -11), "front": &"west"},
	{"id": &"B3", "at": Vector2(-86.5, 9), "front": &"west"},
	{"id": &"B4", "at": Vector2(-86.5, 17), "front": &"west"},
	{"id": &"K1", "at": Vector2(9.5, 97), "front": &"north"},
	{"id": &"K2", "at": Vector2(14.5, 91), "front": &"north"},
]

const REBUILD_SERVICE_SPINES := [
	{"id": &"S1", "points": [Vector2(-52, -124), Vector2(-68, -108),
		Vector2(-69, -80), Vector2(-64, -60), Vector2(-62, -38), Vector2(-62, -23)]},
	{"id": &"S2", "points": [Vector2(-34, 126), Vector2(-40, 127),
		Vector2(-70, 120), Vector2(-80, 105), Vector2(-73, 80),
		Vector2(-64, 61), Vector2(-62, 38), Vector2(-62, 20)]},
	{"id": &"S3", "points": [Vector2(34, 126), Vector2(75, 126),
		Vector2(111, 116), Vector2(136, 100), Vector2(149, 75),
		Vector2(154, 42), Vector2(155, 10), Vector2(154, -22),
		Vector2(150, -55), Vector2(138, -82), Vector2(124, -100),
		Vector2(105, -122), Vector2(78, -132), Vector2(42, -135)]},
]

const REBUILD_COASTAL_CREEK := [
	Vector2(-48, 22), Vector2(-54, 29), Vector2(-59, 37),
	Vector2(-62, 44), Vector2(-70, 50), Vector2(-79, 54),
	Vector2(-88, 55), Vector2(-96, 55), Vector2(-104, 55),
]

const REBUILD_PLANTING_BANDS := [
	{"id": &"PL1_a", "kind": &"shade", "points": [Vector2(-10, 112),
		Vector2(-10, 86), Vector2(-10, 62), Vector2(-10, 38)]},
	{"id": &"PL1_b", "kind": &"shade", "points": [Vector2(10, 112),
		Vector2(10, 86), Vector2(10, 62), Vector2(10, 38)]},
	{"id": &"PL1_c", "kind": &"shade", "points": [Vector2(-11, -23),
		Vector2(-12, -38), Vector2(-15, -52), Vector2(-20, -68),
		Vector2(-24, -84), Vector2(-27, -98)]},
	{"id": &"PL1_d", "kind": &"shade", "points": [Vector2(11, -23),
		Vector2(10, -38), Vector2(7, -52), Vector2(2, -68),
		Vector2(-2, -84), Vector2(-5, -98)]},
	{"id": &"PL1_e", "kind": &"shade", "points": [Vector2(-84, -58),
		Vector2(-84, -38), Vector2(-84, -15), Vector2(-84, 10),
		Vector2(-84, 34), Vector2(-84, 55)]},
	{"id": &"PL2_a", "kind": &"screen", "points": [Vector2(-78, 116),
		Vector2(-60, 124), Vector2(-40, 128)]},
	{"id": &"PL2_b", "kind": &"screen", "points": [Vector2(34, 120),
		Vector2(58, 121), Vector2(80, 118)]},
	{"id": &"PL2_c", "kind": &"screen", "points": [Vector2(-59, -47),
		Vector2(-54, -44), Vector2(-48, -41)]},
	{"id": &"PL2_d", "kind": &"screen", "points": [Vector2(130, -71),
		Vector2(144, -65), Vector2(151, -57)]},
]


static func rebuild_expand_points2(points: Array) -> Array[Vector2]:
	var out: Array[Vector2] = []
	for point in points:
		out.append(rebuild_expand_point(Vector2(point)))
	return out


static func _rebuild_expand_plan_run(run: Dictionary) -> Dictionary:
	var out := run.duplicate(true)
	var points: Array[Vector2] = []
	for point in run["points"]:
		points.append(rebuild_expand_point(Vector2(point)))
	out["points"] = points
	return out


static func rebuild_route_runs() -> Array:
	var out := []
	for run in REBUILD_PRIMARY_ROUTE_RUNS:
		out.append(_plan_run(run["id"], _rebuild_expanded_points(run["points"]),
			float(run["width"])))
	for source in REBUILD_DISTRICT_ROUTE_RUNS:
		var run := _rebuild_expand_plan_run(source)
		out.append({
			"id": run["id"],
			"route": run["route"],
			"points": run["points"],
			"width": run["width"],
			"closed": bool(run.get("closed", false)),
		})
	return out


static func rebuild_build_runs() -> Array:
	var out := []
	for run in REBUILD_PRIMARY_ROUTE_RUNS:
		if bool(run.get("build", false)):
			out.append(_rebuild_expanded_run(run))
	for connector in REBUILD_PRIMARY_CONNECTORS:
		out.append(_rebuild_expanded_run(connector))
	return out


static func rebuild_district_build_runs() -> Array:
	var out := []
	for source in REBUILD_DISTRICT_ROUTE_RUNS:
		if bool(source.get("build", false)):
			out.append(_rebuild_expand_plan_run(source))
	return out


static func rebuild_terrain_shape(id: StringName, index := 0) -> Array:
	var out := []
	for p in REBUILD_TERRAIN_BANDS[id]["shapes"][index]:
		out.append(rebuild_expand_point(p))
	return out


# ---------------------------------------------------------------------------
# Inherited anchor walkways
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

	## South out of the plaza and down the street to the gate and the apron. The
	## extra node at z 31.3 is the junction with Kiddieland's secondary route:
	## people arriving through the gate can take one legible turn onto it instead
	## of walking past the corridor, circling the photo hut, and doubling back.
	## The small dogleg before it remains real: the ring is centred on the fountain
	## and the street is not, so the walk bends onto the street's centre line.
	##
	## The run is pinched between the ring and z 30 — `bench_south` at (−5,19)
	## and `bench_se` at (2,22) leave about five metres between them — so its six-
	## metre paving is the most this approach can honestly claim. At z 31.3 it
	## opens into the long east corridor. The crowd graph names that junction and
	## follows it toward Kiddieland, so player paving and guest traffic agree.
	&"spoke_south": [
		Vector2(0.0, 16.0), Vector2(-1.5, 30.0), Vector2(-1.5, 31.3),
		Vector2(-1.5, STREET_FROM_Z),
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

	## Three spokes to the outer sections. Each run stops at its mouth.
	##
	## **These were straight, and three of them ran through buildings.** Written
	## when this file's only consumer was the minimap, they were drawn as rays
	## from the ring to each threshold and never checked against `plaza.tscn`,
	## which is hand-placed and did not agree: the retired north-east spoke spent
	## 21m inside `perim_e_north`, `spoke_se` 28m inside `perim_e_south`, `spoke_sw` 11m
	## inside `building_south_west`. On a map at that scale a line through a wall
	## is a few pixels and looks like nothing. Paving them made it visible in one
	## screenshot, which is the whole argument for a plan being built rather than
	## only drawn.
	##
	## The unopened NNW and SW spokes still bend around permanent buildings. The
	## open SE route is different: it uses the long east-west corridor already
	## visible from the entrance street. Its former dogleg was an attempt to keep
	## a hand planter and generated furniture fixed; that made scenery dictate
	## circulation, so those objects move and the public path stays straight.

	## East of the bandstand, then into the twelve-metre corridor between
	## `building_north` and `perim_nw` that the north wall's gap opens onto.
	&"spoke_nnw": [
		Vector2(-8.0, -13.86), Vector2(-14.0, -30.0), Vector2(-16.9, -51.5),
	],

	## The first orbital connection. It starts beside the east-gate forecourt,
	## turns behind the dark ride and meets the NNW/Grove mouth from its plaza
	## side. These are public brick walks rather than asphalt plaza spokes; the
	## separate entries preserve the narrower architectural pinch at the mouth.
	&"promenade_ne": PROMENADE_NE_POINTS,
	&"promenade_nnw_link": PROMENADE_NNW_LINK_POINTS,

	## Kiddieland's secondary link: one straight run from the entrance/plaza axis
	## through the south-east arch. The photo hut sits 6.8m north of its edge and
	## the east frontage already opens around the arch, so there is no architectural
	## reason to bend. The planter formerly at (8,29) moves into the south-side bay;
	## generated trees, lamps and bins use `stand_score` and move automatically.
	&"spoke_se": [
		Vector2(-1.5, 31.3), Vector2(51.5, 31.3),
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
	&"promenade_ne": PROMENADE_WIDTH,
	&"promenade_nnw_link": 3.0,
	## Still unmistakable from the hub, but subordinate to Kiddieland's 7.5–8m
	## entrance-side primary route.
	&"spoke_se": 5.5,
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
	# The minimap describes the complete approved rebuild instead of
	# accumulating every temporary route the park has ever had. A, B, D and E
	# include inherited spans with canonical owners, so callers still see one
	# continuous network where the new generator correctly yields ownership.
	var out := rebuild_route_runs()
	# P5 is inside the fixed Plaza rather than a district route layer, but its
	# entry, release and photo branch are still public circulation. Publishing
	# them here gives the minimap, furniture scatter and clearance tooling the
	# same complete walking envelope that package 04E builds and tests.
	for site in REBUILD_ATTRACTION_SITES:
		if StringName(site["id"]) != &"P5":
			continue
		out.append({"id": &"p5_audience_entry", "points": site["access"],
			"width": 3.0})
		out.append({"id": &"p5_audience_release", "points": site["exit"],
			"width": 3.0})
		out.append({"id": &"p5_photo_access", "points": site["photo_access"],
			"width": 2.6})
		break
	return out


static func _plan_run(id: StringName, points3: Array, width: float) -> Dictionary:
	var points2: Array[Vector2] = []
	for p in points3:
		points2.append(Vector2(p.x, p.z))
	return {"id": id, "points": points2, "width": width}


## The full public route over the east hill, projected for the minimap. These
## are arrangements of the same paths the ground, crowd and walk tests consume;
## no hand-drawn map line gets a second opinion about where a route bends.
static func east_public_walkway_runs() -> Array:
	var out := []
	var axis: float = ARCH_AT.y
	# Kiddieland is already public ground even though its eventual section seam
	# is not. Publishing all three hierarchy levels makes the minimap agree with
	# what a guest can actually walk, including the family-commons loop.
	var kiddie_gateway: Array[Vector3] = []
	var kiddie_plaza: Array[Vector3] = []
	var kiddie_primary: Array[Vector3] = []
	for i in KIDDIE_GATEWAY_INDEX + 1:
		kiddie_gateway.append(KIDDIE_ARRIVAL_POINTS[i])
	for i in range(KIDDIE_GATEWAY_INDEX, KIDDIE_COMMONS_INDEX + 1):
		kiddie_plaza.append(KIDDIE_ARRIVAL_POINTS[i])
	for i in range(KIDDIE_COMMONS_INDEX, KIDDIE_ARRIVAL_POINTS.size()):
		kiddie_primary.append(KIDDIE_ARRIVAL_POINTS[i])
	out.append(_plan_run(&"kiddie_gateway", kiddie_gateway, KIDDIE_GATEWAY_W))
	out.append(_plan_run(&"kiddie_plaza_return", kiddie_plaza, KIDDIE_PLAZA_LINK_W))
	out.append(_plan_run(&"kiddie_primary", kiddie_primary, KIDDIE_PRIMARY_PATH_W))
	out.append(_plan_run(&"kiddie_entrance", KIDDIE_ENTRANCE_LINK,
		KIDDIE_ENTRANCE_LINK_W))
	out.append(_plan_run(&"kiddie_commons_garden", KIDDIE_COMMONS_GARDEN_LINK,
		KIDDIE_COMMONS_GARDEN_W))
	for entry in [[-1.0, &"n"], [1.0, &"s"]]:
		var side: float = entry[0]
		var tag: StringName = entry[1]
		var wing: Array = wing_path(CASCADE_EAST, side)
		out.append(_plan_run(StringName("east_wing_%s" % tag), wing, WING_W))

		var climb: Array[Vector3] = [
			Vector3(CLIMB_FROM_X, HILL_TOP, axis + side * climb_flight_z()),
		]
		for reach in climb_reaches():
			climb.append(Vector3(float(reach[1]), float(reach[3]),
				axis + side * climb_flight_z()))
		climb.append(Vector3(CLIMB_TO_X + 4.0, CLIMB_HEAD_Y, axis))
		out.append(_plan_run(StringName("east_climb_%s" % tag), climb,
			CLIMB_FLIGHT_W))

		var end: Array[Vector3] = [
			Vector3(CLIMB_TO_X + 4.0, CLIMB_HEAD_Y, axis),
		]
		end.append_array(east_end_path(side))
		out.append(_plan_run(StringName("east_end_%s" % tag), end,
			EAST_END_PATH_HALF_W * 2.0))

	out.append(_plan_run(&"east_tower", east_tower_path(),
		EAST_END_PATH_HALF_W * 2.0))
	out.append(_plan_run(&"east_frontier", east_frontier_path(),
		EAST_FRONTIER_PATH_W))
	out.append(_plan_run(&"sky_ride_access", sky_ride_access_path(),
		SKY_RIDE_ACCESS_W))
	return out


## The Grove's public hierarchy, projected for the minimap from the same paths
## used by its paving and walking tests. The main and garden runs are through
## routes; the remaining three deliberately stop at side destinations or at a
## temporary future-land gate.
static func grove_public_walkway_runs() -> Array:
	return [
		_plan_run(&"grove_arrival", GROVE_ARRIVAL_POINTS,
			GROVE_ARRIVAL_PATH_W),
		_plan_run(&"grove_garden_loop", GROVE_GARDEN_LOOP,
			GROVE_GARDEN_PATH_W),
		_plan_run(&"grove_sky_ride", GROVE_SKY_RIDE_SPUR,
			GROVE_SKY_RIDE_SPUR_W),
		_plan_run(&"grove_tram", GROVE_TRAM_ACCESS,
			GROVE_TRAM_ACCESS_W),
		_plan_run(&"grove_frontier_handoff", GROVE_FRONTIER_HANDOFF,
			GROVE_FRONTIER_HANDOFF_W),
		_plan_run(&"grove_photo", GROVE_PHOTO_SPUR,
			GROVE_PHOTO_SPUR_W),
	]


## Every walkway as a flat list of (from, to) segment pairs, which is what a
## line-drawing consumer actually wants. Built rather than stored so the
## polylines above stay the single description.
static func walkway_segments() -> Array:
	var out := []
	for entry in walkway_runs():
		var run: Array = entry["points"]
		for i in run.size() - 1:
			out.append({"id": entry["id"], "from": run[i], "to": run[i + 1],
				"width": entry["width"]})
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
## to no section — the three passages that bend and stop, which is the set a
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
	# Package 04E pulls this corner's inner face back to make the approved P5
	# performance pocket. Its outer face and the Plaza boundary do not move.
	{"at": Vector2(-36.45, -43.5), "half": Vector2(11.55, 3.5)},
	{"at": Vector2(2.55, -41.5), "half": Vector2(11.45, 5.5)},
	{"at": Vector2(25.0, -41.5), "half": Vector2(11.0, 5.5)},
	# east side, inner face x = 36
	{"at": Vector2(41.5, -41.7), "half": Vector2(5.5, 6.3)},
	{"at": Vector2(41.5, -27.4), "half": Vector2(5.5, 8.0)},
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
	# Cut back at x 43 for the SE gateway forecourt. Its old east end at x 48
	# projected 1.8m into the thirteen-metre opening, invisible on a centreline
	# walk but a literal wall across the southern traffic lane.
	{"at": Vector2(35.0, 41.5), "half": Vector2(8.0, 5.5)},
	# west side, inner face x = -33, set in for the overlook terrace
	# The former 25m west range occupied P5's stage. Its retained north end now
	# terminates at the performance pocket; the stage and cue yard close the gap.
	{"at": Vector2(-38.5, -44.0), "half": Vector2(5.5, 4.0)},
	{"at": Vector2(-38.5, 14.5), "half": Vector2(5.5, 10.5)},
	{"at": Vector2(-38.5, 36.5), "half": Vector2(5.5, 11.5)},
	{"at": Vector2(-38.5, -8.0), "half": Vector2(5.5, 1.5)},
	{"at": Vector2(-38.5, 4.0), "half": Vector2(5.5, 1.5)},
	# inside
	{"at": CLOCK_TOWER_AT, "half": Vector2(2.8, 2.8)},
	{"at": PHOTO_HUT_AT, "half": Vector2(4.0, 3.25)},
	{"at": Vector2(-42.0, -32.0), "half": Vector2(6.2, 6.2)},
	{"at": Vector2(-53.0, -39.0), "half": Vector2(5.0, 3.0)},
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


## Clearance reserved for removable or scheduled Plaza program that should not
## become a permanent crowd obstacle. P5's event lawn belongs here rather than
## in `PLAZA_MASSES`: putting it in the structural obstacle list would make the
## audience entry, release and photographer route invalidate themselves, while
## omitting it lets the deterministic tree and furniture scatter grow straight
## through the 96-chair event field.
static func program_furnishing_clearance(p: Vector2) -> float:
	var best := 1e9
	for site in REBUILD_ATTRACTION_SITES:
		if StringName(site["id"]) != &"P5":
			continue
		var at: Vector2 = site["audience"]
		var radii: Vector2 = site["audience_radii"] + Vector2.ONE * 0.8
		var theta := deg_to_rad(float(site["audience_rotation"]))
		var u := Vector2(cos(theta), sin(theta))
		var v := Vector2(-sin(theta), cos(theta))
		var delta := p - at
		var local := Vector2(delta.dot(u), delta.dot(v))
		var normalized := Vector2(local.x / radii.x, local.y / radii.y)
		var scale := normalized.length()
		if scale <= 1.0:
			return 0.0
		# Distance to the ellipse along this ray. Exact Euclidean ellipse
		# distance is unnecessary for scatter rejection; this is continuous,
		# conservative at the boundary and expressed in metres.
		best = minf(best, local.length() * (scale - 1.0) / scale)
		break
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
		minf(mass_clearance(p),
			minf(program_furnishing_clearance(p),
				p.length() - FOUNTAIN_RADIUS)))


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
		if program_furnishing_clearance(p) < clear:
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
