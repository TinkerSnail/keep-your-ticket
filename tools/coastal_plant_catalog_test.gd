extends Node

## Focused source acceptance for the reusable broadleaf, Cordyline, grass,
## flowering-perennial, hanging-planter and palm-footing families in the visual
## prop catalog.

const VARIANTS := [
	{"path": "res://scenes/world/coastal_banana_tree_va.tscn", "index": 0,
		"leaves": 7, "name": "vA"},
	{"path": "res://scenes/world/coastal_banana_tree_vb.tscn", "index": 1,
		"leaves": 9, "name": "vB"},
	{"path": "res://scenes/world/coastal_banana_tree_vc.tscn", "index": 2,
		"leaves": 10, "name": "vC"},
]

const CABBAGE_VARIANTS := [
	{"path": "res://scenes/world/red_sensation_cabbage_tree_va.tscn", "index": 0,
		"leaves": 16, "name": "vA"},
	{"path": "res://scenes/world/red_sensation_cabbage_tree_vb.tscn", "index": 1,
		"leaves": 22, "name": "vB"},
	{"path": "res://scenes/world/red_sensation_cabbage_tree_vc.tscn", "index": 2,
		"leaves": 26, "name": "vC"},
]

const PURPLE_HEART_VARIANTS := [
	{"path": "res://scenes/world/purple_heart_row_va.tscn", "sprigs": 14,
		"min_flowers": 4, "name": "row vA"},
	{"path": "res://scenes/world/purple_heart_row_vb.tscn", "sprigs": 24,
		"min_flowers": 8, "name": "row vB"},
	{"path": "res://scenes/world/purple_heart_cluster.tscn", "sprigs": 14,
		"min_flowers": 6, "name": "cluster"},
]

const HAKONE_VARIANTS := [
	{"path": "res://scenes/world/hakone_grass_tuft_va.tscn", "index": 0,
		"blades": 54, "name": "clump vA"},
	{"path": "res://scenes/world/hakone_grass_tuft_vb.tscn", "index": 1,
		"blades": 72, "name": "clump vB"},
]

const HAKONE_COMPOSITIONS := [
	{"path": "res://scenes/world/hakone_grass_row.tscn", "clumps": 5,
		"name": "row", "ring": false},
	{"path": "res://scenes/world/hakone_grass_ring.tscn", "clumps": 10,
		"name": "ring", "ring": true},
]

const DELPHINIUM_VARIANTS := [
	{"path": "res://scenes/world/delphinium_clump_va.tscn", "spires": 7,
		"colors": 1, "name": "blue clump"},
	{"path": "res://scenes/world/delphinium_clump_vb.tscn", "spires": 11,
		"colors": 1, "name": "purple clump"},
	{"path": "res://scenes/world/delphinium_clump_white.tscn", "spires": 8,
		"colors": 1, "name": "white clump"},
	{"path": "res://scenes/world/delphinium_border.tscn", "spires": 16,
		"colors": 4, "name": "mixed border"},
]

const HANGING_PLANTERS := [
	{"path": "res://scenes/world/hanging_planter_flower_basket.tscn",
		"hardware": 7, "planting": 5, "vessel": "basket", "suspensions": 3,
		"landings": {
			"chain_front": Vector3(0.0, -1.25, 0.55),
			"chain_back_left": Vector3(-0.476314, -1.25, -0.275),
			"chain_back_right": Vector3(0.476314, -1.25, -0.275),
		},
		"name": "mixed-flower coir basket"},
	{"path": "res://scenes/world/hanging_planter_fern_bowl.tscn",
		"hardware": 7, "planting": 25, "vessel": "bowl", "suspensions": 3,
		"landings": {
			"chain_front": Vector3(0.0, -1.18, 0.5),
			"chain_back_left": Vector3(-0.433013, -1.18, -0.25),
			"chain_back_right": Vector3(0.433013, -1.18, -0.25),
		},
		"name": "fern bowl"},
	{"path": "res://scenes/world/hanging_planter_purple_heart_box.tscn",
		"hardware": 7, "planting": 9, "vessel": "box", "suspensions": 4,
		"landings": {
			"cord_nw": Vector3(-0.43, -1.2, -0.43),
			"cord_ne": Vector3(0.43, -1.2, -0.43),
			"cord_se": Vector3(0.43, -1.2, 0.43),
			"cord_sw": Vector3(-0.43, -1.2, 0.43),
		},
		"name": "Purple Heart cedar box"},
	{"path": "res://scenes/world/hanging_planter_petunia_cloud.tscn",
		"hardware": 7, "planting": 53, "vessel": "bowl", "suspensions": 3,
		"landings": {
			"chain_front": Vector3(0.0, -1.15, 0.58),
			"chain_back_left": Vector3(-0.502295, -1.15, -0.29),
			"chain_back_right": Vector3(0.502295, -1.15, -0.29),
		},
		"name": "overflowing petunia cloud"},
]


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	for specification in VARIANTS:
		var packed := load(specification["path"]) as PackedScene
		var plant := packed.instantiate() as Node3D if packed != null else null
		if plant == null:
			_fail("could not instantiate banana tree %s" % specification["name"])
			return
		add_child(plant)
		for _frame in 4:
			await get_tree().process_frame
		if int(plant.get("catalog_variant")) != specification["index"]:
			_fail("banana tree %s lost its catalog variant" % specification["name"])
			return
		var courses := plant.get_node_or_null("leaf_courses")
		var leaves := plant.get_node_or_null("derived_leaves")
		var pseudostem := plant.get_node_or_null("pseudostem")
		if courses == null or courses.get_child_count() != 10:
			_fail("banana tree %s does not preserve ten editable source courses" %
				specification["name"])
			return
		if leaves == null or leaves.get_child_count() != specification["leaves"]:
			_fail("banana tree %s expected %d derived leaves, found %d" % [
				specification["name"], specification["leaves"],
				leaves.get_child_count() if leaves != null else 0])
			return
		if pseudostem == null or pseudostem.get_child_count() != 3:
			_fail("banana tree %s is missing its layered pseudostem" %
				specification["name"])
			return
		for leaf in leaves.get_children():
			var mesh := (leaf as MeshInstance3D).mesh as ArrayMesh
			if mesh == null or mesh.get_surface_count() != 2:
				_fail("banana tree %s/%s is missing its cupped blade or midrib" % [
					specification["name"], leaf.name])
				return
			var blade_vertices := mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX] \
				as PackedVector3Array
			if blade_vertices.size() < 360:
				_fail("banana tree %s/%s is not a fully surfaced broad blade" % [
					specification["name"], leaf.name])
				return
		plant.queue_free()
		await get_tree().process_frame

	for specification in CABBAGE_VARIANTS:
		var packed := load(specification["path"]) as PackedScene
		var plant := packed.instantiate() as Node3D if packed != null else null
		if plant == null:
			_fail("could not instantiate Red Sensation cabbage tree %s" %
				specification["name"])
			return
		add_child(plant)
		for _frame in 4:
			await get_tree().process_frame
		if int(plant.get("catalog_variant")) != specification["index"]:
			_fail("cabbage tree %s lost its catalog variant" % specification["name"])
			return
		var courses := plant.get_node_or_null("leaf_courses")
		var leaves := plant.get_node_or_null("derived_leaves")
		if courses == null or courses.get_child_count() != 26:
			_fail("cabbage tree %s does not preserve 26 editable source courses" %
				specification["name"])
			return
		if leaves == null or leaves.get_child_count() != specification["leaves"]:
			_fail("cabbage tree %s expected %d derived leaves, found %d" % [
				specification["name"], specification["leaves"],
				leaves.get_child_count() if leaves != null else 0])
			return
		if plant.get_node_or_null("crown_base") == null:
			_fail("cabbage tree %s is missing its compact crown base" %
				specification["name"])
			return
		for course in courses.get_children():
			if not course is Path3D or (course as Path3D).curve == null:
				_fail("cabbage tree %s has a non-editable leaf course" %
					specification["name"])
				return
		for leaf in leaves.get_children():
			var mesh := (leaf as MeshInstance3D).mesh as ArrayMesh
			if mesh == null or mesh.get_surface_count() != 2:
				_fail("cabbage tree %s/%s is missing its folded blade or midrib" % [
					specification["name"], leaf.name])
				return
			var blade_vertices := mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX] \
				as PackedVector3Array
			if blade_vertices.size() < 320:
				_fail("cabbage tree %s/%s is not a fully surfaced sword blade" % [
					specification["name"], leaf.name])
				return
		plant.queue_free()
		await get_tree().process_frame

	for specification in PURPLE_HEART_VARIANTS:
		var packed := load(specification["path"]) as PackedScene
		var composition := packed.instantiate() as Node3D if packed != null else null
		if composition == null:
			_fail("could not instantiate Purple Heart %s" % specification["name"])
			return
		add_child(composition)
		for _frame in 5:
			await get_tree().process_frame
		var sprigs := composition.get_node_or_null("sprigs")
		if sprigs == null or sprigs.get_child_count() != specification["sprigs"]:
			_fail("Purple Heart %s expected %d selectable sprigs, found %d" % [
				specification["name"], specification["sprigs"],
				sprigs.get_child_count() if sprigs != null else 0])
			return
		var flowered_count := 0
		for sprig in sprigs.get_children():
			var course := sprig.get_node_or_null("stem_course") as Path3D
			var stems := sprig.get_node_or_null("derived_stem")
			var leaves := sprig.get_node_or_null("derived_leaves")
			var flowers := sprig.get_node_or_null("derived_flowers")
			if course == null or course.curve == null:
				_fail("Purple Heart %s/%s lost its editable stem course" % [
					specification["name"], sprig.name])
				return
			if stems == null or stems.get_child_count() != 8:
				_fail("Purple Heart %s/%s is missing its segmented stem" % [
					specification["name"], sprig.name])
				return
			var expected_leaves := int(sprig.get("leaf_pair_count")) * 2
			if leaves == null or leaves.get_child_count() != expected_leaves:
				_fail("Purple Heart %s/%s expected %d paired leaves" % [
					specification["name"], sprig.name, expected_leaves])
				return
			for leaf in leaves.get_children():
				var mesh := (leaf as MeshInstance3D).mesh as ArrayMesh
				if mesh == null or mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX].size() < 40:
					_fail("Purple Heart %s/%s has an incomplete lance leaf" % [
						specification["name"], sprig.name])
					return
			if bool(sprig.get("flowered")):
				flowered_count += 1
				if flowers == null or flowers.get_child_count() != 4:
					_fail("Purple Heart %s/%s lost its three-petal flower" % [
						specification["name"], sprig.name])
					return
		if flowered_count < specification["min_flowers"]:
			_fail("Purple Heart %s has too few flowering sprigs" % specification["name"])
			return
		composition.queue_free()
		await get_tree().process_frame

	for specification in HAKONE_VARIANTS:
		var packed := load(specification["path"]) as PackedScene
		var grass := packed.instantiate() as Node3D if packed != null else null
		if grass == null:
			_fail("could not instantiate Hakone grass %s" % specification["name"])
			return
		add_child(grass)
		for _frame in 5:
			await get_tree().process_frame
		if int(grass.get("catalog_variant")) != specification["index"]:
			_fail("Hakone grass %s lost its catalog variant" % specification["name"])
			return
		var courses := grass.get_node_or_null("blade_courses")
		var blades := grass.get_node_or_null("derived_blades")
		if courses == null or courses.get_child_count() != 24:
			_fail("Hakone grass %s does not preserve 24 editable fountain courses" %
				specification["name"])
			return
		for course in courses.get_children():
			if not course is Path3D or (course as Path3D).curve == null:
				_fail("Hakone grass %s has a non-editable blade course" %
					specification["name"])
				return
		if blades == null or blades.get_child_count() != specification["blades"]:
			_fail("Hakone grass %s expected %d striped blades, found %d" % [
				specification["name"], specification["blades"],
				blades.get_child_count() if blades != null else 0])
			return
		for blade in blades.get_children():
			var mesh := (blade as MeshInstance3D).mesh as ArrayMesh
			if mesh == null or mesh.get_surface_count() != 2:
				_fail("Hakone grass %s/%s lost its green edges or lemon stripe" % [
					specification["name"], blade.name])
				return
			# Nine stations a blade since 2026-09-18, Christina's approval: two
			# edge strips are 96 vertices and the lemon strip 48. The floor was
			# 140 and 70, which held the blade at thirteen.
			if mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX].size() < 96 \
					or mesh.surface_get_arrays(1)[Mesh.ARRAY_VERTEX].size() < 48:
				_fail("Hakone grass %s/%s is not a fully surfaced fine blade" % [
					specification["name"], blade.name])
				return
		var lemon := grass.get("lemon_material") as StandardMaterial3D
		var young_lemon := grass.get("young_lemon_material") as StandardMaterial3D
		if lemon == null or young_lemon == null or lemon.albedo_color.g < 0.78 \
				or lemon.albedo_color.r < 0.58 or young_lemon.albedo_color.g < 0.88:
			_fail("Hakone grass %s lost its bright yellow-green identity" %
				specification["name"])
			return
		grass.queue_free()
		await get_tree().process_frame

	for specification in HAKONE_COMPOSITIONS:
		var packed := load(specification["path"]) as PackedScene
		var composition := packed.instantiate() as Node3D if packed != null else null
		if composition == null:
			_fail("could not instantiate Hakone grass %s" % specification["name"])
			return
		add_child(composition)
		for _frame in 5:
			await get_tree().process_frame
		var clumps := composition.get_node_or_null("clumps")
		if clumps == null or clumps.get_child_count() != specification["clumps"]:
			_fail("Hakone grass %s expected %d selectable clumps" % [
				specification["name"], specification["clumps"]])
			return
		if specification["ring"]:
			for clump in clumps.get_children():
				var radius := Vector2(clump.position.x, clump.position.z).length()
				if radius < 0.95:
					_fail("Hakone grass ring no longer preserves its open center")
					return
		composition.queue_free()
		await get_tree().process_frame

	for specification in DELPHINIUM_VARIANTS:
		var packed := load(specification["path"]) as PackedScene
		var composition := packed.instantiate() as Node3D if packed != null else null
		if composition == null:
			_fail("could not instantiate delphinium %s" % specification["name"])
			return
		add_child(composition)
		for _frame in 5:
			await get_tree().process_frame
		var spires := composition.get_node_or_null("spires")
		if spires == null or spires.get_child_count() != specification["spires"]:
			_fail("delphinium %s expected %d selectable spires" % [
				specification["name"], specification["spires"]])
			return
		var colors: Dictionary = {}
		for spire in spires.get_children():
			var course := spire.get_node_or_null("stem_course") as Path3D
			var stems := spire.get_node_or_null("derived_stem")
			var leaves := spire.get_node_or_null("derived_leaves")
			var flowers := spire.get_node_or_null("derived_flowers")
			if course == null or course.curve == null:
				_fail("delphinium %s/%s lost its editable flower-spike course" % [
					specification["name"], spire.name])
				return
			var expected_stem_parts := 12 + int(spire.get("bloom_count"))
			if stems == null or stems.get_child_count() != expected_stem_parts:
				_fail("delphinium %s/%s is missing stem or pedicel construction" % [
					specification["name"], spire.name])
				return
			if leaves == null or leaves.get_child_count() != 2:
				_fail("delphinium %s/%s lost its layered palmate foliage" % [
					specification["name"], spire.name])
				return
			for leaf_mesh in leaves.get_children():
				var mesh := (leaf_mesh as MeshInstance3D).mesh as ArrayMesh
				if mesh == null or mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX].size() < 60:
					_fail("delphinium %s/%s has incomplete palmate leaves" % [
						specification["name"], spire.name])
					return
			if flowers == null or flowers.get_child_count() != 4:
				_fail("delphinium %s/%s lost petals, young flowers or buds" % [
					specification["name"], spire.name])
				return
			for flower_mesh in flowers.get_children():
				var mesh := (flower_mesh as MeshInstance3D).mesh as ArrayMesh
				if mesh == null or mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX].size() < 48:
					_fail("delphinium %s/%s has an incomplete flower raceme" % [
						specification["name"], spire.name])
					return
			var leaf_material := spire.get("leaf_material") as StandardMaterial3D
			if leaf_material == null or leaf_material.albedo_color.g > 0.4:
				_fail("delphinium %s/%s lost its dark contrast foliage" % [
					specification["name"], spire.name])
				return
			var petal_material := spire.get("petal_material") as StandardMaterial3D
			if petal_material == null:
				_fail("delphinium %s/%s has no bloom color" % [
					specification["name"], spire.name])
				return
			colors[petal_material.albedo_color.to_html(false)] = true
		if colors.size() < specification["colors"]:
			_fail("delphinium %s expected %d distinct bloom colors" % [
				specification["name"], specification["colors"]])
			return
		composition.queue_free()
		await get_tree().process_frame

	for specification in HANGING_PLANTERS:
		var packed := load(specification["path"]) as PackedScene
		var planter := packed.instantiate() as Node3D if packed != null else null
		if planter == null:
			_fail("could not instantiate hanging planter %s" % specification["name"])
			return
		add_child(planter)
		for _frame in 5:
			await get_tree().process_frame
		var hardware := planter.get_node_or_null("hardware")
		var planting := planter.get_node_or_null("planting")
		var attachment := planter.get_node_or_null("hardware/attachment_eye") as Node3D
		if hardware == null or hardware.get_child_count() != specification["hardware"]:
			_fail("hanging planter %s lost its selectable suspension hardware" %
				specification["name"])
			return
		if attachment == null or attachment.position.y >= 0.0:
			_fail("hanging planter %s lost its ceiling-origin attachment" %
				specification["name"])
			return
		var join_name := "cord_join" if specification["suspensions"] == 4 \
			else "chain_join"
		var join := planter.get_node_or_null("hardware/" + join_name) as Node3D
		var shank := planter.get_node_or_null("hardware/eye_shank") as Node3D
		if join == null or shank == null \
				or absf(shank.position.y - join.position.y) > 0.07:
			_fail("hanging planter %s has a disconnected upper junction" %
				specification["name"])
			return
		var suspension_count := 0
		for piece in hardware.get_children():
			var piece_name := String(piece.name)
			if not piece_name.begins_with("chain_") \
					and not piece_name.begins_with("cord_"):
				continue
			if piece_name.ends_with("join"):
				continue
			var suspension := piece as MeshInstance3D
			var cylinder := suspension.mesh as CylinderMesh if suspension != null else null
			if cylinder == null:
				_fail("hanging planter %s has non-cylindrical suspension hardware" %
					specification["name"])
				return
			var half_axis := suspension.transform.basis.y * cylinder.height * 0.5
			var endpoint_a := suspension.position + half_axis
			var endpoint_b := suspension.position - half_axis
			var join_distance := minf(endpoint_a.distance_to(join.position),
					endpoint_b.distance_to(join.position))
			if join_distance > 0.065:
				print("SUSPENSION_DIAGNOSTIC %s/%s centre=%s axis=%s endpoints=%s,%s join=%s distance=%.6f" % [
					specification["name"], piece_name, suspension.position,
					suspension.transform.basis.y, endpoint_a, endpoint_b,
					join.position, join_distance])
				_fail("hanging planter %s has a suspension that misses its junction" %
					specification["name"])
				return
			var landing: Vector3 = specification["landings"].get(piece_name,
					Vector3(INF, INF, INF))
			if not landing.is_finite() or minf(endpoint_a.distance_to(landing),
					endpoint_b.distance_to(landing)) > 0.065:
				_fail("hanging planter %s/%s misses its vessel landing" % [
					specification["name"], piece_name])
				return
			suspension_count += 1
		if suspension_count != specification["suspensions"]:
			_fail("hanging planter %s expected %d complete suspensions" % [
				specification["name"], specification["suspensions"]])
			return
		if planter.get_node_or_null(specification["vessel"]) == null:
			_fail("hanging planter %s lost its distinct vessel" % specification["name"])
			return
		if String(specification["path"]).ends_with("hanging_planter_flower_basket.tscn"):
			var coir_basket := planter.get_node_or_null("basket") as MeshInstance3D
			var coir_material := coir_basket.material_override as StandardMaterial3D \
					if coir_basket != null else null
			if coir_material == null or coir_material.albedo_color.r > 0.24 \
					or coir_material.albedo_color.g > 0.13:
				_fail("mixed-flower coir basket lost its deep cocoa-brown finish")
				return
		if planting == null or planting.get_child_count() != specification["planting"]:
			_fail("hanging planter %s expected %d selectable planting pockets" % [
				specification["name"], specification["planting"]])
			return
		if String(specification["path"]).ends_with("hanging_planter_fern_bowl.tscn"):
			var crown_fans := 0
			var shoulder_fans := 0
			var trailing_fans := 0
			var editable_frond_courses := 0
			for child in planting.get_children():
				var fern := child as Node3D
				var courses := fern.get_node_or_null("frond_courses") if fern != null else null
				if courses == null or courses.get_child_count() != 7:
					_fail("mature fern basket/%s lost its seven editable frond courses" % child.name)
					return
				editable_frond_courses += courses.get_child_count()
				var child_name := String(child.name)
				var frond_reach := fern.transform.basis.z.normalized()
				if child_name.begins_with("crown_") and frond_reach.y >= 0.4:
					crown_fans += 1
				elif child_name.begins_with("shoulder_") and absf(frond_reach.y) <= 0.15:
					shoulder_fans += 1
				elif child_name.begins_with("trail_") and frond_reach.y <= -0.5:
					trailing_fans += 1
			if crown_fans != 5 or shoulder_fans != 8 or trailing_fans != 12 \
					or editable_frond_courses != 175:
				_fail("mature fern basket lost its upright, arching and trailing density tiers")
				return
		if String(specification["path"]).ends_with("hanging_planter_petunia_cloud.tscn"):
			var bloom_count := 0
			var high_centre_count := 0
			var overflowing_rim_count := 0
			var highest := -INF
			var lowest := INF
			for child in planting.get_children():
				if not String(child.name).begins_with("bloom_"):
					continue
				bloom_count += 1
				var bloom_position := (child as Node3D).position
				var radius := Vector2(bloom_position.x, bloom_position.z).length()
				highest = maxf(highest, bloom_position.y)
				lowest = minf(lowest, bloom_position.y)
				if bloom_position.y >= -0.58 and radius <= 0.24:
					high_centre_count += 1
				if bloom_position.y <= -0.9 and radius >= 0.55:
					overflowing_rim_count += 1
			var foliage_core := planting.get_node_or_null("foliage_core")
			if bloom_count != 48 or high_centre_count < 9 \
					or overflowing_rim_count < 8 or highest - lowest < 0.48:
				_fail("overflowing petunia basket lost its high-centre, rounded-middle and lower-rim scoop")
				return
			if foliage_core == null or float(foliage_core.get("mound_height")) < 0.45:
				_fail("overflowing petunia basket lost the foliage volume beneath its flower scoop")
				return
		if specification["suspensions"] == 4:
			for trail in planting.get_children():
				if not String(trail.name).begins_with("trail_"):
					continue
				if maxf(absf(trail.position.x), absf(trail.position.z)) < 0.49:
					_fail("Purple Heart trail %s still begins inside the cedar wall" %
						trail.name)
					return
		planter.queue_free()
		await get_tree().process_frame

	var single_bracket := load(
		"res://scenes/world/hanging_planter_single_bracket.tscn").instantiate() as Node3D
	add_child(single_bracket)
	for _frame in 5:
		await get_tree().process_frame
	var bracket_hardware := single_bracket.get_node_or_null("bracket")
	if bracket_hardware == null or bracket_hardware.get_child_count() != 6 \
			or single_bracket.get_node_or_null("basket/planting") == null:
		_fail("single-bracket hanging basket lost its selectable mount or planting")
		return
	single_bracket.queue_free()
	await get_tree().process_frame

	var twin_lamp := load(
		"res://scenes/world/hanging_planter_twin_lamp.tscn").instantiate() as Node3D
	add_child(twin_lamp)
	for _frame in 5:
		await get_tree().process_frame
	if twin_lamp.get_node_or_null("lamp") == null \
			or twin_lamp.get_node_or_null("crossarm") == null \
			or twin_lamp.get_node_or_null("left_basket/planting") == null \
			or twin_lamp.get_node_or_null("right_basket/planting") == null:
		_fail("twin-basket heritage lamp lost a selectable composition layer")
		return
	twin_lamp.queue_free()
	await get_tree().process_frame

	var ground_row := load(
		"res://scenes/world/petunia_ground_row.tscn").instantiate() as Node3D
	add_child(ground_row)
	for _frame in 5:
		await get_tree().process_frame
	var row_foliage := ground_row.get_node_or_null("foliage")
	var row_blooms := ground_row.get_node_or_null("blooms")
	if row_foliage == null or row_foliage.get_child_count() != 8 \
			or row_blooms == null or row_blooms.get_child_count() != 18:
		_fail("furniture-free petunia row lost its selectable planting rhythm")
		return
	var bright_heaps := 0
	for mound in row_foliage.get_children():
		if float(mound.get("mound_height")) < 0.6 or mound.scale.y < 0.95:
			_fail("ground-row foliage %s is flattened instead of heaped" % mound.name)
			return
		var mound_color: Color = mound.get("leaf_color")
		if mound_color.g >= 0.75 and mound_color.r >= 0.5:
			bright_heaps += 1
	if bright_heaps < 7:
		_fail("ground row needs at least seven bright chartreuse heaps")
		return
	for bloom in row_blooms.get_children():
		if bloom.position.y < 0.5:
			_fail("ground-row bloom %s is buried below the heap top" % bloom.name)
			return
	for forbidden_name in ["lamp", "basket", "hardware", "bracket"]:
		if ground_row.find_child("*%s*" % forbidden_name, true, false) != null:
			_fail("furniture-free petunia row still contains %s geometry" %
				forbidden_name)
			return
	ground_row.queue_free()
	await get_tree().process_frame

	var lamp_row := load(
		"res://scenes/world/petunia_lamp_row.tscn").instantiate() as Node3D
	add_child(lamp_row)
	for _frame in 5:
		await get_tree().process_frame
	var row_lamps := lamp_row.get_node_or_null("lamps")
	var row_baskets := lamp_row.get_node_or_null("hanging_baskets")
	if lamp_row.get_node_or_null("ground_row") == null \
			or row_lamps == null or row_lamps.get_child_count() != 3 \
			or row_baskets == null or row_baskets.get_child_count() != 3:
		_fail("petunia lamp mini-row lost its three-lamp, three-basket rhythm")
		return
	lamp_row.queue_free()
	await get_tree().process_frame

	for path in ["res://scenes/world/coastal_palm_ground_base.tscn",
			"res://scenes/world/coastal_palm_boardwalk_base.tscn"]:
		var packed := load(path) as PackedScene
		var footing := packed.instantiate() as Node3D if packed != null else null
		if footing == null:
			_fail("could not instantiate catalog footing %s" % path)
			return
		add_child(footing)
		for _frame in 4:
			await get_tree().process_frame
		var fern_group_name := "fern_ring" \
			if path.ends_with("boardwalk_base.tscn") else "fern_pockets"
		if footing.get_node_or_null(fern_group_name) == null \
				or footing.get_node_or_null("flowers") == null \
				or footing.get_node_or_null("border_rosettes") == null:
			_fail("%s is missing a layer required by its catalog identity" % path)
			return
		footing.queue_free()
		await get_tree().process_frame

	var arrival_rings_packed := load(
		"res://scenes/world/coastal_palm_arrival_rings.tscn") as PackedScene
	var arrival_rings := arrival_rings_packed.instantiate() as Node3D \
		if arrival_rings_packed != null else null
	if arrival_rings == null:
		_fail("could not instantiate the arrival-palm planting rings")
		return
	add_child(arrival_rings)
	for _frame in 5:
		await get_tree().process_frame
	var arrival_hakone := arrival_rings.get_node_or_null(
		"japanese_forest_grass_inner_ring/clumps")
	var arrival_purple := arrival_rings.get_node_or_null(
		"purple_heart_outer_ring")
	if arrival_hakone == null or arrival_hakone.get_child_count() != 10 \
			or arrival_purple == null or arrival_purple.get_child_count() != 36:
		_fail("arrival-palm layer lost its ten Hakone clumps or 36 Purple Heart sprigs")
		return
	if (arrival_purple as Node3D).scale.x > 0.71 \
			or float(arrival_rings.get_meta("center_height_scale", 0.0)) < 3.1 \
			or float(arrival_rings.get_meta("fern_scale", 0.0)) < 1.99:
		_fail("arrival-palm layer lost its tucked Purple Heart, raised-center or doubled-fern relationship")
		return
	var flowered_purple := 0
	for sprig in arrival_purple.get_children():
		if bool(sprig.get("flowered")):
			flowered_purple += 1
		if sprig.get_node_or_null("stem_course") == null \
				or sprig.get_node_or_null("derived_leaves") == null:
			_fail("arrival Purple Heart ring lost an editable sprig")
			return
	if flowered_purple < 5:
		_fail("arrival Purple Heart ring has lost its sparse pink flowers")
		return
	arrival_rings.queue_free()
	await get_tree().process_frame

	var rosette_packed := load(
		"res://scenes/world/coastal_palm_border_rosette.tscn") as PackedScene
	var rosette := rosette_packed.instantiate() as Node3D \
		if rosette_packed != null else null
	if rosette == null:
		_fail("could not instantiate the shared flower rosette")
		return
	add_child(rosette)
	var outer_leaf_count := 0
	var inner_leaf_count := 0
	for child in rosette.get_children():
		var leaf := child as MeshInstance3D
		if leaf == null or not String(child.name).contains("leaf_"):
			continue
		if leaf.mesh is BoxMesh:
			_fail("%s still uses the retired rectangular flower leaf" % child.name)
			return
		if not leaf.mesh is SphereMesh or leaf.scale.z > 0.3:
			_fail("%s is not a flattened tapered lance leaf" % child.name)
			return
		if String(child.name).begins_with("inner_"):
			inner_leaf_count += 1
		else:
			outer_leaf_count += 1
	if outer_leaf_count != 6 or inner_leaf_count != 3:
		_fail("flower rosette expected six outer and three cupped inner leaves")
		return
	rosette.queue_free()
	await get_tree().process_frame

	print("PASS: banana, Red Sensation, Purple Heart, lemon-zest Hakone grass and blue/purple/white/mixed delphinium catalog families preserve editor-owned courses and surfaced foliage; all four hanging planters keep ceiling-origin attachment hardware, distinct vessels and selectable recipes, including the flower basket's deep cocoa coir and the fern bowl's 175-course upright, arching and trailing mature cluster; single-bracket, twin-lamp and three-lamp compositions preserve their basket layers; the furniture-free petunia row contains only its soil and planting recipe; Hakone rows and rings keep selectable clumps, the arrival-palm layer combines ten Hakone clumps with 36 tucked Purple Heart sprigs and an authored raised-center relationship, both palm footing types remain reusable, and the shared flower rosette uses layered lance leaves rather than blocks")
	get_tree().quit()


func _fail(message: String) -> void:
	push_error("coastal_plant_catalog_test: " + message)
	get_tree().quit(1)
