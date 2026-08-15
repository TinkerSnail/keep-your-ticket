class_name Guest
extends AnimatableBody3D

## A park guest: walks the plaza's path graph, looks at things, and reacts to
## having a camera pointed at them.
##
## Bodies and placement are generated. `tools/gen_crowd.gd` writes the scene
## this lives in, `scenes/world/plaza_crowd.tscn` — a guest edited by hand in
## the editor is lost on the next regeneration. Behaviour lives here so that it
## stays hand-editable while the crowd around it is disposable.
##
## Attention is a priority stack rather than a state machine. Several things can
## be worth looking at at once, the highest-priority one wins, and the head only
## turns as far as a neck goes — past that the guest either turns their body or
## gives up and faces forward. At this fidelity what a guest is looking at is
## the whole of their performance, so it is where the detail went.
##
## A guest is not always in the park. The crowd admits and sends home whole
## groups against the hour, so the same body is a different visitor at eleven
## and at eight. Everything below the `-- coming and going --` line is what that
## costs a guest: somewhere to be parked, a way in and a way out, and sitting
## down as something they do rather than something they were built as.

enum Attention { FORWARD, POI, COMPANION, GAZE, CAMERA, POSE }

## What to do on reaching the last waypoint. Arriving and leaving are the same
## walk with a different end to it.
enum Then { NOTHING, SIT, WANDER, SLEEP }

## How a guest takes being photographed. Rolled once per camera raise, against
## the guest's own curiosity and shyness, so the same person tends to respond
## the same way twice — but not always, because people don't.
enum Reaction { OBLIVIOUS, GLANCE, HOLD, AVOID }

## Physics layers, named in project settings so the editor's layer picker reads
## as words rather than as numbers. The distinction exists because a camera arm
## has to be shoved aside by a building and walk straight through a crowd.
const LAYER_WORLD := 1
const LAYER_PEOPLE := 2

const ARRIVE_DISTANCE := 0.35
const SEPARATION_RADIUS := 0.95
const SEPARATION_STRENGTH := 1.4

## How much room a guest leaves the player, and how hard they insist on it.
##
## Wider than they give each other, because a guest who merely stops overlapping
## the player still leans on them, and leaning is what carried the photographer
## across the plaza. The clearance is what does the work: past about 0.6m the
## player's capsule has nothing to depenetrate from, so 1.25 is margin rather
## than a limit.
##
## The strength is deliberately low, and it was 2.2 first. At that value a guest
## the player walks into darts away at over twice their own walking speed, which
## reads as a flinch. Measured at 1.0, 1.3 and 2.2 against a full plaza: all
## three hold the drift at zero, so the gentlest that keeps its margin wins.
const PLAYER_CLEARANCE := 1.25
const PLAYER_AVOIDANCE := 1.3

## Where a guest who is not in the park is parked. Far under the world, so that
## a raycast, a nearest-guest search or a stray bit of physics cannot find one.
const DORMANT_Y := -400.0

const HEAD_YAW_LIMIT := deg_to_rad(78.0)
const HEAD_PITCH_LIMIT := deg_to_rad(32.0)
const HEAD_TURN_RATE := 7.0

## Beyond this the guest turns their whole body rather than craning, but only
## when stopped. Walking guests just let the target go.
const BODY_TURN_THRESHOLD := deg_to_rad(60.0)

const CAMERA_NOTICE_RANGE := 13.0
const GLANCE_SECONDS := Vector2(0.9, 2.1)

## Nobody looks up at the same instant. Each guest has their own beat before
## they react, shorter the closer the camera is, which is what turns the
## crowd's response into a ripple rather than a flinch.
const NOTICE_DELAY := Vector2(0.1, 0.85)

## How near the person who turned has to be to be worth turning about. Much
## smaller than the camera's own range: this is peripheral movement, not a man
## with a camera across the plaza.
const CONTAGION_NEIGHBOUR := 5.5
## Past this from the player, following a neighbour's gaze finds nothing worth
## reacting to. The chain can outrun the camera's notice range, but not far.
const CONTAGION_PLAYER_RANGE := CAMERA_NOTICE_RANGE * 1.6
## How often a guest who has not noticed yet checks whether anyone near them
## just did.
const CONTAGION_SCAN := 0.3
const CONTAGION_DELAY := Vector2(0.2, 0.75)
## Movement is caught at the edge of vision, so the arc is wide — but it is not
## the whole circle, and someone turning behind your back goes unseen unless
## they are one of yours.
const NEIGHBOUR_ARC := deg_to_rad(100.0)

## Where the eye goes first: to the person who turned, not to whatever they
## turned at. Following the gaze before finding the camera is the whole of what
## makes a chain legible from outside it — without it, contagious noticing is
## indistinguishable from everyone happening to notice at once.
const GAZE_FOLLOW := Vector2(0.35, 0.8)

const POSE_HOLD := 7.0
## The pose does not end, it comes apart. Each guest drops out somewhere in
## this window, so a group unravels raggedly instead of switching off.
const POSE_DECAY := Vector2(1.5, 4.5)
const POSE_GATHER_DISTANCE := 2.6

## Set by the generator. Everything about a guest that varies is data.
@export var walk_speed := 1.25
@export var rng_seed := 0
@export var curiosity := 0.5
@export var shyness := 0.25
## Where this guest belongs while they are in the park. `INF` is somebody who
## came to walk about; anything else is a seat, and they walk to it and sit
## down. Sitting used to be a fact about a body and is now something a visit
## does, which is the whole difference between a cafe that is always half full
## and a cafe that fills up at lunch.
@export var seat_at := Vector3.INF
@export var seat_yaw := 0.0
## Top of whatever they are sitting on. Benches and cafe chairs differ, and a
## guest hovering two centimetres above a seat is the first thing anyone sees.
@export var seat_height := 0.51
## Which population this guest counts towards — `wander`, `bench` or `cafe`.
## Each has its own curve across the day, so the seats do not simply track the
## crowd: the tables fill at meals whether or not the plaza is busy.
@export var group_kind := "wander"
## A guest who came in a wheelchair.
##
## **Seated and moving at once, which nothing here modelled.** `_seated` meant
## "not going anywhere" — the fold, the stop and the bench were one state,
## because on foot they always arrive together. A wheelchair separates them: the
## body is folded from the moment it is built and never unfolds, and the stopping
## is the only part of sitting that a seat still means. So `_sit` and `_stand`
## keep the stopping and skip the pose, and the walk cycle is replaced rather
## than suppressed — the wheels turn on ground crossed and the arms push.
##
## The fold itself is baked by `tools/gen_crowd.gd` rather than applied here,
## because the angle the knees hold is what puts the feet on the footplate and
## the footplate is part of the chair. One of them has to own it and it is the
## one that knows where the chair is.
@export var wheelchair := false
## Rolling radius of the driven wheels, so a turn is ground crossed rather than a
## rate somebody picked. Set by the generator alongside the chair — or the
## stroller — it belongs to. One property for both, because to the animator they
## are the same thing: the pair that is turned by the ground going past.
@export var wheel_radius := 0.3
## A guest pushing a stroller, twin buggy or pram.
##
## **The opposite shape to `wheelchair`, and deliberately not folded into it.**
## There, the body is seated and moving at once and the walk cycle had to be
## replaced. Here the person walks perfectly normally and the thing they are
## pushing is a prop that rolls along in front of them — so this keeps the
## ordinary walk cycle and changes only what the arms do. Both hands go to the
## handle and stay there, which is the whole of what distinguishes pushing from
## walking at this fidelity.
##
## The child in it is geometry rather than a guest. A toddler strapped into a
## moving buggy is seated *and* moving — precisely the case the wheelchair had to
## decompose `_seated` to handle — and unlike a wheelchair user it has no
## independent movement to model at all. So it does not route, does not collide,
## is not in the headcount and cannot be asked to pose. The one thing it does is
## turn its head, and that is driven from here.
@export var stroller := false
## How far forward the arms are held to reach the handle, in radians. Solved by
## the generator against the bar it built, because these arms have no elbow to
## take up a difference and a typed angle puts the hands through the handle.
@export var push_arm := 0.0
## Followers shadow their group's leader instead of routing for themselves,
## which is what makes a family read as a family rather than four strangers
## on the same heading.
@export var leader_path := NodePath()
@export var follow_offset := Vector3.ZERO
## Who a guest arrived with. The crowd turns this into the list of people they
## look at while stopped — a group standing in silence all facing the same way
## is the thing that makes a crowd look wrong.
@export var group_id := 0

var _crowd: Node = null
var _rng := RandomNumberGenerator.new()

var _body: Node3D
var _head_pivot: Node3D
var _arm_l: Node3D
var _arm_r: Node3D
var _hip_l: Node3D
var _hip_r: Node3D
var _knee_l: Node3D
var _knee_r: Node3D
var _body_rest_y := 0.0
## The chair, when there is one. The rear wheels and the casters are pivots the
## parts hang off, so turning one is a rotation and not a rebuild.
var _wheel_l: Node3D
var _wheel_r: Node3D
var _caster_l: Node3D
var _caster_r: Node3D
var _caster_ratio := 1.0
## The buggy, when there is one, and where it sits while it is being pushed —
## kept so that parking it beside a seat is reversible without recomputing it.
var _stroller_node: Node3D
var _stroller_home := Transform3D.IDENTITY
## The head pivots of whoever is riding in it. Empty for a pram, whose occupant
## is lying down and has no head to track anybody with.
var _passenger_heads: Array[Node3D] = []

var _leader: Guest = null
var _companions: Array[Guest] = []

var _route: PackedInt32Array = PackedInt32Array()
var _leg := 0
var _wait := 0.0
var _wander := Vector3.ZERO

## Somewhere to be that is not the graph: the walk in from off-stage, the walk
## out to it, and the last few metres to a seat. Takes precedence over the
## route, because a guest on their way home is not wandering.
var _waypoints: Array[Vector3] = []
var _then := Then.NOTHING
var _live := false
var _seated := false
var _stand_rest_y := 0.0
## Reached the end of the walk out and waiting to be put away. The crowd does
## the putting away, because whether it is safe to vanish is a fact about where
## the player is looking and the guest has no business knowing that.
var _off_stage := false

var _phase := 0.0
var _stride := 0.0
var _speed := 0.0
var _idle_phase := 0.0
## The push stroke, which is slower than the wheel and is not a multiple of it —
## a hand catches the rim, pushes through, and comes back for another. Tying the
## arms to `_phase` would have them stroking once per revolution forever.
var _push_phase := 0.0
## How far the wheels have turned, kept off `_phase` on purpose.
##
## A wheelchair user's legs do not walk, so the chair could have borrowed the
## walk cycle's accumulator. Somebody pushing a buggy is walking *and* rolling at
## once, and sharing one counter turned the wheels at the leg cadence — about
## four times too fast, and wrong at exactly the distance the player photographs
## a family from.
var _roll_phase := 0.0

var _attention := Attention.FORWARD
var _look_point := Vector3.ZERO
var _look_weight := 0.0
var _head_yaw := 0.0
var _head_pitch := 0.0

var _reaction := Reaction.OBLIVIOUS
var _reaction_timer := 0.0
var _was_camera_raised := false

## Committed to a reaction, oblivious or otherwise, and done deciding. Until
## this is true the guest is still catchable off a neighbour.
var _noticed := false
var _notice_timer := 0.0
var _direct_pending := false
var _catch_from: Guest = null
## Alerters already shrugged off. Each one gets a single roll — without this a
## guest re-rolls against the same neighbour every scan and the whole plaza
## notices eventually, which is exactly the crowd-wide flinch this avoids.
var _declined: Array[int] = []

var _gaze_at: Guest = null
var _gaze_timer := 0.0

var _posing := false
var _pose_timer := 0.0
var _pose_anchor := Vector3.ZERO
## Some guests — usually the small ones — do not comply, and that is a better
## photograph than the one that was asked for.
var _pose_complies := true


func _ready() -> void:
	add_to_group("npc")
	add_to_group("guest")

	_rng.seed = rng_seed if rng_seed != 0 else hash(name)

	_body = $body
	_head_pivot = $body/neck/head_pivot
	_arm_l = $body/arm_l
	_arm_r = $body/arm_r
	_hip_l = $body/hip_l
	_hip_r = $body/hip_r
	_knee_l = $body/hip_l/knee_l
	_knee_r = $body/hip_r/knee_r
	_stand_rest_y = _body.position.y
	_body_rest_y = _stand_rest_y

	if wheelchair:
		_mount_wheels("chair")
	elif stroller:
		_mount_wheels("stroller")
		_stroller_node = get_node_or_null("stroller") as Node3D
		if _stroller_node != null:
			_stroller_home = _stroller_node.transform
		# However many seats the chassis came with. A pram emits none — its
		# occupant is lying down — so this finds nothing and the passenger pass
		# does nothing, which is the intended behaviour rather than a gap.
		for i in MAX_PASSENGERS:
			var pivot := get_node_or_null("stroller/kid_%d/head_pivot" % i) as Node3D
			if pivot != null:
				_passenger_heads.append(pivot)

	# An AnimatableBody3D syncing to physics takes its transform from the
	# physics server, and a write from outside the physics step is silently
	# thrown away — not warned about, not clamped, just gone. Guests move by
	# adding to `global_position` inside `_physics_process`, which is why this
	# never came up until they had to be teleported: put to bed off-stage,
	# fetched back to the threshold, dropped onto a seat.
	#
	# Verified rather than reasoned about, because the first two explanations
	# for it were both wrong. Setting the position on a live, fully enabled
	# guest and reading it back on the same line returns the old value.
	#
	# What it costs: a guest walking into a standing player no longer shoves
	# them aside, because that shove was the physics server moving the body. It
	# still blocks them — collision is unaffected — and being shoved by a crowd
	# was never something anybody asked for.
	sync_to_physics = false

	_idle_phase = _rng.randf() * TAU
	_wander = Vector3(_rng.randfn(0.0, 0.5), 0.0, _rng.randfn(0.0, 0.5))
	_pose_complies = _rng.randf() > 0.16

	_crowd = _find_crowd()
	if _crowd != null and _crowd.has_method("register"):
		_crowd.register(self)

	call_deferred("_resolve_group")

	# Nobody is in the park until the clock says so. The crowd runs its first
	# sync in its own `_ready`, which is after every guest's, so a guest that
	# belongs to the opening hour is put back on stage before the first frame
	# and never flickers.
	_go_dormant()


## **Up the parent chain, not out to the group.**
##
## This asked the tree for the first node in the `crowd` group, which was right
## while there was one crowd and became silently wrong the moment there were two.
## `ParkSections._swap` adds the incoming section's scenes *before* it frees the
## outgoing one — deliberately, so the player is never moved onto a floor that
## has already gone — which means every boardwalk guest ran its `_ready` with the
## plaza's crowd still standing, registered with it, and was thrown away with it
## seconds later. The boardwalk mounted with a roster of nobody.
##
## Nothing errored. The section had a crowd node, a graph, a day and fifty-seven
## guest bodies in the tree, and every one of them was dormant forever.
##
## A guest is a child of its own crowd, so the answer was always here rather than
## in a group. The group lookup stays as a fallback for a harness that parents
## guests somewhere else.
## How many seats any chassis in `gen_crowd.gd` has. A bound rather than a fact —
## it only decides how far to look for pivots that may not be there.
const MAX_PASSENGERS := 2


## The four wheel pivots, whichever thing they belong to.
##
## A wheelchair and a stroller have the same two-and-two arrangement — a driven
## pair, and a smaller pair that trails — so they share the lookup, the ratio and
## the spin rather than growing a second set that drifts from the first. Both are
## siblings of the body and not children of it: the body bobs and sways, and
## anything on wheels underneath it must not.
##
## The front radius is read off the pivot's own height, because a pivot sits at
## its axle and an axle sits one radius off the ground. That saves the generator
## having to export a second number that could disagree with the geometry.
func _mount_wheels(root: String) -> void:
	_wheel_l = get_node_or_null(root + "/wheel_l")
	_wheel_r = get_node_or_null(root + "/wheel_r")
	_caster_l = get_node_or_null(root + "/caster_l")
	_caster_r = get_node_or_null(root + "/caster_r")
	if _caster_l != null and _caster_l.position.y > 0.001:
		_caster_ratio = wheel_radius / _caster_l.position.y


## Swing the buggy to the pusher's side, or put it back.
##
## Left where it was, a parked stroller stands in the table: a seated body is
## most of a metre shorter than the thing it was pushing, and the chassis does
## not fold. Turned out and set beside the chair it reads as what anybody does
## before they sit down.
##
## The side is taken from `rng_seed` rather than rolled, so a guest who sits,
## stands and sits again parks on the same side both times.
func _park_stroller(parked: bool) -> void:
	if _stroller_node == null:
		return
	if not parked:
		_stroller_node.transform = _stroller_home
		return
	var side := 1.0 if (rng_seed & 1) == 0 else -1.0
	_stroller_node.position = _stroller_home.origin + Vector3(side * 0.62, 0.0, 0.15)
	_stroller_node.rotation.y = side * 1.35


func _find_crowd() -> Node:
	var at: Node = get_parent()
	while at != null:
		if at.has_method("register") and at.is_in_group("crowd"):
			return at
		at = at.get_parent()
	return get_tree().get_first_node_in_group("crowd")


func _exit_tree() -> void:
	if _crowd != null and _crowd.has_method("unregister"):
		_crowd.unregister(self)


func _resolve_group() -> void:
	if not leader_path.is_empty():
		_leader = get_node_or_null(leader_path) as Guest
	if _crowd != null:
		_companions.assign(_crowd.companions(self))


# --- coming and going -------------------------------------------------------


func has_seat() -> bool:
	return seat_at != Vector3.INF


func is_live() -> bool:
	return _live


## Finished the walk out and standing off-stage, waiting to be put away.
func is_off_stage() -> bool:
	return _off_stage


## Put down on the floor of whatever section this guest belongs to.
##
## The three places that teleport a guest — spawning at opening, arriving from
## off-stage, and the last snap onto a seat — all wrote `Vector3(p.x, 0.0, p.z)`,
## which was the plaza's floor written down as a literal three times. It was
## invisible for as long as the plaza was the only section anybody stood in, and
## the boardwalk is six metres down: every guest that spawned or arrived down
## there was placed six metres above the promenade, in the air, and then walked
## about up there.
##
## The y comes off the point now, and every point handed in already carries the
## right one — the graph's nodes, the hold point and the seats are all generated
## at the section's own floor. Dropping it was never buying anything.
func _on_ground(at: Vector3) -> Vector3:
	return at


## Already in the park when the clock is read — the first frame of a session, or
## a dev jump to an hour. No walk in: a plaza at opening should have people
## standing about in it, not a queue of them filing through the gate one at a
## time while the player watches.
func spawn_at(at: Vector3) -> void:
	_wake()
	global_position = _on_ground(at)
	if has_seat():
		rotation.y = seat_yaw
		_sit()
		return
	rotation.y = _rng.randf() * TAU
	_route = PackedInt32Array()
	# Staggered, or every wanderer in the plaza sets off on the same frame.
	_wait = _rng.randf_range(0.0, 5.0)


## Walk in. `via` ends wherever this guest belongs — a seat, or the threshold
## itself for somebody who came to walk about and will route on from there.
func arrive_from(hold: Vector3, via: Array[Vector3]) -> void:
	_wake()
	global_position = _on_ground(hold)
	_waypoints = via.duplicate()
	_then = Then.SIT if has_seat() else Then.WANDER
	if not _waypoints.is_empty():
		var heading := _waypoints[0] - global_position
		heading.y = 0.0
		if heading.length_squared() > 0.0001:
			rotation.y = atan2(-heading.x, -heading.z)


## Go home. Whoever is sitting stands up first, which is most of what makes the
## cafe emptying in the evening read as people leaving rather than as furniture
## being cleared.
func depart_via(via: Array[Vector3]) -> void:
	if not _live:
		return
	_stand()
	_posing = false
	_route = PackedInt32Array()
	_wait = 0.0
	_waypoints = via.duplicate()
	_then = Then.SLEEP


## Followers have no waypoints of their own — they shadow their leader through
## the gate the same way they shadow them everywhere else. But a follower whose
## leader has gone off-stage has nothing left to follow, so the crowd asks them
## directly whether they have caught up.
##
## Generous, and it has to be: the guest walked to a point scattered several
## metres off `hold`, and a follower stops a stride and a half behind that
## again. Measured tightly against `hold` itself this is never true and nobody
## ever goes home. Precision buys nothing here — the nearest thing the player
## can stand on is eighteen metres away.
const HOME_RADIUS := 8.0


func is_home(hold: Vector3) -> bool:
	if _off_stage:
		return true
	var away := global_position - hold
	away.y = 0.0
	return away.length() < HOME_RADIUS


func go_dormant() -> void:
	_go_dormant()


func _wake() -> void:
	if _live:
		return
	_live = true
	_off_stage = false
	visible = true
	process_mode = Node.PROCESS_MODE_INHERIT
	# People, not architecture. Set here rather than in the generator because a
	# guest is not the only thing that needs to be distinguishable from a wall,
	# and because it would otherwise be one more thing lost to a regeneration.
	# Still collides with the world, with the player, and with other guests —
	# only the things that ask specifically for architecture see the difference.
	collision_layer = LAYER_PEOPLE
	collision_mask = LAYER_WORLD | LAYER_PEOPLE
	if _crowd != null and _crowd.has_method("set_live"):
		_crowd.set_live(self, true)


func _go_dormant() -> void:
	_live = false
	_off_stage = false
	visible = false
	process_mode = Node.PROCESS_MODE_DISABLED
	# A disabled node keeps its collision shapes. Without this a whole day's
	# worth of guests who have gone home are still standing in the street,
	# invisibly, in the way.
	collision_layer = 0
	collision_mask = 0
	# Under the world rather than at the threshold, so there is no pile of
	# nobody for a stray query to find.
	global_position = Vector3(0.0, DORMANT_Y, 0.0)

	_stand()
	_waypoints.clear()
	_then = Then.NOTHING
	_route = PackedInt32Array()
	_leg = 0
	_wait = 0.0
	_posing = false
	_pose_timer = 0.0
	_speed = 0.0
	_clear_notice()
	_was_camera_raised = false

	if _crowd != null and _crowd.has_method("set_live"):
		_crowd.set_live(self, false)


func _finish_waypoints() -> void:
	match _then:
		Then.SIT:
			# Snapped, because arriving is `ARRIVE_DISTANCE` and a third of a
			# metre off a bench is sitting on the arm of it. It is the last
			# frame of a walk, so it reads as settling rather than as a jump.
			global_position = _on_ground(seat_at)
			rotation.y = seat_yaw
			_sit()
		Then.WANDER:
			_route = PackedInt32Array()
			_wait = _rng.randf_range(0.0, 1.5)
		Then.SLEEP:
			# Standing off-stage. The crowd decides when it is safe to vanish.
			_off_stage = true
	_then = Then.NOTHING


func _sit() -> void:
	_seated = true
	_waypoints.clear()
	_route = PackedInt32Array()
	_wait = 0.0
	# A wheelchair user brought their seat with them. What a bench or a cafe
	# table means for them is a place to stop and a direction to face — the fold
	# is already held and the seat height is already theirs, and writing either
	# one would drop them through the chair onto the bench they pulled up beside.
	if wheelchair:
		return
	# The buggy is parked, not abandoned. Left where it was it would stand in the
	# table — a seated body is most of a metre shorter than the thing it was
	# pushing, and the chassis does not fold.
	_park_stroller(true)
	_body_rest_y = seat_height
	_apply_seated_pose()


func _stand() -> void:
	if not _seated:
		return
	_seated = false
	# Nothing to stand up out of, and nothing to straighten. The stopping was
	# the whole of the sitting, and `_animate_wheels` drives the arms from here
	# whether the chair is moving or not.
	if wheelchair:
		return
	_park_stroller(false)
	_body_rest_y = _stand_rest_y
	_body.position.y = _body_rest_y
	# Straightened rather than left folded. `_animate` drives the limbs from
	# here every frame, but it lerps `_stride` up from zero, so a guest who
	# stood up out of a fold would take their first two steps still sitting.
	_hip_l.rotation.x = 0.0
	_hip_r.rotation.x = 0.0
	_knee_l.rotation.x = 0.0
	_knee_r.rotation.x = 0.0
	_arm_l.rotation.x = 0.0
	_arm_r.rotation.x = 0.0
	_phase = 0.0
	_stride = 0.0


func _physics_process(delta: float) -> void:
	_update_reaction(delta)
	_update_pose(delta)

	var moved := 0.0
	if not _seated:
		moved = _update_movement(delta)
		_speed = moved / maxf(delta, 0.0001)

	_update_attention()
	_update_head(delta)
	_animate(delta, moved)


# --- movement ---------------------------------------------------------------


## Returns distance covered this frame, which is what drives the walk cycle —
## the legs are tied to ground actually crossed rather than to a clock, so a
## guest slowed by the crowd around them does not skate.
func _update_movement(delta: float) -> float:
	var before := global_position

	if _wait > 0.0 and not _posing:
		_wait -= delta
		_apply_separation(delta)
		return (global_position - before).length()

	var target := _movement_target()
	if target == Vector3.INF:
		_apply_separation(delta)
		return (global_position - before).length()

	var to_target := target - global_position
	to_target.y = 0.0
	var distance := to_target.length()

	var stop_distance := ARRIVE_DISTANCE
	if _leader != null and _waypoints.is_empty():
		# Followers keep station loosely. Holding a precise offset looks like
		# formation marching; letting them drift and catch up looks like people.
		stop_distance = 0.55
	if _posing:
		stop_distance = 0.4

	if distance > stop_distance:
		var direction := to_target / distance
		var step := minf(walk_speed * delta, distance - stop_distance * 0.5)
		global_position += direction * step
		_face_direction(direction, delta, 6.0)
	elif not _waypoints.is_empty():
		_waypoints.remove_at(0)
		if _waypoints.is_empty():
			_finish_waypoints()
	elif _leader == null and not _posing:
		_advance_route()

	_apply_separation(delta)
	return (global_position - before).length()


func _movement_target() -> Vector3:
	if _posing:
		return _pose_anchor

	# Gone home, and standing off-stage until the crowd puts them away. Without
	# this they finish the walk out, find themselves with no waypoints and no
	# route, ask for a new one, and wander straight back into the park — which
	# is what froze the first run of the day test with nineteen people still
	# inside at eleven at night.
	if _off_stage:
		return Vector3.INF

	# Arriving, leaving, or crossing the last few metres to a seat. A guest on
	# their way somewhere specific is not wandering, and a follower on the way
	# in walks the way in rather than after whoever happens to be ahead.
	if not _waypoints.is_empty():
		return _waypoints[0]

	if _leader != null:
		if not is_instance_valid(_leader):
			_leader = null
		else:
			var basis := Basis(Vector3.UP, _leader.rotation.y)
			return _leader.global_position + basis * follow_offset

	if _route.is_empty():
		_request_route()
		if _route.is_empty():
			return Vector3.INF

	if _leg >= _route.size():
		return Vector3.INF

	if _crowd == null:
		return Vector3.INF
	return _crowd.node_position(_route[_leg]) + _wander


func _advance_route() -> void:
	_leg += 1
	if _leg < _route.size():
		# A short beat at intermediate nodes and a real stop at the end, so the
		# crowd has people standing in it and not only people crossing it.
		if _rng.randf() < 0.25:
			_wait = _rng.randf_range(1.5, 5.0)
		return
	_wait = _rng.randf_range(2.5, 9.0)
	_route = PackedInt32Array()


func _request_route() -> void:
	if _crowd == null:
		return
	_route = _crowd.route_from(global_position, _rng.randi())
	_leg = 0
	_wander = Vector3(_rng.randfn(0.0, 0.45), 0.0, _rng.randfn(0.0, 0.45))


## Guests do not path around each other, they just refuse to overlap. At this
## density that is indistinguishable from the real thing and costs nothing.
##
## The player counts. They did not until somebody played it: guests separated
## from each other and walked straight through the photographer, and since a
## guest is moved by assignment while the player is a `CharacterBody3D` that
## depenetrates, every one of those pass-throughs shoved the player sideways.
## Standing still in the plaza at three in the afternoon carried them five
## metres a minute, and twelve if they were standing in the gap at the south
## where arriving groups funnel through. Long enough at the wrong spot and the
## player was pushed clean out of the plaza and down the entrance street.
##
## That is disqualifying rather than untidy. Standing still and waiting for a
## shot is most of what the job is.
func _apply_separation(delta: float) -> void:
	if _crowd == null:
		return
	var push := Vector3.ZERO
	# Not `_crowd.guests`. Asking the whole live list here is asking every pair
	# every frame, and measured at a cast of 150 that one loop was 87% of what
	# the crowd cost — 21,904 distance checks a frame for a plaza where nobody
	# can be pushed by anyone more than a metre away. The crowd buckets everybody
	# by the ground they are standing on once a frame and this asks for the nine
	# squares around it.
	#
	# The array is the crowd's own and is refilled on the next call, so it is
	# read here and never kept.
	var others: Array = _crowd.neighbours(global_position)
	for entry in others:
		var other := entry as Node3D
		if other == self or other == null or not is_instance_valid(other):
			continue
		var away := global_position - other.global_position
		away.y = 0.0
		var d := away.length()
		if d > SEPARATION_RADIUS or d < 0.001:
			continue
		push += (away / d) * (1.0 - d / SEPARATION_RADIUS)

	if _crowd.player_present:
		var at: Vector3 = _crowd.player_position
		var off := global_position - at
		off.y = 0.0
		var pd := off.length()
		# A wider berth than they give each other, because that is what people
		# do with a stranger — and because the margin is what decides whether
		# the crowd parts around the player or merely stops overlapping them.
		if pd < PLAYER_CLEARANCE and pd > 0.001:
			push += (off / pd) * (1.0 - pd / PLAYER_CLEARANCE) * PLAYER_AVOIDANCE

	if push == Vector3.ZERO:
		return
	global_position += push * SEPARATION_STRENGTH * delta


func _face_direction(direction: Vector3, delta: float, rate: float) -> void:
	if direction.length_squared() < 0.0001:
		return
	var wanted := atan2(-direction.x, -direction.z)
	rotation.y = lerp_angle(rotation.y, wanted, rate * delta)


# --- being photographed -----------------------------------------------------


func _update_reaction(delta: float) -> void:
	if _reaction_timer > 0.0:
		_reaction_timer -= delta
	if _gaze_timer > 0.0:
		_gaze_timer -= delta

	if _crowd == null:
		return

	var raised: bool = _crowd.camera_raised
	if raised and not _was_camera_raised:
		_begin_notice()
	elif not raised and _was_camera_raised:
		_clear_notice()
	_was_camera_raised = raised

	if raised and not _noticed:
		_advance_notice(delta)


func _begin_notice() -> void:
	_clear_notice()
	var distance := global_position.distance_to(_crowd.player_position)
	_direct_pending = distance <= CAMERA_NOTICE_RANGE
	if not _direct_pending:
		# Too far to see it for themselves, but not too far to see someone else
		# see it. Start scanning on a scattered beat.
		_notice_timer = _rng.randf_range(0.0, CONTAGION_SCAN)
		return
	# The people the camera is pointed at look up first.
	var closeness := 1.0 - clampf(distance / CAMERA_NOTICE_RANGE, 0.0, 1.0)
	_notice_timer = lerpf(NOTICE_DELAY.y, NOTICE_DELAY.x, closeness) * _rng.randf_range(0.6, 1.4)


func _clear_notice() -> void:
	_reaction = Reaction.OBLIVIOUS
	_reaction_timer = 0.0
	_noticed = false
	_direct_pending = false
	_notice_timer = 0.0
	_catch_from = null
	_declined.clear()
	_gaze_at = null
	_gaze_timer = 0.0


## One step of deciding whether to notice: the guest's own look first, then a
## standing watch on the people around them for as long as the camera is up.
func _advance_notice(delta: float) -> void:
	_notice_timer -= delta
	if _notice_timer > 0.0:
		return

	if _direct_pending:
		_direct_pending = false
		_notice_timer = _rng.randf_range(0.0, CONTAGION_SCAN)
		if _rolls_direct():
			_commit_notice(null)
		return

	if _catch_from != null:
		var source := _catch_from
		_catch_from = null
		_notice_timer = CONTAGION_SCAN
		if is_instance_valid(source):
			_commit_notice(source)
		return

	# Set before the scan, which overwrites it with the catch delay on a hit.
	_notice_timer = CONTAGION_SCAN
	_scan_for_alert()


## Nearer guests notice more reliably. The base is deliberately low — most of a
## distant guest's chance of clocking the camera now comes from the person next
## to them rather than from the camera itself.
func _rolls_direct() -> bool:
	var distance := global_position.distance_to(_crowd.player_position)
	if distance > CAMERA_NOTICE_RANGE:
		return false
	var closeness := 1.0 - clampf(distance / CAMERA_NOTICE_RANGE, 0.0, 1.0)
	return _rng.randf() < 0.12 + closeness * (0.38 + curiosity * 0.5)


func _scan_for_alert() -> void:
	if _posing:
		return
	var source := _crowd.fresh_alert_near(self, CONTAGION_NEIGHBOUR, _declined) as Guest
	if source == null:
		return
	if not _catches_from(source):
		_declined.append(source.get_instance_id())
		return
	_catch_from = source
	_notice_timer = _rng.randf_range(CONTAGION_DELAY.x, CONTAGION_DELAY.y)


func _catches_from(source: Guest) -> bool:
	if global_position.distance_to(_crowd.player_position) > CONTAGION_PLAYER_RANGE:
		return false

	var to_source := source.global_position - global_position
	to_source.y = 0.0
	var distance := to_source.length()
	if distance < 0.01:
		return false

	# You are aware of the people you came with whichever way they are standing.
	# A stranger has to turn where you can see them turn.
	var companion := source in _companions
	if not companion and not _sees_direction(to_source / distance):
		return false

	var closeness := 1.0 - clampf(distance / CONTAGION_NEIGHBOUR, 0.0, 1.0)
	var chance := (0.16 + closeness * 0.34) * (0.7 + curiosity * 0.6)
	if companion:
		chance *= 1.9
	return _rng.randf() < chance


func _sees_direction(direction: Vector3) -> bool:
	var forward := -global_transform.basis.z
	forward.y = 0.0
	if forward.length_squared() < 0.0001:
		return false
	return forward.normalized().angle_to(direction) < NEIGHBOUR_ARC


## Settle on a reaction and become news yourself. How a guest takes it is their
## own — shyness and curiosity decide it — whether they came to it by looking
## up or by watching a friend look up.
func _commit_notice(source: Guest) -> void:
	_noticed = true

	var gaze := 0.0
	if source != null:
		gaze = _rng.randf_range(GAZE_FOLLOW.x, GAZE_FOLLOW.y)
		_gaze_at = source
		_gaze_timer = gaze

	if _rng.randf() < shyness:
		_reaction = Reaction.AVOID
	elif _rng.randf() < curiosity * 0.55:
		_reaction = Reaction.HOLD
	else:
		_reaction = Reaction.GLANCE
		# The glance is at the camera, so it starts once the eye has arrived
		# there. Otherwise a caught guest spends their whole glance looking at
		# their friend and never gets to the lens.
		_reaction_timer = gaze + _rng.randf_range(GLANCE_SECONDS.x, GLANCE_SECONDS.y)

	if _crowd != null and _crowd.has_method("report_notice"):
		_crowd.report_notice(self)


## Asked to pose. The guest does not stop being a person about it — they walk
## in a little, turn, and hold, and then they stop holding.
func ask_to_pose(anchor: Vector3) -> void:
	if _seated:
		_posing = true
		_pose_timer = POSE_HOLD + _rng.randf_range(POSE_DECAY.x, POSE_DECAY.y)
		return
	_posing = true
	_pose_timer = POSE_HOLD + _rng.randf_range(POSE_DECAY.x, POSE_DECAY.y)
	_wait = 0.0
	_pose_anchor = _gather_point(anchor)


## Stand near the anchor without standing on it or on each other, facing back
## the way the ask came from.
func _gather_point(anchor: Vector3) -> Vector3:
	var away := global_position - anchor
	away.y = 0.0
	if away.length() < 0.5:
		away = Vector3(_rng.randfn(0.0, 1.0), 0.0, _rng.randfn(0.0, 1.0))
	var spread := _rng.randf_range(-0.7, 0.7)
	var offset := away.normalized().rotated(Vector3.UP, spread) * POSE_GATHER_DISTANCE
	return anchor + offset


func _update_pose(delta: float) -> void:
	if not _posing:
		return
	_pose_timer -= delta
	if _pose_timer <= 0.0:
		_posing = false
		_route = PackedInt32Array()
		_wait = _rng.randf_range(0.4, 2.0)


func is_posing() -> bool:
	return _posing


# --- attention --------------------------------------------------------------


func _update_attention() -> void:
	if _crowd == null:
		_attention = Attention.FORWARD
		_look_weight = 0.0
		return

	var eye: Vector3 = _crowd.player_eye

	if _posing:
		if _pose_complies:
			_set_attention(Attention.POSE, eye, 1.0)
		else:
			# Looking at anything except the camera. Reliably the better photo.
			var elsewhere := global_position + Vector3(sin(_idle_phase) * 4.0, 1.2, cos(_idle_phase * 0.7) * 4.0)
			_set_attention(Attention.POSE, elsewhere, 0.8)
		return

	if _crowd.camera_raised and _reaction != Reaction.OBLIVIOUS:
		# The beat where they are looking at whoever tipped them off, before
		# they find what that person found.
		if _gaze_timer > 0.0 and is_instance_valid(_gaze_at):
			_set_attention(Attention.GAZE, _gaze_at.eye_position(), 0.9)
			return

		var holding := _reaction == Reaction.HOLD
		var glancing := _reaction == Reaction.GLANCE and _reaction_timer > 0.0
		if holding or glancing:
			_set_attention(Attention.CAMERA, eye, 1.0)
			return
		if _reaction == Reaction.AVOID:
			var to_player := (eye - global_position).normalized()
			var turned := to_player.rotated(Vector3.UP, PI * 0.55)
			_set_attention(Attention.CAMERA, global_position + turned * 6.0 + Vector3.UP * 1.4, 0.7)
			return

	# Measured rather than declared. A follower keeping station is standing
	# still without ever having decided to, and looks at their group for the
	# same reason a leader on a pause does.
	var stopped := _speed < 0.2

	if stopped and not _companions.is_empty():
		var companion: Guest = _companions[wrapi(int(_idle_phase * 0.25), 0, _companions.size())]
		if is_instance_valid(companion):
			_set_attention(Attention.COMPANION, companion.eye_position(), 0.85)
			return

	var poi: Vector3 = _crowd.poi_near(global_position, 9.0 if stopped else 5.0)
	if poi != Vector3.INF:
		_set_attention(Attention.POI, poi, 0.7 if stopped else 0.45)
		return

	_attention = Attention.FORWARD
	_look_weight = lerpf(_look_weight, 0.0, 0.05)


func _set_attention(kind: int, point: Vector3, weight: float) -> void:
	_attention = kind
	_look_point = point
	_look_weight = weight


func eye_position() -> Vector3:
	if _head_pivot == null:
		return global_position + Vector3.UP * 1.5
	return _head_pivot.global_position


func _update_head(delta: float) -> void:
	var wanted_yaw := 0.0
	var wanted_pitch := 0.0

	if _look_weight > 0.01:
		var local: Vector3 = global_transform.basis.inverse() * (_look_point - eye_position())
		var flat := Vector2(local.x, local.z).length()
		wanted_yaw = atan2(-local.x, -local.z)
		wanted_pitch = atan2(local.y, maxf(flat, 0.001))

		# A neck that cannot reach either turns the shoulders or looks away. It
		# does not stretch, which is the tell in every game that gets this wrong.
		if absf(wanted_yaw) > BODY_TURN_THRESHOLD:
			var can_turn := _posing or (_wait > 0.0 and _attention >= Attention.COMPANION)
			if can_turn:
				var to_point := _look_point - global_position
				to_point.y = 0.0
				_face_direction(to_point.normalized(), delta, 3.2)
			elif absf(wanted_yaw) > HEAD_YAW_LIMIT:
				wanted_yaw = 0.0
				wanted_pitch = 0.0

		wanted_yaw = clampf(wanted_yaw, -HEAD_YAW_LIMIT, HEAD_YAW_LIMIT) * _look_weight
		wanted_pitch = clampf(wanted_pitch, -HEAD_PITCH_LIMIT, HEAD_PITCH_LIMIT) * _look_weight

	# Idle drift so a head at rest is never perfectly still.
	wanted_yaw += sin(_idle_phase * 0.31) * 0.05
	wanted_pitch += sin(_idle_phase * 0.23) * 0.02

	_head_yaw = lerp_angle(_head_yaw, wanted_yaw, HEAD_TURN_RATE * delta)
	_head_pitch = lerp_angle(_head_pitch, wanted_pitch, HEAD_TURN_RATE * delta)
	_head_pivot.rotation = Vector3(_head_pitch, _head_yaw, 0.0)

	if not _passenger_heads.is_empty():
		_update_passengers(delta)


## How much further round a passenger turns than the adult pushing them. Over one
## because a strapped-in child turns as far as the straps allow, and an adult
## only as far as is polite.
const PASSENGER_CRANE := 1.4
const PASSENGER_YAW_LIMIT := 1.5
const PASSENGER_PITCH_LIMIT := 0.5
const PASSENGER_TURN_RATE := 4.0


## The children in the buggy, looking where the adult pushing them is looking.
##
## Not a copy of that adult's head: later, further round, and each on its own
## beat. A small child follows what the grown-up is attending to rather than
## finding it themselves, and takes a moment about it — so the gaze arrives as a
## ripple through the group rather than as two heads snapping together, which is
## the same reason `crowd.gd` staggers contagious noticing.
##
## Reusing the pusher's head angles rather than aiming these at the look point
## costs a little accuracy — a passenger sits about a metre in front of the
## person pushing, so their true angle to a subject differs. At the eight metres
## a photograph is taken from that difference is under two degrees, and it buys
## the passengers out of the attention system entirely.
func _update_passengers(delta: float) -> void:
	for i in _passenger_heads.size():
		var head: Node3D = _passenger_heads[i]
		var yaw := clampf(_head_yaw * PASSENGER_CRANE,
			-PASSENGER_YAW_LIMIT, PASSENGER_YAW_LIMIT)
		var pitch := clampf(_head_pitch * PASSENGER_CRANE,
			-PASSENGER_PITCH_LIMIT, PASSENGER_PITCH_LIMIT)
		# Each on a frequency of its own, so twins are never in step.
		yaw += sin(_idle_phase * (0.34 + 0.09 * float(i))) * 0.13
		pitch += sin(_idle_phase * (0.27 + 0.07 * float(i))) * 0.06
		# Clamped, because `lerp_angle` past one overshoots and a delta spike
		# would snap a head past the target and back.
		var rate := minf(PASSENGER_TURN_RATE * (1.0 + float(i) * 0.27) * delta, 1.0)
		head.rotation = Vector3(
			lerp_angle(head.rotation.x, pitch, rate),
			lerp_angle(head.rotation.y, yaw, rate),
			0.0)


# --- animation --------------------------------------------------------------


func _animate(delta: float, moved: float) -> void:
	_idle_phase += delta

	# Checked before `_seated`, because a wheelchair guest is seated the whole
	# time and this one function has to cover both rolling and stopped.
	if wheelchair:
		_animate_wheels(delta, moved)
		return

	if _seated:
		_animate_seated()
		return

	# Stride length scales with height so short guests take more steps to cross
	# the same ground, which is most of what makes a mixed crowd read as mixed.
	var cadence := 3.4
	_stride = lerpf(_stride, clampf(moved / maxf(delta, 0.0001) / walk_speed, 0.0, 1.0), 8.0 * delta)
	_phase += moved * cadence

	var swing := 0.62 * _stride
	var hip := sin(_phase)
	_hip_l.rotation.x = hip * swing
	_hip_r.rotation.x = -hip * swing
	# Knees only bend one way, and only on the leg that is swinging through.
	_knee_l.rotation.x = -maxf(sin(_phase - 0.9), 0.0) * 0.85 * _stride
	_knee_r.rotation.x = -maxf(sin(_phase - 0.9 + PI), 0.0) * 0.85 * _stride

	if stroller:
		# Both hands on the bar, and staying there. An arm swinging over a
		# stroller reads as somebody walking beside one rather than pushing it,
		# and that is the entire difference at this fidelity.
		_arm_l.rotation.x = push_arm
		_arm_r.rotation.x = push_arm
		_spin_wheels(moved)
	else:
		_arm_l.rotation.x = -hip * swing * 0.7
		_arm_r.rotation.x = hip * swing * 0.7

	# Damped when the hands are anchored to something that does not bob with the
	# shoulders. At a full walking bob they slide up and down through the handle
	# a centimetre every step, which is small enough to miss in motion and
	# obvious in a photograph — and a photograph is what this game makes.
	var carry := 0.35 if stroller else 1.0
	var bob := absf(sin(_phase)) * 0.022 * _stride * carry
	var sway := sin(_idle_phase * 0.9) * 0.012 * (1.0 - _stride)
	_body.position.y = _body_rest_y + bob + sway
	_body.rotation.z = sin(_phase) * 0.03 * _stride * carry


## Rolling. The same idea as the walk cycle and for the same reason — the wheels
## turn on ground actually crossed rather than on a clock, so a guest held up by
## the crowd slows down instead of skating.
##
## The arms are the part that has to be right. Both go together rather than
## alternating, which is the single thing that distinguishes pushing a chair from
## walking at this fidelity, and the stroke is a slower beat than the wheel: a
## hand catches the rim, pushes through and comes back. `_stride` fades it out
## when the chair stops, so the hands settle onto the rims rather than freezing
## mid-push.
func _animate_wheels(delta: float, moved: float) -> void:
	_stride = lerpf(_stride, clampf(moved / maxf(delta, 0.0001) / walk_speed, 0.0, 1.0),
		8.0 * delta)

	_spin_wheels(moved)

	_push_phase += moved * 1.45
	var reach := 0.35 + sin(_push_phase) * 0.5 * _stride
	_arm_l.rotation.x = reach
	_arm_r.rotation.x = reach

	# Leaning into the stroke and not out of it, so the lean is only ever
	# forward — half a sine rather than a whole one.
	_body.rotation.x = maxf(sin(_push_phase), 0.0) * 0.07 * _stride
	_body.rotation.z = sin(_idle_phase * 0.4) * 0.02 * (1.0 - _stride)
	# Off the wheels, not off `_phase`. The walk cycle no longer advances for a
	# guest whose legs are folded, so a jostle tied to it stood perfectly still.
	var jostle := absf(sin(_roll_phase * 0.5)) * 0.005 * _stride
	_body.position.y = _body_rest_y + jostle + sin(_idle_phase * 0.6) * 0.008 * (1.0 - _stride)


## Turning the wheels of whatever is being pushed, or pushed in, on ground
## actually crossed rather than on a clock — so anything held up by the crowd
## slows down instead of skating.
##
## Shared by the chair and the buggy because they are the same arrangement: a
## driven pair, and a smaller pair that trails and therefore turns further over
## the same ground.
func _spin_wheels(moved: float) -> void:
	_roll_phase += moved / maxf(wheel_radius, 0.05)
	# Positive rotation about X carries the bottom of the wheel forward, so a
	# wheel rolling the way the guest is facing turns the other way.
	if _wheel_l != null:
		_wheel_l.rotation.x = -_roll_phase
		_wheel_r.rotation.x = -_roll_phase
	if _caster_l != null:
		var spin := -_roll_phase * _caster_ratio
		_caster_l.rotation.x = spin
		_caster_r.rotation.x = spin


func _animate_seated() -> void:
	var shift := sin(_idle_phase * 0.6) * 0.012
	_body.position.y = _body_rest_y + shift
	_body.rotation.z = sin(_idle_phase * 0.4) * 0.02
	_arm_l.rotation.x = 0.35 + sin(_idle_phase * 0.5) * 0.04
	_arm_r.rotation.x = 0.35 + sin(_idle_phase * 0.43) * 0.04


## Sitting is the same skeleton folded: hips raised to the seat, thighs swung
## forward, shins hanging back down. The guest walks their root onto the seat's
## centre, so the only thing to solve here is the fold.
##
## Positive rotation about X carries a limb forward (-Z). The thigh goes almost
## all the way over; the knee takes almost all of it back off, which leaves the
## shins vertical and the feet under the seat's front edge rather than out in
## front of it.
func _apply_seated_pose() -> void:
	_body.position.y = _body_rest_y
	_hip_l.rotation.x = deg_to_rad(84.0)
	_hip_r.rotation.x = deg_to_rad(80.0)
	_knee_l.rotation.x = deg_to_rad(-80.0)
	_knee_r.rotation.x = deg_to_rad(-76.0)
	_arm_l.rotation.x = 0.35
	_arm_r.rotation.x = 0.35
