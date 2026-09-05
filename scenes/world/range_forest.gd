extends Node3D

## The forest on the crescent range, planted at runtime from the same seed and
## the same rules the terrain uses, so it needs no scene of its own and can be
## re-tuned without regenerating the park.
##
## Trees stand where the ground has risen into the forest band and below the
## treeline; the meadow shoulder gets sparse clumps; nothing is planted inside
## the developed envelope, which has its own props, or on anything that is not
## terrain. Two instanced meshes, conifer and broadleaf, with per-instance
## colour. Placement is a seeded jittered grid resolved onto the ground by
## raycast, which is the one runtime step: the height functions live in the
## generator and are not available here.

const Plan := preload("res://scripts/park_plan.gd")

## The near band, full meshes within `cards_from`: 110 measured as free at
## every standpoint; 160 begins to show from the head of the climb.
@export var forest_per_hectare := 110.0
@export var meadow_per_hectare := 3.0
## Beyond `far_from` the forest thickens to `far_per_hectare` and each tree
## grows toward `far_scale`, so the distant canopy closes with no gaps while
## the trees near any standpoint stay real size. Measured: 60/ha without
## shadows costs about 1.5 to 2.5ms over the floor.
@export var far_from := 450.0
@export var far_over := 400.0
## Two hundred, measured with the card tier: 175,000 trees add nothing at the
## promenade or the climb head and about 1.5s of planting at startup. At 300
## the frame cost begins to show (about a millisecond) and planting takes 2.2s.
@export var far_per_hectare := 200.0
@export var far_scale := 1.4
## Beyond `cards_from` a tree is an impostor card — two triangles, billboarded
## — instead of a fifty-triangle mesh, which is what lets the far forest be
## dense. No standpoint a player holds is nearer the range than the plateau's
## edge and the promontory, both inside this radius.
@export var cards_from := 560.0
@export var seed := 2026
@export var reach := 2200.0
## Off, and measured rather than assumed: with shadows the forest cost about
## 0.2ms per thousand trees and 45/ha ran 5ms over the vsync floor; without
## them the same forest sits on the floor. See the 2026-09-04 journal.
@export var cast_shadows := false
@export var plant_on_ready := true

var conifers: MultiMeshInstance3D
var broadleaves: MultiMeshInstance3D
var conifer_cards: MultiMeshInstance3D
var broadleaf_cards: MultiMeshInstance3D
var planted := 0
var plant_ms := 0.0


func _ready() -> void:
	conifers = _instance("conifers", _conifer_mesh())
	broadleaves = _instance("broadleaves", _broadleaf_mesh())
	conifer_cards = _instance("conifer_cards", _card_mesh(true))
	broadleaf_cards = _instance("broadleaf_cards", _card_mesh(false))
	if plant_on_ready:
		call_deferred("replant")


func _instance(nm: String, mesh: Mesh) -> MultiMeshInstance3D:
	var mmi := MultiMeshInstance3D.new()
	mmi.name = nm
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	mm.mesh = mesh
	mmi.multimesh = mm
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if cast_shadows \
		else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mmi)
	return mmi


func _material(billboard := false) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(1, 1, 1)
	m.vertex_color_use_as_albedo = true
	m.vertex_color_is_srgb = true
	m.roughness = 0.95
	if billboard:
		m.billboard_mode = BaseMaterial3D.BILLBOARD_FIXED_Y
		m.billboard_keep_scale = true
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
	return m


## An impostor: a flat silhouette of the tree, a conifer's triangle over a
## trunk or a broadleaf's blob, billboarded about its trunk. Two triangles.
func _card_mesh(conifer: bool) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var trunk := Color(0.36, 0.26, 0.18)
	var crown := Color(1, 1, 1)
	if conifer:
		_tri(st, Vector3(-0.35, 0, 0), Vector3(0.35, 0, 0), Vector3(0.35, 2.5, 0), trunk)
		_tri(st, Vector3(-0.35, 0, 0), Vector3(0.35, 2.5, 0), Vector3(-0.35, 2.5, 0), trunk)
		_tri(st, Vector3(-3.4, 2.2, 0), Vector3(3.4, 2.2, 0), Vector3(0, 12.5, 0), crown)
	else:
		_tri(st, Vector3(-0.4, 0, 0), Vector3(0.4, 0, 0), Vector3(0.4, 3.4, 0), trunk)
		_tri(st, Vector3(-0.4, 0, 0), Vector3(0.4, 3.4, 0), Vector3(-0.4, 3.4, 0), trunk)
		_tri(st, Vector3(-3.8, 3.0, 0), Vector3(3.8, 3.0, 0), Vector3(0, 10.4, 0), crown)
		_tri(st, Vector3(-3.8, 7.5, 0), Vector3(0, 3.0, 0), Vector3(3.8, 7.5, 0), crown)
	st.generate_normals()
	var mesh := st.commit()
	mesh.surface_set_material(0, _material(true))
	return mesh


## A trunk and two stacked cones: about 50 triangles.
func _conifer_mesh() -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	_cylinder(st, 0.0, 3.0, 0.28, 0.22, 6, Color(0.36, 0.26, 0.18))
	_cone(st, 2.2, 8.0, 3.4, 7, Color(1, 1, 1))
	_cone(st, 6.5, 12.5, 2.4, 7, Color(1, 1, 1))
	st.generate_normals()
	var mesh := st.commit()
	mesh.surface_set_material(0, _material())
	return mesh


## A trunk and a lumpy canopy: about 60 triangles.
func _broadleaf_mesh() -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	_cylinder(st, 0.0, 3.4, 0.34, 0.28, 6, Color(0.36, 0.26, 0.18))
	_blob(st, Vector3(0, 6.6, 0), 3.6, Color(1, 1, 1))
	st.generate_normals()
	var mesh := st.commit()
	mesh.surface_set_material(0, _material())
	return mesh


func _cylinder(st: SurfaceTool, y0: float, y1: float, r0: float, r1: float,
		segs: int, col: Color) -> void:
	for i in segs:
		var a0 := TAU * float(i) / float(segs)
		var a1 := TAU * float(i + 1) / float(segs)
		var p00 := Vector3(cos(a0) * r0, y0, sin(a0) * r0)
		var p10 := Vector3(cos(a1) * r0, y0, sin(a1) * r0)
		var p01 := Vector3(cos(a0) * r1, y1, sin(a0) * r1)
		var p11 := Vector3(cos(a1) * r1, y1, sin(a1) * r1)
		_tri(st, p00, p11, p10, col)
		_tri(st, p00, p01, p11, col)


func _cone(st: SurfaceTool, y0: float, y1: float, r: float, segs: int, col: Color) -> void:
	var apex := Vector3(0, y1, 0)
	for i in segs:
		var a0 := TAU * float(i) / float(segs)
		var a1 := TAU * float(i + 1) / float(segs)
		var p0 := Vector3(cos(a0) * r, y0, sin(a0) * r)
		var p1 := Vector3(cos(a1) * r, y0, sin(a1) * r)
		_tri(st, p0, apex, p1, col)
		_tri(st, p0, p1, Vector3(0, y0, 0), col)


func _blob(st: SurfaceTool, c: Vector3, r: float, col: Color) -> void:
	var rings := 4
	var segs := 7
	for j in rings:
		var t0 := PI * float(j) / float(rings)
		var t1 := PI * float(j + 1) / float(rings)
		for i in segs:
			var a0 := TAU * float(i) / float(segs)
			var a1 := TAU * float(i + 1) / float(segs)
			var q00 := c + Vector3(sin(t0) * cos(a0), cos(t0), sin(t0) * sin(a0)) * r
			var q10 := c + Vector3(sin(t0) * cos(a1), cos(t0), sin(t0) * sin(a1)) * r
			var q01 := c + Vector3(sin(t1) * cos(a0), cos(t1), sin(t1) * sin(a0)) * r
			var q11 := c + Vector3(sin(t1) * cos(a1), cos(t1), sin(t1) * sin(a1)) * r
			_tri(st, q00, q10, q11, col)
			_tri(st, q00, q11, q01, col)


func _tri(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, col: Color) -> void:
	for v in [a, b, c]:
		st.set_color(col)
		st.add_vertex(v)


func set_shadows(on: bool) -> void:
	cast_shadows = on
	for mmi in [conifers, broadleaves, conifer_cards, broadleaf_cards]:
		if mmi:
			mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if on \
				else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


## Plant, or plant again after a density change. Deterministic for a seed.
func replant() -> void:
	var t0 := Time.get_ticks_usec()
	var space := get_world_3d().direct_space_state
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var road: Array[Vector3] = Plan.approach_road_points()
	# The highway (02B) as a coarse cell mask, since a distance test against
	# its three hundred segments for every candidate would be most of the
	# planting time: 8m cells, the three-by-three round every five-metre
	# sample, about twelve metres of verge either side.
	var road_mask := {}
	var highway: Array[Vector2] = Plan.highway_path()
	for i in highway.size() - 1:
		var a: Vector2 = highway[i]
		var b: Vector2 = highway[i + 1]
		var steps := maxi(1, ceili(a.distance_to(b) / 5.0))
		for k in range(steps + 1):
			var q := a.lerp(b, float(k) / float(steps))
			var cell := Vector2i(floori(q.x / 8.0), floori(q.y / 8.0))
			for dx in range(-1, 2):
				for dz in range(-1, 2):
					road_mask[cell + Vector2i(dx, dz)] = true
	var forest_t: Array[Transform3D] = []
	var forest_c: Array[Color] = []
	var leaf_t: Array[Transform3D] = []
	var leaf_c: Array[Color] = []
	var card_con_t: Array[Transform3D] = []
	var card_con_c: Array[Color] = []
	var card_leaf_t: Array[Transform3D] = []
	var card_leaf_c: Array[Color] = []
	var centre: Vector2 = Plan.RIM_RANGE_CENTRE
	var top_density := maxf(forest_per_hectare, far_per_hectare)
	var step := sqrt(10000.0 / maxf(top_density, 0.1))
	var keep_meadow := meadow_per_hectare / maxf(top_density, 0.1)
	var forest_col := Color(0.19, 0.33, 0.18)
	var meadow_col := Color(0.30, 0.42, 0.26)
	var x0 := centre.x - reach
	var z := centre.y - reach
	while z <= centre.y + reach:
		var x := x0
		while x <= centre.x + reach:
			var px := x + rng.randf_range(-0.45, 0.45) * step
			var pz := z + rng.randf_range(-0.45, 0.45) * step
			x += step
			var p := Vector2(px, pz)
			if px > Plan.REBUILD_FOOTPRINT_MIN_X and px < Plan.REBUILD_FOOTPRINT_MAX_X \
					and pz > Plan.REBUILD_FOOTPRINT_MIN_Z and pz < Plan.REBUILD_FOOTPRINT_MAX_Z:
				continue
			if px < Plan.shore_x(pz) + 4.0:
				continue
			var v := p - centre
			var theta := rad_to_deg(atan2(v.y, v.x))
			var far := clampf((v.length() - far_from) / far_over, 0.0, 1.0)
			var local_density := lerpf(forest_per_hectare, far_per_hectare, far)
			if rng.randf() > local_density / top_density:
				continue
			if Plan.range_weight(theta) <= 0.05 and px > Plan.REBUILD_WORLD_LAND_FROM_X:
				continue
			var near_road := false
			for i in road.size() - 1:
				var a := Vector2(road[i].x, road[i].z)
				var b := Vector2(road[i + 1].x, road[i + 1].z)
				if p.distance_to(Geometry2D.get_closest_point_to_segment(p, a, b)) < 9.0:
					near_road = true
					break
			if near_road:
				continue
			if road_mask.has(Vector2i(floori(px / 8.0), floori(pz / 8.0))):
				continue
			var cleared := false
			for clearing in Plan.HIGHWAY_CLEARINGS:
				if p.distance_to(Vector2(clearing[0])) < float(clearing[1]):
					cleared = true
					break
			if cleared:
				continue
			var query := PhysicsRayQueryParameters3D.create(
				Vector3(px, 700.0, pz), Vector3(px, -40.0, pz), 1)
			var hit := space.intersect_ray(query)
			if hit.is_empty():
				continue
			var body: Object = hit["collider"]
			if not (body is Node) or not String((body as Node).name).begins_with("terrain_"):
				continue
			var y: float = hit["position"].y
			if y >= Plan.RIM_RANGE_TREELINE_Y:
				continue
			var plateau := String((body as Node).name).find("highland") >= 0
			var rise := y - (12.0 if plateau else 0.0)
			var in_forest := rise >= Plan.RIM_RANGE_FOREST_RISE
			if not in_forest and rng.randf() > keep_meadow:
				continue
			var conifer := rng.randf() < (0.62 if in_forest else 0.35)
			var scale := rng.randf_range(0.8, 1.25) * (1.0 if in_forest else 0.85) \
				* lerpf(1.0, far_scale, far)
			var yaw := rng.randf_range(0.0, TAU)
			var xf := Transform3D(Basis(Vector3.UP, yaw).scaled(Vector3(scale, scale, scale)),
				Vector3(px, y - 0.3, pz))
			var base := forest_col if in_forest else meadow_col
			var tint := rng.randf_range(0.82, 1.12)
			var col := Color(base.r * tint, base.g * tint, base.b * tint)
			var card := v.length() > cards_from
			if card and conifer:
				card_con_t.append(xf)
				card_con_c.append(col)
			elif card:
				card_leaf_t.append(xf)
				card_leaf_c.append(col)
			elif conifer:
				forest_t.append(xf)
				forest_c.append(col)
			else:
				leaf_t.append(xf)
				leaf_c.append(col)
		z += step
	_fill(conifers.multimesh, forest_t, forest_c)
	_fill(broadleaves.multimesh, leaf_t, leaf_c)
	_fill(conifer_cards.multimesh, card_con_t, card_con_c)
	_fill(broadleaf_cards.multimesh, card_leaf_t, card_leaf_c)
	planted = forest_t.size() + leaf_t.size() + card_con_t.size() + card_leaf_t.size()
	plant_ms = float(Time.get_ticks_usec() - t0) / 1000.0


func _fill(mm: MultiMesh, xfs: Array[Transform3D], cols: Array[Color]) -> void:
	mm.instance_count = 0
	mm.instance_count = xfs.size()
	for i in xfs.size():
		mm.set_instance_transform(i, xfs[i])
		mm.set_instance_color(i, cols[i])
