extends Node

## Focused palm acceptance: every established foot remains fixed while the
## shared editor-owned trunk, crown and footing sources provide tightly bounded
## height, bend, crown-density and retained-frond variation. Arrival pairs use
## tall near-straight shafts and dense, layered classic-California pinnate
## crowns; both former fan-palm readings remain outside the standing world.


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run.call_deferred()


func _run() -> void:
	for _i in 12:
		await get_tree().process_frame
	var boardwalk := get_tree().root.find_child("boardwalk", true, false) as Node3D
	var approach := get_tree().root.find_child("park_approach", true, false) as Node3D
	if boardwalk == null or approach == null:
		_fail("the Boardwalk or park approach is not mounted")
		return
	if not _check_place(boardwalk, 8):
		return
	if not _check_place(approach, 26):
		return
	if not _check_arrival_landscaping(approach):
		return
	if not _check_roadside_landscaping(approach):
		return
	if not await _check_date_palm_catalog():
		return
	if not await _check_palmetto_catalog():
		return
	print("PASS: 34 fixed-foot coastal palms retain their layered bases; the sixteen arrival palms keep their approved 30–32-frond classic-California crowns; PRP-PLANT-051 doubles that live head to 64 interleaved pinnate fronds; the former fan forms have no standing placement; all 26 arrival and front-road feet keep their planting rings and every opening remains clear")
	get_tree().quit()


func _check_arrival_landscaping(approach: Node3D) -> bool:
	var landscaping := approach.get_node_or_null(
		"authored_additions/coastal_arrival_curb_landscaping") as Node3D
	if landscaping == null:
		_fail("park approach has no arrival curb landscaping")
		return false
	var courses := landscaping.get_node("bed_courses")
	var beds := landscaping.get_node("derived_beds")
	var modules := landscaping.get_node("derived_modules")
	var purple_heart_accents := landscaping.get_node_or_null(
		"purple_heart_accents")
	if courses.get_child_count() != 4 or beds.get_child_count() != 4:
		_fail("arrival landscaping does not preserve four editable curb-bed courses")
		return false
	if modules.get_child_count() != 60:
		_fail("arrival landscaping expected 60 lush modules, found %d" %
			modules.get_child_count())
		return false
	if purple_heart_accents == null \
			or purple_heart_accents.get_child_count() != 2:
		_fail("arrival landscaping expected two restrained Purple Heart accents")
		return false
	for accent in purple_heart_accents.get_children():
		var sprigs := accent.get_node_or_null("sprigs")
		if sprigs == null or sprigs.get_child_count() != 14:
			_fail("%s is not the airy Purple Heart vA catalog row" % accent.name)
			return false
	for bed in beds.get_children():
		var mesh := (bed as MeshInstance3D).mesh
		if mesh == null or mesh.get_surface_count() != 1:
			_fail("%s is missing its derived soil ribbon" % bed.name)
			return false
	for module in modules.get_children():
		for required in ["groundcover", "groundcover_lobe", "rosette_near", "rosette_far", "flower_drift",
				"fern_near", "fern_far"]:
			if module.get_node_or_null(required) == null:
				_fail("%s is missing its landscaped %s layer" % [
					module.name, required])
				return false
		var groundcover := module.get_node("groundcover") as MeshInstance3D
		if groundcover.scale.y > 0.22 or absf(groundcover.position.x) < 0.08:
			_fail("%s has returned to a raised centred groundcover donut" % module.name)
			return false
		var flower_drift := module.get_node("flower_drift") as Node3D
		if flower_drift.get_node_or_null("foliage_secondary") == null:
			_fail("%s flower drift has returned to one centred foliage mound" % module.name)
			return false
		if not module.has_meta("bed_variation"):
			_fail("%s is missing its loose-bed placement variation" % module.name)
			return false
		for fern_name in ["fern_near", "fern_far"]:
			if not _check_fern(module.get_node(fern_name) as Node3D,
					"%s/%s" % [module.name, fern_name]):
				return false
	return true


func _check_roadside_landscaping(approach: Node3D) -> bool:
	var landscaping := approach.get_node_or_null(
		"authored_additions/coastal_roadside_landscaping") as Node3D
	if landscaping == null:
		_fail("park approach has no roadside curb and linear-bed source")
		return false
	var courses := landscaping.get_node("edge_courses")
	var curbs := landscaping.get_node("derived_curbs")
	var beds := landscaping.get_node("derived_beds")
	var modules := landscaping.get_node("derived_modules")
	if courses.get_child_count() != 8 or curbs.get_child_count() != 8 \
			or beds.get_child_count() != 8:
		_fail("roadside landscaping does not preserve eight editable edge courses and derived ribbons")
		return false
	if modules.get_child_count() != 90:
		_fail("roadside landscaping expected 90 linear-bed modules, found %d" %
			modules.get_child_count())
		return false
	for curb in curbs.get_children():
		var curb_mesh := (curb as MeshInstance3D).mesh
		if curb_mesh == null or curb_mesh.get_surface_count() != 1 \
				or not is_equal_approx(float(curb.get_meta("curb_height", 0.0)), 0.16):
			_fail("%s is not the approved 16cm low curb" % curb.name)
			return false
	for bed in beds.get_children():
		var bed_mesh := (bed as MeshInstance3D).mesh
		if bed_mesh == null or bed_mesh.get_surface_count() != 1 \
				or float(bed.get_meta("bed_width", 0.0)) < 3.89:
			_fail("%s is missing its broad linear soil border" % bed.name)
			return false
	for module in modules.get_children():
		if not module.has_meta("roadside_variation") \
				or module.get_node_or_null("flower_drift") == null \
				or module.get_node_or_null("fern_near") == null \
				or module.get_node_or_null("fern_far") == null:
			_fail("%s is missing its layered roadside planting" % module.name)
			return false
	return true


func _check_place(place: Node3D, expected_count: int) -> bool:
	var controller := place.get_node_or_null("authored_additions/coastal_palm_replacements")
	if controller == null:
		_fail("%s has no palm replacement controller" % place.name)
		return false
	var crown_output := controller.get_node("generated_crowns")
	var trunk_output := controller.get_node("generated_trunks")
	var base_output := controller.get_node("generated_bases")
	if crown_output.get_child_count() != expected_count:
		_fail("%s expected %d new crowns, found %d" % [
			place.name, expected_count, crown_output.get_child_count()])
		return false
	if trunk_output.get_child_count() != expected_count:
		_fail("%s expected %d new trunks, found %d" % [
			place.name, expected_count, trunk_output.get_child_count()])
		return false
	if base_output.get_child_count() != expected_count:
		_fail("%s expected %d new bases, found %d" % [
			place.name, expected_count, base_output.get_child_count()])
		return false

	var saw_added_fronds := false
	var shared_ring_count := 0
	for replacement in crown_output.get_children():
		var prefix := String(replacement.name).trim_suffix("_editor_crown")
		var old_crown := place.get_node_or_null(prefix + "_crown") as GeometryInstance3D
		var old_trunk := place.get_node_or_null(prefix + "_trunk") as GeometryInstance3D
		var new_trunk := trunk_output.get_node_or_null(prefix + "_editor_trunk") as Node3D
		var new_base := base_output.get_node_or_null(prefix + "_editor_base") as Node3D
		if old_crown == null or old_trunk == null or new_trunk == null \
				or new_base == null:
			_fail("%s cannot be matched to its established source palm" % replacement.name)
			return false
		if old_crown.visible:
			_fail("%s old crown remains visible" % old_crown.name)
			return false
		if old_trunk.visible:
			_fail("%s old rod trunk remains visible" % old_trunk.name)
			return false
		var source_base := new_trunk.get_meta("source_base") as Vector3
		var source_top := new_trunk.get_meta("source_top") as Vector3
		var new_top := new_trunk.get_meta("new_top") as Vector3
		var height_gain := float(new_trunk.get_meta("height_gain"))
		var lateral_offset := new_trunk.get_meta("lateral_offset") as Vector3
		if not new_trunk.position.is_equal_approx(source_base):
			_fail("%s moved its established foot" % new_trunk.name)
			return false
		if not new_base.position.is_equal_approx(source_base):
			_fail("%s is detached from its established foot" % new_base.name)
			return false
		var flowers := new_base.get_node_or_null("flowers")
		var flower_clusters: Array[Node] = []
		if flowers != null:
			for flower_child in flowers.get_children():
				if String(flower_child.name).ends_with("_cluster"):
					flower_clusters.append(flower_child)
		if flowers == null or flower_clusters.size() != 3 \
				or flowers.get_node_or_null("planted_collar") == null:
			_fail("%s is missing its three landscaped flower clusters" % new_base.name)
			return false
		if not prefix.begins_with("deck_palm_"):
			var planted_collar := flowers.get_node("planted_collar") as MeshInstance3D
			if planted_collar.mesh is TorusMesh \
					or flowers.get_node_or_null("planted_lobe_east") == null \
					or flowers.get_node_or_null("planted_lobe_south") == null:
				_fail("%s has returned to a circular donut planting collar" % new_base.name)
				return false
			if new_base.get_node_or_null("soil_patch_east") == null \
					or new_base.get_node_or_null("soil_patch_south") == null:
				_fail("%s has returned to one circular soil disc" % new_base.name)
				return false
			var fern_pockets := new_base.get_node_or_null("fern_pockets")
			var rosettes := new_base.get_node_or_null("border_rosettes")
			if fern_pockets == null or fern_pockets.get_child_count() != 6 \
					or rosettes == null or rosettes.get_child_count() != 8:
				_fail("%s is missing its loose fern or rosette sweep" % new_base.name)
				return false
			var rosette_radii: Array[float] = []
			for rosette in rosettes.get_children():
				var rosette_position := (rosette as Node3D).position
				rosette_radii.append(Vector2(rosette_position.x,
					rosette_position.z).length())
			rosette_radii.sort()
			if rosette_radii[-1] - rosette_radii[0] < 0.08:
				_fail("%s rosettes have returned to an even circular ring" % new_base.name)
				return false
		for cluster in flower_clusters:
			var bloom_count := 0
			for part in cluster.get_children():
				if String(part.name).begins_with("bloom_"):
					bloom_count += 1
			if cluster.get_node_or_null("foliage") == null or bloom_count < 4:
				_fail("%s/%s is not a dense bedding cluster" % [
					new_base.name, cluster.name])
				return false
		if prefix.begins_with("deck_palm_"):
			var timber_frame := new_base.get_node_or_null("timber_frame")
			var timber_details := new_base.get_node_or_null("timber_details")
			var fern_ring := new_base.get_node_or_null("fern_ring")
			var border_rosettes := new_base.get_node_or_null("border_rosettes")
			var color_accents := new_base.get_node_or_null("color_accents")
			if new_base.get_node_or_null("soil_fill") == null \
					or timber_frame == null or timber_frame.get_child_count() != 4 \
					or timber_details == null or timber_details.get_child_count() != 12 \
					or fern_ring == null or fern_ring.get_child_count() != 4 \
					or border_rosettes == null or border_rosettes.get_child_count() != 4 \
					or color_accents == null or color_accents.get_child_count() != 4:
				_fail("%s is missing its Boardwalk timber tree box" % new_base.name)
				return false
			for accent_name in [&"hakone_nw", &"hakone_se", &"purple_ne", &"purple_sw"]:
				var accent := color_accents.get_node_or_null(NodePath(accent_name)) as Node3D
				if accent == null or accent.position.y < 0.37 or accent.scale.y < 0.5 \
						or Vector2(accent.position.x, accent.position.z).length() < 0.38:
					_fail("%s/%s does not preserve the open-center contrast pocket" % [
						new_base.name, accent_name])
					return false
			for fern in fern_ring.get_children():
				if (fern as Node3D).position.y < 0.38 or (fern as Node3D).scale.y < 1.0:
					_fail("%s/%s disappears below the Boardwalk cap rail" % [
						new_base.name, fern.name])
					return false
				if not _check_fern(fern as Node3D,
						"%s/%s" % [new_base.name, fern.name]):
					return false
			for rosette in border_rosettes.get_children():
				if (rosette as Node3D).position.y < 0.36 or (rosette as Node3D).scale.y < 0.78:
					_fail("%s/%s disappears below the Boardwalk cap rail" % [
						new_base.name, rosette.name])
					return false
			for cluster in flower_clusters:
				if (cluster as Node3D).position.y < 0.34:
					_fail("%s/%s disappears below the Boardwalk cap rail" % [
						new_base.name, cluster.name])
					return false
		else:
			var fern_pockets := new_base.get_node_or_null("fern_pockets")
			var border_rosettes := new_base.get_node_or_null("border_rosettes")
			if new_base.get_node_or_null("soil_patch") == null \
					or fern_pockets == null or fern_pockets.get_child_count() != 6 \
					or border_rosettes == null or border_rosettes.get_child_count() != 8:
				_fail("%s is missing its layered lawn planting" % new_base.name)
				return false
			for fern in fern_pockets.get_children():
				if not _check_fern(fern as Node3D,
						"%s/%s" % [new_base.name, fern.name]):
					return false
		var uses_shared_rings := prefix.begins_with("walk_palm_") \
			or prefix.begins_with("front_palm_")
		if uses_shared_rings:
			shared_ring_count += 1
			var arrival_rings := new_base.get_node_or_null("arrival_accent_rings")
			var arrival_fern_pockets := new_base.get_node_or_null("fern_pockets")
			var hakone_clumps := new_base.get_node_or_null(
				"arrival_accent_rings/japanese_forest_grass_inner_ring/clumps")
			var purple_sprigs := new_base.get_node_or_null(
				"arrival_accent_rings/purple_heart_outer_ring")
			if arrival_rings == null or hakone_clumps == null \
					or hakone_clumps.get_child_count() != 10 \
					or purple_sprigs == null or purple_sprigs.get_child_count() != 36:
				_fail("%s is missing its two arrival planting rings" % new_base.name)
				return false
			if (purple_sprigs as Node3D).scale.x > 0.71:
				_fail("%s Purple Heart ring is no longer tucked under the Hakone skirt" %
					new_base.name)
				return false
			var purple_radii: Array[float] = []
			for sprig in purple_sprigs.get_children():
				var sprig_position := (sprig as Node3D).position
				purple_radii.append(Vector2(sprig_position.x,
					sprig_position.z).length())
			purple_radii.sort()
			if purple_radii[0] < 1.4 or purple_radii[-1] > 1.6 \
					or purple_radii[-1] - purple_radii[0] < 0.05:
				_fail("%s Purple Heart band lost its loose outer-ring spacing" %
					new_base.name)
				return false
			if flowers.scale.y < 3.1 \
					or float(flowers.get_meta("arrival_height_scale", 0.0)) < 3.1:
				_fail("%s mixed center no longer rises above the forest grass" %
					new_base.name)
				return false
			if arrival_fern_pockets == null \
					or float(arrival_fern_pockets.get_meta(
						"arrival_fern_scale", 0.0)) < 1.99:
				_fail("%s arrival ferns are no longer doubled in size" %
					new_base.name)
				return false
			for fern in arrival_fern_pockets.get_children():
				if (fern as Node3D).scale.x < 1.35:
					_fail("%s/%s did not receive the doubled arrival scale" % [
						new_base.name, fern.name])
					return false
		if prefix.begins_with("walk_palm_"):
			if height_gain < 0.849 or height_gain > 1.019:
				_fail("%s height gain %.3fm exceeds the taller arrival band" % [
					new_trunk.name, height_gain])
				return false
		elif not prefix.begins_with("front_palm_") \
				and new_base.get_node_or_null("arrival_accent_rings") != null:
			_fail("%s incorrectly carries the arrival/front-road planting rings" %
				new_base.name)
			return false
		elif height_gain < 0.099 or height_gain > 0.269:
			_fail("%s height gain %.3fm exceeds the non-arrival band" % [
				new_trunk.name, height_gain])
			return false
		if not replacement.position.is_equal_approx(new_top):
			_fail("%s is detached from its new trunk top" % replacement.name)
			return false
		var expected_top := Vector3(source_base.x, source_top.y + height_gain,
			source_base.z) + lateral_offset
		var trunk_mesh := new_trunk.get_node("derived_trunk") as MeshInstance3D
		if trunk_mesh.mesh == null or trunk_mesh.mesh.get_surface_count() != 1:
			_fail("%s is missing its tapered trunk surface" % new_trunk.name)
			return false
		if prefix.begins_with("walk_palm_"):
			if not is_equal_approx(lateral_offset.x,
					-signf(source_base.x) * 0.55) or absf(lateral_offset.z) > 0.121:
				_fail("%s exceeds the restrained arrival-row lean" % new_trunk.name)
				return false
			var bend_direction := new_trunk.get_meta("bend_direction") as Vector3
			var inward := Vector3(-signf(source_base.x), 0.0, 0.0)
			if bend_direction.dot(inward) < 0.99:
				_fail("%s does not curve toward the opposite row" % new_trunk.name)
				return false
			# Check the emitted shaft rather than trusting the controller's intended
			# direction metadata. Ring six is near mid-height, where the source bow
			# reaches its clearest offset from the straight base-to-top chord.
			var trunk_vertices := trunk_mesh.mesh.surface_get_arrays(0)[
				Mesh.ARRAY_VERTEX] as PackedVector3Array
			var middle_ring := 6
			var middle_center := Vector3.ZERO
			for side_index in 8:
				middle_center += trunk_mesh.to_global(
					trunk_vertices[middle_ring * 8 + side_index])
			middle_center /= 8.0
			var chord_point := source_base.lerp(new_top,
				float(middle_ring) / 13.0)
			if (middle_center - chord_point).dot(inward) < 0.04:
				_fail("%s emitted shaft bends away from the opposite row" %
					new_trunk.name)
				return false
		elif lateral_offset.length() < 0.079 or lateral_offset.length() > 0.117:
			_fail("%s exceeds its restrained non-arrival lean" % new_trunk.name)
			return false
		if not new_top.is_equal_approx(expected_top):
			_fail("%s exceeds its authorized top variation" % new_trunk.name)
			return false

		var courses := replacement.get_node("frond_courses")
		var derived := replacement.get_node("derived_fronds")
		var extra_fronds := int(replacement.get("extra_frond_count"))
		var density_multiplier := int(replacement.get("density_multiplier"))
		var expected_core_courses := 12
		var expected_source_courses := 32
		if courses.get_child_count() != expected_source_courses \
				or density_multiplier != 1 \
				or derived.get_child_count() \
					!= (expected_core_courses + extra_fronds) * density_multiplier:
			_fail("%s does not preserve its core plus twenty optional pinnate courses" % replacement.name)
			return false
		saw_added_fronds = saw_added_fronds or extra_fronds > 0
		var full_feather_fronds := 0
		for frond in derived.get_children():
			var mesh := (frond as MeshInstance3D).mesh as ArrayMesh
			if mesh == null or mesh.get_surface_count() != 2:
				_fail("%s/%s is missing its live-leaf or midrib surface" % [replacement.name, frond.name])
				return false
			if String(frond.get_meta("silhouette", "")) != "pinnate" \
					or frond.has_meta("fan_finger_count"):
				_fail("%s/%s is not a feather-palm frond" % [replacement.name, frond.name])
				return false
			if int(frond.get_meta("leaflet_pair_count", 0)) == 16:
				full_feather_fronds += 1
		var remnant_count := int(replacement.get("remnant_count"))
		if prefix.begins_with("walk_palm_"):
			var remnant_courses := replacement.get_node_or_null("remnant_courses")
			var remnants := replacement.get_node_or_null("derived_remnants")
			if String(replacement.get_meta("species_language", "")) \
					!= "classic_california_date_palm" \
					or extra_fronds < 18 or extra_fronds > 20 \
					or full_feather_fronds < 26 \
					or remnant_courses == null or remnant_courses.get_child_count() != 12 \
					or remnant_count < 10 or remnant_count > 12 \
					or remnants == null or remnants.get_child_count() != remnant_count:
				_fail("%s has no dense classic-California pinnate crown" % replacement.name)
				return false
		else:
			var remnant_courses := replacement.get_node("remnant_courses")
			var remnants := replacement.get_node("derived_remnants")
			if remnant_courses.get_child_count() != 12 \
					or remnant_count < 8 or remnant_count > 12 \
					or remnants.get_child_count() != remnant_count:
				_fail("%s has an invalid retained-frond collar" % replacement.name)
				return false
		for index in 7:
			var old_frond := place.get_node_or_null("%s_frond_%d" % [prefix, index]) as GeometryInstance3D
			if old_frond == null or old_frond.visible:
				_fail("%s old strut frond %d was not retired" % [prefix, index])
				return false
	if not saw_added_fronds:
		_fail("%s has no denser crown variants" % place.name)
		return false
	var expected_ring_count := 26 if place.name == &"park_approach" else 0
	if shared_ring_count != expected_ring_count:
		_fail("%s expected %d shared-ring palm feet, found %d" % [
			place.name, expected_ring_count, shared_ring_count])
		return false
	return true


func _check_palmetto_catalog() -> bool:
	var packed := load("res://scenes/world/coastal_palmetto.tscn") as PackedScene
	if packed == null:
		_fail("PRP-PLANT-045 compact fan palmetto does not load")
		return false
	var palmetto := packed.instantiate() as Node3D
	if palmetto == null:
		_fail("PRP-PLANT-045 root is not Node3D")
		return false
	add_child(palmetto)
	for _i in 3:
		await get_tree().process_frame
	var trunk := palmetto.get_node_or_null("short_trunk") as Node3D
	var crown := palmetto.get_node_or_null("broad_fan_crown") as Node3D
	if String(palmetto.get_meta("catalog_id", "")) != "PRP-PLANT-045" \
			or trunk == null or crown == null:
		_fail("PRP-PLANT-045 is missing its catalog identity, trunk or crown")
		return false
	if trunk.scale.y < 4.3 or trunk.scale.y > 4.9 or crown.position.y > 4.7:
		_fail("PRP-PLANT-045 is not the saved short-trunk form")
		return false
	if trunk.scale.x < trunk.scale.y * 2.5 \
			or trunk.scale.z < trunk.scale.y * 2.5:
		_fail("PRP-PLANT-045 lost its stout palmetto trunk proportion")
		return false
	var courses := crown.get_node_or_null("frond_courses")
	var derived := crown.get_node_or_null("derived_fronds")
	var skirt := crown.get_node_or_null("derived_skirt")
	if courses == null or courses.get_child_count() != 14 \
			or derived == null or derived.get_child_count() != 13 \
			or skirt == null or skirt.get_child_count() != 14:
		_fail("PRP-PLANT-045 did not preserve the broad palmetto crown")
		return false
	remove_child(palmetto)
	palmetto.free()
	return true


func _check_date_palm_catalog() -> bool:
	var packed := load("res://scenes/world/classic_california_date_palm.tscn") as PackedScene
	if packed == null:
		_fail("PRP-PLANT-051 classic California date palm does not load")
		return false
	var palm := packed.instantiate() as Node3D
	if palm == null:
		_fail("PRP-PLANT-051 root is not Node3D")
		return false
	add_child(palm)
	for _i in 3:
		await get_tree().process_frame
	var trunk := palm.get_node_or_null("trunk") as Node3D
	var root_flare := palm.get_node_or_null("root_flare") as MeshInstance3D
	var flare_mesh := root_flare.mesh as CylinderMesh if root_flare != null else null
	var crown := palm.get_node_or_null("crown") as Node3D
	var derived := crown.get_node_or_null("derived_fronds") if crown != null else null
	var remnants := crown.get_node_or_null("derived_remnants") if crown != null else null
	var raised_density_fronds := 0
	if derived != null:
		for frond in derived.get_children():
			if int(frond.get_meta("density_copy", 0)) == 1 \
					and float(frond.get_meta("density_lift", 0.0)) >= 0.379 \
					and float(frond.get_meta("density_scale", 1.0)) <= 0.861:
				raised_density_fronds += 1
	if String(palm.get_meta("catalog_id", "")) != "PRP-PLANT-051" \
			or trunk == null or root_flare == null or flare_mesh == null \
			or crown == null \
			or not is_equal_approx(trunk.scale.y, 10.4) \
			or flare_mesh.bottom_radius < 0.299 \
			or flare_mesh.top_radius < 0.229 \
			or not is_equal_approx(flare_mesh.height, 0.48) \
			or not is_equal_approx(root_flare.position.y, 0.24) \
			or not is_equal_approx(crown.position.y, 10.4) \
			or crown.scale.x < 1.279 or crown.scale.z < 1.279 \
			or int(crown.get("extra_frond_count")) != 20 \
			or int(crown.get("remnant_count")) != 12 \
			or int(crown.get("density_multiplier")) != 2 \
			or derived == null or derived.get_child_count() != 64 \
			or raised_density_fronds != 32 \
			or remnants == null or remnants.get_child_count() != 12 \
			or String(crown.get_meta("species_language", "")) \
				!= "classic_california_date_palm":
		_fail("PRP-PLANT-051 does not preserve the approved dense whole-tree form")
		return false
	remove_child(palm)
	palm.free()
	return true


func _check_fern(fern: Node3D, label: String) -> bool:
	if fern == null:
		_fail("%s is not a fern instance" % label)
		return false
	var courses := fern.get_node_or_null("frond_courses")
	var derived := fern.get_node_or_null("derived_fronds")
	if courses == null or derived == null or courses.get_child_count() != 7 \
			or derived.get_child_count() != 7:
		_fail("%s does not preserve seven editable fern courses" % label)
		return false
	if int(fern.get("pinnae_pairs")) < 10:
		_fail("%s is too sparse to read as a fine-pinnaed fern" % label)
		return false
	for frond in derived.get_children():
		var mesh := (frond as MeshInstance3D).mesh as ArrayMesh
		if mesh == null or mesh.get_surface_count() != 2:
			_fail("%s/%s is missing its pinnae or rachis surface" % [label, frond.name])
			return false
		var pinnae_vertices := mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX] as PackedVector3Array
		if pinnae_vertices.size() < 120:
			_fail("%s/%s does not carry dense paired pinnae" % [label, frond.name])
			return false
	return true


func _fail(message: String) -> void:
	push_error("coastal_palm_test: " + message)
	get_tree().quit(1)
