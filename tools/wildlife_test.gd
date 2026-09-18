extends Node

## Focused structural and behavior check for the persistent bird layer. It
## verifies authored species/placements, purpose-built gull meshes, articulated
## bills, colony roost/feeding routes and the shared flush response without
## interpreting a photograph or turning wildlife into scored state.

const EXPECTED_GULLS := 23
const EXPECTED_PIGEONS := 6
const EXPECTED_JUVENILE_GULLS := 4
const EXPECTED_COLONY_GULLS := 18
const EXPECTED_ROOSTS := 9
const EXPECTED_FORAGING_SITES := 6


func _ready() -> void:
	var scene := load("res://scenes/wildlife/wildlife.tscn") as PackedScene
	if scene == null:
		_fail("wildlife scene did not load")
		return
	var flock := scene.instantiate()
	add_child(flock)
	await get_tree().process_frame

	var birds := get_tree().get_nodes_in_group("wildlife")
	var gulls := get_tree().get_nodes_in_group("gull")
	var pigeons := get_tree().get_nodes_in_group("pigeon")
	var failures: Array[String] = []
	_expect(gulls.size() == EXPECTED_GULLS,
		"expected %d gulls, found %d" % [EXPECTED_GULLS, gulls.size()], failures)
	_expect(pigeons.size() == EXPECTED_PIGEONS,
		"expected %d pigeons, found %d" % [EXPECTED_PIGEONS, pigeons.size()], failures)
	_expect(birds.size() == EXPECTED_GULLS + EXPECTED_PIGEONS,
		"wildlife group does not match species totals", failures)

	var juvenile_count := 0
	var adult_white_tail_count := 0
	var adult_dark_tail_count := 0
	var airborne_count := 0
	for bird in birds:
		_check_feet(bird, failures)
		_check_beak(bird, failures)
		if String(bird.get("species")) == "gull":
			_check_gull_form(bird, failures)
			_check_gull_texture(bird, failures)
		if bool(bird.get("juvenile")):
			juvenile_count += 1
			var body := _pose_root(bird).get_node_or_null("body") as MeshInstance3D
			_expect(bool(bird.get("model_has_authored_plumage")) and body != null
				and body.mesh != null,
				"juvenile gull does not carry its authored mottled plumage", failures)
			_check_juvenile_wing_sides(bird, failures)
			_check_juvenile_tail_fan(bird, failures)
		elif String(bird.get("species")) == "gull":
			_check_adult_wing_sides(bird, failures)
			_check_adult_tail_variant(bird, failures)
			if bool(bird.get("black_tail")):
				adult_dark_tail_count += 1
			else:
				adult_white_tail_count += 1
		if bool(bird.get("starts_airborne")):
			airborne_count += 1
		else:
			_expect(not _inside_protected_anchor(bird.global_position),
				"ground bird %s is inside a protected anchor" % bird.name, failures)
		_expect(not bird.is_in_group("collectible"),
			"bird %s was made collectible" % bird.name, failures)
	_expect(juvenile_count == EXPECTED_JUVENILE_GULLS,
		"expected %d juvenile gulls, found %d" % [EXPECTED_JUVENILE_GULLS, juvenile_count],
		failures)
	_expect(adult_white_tail_count == 10 and adult_dark_tail_count == 9,
		"adult gull colony lost its near-even white/dark tail split", failures)
	_expect(airborne_count == 2, "waterfront circling pair is missing", failures)
	_check_colony(failures)

	var test_gull = gulls[0] if not gulls.is_empty() else null
	if test_gull != null:
		_check_full_beak_pose(test_gull, failures)

	var test_pigeon = pigeons[0] if not pigeons.is_empty() else null
	if test_pigeon != null:
		_check_full_beak_pose(test_pigeon, failures)
		test_pigeon.scare_from(test_pigeon.global_position + Vector3(0.5, 0.0, 0.0))
		_expect(test_pigeon.is_flying(), "ground bird did not flush when approached", failures)

	flock.queue_free()
	if failures.is_empty():
		print("PASS: %d gulls, %d rock doves, rock roosts, park/beach range, UV atlases, articulated bills and flush behavior" % [
			gulls.size(), pigeons.size()])
		get_tree().quit()
		return
	for failure in failures:
		printerr("FAIL: ", failure)
	get_tree().quit(1)


func _inside_protected_anchor(position: Vector3) -> bool:
	var p := Vector2(position.x, position.z)
	var in_west := p.x >= -74.0 and p.x <= -55.0 and p.y >= -15.0 and p.y <= 12.0
	var east_delta := p - Vector2(86.0, 0.0)
	var in_east := pow(east_delta.x / 42.0, 2.0) + pow(east_delta.y / 36.0, 2.0) <= 1.0
	return in_west or in_east


func _check_colony(failures: Array[String]) -> void:
	var members := get_tree().get_nodes_in_group("gull_colony_member")
	var residents := get_tree().get_nodes_in_group("gull_roost_resident")
	var commuters := get_tree().get_nodes_in_group("gull_colony_commuter")
	var roosts := get_tree().get_nodes_in_group("gull_roost")
	var sites := get_tree().get_nodes_in_group("gull_foraging_site")
	_expect(members.size() == EXPECTED_COLONY_GULLS,
		"expected %d colony gulls, found %d" % [EXPECTED_COLONY_GULLS, members.size()], failures)
	_expect(roosts.size() == EXPECTED_ROOSTS,
		"expected %d rock roost sockets, found %d" % [EXPECTED_ROOSTS, roosts.size()], failures)
	_expect(sites.size() == EXPECTED_FORAGING_SITES,
		"expected %d park/beach feeding sites, found %d" % [EXPECTED_FORAGING_SITES, sites.size()], failures)
	_expect(residents.size() == EXPECTED_ROOSTS,
		"each rock roost does not retain one resident gull", failures)
	_expect(commuters.size() == EXPECTED_COLONY_GULLS - EXPECTED_ROOSTS,
		"colony commuter count does not preserve the ranged flock", failures)
	_check_roost_grounding(roosts, failures)

	var has_park_site := false
	var has_north_beach := false
	var has_south_beach := false
	for site in sites:
		var p: Vector3 = site.global_position
		has_park_site = has_park_site or (absf(p.x) <= 230.0 and absf(p.z) <= 230.0)
		has_north_beach = has_north_beach or p.z <= -1500.0
		has_south_beach = has_south_beach or p.z >= 300.0
	_expect(has_park_site, "gull range no longer enters the park", failures)
	_expect(has_north_beach and has_south_beach,
		"gull range no longer spans other north and south beaches", failures)

	for member in members:
		_expect(String(member.get("species")) == "gull",
			"non-gull was enrolled in the gull colony", failures)
		var roost: Vector3 = member.call("get_colony_roost")
		var matches_roost := false
		for marker in roosts:
			if roost.distance_to(marker.global_position) < 0.05:
				matches_roost = true
				break
		_expect(matches_roost,
			"%s does not return to an authored rock roost" % member.name, failures)
		var feeding: Array[Vector3] = member.call("get_colony_foraging_sites")
		_expect(feeding.size() == EXPECTED_FORAGING_SITES,
			"%s does not retain the complete park/beach range" % member.name, failures)
		if bool(member.call("is_colony_resident")):
			_expect(bool(member.call("is_roosting")),
				"resident gull %s did not remain at its nest" % member.name, failures)
			_expect(member.global_position.distance_to(roost) < 0.05,
				"resident gull %s is not standing at its roost socket" % member.name, failures)
		else:
			_expect(bool(member.call("is_flying")),
				"commuter gull %s did not begin in the active range" % member.name, failures)

	for roost in roosts:
		var resident_matches := 0
		for resident in residents:
			var resident_roost: Vector3 = resident.call("get_colony_roost")
			if resident_roost.distance_to(roost.global_position) < 0.05:
				resident_matches += 1
		_expect(resident_matches == 1,
			"rock socket %s does not have exactly one resident nesting gull" % roost.name,
			failures)

	if not commuters.is_empty():
		var returning = commuters[0]
		returning.set("colony_sites_per_trip", 1)
		returning.set("colony_flight_speed", 100000.0)
		returning.set("_colony_phase_timer", 0.0)
		returning.call("_physics_process", 0.1)
		for step in range(60):
			returning.call("_physics_process", 0.1)
		_expect(bool(returning.call("is_roosting")),
			"commuter gull did not return from a feeding site to its rock roost", failures)
		var returned_roost: Vector3 = returning.call("get_colony_roost")
		_expect(returning.global_position.distance_to(returned_roost) < 0.05,
			"returning commuter missed its authored rock socket", failures)


func _check_roost_grounding(roosts: Array[Node], failures: Array[String]) -> void:
	var source := load("res://assets/range_forest_distinct_background.glb") as PackedScene
	_expect(source != null, "mounted editor-owned range source did not load", failures)
	if source == null:
		return
	var range_root := source.instantiate()
	var rock_points: Array[Vector3] = []
	var roost_hosts := {
		"background_distant_range_north": true,
		"background_distant_range_north_west_companion": true,
		"north_shore_volcanic_plug": true,
	}
	for child in range_root.get_children():
		if not child is MeshInstance3D or not roost_hosts.has(String(child.name)):
			continue
		var mesh_instance := child as MeshInstance3D
		if not mesh_instance.mesh is ArrayMesh:
			continue
		for surface_index in range(mesh_instance.mesh.get_surface_count()):
			var arrays := mesh_instance.mesh.surface_get_arrays(surface_index)
			var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			for vertex in vertices:
				rock_points.append(mesh_instance.transform * vertex)
	for roost in roosts:
		var marker_position: Vector3 = roost.global_position
		var grounded := false
		for point in rock_points:
			if Vector2(marker_position.x - point.x, marker_position.z - point.z).length() <= 0.05 \
					and marker_position.y >= point.y \
					and marker_position.y - point.y <= 0.2:
				grounded = true
				break
		_expect(grounded,
			"rock roost %s no longer sits on its editor-owned landform source" % roost.name,
			failures)
	range_root.queue_free()


func _check_feet(bird: Node, failures: Array[String]) -> void:
	var root := _pose_root(bird)
	for leg_name in ["leg_left", "leg_right"]:
		var leg := root.get_node_or_null(leg_name) as Node3D
		_expect(leg != null, "%s is missing %s" % [bird.name, leg_name], failures)
		if leg == null:
			continue
		var foot := _named_mesh_child(leg, "foot")
		if foot != null and foot.mesh != null:
			var bounds := foot.mesh.get_aabb()
			_expect(-bounds.position.z > bounds.end.z,
				"%s/%s webbed foot does not taper forward" % [bird.name, leg_name], failures)
			continue
		for toe_name in ["toe_centre", "toe_inner", "toe_outer"]:
			var toe := leg.get_node_or_null(toe_name) as Node3D
			_expect(toe != null, "%s/%s is missing" % [leg_name, toe_name], failures)
			if toe != null:
				var toe_mesh := toe.get_node_or_null("mesh") as MeshInstance3D
				_expect(toe_mesh != null, "%s/%s/mesh is missing" % [leg_name, toe_name], failures)
				if toe_mesh != null:
					_expect(toe_mesh.position.z < 0.0 and toe_mesh.rotation.x < 0.0,
					"%s/%s/%s does not taper forward" % [bird.name, leg_name, toe_name], failures)
		var back_toe := leg.get_node_or_null("toe_back") as Node3D
		_expect(back_toe != null, "%s/toe_back is missing" % leg_name, failures)
		if back_toe != null:
			var back_mesh := back_toe.get_node_or_null("mesh") as MeshInstance3D
			_expect(back_mesh != null, "%s/toe_back/mesh is missing" % leg_name, failures)
			if back_mesh != null:
				_expect(back_mesh.position.z > 0.0 and back_mesh.rotation.x > 0.0,
					"%s/%s/toe_back does not taper backward" % [bird.name, leg_name], failures)


func _check_beak(bird: Node, failures: Array[String]) -> void:
	var beak := _pose_root(bird).get_node_or_null("head_pivot/beak") as Node3D
	_expect(beak != null, "%s is missing its bill root" % bird.name, failures)
	if beak == null:
		return
	var upper := beak.get_node_or_null("upper_pivot") as Node3D
	var lower := beak.get_node_or_null("lower_pivot") as Node3D
	var mouth := beak.get_node_or_null("mouth_interior") as MeshInstance3D
	_expect(upper != null, "%s is missing its upper bill pivot" % bird.name, failures)
	_expect(lower != null, "%s is missing its lower bill pivot" % bird.name, failures)
	_expect(mouth != null, "%s is missing its mouth interior" % bird.name, failures)
	if upper != null:
		_expect(_has_mesh_child(upper),
			"%s is missing its upper bill mesh" % bird.name, failures)
	if lower != null:
		_expect(_has_mesh_child(lower),
			"%s is missing its lower bill mesh" % bird.name, failures)


func _check_full_beak_pose(bird: Node, failures: Array[String]) -> void:
	var root := _pose_root(bird)
	var upper := root.get_node("head_pivot/beak/upper_pivot") as Node3D
	var lower := root.get_node("head_pivot/beak/lower_pivot") as Node3D
	bird.call("set_beak_open", 0.0)
	var upper_closed := upper.rotation.x
	var lower_closed := lower.rotation.x
	bird.call("set_beak_open", 1.0)
	_expect(is_equal_approx(float(bird.call("get_beak_open_amount")), 1.0),
		"%s does not retain an explicit open-bill pose" % bird.name, failures)
	_expect(upper.rotation.x > upper_closed,
		"%s upper bill does not lift" % bird.name, failures)
	_expect(lower.rotation.x < lower_closed,
		"%s lower bill does not drop" % bird.name, failures)
	bird.call("set_beak_open", 0.0)
	bird.call("clear_beak_pose")


func _check_gull_form(bird: Node, failures: Array[String]) -> void:
	var root := _pose_root(bird)
	var body := root.get_node_or_null("body") as MeshInstance3D
	_expect(body != null and body.mesh is ArrayMesh,
		"%s does not use a single authored low-poly body" % bird.name, failures)
	for side in ["left", "right"]:
		var wing := root.get_node_or_null("wing_%s" % side) as Node3D
		_expect(wing != null, "%s is missing wing_%s" % [bird.name, side], failures)
		if wing == null:
			continue
		var outer_found := false
		for child in wing.get_children():
			if child is Node3D and String(child.name).begins_with("outer_pivot"):
				outer_found = true
				break
		_expect(outer_found,
			"%s wing_%s lacks its tapered outer panel" % [bird.name, side], failures)
	for descendant in root.find_children("*", "MeshInstance3D", true, false):
		var mesh_instance := descendant as MeshInstance3D
		_expect(not mesh_instance.mesh is SphereMesh,
			"%s still contains primitive sphere construction at %s" % [
				bird.name, root.get_path_to(mesh_instance)], failures)


func _check_gull_texture(bird: Node, failures: Array[String]) -> void:
	var root := _pose_root(bird)
	var surface_count := 0
	var uv_surface_count := 0
	var textured_surface_count := 0
	for descendant in root.find_children("*", "MeshInstance3D", true, false):
		var mesh_instance := descendant as MeshInstance3D
		if mesh_instance.mesh == null:
			continue
		for surface_index in mesh_instance.mesh.get_surface_count():
			surface_count += 1
			if mesh_instance.mesh.surface_get_format(surface_index) & Mesh.ARRAY_FORMAT_TEX_UV:
				uv_surface_count += 1
			var material := mesh_instance.mesh.surface_get_material(surface_index) as BaseMaterial3D
			if material != null and material.albedo_texture != null:
				textured_surface_count += 1
	_expect(surface_count > 0,
		"%s contains no visible atlas surfaces" % bird.name, failures)
	_expect(uv_surface_count == surface_count,
		"%s has %d of %d surfaces UV-wrapped" % [bird.name, uv_surface_count, surface_count], failures)
	_expect(textured_surface_count == surface_count,
		"%s has %d of %d surfaces using its texture atlas" % [
			bird.name, textured_surface_count, surface_count], failures)


func _check_juvenile_wing_sides(bird: Node, failures: Array[String]) -> void:
	var inner_top_uv_count := 0
	var inner_underside_uv_count := 0
	var outer_top_uv_count := 0
	var outer_underside_uv_count := 0
	for descendant in _pose_root(bird).find_children("*", "MeshInstance3D", true, false):
		var mesh_instance := descendant as MeshInstance3D
		var mesh_name := String(mesh_instance.name)
		if not mesh_name.begins_with("inner_mesh") and not mesh_name.begins_with("outer_mesh"):
			continue
		if mesh_instance.mesh == null:
			continue
		for surface_index in mesh_instance.mesh.get_surface_count():
			var arrays := mesh_instance.mesh.surface_get_arrays(surface_index)
			var uvs := arrays[Mesh.ARRAY_TEX_UV] as PackedVector2Array
			for uv in uvs:
				if mesh_name.begins_with("inner_mesh"):
					if uv.x > 0.25 and uv.x < 0.50:
						inner_top_uv_count += 1
					elif uv.x > 0.50 and uv.x < 0.75:
						inner_underside_uv_count += 1
				elif mesh_name.begins_with("outer_mesh"):
					if uv.x < 0.25:
						outer_top_uv_count += 1
					elif uv.x > 0.75:
						outer_underside_uv_count += 1
	_expect(inner_top_uv_count > 0,
		"juvenile gull inner upper wings do not use their covert region", failures)
	_expect(inner_underside_uv_count > 0,
		"juvenile gull inner wing undersides do not use their pale barred region", failures)
	_expect(outer_top_uv_count > 0,
		"juvenile gull outer upper wings do not use their dark primary-tip region", failures)
	_expect(outer_underside_uv_count > 0,
		"juvenile gull outer wing undersides do not use their separately tipped region", failures)


func _check_juvenile_tail_fan(bird: Node, failures: Array[String]) -> void:
	var tail := _pose_root(bird).get_node_or_null("tail") as MeshInstance3D
	_expect(tail != null and tail.mesh != null,
		"juvenile gull is missing its authored tail fan", failures)
	if tail == null or tail.mesh == null:
		return
	var vertex_count := 0
	for surface_index in tail.mesh.get_surface_count():
		var arrays := tail.mesh.surface_get_arrays(surface_index)
		vertex_count += (arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()
	_expect(vertex_count >= 80,
		"juvenile gull tail has regressed to a single-point silhouette", failures)
	_expect(tail.mesh.get_aabb().size.x >= 0.40,
		"juvenile gull tail no longer reads as a broad fan", failures)


func _check_adult_wing_sides(bird: Node, failures: Array[String]) -> void:
	var inner_top := 0
	var inner_under := 0
	var outer_top := 0
	var outer_under := 0
	for descendant in _pose_root(bird).find_children("*", "MeshInstance3D", true, false):
		var mesh_instance := descendant as MeshInstance3D
		var mesh_name := String(mesh_instance.name)
		if not mesh_name.begins_with("inner_mesh") and not mesh_name.begins_with("outer_mesh"):
			continue
		for surface_index in mesh_instance.mesh.get_surface_count():
			var arrays := mesh_instance.mesh.surface_get_arrays(surface_index)
			var uvs := arrays[Mesh.ARRAY_TEX_UV] as PackedVector2Array
			for uv in uvs:
				if mesh_name.begins_with("inner_mesh"):
					if uv.x > 0.25 and uv.x < 0.50 and uv.y > 0.75:
						inner_top += 1
					elif uv.x > 0.50 and uv.x < 0.75 and uv.y > 0.75:
						inner_under += 1
				elif uv.x > 0.75 and uv.y > 0.75:
					outer_top += 1
				elif uv.x < 0.25 and uv.y > 0.50 and uv.y < 0.75:
					outer_under += 1
	_expect(inner_top > 0 and inner_under > 0,
		"adult gull inner wing top and underside do not use separate atlas regions", failures)
	_expect(outer_top > 0 and outer_under > 0,
		"adult gull primary top and underside do not use separate atlas regions", failures)


func _check_adult_tail_variant(bird: Node, failures: Array[String]) -> void:
	var root := _pose_root(bird)
	var white_tail := root.get_node_or_null("tail_white") as MeshInstance3D
	var dark_tail := root.get_node_or_null("tail_dark") as MeshInstance3D
	var uses_dark := bool(bird.get("black_tail"))
	_expect(white_tail != null and dark_tail != null,
		"adult gull does not carry both authored tail meshes", failures)
	if white_tail != null and dark_tail != null:
		_expect(white_tail.visible == not uses_dark and dark_tail.visible == uses_dark,
			"adult gull tail visibility does not match its Inspector variant", failures)
		var tails: Array[MeshInstance3D] = [white_tail, dark_tail]
		for tail in tails:
			var vertex_count := 0
			for surface_index in tail.mesh.get_surface_count():
				var arrays: Array = tail.mesh.surface_get_arrays(surface_index)
				vertex_count += (arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()
			_expect(vertex_count >= 80 and tail.mesh.get_aabb().size.x >= 0.40,
				"adult gull tail has regressed from its broad feather fan", failures)
	for spot_name in ["bill_spot_left", "bill_spot_right"]:
		var spot := root.find_child(spot_name, true, false) as GeometryInstance3D
		_expect(spot != null and spot.visible == uses_dark,
			"adult gull bill dot does not follow the dark-tail variant", failures)


func _pose_root(bird: Node) -> Node3D:
	return bird.call("get_pose_root") as Node3D


func _has_mesh_child(node: Node) -> bool:
	for child in node.get_children():
		if child is MeshInstance3D:
			return true
	return false


func _named_mesh_child(node: Node, prefix: String) -> MeshInstance3D:
	for child in node.get_children():
		if child is MeshInstance3D and String(child.name).begins_with(prefix):
			return child as MeshInstance3D
	return null


func _expect(condition: bool, message: String, failures: Array[String]) -> void:
	if not condition:
		failures.append(message)


func _fail(message: String) -> void:
	printerr("FAIL: ", message)
	get_tree().quit(1)
