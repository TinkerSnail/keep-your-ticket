extends Node3D

## The plaza's crowd: a walkable graph, a list of things worth looking at, the
## guests standing on both, and the day they are having.
##
## This exists so that a guest does not have to know about the plaza and the
## plaza does not have to know about guests. Guests ask it where they may walk
## and what is worth a glance; it watches the player on their behalf, once,
## instead of thirty times a frame.
##
## It also owns the hour. The cast below is the park's *busiest* hour, and how
## much of it is standing in the plaza at any moment is read off `ParkClock`.
## Groups arrive and go home through the gap at the south — the park's own way
## in — so the plaza fills and empties without anybody appearing from nowhere.
##
## The point of that is not simulation. `documentation/design.md` asks the
## player to read the time off the park rather than off a readout, and the
## clock face on the sign tower cannot be the only way to do it. A plaza you
## can barely cross, with the tables full, is two in the afternoon. Twenty
## people and an empty cafe is opening.
##
## The graph and the guests below it are generated — see `tools/gen_crowd.gd`.

## Flat pairs of node indices. Every edge is walkable in both directions, and
## the generator has already checked that nothing stands on it.
@export var nodes: PackedVector3Array = PackedVector3Array()
@export var edges: PackedInt32Array = PackedInt32Array()
## One byte per edge *pair*: 1 if that edge has steps on it, 0 if it does not.
##
## **This is the first thing in the park that wheels and legs disagree about.**
## Until the east climb there was no edge anywhere with a step-free twin, so a
## flag like this would have been scaffolding nothing could check. The cascade
## and the staircase each carry a ramp on the north and a stair on the south
## between the same two points, which is exactly the case it needs.
##
## Empty is legal and means "no edge has steps" — every scene generated before
## this existed still loads and every guest still routes.
@export var edge_steps: PackedByteArray = PackedByteArray()
## Points a guest might plausibly look at: the fountain, the sign, the
## bandstand, a lamp they are standing under. Height is part of the point —
## looking up at the sign tower is a different photograph than looking across.
@export var pois: PackedVector3Array = PackedVector3Array()

@export var route_hops := Vector2i(2, 5)

## The graph node at the plaza's south gap — the way to the gate, and the only
## way in or out that exists. Everything about coming and going is measured in
## hops from here.
@export var entry_node := -1
## Off-stage, down the street past the perimeter wall and short of the first
## shopfront. Groups waiting their turn are parked under the world rather than
## here; this is only where they set off from and where they walk to.
@export var hold_point := Vector3(-1.5, 0.0, 45.0)

## How long a guest who has just noticed the camera stays worth noticing. The
## signal a neighbour picks up is the turn, not the staring that follows, so a
## chain can only hop while the last hop is still recent. That is what makes
## contagion a ripple that dies out rather than an alarm the whole plaza joins.
const ALERT_FRESHNESS := 1.3

## Where a group is in its visit. `OUT` is dormant — either not arrived yet or
## gone home; nothing here distinguishes the two, because nothing yet needs a
## guest to be the same person twice. That is the roster, and it is the half of
## the claim ticket that has not been built.
##
## Walking in counts as `IN`. A group told to go home while it is still coming
## through the gap simply turns round, which is what a park closing early would
## actually look like.
enum Visit { OUT, IN, LEAVING }

## The day's shape, per population, as a fraction of that population's peak on
## each hour. Between hours it is a straight line; a crowd does not turn over
## fast enough for anything smoother to be visible.
##
## Read off how a park of this kind actually fills rather than picked to be
## pretty. Thin at opening, most of the way full by early afternoon, a long
## plateau rather than a spike, and a real evening — the park runs to ten and
## people stay for it. The last hour thins because people are going home, not
## because the park is shutting on them.
const PLAZA_WANDER_DAY := [
	0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
	0.34, 0.60, 0.74, 0.85, 0.94, 1.00,
	0.98, 0.90, 0.84, 0.88, 0.78, 0.46,
	0.0, 0.0,
]

## The tables do not track the crowd, which is the point of giving them their
## own curve: a full cafe at one o'clock and an empty one at four is a fact
## about lunch, and reading it is worth more than another copy of the headcount.
const PLAZA_CAFE_DAY := [
	0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
	0.15, 0.45, 0.90, 1.00, 0.75, 0.50,
	0.45, 0.70, 0.95, 0.85, 0.55, 0.30,
	0.0, 0.0,
]

## Benches fill later and stay full longer. People sit down in the afternoon
## because they have been walking since eleven, and they sit down in the
## evening because there is a bandstand and the light is good.
const PLAZA_BENCH_DAY := [
	0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
	0.15, 0.30, 0.50, 0.65, 0.85, 1.00,
	1.00, 0.90, 0.75, 0.80, 0.85, 0.50,
	0.0, 0.0,
]

## Which way the section is drifting. +1 is people heading in, −1 is people
## heading for the way out. A thumb on the scale in `route_from` and nothing
## more, so the evening is a drift towards the gate and never a march.
const PLAZA_FLOW := [
	0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
	1.00, 0.85, 0.50, 0.20, 0.00, 0.00,
	-0.10, -0.20, -0.30, -0.35, -0.60, -1.00,
	0.0, 0.0,
]

## The four curves above are the *plaza's*, and they are defaults rather than
## law. A section's day is section data in exactly the way its graph is, and the
## first section to disagree was the second one built: a seaside strip peaks in
## the evening, which is the whole reason the boardwalk is on the side the sun
## sets into. Curves belonging to the crowd rather than to the section would have
## made that unsayable.
##
## Set by `tools/gen_crowd.gd` alongside `nodes` and `edges`. Anything mounted
## without them gets the plaza's shape, which is the right failure: a section
## with a generic day is odd, and a section with no day at all is empty.
@export var wander_day: Array = PLAZA_WANDER_DAY
@export var cafe_day: Array = PLAZA_CAFE_DAY
@export var bench_day: Array = PLAZA_BENCH_DAY
@export var flow_day: Array = PLAZA_FLOW

## How hard the flow leans on each hop. Small on purpose, and measured rather
## than guessed: over four thousand wanders starting three hops from the gate,
## the average one ends at depth 4.53 at eleven in the morning, 4.00 at two in
## the afternoon and 3.13 at nine at night. A swing of a hop and a half, which
## is a drift you can watch happen over a minute and never a march.
const FLOW_WEIGHT := 0.35

const SYNC_INTERVAL := 1.5
## How long a group gets to walk out before it is put away regardless of where
## it has got to. Counted from being told to go home, not from arriving
## off-stage, which is the difference between a backstop and a deadlock: the
## first version only started counting once everybody was home, so a group that
## could not get home never timed out and simply stayed in the park forever.
##
## Comfortably longer than the walk itself — the far side of the plaza to the
## street is about seventy metres at a bit over a metre a second.
const SLEEP_PATIENCE := 90.0

var guests: Array = []
var camera_raised := false
## Whether `player_position` means anything yet. Guests give the player a berth
## and would otherwise all give a berth to the origin — which is the fountain —
## for as long as it took the player to be found, or forever in a harness that
## runs without one.
var player_present := false
var player_position := Vector3.ZERO
var player_eye := Vector3.ZERO

var _adjacency: Array[PackedInt32Array] = []
## The step-free subset of the above, and the graph a guest on wheels walks.
var _adjacency_flat: Array[PackedInt32Array] = []
## Hops from `entry_node`. How deep into the plaza a node is, which is both the
## flow bias and — walked downhill — the way out.
var _depth: PackedInt32Array = PackedInt32Array()
## The same sweep over step-free edges. −1 means a node no wheelchair, buggy or
## pram can reach, which is a legitimate answer rather than a fault.
var _depth_flat: PackedInt32Array = PackedInt32Array()
var _roster: Array = []
var _groups: Dictionary = {}
var _visits: Array = []
var _visits_by_kind: Dictionary = {}
var _sync_timer := 0.0
## Guests who noticed the camera recently enough to still be catching eyes,
## each with how long ago. Short — usually nobody, briefly a handful.
var _alerts: Array = []
var _player: Node3D = null
var _player_camera: Node3D = null
var _rng := RandomNumberGenerator.new()
## Routing gets its own, because `route_from` reseeds on the caller's seed to
## keep a guest's wander reproducible. Sharing one generator meant every scatter
## and every spawn point was drawn from a stream some guest had just reset.
var _route_rng := RandomNumberGenerator.new()


## In `_enter_tree`, not `_ready`. Children run `_ready` before their parent, so
## a guest looking for the crowd in its own `_ready` finds nothing — every guest
## comes up with a null router, stands still forever, and looks like it is
## working because the generator scattered them across the plaza to begin with.
## `_enter_tree` runs parent-first, which is the order this needs.
func _enter_tree() -> void:
	add_to_group("crowd")


## Guests register in their own `_ready`, which runs before this one, so the
## roster is complete by the time the visits are built off it — and the first
## sync happens here rather than deferred so that the opening hour's crowd is
## already standing in the plaza on frame one.
func _ready() -> void:
	# Fixed, so the same day happens twice. A park the player is meant to learn
	# should not reshuffle which bench fills first every time it is launched,
	# and a harness measuring the day cannot say anything about it if the day is
	# different on every run.
	_rng.seed = 0x5150

	_build_adjacency()
	_build_depth()
	_build_visits()
	_sync_population(true)
	call_deferred("_connect_player")

	ParkClock.park_closed.connect(_on_park_closed)
	# A jump is not an hour passing. Nobody walks anywhere for it — the crowd
	# the new time wants is simply standing there.
	ParkClock.clock_jumped.connect(func() -> void: _sync_population(true))


## Two adjacencies off one edge list: everything, and the step-free subset a
## guest on wheels is allowed. Built together so they cannot drift.
func _build_adjacency() -> void:
	_adjacency.resize(nodes.size())
	_adjacency_flat.resize(nodes.size())
	for i in nodes.size():
		_adjacency[i] = PackedInt32Array()
		_adjacency_flat[i] = PackedInt32Array()
	var pairs := edges.size() / 2
	for p in pairs:
		var a := edges[p * 2]
		var b := edges[p * 2 + 1]
		if a < 0 or b < 0 or a >= nodes.size() or b >= nodes.size():
			push_warning("crowd: edge %d references a node that does not exist" % p)
			continue
		_adjacency[a].append(b)
		_adjacency[b].append(a)
		# Absent `edge_steps` means a graph written before steps existed, and the
		# safe reading of that is "no steps" — the alternative strands every
		# wheeled guest in the plaza on a flag nobody set.
		if p < edge_steps.size() and edge_steps[p] != 0:
			continue
		_adjacency_flat[a].append(b)
		_adjacency_flat[b].append(a)


## Breadth-first from the way out. Doing it once buys two things at no cost: a
## measure of how deep into the plaza somewhere is, which is what the flow leans
## on, and a shortest path to the gate for free — walking downhill on a BFS
## depth *is* the path, so nothing here has to search.
func _build_depth() -> void:
	_depth = _sweep(_adjacency, true)
	# And the same sweep over step-free edges only, which is how a guest on
	# wheels finds its way out. It is allowed to leave nodes unreached — a stair
	# with no ramp beside it is exactly that — so this one does not complain.
	_depth_flat = _sweep(_adjacency_flat, false)


func _sweep(adjacency: Array, complain: bool) -> PackedInt32Array:
	var depth := PackedInt32Array()
	depth.resize(nodes.size())
	depth.fill(-1)
	if entry_node < 0 or entry_node >= nodes.size():
		if complain:
			push_warning("crowd: no entry node — nobody can arrive or leave")
		return depth

	depth[entry_node] = 0
	var frontier := PackedInt32Array([entry_node])
	while not frontier.is_empty():
		var next := PackedInt32Array()
		for i in frontier:
			for option in adjacency[i]:
				if depth[option] >= 0:
					continue
				depth[option] = depth[i] + 1
				next.append(option)
		frontier = next

	if complain:
		for i in nodes.size():
			if depth[i] < 0:
				push_warning("crowd: node %d cannot reach the gate" % i)
	return depth


func _connect_player() -> void:
	_player = get_tree().get_first_node_in_group("player") as Node3D
	if _player != null:
		_player_camera = _player.get_node_or_null("head/camera") as Node3D
		player_position = _player.global_position
		player_present = true

	var camera_tool := get_tree().get_first_node_in_group("camera_tool")
	if camera_tool == null:
		push_warning("crowd: no camera_tool found — guests will never notice the camera")
		return
	camera_tool.raised_changed.connect(_on_camera_raised_changed)


func _on_camera_raised_changed(raised: bool) -> void:
	camera_raised = raised
	if not raised:
		_alerts.clear()


## One separation radius to a side. With cells at least as wide as the radius,
## everything within a push of a point lies inside the nine cells around it, so
## a guest never has to look past its own block.
const CELL_SIZE := Guest.SEPARATION_RADIUS

## Live guests bucketed by a square of ground, rebuilt once per physics frame.
##
## This is the whole reason the crowd can be more than about sixty people.
## Separation used to walk the entire live list for every live guest, which is
## every pair, every frame — 2,916 distance checks at 54 people and 21,904 at
## 148. Measured across a cast of 56 and a cast of 150, that quadratic term was
## **87% of the crowd's frame cost at 148**, and the plaza was spending half its
## physics budget on people not bumping into each other.
##
## Keyed on the ground plane only. Height is not part of it because nobody is
## standing on anybody.
var _cells: Dictionary = {}

## Handed straight back by `neighbours` and refilled by the next call — see the
## warning there.
var _near: Array = []


func _rebuild_cells() -> void:
	_cells.clear()
	for entry in guests:
		var guest := entry as Node3D
		if guest == null or not is_instance_valid(guest):
			continue
		var key := _cell_of(guest.global_position)
		if not _cells.has(key):
			_cells[key] = []
		_cells[key].append(guest)


func _cell_of(at: Vector3) -> Vector2i:
	return Vector2i(int(floor(at.x / CELL_SIZE)), int(floor(at.z / CELL_SIZE)))


## Everyone in the nine cells around `at`: everybody close enough to push, plus
## a few who are not. The caller measures distance anyway, so a loose answer
## costs nothing and a tight one would cost more to compute than it saves.
##
## **The array handed back is reused.** The next call refills it, so it is safe
## to iterate and never safe to keep. Guests ask once inside their own
## `_physics_process` and use it immediately; handing out a fresh array per
## guest per frame would put back a good part of what the bucketing just saved.
func neighbours(at: Vector3) -> Array:
	_near.clear()
	var base := _cell_of(at)
	for dx in range(-1, 2):
		for dz in range(-1, 2):
			var bucket: Variant = _cells.get(Vector2i(base.x + dx, base.y + dz))
			if bucket != null:
				_near.append_array(bucket)
	return _near


func _physics_process(_delta: float) -> void:
	# First, and before any guest has run. `_physics_process` is called down the
	# tree and the guests are children of this node, so a hash built here is
	# already standing by the time they ask for it.
	#
	# It is one frame stale against their own movement, which is at most about
	# five centimetres at a walk. That is well inside the slack the nine-cell
	# block gives, and a push missed for a sixtieth of a second is not a push.
	_rebuild_cells()
	_age_alerts(_delta)

	_sync_timer -= _delta
	if _sync_timer <= 0.0:
		_sync_timer = SYNC_INTERVAL
		_sync_population(false)

	if _player == null:
		return
	player_position = _player.global_position
	player_eye = _player_camera.global_position if _player_camera != null \
		else player_position + Vector3.UP * 1.6


# --- the day ----------------------------------------------------------------


## One record per generated group, in generation order. That order is the order
## they arrive in, every day, which is what makes the cafe filling from the
## north end something the player can come to know rather than a shuffle.
func _build_visits() -> void:
	_visits.clear()
	_visits_by_kind = {"wander": [], "bench": [], "cafe": []}

	var ids: Array = _groups.keys()
	ids.sort()
	for id in ids:
		var members: Array = _groups[id]
		if members.is_empty():
			continue
		var kind: String = members[0].group_kind
		if not _visits_by_kind.has(kind):
			push_warning("crowd: group %d has an unknown kind '%s'" % [id, kind])
			kind = "wander"
		var visit := {
			"id": id,
			"kind": kind,
			"members": members,
			"state": Visit.OUT,
			"waiting": 0.0,
		}
		_visits.append(visit)
		_visits_by_kind[kind].append(visit)


## Plain `Array`, not `PackedFloat32Array`, because a packed array's constructor
## is not a constant expression and these want to be constants.
func _curve_at(curve: Array, h: float) -> float:
	var whole := int(floor(h)) % 24
	var frac: float = h - floor(h)
	return lerpf(curve[whole], curve[(whole + 1) % 24], frac)


## How many of each population the hour wants. A fraction of the generated
## peak, so the cast is what sets the busiest the plaza ever gets and the clock
## only ever asks for less.
func _target_for(kind: String, peak: int) -> int:
	if not ParkClock.is_open():
		return 0
	var h := ParkClock.hours()
	var curve := wander_day
	match kind:
		"cafe":
			curve = cafe_day
		"bench":
			curve = bench_day
	return int(round(_curve_at(curve, h) * float(peak)))


## Asked once per sync rather than per group, so that all three populations
## make the same decision about whether the way in is available this tick.
func _sync_population(immediate: bool) -> void:
	var held := not immediate and _threshold_is_watched()
	for kind in _visits_by_kind:
		var list: Array = _visits_by_kind[kind]
		var peak := 0
		for visit in list:
			peak += visit["members"].size()
		_sync_kind(list, _target_for(kind, peak), immediate, held)
	_sweep_departed(immediate)


## Admit in generation order, send home in reverse, and never cross the target
## in either direction — a group only comes in if the whole group still fits
## under what the hour wants, and only goes home if the whole group can leave
## without dropping below it.
##
## The obvious rule instead of that one is "take whichever move gets closest",
## and it was the first version. It churns. A group of four is admitted because
## seven is nearer to six than three is, and then a group of one is sent home in
## the same sync to trim the overshoot — so the plaza spends the morning, which
## is supposed to be filling up, walking people back out of the gate. Sitting a
## head or two under the target costs nothing and nobody can count anyway.
func _sync_kind(list: Array, want: int, immediate: bool, held: bool) -> void:
	# Nobody can arrive while the way in is on screen, so nobody may leave
	# either. Gating one direction and not the other means a player who stands
	# and watches the gate sees the plaza drain and never refill — which is what
	# the day test found, at eleven heads under the curve and falling. Holding
	# both is the honest answer: the hour is a target, and a target is allowed
	# to wait for somebody to look away.
	if held:
		return

	var live := 0
	for visit in list:
		if visit["state"] != Visit.OUT:
			live += visit["members"].size()

	if live < want:
		for visit in list:
			if visit["state"] != Visit.OUT:
				continue
			var after: int = live + visit["members"].size()
			if after > want:
				continue
			_admit(visit, immediate)
			live = after
		return

	for i in range(list.size() - 1, -1, -1):
		if live <= want:
			return
		var visit: Dictionary = list[i]
		if visit["state"] != Visit.IN:
			continue
		var after: int = live - visit["members"].size()
		if after < want:
			continue
		_retire(visit, immediate)
		live = after


## Groups that have finished the walk out and are standing off-stage. They are
## put away when the way out is not being watched, which is nearly always — and
## after `SLEEP_PATIENCE` regardless, because a guest standing still at the far
## end of an empty street is a worse thing to see than one that is not there.
func _sweep_departed(immediate: bool) -> void:
	for visit in _visits:
		if visit["state"] != Visit.LEAVING:
			continue

		visit["waiting"] += SYNC_INTERVAL
		var forced: bool = visit["waiting"] >= SLEEP_PATIENCE

		if not forced:
			var all_home := true
			for guest in visit["members"]:
				if is_instance_valid(guest) and not guest.is_home(hold_point):
					all_home = false
					break
			if not all_home:
				continue
			if not immediate and _threshold_is_watched():
				continue

		for guest in visit["members"]:
			if is_instance_valid(guest):
				guest.go_dormant()
		visit["state"] = Visit.OUT
		visit["waiting"] = 0.0


## `immediate` is the first read of the clock — a session starting, or a dev
## tool jumping the hour. Nobody walks in then: the crowd the hour asks for is
## simply standing in the plaza, because a park at opening has people in it and
## not a queue filing through the gate while the player watches.
func _admit(visit: Dictionary, immediate: bool) -> void:
	var members: Array = visit["members"]

	if immediate:
		# **A group is put down together.** `_home_point` rolls an independent
		# graph node for every guest who has no seat, which for a leader is what
		# is wanted and for their followers scattered the group across the whole
		# plaza — and a follower's only instinct is to head for their leader, in
		# a straight line, from wherever they woke up.
		#
		# That is where the guests walking through the fountain came from. Not
		# from the wander graph, which `_validate_graph` keeps clear of it, and
		# not from the leader, who is on the ring the whole time: from a follower
		# put down 21m from their station on the far side and walking at it.
		# Measured at radius 4.98 in an 8.26m pool.
		#
		# Members are in generation order and member 0 is the leader, so the
		# first non-follower placed becomes the anchor for the rest of them.
		# Seated guests keep their own seat — they are not following anybody
		# across the plaza, they are going to a bench.
		var anchor := Vector3.INF
		for guest in members:
			if not is_instance_valid(guest):
				continue
			var at := _home_point(guest)
			if guest.has_seat():
				pass
			elif _follows(guest) and anchor != Vector3.INF:
				# Beside their leader rather than exactly on station: they walk
				# onto station over the next stride, and starting them stacked
				# on one point makes the group shove itself apart on frame one.
				at = anchor + Vector3(
					_rng.randf_range(-1.2, 1.2), 0.0, _rng.randf_range(-1.2, 1.2))
			else:
				anchor = at
			guest.spawn_at(at)
		visit["state"] = Visit.IN
		return

	for guest in members:
		if not is_instance_valid(guest):
			continue
		# Followers have no way in of their own — they walk in after whoever
		# they came with, the same as they do everywhere else.
		var via: Array[Vector3] = []
		if not _follows(guest):
			via = _way_in_for(guest)
		guest.arrive_from(_scatter(hold_point), via)
	visit["state"] = Visit.IN


## The mirror of `_admit`: `immediate` is a clock that jumped rather than one
## that ran, and nobody walks anywhere for it.
func _retire(visit: Dictionary, immediate := false) -> void:
	if immediate:
		for guest in visit["members"]:
			if is_instance_valid(guest):
				guest.go_dormant()
		visit["state"] = Visit.OUT
		visit["waiting"] = 0.0
		return

	for guest in visit["members"]:
		if not is_instance_valid(guest):
			continue
		var via: Array[Vector3] = []
		if not _follows(guest):
			via = _way_out_from(guest.global_position, guest.is_wheeled())
		guest.depart_via(via)
	visit["state"] = Visit.LEAVING
	visit["waiting"] = 0.0


## Ten at night. Everyone still in the plaza is walked out rather than switched
## off — the last guest leaving is the beginning of the night, and the player
## should be able to watch it happen.
func _on_park_closed() -> void:
	for visit in _visits:
		if visit["state"] == Visit.IN:
			_retire(visit)


func _follows(guest: Node) -> bool:
	return not (guest.leader_path as NodePath).is_empty()


## Where a guest belongs once they are in: their seat, or a node deep enough
## into the plaza that spawning them there does not put the whole opening hour
## in the doorway.
func _home_point(guest: Node) -> Vector3:
	if guest.has_seat():
		return guest.seat_at
	if nodes.is_empty():
		return global_position
	var pick := _rng.randi_range(0, nodes.size() - 1)
	return nodes[pick] + Vector3(_rng.randfn(0.0, 0.8), 0.0, _rng.randfn(0.0, 0.8))


func _way_in_for(guest: Node) -> Array[Vector3]:
	var via: Array[Vector3] = []
	if entry_node >= 0:
		via.append(nodes[entry_node])
	if not guest.has_seat():
		return via
	# The way to a bench is the way from it, backwards. Walking the graph rather
	# than the straight line matters here: the line from the gap to the west
	# benches goes through the fountain.
	var path := _path_to_entry(guest.seat_at, guest.is_wheeled())
	for i in range(path.size() - 1, -1, -1):
		if path[i] == entry_node:
			continue
		via.append(nodes[path[i]])
	via.append(guest.seat_at)
	return via


func _way_out_from(point: Vector3, wheeled := false) -> Array[Vector3]:
	var via: Array[Vector3] = []
	for i in _path_to_entry(point, wheeled):
		via.append(nodes[i])
	via.append(_scatter(hold_point))
	return via


## Downhill on `_depth`, which is a shortest path to the gate because the depth
## came from a breadth-first sweep out of it. Includes the node it starts from
## and ends on the entry.
func _path_to_entry(point: Vector3, wheeled := false) -> PackedInt32Array:
	var path := PackedInt32Array()
	var adjacency: Array = _adjacency_flat if wheeled else _adjacency
	var depth: PackedInt32Array = _depth_flat if wheeled else _depth
	var current := nearest_node(point, wheeled)
	if current < 0 or entry_node < 0 or depth.is_empty():
		return path

	path.append(current)
	# Bounded by the graph's own diameter. The cap is a backstop against a node
	# whose depth never came out of the sweep, not an expected outcome.
	for _i in nodes.size():
		if current == entry_node:
			break
		var best := -1
		var best_depth := depth[current]
		for option in adjacency[current]:
			if depth[option] >= 0 and depth[option] < best_depth:
				best_depth = depth[option]
				best = option
		if best < 0:
			break
		current = best
		path.append(current)
	return path


func _scatter(point: Vector3) -> Vector3:
	return point + Vector3(_rng.randf_range(-3.0, 2.5), 0.0, _rng.randf_range(-2.0, 3.0))


## Whether the player can see the way in. Frustum only, with no occlusion test —
## it says yes when a building is in between, which is the wrong answer in the
## safe direction: the cost is that a group waits another second and a half.
func _threshold_is_watched() -> bool:
	var camera := get_viewport().get_camera_3d()
	if camera == null:
		return false
	if entry_node < 0:
		return false
	var eyeline := Vector3.UP * 0.9
	# Both ends of the walk in. Checking the far end alone lets a group appear
	# at the near edge of frame and stride into the middle of it.
	return camera.is_position_in_frustum(hold_point + eyeline) \
		or camera.is_position_in_frustum(nodes[entry_node] + eyeline)


# --- the graph --------------------------------------------------------------


func node_position(index: int) -> Vector3:
	if index < 0 or index >= nodes.size():
		return Vector3.INF
	return nodes[index]


## **A wheeled guest snaps only to nodes it could actually leave.** Nearest by
## distance alone will happily put a wheelchair on the middle of a garden stair,
## where it then has no step-free edge and stands still forever. Falls back to
## the plain nearest if the step-free sweep reached nothing, so a graph with no
## flags behaves exactly as it did before.
func nearest_node(point: Vector3, wheeled := false) -> int:
	var best := -1
	var best_distance := INF
	for i in nodes.size():
		if wheeled and not _depth_flat.is_empty() and _depth_flat[i] < 0:
			continue
		var d := point.distance_squared_to(nodes[i])
		if d < best_distance:
			best_distance = d
			best = i
	if best < 0 and wheeled:
		return nearest_node(point, false)
	return best


## A wander rather than a path: pick a start, walk a few edges without doubling
## straight back. Guests are not going anywhere, so pathfinding would be a lie
## about their intentions as well as an expense.
##
## The hour leans on it. At eleven the plaza is full of people who have just
## come through the gate and are heading in; at nine it is full of people
## heading back out. `FLOW_WEIGHT` keeps that a bias and not an instruction —
## enough that the drift is visible over a minute of watching, not so much that
## anybody appears to be under orders.
func route_from(point: Vector3, route_seed: int, wheeled := false) -> PackedInt32Array:
	var route := PackedInt32Array()
	var adjacency: Array = _adjacency_flat if wheeled else _adjacency
	var current := nearest_node(point, wheeled)
	if current < 0:
		return route

	_route_rng.seed = route_seed
	var flow := _curve_at(flow_day, ParkClock.hours())
	var previous := -1
	var hops := _route_rng.randi_range(route_hops.x, route_hops.y)
	for _i in hops:
		var options: PackedInt32Array = adjacency[current]
		if options.is_empty():
			break
		var choices := PackedInt32Array()
		for option in options:
			if option != previous:
				choices.append(option)
		if choices.is_empty():
			choices = options
		var next := _pick_hop(choices, current, flow)
		route.append(next)
		previous = current
		current = next
	return route


## Weighted by whether a hop goes deeper into the plaza or back towards the
## gate. Weights are floored well above zero so that no direction is ever shut
## off — the last hour still has people wandering the wrong way, because it
## would otherwise read as the park being evacuated.
func _pick_hop(choices: PackedInt32Array, current: int, flow: float) -> int:
	if absf(flow) < 0.01 or _depth.is_empty() or _depth[current] < 0:
		return choices[_route_rng.randi_range(0, choices.size() - 1)]

	var weights := PackedFloat32Array()
	var total := 0.0
	for option in choices:
		var w := 1.0
		if _depth[option] >= 0:
			var deeper := float(_depth[option] - _depth[current])
			w = maxf(0.2, 1.0 + flow * deeper * FLOW_WEIGHT)
		weights.append(w)
		total += w

	var roll := _route_rng.randf() * total
	for i in choices.size():
		roll -= weights[i]
		if roll <= 0.0:
			return choices[i]
	return choices[choices.size() - 1]


func poi_near(point: Vector3, radius: float) -> Vector3:
	var best := Vector3.INF
	var best_distance := radius * radius
	for poi in pois:
		var flat := Vector3(poi.x - point.x, 0.0, poi.z - point.z)
		var d := flat.length_squared()
		# Directly underfoot is not something anyone looks at.
		if d < 1.5 or d > best_distance:
			continue
		best_distance = d
		best = poi
	return best


# --- guests -----------------------------------------------------------------


## The whole cast, whether or not they are in the park. Called from every
## guest's `_ready`, which is before this node's, so the roster is complete
## before anything is asked of it.
func register(guest: Node) -> void:
	if guest in _roster:
		return
	_roster.append(guest)
	var id: int = guest.group_id
	if not _groups.has(id):
		_groups[id] = []
	_groups[id].append(guest)


func unregister(guest: Node) -> void:
	_roster.erase(guest)
	guests.erase(guest)
	var id: int = guest.group_id
	if _groups.has(id):
		_groups[id].erase(guest)


## `guests` is only the people actually in the park. Everything that costs per
## guest and per frame — separation, the alert scan, finding who the player is
## looking at — runs off this list rather than off the roster, so an hour with
## twenty people in the plaza costs what twenty people cost.
func set_live(guest: Node, live: bool) -> void:
	if live:
		if not guest in guests:
			guests.append(guest)
	else:
		guests.erase(guest)


## Everyone in the same group except the guest asking, and only those actually
## here. Singles get an empty list, which is the point of them.
func companions(guest: Node) -> Array:
	var group: Array = _groups.get(guest.group_id, [])
	var result: Array = []
	for other in group:
		if other != guest and is_instance_valid(other) and other.is_live():
			result.append(other)
	return result


# --- noticing ---------------------------------------------------------------


## A guest reporting that they have just clocked the camera, whether they saw
## it themselves or caught it off somebody else. Both spread it onward — that
## is what makes it a chain rather than a single ring.
func report_notice(guest: Node) -> void:
	_alerts.append({"guest": guest, "age": 0.0})


func _age_alerts(delta: float) -> void:
	for i in range(_alerts.size() - 1, -1, -1):
		var alert: Dictionary = _alerts[i]
		alert.age += delta
		if alert.age > ALERT_FRESHNESS or not is_instance_valid(alert.guest):
			_alerts.remove_at(i)


## The nearest guest within `radius` who noticed recently enough to be worth
## noticing in turn, skipping any the asker has already shrugged off.
func fresh_alert_near(asker: Node3D, radius: float, declined: Array) -> Node:
	var best: Node = null
	var best_distance := radius * radius
	for alert in _alerts:
		var guest := alert.guest as Node3D
		if guest == null or guest == asker or not is_instance_valid(guest):
			continue
		if guest.get_instance_id() in declined:
			continue
		var d := asker.global_position.distance_squared_to(guest.global_position)
		if d > best_distance:
			continue
		best_distance = d
		best = guest
	return best


# --- interaction ------------------------------------------------------------


## The guest nearest the centre of the view, close enough to talk to. Look is
## the pointer: there is no cursor and no highlight, and the only feedback that
## someone is reachable is that they look back at you.
func interaction_candidate(from: Vector3, forward: Vector3, max_distance := 3.6,
		max_angle := deg_to_rad(28.0)) -> Node:
	var best: Node = null
	var best_angle := max_angle
	for entry in guests:
		var guest := entry as Node3D
		if guest == null or not is_instance_valid(guest):
			continue
		var to_guest := guest.global_position - from
		to_guest.y = 0.0
		var distance := to_guest.length()
		if distance > max_distance or distance < 0.01:
			continue
		var angle := forward.normalized().angle_to(to_guest / distance)
		if angle < best_angle:
			best_angle = angle
			best = guest
	return best


## Asking one guest asks the group they came with. Nobody in a park is
## photographed alone by accident.
func ask_to_pose(guest: Node, anchor: Vector3) -> int:
	if guest == null or not is_instance_valid(guest):
		return 0
	var asked := 1
	guest.ask_to_pose(anchor)
	for companion in companions(guest):
		if companion.global_position.distance_to(guest.global_position) > 9.0:
			continue
		companion.ask_to_pose(anchor)
		asked += 1
	return asked
