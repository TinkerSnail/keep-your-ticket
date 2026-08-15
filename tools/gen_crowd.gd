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

var _graph_names: PackedStringArray = PackedStringArray()
var _graph_points: PackedVector3Array = PackedVector3Array()
var _graph_edges: PackedInt32Array = PackedInt32Array()

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
	quit()


## Reset everything a section owns. The two passes share the body-building and
## nothing else, and the plaza must come out byte-identical to what is committed
## — so it runs first, with its seed set here rather than once at startup.
func _begin(nm: String, floor_y: float, bounds: Rect2, seed_value: int) -> void:
	_rng.seed = seed_value
	_graph_names = PackedStringArray()
	_graph_points = PackedVector3Array()
	_graph_edges = PackedInt32Array()
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
	_root.set("pois", _plaza_pois())

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
	}
	for key in defs:
		var m := StandardMaterial3D.new()
		m.albedo_color = defs[key]
		m.roughness = 0.9 if key.begins_with("skin") else 0.85
		if key == "metal":
			m.roughness = 0.55
			m.metallic = 0.2
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
		_graph_edges.append(_node_index(link[0]))
		_graph_edges.append(_node_index(link[1]))


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


## Things a guest might plausibly look at. Height matters: the sign tower is a
## different photograph looked up at than looked across.
func _plaza_pois() -> PackedVector3Array:
	var out := PackedVector3Array([
		Vector3(0, 3.1, 0),           # the fountain column
		Vector3(18, 12.5, -16),       # the sign board, high up
		Vector3(-12, 1.4, -12),       # the bandstand stage
		Vector3(9, 2.0, 6.0),         # the photo hut counter
		Vector3(-6, 1.4, -10),        # the cart
		Vector3(5.8, 1.7, 5.1),       # the tied balloons
		Vector3(3, 1.0, 10),          # a-frame signs, which are there to be read
		Vector3(-9, 1.0, -2),
		Vector3(12, 1.0, -8),
		Vector3(3.0, 0.9, 7.5),       # the newspaper boxes
		Vector3(15.5, 4.6, -16),      # flagpole banners
		Vector3(20.5, 4.6, -16),
		# The park over the wall. Guests looking up and out at rides they
		# cannot reach from here is most of what sells the plaza as a hub.
		Vector3(-58, 14.0, -4),       # the wheel, west
		Vector3(54, 24.0, -40),       # the tower, north-east
		Vector3(-22, 12.0, -58),      # the coaster, north
	])
	for spot in _lamp_spots():
		out.append(Vector3(spot.x, 4.1, spot.y))
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
		{"start": "queue", "kinds": ["adult", "adult"]},
		{"start": "street_n", "kinds": ["adult", "adult"]},
		{"start": "ring_w", "kinds": ["adult", "adult"]},
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
		{"start": "hut_walk", "kinds": ["adult"]},
	]

	for entry in plan:
		var origin: Vector3 = _graph_points[_node_index(entry["start"])]
		var group := _group_index
		_group_index += 1
		var leader_name := ""
		var kinds: Array = entry["kinds"]
		for i in kinds.size():
			var scatter := Vector3(_rng.randf_range(-1.0, 1.0), 0.0, _rng.randf_range(-1.0, 1.0))
			var guest := _guest(kinds[i], origin + scatter, _rng.randf_range(0.0, TAU), group)
			if i == 0:
				leader_name = guest.name
			else:
				guest.set("leader_path", NodePath("../" + leader_name))
				# Kids trail further back and wider, which is where the
				# straggler comes from without anyone scripting one.
				var lateral: float = _rng.randf_range(0.55, 1.15) * (1.0 if i % 2 == 0 else -1.0)
				var behind: float = _rng.randf_range(0.4, 1.5) if kinds[i] == "adult" \
					else _rng.randf_range(0.9, 2.4)
				guest.set("follow_offset", Vector3(lateral, 0.0, behind))


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
		for s in int(entry[1]):
			var side := -0.45 if s == 0 else 0.45
			var offset: Vector3 = Basis(Vector3.UP, bench["theta"]) * Vector3(side, 0.0, 0.06)
			var seat: Vector3 = bench["at"] + offset
			var guest := _guest(
				"adult" if _rng.randf() > 0.25 else "kid",
				seat,
				bench["theta"] + PI,
				group)
			guest.set("group_kind", "bench")
			guest.set("seat_at", seat)
			guest.set("seat_yaw", bench["theta"] + PI)
			guest.set("seat_height", 0.51)

	# A table at a time, both chairs. Two people at one table is a pair having
	# lunch; two people at two tables is two strangers, and the cafe fills more
	# convincingly as the first thing.
	var chairs := _plaza_chair_spots()
	for table in 3:
		var group := _group_index
		_group_index += 1
		for j in 2:
			var chair: Dictionary = chairs[table * 2 + j]
			var guest := _guest("adult", chair["at"], chair["theta"] + PI, group)
			guest.set("group_kind", "cafe")
			guest.set("seat_at", chair["at"])
			guest.set("seat_yaw", chair["theta"] + PI)
			guest.set("seat_height", 0.475)


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
	]

	while _guest_index < CAST_TARGET:
		var origin: Vector3 = _graph_points[pad.randi_range(0, _graph_points.size() - 1)]
		var kinds: Array = shapes[pad.randi_range(0, shapes.size() - 1)]
		var group := _group_index
		_group_index += 1
		var leader_name := ""
		for i in kinds.size():
			if _guest_index >= CAST_TARGET:
				break
			var scatter := Vector3(pad.randf_range(-1.2, 1.2), 0.0, pad.randf_range(-1.2, 1.2))
			var guest := _guest(kinds[i], origin + scatter, pad.randf_range(0.0, TAU), group)
			if i == 0:
				leader_name = guest.name
			elif leader_name != "":
				guest.set("leader_path", NodePath("../" + leader_name))
				var lateral: float = pad.randf_range(0.55, 1.15) * (1.0 if i % 2 == 0 else -1.0)
				var behind: float = pad.randf_range(0.4, 1.5) if kinds[i] == "adult" \
					else pad.randf_range(0.9, 2.4)
				guest.set("follow_offset", Vector3(lateral, 0.0, behind))


func _guest(kind: String, at: Vector3, yaw: float, group: int) -> Node3D:
	var is_kid := kind == "kid"
	var height := _rng.randf_range(1.05, 1.34) if is_kid else _rng.randf_range(1.58, 1.9)
	var build := _rng.randf_range(0.88, 1.18)

	var guest := AnimatableBody3D.new()
	guest.set_script(load(GUEST_SCRIPT))
	guest.transform = Transform3D(Basis(Vector3.UP, yaw), Vector3(at.x, _floor, at.z))
	_add(guest, _root, "guest_%02d" % _guest_index)
	_guest_index += 1

	# Shorter legs mean more steps for the same ground, so a mixed crowd moves
	# at mixed speeds without anyone choosing the numbers.
	guest.set("walk_speed", (1.05 + (height - 1.5) * 0.55) * _rng.randf_range(0.9, 1.12))
	guest.set("group_id", group)
	guest.set("rng_seed", _rng.randi())
	# Children are the curious ones and adults are more often the shy ones,
	# which is why the kid in the family photo is the one looking at you.
	guest.set("curiosity", _rng.randf_range(0.55, 1.0) if is_kid else _rng.randf_range(0.1, 0.8))
	guest.set("shyness", _rng.randf_range(0.0, 0.25) if is_kid else _rng.randf_range(0.05, 0.5))

	_build_body(guest, height, build, is_kid)
	return guest


# --- bodies -----------------------------------------------------------------


func _build_body(guest: Node3D, h: float, build: float, is_kid: bool) -> void:
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

	var skin := _pick("skin_")
	var shirt := _pick("shirt_")
	var bottom := _pick("bottom_")
	var hair := _pick("hair_")

	var collision := CollisionShape3D.new()
	var shape := CapsuleShape3D.new()
	shape.radius = maxf(shoulder * 0.5, 0.22)
	shape.height = h
	collision.shape = shape
	collision.position.y = h * 0.5
	_add(collision, guest, "collision")

	var body := Node3D.new()
	body.position.y = leg
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

	for side in [-1.0, 1.0]:
		var nm := "hip_l" if side < 0.0 else "hip_r"
		var pivot := Node3D.new()
		pivot.position = Vector3(side * hip_w * 0.26, 0, 0)
		_add(pivot, body, nm)
		_part(pivot, nm + "_thigh", Vector3(limb * 1.25, thigh, limb * 1.25),
			Vector3(0, -thigh * 0.5, 0), bottom)
		var knee := Node3D.new()
		knee.position = Vector3(0, -thigh, 0)
		_add(knee, pivot, "knee_l" if side < 0.0 else "knee_r")
		# guest.gd reads shin length off this child, so it stays first.
		_part(knee, "shin", Vector3(limb * 1.1, shin, limb * 1.1),
			Vector3(0, -shin * 0.5, 0), skin if _rng.randf() > 0.4 else bottom)
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
	_build_carried(body, head_pivot, hips_h, torso_h, shoulder, depth, limb, arm, is_kid)


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
		_part(head_pivot, "sunhat", Vector3(w * 2.1, h * 0.1, d * 2.1),
			Vector3(0, h * 0.95, 0), "shirt_white")
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
			# A plush too big to carry properly.
			_part(arm_r, "plush", Vector3(limb * 3.4, limb * 4.2, limb * 3.0),
				Vector3(-limb * 1.2, -arm * 0.62, -depth * 0.5), _pick("shirt_"))
		elif roll < 0.5:
			# The string is a fixed 1.4m rather than a fraction of the arm. Tied
			# to arm length it came out at half a metre, which put the balloon
			# beside the kid's head instead of over it — a floating ball rather
			# than a balloon.
			var shade := _pick("shirt_")
			var string_length := 1.4
			_part(arm_r, "balloon_string", Vector3(0.02, string_length, 0.02),
				Vector3(0, hand_y + string_length * 0.5, 0), "shirt_white")
			_sphere_part(arm_r, "balloon", 0.22,
				Vector3(0, hand_y + string_length + 0.22, 0), shade)
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
	_root.set("pois", _boardwalk_pois())

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
		"prom_gap": Vector2(-94, Plan.ALLEY_Z),
		# North, past the wheel to the coaster.
		# West of the tables outside the corn-dog stand and east of the wheel
		# platform, which between them leave a 4m gap. The validator found this:
		# -66.5 put a graph node a metre inside a table.
		"prom_n1": Vector2(-96.5, -10.0),
		"wheel_q": Vector2(-97.0, -19.0),
		"prom_n2": Vector2(-94.5, -28.0),
		"station_q": Vector2(-95, -41.0),
		"prom_n3": Vector2(-98, -55.0),
		"prom_n4": Vector2(-98, -72.0),
		# Out over the water.
		"pier_root": Vector2(-105, Plan.ALLEY_Z),
		"pier_mid": Vector2(-123, Plan.ALLEY_Z),
		"pier_head": Vector2(-146, Plan.ALLEY_Z),
		"pavilion_door": Vector2(-150.5, Plan.ALLEY_Z),
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
		["prom_gap", "pier_root"], ["pier_root", "pier_mid"],
		["pier_mid", "pier_head"], ["pier_head", "pavilion_door"],
		["prom_gap", "prom_s1"], ["prom_s1", "prom_s2"],
		["prom_s2", "prom_s3"], ["prom_s3", "prom_s4"],
	]
	for link in links:
		_graph_edges.append(_node_index(link[0]))
		_graph_edges.append(_node_index(link[1]))


## Same rule as the plaza's: only things somebody would actually walk around.
## Masts, lamp standards, bins and the two carts are left out — people brush past
## those, and treating a 22cm mast as a wall closes a promenade.
##
## The sea is in here, as two rectangles either side of the pier's corridor. It
## is the one obstacle that is not an object: without it a promenade node typed
## at x −85 instead of −65 validates cleanly and puts a family in the water.
func _boardwalk_obstacles() -> Array:
	var out: Array = []

	var circles := [
		[Vector2(-81.6, -19.0), 1.6],   # the wheel's ticket booth
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
		[Vector2(Plan.SHORE_EDGE - 31.0, -50.0), Vector2(31.0, 40.0)],
		[Vector2(Plan.SHORE_EDGE - 31.0, 50.0), Vector2(31.0, 40.0)],
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
		{"start": "prom_s1", "kinds": ["adult", "adult"]},
		{"start": "pier_head", "kinds": ["adult"]},
		{"start": "prom_n2", "kinds": ["adult", "adult"]},
		{"start": "alley_w", "kinds": ["adult", "adult", "kid"]},
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
	]

	for entry in plan:
		var origin: Vector3 = _graph_points[_node_index(entry["start"])]
		var group := _group_index
		_group_index += 1
		var leader_name := ""
		var kinds: Array = entry["kinds"]
		for i in kinds.size():
			var scatter := Vector3(_rng.randf_range(-1.0, 1.0), 0.0, _rng.randf_range(-1.0, 1.0))
			var guest := _guest(kinds[i], origin + scatter, _rng.randf_range(0.0, TAU), group)
			if i == 0:
				leader_name = guest.name
			else:
				guest.set("leader_path", NodePath("../" + leader_name))
				var lateral: float = _rng.randf_range(0.55, 1.15) * (1.0 if i % 2 == 0 else -1.0)
				var behind: float = _rng.randf_range(0.4, 1.5) if kinds[i] == "adult" \
					else _rng.randf_range(0.9, 2.4)
				guest.set("follow_offset", Vector3(lateral, 0.0, behind))


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
	# so the middle of the list is the middle of the strip.
	var plan := [[4, 2], [5, 2], [3, 1], [6, 2], [2, 2], [7, 1], [1, 2]]
	for entry in plan:
		var bench: Dictionary = benches[entry[0]]
		var group := _group_index
		_group_index += 1
		for s in int(entry[1]):
			var side := -0.45 if s == 0 else 0.45
			var offset: Vector3 = Basis(Vector3.UP, bench["theta"]) * Vector3(side, 0.0, 0.06)
			var seat: Vector3 = bench["at"] + offset
			var guest := _guest(
				"adult" if _rng.randf() > 0.25 else "kid",
				seat,
				bench["theta"] + PI,
				group)
			guest.set("group_kind", "bench")
			guest.set("seat_at", seat)
			guest.set("seat_yaw", bench["theta"] + PI)
			guest.set("seat_height", 0.51)

	var chairs := _boardwalk_chair_spots()
	for table in 4:
		var group := _group_index
		_group_index += 1
		for j in 2:
			var chair: Dictionary = chairs[table * 2 + j]
			var guest := _guest("adult", chair["at"], chair["theta"] + PI, group)
			guest.set("group_kind", "cafe")
			guest.set("seat_at", chair["at"])
			guest.set("seat_yaw", chair["theta"] + PI)
			guest.set("seat_height", 0.47)
