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
const GUEST_SCRIPT := "res://scenes/npc/guest.gd"
const CROWD_SCRIPT := "res://scenes/npc/crowd.gd"

## Guest radius plus room to not scrape. Anything closer than this to a prop
## counts as blocked.
const CLEARANCE := 0.45

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


func _initialize() -> void:
	# Fixed seed: this file is committed, so the same source must produce the
	# same scene or every run shows up as a diff.
	_rng.seed = 0x5150
	_build_resources()

	_root = Node3D.new()
	_root.name = "crowd"
	_root.set_script(load(CROWD_SCRIPT))

	_build_graph()
	if not _validate_graph():
		push_error("graph is not walkable — fix the nodes above before regenerating")
		quit(1)
		return

	_root.set("nodes", _graph_points)
	_root.set("edges", _graph_edges)
	_root.set("pois", _points_of_interest())

	# The way in and out, and where off-stage is. z=45 is the entrance street's
	# own ground, six metres beyond the perimeter wall, in the middle lane
	# between two ranges of shopfronts that stand at x −9 and +6. Nobody in the
	# plaza is looking at it unless they are looking down the street at the
	# gate — which is exactly the case the crowd checks for before using it.
	_root.set("entry_node", _node_index("gate"))
	_root.set("hold_point", Vector3(-1.5, 0.0, 45.0))

	_walking_groups()
	_seated_groups()

	var saved := _save(_root, OUT_PATH)
	# Nothing here was ever added to a tree, so it has to be released by hand.
	_root.free()
	if not saved:
		return
	quit()


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
func _build_graph() -> void:
	# Every position here survived `_validate_graph`, and several of them are not
	# where they were first put. What the validator turned up: the south side of
	# the plaza is not a corridor. `bench_south`, `bench_sw` and `planter_b`
	# between them leave no gap wide enough to walk along the south wall, so
	# east–west traffic goes around the fountain instead. That is what a real
	# plaza does, and it was found by checking rather than by deciding.
	var points := {
		"gate": Vector2(-1.5, 27.0),
		"south": Vector2(-1.5, 21.5),
		"south_east": Vector2(6.5, 18.0),
		"south_west": Vector2(-11.0, 17.0),
		"hut_walk": Vector2(4.6, 14.0),
		"queue": Vector2(8.5, 15.5),
		"cafe_s": Vector2(16.0, 14.5),
		"cafe_mid": Vector2(15.0, 10.0),
		"cafe_n": Vector2(15.5, 5.5),
		"east": Vector2(17.0, -5.0),
		"sign": Vector2(14.5, -13.5),
		"north": Vector2(4.5, -16.0),
		"ring_s": Vector2(0.0, 11.0),
		"ring_sw": Vector2(-6.5, 5.5),
		"ring_w": Vector2(-12.0, 0.0),
		# The ring bulges around an a-frame sign and the bench at 235 degrees,
		# which is why the north-west is two nodes instead of a clean arc.
		"ring_wnw": Vector2(-10.5, -4.0),
		"ring_nw": Vector2(-3.0, -9.0),
		"ring_n": Vector2(0.0, -11.0),
		"ring_ne": Vector2(8.0, -8.0),
		"ring_e": Vector2(12.0, 0.0),
		"west_mid": Vector2(-11.5, 9.0),
		"west": Vector2(-16.0, 4.0),
		"west_s": Vector2(-18.0, 11.0),
		"west_n": Vector2(-18.5, -2.0),
		"band_e": Vector2(-3.5, -12.0),
		# Behind the bandstand the walkable strip is 1.8m wide, between one of
		# the bandstand's own benches and the north perimeter. Both of these sit
		# in it, which is why they are further south than they look like they
		# should be.
		"band_n": Vector2(-9.0, -21.0),
		"band_w": Vector2(-19.0, -21.0),
	}
	for name in points:
		_graph_names.append(name)
		var p: Vector2 = points[name]
		_graph_points.append(Vector3(p.x, 0.0, p.y))

	# `band_w` is deliberately a dead end. The crates parked against the west
	# wall block the corridor down the bandstand's blind side, so the only way
	# in is from the north — which is exactly the kind of thing the player is
	# meant to learn about this place by walking it.
	var links := [
		["gate", "south"],
		["south", "south_east"], ["south", "ring_s"],
		["south_east", "queue"], ["south_east", "hut_walk"],
		["queue", "hut_walk"], ["queue", "cafe_s"],
		["cafe_s", "cafe_mid"],
		["cafe_mid", "cafe_n"],
		["cafe_n", "east"],
		["east", "sign"], ["east", "ring_e"],
		["sign", "north"],
		["north", "ring_n"], ["north", "ring_ne"], ["north", "band_n"],
		["hut_walk", "ring_s"],
		["ring_s", "ring_sw"],
		["ring_sw", "ring_w"], ["ring_sw", "west_mid"],
		["ring_w", "ring_wnw"], ["ring_w", "west"], ["ring_w", "west_n"],
		["ring_w", "west_mid"],
		["ring_wnw", "ring_nw"],
		["ring_nw", "ring_n"], ["ring_nw", "band_e"],
		["ring_n", "ring_ne"],
		["ring_ne", "ring_e"],
		["band_e", "band_n"],
		["band_n", "band_w"],
		["west", "west_mid"], ["west", "west_s"], ["west", "west_n"],
		["west_s", "south_west"],
		["south_west", "west_mid"],
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
func _obstacles() -> Array:
	var out: Array = []

	# Circles: [centre, radius]
	var circles := [
		[Vector2(0, 0), 5.0],          # fountain
		[Vector2(-6, -10), 1.3],       # cart
		# Table and its two chairs. The umbrella above is 2.3m up and overhangs
		# the corridor rather than blocking it.
		[Vector2(14, 3), 1.15],
		[Vector2(17, 8), 1.15],
		[Vector2(13, 12), 1.15],
		[Vector2(-19, -6), 1.0],       # crates
		[Vector2(-13, 18), 1.3],       # picnic tables
		[Vector2(-17, 15), 1.3],
		[Vector2(3, 10), 0.65],        # a-frames
		[Vector2(-9, -2), 0.65],
		[Vector2(12, -8), 0.65],
		[Vector2(19.3, 2.0), 0.6],     # ladder
		[Vector2(15.5, -16), 0.25],    # flagpoles
		[Vector2(20.5, -16), 0.25],
	]
	for spot in circles:
		out.append({"kind": "circle", "at": spot[0], "r": spot[1]})

	for spot in _bench_spots():
		out.append({"kind": "circle", "at": Vector2(spot["at"].x, spot["at"].z), "r": 1.05})

	# Rectangles: [centre, half extent]
	var rects := [
		[Vector2(-26, -4), Vector2(5, 12)],       # building_west
		[Vector2(2, -28), Vector2(14, 5)],        # building_north
		[Vector2(26, 2), Vector2(6, 9)],          # building_east
		[Vector2(-16, 26), Vector2(7, 4)],        # building_south_west
		[Vector2(12, 27), Vector2(6, 4)],         # building_south_east
		[Vector2(9, 8), Vector2(3.2, 2.7)],       # photo hut and its roof
		[Vector2(-12, -12), Vector2(4.5, 4.5)],   # bandstand
		[Vector2(18, -16), Vector2(0.8, 0.8)],    # sign tower
		[Vector2(-8, 10), Vector2(1.5, 1.5)],     # planters
		[Vector2(2, 16), Vector2(1.5, 1.5)],
		[Vector2(-7, 26), Vector2(1.3, 1.3)],
		[Vector2(4, 26), Vector2(1.3, 1.3)],
		[Vector2(-21.5, -27), Vector2(8.5, 4)],   # perimeter
		[Vector2(22, -26), Vector2(7, 4.5)],
		[Vector2(-26, -19.5), Vector2(5, 3.5)],
		[Vector2(26, -14), Vector2(6, 7)],
		[Vector2(-26, 16), Vector2(5, 7)],
		[Vector2(26, 17), Vector2(6, 6)],
		[Vector2(-28, 26), Vector2(4, 5)],
		[Vector2(25, 27), Vector2(6, 4)],
		[Vector2(8.5, 12), Vector2(3.2, 0.2)],    # queue rope
		[Vector2(2, -20), Vector2(6.2, 0.2)],     # bollard lines
		[Vector2(0, 30), Vector2(6.2, 0.2)],
	]
	for rect in rects:
		out.append({"kind": "rect", "at": rect[0], "half": rect[1]})

	return out


func _blocked(p: Vector2, obstacles: Array) -> String:
	if absf(p.x) > 36.0 or absf(p.y) > 36.0:
		return "outside the walls"
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
	var obstacles := _obstacles()
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
func _points_of_interest() -> PackedVector3Array:
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
func _bench_spots() -> Array:
	var out: Array = []
	var r := 7.5
	for deg in [25.0, 95.0, 165.0, 235.0, 305.0]:
		var a := deg_to_rad(deg)
		var p := Vector3(r * cos(a), 0.0, r * sin(a))
		out.append({"at": p, "theta": atan2(-p.x, -p.z)})
	out.append({"at": Vector3(4.5, 0, 11.5), "theta": deg_to_rad(8.0)})
	out.append({"at": Vector3(-5, 0, 19), "theta": deg_to_rad(186.0)})

	var band := Vector3(-12, 0, -12)
	for deg in [20.0, 140.0, 260.0]:
		var a := deg_to_rad(deg)
		var p: Vector3 = band + Vector3(7.4 * cos(a), 0.0, 7.4 * sin(a))
		var d: Vector3 = band - p
		out.append({"at": p, "theta": atan2(d.x, d.z)})
	out.append({"at": Vector3(-11, 0, 20), "theta": deg_to_rad(120.0)})
	out.append({"at": Vector3(2, 0, 22), "theta": deg_to_rad(200.0)})
	return out


## Mirrors `gen_props.gd::_cafe()` for the same reason.
func _chair_spots() -> Array:
	var out: Array = []
	var spots := [Vector2(14, 3), Vector2(17, 8), Vector2(13, 12)]
	var turns := [15.0, -25.0, 40.0]
	var offs := [Vector3(0.95, 0, 0.2), Vector3(-0.9, 0, -0.35)]
	for i in spots.size():
		var b := Vector3(spots[i].x, 0, spots[i].y)
		var th := deg_to_rad(turns[i])
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
func _walking_groups() -> void:
	# Families lead with an adult and trail a kid; pairs walk abreast; singles
	# are the ones who stop in the middle of everything.
	var plan := [
		{"start": "gate", "kinds": ["adult", "adult", "kid"]},
		{"start": "south_east", "kinds": ["adult", "kid", "kid"]},
		{"start": "ring_ne", "kinds": ["adult", "adult", "kid", "kid"]},
		{"start": "band_e", "kinds": ["adult", "adult", "kid"]},
		{"start": "queue", "kinds": ["adult", "adult"]},
		{"start": "cafe_n", "kinds": ["adult", "adult"]},
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
func _seated_groups() -> void:
	var benches := _bench_spots()
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
	var chairs := _chair_spots()
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


func _guest(kind: String, at: Vector3, yaw: float, group: int) -> Node3D:
	var is_kid := kind == "kid"
	var height := _rng.randf_range(1.05, 1.34) if is_kid else _rng.randf_range(1.58, 1.9)
	var build := _rng.randf_range(0.88, 1.18)

	var guest := AnimatableBody3D.new()
	guest.set_script(load(GUEST_SCRIPT))
	guest.transform = Transform3D(Basis(Vector3.UP, yaw), Vector3(at.x, 0.0, at.z))
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
