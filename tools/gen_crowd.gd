extends SceneTree

## Dev tool: builds the plaza's crowd and saves it as its own scene.
##
## Like `gen_props.gd` this is generated output — a guest moved or recoloured by
## hand in the editor is lost the next time this runs. Behaviour is not
## generated; it lives in `scenes/npc/guest.gd` and is meant to be edited.
##
## Bodies are MeshInstance3D over shared unit meshes rather than CSG. The props
## are CSG because they are static and never move; thirty-six guests with
## swinging limbs are neither, and sharing one BoxMesh across five hundred parts
## costs a fraction of five hundred CSG brushes.
##
##   godot --headless --path . --script res://tools/gen_crowd.gd

const OUT_PATH := "res://scenes/world/plaza_crowd.tscn"
const BOARDWALK_PATH := "res://scenes/world/boardwalk_crowd.tscn"
const TERRACES_PATH := "res://scenes/world/terraces_crowd.tscn"
const GUEST_SCRIPT := "res://scenes/npc/guest.gd"
const CROWD_SCRIPT := "res://scenes/npc/crowd.gd"

## The park's plan, for the boardwalk half. Same reasoning as `gen_props.gd`:
## preloaded rather than reached for by `class_name`, because this file runs
## under `--script` and that compiles before the script registry is up.
## `park_plan.gd` is autoload-free, which is what makes the preload safe.
const Plan := preload("res://scripts/park_plan.gd")

## Guest radius plus room to not scrape. Anything closer than this to a prop
## counts as blocked.
const CLEARANCE := 0.45

## How many guests the cast should come to, padded with procedural groups if the
## authored list is short of it. Zero means no padding, which is the authored 56.
##
## **This is a measuring knob, not a design.** The list in `_plaza_walking_groups` is
## composed — the front of it is what the opening hour looks like — and nothing
## `_pad_cast` adds is composed at all. It exists because the estimate of a real
## peak for a plaza this size is 320 to 640 people, the cast is 56, and the
## cheap way to find out where the plain path stops holding is to raise the
## number and watch the frame time rather than to design a tiering scheme
## against a guess.
##
## The padding runs last, after the authored cast is complete, so the 56 come
## out byte-identical whatever this is set to and setting it back to 0
## reproduces the committed scene exactly. Seated groups are not padded — the
## plaza has fourteen bench seats and six chairs, and that is the constraint
## rather than an oversight. Extra people walk.
const CAST_TARGET := 0

var _root: Node3D
var _rng := RandomNumberGenerator.new()
var mats: Dictionary = {}
var _box: BoxMesh
var _cyl: CylinderMesh
var _sphere: SphereMesh
## A rounder cylinder and a ring, for wheels only. Eight sides is plenty for a
## cup held at arm's length and is plainly an octagon on a 65cm wheel standing at
## the front of the shot — a wheel is the one round thing in this park that the
## player gets close to.
var _wheel_cyl: CylinderMesh
var _tyre_ring: TorusMesh
var _ring: TorusMesh

var _graph_names: PackedStringArray = PackedStringArray()
var _graph_points: PackedVector3Array = PackedVector3Array()
var _graph_edges: PackedInt32Array = PackedInt32Array()
## One byte per edge pair: 1 if it has steps on it. See `crowd.gd`'s `edge_steps`
## for why this exists now and could not have meant anything before the climb.
var _graph_steps: PackedByteArray = PackedByteArray()

var _guest_index := 0
var _group_index := 0

## The floor the section stands on. Zero in the plaza; the boardwalk is six
## metres down, and a guest generated at y = 0 down there is a guest standing in
## the air above the promenade.
var _floor := 0.0

## How far out a node may be before the validator calls it outside the section.
## A sanity bound rather than a wall — it catches a node typed with a sign
## wrong, which is the mistake that otherwise produces a guest walking calmly
## into the sea.
var _bounds := Rect2(-36.0, -36.0, 72.0, 72.0)

## The obstacles of whichever section is being built, set before validating.
var _obstacles: Array = []


func _initialize() -> void:
	_build_resources()
	if not _build_plaza():
		return
	if not _build_boardwalk():
		return
	if not _build_terraces():
		return
	quit()


## Reset everything a section owns. The two passes share the body-building and
## nothing else, and the plaza must come out byte-identical to what is committed
## — so it runs first, with its seed set here rather than once at startup.
func _begin(nm: String, floor_y: float, bounds: Rect2, seed_value: int) -> void:
	_rng.seed = seed_value
	_graph_names = PackedStringArray()
	_graph_points = PackedVector3Array()
	_graph_edges = PackedInt32Array()
	_graph_steps = PackedByteArray()
	_guest_index = 0
	_group_index = 0
	_floor = floor_y
	_bounds = bounds
	_obstacles = []
	_root = Node3D.new()
	_root.name = nm
	_root.set_script(load(CROWD_SCRIPT))


func _finish(path: String) -> bool:
	var saved := _save(_root, path)
	# Nothing here was ever added to a tree, so it has to be released by hand.
	_root.free()
	_root = null
	if not saved:
		return false
	return true


func _build_plaza() -> bool:
	# Fixed seed: this file is committed, so the same source must produce the
	# same scene or every run shows up as a diff.
	_begin("crowd", 0.0, Rect2(-48.0, -48.0, 96.0, 96.0), 0x5150)

	_plaza_graph()
	_obstacles = _plaza_obstacles()
	if not _validate_graph():
		push_error("plaza graph is not walkable — fix the nodes above before regenerating")
		quit(1)
		return false

	_root.set("nodes", _graph_points)
	_root.set("edges", _graph_edges)
	_root.set("edge_steps", _graph_steps)
	_root.set("pois", _reachable_pois("plaza", _plaza_pois(), _plaza_seats()))

	# The way in and out, and where off-stage is. z=45 is the entrance street's
	# own ground, six metres beyond the perimeter wall, in the middle lane
	# between two ranges of shopfronts that stand at x −9 and +6. Nobody in the
	# plaza is looking at it unless they are looking down the street at the
	# gate — which is exactly the case the crowd checks for before using it.
	_root.set("entry_node", _node_index("gate"))
	_root.set("hold_point", Vector3(-1.5, 0.0, 45.0))

	_plaza_walking_groups()
	_plaza_seated_groups()
	_pad_cast()
	return _finish(OUT_PATH)


func _save(node: Node3D, path: String) -> bool:
	var packed := PackedScene.new()
	var err := packed.pack(node)
	if err != OK:
		push_error("pack failed: %d" % err)
		quit(1)
		return false
	err = ResourceSaver.save(packed, path)
	if err != OK:
		push_error("save failed: %d" % err)
		quit(1)
		return false
	print("wrote %d guests (%d nodes total) to %s" % [
		node.get_child_count(), _count(node), path])
	return true


func _count(node: Node) -> int:
	var total := 1
	for child in node.get_children():
		total += _count(child)
	return total


# --- palette ----------------------------------------------------------------


func _build_resources() -> void:
	# Late-nineties park crowd: saturated primaries gone slightly chalky,
	# denim, khaki, and a couple of colours nobody would choose now.
	var defs := {
		"shirt_teal": Color(0.24, 0.58, 0.55),
		"shirt_purple": Color(0.44, 0.34, 0.6),
		"shirt_mustard": Color(0.85, 0.68, 0.24),
		"shirt_salmon": Color(0.88, 0.52, 0.45),
		"shirt_white": Color(0.9, 0.89, 0.86),
		"shirt_red": Color(0.79, 0.28, 0.26),
		"shirt_lime": Color(0.65, 0.78, 0.32),
		"shirt_denim": Color(0.42, 0.52, 0.66),
		"shirt_forest": Color(0.26, 0.42, 0.31),
		"shirt_lilac": Color(0.74, 0.66, 0.79),
		"shirt_orange": Color(0.88, 0.55, 0.24),
		"shirt_grey": Color(0.55, 0.55, 0.57),
		"bottom_denim": Color(0.3, 0.36, 0.48),
		"bottom_khaki": Color(0.71, 0.65, 0.5),
		"bottom_black": Color(0.22, 0.22, 0.24),
		"bottom_olive": Color(0.42, 0.43, 0.3),
		"bottom_grey": Color(0.45, 0.45, 0.47),
		"bottom_maroon": Color(0.42, 0.26, 0.28),
		"skin_0": Color(0.95, 0.8, 0.68),
		"skin_1": Color(0.87, 0.7, 0.56),
		"skin_2": Color(0.76, 0.58, 0.44),
		"skin_3": Color(0.6, 0.43, 0.32),
		"skin_4": Color(0.44, 0.31, 0.24),
		"skin_5": Color(0.3, 0.21, 0.17),
		"hair_black": Color(0.13, 0.12, 0.12),
		"hair_dark": Color(0.24, 0.17, 0.13),
		"hair_brown": Color(0.36, 0.25, 0.17),
		"hair_sandy": Color(0.62, 0.5, 0.31),
		"hair_ginger": Color(0.6, 0.32, 0.16),
		"hair_grey": Color(0.68, 0.67, 0.65),
		"metal": Color(0.3, 0.31, 0.33),
		"plastic": Color(0.85, 0.84, 0.8),
		# The chairs. Powder-coated frames in colours a chair actually came in,
		# chrome for the push rims, dark rubber for the tyres and dark nylon for
		# the upholstery. Prefixed `frame_` so `_pick` draws from them the way it
		# draws shirts — a park where every wheelchair is the same colour is a
		# park with a fleet of them rather than a park with people in them.
		"frame_chrome": Color(0.63, 0.64, 0.67),
		"frame_blue": Color(0.2, 0.33, 0.56),
		"frame_red": Color(0.6, 0.2, 0.21),
		"frame_violet": Color(0.37, 0.28, 0.5),
		"frame_teal": Color(0.16, 0.42, 0.44),
		"frame_black": Color(0.19, 0.19, 0.21),
		"tyre": Color(0.13, 0.13, 0.14),
		"nylon": Color(0.16, 0.17, 0.2),
	}
	for key in defs:
		var m := StandardMaterial3D.new()
		m.albedo_color = defs[key]
		m.roughness = 0.9 if key.begins_with("skin") else 0.85
		if key == "metal":
			m.roughness = 0.55
			m.metallic = 0.2
		elif key.begins_with("frame_"):
			m.roughness = 0.42
			m.metallic = 0.35
		elif key == "tyre":
			m.roughness = 0.95
		mats[key] = m

	_box = BoxMesh.new()
	_box.size = Vector3.ONE
	_cyl = CylinderMesh.new()
	_cyl.top_radius = 0.5
	_cyl.bottom_radius = 0.5
	_cyl.height = 1.0
	_cyl.radial_segments = 8
	_cyl.rings = 1
	_sphere = SphereMesh.new()
	_sphere.radius = 0.5
	_sphere.height = 1.0
	_sphere.radial_segments = 10
	_sphere.rings = 6
	_wheel_cyl = CylinderMesh.new()
	_wheel_cyl.top_radius = 0.5
	_wheel_cyl.bottom_radius = 0.5
	_wheel_cyl.height = 1.0
	_wheel_cyl.radial_segments = 16
	_wheel_cyl.rings = 1
	# The tyre and the hand rim, both rings and neither a disc. They were discs
	# first, and a disc is wrong twice over: a hubcap-sized rim filled the wheel
	# and turned a wheelchair into a car wheel, and a filled tyre buried the
	# spokes inside itself — so the one part that shows a wheel turning could not
	# be seen, and a rolling chair had three motionless dark circles under it.
	# A tyre is a ring with spokes across the hole, which is also the only shape
	# that makes the rotation legible.
	_tyre_ring = TorusMesh.new()
	_tyre_ring.outer_radius = 0.5
	_tyre_ring.inner_radius = 0.42
	_tyre_ring.rings = 20
	_tyre_ring.ring_segments = 6
	_ring = TorusMesh.new()
	_ring.outer_radius = 0.5
	_ring.inner_radius = 0.455
	_ring.rings = 16
	_ring.ring_segments = 5


func _pick(prefix: String) -> String:
	var keys: Array = []
	for key in mats:
		if key.begins_with(prefix):
			keys.append(key)
	keys.sort()
	return keys[_rng.randi_range(0, keys.size() - 1)]


# --- the walkable graph -----------------------------------------------------


## Named so the edge list reads as a description of the plaza rather than as a
## table of indices. Positions are on the ground; guests walk to them exactly,
## plus a per-guest wander offset, so a node is a loose destination and not a
## mark to stand on.
func _plaza_graph() -> void:
	# Every position here survived `_validate_graph`, and several of them are not
	# where they were first put. What the validator turned up: the south side of
	# the plaza is not a corridor. `bench_south`, `bench_sw` and `planter_b`
	# between them leave no gap wide enough to walk along the south wall, so
	# east–west traffic goes around the fountain instead. That is what a real
	# plaza does, and it was found by checking rather than by deciding.
	var points := {
		# The plaza mouth, and the south walk in from it.
		"gate": Vector2(-1.5, 41.0),
		"south": Vector2(-1.5, 30.0),
		"south_east": Vector2(12.0, 22.0),
		"south_west": Vector2(-24.0, 26.0),
		# The photo hut, out at radius 28 now, with its queue on the south side.
		"hut_walk": Vector2(14.0, 18.0),
		"queue": Vector2(17.0, 27.0),
		# The street out to the south-east threshold, which the crowd walks the
		# near end of and no further — past the mouth is scaffolding.
		"street_n": Vector2(22.0, 11.0),
		"east": Vector2(25.0, -2.0),
		"east_n": Vector2(24.0, -18.0),
		"north": Vector2(5.0, -25.0),
		# In front of the clock tower. The node kept its name when the tower moved
		# onto the axis, because what it means — the walk under the sign — did not.
		"sign": Vector2(-1.5, -26.0),
		"band_e": Vector2(-11.0, -20.0),
		"band_n": Vector2(-17.0, -31.0),
		"band_w": Vector2(-31.0, -30.0),
		"west": Vector2(-24.0, -6.0),
		# In front of the arch, and it has to stay in front of it. This was
		# (−30, −2), which was three metres clear of a wall face at −33; the arch
		# became a tunnel on 2026-08-14 and its gate house came forward to −30.5,
		# which left the node half a metre inside the throat with guests standing
		# in a 6m passage the player crosses a section seam in.
		"west_n": Vector2(-27.0, -2.0),
		"cafe": Vector2(-22.0, 8.0),
		"west_s": Vector2(-22.0, 20.0),
		# The ring, at r=16 where the walkway is. Nine nodes now rather than eight:
		# the south-east arc was missing because the photo hut used to stand in it,
		# and with the hut moved out the ring closes properly.
		"ring_s": Vector2(0.0, 16.0),
		"ring_se": Vector2(11.0, 11.0),
		"ring_e": Vector2(16.0, 0.0),
		"ring_ne": Vector2(11.0, -11.0),
		"ring_n": Vector2(0.0, -16.0),
		"ring_nw": Vector2(-8.0, -14.0),
		"ring_wnw": Vector2(-15.0, -11.0),
		"ring_w": Vector2(-19.0, 0.0),
		"ring_sw": Vector2(-11.0, 11.0),
	}
	for name in points:
		_graph_names.append(name)
		var p: Vector2 = points[name]
		_graph_points.append(Vector3(p.x, _floor, p.y))

	# `band_w` is deliberately a dead end. The crates parked against the west
	# wall block the corridor down the bandstand's blind side, so the only way
	# in is from the north — which is exactly the kind of thing the player is
	# meant to learn about this place by walking it.
	var links := [
		["gate", "south"],
		["south", "south_east"], ["south", "south_west"], ["south", "ring_s"],
		["south_east", "queue"], ["south_east", "hut_walk"],
		["queue", "hut_walk"],
		["hut_walk", "ring_se"],
		["street_n", "east"], ["street_n", "ring_se"], ["street_n", "ring_e"],
		["east", "ring_e"], ["east", "east_n"],
		["east_n", "north"], ["east_n", "ring_ne"],
		["north", "sign"], ["north", "ring_n"], ["north", "ring_ne"],
		["sign", "band_e"], ["sign", "band_n"], ["sign", "ring_n"],
		["band_e", "ring_n"],
		["band_n", "band_w"],
		["west", "west_n"], ["west", "cafe"], ["west", "ring_w"],
		["west", "ring_wnw"],
		["cafe", "west_s"], ["cafe", "ring_sw"],
		["west_s", "south_west"],
		# The ring, closed.
		["ring_s", "ring_se"], ["ring_se", "ring_e"], ["ring_e", "ring_ne"],
		["ring_ne", "ring_n"], ["ring_n", "ring_nw"], ["ring_nw", "ring_wnw"],
		["ring_wnw", "ring_w"], ["ring_w", "ring_sw"], ["ring_sw", "ring_s"],
	]
	for link in links:
		_edge(link[0], link[1], false)


## One edge, and whether a foot has to leave the ground to use it.
func _edge(a: String, b: String, stepped: bool) -> void:
	_graph_edges.append(_node_index(a))
	_graph_edges.append(_node_index(b))
	_graph_steps.append(1 if stepped else 0)


## **The east, and the first ground in the park where the route matters more than
## the distance.** The plaza graph stopped at x 25 — eleven metres short of the
## east wall's inner face — so no guest had ever been through the gate, into the
## forecourt, onto the cascade or up the hill.
##
## Both climbs carry a ramp on the north and a stair on the south between the
## same two points, so every level here is reachable either way and only one of
## the two ways has steps in it. That is what makes `edge_steps` a fact about the
## park rather than a flag nothing sets.
##
## Node heights are real. The rest of the graph is flat at `_floor` because the
## plaza is; this climbs twelve metres, and a guest walking to a node whose y is
## a lie walks into the hillside.
func _east_graph() -> void:
	var axis: float = Plan.ARCH_AT.y
	var fz: float = Plan.climb_flight_z()

	# Every node first, then every edge. `_node_index` resolves by name against
	# what is already there, so a link written ahead of its node is a push_error
	# and a −1 index rather than a forward reference.
	_node("e_gate", Vector3(43.0, 0.0, axis))
	_node("e_court", Vector3(52.0, 0.0, axis))
	_node("e_belv", Vector3(74.0, Plan.HILL_TOP, axis))
	_node("e_belv_n", Vector3(78.0, Plan.HILL_TOP, axis - 7.0))
	_node("e_belv_s", Vector3(78.0, Plan.HILL_TOP, axis + 7.0))
	_node("e_top", Vector3(Plan.CLIMB_TO_X + 4.0, Plan.TERRACE_TWO_Y, axis))
	# **No link back to `ring_e`.** It was there while the east lived in the
	# plaza's graph, and the split made it a dangling name: the plaza's ring is
	# not in this section and the seam at the gate is what joins the two, not an
	# edge. `e_gate` is the entry node, which is the same job `lane_s` does on the
	# boardwalk.
	_edge("e_gate", "e_court", false)

	# The monument's own wings. North is the ramp and south the garden stair, and
	# that difference is the whole reason this graph knows about steps.
	for w in [[-1.0, "n", false], [1.0, "s", true]]:
		var side: float = w[0]
		var tag: String = w[1]
		var stepped: bool = w[2]
		var path: Array = Plan.wing_path(Plan.CASCADE_EAST, side)
		for i in path.size():
			var v: Vector3 = path[i]
			_node("e_wing_%s_%d" % [tag, i], v)
		_edge("e_court", "e_wing_%s_3" % tag, false)
		for i in range(3, 0, -1):
			_edge("e_wing_%s_%d" % [tag, i], "e_wing_%s_%d" % [tag, i - 1], stepped)
		_edge("e_wing_%s_0" % tag, "e_belv", false)

	# The belvedere, either side of the collecting pool.
	_edge("e_belv", "e_belv_n", false)
	_edge("e_belv", "e_belv_s", false)

	# The staircase. One node per reach boundary on each run, so a guest walking
	# it stops where the floor changes what it is doing.
	var reaches: Array = Plan.climb_reaches()
	var bay := 0
	for w in [[-1.0, "n", false], [1.0, "s", true]]:
		var side: float = w[0]
		var tag: String = w[1]
		var stepped: bool = w[2]
		var zc: float = axis + side * fz
		_node("e_climb_%s_0" % tag, Vector3(Plan.CLIMB_FROM_X, Plan.HILL_TOP, zc))
		_edge("e_belv_%s" % tag, "e_climb_%s_0" % tag, false)
		for ri in reaches.size():
			var r: Array = reaches[ri]
			_node("e_climb_%s_%d" % [tag, ri + 1],
				Vector3(float(r[1]), float(r[3]), zc))
			# A flight is stepped on the south run and a ramp on the north; a
			# terrace is level on both, so it never is.
			_edge("e_climb_%s_%d" % [tag, ri], "e_climb_%s_%d" % [tag, ri + 1],
				stepped and bool(r[4]))
		_edge("e_climb_%s_%d" % [tag, reaches.size()], "e_top", false)

	# The bays, hung off the landing that serves them. Always step-free: a shelf
	# you can only reach up a stair is a shop half the park cannot go into.
	for ri in reaches.size():
		var r: Array = reaches[ri]
		# Narrow landings carry no bay — see `CLIMB_BAY_MIN_T`.
		if bool(r[4]) or float(r[1]) - float(r[0]) < Plan.CLIMB_BAY_MIN_T:
			continue
		var bx: float = (float(r[0]) + float(r[1])) * 0.5
		var bd: float = Plan.CLIMB_BAY_D
		for w in [[-1.0, "n"], [1.0, "s"]]:
			var side: float = w[0]
			var tag: String = w[1]
			_node("e_bay_%s_%d" % [tag, bay],
				Vector3(bx, float(r[2]),
					axis + side * (Plan.CLIMB_HALF_Z + bd * 0.55)))
			_edge("e_climb_%s_%d" % [tag, ri + 1], "e_bay_%s_%d" % [tag, bay], false)
		bay += 1


func _node(name: String, at: Vector3) -> void:
	if _graph_names.find(name) >= 0:
		return
	_graph_names.append(name)
	_graph_points.append(at)


func _node_index(name: String) -> int:
	var i := _graph_names.find(name)
	if i < 0:
		push_error("unknown graph node: %s" % name)
	return i


## Everything a guest could walk into, as circles and axis-aligned rectangles.
## Approximate on purpose: a rotated bench treated as a circle costs a few
## centimetres of plaza and saves an oriented-box test.
##
## Only things you would actually walk around are here. Bins, lamp posts,
## litter, newspaper boxes and the loose stroller are all left out on purpose —
## people brush past those without thinking, the per-guest wander offset already
## keeps nobody on the exact line, and treating a 36cm bin as a wall was closing
## corridors that are genuinely walkable.
func _plaza_obstacles() -> Array:
	var out: Array = []

	# Props, at the positions `gen_props.gd` placed them *before* the dilation —
	# put through the same map below, so this list stays readable as the layout
	# somebody typed rather than as a column of arithmetic.
	#
	# The third column is the margin `gen_props.gd` stands each of them clear of
	# the paving by, and it is not the same as the radius: a prop is pushed off
	# the walkway by more than it is wide, so that there is a walk beside it and
	# not merely a squeeze. **A zero here means the prop is placed where it is
	# written** — the crates and the ladder lean on buildings and never moved.
	#
	# Getting this column wrong is quiet rather than loud: the guest graph would
	# route round a cart that is four metres away and walk through the one that is
	# there. Which is the same failure the terrace had, in the same file.
	var circles := [
		[Vector2(-6, -10), 1.3, 1.5],     # cart
		[Vector2(-19, -6), 1.0, 0.0],     # crates
		[Vector2(-13, 18), 1.3, 1.4],     # picnic tables
		[Vector2(-17, 15), 1.3, 1.4],
		[Vector2(3, 10), 0.65, 0.8],      # a-frames
		[Vector2(-9, -2), 0.65, 0.8],
		[Vector2(12, -8), 0.65, 0.8],
		[Vector2(19.3, 2.0), 0.6, 0.0],   # ladder
	]
	for spot in circles:
		var at: Vector2 = Plan.plaza_out2(spot[0])
		if float(spot[2]) > 0.0:
			at = Plan.clear_of_walkways(at, spot[2])
		out.append({"kind": "circle", "at": at, "r": spot[1]})

	# The flagpoles are one assembly with two poles 5m apart, so they are stood
	# clear as a pair and then modelled as a pair — two circles hung off the one
	# base, the way `gen_props.gd` builds them. Listed separately from the rest
	# because nothing else in the plaza has an offset from its own stand point.
	var flags := Plan.clear_of_walkways(Plan.plaza_out2(Vector2(18, -16)), 3.0)
	for dx in [-2.5, 2.5]:
		out.append({"kind": "circle", "at": flags + Vector2(dx, 0.0), "r": 0.25})

	# The fountain is not dilated: it is the thing the map is measured from, and
	# its radius is plan data.
	out.append({"kind": "circle", "at": Plan.FOUNTAIN_AT, "r": Plan.FOUNTAIN_RADIUS})

	# Each cafe table and its two chairs, from the plan. **This was a third copy
	# of the same three coordinates** — `gen_props.gd` had them, the chair-spot
	# mirror had them, and so did this list, which is the one that decides
	# whether a corridor is walkable. Moving the terrace with only two of the
	# three updated left the validator holding a table at (17,8) that no longer
	# existed, and it duly reported the new street as blocked by it. Right to
	# complain, wrong about why, which is the worst kind of correct.
	#
	# The umbrella above each is 2.3m up and overhangs rather than blocks.
	for spec in Plan.PLAZA_CAFE:
		out.append({"kind": "circle", "at": spec["at"], "r": 1.15})

	# The outer room's benches and flower beds, asked for with the same arguments
	# `gen_props.gd` stands them on. Trees, bins and litter are left out for the
	# same reason the lamp posts are: people brush past those without thinking,
	# and treating them as walls closes corridors that are genuinely walkable.
	for at in Plan.ring_verge(1.8, 2.2):
		out.append({"kind": "circle", "at": at, "r": 1.05})

	for spot in _plaza_bench_spots():
		out.append({"kind": "circle", "at": Vector2(spot["at"].x, spot["at"].z), "r": 1.05})

	# The plaza's own masses, from the plan. This was a typed copy of
	# `plaza.tscn` and the third survey of the same buildings; when the plaza grew
	# every line of it was wrong at once.
	for m in Plan.PLAZA_MASSES:
		out.append({"kind": "rect", "at": m["at"], "half": m["half"]})

	# The hut's queue rope, which belongs to the hut rather than to the plan.
	out.append({"kind": "rect", "at": Vector2(Plan.PHOTO_HUT_AT.x, Plan.PHOTO_HUT_AT.y + 4.5),
		"half": Vector2(3.2, 0.2)})

	# The bollard lines, which are props and so are dilated like the rest.
	for at in [Vector2(2, -20), Vector2(0, 30)]:
		out.append({"kind": "rect", "at": Plan.plaza_out2(at), "half": Vector2(8.0, 0.2)})

	return out


func _blocked(p: Vector2, obstacles: Array) -> String:
	if not _bounds.has_point(p):
		return "outside the section"
	for i in obstacles.size():
		var o: Dictionary = obstacles[i]
		if o["kind"] == "circle":
			if p.distance_to(o["at"]) < o["r"] + CLEARANCE:
				return "circle at %v" % o["at"]
		else:
			var d: Vector2 = (p - o["at"]).abs() - o["half"]
			var outside := Vector2(maxf(d.x, 0.0), maxf(d.y, 0.0))
			var distance := outside.length() if outside != Vector2.ZERO else maxf(d.x, d.y)
			if distance < CLEARANCE:
				return "rect at %v" % o["at"]
	return ""


## The whole point of generating the graph is that the graph can be checked.
## Every node and every edge is walked at 0.35m and tested for clearance, so a
## path that runs through a planter is a build error rather than something to
## notice later while playing.
func _validate_graph() -> bool:
	var obstacles := _obstacles
	var ok := true

	for i in _graph_points.size():
		var p := Vector2(_graph_points[i].x, _graph_points[i].z)
		var why := _blocked(p, obstacles)
		if why != "":
			push_error("node '%s' at %v is blocked by %s" % [_graph_names[i], p, why])
			ok = false

	var pairs := _graph_edges.size() / 2
	for e in pairs:
		var a_index := _graph_edges[e * 2]
		var b_index := _graph_edges[e * 2 + 1]
		var a := Vector2(_graph_points[a_index].x, _graph_points[a_index].z)
		var b := Vector2(_graph_points[b_index].x, _graph_points[b_index].z)
		var length := a.distance_to(b)
		var steps := maxi(int(length / 0.35), 1)
		for s in range(1, steps):
			var p: Vector2 = a.lerp(b, float(s) / float(steps))
			var why := _blocked(p, obstacles)
			if why != "":
				push_error("edge %s–%s is blocked at %v by %s" % [
					_graph_names[a_index], _graph_names[b_index], p, why])
				ok = false
				break
	return ok


## Things a guest might plausibly look at. Height matters: the clock tower is a
## different photograph looked up at than looked across.
##
## **Every entry is derived from where the thing actually is.** The list used to
## be sixteen literals, and on 2026-08-14c all but three of them were measured
## against the props they name:
##
## | written | claims to be | nearest real prop |
## |---|---|---|
## | (9, 6) | the photo hut counter | a bench on the fountain skirt, 0.5m |
## | (5.8, 5.1) | the tied balloons | a bench leg, 3.2m |
## | (-12, -12) | the bandstand stage | 7.2m from anything |
## | (18, -16) | the sign board | a lamp head, 3.8m |
## | (3, 7.5) | the newspaper boxes | 2.6m off |
##
## They are the **80m plaza's** coordinates. Everything else in this file was put
## through `ParkPlan.plaza_out` when the plaza grew on 2026-08-13 and this was
## not, so the whole crowd has been looking at where the park used to be for a
## day. It is the same fault as the balloons and it stayed hidden for the same
## reason: a guest staring at empty air two metres from a bench photographs as a
## guest looking at a bench.
##
## So nothing here is typed twice. Plan data where there is plan data, and the
## same `plaza_out` + `clear_of_walkways` pipeline the props themselves went
## through where there is not — if a prop moves, the eyes follow it.
##
## **The three "over the wall" entries are gone.** The wheel, the observation
## tower and the coaster were listed on the argument that "guests looking up and
## out at rides they cannot reach is most of what sells the plaza as a hub",
## which is a good argument and has never once fired: `guest.gd` asks
## `poi_near` for something within nine metres, and those three are 31m, 37m and
## 27m from the nearest node of the plaza's own graph. A landmark POI needs a
## mechanism — a per-POI range, or a separate distant-attention pass — and not a
## coordinate. Deleting them changes no behaviour whatsoever, which is exactly
## the problem with having kept them.
func _plaza_pois() -> PackedVector3Array:
	var out := PackedVector3Array()
	out.append_array(_fountain_pois())

	# The clock, which is the park's one readout and the thing the entrance
	# street is aimed at. Well over the head-pitch limit from anywhere a guest
	# can stand, so what this actually produces is a head tilted as far back as
	# it goes — which is the right picture.
	out.append(Vector3(Plan.CLOCK_TOWER_AT.x, 21.0, Plan.CLOCK_TOWER_AT.y))
	# The counter of the hut the player works out of.
	out.append(Vector3(Plan.PHOTO_HUT_AT.x, 2.0, Plan.PHOTO_HUT_AT.y))
	# The bandstand's stage. Hand-placed in `plaza.tscn` at final coordinates,
	# and `_plaza_bench_spots` already knows the same number.
	out.append(Vector3(BANDSTAND_AT.x, 1.6, BANDSTAND_AT.z))

	for spec in Plan.PLAZA_CAFE:
		var at: Vector2 = spec["at"]
		out.append(Vector3(at.x, 1.15, at.y))

	# The snack cart, the a-frames and the newspaper boxes, each through the
	# same two steps `gen_props.gd` puts them through: the dilation, then the
	# push off the paving with that prop's own margin. The margins are the ones
	# in `_plaza_obstacles`, which is the list that already had to agree.
	out.append(_prop_poi(Vector2(-6, -10), 1.5, 1.5))
	for at in [Vector2(3, 10), Vector2(-9, -2), Vector2(12, -8)]:
		out.append(_prop_poi(at, 0.8, 1.0))
	out.append(_prop_poi(Vector2(3, 7.5), 0.8, 0.95))

	# The two balloons on the rail of the hut's bench — which is where they have
	# been since this morning and nowhere near where this list had them.
	var bench := Vector3(Plan.PHOTO_HUT_AT.x, 0.0, Plan.PHOTO_HUT_AT.y) \
		+ Plan.PHOTO_HUT_BENCH
	out.append(bench + Basis(Vector3.UP, deg_to_rad(Plan.PHOTO_HUT_BENCH_YAW))
		* Vector3(0.63, 2.2, -0.22))

	# The banners, which hang off two poles 5m apart on one stand point.
	var flags := Plan.clear_of_walkways(Plan.plaza_out2(Vector2(18, -16)), 3.0)
	for dx in [-2.5, 2.5]:
		out.append(Vector3(flags.x + dx, 4.6, flags.y))

	for spot in _lamp_spots():
		var p := Plan.clear_of_walkways(Plan.plaza_out2(spot), 0.45)
		out.append(Vector3(p.x, 4.1, p.y))
	return out


## The bandstand, which is hand-authored in `plaza.tscn` and so has no plan
## constant to read. Written once here rather than at both the places in this
## file that want it.
const BANDSTAND_AT := Vector3(-20.0, 0.0, -20.0)

## Everywhere a guest stands still in the plaza. Only used by the reachability
## report, which is why it is allowed to be an approximate union rather than the
## authority on seating — the authority is `_plaza_seated_groups`, and this is
## the same three sources it draws from.
func _plaza_seats() -> Array:
	var out: Array = []
	for bench in _plaza_bench_spots():
		out.append(bench["at"])
	for chair in _plaza_chair_spots():
		out.append(chair["at"])
	for group in _plaza_rim_spots():
		for seat in group:
			out.append(seat["at"])
	return out


## How far a guest will reach for something to look at. Mirrors the larger of
## `guest.gd`'s two radii — the one a *stopped* guest uses; a walking one asks
## for five and gets fewer answers, which is intended.
##
## Spelled out here rather than shared, because `guest.gd` is a scene script and
## this is a `SceneTree` tool that cannot preload one. If that number moves, this
## one has to move with it, and the check below is what makes the disagreement
## visible rather than silent.
const POI_REACH := 9.0


## Whether anybody can actually get close enough to look at each of these.
##
## This exists because three POIs sat in the plaza's list from the day the west
## was built until 2026-08-14c — the wheel, the observation tower and the
## coaster — and not one of them had ever been selected. They are 31m, 37m and
## 27m from the closest point on the plaza's own walkable graph, against a nine
## metre reach. Nothing said so. The list is a `PackedVector3Array` of points
## with no owner and no assertion attached, so a coordinate that means nothing
## looks exactly like a coordinate that means something.
##
## Measured against the graph's **edges** rather than its nodes, because a guest
## spends almost all their time between nodes and a POI beside a long edge is
## perfectly reachable while being far from either end of it.
##
## **Dropped rather than fatal, and dropping is behaviour-neutral by
## definition** — an unreachable POI is one that could never have been selected,
## so removing it changes nothing at runtime and only makes the emitted data
## honest. What it buys is that the source list stays free to describe *intent*:
## the flagpole banners are left in above even though the flagpoles ended up
## where nothing walks, and if the graph ever reaches them they come back on
## their own. What it costs is nothing, because they were never doing anything.
##
## The printed count is the point. Silence is what let three landmarks sit in
## this list for two days meaning nothing.
func _reachable_pois(tag: String, pois: PackedVector3Array, seats: Array) -> PackedVector3Array:
	var far: Array = []
	var kept := PackedVector3Array()
	for poi in pois:
		var flat := Vector2(poi.x, poi.z)
		var best := INF
		for e in range(0, _graph_edges.size(), 2):
			var a: Vector3 = _graph_points[_graph_edges[e]]
			var b: Vector3 = _graph_points[_graph_edges[e + 1]]
			best = minf(best, _flat_to_segment(flat, Vector2(a.x, a.z), Vector2(b.x, b.z)))
		# **And every seat.** Measuring the graph alone was the first version and
		# it was wrong in a way that would have driven the fix backwards: it
		# called the fountain's jets unreachable, because the ring walkway keeps
		# 15.6m off the middle — and then the obvious "fix" is to drag the POIs
		# off the jets and out towards the walk, which is precisely the bug this
		# whole pass is about. A seated guest is a guest, the benches sit on the
		# fountain's skirt, and nine of them sit on its rim.
		for seat in seats:
			var at: Vector3 = seat
			best = minf(best, flat.distance_to(Vector2(at.x, at.z)))
		if best > POI_REACH:
			far.append("%v is %.1fm from anywhere a guest can be" % [poi, best])
		else:
			kept.append(poi)
	print("%s: %d POIs, %d dropped as unreachable" % [tag, pois.size(), far.size()])
	for line in far:
		push_warning("%s POI unreachable: %s" % [tag, line])
		print("  dropped: ", line)
	return kept


func _flat_to_segment(p: Vector2, a: Vector2, b: Vector2) -> float:
	var ab := b - a
	var len2 := ab.length_squared()
	if len2 < 0.0001:
		return p.distance_to(a)
	var t := clampf((p - a).dot(ab) / len2, 0.0, 1.0)
	return p.distance_to(a + ab * t)


## One prop, at the position the props generator actually left it.
func _prop_poi(written: Vector2, margin: float, y: float) -> Vector3:
	var p := Plan.clear_of_walkways(Plan.plaza_out2(written), margin)
	return Vector3(p.x, y, p.y)


## The fountain — and this is the whole reason the list was reopened.
##
## What was there was `Vector3(0, 3.1, 0)`, labelled "the fountain column". It
## had two things wrong with it. The lesser is that there is no column any more;
## 3.1 is the lower basin's rim, which is stone. The greater is that **it could
## never be selected at all**: `poi_near` measures *horizontal* distance and
## `guest.gd` asks for nine metres, and the fountain's own radius is nine — so
## the nearest a guest could ever stand to the middle of it was the boundary
## itself, and a walking guest, who only asks for five, was never in with a
## chance. The plaza's centrepiece has never been looked at.
##
## The fix is to put the points on the *water*, which is also where they are
## reachable from. Two kinds, alternating every thirty degrees:
##
##   - the **jets**, on their own ring at `FOUNTAIN_JET_R`. From the coping that
##     is under three metres, so these are the one set of plaza POIs inside the
##     *walking* radius as well — people look at the fountain on their way past
##     it, which is the single biggest thing this change buys.
##   - the **pool surface**, further out and below eye level, so the gaze goes
##     down into the water rather than across it.
##
## Alternating by bearing is what stops the crowd converging: `poi_near` takes
## the nearest, so a guest looks at the piece of water on their own side.
##
## **The plume is deliberately not here**, and that is geometry rather than
## taste. For an observer outside the fountain, a point on an inner ring is
## always further away than one on an outer ring at a similar bearing, so a
## plume point at r≈1 could only ever win if the jets left a gap of about 120
## degrees — a quarter of the fountain with no water to look at, to buy one
## upward glance. The plume is what the fountain shows at twenty metres, and at
## twenty metres `poi_near` is not reaching the fountain at all. That is
## coherent: far away you see the plume, up close you watch the jets.
const FOUNTAIN_POI_ARMS := 12


func _fountain_pois() -> PackedVector3Array:
	var out := PackedVector3Array()
	var c := Plan.FOUNTAIN_AT
	for i in FOUNTAIN_POI_ARMS:
		var a := TAU * float(i) / float(FOUNTAIN_POI_ARMS)
		var d := Vector2(cos(a), sin(a))
		if i % 2 == 0:
			# A jet, a little below its tip — the part of it that is thickest
			# and most obviously moving.
			var p := c + d * Plan.FOUNTAIN_JET_R
			out.append(Vector3(p.x, Plan.FOUNTAIN_JET_TOP - 0.3, p.y))
		else:
			# Open water just inside the kerb — the nearest water to anybody
			# standing outside, and the part of the pool a passer-by actually
			# sees. It has to be out here for a second reason too: the crowd's
			# ring walkway never comes closer than 15.6m to the middle, so a
			# point much further in is out of a walking guest's five-metre
			# reach and most of a stopped one's nine.
			var p := c + d * (Plan.FOUNTAIN_RADIUS - 1.0)
			out.append(Vector3(p.x, Plan.FOUNTAIN_POOL_TOP + 0.04, p.y))
	return out


func _lamp_spots() -> Array:
	return [
		Vector2(13, -2), Vector2(9, -11), Vector2(-2, -13), Vector2(-13, -3),
		Vector2(-11, 6), Vector2(-3, 13), Vector2(7, 14), Vector2(14, 9),
		Vector2(-19, 2), Vector2(-19, 12), Vector2(-18, -14), Vector2(-16, 20),
	]


func _bin_spots() -> Array:
	return [
		Vector2(5.5, 6), Vector2(-6, 5.5), Vector2(-6.5, -6), Vector2(6, -6.5),
		Vector2(12, 12), Vector2(-14, 14), Vector2(3, -14),
		Vector2(-19, 7), Vector2(-17, 18), Vector2(-6.5, 24), Vector2(8, 20),
	]


## Mirrors `gen_props.gd::_benches()`. Duplicated deliberately rather than
## shared: the props tool owns where benches are, and if it moves one this list
## going stale is a visible bug — guests sitting in mid-air — rather than a
## silent one.
## Mirrors `gen_props.gd::_benches()`, dilation and exceptions included — a
## guest has to sit on a bench that exists, and after the plaza grew the two
## agree only if they scale the same way. The ring benches, the south bench and
## the two by the south wall go through `ParkPlan.plaza_out`; the hut's bench and
## the bandstand's three do not, for the same reason they do not over there.
## **And they are stood clear of the paving the same way too**, which is the half
## of this that was missing. `plaza_out` alone put the ring of five in the middle
## of the ring walkway; `plaza_stand` walks them back onto the fountain's skirt.
## A guest sitting on `gen_props`' idea of where a bench is and a bench built on
## this one's is the same drift the cafe terrace caused, so the two call the same
## function with the same margin — `gen_props.BENCH_CLEAR`, spelled out here
## because that file is a `SceneTree` this one cannot preload.
const BENCH_CLEAR := 1.2


func _bench_spot(at: Vector3, theta: float, dilate := true) -> Dictionary:
	var p: Vector3 = Plan.plaza_out(at) if dilate else at
	var c := Plan.clear_of_walkways(Vector2(p.x, p.z), BENCH_CLEAR)
	return {"at": Vector3(c.x, p.y, c.y), "theta": theta}


func _plaza_bench_spots() -> Array:
	var out: Array = []
	var r := 7.5
	for deg in [25.0, 95.0, 165.0, 235.0, 305.0]:
		var a := deg_to_rad(deg)
		var spot := _bench_spot(Vector3(r * cos(a), 0.0, r * sin(a)), 0.0)
		var p: Vector3 = spot["at"]
		spot["theta"] = atan2(-p.x, -p.z)
		out.append(spot)
	out.append(_bench_spot(Vector3(-5, 0, 19), deg_to_rad(186.0)))

	var hut := Vector3(Plan.PHOTO_HUT_AT.x, 0.0, Plan.PHOTO_HUT_AT.y)
	out.append(_bench_spot(hut + Vector3(-6.0, 0, -4.0), deg_to_rad(8.0), false))

	# The bandstand's three are not stood clear, because they moved a different
	# way: they belong to the bandstand, so they gave up the east bearing rather
	# than the radius. `spoke_nnw` runs down that side. See `gen_props._benches`.
	var band := Vector3(-20, 0, -20)
	for deg in [90.0, 180.0, 270.0]:
		var a := deg_to_rad(deg)
		var p: Vector3 = band + Vector3(8.6 * cos(a), 0.0, 8.6 * sin(a))
		var d: Vector3 = band - p
		out.append({"at": p, "theta": atan2(d.x, d.z)})
	out.append(_bench_spot(Vector3(-11, 0, 20), deg_to_rad(120.0)))
	out.append(_bench_spot(Vector3(2, 0, 22), deg_to_rad(200.0)))
	return out


## The fountain's coping, which is fifty-four metres of seat and was empty until
## 2026-08-14c.
##
## Unlike every other seat in the plaza there is no furniture to mirror — the
## rim is a *surface*, so all this needs is the plan's radius and height. Seats
## are spaced by **angle** rather than along the tangent: 0.78m of chord on an
## 8.66m circle is 0.09 radians, and stepping in angle keeps every member of a
## group exactly on the coping where stepping along the tangent would walk the
## outer ones 3cm inboard of it. Small, but it is free to be exact.
##
## Facing is `atan2(-p.x, -p.z)` for outward, which is the guest convention —
## a walking guest takes `atan2(-heading.x, -heading.z)`, so forward is −Z, and
## the same expression that turns a ring *bench* to face the fountain turns a
## *person* to face away from it. That coincidence is worth stating because it
## is the kind of thing that gets "simplified" into a bug.
##
## **Most face out and one group faces in**, which is what people on a fountain
## rim actually do: you sit with your back to the spray and watch the square,
## unless you came to watch the water. It also matters to the job — a guest
## facing the plaza is a guest the player can photograph without standing in
## the pool.
const RIM_SPACING := 0.78


func _plaza_rim_spots() -> Array:
	# Bearings picked to fall *between* the ring of five benches, which sit at
	# 25, 95, 165, 305 and 340 degrees on the same parametrisation. Nothing
	# actually collides — the benches are pushed out past radius 9 and these are
	# at 8.66, so the fountain wall is between them — but a row of people sitting
	# with their backs a metre from a bench reads as a queue rather than as two
	# separate places to sit.
	var plan := [
		# The south-east arc. First because it is the one the entrance street
		# points at and the one the player walks towards from the spawn.
		{"deg": 78.0, "n": 3, "face_in": false},
		{"deg": 128.0, "n": 2, "face_in": false},
		# Turned in, watching the water, directly across from the bench at 25.
		{"deg": 22.0, "n": 2, "face_in": true},
		{"deg": 288.0, "n": 2, "face_in": false},
	]
	var out: Array = []
	var r := Plan.FOUNTAIN_RIM_SEAT_R
	var step := RIM_SPACING / r
	for spec in plan:
		var mid := deg_to_rad(float(spec["deg"]))
		var n: int = spec["n"]
		var seats: Array = []
		for i in n:
			var a: float = mid + (float(i) - (float(n) - 1.0) * 0.5) * step
			var p := Vector3(cos(a) * r, 0.0, sin(a) * r)
			var yaw := atan2(-p.x, -p.z)
			if spec["face_in"]:
				yaw += PI
			seats.append({"at": p, "yaw": yaw})
		out.append(seats)
	return out


## The same three tables `gen_props.gd::_cafe()` builds, out of the same table
## in `ParkPlan`. It used to be the same literal typed into both files, with a
## comment in each saying so, which is a duplicate waiting for one of them to be
## edited alone — and the terrace moved today.
func _plaza_chair_spots() -> Array:
	var out: Array = []
	var offs := Plan.CAFE_CHAIRS
	for i in Plan.PLAZA_CAFE.size():
		var spec: Dictionary = Plan.PLAZA_CAFE[i]
		var at: Vector2 = spec["at"]
		var b := Vector3(at.x, 0, at.y)
		var th := deg_to_rad(float(spec["theta"]))
		for j in offs.size():
			out.append({
				"at": b + offs[j],
				"theta": th + deg_to_rad(30.0 * (j + 1)),
				"table": Vector3(b.x, 0.8, b.z),
			})
	return out


# --- the crowd --------------------------------------------------------------


## The cast, not the crowd. This is the park's busiest hour; `crowd.gd` decides
## how much of it is standing in the plaza at any given time, and the order
## below is the order they arrive in.
##
## The early entries are the ones the plaza is never without, because they are
## admitted first and sent home last. So the front of this list is what the
## opening hour looks like, and it is deliberately families and pairs rather
## than singles — a park that has just opened is people who queued for it.
func _plaza_walking_groups() -> void:
	# Families lead with an adult and trail a kid; pairs walk abreast; singles
	# are the ones who stop in the middle of everything.
	var plan := [
		{"start": "gate", "kinds": ["adult", "adult", "kid"]},
		{"start": "south_east", "kinds": ["adult", "kid", "kid"]},
		{"start": "ring_ne", "kinds": ["adult", "adult", "kid", "kid"]},
		{"start": "band_e", "kinds": ["adult", "adult", "kid"]},
		# The family the cascade was built for, and it is early in the list on
		# purpose: a group that has to plan its route round the park is a group
		# that comes when the park opens, not one that turns up at four.
		{"start": "west_s", "kinds": ["adult", "adult", "chair_kid", "kid"]},
		# The other thing that cannot take a flight of stairs, and the commoner
		# one by far. The ramp on the cascade's north wing was built so that a
		# group with a wheelchair in it never has to split up; a park on a normal
		# afternoon has one of those and a dozen of these, and the wing carries
		# them both. Started at the west so it is aimed at the arch.
		{"start": "west_s", "kinds": ["stroller_adult", "adult", "kid"]},
		{"start": "queue", "kinds": ["adult", "adult"]},
		{"start": "street_n", "kinds": ["adult", "adult"]},
		# The wheelchair user is the leader here rather than the one trailed.
		# Followers hold station on whoever is first in the list, so this is the
		# difference between two friends walking with somebody and two friends
		# keeping up with them.
		{"start": "ring_w", "kinds": ["chair_adult", "adult"]},
		{"start": "north", "kinds": ["adult", "adult"]},
		{"start": "west_s", "kinds": ["adult", "kid"]},
		{"start": "ring_s", "kinds": ["adult"]},
		{"start": "sign", "kinds": ["adult"]},
		{"start": "band_w", "kinds": ["adult"]},
		{"start": "south_west", "kinds": ["adult"]},
		{"start": "ring_nw", "kinds": ["adult"]},
		# Added when the day went on the clock. These are the afternoon — the
		# plaza only ever holds all of them between about one and five.
		{"start": "east", "kinds": ["adult", "adult", "kid"]},
		{"start": "ring_sw", "kinds": ["adult", "kid"]},
		{"start": "west_n", "kinds": ["adult", "adult"]},
		{"start": "north", "kinds": ["adult", "chair_adult"]},
		{"start": "hut_walk", "kinds": ["adult"]},
		{"start": "band_n", "kinds": ["chair_adult"]},
		# A pram comes in early and goes home early, so this one is in the
		# afternoon block rather than the opening one on purpose: it is the
		# second outing of the day, not the first.
		{"start": "ring_ne", "kinds": ["pram_adult", "adult"]},
		# Twins, and the parent is on their own with them — which is the reason
		# the buggy is a twin rather than two singles, and is worth one group in
		# the cast because it reads instantly from across the plaza.
		{"start": "south_east", "kinds": ["twin_adult", "kid"]},
		{"start": "ring_nw", "kinds": ["adult", "stroller_adult"]},
	]

	for entry in plan:
		var origin: Vector3 = _graph_points[_node_index(entry["start"])]
		var group := _group_index
		_group_index += 1
		var leader_name := ""
		var kinds: Array = entry["kinds"]
		var members: Array = []
		for i in kinds.size():
			var scatter := Vector3(_rng.randf_range(-1.0, 1.0), 0.0, _rng.randf_range(-1.0, 1.0))
			var guest := _guest(kinds[i], origin + scatter, _rng.randf_range(0.0, TAU), group)
			members.append(guest)
			if i == 0:
				leader_name = guest.name
			else:
				guest.set("leader_path", NodePath("../" + leader_name))
				# Kids trail further back and wider, which is where the
				# straggler comes from without anyone scripting one.
				#
				# **The test used to be `kinds[i] == "adult"`, and there are
				# seven kinds.** Only the bare `adult` matched it, so every
				# wheelchair user, every buggy pusher and every kid took the
				# child's trailing range — a chair_adult was parked up to 2.4m
				# behind their own group, permanently, and it read exactly like
				# somebody being left behind. Which is the one thing the ramp on
				# the cascade's north wing exists so as not to say.
				#
				# It is not a lag. `_pace_group` already gears the group to the
				# wheels and gives followers a catch-up margin, so the chair was
				# closing on its station the whole time — the station was two
				# metres back. Nothing about speed would ever have fixed it.
				#
				# `ends_with("kid")` and `begins_with("chair")` are the file's
				# own conventions, stated in `_guest` and used everywhere else
				# that reads a kind. This one line used neither.
				var is_kid: bool = kinds[i].ends_with("kid")
				var wheels: bool = kinds[i].begins_with("chair")
				# **Exactly two draws whatever the branch.** `_rng` is the cast's
				# one stream, so a branch that rolls a different *number* of
				# times shifts every guest generated after it — same reason
				# `_pace_group` draws none at all. Different ranges are free;
				# different counts are not.
				var lateral: float = _rng.randf_range(0.95, 1.35) if wheels \
					else _rng.randf_range(0.55, 1.15)
				var behind: float = _rng.randf_range(0.1, 0.7) if wheels \
					else (_rng.randf_range(0.9, 2.4) if is_kid
						else _rng.randf_range(0.4, 1.5))
				# A chair goes *beside* the group rather than behind it: wider
				# across, barely back at all. Somebody is pushing it, and you
				# walk alongside the person you are pushing.
				lateral *= 1.0 if i % 2 == 0 else -1.0
				guest.set("follow_offset", Vector3(lateral, 0.0, behind))
		_pace_group(members)


## Which seats are taken, and in what order they fill. Order is the whole point
## of the list: `crowd.gd` admits groups in generation order, so this is what
## the plaza looks like filling up. The fountain benches go first because they
## are the good seats and they are the ones the player is nearest.
##
## Benches and cafe tables are separate populations with separate curves. A
## bench is somewhere to rest and fills through the afternoon; a table is a
## meal and fills at one and at six. That the two disagree is the reason for
## splitting them — a cafe that simply tracked the crowd would say nothing the
## headcount does not already say.
func _plaza_seated_groups() -> void:
	var benches := _plaza_bench_spots()
	var plan := [[0, 2], [2, 1], [5, 2], [7, 2], [1, 1], [4, 2], [8, 1], [10, 2], [6, 1]]
	for entry in plan:
		var bench: Dictionary = benches[entry[0]]
		var group := _group_index
		_group_index += 1
		var members: Array = []
		var seats := int(entry[1])
		for s in seats:
			var side := -0.45 if s == 0 else 0.45
			var offset: Vector3 = Basis(Vector3.UP, bench["theta"]) * Vector3(side, 0.0, 0.06)
			var seat: Vector3 = bench["at"] + offset
			var guest := _guest(_seat_kind(seats, 0.25), seat, bench["theta"] + PI, group)
			guest.set("group_kind", "bench")
			guest.set("seat_at", seat)
			guest.set("seat_yaw", bench["theta"] + PI)
			guest.set("seat_height", 0.51)
			members.append(guest)
		_pace_seated_group(members)

	# The fountain rim, **after the benches and before the cafe**, and the
	# position in this list is the whole design of it.
	#
	# These are `"bench"` rather than a fourth population, which is a claim that
	# the rim is seating and fills like seating rather than a claim that it is
	# special. `crowd.gd` only knows three kinds and would have warned and
	# demoted a new one to `"wander"`, but that is not why — a fourth curve would
	# have had to be invented, and the bench curve already says the true thing:
	# people sit down in the afternoon because they have been walking since
	# eleven, and in the evening because the light is good.
	#
	# Coming *after* the benches makes the rim the overflow, which is what a
	# fountain rim is. `crowd.gd` admits groups in generation order within a
	# kind, so at 0.15 of the bench peak the three people sitting down are on
	# benches and the coping is bare; by the plateau every seat in the plaza is
	# taken and there is a row of nine on the fountain. An empty rim is
	# therefore a legible way of reading the hour, in the same way the cafe is —
	# and it is the one the player is standing nearest.
	#
	# It raises the bench population's peak from 14 to 23, which raises how many
	# the curve admits at every hour. That is intended: the plaza gained
	# fifty-four metres of seat and should look like it.
	for seats in _plaza_rim_spots():
		var rim_group := _group_index
		_group_index += 1
		var members: Array = []
		for seat in seats:
			var at: Vector3 = seat["at"]
			var yaw: float = seat["yaw"]
			var guest := _guest(_seat_kind(seats.size(), 0.35), at, yaw, rim_group)
			guest.set("group_kind", "bench")
			guest.set("seat_at", at)
			guest.set("seat_yaw", yaw)
			guest.set("seat_height", Plan.FOUNTAIN_RIM_TOP)
			members.append(guest)
		_pace_seated_group(members)

	# A table at a time, both chairs. Two people at one table is a pair having
	# lunch; two people at two tables is two strangers, and the cafe fills more
	# convincingly as the first thing.
	var chairs := _plaza_chair_spots()
	for table in 3:
		var group := _group_index
		_group_index += 1
		var members: Array = []
		for j in 2:
			var chair: Dictionary = chairs[table * 2 + j]
			# One table has a pram parked at it. `guest.gd` swings it out to the
			# side on the way into the chair, because a buggy left where it was
			# being pushed ends up standing in the table — which is also why a
			# real terrace has them parked all along the outside of the row.
			var kind := "pram_adult" if table == CAFE_PRAM_TABLE and j == 0 else "adult"
			var guest := _guest(kind, chair["at"], chair["theta"] + PI, group)
			guest.set("group_kind", "cafe")
			guest.set("seat_at", chair["at"])
			guest.set("seat_yaw", chair["theta"] + PI)
			guest.set("seat_height", 0.475)
			members.append(guest)
		if table == CAFE_PULL_UP_TABLE:
			# Appended before the pacing rather than after it, because somebody
			# who pulled up to the table came to it with the people already
			# sitting there — they are the group's slowest member as often as not.
			members.append(_cafe_pull_up(table, group))
		_pace_seated_group(members)


## Who is sitting in a given seat, given how many seats the group has.
##
## **A seated group of one is always an adult.** The roll is not offered rather
## than being offered and overridden, because a lone kid is not a rarer version
## of a group — it is a different claim about the park, and not one this park is
## making. A bench group has no leader and no `follow_offset`, so unlike a
## walking group there is nothing in the data that says who the child came with;
## a singleton that rolled `kid` was an unaccompanied eight-year-old crossing the
## plaza, sitting down for two hours and going home alone.
##
## It bit once at 0.25 across four singleton benches in the plaza and two on the
## boardwalk, which is a coin that comes up about four times in five runs.
##
## Skipping the draw rather than discarding it shifts every guest built after the
## first singleton. That is accepted — the alternative is a dead random number
## kept solely to hold a seed stream still, and the stream is not a fixture.
func _seat_kind(seats: int, kid_chance: float) -> String:
	if seats < 2:
		return "adult"
	return "kid" if _rng.randf() < kid_chance else "adult"


## A seated group crosses the park at its slowest member's pace.
##
## Not `_pace_group`, and the difference is the whole reason this exists. That
## one is about a *walking* group, where the spread between a tall adult and a
## small child is wanted — a leader plus `follow_offset` turns it into a
## straggler, which is a family. It only intervenes for wheels, which cannot
## straggle without reading as abandonment.
##
## A seated group has neither. `crowd.gd:_admit` checks `_follows()`, finds no
## `leader_path` on anything with a seat, and hands every member its own
## `_way_in_for` route to its own place on the bench. They are a group for the
## day curve and for nothing else. So the only thing keeping them together on
## the way in is that they walk the same line at the same speed — and they did
## not: `walk_speed` comes off height, and on one plaza bench an adult drew 1.19
## against a child's 0.77. Over the forty metres from the gap at the south that
## is the adult seated some eighteen seconds early, and a 1.10m child alone in
## the middle of the plaza for the last stretch of it. Then again in reverse when
## the visit ends, because `_retire` reads `_follows()` the same way.
##
## Everyone takes the slowest rather than the first member's, which is both the
## true thing — a group moves at the pace of whoever is slowest in it — and the
## one that does not depend on the order seats happen to be built in.
##
## No catch-up margin, unlike `_pace_group`. There is no station to keep here and
## nobody to keep it on: every member is walking to a fixed point of their own,
## so an exact match is what makes them arrive together.
##
## Draws no random numbers, for the reason `_pace_group` gives.
func _pace_seated_group(members: Array) -> void:
	var pace := 0.0
	for guest in members:
		if guest == null:
			continue
		var rolled: float = guest.get("walk_speed")
		pace = rolled if pace == 0.0 else minf(pace, rolled)
	if pace == 0.0:
		return
	for guest in members:
		if guest != null:
			guest.set("walk_speed", pace)


## Which table has a pram parked at it — a different one from the wheelchair's,
## because the point of both is that the terrace is an ordinary terrace people
## turn up to with what they turn up with, and putting them at one table would
## make that table the accessible one and the other two the normal ones.
const CAFE_PRAM_TABLE := 2


## Which table has somebody at it who brought their own seat. One of three, so
## the terrace is a terrace with a wheelchair at it rather than an accessible
## terrace — the middle one, because the middle one is the one you see from the
## fountain across the open ground the cafe was moved onto.
const CAFE_PULL_UP_TABLE := 1

## The third side of the table, which is deliberately the side `gen_props.gd`
## does not put a chair on. That is the whole content of pulling up to a table:
## not a reserved space, just the gap between the two chairs that are there.
const CAFE_PULL_UP := Vector3(0.05, 0.0, 1.1)


## Returns the guest so the table can pace itself around them. The `null` is the
## abort path and nothing downstream ever sees it — `quit(1)` has already fired.
func _cafe_pull_up(table: int, group: int) -> Node3D:
	var spec: Dictionary = Plan.PLAZA_CAFE[table]
	var at: Vector2 = spec["at"]
	var seat := Vector3(at.x, 0.0, at.y) + CAFE_PULL_UP

	# The two chairs are furniture and this guest is not sitting on one, so the
	# only thing that can go wrong here is parking on top of one. Checked rather
	# than eyeballed: `CAFE_CHAIRS` is plan data and can move.
	for off in Plan.CAFE_CHAIRS:
		if (CAFE_PULL_UP - off).length() < 0.9:
			push_error("cafe pull-up at %v stands on a chair at %v" % [CAFE_PULL_UP, off])
			quit(1)
			return null

	# Facing the table, unlike the two on chairs — those take the chair's own
	# bearing, which is near enough for furniture somebody is sitting in and
	# would be plainly wrong for somebody who chose where to stop.
	var to_table := Vector3(at.x, 0.0, at.y) - seat
	var guest := _guest("chair_adult", seat, atan2(-to_table.x, -to_table.z), group)
	guest.set("group_kind", "cafe")
	guest.set("seat_at", seat)
	guest.set("seat_yaw", atan2(-to_table.x, -to_table.z))
	return guest


## Fill the cast out to `CAST_TARGET` with wandering groups nobody composed.
##
## Its own generator, seeded separately, so that padding on and off cannot shift
## a single draw in the authored cast above. Placement is a graph node picked at
## random with a scatter — the graph is already validated as walkable and clear
## of props, so a point on it is a point somebody can stand.
func _pad_cast() -> void:
	if CAST_TARGET <= 0 or _guest_index >= CAST_TARGET:
		return

	var pad := RandomNumberGenerator.new()
	pad.seed = 0x9E3779B9
	# Roughly the mix of the authored list: mostly pairs and families, a third
	# of them singles. Group size is what decides how much of the per-frame cost
	# is follower logic rather than routing, so it should not be all singles.
	var shapes := [
		["adult", "adult", "kid"],
		["adult", "adult"],
		["adult", "kid"],
		["adult"],
		["adult", "adult", "kid", "kid"],
		["adult"],
		# One in six padded groups has a buggy in it, which is about the rate in
		# the authored cast. It matters here rather than being decoration: a
		# pusher carries a chassis, two passengers and four wheels — the heaviest
		# guest in the park to draw — so padding made entirely of bare adults
		# would measure a crowd this park does not have.
		["stroller_adult", "adult"],
	]

	while _guest_index < CAST_TARGET:
		var origin: Vector3 = _graph_points[pad.randi_range(0, _graph_points.size() - 1)]
		var kinds: Array = shapes[pad.randi_range(0, shapes.size() - 1)]
		var group := _group_index
		_group_index += 1
		var leader_name := ""
		var members: Array = []
		for i in kinds.size():
			if _guest_index >= CAST_TARGET:
				break
			var scatter := Vector3(pad.randf_range(-1.2, 1.2), 0.0, pad.randf_range(-1.2, 1.2))
			var guest := _guest(kinds[i], origin + scatter, pad.randf_range(0.0, TAU), group)
			members.append(guest)
			if i == 0:
				leader_name = guest.name
			elif leader_name != "":
				guest.set("leader_path", NodePath("../" + leader_name))
				var lateral: float = pad.randf_range(0.55, 1.15) * (1.0 if i % 2 == 0 else -1.0)
				var behind: float = pad.randf_range(0.4, 1.5) if kinds[i] == "adult" \
					else pad.randf_range(0.9, 2.4)
				guest.set("follow_offset", Vector3(lateral, 0.0, behind))
		# Reaches the one buggy shape in the table above. No shape there has a
		# chair in it today, and this is what makes adding one a row in `shapes`
		# rather than a row plus a rule somebody has to remember lives in the
		# other two loops.
		_pace_group(members)


## How much faster than the group's pace a follower walks. Small on purpose: it
## is catch-up, not a different speed, and at 8% a follower closes a metre of
## lost station in about eleven seconds — long enough to read as drifting back
## and coming up again rather than as snapping into formation.
const GROUP_CATCH_UP := 1.08


## Gear a group's walking speeds to whatever it brought on wheels.
##
## A follower has no notion of the pace in front of them: `guest.gd` walks them
## at their own `walk_speed` towards a station behind the leader, and nothing
## closes a gap faster than that. So a member slower than the leader falls
## behind by the difference every second, for as long as the group is moving.
## Between a tall adult and a small child that is wanted — it is the straggler
## `follow_offset` is shaped to produce. Between a group and the chair or the
## buggy it came with it is the group walking off and leaving somebody behind,
## which is the one thing the ramp on the cascade's north wing exists so as not
## to say. The rolls made it likely rather than possible: an adult draws
## 0.98–1.42 and a chair_kid 0.77–0.96, so most of those two ranges do not
## overlap at all.
##
## **A chair and a buggy are the same problem here and deliberately not the same
## problem anywhere else in this file.** Everywhere else the two are kept apart
## because they are opposite shapes — one is a body that is seated and moving,
## the other is an ordinary walk with a prop rolling in front of it. But what
## makes a group come apart is one member geared differently from the rest, and
## a set of wheels is a set of wheels to the arithmetic. The buggy is the milder
## case and much the commoner one: `_guest` takes 8% off a pusher rather than
## handing them a range of their own, so the drift is slow — a metre every
## twelve seconds against one every three. Slow enough that it reads as a parent
## trailing rather than as a bug, which is exactly how it survived.
##
## The wheels set the pace and everybody else is geared off them, whichever
## position they walk in — the leader gets exactly that pace, followers get the
## catch-up margin over it. A group with two of them takes the slower, so the
## family with a chair *and* a buggy in it is one rule rather than a case.
##
## The margin is the part that is easy to leave out and it is load-bearing: a
## follower matched exactly to the leader can never recover the distance a turn
## or a shove from `_apply_separation` opens, so it holds whatever gap it was
## last knocked to and the group spreads anyway, slowly.
##
## Draws no random numbers, deliberately. It runs inside the same `_rng` stream
## as the rest of the cast, and one draw here would shift every guest built
## after it — the groups on wheels are meant to be the only thing this changes.
func _pace_group(members: Array) -> void:
	var pace := 0.0
	for guest in members:
		if guest.get("wheelchair") or guest.get("stroller"):
			var rolled: float = guest.get("walk_speed")
			pace = rolled if pace == 0.0 else minf(pace, rolled)
	if pace == 0.0:
		return
	for i in members.size():
		members[i].set("walk_speed", pace if i == 0 else pace * GROUP_CATCH_UP)


## Seven kinds: `adult`, `kid`, `chair_adult`, `chair_kid`, `stroller_adult`,
## `twin_adult`, `pram_adult`. What somebody arrived with is spelled into the
## kind rather than passed beside it, so that a group reads as a group in the
## tables above — `["adult", "chair_kid", "kid"]` is a family with a sibling in a
## wheelchair, `["pram_adult", "adult", "kid"]` is a family with a baby asleep
## and an older one walking, and each says so on one line.
##
## Every prefix is matched with `begins_with` and none of them ends in `kid`,
## which is what lets a new chassis be one row in `STROLLER_STYLES` rather than
## an entry here and a second copy of the name in the parse.
func _guest(kind: String, at: Vector3, yaw: float, group: int) -> Node3D:
	var is_kid := kind.ends_with("kid")
	var wheels := kind.begins_with("chair")
	# What they are pushing, if anything. Read off the style table rather than a
	# list of names kept beside it.
	var pushes := ""
	for style in STROLLER_STYLES:
		if kind.begins_with(style):
			pushes = style
			break
	var height := _rng.randf_range(1.05, 1.34) if is_kid else _rng.randf_range(1.58, 1.9)
	var build := _rng.randf_range(0.88, 1.18)

	var guest := AnimatableBody3D.new()
	guest.set_script(load(GUEST_SCRIPT))
	# **Placed at the height it was handed, not at the section's floor.** `_floor`
	# was flattening every guest onto one plane, which is the right answer for a
	# plaza and for a promenade and no answer at all for a hillside: the
	# terraces climb twelve metres, so the two groups on terrace two were
	# authored twelve metres inside the hill and the belvedere's three were six.
	# Every caller derives `at` from a graph node or a seat, and those already
	# carry the floor in the two flat sections — so this changes nothing there
	# and is the whole of it here.
	guest.transform = Transform3D(Basis(Vector3.UP, yaw), at)
	_add(guest, _root, "guest_%02d" % _guest_index)
	_guest_index += 1

	# Shorter legs mean more steps for the same ground, so a mixed crowd moves
	# at mixed speeds without anyone choosing the numbers. That argument does not
	# survive the legs coming off the ground: a manual chair on the flat is
	# pushed at about walking pace whatever the length of the legs folded into
	# it, and what makes a child in one slower is the length of their arms.
	if wheels:
		guest.set("walk_speed", (0.86 if is_kid else 1.16) * _rng.randf_range(0.9, 1.12))
	else:
		var pace := 1.05 + (height - 1.5) * 0.55
		# Pushing something takes the top off a walking pace, and by the same few
		# percent whoever is doing it — the brake is the thing out in front, not
		# the legs behind it. It used to be small because a pusher who visibly
		# lagged would pull the family apart down the length of the plaza, which
		# `follow_offset` has no slack to absorb. `_pace_group` is what absorbs
		# it now, so this is no longer holding a group together on its own: what
		# it does today is decide how much slower the *whole* group walks, since
		# a pusher is the member the rest get geared to.
		if pushes != "":
			pace *= 0.92
		guest.set("walk_speed", pace * _rng.randf_range(0.9, 1.12))
	guest.set("group_id", group)
	guest.set("rng_seed", _rng.randi())
	# Children are the curious ones and adults are more often the shy ones,
	# which is why the kid in the family photo is the one looking at you.
	guest.set("curiosity", _rng.randf_range(0.55, 1.0) if is_kid else _rng.randf_range(0.1, 0.8))
	guest.set("shyness", _rng.randf_range(0.0, 0.25) if is_kid else _rng.randf_range(0.05, 0.5))

	var wheel_r := _build_body(guest, height, build, is_kid, wheels, pushes)
	guest.set("wheelchair", wheels)
	guest.set("stroller", pushes != "")
	# One radius, two owners. A chair's rear wheel and a stroller's are the same
	# thing to the animator — the pair that is driven by ground crossed — so they
	# share the property rather than growing a second one that means the same.
	if wheels or pushes != "":
		guest.set("wheel_radius", wheel_r)
	if pushes != "":
		guest.set("push_arm", PUSH_ARM)
	return guest


# --- bodies -----------------------------------------------------------------


## The fold a wheelchair holds a body in, and it is not the fold a bench holds
## one in. `guest.gd`'s seated pose drops the shins vertical and the feet under
## the seat's front edge; a wheelchair has a footplate there, and the knee sits
## a little *above* the hip rather than level with it, which is what a cushion
## does and is the reason this is past ninety.
##
## **Only the thigh angle is written down; the knee is solved.** The drop from
## seat to footplate is the guest's own leg length and the cast runs from 1.05m
## to 1.9m, so a typed pair of angles put the tallest guests' feet through the
## ground and left the shortest ones' hanging in the air.
const CHAIR_THIGH := deg_to_rad(92.0)


## The knee angle that stands the **sole** on the footplate, not the ankle.
##
## The shoe is a box that rotates with the shin, so its lowest point is a corner
## and travels with both the sine and the cosine of the angle. Solving for the
## ankle and then hanging the shoe off it is 3cm out at adult scale, in the one
## direction that matters — a foot through the plate. That version looked right
## in every screenshot, because a screenshot of a seated guest is taken from
## standing and the footplate is the part a standing camera cannot see.
##
## Closed form: `a·cos b + c·sin b = knee − sole` is `R·cos(b − phi)`. Clamped,
## because the shortest children's legs cannot reach as low as the rule wants —
## which is why the plate is placed at the sole this returns rather than at the
## height it was asked for.
func _solve_knee(seat_y: float, thigh: float, shin: float, limb: float) -> float:
	var knee_y := seat_y - thigh * cos(CHAIR_THIGH)
	var want := seat_y * 0.15
	var a := shin + limb * 0.25
	var c := limb * 0.65
	var r := sqrt(a * a + c * c)
	return atan2(c, a) + acos(clampf((knee_y - want) / maxf(r, 0.001), -1.0, 1.0))


func _sole_height(seat_y: float, thigh: float, shin: float, limb: float,
		bend: float) -> float:
	var knee_y := seat_y - thigh * cos(CHAIR_THIGH)
	return knee_y - (shin + limb * 0.25) * cos(bend) - limb * 0.65 * sin(bend)


## How far forward a pushing arm is held, measured from hanging straight down.
##
## **The handle is solved from this, and not the other way round.** A stroller
## handle is about a metre off the ground in life, and typing that in put every
## short guest's hands under the bar and every tall guest's through it — these
## arms are one rigid segment with no elbow, so they cannot take up the
## difference the way a real arm does. Deriving the bar from where the hand
## actually lands means the hands are on it for every guest in the cast, and the
## handle height then comes out between 86cm and 1.03m across the adults, which
## is a narrower spread than real strollers have anyway.
##
## Same lesson as `CHAIR_THIGH` above, learned from the other end: there, the
## seat was fixed and the fold was solved; here, the arm is fixed and the thing
## it holds is solved. Either way only one of the two may be typed.
const PUSH_ARM := deg_to_rad(46.0)


## The three chassis, in the dimensions that tell them apart. Everything else is
## the same few tubes and a fabric seat, and the point of having three is the
## silhouette: a single is a wedge, a twin is that wedge twice as wide, and a
## pram is a deep box on tall wheels that reads from further off than either.
##
## `span` is the gap between seat centres, so the singles are the ones with a
## zero in it. **Sizes are real and do not scale with the pusher** — a stroller
## is a bought object and a tall parent does not get a bigger one. Only the
## handle follows the arms, which is why the bar's width is computed against the
## hands as well as the seats and the wider of the two wins.
const STROLLER_STYLES := {
	"stroller": {
		"seats": 1, "span": 0.0, "seat_w": 0.32, "rear_r": 0.085, "front_r": 0.072,
		"length": 0.74, "seat_y": 0.44, "back_h": 0.36, "bassinet": false,
	},
	"twin": {
		"seats": 2, "span": 0.35, "seat_w": 0.31, "rear_r": 0.085, "front_r": 0.072,
		"length": 0.74, "seat_y": 0.44, "back_h": 0.36, "bassinet": false,
	},
	# Coach-built, which is what a pram is and why it is not just a deeper
	# stroller: the baby lies down inside a body rather than sitting in a sling,
	# so the wheels are big enough to carry it and the whole thing stands high.
	# Lower and on bigger wheels than the first pass, which put a 30cm box at
	# 56cm on thin legs and read as a vendor's cart rather than a pram. What
	# separates the two shapes is the ratio of wheel to body: a pram is mostly
	# wheel, and the body sits *between* them rather than on top of them.
	"pram": {
		"seats": 1, "span": 0.0, "seat_w": 0.40, "rear_r": 0.155, "front_r": 0.125,
		"length": 0.80, "seat_y": 0.50, "back_h": 0.30, "bassinet": true,
	},
}


## Returns the rolling radius of the driven wheels — the chair's or the
## stroller's — and zero for a guest walking with nothing. `guest.gd` needs it to
## turn ground crossed into a rotation, and this is the only place that knows how
## big either of them came out.
func _build_body(guest: Node3D, h: float, build: float, is_kid: bool,
		wheels := false, pushes := "") -> float:
	var head_h: float = h * (0.175 if is_kid else 0.132)
	var neck_h: float = h * (0.02 if is_kid else 0.03)
	var torso_h: float = h * (0.235 if is_kid else 0.258)
	var hips_h := h * 0.1
	var leg := h - head_h - neck_h - torso_h - hips_h
	var thigh := leg * 0.5
	var shin := leg * 0.5

	var shoulder := h * 0.245 * build
	var hip_w := h * 0.2 * build
	var depth := h * 0.115 * build
	var limb := h * 0.055 * build

	# Seat and footplate first, because the fold is measured between them. The
	# floor under the seat height is for the smallest of the children: a chair
	# built strictly in proportion to a 1.05m guest has its seat below its own
	# casters.
	var seat_y := maxf(h * 0.29, 0.32)
	var knee_a := 0.0
	var sole := 0.0
	if wheels:
		knee_a = _solve_knee(seat_y, thigh, shin, limb)
		sole = _sole_height(seat_y, thigh, shin, limb, knee_a)

	var skin := _pick("skin_")
	var shirt := _pick("shirt_")
	var bottom := _pick("bottom_")
	var hair := _pick("hair_")

	var collision := CollisionShape3D.new()
	var shape := CapsuleShape3D.new()
	if wheels:
		# Wider than a body and shorter than one. The footplate and the casters
		# stand outside it, deliberately — a capsule long enough to cover them is
		# a capsule the player cannot get past on any side, and nothing in the
		# park needs to bump into a footrest.
		shape.radius = maxf(hip_w * 0.5 + 0.13, 0.3)
		shape.height = maxf(seat_y + hips_h + torso_h + neck_h + head_h, shape.radius * 2.0)
	else:
		shape.radius = maxf(shoulder * 0.5, 0.22)
		shape.height = h
	collision.shape = shape
	collision.position.y = shape.height * 0.5
	_add(collision, guest, "collision")

	var body := Node3D.new()
	body.position.y = seat_y if wheels else leg
	_add(body, guest, "body")

	_part(body, "hips", Vector3(hip_w, hips_h, depth), Vector3(0, hips_h * 0.5, 0), bottom)
	_part(body, "torso", Vector3(shoulder, torso_h, depth),
		Vector3(0, hips_h + torso_h * 0.5, 0), shirt)

	var shoulder_y := hips_h + torso_h - limb * 0.5
	var arm := (thigh + shin) * 0.82
	for side in [-1.0, 1.0]:
		var nm := "arm_l" if side < 0.0 else "arm_r"
		var pivot := Node3D.new()
		pivot.position = Vector3(side * (shoulder * 0.5 + limb * 0.35), shoulder_y, 0)
		_add(pivot, body, nm)
		# Sleeve then forearm, so a short-sleeved shirt reads at distance.
		_part(pivot, nm + "_sleeve", Vector3(limb, arm * 0.42, limb),
			Vector3(0, -arm * 0.21, 0), shirt)
		_part(pivot, nm + "_skin", Vector3(limb * 0.88, arm * 0.58, limb * 0.88),
			Vector3(0, -arm * 0.71, 0), skin)

	# Shorts or long trousers, and it is **one** roll for the guest rather than
	# one per leg. It used to be drawn inside the loop below, which gave about
	# half the park a bare shin on one side and a trouser leg on the other.
	# Christina, playing: some of the guests have one long pant leg and one
	# short pant leg. Nothing about a per-leg roll was ever wanted — it was a
	# line that happened to sit inside a loop.
	var lower := skin if _rng.randf() > 0.4 else bottom

	for side in [-1.0, 1.0]:
		var nm := "hip_l" if side < 0.0 else "hip_r"
		var pivot := Node3D.new()
		pivot.position = Vector3(side * hip_w * 0.26, 0, 0)
		# The fold is baked here rather than applied by `guest.gd`, because the
		# angle the knee holds is what puts the foot on the footplate and the
		# footplate is part of the chair. One of the two has to own it, and it is
		# the one that knows where the chair is.
		if wheels:
			pivot.rotation.x = CHAIR_THIGH
		_add(pivot, body, nm)
		_part(pivot, nm + "_thigh", Vector3(limb * 1.25, thigh, limb * 1.25),
			Vector3(0, -thigh * 0.5, 0), bottom)
		var knee := Node3D.new()
		knee.position = Vector3(0, -thigh, 0)
		if wheels:
			knee.rotation.x = knee_a - CHAIR_THIGH
		_add(knee, pivot, "knee_l" if side < 0.0 else "knee_r")
		# guest.gd reads shin length off this child, so it stays first.
		_part(knee, "shin", Vector3(limb * 1.1, shin, limb * 1.1),
			Vector3(0, -shin * 0.5, 0), lower)
		# The shoe is deeper than the shin and offset forward, so that neither
		# end of it shares a plane with the leg above. It used to be exactly as
		# deep behind as the shin was, which put the back of the shoe and the
		# back of the shin on one plane with different materials — 21cm² of
		# z-fighting per leg, on every guest in the park. Christina, playing:
		# the heels of each character kind of vibrate.
		#
		# A tenth of `limb` is about a centimetre at adult scale. It reads as a
		# heel rather than as a correction, which is the shape a shoe has
		# anyway.
		_part(knee, "shoe", Vector3(limb * 1.25, limb * 0.5, limb * 2.1),
			Vector3(0, -shin, -limb * 0.40), "bottom_black")

	var neck := Node3D.new()
	neck.position = Vector3(0, hips_h + torso_h, 0)
	_add(neck, body, "neck")
	_part(neck, "throat", Vector3(limb * 1.1, neck_h * 2.0, limb * 1.1),
		Vector3(0, neck_h * 0.4, 0), skin)

	var head_pivot := Node3D.new()
	head_pivot.position = Vector3(0, neck_h, 0)
	_add(head_pivot, neck, "head_pivot")

	var head_w := h * 0.105
	var head_d := h * 0.112
	_part(head_pivot, "head", Vector3(head_w, head_h, head_d),
		Vector3(0, head_h * 0.5, 0), skin)
	# Eyes as one bar. At greybox the eye-line is the whole performance, and it
	# has to read through a viewfinder from eight metres.
	_part(head_pivot, "eyes", Vector3(head_w * 0.72, head_h * 0.13, 0.02),
		Vector3(0, head_h * 0.6, -head_d * 0.5 - 0.01), "hair_black")
	_build_hair(head_pivot, head_w, head_h, head_d, hair, is_kid)

	if not wheels:
		if pushes != "":
			# The pusher keeps the ordinary walk cycle and the ordinary standing
			# body — the legs underneath are doing exactly what a walking guest's
			# do, and only the arms are spoken for. That is the whole difference
			# between this and the chair above, and it is why nothing here
			# touches the fold.
			_build_stroller(guest, body, head_pivot, pushes, leg, hips_h, torso_h,
				shoulder, depth, limb, arm)
			return float(STROLLER_STYLES[pushes]["rear_r"])
		_build_carried(body, head_pivot, hips_h, torso_h, shoulder, depth, limb, arm, is_kid)
		return 0.0

	# Where the shoe came out: its lowest point, and how far forward its middle
	# stands. The footplate goes under the first and the casters behind it.
	var knee_z := -thigh * sin(CHAIR_THIGH)
	var shoe_z := knee_z - shin * sin(knee_a) - limb * 0.4 * cos(knee_a)
	# A 24" rear wheel under a 0.5m seat puts the top of the tyre a hand above
	# the seat, which is the proportion that reads as a wheelchair from across a
	# plaza. Everything else about the chair follows the guest in it.
	var wheel_r := seat_y * 0.6
	var chair := _build_chair(guest, wheel_r, seat_y, sole, hip_w, hips_h, torso_h,
		depth, limb, thigh, shoe_z)
	_build_carried_seated(body, chair, head_pivot, hips_h, torso_h, depth,
		limb, arm, thigh, seat_y, hip_w, is_kid)
	return wheel_r


## The chair, as a sibling of the body rather than a child of it. The body bobs
## and leans into the push stroke; the chair under it does neither, and parenting
## it to the body would have the wheels rise and fall with the shoulders.
##
## The two rear wheels and the two casters are **pivot nodes with the parts hung
## off them**, so `guest.gd` turns one by setting a rotation rather than by
## knowing anything about how it is built.
##
## Nothing here shares a plane with anything, which took more care than usual
## because a wheel is a stack of discs on one axis: the tyre, the push rim and
## the hub plate are three different radii at three different widths, and the
## seat pan is sunk into the hips rather than laid against them.
## The front post down to the caster. Named because the caster's own width is
## derived from it — see `_build_chair` — and two literals that have to differ
## are two literals that will one day match.
const LEG_W := 0.032


func _build_chair(guest: Node3D, wheel_r: float, seat_y: float, sole: float,
		hip_w: float, hips_h: float, torso_h: float, depth: float, limb: float,
		thigh: float, shoe_z: float) -> Node3D:
	var chair := Node3D.new()
	_add(chair, guest, "chair")

	var frame := _pick("frame_")
	var hub_x := hip_w * 0.5 + 0.13
	var tyre_w := maxf(limb * 0.42, 0.035)
	var caster_r := maxf(wheel_r * 0.2, 0.05)
	# Behind the footplate, which is where a caster trails.
	var caster_z := shoe_z + limb * 1.5 + caster_r
	var back_y := seat_y + hips_h * 0.5 + torso_h * 0.3

	# The seat. Its top stands 15mm inside the hips rather than level with them,
	# because level with them is the one thing it may not be — the underside of
	# the pelvis and the top of the pan would be the same plane in two materials.
	_part(chair, "seat", Vector3(hip_w + 0.12, 0.05, thigh * 0.95),
		Vector3(0, seat_y - 0.01, -thigh * 0.34), "nylon")
	# The back, sunk a centimetre into the torso for the same reason.
	_part(chair, "back", Vector3(hip_w + 0.1, torso_h * 0.66, 0.05),
		Vector3(0, back_y, depth * 0.5 + 0.008), "nylon")

	for side in [-1.0, 1.0]:
		var s := "l" if side < 0.0 else "r"
		# The upright behind the back, and the handle somebody else would push by.
		# Nobody pushes anybody in this park — every wheelchair guest here self-
		# propels — but a chair without handles is a chair nobody has ever seen.
		_part(chair, "post_" + s, Vector3(0.035, torso_h * 0.95, 0.035),
			Vector3(side * (hip_w * 0.5 + 0.045), seat_y + hips_h * 0.5 + torso_h * 0.44,
				depth * 0.5 + 0.035), frame)
		_part(chair, "handle_" + s, Vector3(0.032, 0.032, 0.15),
			Vector3(side * (hip_w * 0.5 + 0.045),
				seat_y + hips_h * 0.5 + torso_h * 0.9, depth * 0.5 + 0.1), "bottom_black")
		# The side rail under the seat, and the front post down to the caster.
		_part(chair, "rail_" + s, Vector3(0.034, 0.048, thigh * 1.2),
			Vector3(side * (hub_x - 0.045), seat_y - 0.075, -thigh * 0.36), frame)
		_part(chair, "leg_" + s, Vector3(LEG_W, seat_y - caster_r - 0.03, LEG_W),
			Vector3(side * (hub_x - 0.05), (seat_y + caster_r) * 0.5, caster_z), frame)

		# The rear wheel: pivot at the hub, everything that turns hung off it.
		var hub := Node3D.new()
		hub.position = Vector3(side * hub_x, wheel_r, 0.06)
		_add(hub, chair, "wheel_" + s)
		_rim(hub, "tyre", wheel_r, Vector3.ZERO, "tyre", true)
		# The push rim, which is what a hand actually rests on: a thinner ring
		# standing outboard of the tyre.
		_rim(hub, "rim", wheel_r * 0.86, Vector3(side * tyre_w * 0.8, 0, 0),
			"frame_chrome")
		_disc(hub, "hub", wheel_r * 0.17, tyre_w * 1.8, Vector3.ZERO, frame)
		# Three bars across the hole in the tyre, and they are the whole reason a
		# turning wheel looks like it is turning. Each at its own roll and its own
		# depth, so no two of them ever line up.
		for k in 3:
			_spoke(hub, "spoke_%d" % k, wheel_r, tyre_w * 0.36,
				PI * float(k) / 3.0,
				Vector3(side * tyre_w * (0.06 * k - 0.06), 0, 0), "frame_chrome")

		var caster := Node3D.new()
		caster.position = Vector3(side * (hub_x - 0.05), caster_r, caster_z)
		_add(caster, chair, "caster_" + s)
		# **Narrower than the leg that comes down into it, and by a stated
		# margin rather than by luck.** The post and the caster share a centre
		# in x and in z — a stem straddling its own wheel, which is right — so
		# the only thing keeping their side faces off each other is that the two
		# widths differ. They were `0.032` and `tyre_w * 0.7`, and `tyre_w` is
		# `limb * 0.42`, so at a limb of 0.109 they are *equal*: four coplanar
		# faces in two materials, on whichever guests happen to be that size.
		# `guest_09` on the boardwalk was one, and it is the same case the seat
		# pan states two dozen lines up — level with the hips is the one thing
		# it may not be.
		#
		# It went unreported for as long as it existed, because
		# `coplanar_test.py` was reading every basis transposed and could only
		# ever miss fights inside rotated nested frames, which is exactly what a
		# guest is. Both fixed on 2026-08-20.
		_disc(caster, "tyre", caster_r, minf(tyre_w * 0.7, LEG_W - 0.012),
			Vector3.ZERO, "tyre")

	# The footplate, placed against the sole the fold actually produced rather
	# than against the height the fold was asked for — the shortest legs in the
	# cast cannot reach the height the rule wants, and their plate rides up to
	# meet them. Its top stands 3mm above the sole, so the feet rest *into* it
	# rather than on a plane shared with it.
	var plate_th := 0.026
	_part(chair, "footplate", Vector3(hip_w + 0.08, plate_th, limb * 2.4),
		Vector3(0, sole + 0.003 - plate_th * 0.5, shoe_z), frame)

	return chair


## The stroller, as a sibling of the body for the same reason the chair is: the
## body bobs and sways as it walks and the thing being pushed does neither.
## Parenting it to the body would have the whole chassis rise and fall with the
## pusher's shoulders, which is the one motion a wheeled object may not have.
##
## **The handle is solved from the arms; the chassis is not.** A stroller is a
## bought object, so its seat, wheels and length are real numbers — but the bar
## has to be exactly where the hands land, because these arms have no elbow to
## take up a difference. So the bar goes where `PUSH_ARM` puts the hands and the
## chassis hangs forward from it, which means a tall pusher gets longer handle
## posts and the same buggy. That is also what happens in life.
##
## Nothing about the child in it is a guest. See `_build_passenger`.
func _build_stroller(guest: Node3D, body: Node3D, head_pivot: Node3D,
		style: String, leg: float, hips_h: float, torso_h: float,
		shoulder: float, depth: float, limb: float, arm: float) -> void:
	var spec: Dictionary = STROLLER_STYLES[style]
	var pram := Node3D.new()
	_add(pram, guest, "stroller")

	var frame := _pick("frame_")
	var fabric := _pick("shirt_")

	# Where the hands come out, in the guest's own frame. The arm pivot sits at
	# the shoulder and the hand hangs a whole arm below it, so swinging it
	# forward by PUSH_ARM is the same trig the leg fold uses, run the other way.
	var hand_r := arm * 0.98
	var hand_x := shoulder * 0.5 + limb * 0.35
	var bar_y := leg + hips_h + torso_h - limb * 0.5 - hand_r * cos(PUSH_ARM)
	var bar_z := -hand_r * sin(PUSH_ARM)

	var seats := int(spec["seats"])
	var span: float = spec["span"]
	var seat_w: float = spec["seat_w"]
	var rear_r: float = spec["rear_r"]
	var front_r: float = spec["front_r"]
	var length: float = spec["length"]
	var seat_y: float = spec["seat_y"]
	var back_h: float = spec["back_h"]

	# Wide enough for the seats or for the hands, whichever asks for more. On a
	# twin it is the seats; on a single it is the hands, and a bar cut to the
	# seat width would leave both hands hanging off the ends of it.
	var half := maxf((span + seat_w) * 0.5 + 0.03, hand_x + 0.05)
	var track := maxf(half - 0.02, 0.2)
	var rear_z := bar_z - 0.02
	var front_z := bar_z - length
	var tyre_w := maxf(limb * 0.3, 0.03)

	# The bar the hands actually rest on, and the posts down to the rear axle.
	# The posts are vertical rather than raked: a rake is truer to a real buggy,
	# but it stands the top of the post and the underside of the bar on one plane
	# at an angle, and that seam is 2cm from the camera in every shot of a family.
	_part(pram, "handle", Vector3(half * 2.0, 0.032, 0.034),
		Vector3(0, bar_y, bar_z), "bottom_black")

	for side: float in [-1.0, 1.0]:
		var s := "l" if side < 0.0 else "r"
		_part(pram, "post_" + s, Vector3(0.03, bar_y - rear_r, 0.03),
			Vector3(side * (track - 0.03), (bar_y + rear_r) * 0.5, bar_z - 0.008), frame)
		_part(pram, "rail_" + s, Vector3(0.028, 0.03, length * 0.9),
			Vector3(side * (track - 0.035), seat_y - 0.05, bar_z - length * 0.45), frame)
		_part(pram, "leg_" + s, Vector3(0.028, seat_y - front_r, 0.028),
			Vector3(side * (track - 0.04), (seat_y + front_r) * 0.5, front_z + 0.01), frame)

		var hub := Node3D.new()
		hub.position = Vector3(side * track, rear_r, rear_z)
		_add(hub, pram, "wheel_" + s)
		_buggy_wheel(hub, rear_r, tyre_w, side, frame)

		# `guest.gd` reads the front radius off this node's own height to work
		# out how much further a small wheel turns, so the pivot sits at the
		# axle and the parts hang off it. Same arrangement as the chair's
		# casters, and it shares the spin code with them.
		var caster := Node3D.new()
		caster.position = Vector3(side * (track - 0.02), front_r, front_z)
		_add(caster, pram, "caster_" + s)
		_buggy_wheel(caster, front_r, tyre_w * 0.9, side, frame)

	if bool(spec["bassinet"]):
		# A pram body, not a deeper seat. The hood is over the head end, which is
		# the end nearest whoever is pushing — so walking towards one you see the
		# open side and a face, and from behind you see the hood. That asymmetry
		# is the only thing that says which way round a pram is.
		_part(pram, "body", Vector3(seat_w + 0.1, 0.26, length * 0.72),
			Vector3(0, seat_y + 0.11, bar_z - length * 0.44), fabric)
		# A rim, not a lid. At 5cm deep and wider than the hood it capped the
		# whole pram and buried everything inside it.
		_part(pram, "body_trim", Vector3(seat_w + 0.11, 0.035, length * 0.74),
			Vector3(0, seat_y + 0.24, bar_z - length * 0.44), "plastic")
		_part(pram, "hood", Vector3(seat_w + 0.08, 0.3, length * 0.3),
			Vector3(0, seat_y + 0.33, bar_z - length * 0.17), fabric)
		# What is actually visible of a baby in a pram: a wrapped bundle and a
		# face at the hood end. **Nothing here turns, and there is no pivot.** An
		# infant lying down is the one passenger with no head to track anybody
		# with, so `guest.gd` looks for one, finds none, and drives nothing.
		# Bedding down inside the body rather than laid across the top of it. It
		# sat proud at first and read as a lid; a pram is a box you cannot see
		# into from the side, and the only thing that should break its rim is the
		# head. Its top face is also kept clear of the body's and the trim's —
		# at `seat_y + 0.25` it landed on exactly the trim's plane, same
		# footprint, two materials, which is a z-fight `coplanar_test.py` would
		# never have reported because it reads CSG and a guest is MeshInstance3D.
		_part(pram, "swaddle", Vector3(seat_w * 0.66, 0.07, length * 0.4),
			Vector3(0, seat_y + 0.2, bar_z - length * 0.52), _pick("shirt_"))
		_sphere_part(pram, "baby_head", 0.055,
			Vector3(0, seat_y + 0.22, bar_z - length * 0.27), _pick("skin_"))
		_build_carried_pushing(body, pram, head_pivot, shoulder, torso_h, hips_h,
			depth, limb, bar_y, bar_z, hand_x)
		return

	_part(pram, "seat", Vector3(span + seat_w, 0.04, 0.42),
		Vector3(0, seat_y, bar_z - 0.33), fabric)
	# Sunk into the pan rather than stood on it, so the two do not share a
	# bottom face where they overlap.
	_part(pram, "back", Vector3(span + seat_w, back_h, 0.04),
		Vector3(0, seat_y + back_h * 0.5 + 0.005, bar_z - 0.11), fabric)

	var sole_y := INF
	var sole_z := 0.0
	for i in seats:
		var cx := (float(i) - (float(seats) - 1.0) * 0.5) * span
		# **The child goes in before the hood goes on.** The hood was placed
		# first, off the backrest, and a solid box 20cm deep at that height sat
		# exactly where the head is — so both children were sealed inside their
		# own canopies with an arm out each side. A hood arches *over* a head, and
		# the only way to know where the head is is to have built it.
		var landed := _build_passenger(pram, "kid_%d" % i,
			_rng.randf_range(0.78, 0.95), Vector3(cx, seat_y + 0.02, bar_z - 0.22),
			fabric)
		if landed.x < sole_y:
			sole_y = landed.x
			sole_z = landed.y

		# **The hood is the seat's fabric, not a colour of its own.** It was its
		# own `_pick` first, which put three different brights on one chassis —
		# seat, back and hood — and the whole thing stopped reading as a buggy and
		# started reading as a cart with boxes stacked on it. A stroller is one
		# manufactured object and comes in one fabric, and that single fact is
		# what makes the silhouette parse at ten metres.
		#
		# Up or folded is still rolled per seat, so twins are not identical twins.
		if _rng.randf() < 0.62:
			# Clear of the head by 3cm. That puts it above the handle on the
			# taller children, which is where a real stroller hood sits anyway.
			_part(pram, "canopy_%d" % i, Vector3(seat_w - 0.04, 0.2, 0.3),
				Vector3(cx, landed.z + 0.13, bar_z - 0.2), fabric)
		else:
			# Folded back against the backrest, which is where a canopy lives on
			# a cloudy afternoon and is the shape that says it can move. This one
			# is behind the head in z rather than above it in y, so it needs no
			# clearance.
			_part(pram, "canopy_%d" % i, Vector3(seat_w - 0.04, 0.15, 0.07),
				Vector3(cx, seat_y + back_h - 0.04, bar_z - 0.055), fabric)

	# Under the feet that are actually there, rather than at a height somebody
	# picked. The passengers vary by 17cm of standing height across the cast, and
	# a footrest typed as a fraction of the chassis has half of them resting on
	# air and the other half through it.
	_part(pram, "footrest", Vector3(span + seat_w - 0.06, 0.026, 0.14),
		Vector3(0, sole_y - 0.022, sole_z), frame)

	_build_carried_pushing(body, pram, head_pivot, shoulder, torso_h, hips_h,
		depth, limb, bar_y, bar_z, hand_x)


## One wheel, hung off a pivot the animator turns.
##
## Two builds, and the difference is not decoration. A pram wheel is big enough
## to be a ring with bars across the hole, which is what makes its rotation
## legible. A stroller wheel is a solid moulded disc, so a bar across it would be
## buried inside it and the ribs go **proud of the outer face** instead. Either
## way there has to be something off-axis: a featureless disc turning at any
## speed is a disc standing still, which is how a rolling buggy ends up looking
## like it is being dragged.
func _buggy_wheel(hub: Node3D, radius: float, width: float, side: float,
		frame: String) -> void:
	if radius > 0.11:
		_rim(hub, "tyre", radius, Vector3.ZERO, "tyre", true)
		_disc(hub, "hub", radius * 0.2, width * 1.7, Vector3.ZERO, frame)
		for k in 3:
			_spoke(hub, "spoke_%d" % k, radius, width * 0.34, PI * float(k) / 3.0,
				Vector3(side * width * (0.05 * float(k) - 0.05), 0, 0), "frame_chrome")
		return

	_disc(hub, "tyre", radius, width, Vector3.ZERO, "tyre")
	_disc(hub, "hub", radius * 0.42, width * 1.4, Vector3.ZERO, "plastic")
	for k in 3:
		_spoke(hub, "rib_%d" % k, radius * 0.78, width * 0.3, PI * float(k) / 3.0,
			Vector3(side * (width * 0.78), 0, 0), "plastic")


## A child in a buggy seat, built folded and left that way.
##
## **This is geometry, not a guest**, and the distinction is the whole design.
## A toddler strapped into a moving stroller is seated *and* moving, which is
## precisely the problem the wheelchair had to decompose `_seated` to solve — and
## unlike a wheelchair user, a toddler in a buggy has no independent movement to
## model at all. So there is no body here, no routing, no collision, no place in
## the headcount and nothing to ask for a pose. It cannot be photographed as a
## subject; it is photographed as part of the family, which is what it is.
##
## The one exception is the head, which gets a pivot because a small child
## craning round to look at a stranger with a camera is the photograph the whole
## feature exists for. `guest.gd` drives it off the pusher's own gaze.
##
## Returns the lowest point of the shoes, how far forward they stand, and the top
## of the head — so the footrest goes under the feet that came out and the hood
## goes over the head that came out, rather than either being guessed. The cast
## varies by 17cm of standing height, which is enough for a guess to be wrong at
## both ends at once.
func _build_passenger(parent: Node3D, nm: String, t: float, at: Vector3,
		fabric: String) -> Vector3:
	var kid := Node3D.new()
	kid.position = at
	_add(kid, parent, nm)

	# A toddler is not a scaled adult and is barely a scaled child: the head is
	# most of a quarter of the height, which is what makes one read as a toddler
	# from across a plaza rather than as a small person.
	var head_h := t * 0.23
	var neck_h := t * 0.025
	var torso_h := t * 0.27
	var hips_h := t * 0.11
	var shoulder := t * 0.28
	var hip_w := t * 0.25
	var depth := t * 0.16
	var limb := t * 0.08
	var thigh := t * 0.2
	var shin := t * 0.19
	var arm_l := t * 0.3

	var skin := _pick("skin_")
	# Never the seat's own colour. The palette is twelve shirts and the buggy
	# takes one of them, so about one child in twelve came out dressed in the
	# upholstery and vanished into it — a seat with a head and two shoes. Rolled
	# again rather than shifted along the list, so the distribution stays flat.
	var shirt := _pick("shirt_")
	while shirt == fabric:
		shirt = _pick("shirt_")
	var hair := _pick("hair_")
	# One roll for the child, not one per leg. Drawn inside the loop below this
	# is how half the park ended up with one bare shin and one trouser leg.
	var bottom := _pick("bottom_")
	var lower := skin if _rng.randf() > 0.45 else bottom

	_part(kid, "hips", Vector3(hip_w, hips_h, depth),
		Vector3(0, hips_h * 0.5, 0), bottom)
	_part(kid, "torso", Vector3(shoulder, torso_h, depth),
		Vector3(0, hips_h + torso_h * 0.5, 0), shirt)

	# Thighs forward and level, shins hanging off the front. Written rather than
	# solved, unlike the wheelchair's fold: there is no plate the feet have to
	# land on, because a buggy's footrest goes wherever the feet ended up and
	# `_build_stroller` places it from what this returns.
	var sole := 0.0
	var shoe_z := 0.0
	for side: float in [-1.0, 1.0]:
		var s := "l" if side < 0.0 else "r"
		var x := side * hip_w * 0.26
		_part(kid, "thigh_" + s, Vector3(limb * 1.2, limb * 1.2, thigh),
			Vector3(x, limb * 0.55, -thigh * 0.5), bottom)
		_part(kid, "shin_" + s, Vector3(limb * 1.05, shin, limb * 1.05),
			Vector3(x, limb * 0.55 - shin * 0.5, -thigh * 0.94), lower)
		# Offset forward of the shin so neither end of the shoe shares a plane
		# with the leg above it — the same 21cm² of z-fighting per leg that the
		# adults' heels had.
		shoe_z = -thigh * 0.94 - limb * 0.35
		sole = limb * 0.55 - shin - limb * 0.25
		_part(kid, "shoe_" + s, Vector3(limb * 1.2, limb * 0.5, limb * 1.9),
			Vector3(x, sole + limb * 0.25, shoe_z), "bottom_black")
		# Arms forward along the sides, which is where they go when there is a
		# tray or a bar in front of you.
		_part(kid, "arm_" + s, Vector3(limb * 0.95, limb * 0.95, arm_l),
			Vector3(side * (shoulder * 0.5 + limb * 0.3),
				hips_h + torso_h * 0.72, -arm_l * 0.42), shirt)

	var neck := Node3D.new()
	neck.position = Vector3(0, hips_h + torso_h, 0)
	_add(neck, kid, "neck")
	_part(neck, "throat", Vector3(limb * 1.05, neck_h * 2.0, limb * 1.05),
		Vector3(0, neck_h * 0.4, 0), skin)

	var head_pivot := Node3D.new()
	head_pivot.position = Vector3(0, neck_h, 0)
	_add(head_pivot, neck, "head_pivot")

	var head_w := t * 0.15
	var head_d := t * 0.155
	_part(head_pivot, "head", Vector3(head_w, head_h, head_d),
		Vector3(0, head_h * 0.5, 0), skin)
	_part(head_pivot, "eyes", Vector3(head_w * 0.7, head_h * 0.13, 0.02),
		Vector3(0, head_h * 0.58, -head_d * 0.5 - 0.01), "hair_black")
	_build_hair(head_pivot, head_w, head_h, head_d, hair, true)

	return Vector3(at.y + sole, at.z + shoe_z,
		at.y + hips_h + torso_h + neck_h + head_h)


## What somebody pushing a buggy has with them. Both hands are on the handle, so
## nothing swings from a hand and almost nothing in `_build_carried` survives —
## a pusher's things hang off the stroller, which is what everyone does with a
## stroller and is why the handles of real ones are bent.
func _build_carried_pushing(body: Node3D, pram: Node3D, head_pivot: Node3D,
		shoulder: float, torso_h: float, hips_h: float, depth: float,
		limb: float, bar_y: float, bar_z: float, hand_x: float) -> void:
	var roll := _rng.randf()
	if roll < 0.28:
		# Hung off one end of the handle, and off to one side rather than
		# centred: a bag in the middle of the bar is where the hands are.
		_part(pram, "tote", Vector3(limb * 2.4, limb * 3.0, limb * 1.3),
			Vector3(-hand_x * 0.62, bar_y - limb * 1.8, bar_z + 0.05), _pick("shirt_"))
	elif roll < 0.44:
		_part(body, "backpack", Vector3(shoulder * 0.7, torso_h * 0.72, depth * 0.7),
			Vector3(0, hips_h + torso_h * 0.55, depth * 0.72), _pick("shirt_"))
	elif roll < 0.54:
		_part(head_pivot, "sunglasses", Vector3(0.11, 0.02, 0.02),
			Vector3(0, 0.0, 0.0), "bottom_black")


func _build_hair(head_pivot: Node3D, w: float, h: float, d: float,
		hair: String, is_kid: bool) -> void:
	_part(head_pivot, "hair", Vector3(w * 1.06, h * 0.3, d * 1.06),
		Vector3(0, h * 0.9, 0), hair)

	var roll := _rng.randf()
	if roll < 0.18:
		# Long hair down the back.
		_part(head_pivot, "hair_back", Vector3(w * 0.9, h * 0.85, d * 0.3),
			Vector3(0, h * 0.35, d * 0.5), hair)
	elif roll < 0.3:
		# A ponytail, which is the only silhouette change that reads from behind.
		_part(head_pivot, "hair_tail", Vector3(w * 0.42, h * 0.55, d * 0.42),
			Vector3(0, h * 0.72, d * 0.62), hair)

	var hat := _rng.randf()
	if hat < (0.42 if is_kid else 0.3):
		var shade := _pick("shirt_")
		_part(head_pivot, "cap", Vector3(w * 1.12, h * 0.22, d * 1.12),
			Vector3(0, h * 0.98, 0), shade)
		_part(head_pivot, "cap_brim", Vector3(w * 1.05, h * 0.07, d * 0.6),
			Vector3(0, h * 0.9, -d * 0.72), shade)
	elif hat < 0.4:
		# The brim rides 2% of a head above where it used to. At `h * 0.95` a
		# brim `h * 0.1` deep put its top face at exactly `h` — which is the top
		# of the head, pointing the same way, with the whole crown inside it. Two
		# materials, white on skin, on every guest who drew a sunhat. The cap
		# above escaped it only by being thicker.
		_part(head_pivot, "sunhat", Vector3(w * 2.1, h * 0.1, d * 2.1),
			Vector3(0, h * 0.97, 0), "shirt_white")
		_part(head_pivot, "sunhat_crown", Vector3(w * 1.1, h * 0.28, d * 1.1),
			Vector3(0, h * 1.08, 0), "shirt_white")


## What a guest is carrying is most of who they are at this fidelity — the
## difference between a crowd and a set of subjects is a plush toy the size of a
## torso and a map held upside down.
func _build_carried(body: Node3D, head_pivot: Node3D, hips_h: float, torso_h: float,
		shoulder: float, depth: float, limb: float, arm: float, is_kid: bool) -> void:
	var arm_l: Node3D = body.get_node("arm_l")
	var arm_r: Node3D = body.get_node("arm_r")
	var hand_y := -arm * 0.98

	var roll := _rng.randf()
	if is_kid:
		if roll < 0.3:
			# A plush too big to carry properly, tucked a centimetre further in
			# than it was. At `-limb * 1.2` its outer face landed flush with the
			# sleeve's — both at `limb * 0.5`, both pointing out — so the arm and
			# the toy fought down one edge on every kid carrying one.
			_part(arm_r, "plush", Vector3(limb * 3.4, limb * 4.2, limb * 3.0),
				Vector3(-limb * 1.3, -arm * 0.62, -depth * 0.5), _pick("shirt_"))
		elif roll < 0.5:
			# The string is a fixed 1.4m rather than a fraction of the arm. Tied
			# to arm length it came out at half a metre, which put the balloon
			# beside the kid's head instead of over it — a floating ball rather
			# than a balloon.
			#
			# **On its own knot at the hand rather than straight onto `arm_r`,
			# since 2026-08-14c.** Hung off the arm it inherited the arm's
			# rotation, and `_animate` swings an arm 25 degrees each way: a
			# 1.6m lever off the shoulder then threw the balloon two thirds of a
			# metre fore and aft, leaning the string that far off vertical.
			# Seated was worse and constant — `_apply_seated_pose` parks the arm
			# at 0.35rad, so every kid sitting down held their balloon out at 20
			# degrees. What that reads as, at any distance where a 2cm string has
			# stopped resolving, is a loose balloon drifting over the plaza.
			#
			# The knot is what `guest.gd` counter-rotates to keep upright, and
			# it has to be a node of its own because the correction has to happen
			# at the *hand*: spinning the string about its own centre leaves its
			# top end swinging out of the fist.
			#
			# The chair-borne version below never had the fault, because it is
			# tied to the chair and a chair does not swing. This is that idea
			# applied to the wrist.
			var shade := _pick("shirt_")
			var string_length := 1.4
			var knot := Node3D.new()
			knot.position = Vector3(0, hand_y, 0)
			_add(knot, arm_r, "balloon_knot")
			# 3cm rather than 2. A string is a millimetre in life, but at 20m a
			# 2cm box is under two pixels and drops out entirely — and a balloon
			# whose string has vanished is exactly the thing this is fixing.
			_part(knot, "balloon_string", Vector3(0.03, string_length, 0.03),
				Vector3(0, string_length * 0.5, 0), "shirt_white")
			_sphere_part(knot, "balloon", 0.22,
				Vector3(0, string_length + 0.22, 0), shade)
		elif roll < 0.68:
			_cyl_part(arm_r, "cup", 0.05, 0.16, Vector3(0, hand_y, -0.04), "plastic")
		return

	if roll < 0.16:
		_part(body, "backpack", Vector3(shoulder * 0.7, torso_h * 0.72, depth * 0.7),
			Vector3(0, hips_h + torso_h * 0.55, depth * 0.72), _pick("shirt_"))
	elif roll < 0.3:
		# A park map, held open and low, which is the pose of someone lost.
		_part(arm_l, "map", Vector3(0.34, 0.26, 0.01),
			Vector3(limb * 1.4, hand_y + 0.1, -0.16), "shirt_white")
	elif roll < 0.42:
		_part(arm_l, "tote", Vector3(limb * 2.6, limb * 3.2, limb * 1.4),
			Vector3(0, hand_y - limb * 1.6, 0), _pick("shirt_"))
	elif roll < 0.54:
		_cyl_part(arm_r, "cup", 0.055, 0.18, Vector3(0, hand_y, -0.04), "plastic")
	elif roll < 0.62:
		# Someone else's camera. Other people photograph this park too, and one
		# of them is going to leave it on a bench.
		_part(arm_r, "camera", Vector3(0.11, 0.07, 0.06),
			Vector3(0, hand_y + 0.04, -0.05), "bottom_black")
		_part(head_pivot, "sunglasses", Vector3(0.11, 0.02, 0.02),
			Vector3(0, 0.0, 0.0), "bottom_black")
	elif roll < 0.7:
		_part(arm_l, "cooler", Vector3(limb * 3.0, limb * 2.2, limb * 2.0),
			Vector3(0, hand_y - limb * 1.1, 0), "shirt_white")


## The same idea for somebody whose hands are on the rims. Almost nothing a
## walking guest carries survives the move: a tote swinging from a hand becomes a
## tote hung on a push handle, a plush too big to carry becomes a plush in a lap,
## and a balloon is tied to the chair rather than to a wrist — which is what
## anybody would do with it, and reads better besides, because the string then
## stands over the chair instead of over the shoulder.
func _build_carried_seated(body: Node3D, chair: Node3D, head_pivot: Node3D,
		hips_h: float, torso_h: float, depth: float, limb: float, arm: float,
		thigh: float, seat_y: float, hip_w: float, is_kid: bool) -> void:
	var arm_l: Node3D = body.get_node("arm_l")
	var arm_r: Node3D = body.get_node("arm_r")
	var hand_y := -arm * 0.98
	# On the thighs, which are level. In the body's frame the thighs run forward
	# from the origin, so the lap is a limb's thickness above it.
	var lap := Vector3(0, limb * 0.7, -thigh * 0.45)
	# The right-hand push handle, in the chair's frame.
	var handle := Vector3(hip_w * 0.5 + 0.045,
		seat_y + hips_h * 0.5 + torso_h * 0.9, depth * 0.5 + 0.1)

	var roll := _rng.randf()
	if is_kid:
		if roll < 0.34:
			_part(body, "plush", Vector3(limb * 3.4, limb * 4.0, limb * 3.0),
				lap + Vector3(-limb * 0.6, limb * 1.9, 0), _pick("shirt_"))
		elif roll < 0.56:
			var shade := _pick("shirt_")
			var string_length := 1.4
			# No knot needed — the chair does not swing, which is the whole
			# reason this one was moved off the wrist in the first place. It
			# takes the 3cm string for the same reason the other one does.
			_part(chair, "balloon_string", Vector3(0.03, string_length, 0.03),
				handle + Vector3(0, string_length * 0.5, 0), "shirt_white")
			_sphere_part(chair, "balloon", 0.22,
				handle + Vector3(0, string_length + 0.22, 0), shade)
		elif roll < 0.72:
			_cyl_part(arm_r, "cup", 0.05, 0.16, Vector3(0, hand_y, -0.04), "plastic")
		return

	if roll < 0.16:
		# Slung over the back of the chair, which is where a day bag lives.
		_part(chair, "daypack", Vector3(hip_w * 0.66, torso_h * 0.5, 0.14),
			Vector3(0, seat_y + hips_h * 0.5 + torso_h * 0.34, depth * 0.5 + 0.11),
			_pick("shirt_"))
	elif roll < 0.3:
		_part(body, "map", Vector3(0.34, 0.26, 0.01),
			lap + Vector3(0, limb * 0.9, -0.02), "shirt_white")
	elif roll < 0.44:
		_part(chair, "tote", Vector3(limb * 2.4, limb * 3.0, limb * 1.3),
			handle + Vector3(0, -limb * 1.7, 0), _pick("shirt_"))
	elif roll < 0.56:
		_cyl_part(arm_r, "cup", 0.055, 0.18, Vector3(0, hand_y, -0.04), "plastic")
	elif roll < 0.64:
		_part(body, "camera", Vector3(0.11, 0.07, 0.06),
			lap + Vector3(0, limb * 1.1, -0.02), "bottom_black")
		_part(head_pivot, "sunglasses", Vector3(0.11, 0.02, 0.02),
			Vector3(0, 0.0, 0.0), "bottom_black")


# --- part helpers -----------------------------------------------------------


func _add(node: Node, parent: Node, nm: String) -> void:
	node.name = nm
	parent.add_child(node)
	node.owner = _root


func _part(parent: Node3D, nm: String, size: Vector3, pos: Vector3, mat: String) -> MeshInstance3D:
	var m := MeshInstance3D.new()
	m.mesh = _box
	m.material_override = mats[mat]
	m.transform = Transform3D(Basis.IDENTITY.scaled(size), pos)
	_add(m, parent, nm)
	return m


func _cyl_part(parent: Node3D, nm: String, radius: float, height: float,
		pos: Vector3, mat: String) -> void:
	var m := MeshInstance3D.new()
	m.mesh = _cyl
	m.material_override = mats[mat]
	m.transform = Transform3D(
		Basis.IDENTITY.scaled(Vector3(radius * 2.0, height, radius * 2.0)), pos)
	_add(m, parent, nm)


## A cylinder laid on its side, so it is a wheel rather than a bollard.
##
## The rotation has to be applied **outside** the scale and not through
## `Basis.scaled`, which introduces the scale in the parent's frame — so a
## cylinder turned onto its side and then "scaled" by (2r, width, 2r) comes out
## 2r wide and width tall, which is a bollard again.
func _disc(parent: Node3D, nm: String, radius: float, width: float,
		pos: Vector3, mat: String) -> void:
	_sideways(parent, nm, _wheel_cyl, Vector3(radius * 2.0, width, radius * 2.0), pos, mat)


## The tyre and the hand rim. Scaled uniformly, or the tube goes oval.
func _rim(parent: Node3D, nm: String, radius: float, pos: Vector3, mat: String,
		fat := false) -> void:
	var mesh: Mesh = _tyre_ring if fat else _ring
	_sideways(parent, nm, mesh, Vector3.ONE * radius * 2.0, pos, mat)


## A bar across the wheel, rolled about the axle. Three of them is a spoked
## wheel; without any, a dark tyre with a hole in the middle turns invisibly.
func _spoke(parent: Node3D, nm: String, radius: float, thick: float,
		roll: float, pos: Vector3, mat: String) -> void:
	var m := MeshInstance3D.new()
	m.mesh = _box
	m.material_override = mats[mat]
	m.transform = Transform3D(
		Basis(Vector3(1, 0, 0), roll) * Basis.IDENTITY.scaled(
			Vector3(thick, radius * 1.9, thick)),
		pos)
	_add(m, parent, nm)


func _sideways(parent: Node3D, nm: String, mesh: Mesh, size: Vector3,
		pos: Vector3, mat: String) -> void:
	var m := MeshInstance3D.new()
	m.mesh = mesh
	m.material_override = mats[mat]
	m.transform = Transform3D(
		Basis(Vector3(0, 0, 1), PI * 0.5) * Basis.IDENTITY.scaled(size), pos)
	_add(m, parent, nm)


func _sphere_part(parent: Node3D, nm: String, radius: float, pos: Vector3, mat: String) -> void:
	var m := MeshInstance3D.new()
	m.mesh = _sphere
	m.material_override = mats[mat]
	m.transform = Transform3D(Basis.IDENTITY.scaled(Vector3.ONE * radius * 2.0), pos)
	_add(m, parent, nm)


# --- the boardwalk ----------------------------------------------------------


## The strip's own crowd, and its own day.
##
## The day is the reason this is a second pass rather than a second copy of the
## first. A seaside strip does not fill when the park does — it fills when the
## light goes, which is the whole reason the boardwalk is on the side the sun
## sets into. At eleven in the morning there are four people down here and the
## wheel is turning empty; at seven there are fifty and every bench facing the
## water is taken. The plaza's curves say the opposite and both are right.
##
## That difference is the second instrument for reading the hour off the park.
## `documentation/design.md` asks the player to know what time it is from the
## place rather than from a readout, and the plaza already does it two ways —
## headcount and whether the tables are full. A section that peaked at the same
## hour as the plaza would have added nothing to that; one that peaks eight hours
## later means walking down the stair is itself a way of asking the time.
func _build_boardwalk() -> bool:
	# A different seed from the plaza's, or the two casts are the same fifty-six
	# people in different clothes — same heights, same builds, same draws in the
	# same order.
	# Derived rather than typed. It was a hand-placed Rect2 out to x −139, which
	# was the pavilion's neighbourhood until the strip moved sixteen metres west
	# and the pier's last two nodes fell out of the world.
	var west := Plan.PAVILION_AT.x - 8.0
	var east := Plan.BLUFF_FACE_X + 6.0
	_begin("crowd", Plan.SHORE_TOP, Rect2(west, -84.0, east - west, 164.0), 0x0B0A2D)

	_boardwalk_graph()
	_obstacles = _boardwalk_obstacles()
	if not _validate_graph():
		push_error("boardwalk graph is not walkable — fix the nodes above before regenerating")
		quit(1)
		return false

	_root.set("nodes", _graph_points)
	_root.set("edges", _graph_edges)
	_root.set("edge_steps", _graph_steps)
	_root.set("pois", _reachable_pois("boardwalk", _boardwalk_pois(), []))

	_root.set("wander_day", BOARDWALK_WANDER_DAY)
	_root.set("cafe_day", BOARDWALK_CAFE_DAY)
	_root.set("bench_day", BOARDWALK_BENCH_DAY)
	_root.set("flow_day", BOARDWALK_FLOW)

	# The way in is the back lane, because it is the only way in — everyone down
	# here came down the stair from the plaza, and the lane is what the stair
	# comes out into. Off-stage is further down the same lane, behind the backs
	# of the shops, where the only sightline is from the lane itself.
	#
	# That the player arrives this way too is the point rather than a coincidence.
	# A route with the crowd on it reads as the way in without a sign.
	_root.set("entry_node", _node_index("lane_s"))
	_root.set("hold_point", Vector3(Plan.BACK_LANE_X, Plan.SHORE_TOP, 36.0))

	_boardwalk_walking_groups()
	_boardwalk_seated_groups()
	_pad_cast()
	return _finish(BOARDWALK_PATH)


## Thin all day and then full at sunset. The peak is 19:00 — an hour before the
## sun goes down behind the pier — and it barely drops until the park shuts.
const BOARDWALK_WANDER_DAY := [
	0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
	0.10, 0.18, 0.28, 0.40, 0.50, 0.60,
	0.70, 0.82, 0.92, 1.00, 0.98, 0.80,
	0.0, 0.0,
]

## The tables outside the two food units. A lunch bump, a dip through the
## afternoon while everybody is on the pier, and then the evening — eating on
## the front after dark is most of what a boardwalk is for.
const BOARDWALK_CAFE_DAY := [
	0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
	0.05, 0.25, 0.65, 0.70, 0.45, 0.40,
	0.55, 0.80, 1.00, 0.95, 0.85, 0.55,
	0.0, 0.0,
]

## Every bench faces the water. So they fill as the light does and then stay
## full for three hours, which is the flattest curve in the park and the most
## legible one: a full rail is the hour before sunset and nothing else.
const BOARDWALK_BENCH_DAY := [
	0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
	0.10, 0.20, 0.30, 0.40, 0.50, 0.60,
	0.75, 0.90, 1.00, 1.00, 1.00, 0.85,
	0.0, 0.0,
]

## People arrive down the lane all afternoon and leave in a rush at the end. The
## turn is late and sharp compared to the plaza's, which starts drifting back
## towards the gate at four: nobody comes to the front for the afternoon and
## then heads home before the sun is down.
const BOARDWALK_FLOW := [
	0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
	1.00, 1.00, 0.90, 0.80, 0.70, 0.60,
	0.50, 0.40, 0.20, 0.00, -0.30, -1.00,
	0.0, 0.0,
]


## A strip, so the graph is a strip: a spine up the promenade with the pier
## hanging off the middle of it and the lane hanging off the back.
##
## Deliberately not a network. The plaza's graph is a ring with spokes because a
## plaza is somewhere you cross; this is a line because a promenade is somewhere
## you walk along, and giving it loops would have people cutting corners that do
## not exist.
func _boardwalk_graph() -> void:
	var points := {
		# The back lane, behind the shops. `lane_s` is the way in and out.
		"lane_s": Vector2(Plan.BACK_LANE_X, 24.0),
		"lane_m": Vector2(Plan.BACK_LANE_X, 12.0),
		"lane_n": Vector2(Plan.BACK_LANE_X, 2.0),
		# Through the hole in the frontage.
		"alley_e": Vector2(-82.5, Plan.ALLEY_Z),
		"alley_w": Vector2(-89, Plan.ALLEY_Z),
		# Where the strip and the pier meet, which is where everybody ends up.
		# The alley arrives here and the pier hangs off `pier_mouth`, 8m south,
		# because the pier came off the alley's axis and a single node cannot be
		# on both lines. Two nodes rather than one bent edge: an edge from the
		# alley straight onto the deck would cut the corner of the promenade
		# that the mouth is supposed to be entered from.
		"prom_gap": Vector2(-94, Plan.ALLEY_Z),
		"pier_mouth": Vector2(-96.0, Plan.PIER_ROOT.y),
		# North, past the wheel to the coaster.
		# West of the tables outside the corn-dog stand. It used to be east of
		# the wheel's platform as well — the comment here reasoned about "a 4m
		# gap" between the two, and both halves of that are gone: the platform
		# left the promenade on 2026-08-20, and the gap was never 4m anyway,
		# because the arithmetic was done against a ticket booth the obstacle
		# list had 16m out of place. The validator found the older bug: -66.5
		# put a graph node a metre inside a table.
		"prom_n1": Vector2(-96.5, -10.0),
		# **`wheel_q` was at -97.0 and stood inside the ticket booth.** It was
		# placed against the phantom booth the obstacle list carried 16m inland
		# — see `_boardwalk_obstacles` — so it validated cleanly and put the
		# promenade's spine through the one solid object on that stretch.
		#
		# It moved to -95.2 to clear the real one, into an 0.8m slot between the
		# booth's clearance and the corn-dog tables, and that was the tightest
		# node on the strip. The wheel went onto its own jetty later the same
		# day and took the booth and the queue to the water's edge with it, so
		# the whole band is open: back on the promenade's own line, where a
		# spine belongs.
		# Just east of `PROMENADE_X` rather than on it. The lamp standards stand
		# on that line at 9m centres and they are deliberately *not* obstacles —
		# a 22cm post is something people brush past, and treating one as a wall
		# closes a promenade. Which means the validator cannot see them, so a
		# spine laid down the middle of the paving is a spine that walks through
		# a lamp the day the spacing changes. Every other node on this run is
		# offset for the same reason; this one was put on the centre line when
		# the wheel left the promenade and the offset is the half of that which
		# was missing.
		"wheel_q": Vector2(Plan.PROMENADE_X + 1.7, -19.0),
		"prom_n2": Vector2(-94.5, -28.0),
		"station_q": Vector2(-95, -41.0),
		"prom_n3": Vector2(-98, -55.0),
		"prom_n4": Vector2(-98, -72.0),
		# Out over the water. On the pier's own axis, which stopped being the
		# alley's on 2026-08-20 — see `ParkPlan.PIER_Z`. Read off `PIER_ROOT`
		# rather than `ALLEY_Z`, or the spine runs out over open water beside
		# the deck and the pavilion door opens into the sea.
		"pier_root": Vector2(-105, Plan.PIER_ROOT.y),
		"pier_mid": Vector2(-123, Plan.PIER_ROOT.y),
		"pier_head": Vector2(-146, Plan.PIER_ROOT.y),
		"pavilion_door": Vector2(-150.5, Plan.PIER_ROOT.y),
		# South, which is the quiet end and stays that way.
		"prom_s1": Vector2(-96.5, 12.0),
		"prom_s2": Vector2(-98, 30.0),
		"prom_s3": Vector2(-98, 48.0),
		"prom_s4": Vector2(-98, 66.0),
	}
	for name in points:
		_graph_names.append(name)
		var p: Vector2 = points[name]
		_graph_points.append(Vector3(p.x, _floor, p.y))

	var links := [
		["lane_s", "lane_m"], ["lane_m", "lane_n"],
		["lane_n", "alley_e"], ["alley_e", "alley_w"], ["alley_w", "prom_gap"],
		["prom_gap", "prom_n1"], ["prom_n1", "wheel_q"], ["wheel_q", "prom_n2"],
		["prom_n2", "station_q"], ["station_q", "prom_n3"], ["prom_n3", "prom_n4"],
		["prom_gap", "pier_mouth"], ["pier_mouth", "pier_root"],
		["pier_root", "pier_mid"],
		["pier_mid", "pier_head"], ["pier_head", "pavilion_door"],
		["pier_mouth", "prom_s1"], ["prom_s1", "prom_s2"],
		["prom_s2", "prom_s3"], ["prom_s3", "prom_s4"],
	]
	for link in links:
		_edge(link[0], link[1], false)


## Same rule as the plaza's: only things somebody would actually walk around.
## Masts, lamp standards, bins and the two carts are left out — people brush past
## those, and treating a 22cm mast as a wall closes a promenade.
##
## The sea is in here, as two rectangles either side of the pier's corridor. It
## is the one obstacle that is not an object: without it a promenade node typed
## at x −85 instead of −65 validates cleanly and puts a family in the water.
func _boardwalk_obstacles() -> Array:
	var out: Array = []

	# The wheel's ticket booth. **This was at x -81.6 until 2026-08-20**, which
	# is sixteen metres inland of the booth `gen_props._boardwalk_wheel` builds
	# — the same sixteen metres the strip moved west on 2026-08-14b, and the
	# same bug the sea's comment below records being fixed on the day. So the
	# validator has been keeping people out of a phantom in the middle of the
	# walking band and letting them through the real booth, which is why the
	# promenade beside the wheel reads as choked: `prom_n1` and `wheel_q` were
	# placed against clearances measured from a booth that is not there.
	var booth := Vector2(Plan.WHEEL_AT.x + Plan.WHEEL_PLATFORM.x * 0.5 + 1.4,
		Plan.WHEEL_AT.y - 3.0)
	var circles := [
		[booth, 1.6],
	]
	for at in Plan.TABLES:
		circles.append([at, 1.15])
	for at in Plan.bench_line():
		circles.append([at, 1.05])
	for spot in circles:
		out.append({"kind": "circle", "at": spot[0], "r": spot[1]})

	var front_x := Plan.FRONT_X
	var half_d := Plan.FRONT_DEPTH * 0.5
	var rects := [
		# The frontage, in two runs with the hole between them.
		[Vector2(front_x, (Plan.FRONT_FROM_Z + Plan.GAP_FROM) * 0.5),
			Vector2(half_d, (Plan.GAP_FROM - Plan.FRONT_FROM_Z) * 0.5)],
		[Vector2(front_x, (Plan.GAP_TO + Plan.FRONT_TO_Z) * 0.5),
			Vector2(half_d, (Plan.FRONT_TO_Z - Plan.GAP_TO) * 0.5)],
		# The coaster's station, which is a building on the same line.
		[Vector2(front_x, Plan.COASTER_STATION.y - 4.0), Vector2(5.5, 6.0)],
		# The bluff, the whole east edge. The stair well is filled from this side.
		[Vector2(-54.5, 0.0), Vector2(3.5, 90.0)],
		# The wheel's platform, which is 26m of the promenade's length.
		[Vector2(Plan.WHEEL_AT.x, Plan.WHEEL_AT.y),
			Vector2(Plan.WHEEL_PLATFORM.x * 0.5, Plan.WHEEL_PLATFORM.y * 0.5)],
		# The pavilion at the pier head.
		[Vector2(Plan.PAVILION_AT.x, Plan.PAVILION_AT.y), Vector2(6.0, 6.5)],
		# The two fences that close the promenade's east side beyond the shops.
		[Vector2(front_x - half_d, -66.0), Vector2(0.2, 16.0)],
		[Vector2(front_x - half_d, 71.0), Vector2(0.2, 7.0)],
		# The sea, north and south of the pier's corridor. Measured off the
		# shore's own edge rather than typed: the strip moved sixteen metres west
		# on 2026-08-14b and a hand-placed sea ended up thirty metres inland,
		# blocking half the promenade.
		#
		# The corridor between them is the pier's own, and it is measured off
		# `PIER_ROOT.y` for the same reason the x is measured off `SHORE_EDGE`.
		# It was typed as -10..+10 while the pier sat on `ALLEY_Z`, where it
		# happened to be four metres clear either side; the pier moved eight
		# metres south on 2026-08-20 and a hand-typed corridor would have left
		# the deck's south half standing in the sea and open water walkable off
		# its north rail.
		[Vector2(Plan.SHORE_EDGE - 31.0, Plan.PIER_ROOT.y - Plan.PIER_HALF_W - 4.0 - 44.0),
			Vector2(31.0, 44.0)],
		[Vector2(Plan.SHORE_EDGE - 31.0, Plan.PIER_ROOT.y + Plan.PIER_HALF_W + 4.0 + 44.0),
			Vector2(31.0, 44.0)],
	]
	for rect in rects:
		out.append({"kind": "rect", "at": rect[0], "half": rect[1]})

	return out


## What is worth looking at, and most of it is above eye level or a long way off.
##
## That is the difference from the plaza, where the things to look at are a
## fountain and a bandstand at head height and a sign tower you crane at. Down
## here the wheel is 25m up, the coaster's crest is 27m up and ninety metres
## north, and the horizon is the horizon. A guest looking at any of them is
## looking somewhere the player can also point a camera.
func _boardwalk_pois() -> PackedVector3Array:
	var top := Plan.SHORE_TOP
	var out := PackedVector3Array([
		Vector3(Plan.WHEEL_AT.x, top + 18.6, Plan.WHEEL_AT.y),      # the wheel's hub
		Vector3(Plan.WHEEL_AT.x, top + 6.0, Plan.WHEEL_AT.y - 12.0),  # its cars, low
		Vector3(Plan.PAVILION_AT.x, top + 10.0, Plan.PAVILION_AT.y),  # the spire
		Vector3(Plan.FRONT_X, top + 27.0, -75.0),                   # the coaster's crest
		Vector3(-64.6, top + 6.9, Plan.COASTER_STATION.y - 4.0),    # the station sign
		# The water. Three points rather than one, spread along the horizon, so
		# that "looking out to sea" is a direction rather than a spot everybody
		# turns to face at once.
		Vector3(-150.0, top - 1.0, -60.0),
		Vector3(-160.0, top - 1.0, 0.0),
		Vector3(-150.0, top - 1.0, 60.0),
	])
	# The shop signs, which are there to be read, at the height they hang.
	for unit in _boardwalk_signs():
		out.append(unit)
	# The bulbs on the masts, which is what there is to look up at after dark.
	var z := Plan.WALK_FROM_Z + 15.0
	while z < Plan.WALK_TO_Z:
		out.append(Vector3(Plan.SHORE_EDGE + 1.6, top + 7.4, z))
		z += 22.0
	return out


## Mirrors the sign placement in `gen_props.gd::_boardwalk_frontage()`: above the
## parapet on the tall units, flat on the wall on the short ones.
func _boardwalk_signs() -> Array:
	var out: Array = []
	var face := Plan.FRONT_X - Plan.FRONT_DEPTH * 0.5
	for unit in Plan.FRONTAGE_UNITS:
		var mid: float = (unit["from"] + unit["to"]) * 0.5
		var h: float = unit["h"]
		var y: float = Plan.SHORE_TOP + (h + 1.9 if h >= 8.0 else h - 0.9)
		out.append(Vector3(face - 0.3, y, mid))
	return out


## The benches along the rail, read out of the plan so they cannot drift from the
## furniture `gen_props.gd` builds.
func _boardwalk_bench_spots() -> Array:
	var out: Array = []
	for at in Plan.bench_line():
		# Facing west, so a guest sitting on one is looking at the water.
		out.append({"at": Vector3(at.x, Plan.SHORE_TOP, at.y), "theta": -PI * 0.5})
	return out


## And the chairs at the four tables outside the food units. Same offsets
## `gen_props.gd` puts the chairs at, for the same reason.
func _boardwalk_chair_spots() -> Array:
	var out: Array = []
	var offs := [Vector3(0.95, 0, 0.2), Vector3(-0.9, 0, -0.35)]
	var turns := [-70.0, 110.0, -60.0, 120.0]
	for i in Plan.TABLES.size():
		var at: Vector2 = Plan.TABLES[i]
		var b := Vector3(at.x, Plan.SHORE_TOP, at.y)
		var th := deg_to_rad(turns[i])
		for j in offs.size():
			out.append({
				"at": b + offs[j],
				"theta": th + deg_to_rad(30.0 * (j + 1)),
				"table": Vector3(b.x, Plan.SHORE_TOP + 0.8, b.z),
			})
	return out


## The cast. Same size as the plaza's, on a third of the walkable ground, which
## is what a strip at its peak actually is — and `crowd.gd` only ever asks for a
## fraction of it, so the morning is nearly empty however crowded seven o'clock
## gets.
##
## Order is arrival order. The front of the list is what four in the afternoon
## looks like: couples and pairs on the promenade rather than families, because
## the families are still up in the park and come down after they have eaten.
func _boardwalk_walking_groups() -> void:
	var plan := [
		{"start": "prom_gap", "kinds": ["adult", "adult"]},
		{"start": "pier_mid", "kinds": ["adult", "adult"]},
		{"start": "prom_n1", "kinds": ["adult", "adult", "kid"]},
		{"start": "wheel_q", "kinds": ["adult", "kid"]},
		{"start": "prom_s1", "kinds": ["chair_adult", "adult"]},
		{"start": "pier_head", "kinds": ["adult"]},
		{"start": "prom_n2", "kinds": ["adult", "adult"]},
		{"start": "alley_w", "kinds": ["adult", "adult", "kid"]},
		# Started at the alley mouth, which is where the cascade comes out. The
		# strip is the section the descent exists to reach, so a mixed group
		# arriving down here together is the claim the cascade makes, standing on
		# the promenade where it can be checked by looking at it.
		{"start": "alley_e", "kinds": ["adult", "chair_kid", "kid", "adult"]},
		# Also arriving off the cascade, and the reason the ramp earns its keep on
		# an ordinary day rather than an exceptional one. The strip is 160m of
		# promenade with the interest at the north end, which is a long way to
		# carry a toddler — so the people who come down here with one bring the
		# buggy, and the descent has to take it.
		{"start": "alley_e", "kinds": ["stroller_adult", "adult", "kid"]},
		{"start": "station_q", "kinds": ["adult", "kid", "kid"]},
		{"start": "pier_root", "kinds": ["adult"]},
		{"start": "prom_s2", "kinds": ["adult", "adult"]},
		{"start": "prom_n3", "kinds": ["adult", "adult"]},
		{"start": "lane_m", "kinds": ["adult", "adult", "kid", "kid"]},
		{"start": "prom_gap", "kinds": ["adult"]},
		{"start": "wheel_q", "kinds": ["adult", "adult", "kid"]},
		{"start": "pier_mid", "kinds": ["adult", "kid"]},
		{"start": "prom_s3", "kinds": ["adult"]},
		{"start": "prom_n4", "kinds": ["adult"]},
		# The promenade is where a pram goes at seven in the evening, which is the
		# boardwalk's peak and the plaza's decline. Putting one here rather than
		# in the plaza is part of what makes the two sections disagree.
		{"start": "prom_n2", "kinds": ["pram_adult", "adult"]},
	]

	for entry in plan:
		var origin: Vector3 = _graph_points[_node_index(entry["start"])]
		var group := _group_index
		_group_index += 1
		var leader_name := ""
		var kinds: Array = entry["kinds"]
		var members: Array = []
		for i in kinds.size():
			var scatter := Vector3(_rng.randf_range(-1.0, 1.0), 0.0, _rng.randf_range(-1.0, 1.0))
			var guest := _guest(kinds[i], origin + scatter, _rng.randf_range(0.0, TAU), group)
			members.append(guest)
			if i == 0:
				leader_name = guest.name
			else:
				guest.set("leader_path", NodePath("../" + leader_name))
				var lateral: float = _rng.randf_range(0.55, 1.15) * (1.0 if i % 2 == 0 else -1.0)
				var behind: float = _rng.randf_range(0.4, 1.5) if kinds[i] == "adult" \
					else _rng.randf_range(0.9, 2.4)
				guest.set("follow_offset", Vector3(lateral, 0.0, behind))
		_pace_group(members)


## Who is sitting down, and in what order the seats fill.
##
## The benches fill from the middle of the strip outwards rather than from one
## end, because the middle is where the pier is and the pier is what people came
## to look at. The far south benches are the last to go and are usually empty,
## which is correct — a strip has a quiet end and pretending otherwise is what
## makes a generated crowd read as wallpaper.
func _boardwalk_seated_groups() -> void:
	var benches := _boardwalk_bench_spots()
	# Bench indices, nearest the pier first. `bench_line()` runs north to south,
	# so the middle of the list is the middle of the strip. The third column is
	# how many of the group parked alongside rather than sat down — every bench
	# here faces the water, and pulling up at the end of one beside whoever you
	# came with is what a wheelchair user does with a view.
	var plan := [[4, 2, 0], [5, 2, 1], [3, 1, 0], [6, 2, 0], [2, 2, 0], [7, 1, 0], [1, 2, 0]]
	for entry in plan:
		var bench: Dictionary = benches[entry[0]]
		var group := _group_index
		_group_index += 1
		var members: Array = []
		# The whole group, not the bench alone. Somebody sitting on their own
		# with a wheelchair pulled up beside them came with company, and the
		# singleton rule in `_seat_kind` is asking about company.
		var party := int(entry[1]) + int(entry[2])
		for s in int(entry[1]):
			var side := -0.45 if s == 0 else 0.45
			var offset: Vector3 = Basis(Vector3.UP, bench["theta"]) * Vector3(side, 0.0, 0.06)
			var seat: Vector3 = bench["at"] + offset
			var guest := _guest(_seat_kind(party, 0.25), seat, bench["theta"] + PI, group)
			guest.set("group_kind", "bench")
			guest.set("seat_at", seat)
			guest.set("seat_yaw", bench["theta"] + PI)
			guest.set("seat_height", 0.51)
			members.append(guest)
		for w in int(entry[2]):
			# Past the end of the bench and a little back off the rail, so the
			# chair stands beside the arm of it rather than through it. Facing
			# the same way as everyone on it, which is west, which is the sunset.
			#
			# 1.35 and not 1.15: a bench is 1.8m long and a chair is about 0.65
			# wide, so anything under 1.25 puts the chair's back corner through
			# the bench's end corner. The two overlap in one axis at a time and
			# the arithmetic has to be done in both.
			var offset: Vector3 = Basis(Vector3.UP, bench["theta"]) \
				* Vector3(1.35 + 0.75 * w, 0.0, -0.35)
			var seat: Vector3 = bench["at"] + offset
			var guest := _guest("chair_adult", seat, bench["theta"] + PI, group)
			guest.set("group_kind", "bench")
			guest.set("seat_at", seat)
			guest.set("seat_yaw", bench["theta"] + PI)
			members.append(guest)
		_pace_seated_group(members)

	var chairs := _boardwalk_chair_spots()
	for table in 4:
		var group := _group_index
		_group_index += 1
		var members: Array = []
		for j in 2:
			var chair: Dictionary = chairs[table * 2 + j]
			var guest := _guest("adult", chair["at"], chair["theta"] + PI, group)
			guest.set("group_kind", "cafe")
			guest.set("seat_at", chair["at"])
			guest.set("seat_yaw", chair["theta"] + PI)
			guest.set("seat_height", 0.47)
			members.append(guest)
		_pace_seated_group(members)


## The hillside east of the plaza, and **the reason the graph moved out of the
## plaza's crowd rather than staying in it.** Twenty-two of those nodes are up a
## cascade nobody standing at the fountain can walk to, and a cast mounted for
## ground the player is not on is a cast loaded for nothing. The seam at the east
## gate is what makes the split possible; this is what it buys.
##
## Small on purpose. Nothing is on these terraces yet — the bays are cut and
## empty — so the honest population is people making the climb and a few at the
## top, not a crowd standing about in front of shops that do not exist.
func _build_terraces() -> bool:
	# Its own seed, or this is the plaza's cast in different clothes.
	_begin("crowd", 0.0, Rect2(30.0, -32.0, 92.0, 64.0), 0x7E44)

	_east_graph()
	# No obstacle list. Everything solid out here is hill, masonry or water, and
	# the graph is laid down the middle of the ground between them by
	# construction — there is no furniture to walk into because there is no
	# furniture. When the bays get their kiosks this wants filling in.
	_obstacles = []
	if not _validate_graph():
		push_error("terraces graph is not walkable — fix the nodes above before regenerating")
		quit(1)
		return false

	_root.set("nodes", _graph_points)
	_root.set("edges", _graph_edges)
	_root.set("edge_steps", _graph_steps)
	_root.set("pois", _reachable_pois("terraces", _terraces_pois(), []))

	# In through the gate, and off-stage back through it. Everyone up here walked
	# out of the plaza, which is the same argument the boardwalk's back lane
	# makes: a route with the crowd on it reads as the way in without a sign.
	_root.set("entry_node", _node_index("e_gate"))
	_root.set("hold_point", Vector3(34.0, 0.0, Plan.ARCH_AT.y))

	_terraces_walking_groups()
	_pad_cast()
	return _finish(TERRACES_PATH)


## What there is to look at up here. Read off the plan rather than typed, which
## is the fix `gen_crowd`'s plaza POIs needed after they spent a fortnight in the
## 80m plaza's coordinates.
func _terraces_pois() -> PackedVector3Array:
	var out := PackedVector3Array()
	var axis: float = Plan.ARCH_AT.y
	# The niche fountain, which is the monument's one lit interior.
	out.append(Vector3(Plan.HILL_FACE_X - Plan.LANDING_D + 1.2, 2.4, axis))
	# The collecting pool, and three bowls up the chain.
	out.append(Vector3((Plan.POOL_FROM_X + Plan.CLIMB_FROM_X) * 0.5,
		Plan.POOL_TOP_Y + 0.3, axis))
	for i in [1, 5, 10]:
		var bx: float = Plan.CLIMB_FROM_X + Plan.BASIN_STEP * (float(i) + 0.5)
		out.append(Vector3(bx, Plan.climb_floor_y(bx) + 0.6, axis))
	# Back down the axis at the clock tower, which is the view the belvedere is
	# for and the only instrument the park has.
	out.append(Vector3(Plan.CLOCK_TOWER_AT.x, 26.0, Plan.CLOCK_TOWER_AT.y))
	return out


## Who is on the hill. **Two of these groups are the routing, standing up.**
##
## The chair and the buggy start at the foot and are the first guests in the park
## whose route differs from the person beside them: `edge_steps` marks the south
## wing and the south run stepped, so they take the north ramp both times while
## everybody else picks either. Nothing else in the park could have shown that.
func _terraces_walking_groups() -> void:
	var plan := [
		{"start": "e_court", "kinds": ["adult", "adult"]},
		{"start": "e_wing_n_3", "kinds": ["chair_adult", "adult"]},
		{"start": "e_court", "kinds": ["stroller_adult", "adult", "kid"]},
		{"start": "e_belv", "kinds": ["adult", "kid"]},
		{"start": "e_belv_s", "kinds": ["adult", "adult"]},
		{"start": "e_climb_s_2", "kinds": ["adult"]},
		{"start": "e_bay_n_0", "kinds": ["adult", "adult"]},
		{"start": "e_climb_n_4", "kinds": ["adult", "kid"]},
		{"start": "e_top", "kinds": ["adult", "adult"]},
	]
	for entry in plan:
		var origin: Vector3 = _graph_points[_node_index(entry["start"])]
		var group := _group_index
		_group_index += 1
		var leader_name := ""
		var kinds: Array = entry["kinds"]
		var members: Array = []
		for i in kinds.size():
			var scatter := Vector3(_rng.randf_range(-1.0, 1.0), 0.0,
				_rng.randf_range(-1.0, 1.0))
			var guest := _guest(kinds[i], origin + scatter,
				_rng.randf_range(0.0, TAU), group)
			members.append(guest)
			if i == 0:
				leader_name = guest.name
			else:
				guest.set("leader_path", NodePath("../" + leader_name))
				var lateral: float = _rng.randf_range(0.55, 1.15) \
					* (1.0 if i % 2 == 0 else -1.0)
				# `begins_with`, never `==`. The kind vocabulary has seven entries
				# and a bare equality test drops `chair_adult`, `stroller_adult`,
				# `twin_adult` and `pram_adult` into the child's range — which
				# reads as somebody being left two metres behind their own group.
				var behind: float = _rng.randf_range(0.4, 1.5) \
					if not String(kinds[i]).ends_with("kid") \
					else _rng.randf_range(0.9, 2.4)
				guest.set("follow_offset", Vector3(lateral, 0.0, behind))
		_pace_group(members)
