extends Node

## Focused palm acceptance: every established foot remains fixed while each
## editor-owned `coastal_palm.tscn` placement provides tightly bounded height,
## bend and lean, and its Blender crown (`palm_crown.tscn`) shows the fronds,
## stubs and dead fronds its counts ask for, no two crowns alike. Arrival pairs
## use tall near-straight shafts and dense, groomed classic-California pinnate
## crowns; Boardwalk palms carry one to three dead fronds; both former fan-palm
## readings remain outside the standing world.


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
	print("PASS: 34 fixed-foot coastal palms, each an editor-owned placement, keep their layered bases, bounded heights, leans and the arrival row's inward bow; the sixteen arrival palms carry 30–32-frond groomed crowns, the Boardwalk palms one to three dead fronds, and no two of the 34 Blender crowns are alike; PRP-PLANT-051 still doubles its head to 64 fronds; the former fan forms have no standing placement; all 26 arrival and front-road feet keep their planting rings and every opening remains clear")
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
	var set_name := "approach_palms" if place.name == &"park_approach" else "boardwalk_palms"
	var palms := place.get_node_or_null("authored_additions/" + set_name)
	if palms == null:
		_fail("%s has no editor-owned palm set %s" % [place.name, set_name])
		return false
	if palms.get_child_count() != expected_count:
		_fail("%s expected %d palms, found %d" % [place.name, expected_count, palms.get_child_count()])
		return false
	var feet: Dictionary = ESTABLISHED_FEET[set_name]
	if feet.size() != expected_count:
		_fail("%s has %d established feet on record, not %d" % [set_name, feet.size(), expected_count])
		return false
	# The generator emits no stick palm: the placements own every foot. Its
	# output is flat under the wrapper, so a retired name would be a child here.
	var stick_name := RegEx.create_from_string("^(walk|front|deck)_palm_.+_(trunk|crown|frond_\\d+)$")
	for child in place.get_children():
		if stick_name.search(String(child.name)) != null:
			_fail("%s still carries the generator's stick palm part %s" % [place.name, child.name])
			return false

	var saw_added_fronds := false
	var shared_ring_count := 0
	var crowns_seen := {}
	var frond_sets := {}
	for palm_node in palms.get_children():
		var palm := palm_node as Node3D
		var prefix := String(palm.name)
		if palm.scene_file_path != "res://scenes/world/coastal_palm.tscn":
			_fail("%s is not a placed coastal_palm.tscn" % prefix)
			return false
		if not feet.has(prefix):
			_fail("%s is not one of the established palm feet" % prefix)
			return false
		var source_base: Vector3 = feet[prefix][0]
		var source_height: float = feet[prefix][1]
		var new_trunk := palm.get_node_or_null("trunk") as Node3D
		var new_base := palm.get_node_or_null("footing") as Node3D
		var crown := palm.get_node_or_null("crown") as Node3D
		if new_trunk == null or new_base == null or crown == null:
			_fail("%s is missing its trunk, bed or crown" % prefix)
			return false
		# Measured in the wrapper's frame, so moving the set moves every foot.
		var foot := place.to_local(palm.global_position)
		if foot.distance_to(source_base) > FOOT_TOLERANCE:
			_fail("%s moved its established foot %.4fm, to %s" % [
				prefix, foot.distance_to(source_base), foot])
			return false
		if not new_trunk.global_position.is_equal_approx(palm.global_position) \
				or not new_base.global_position.is_equal_approx(palm.global_position):
			_fail("%s trunk or bed is detached from its established foot" % prefix)
			return false
		if not _check_footing(prefix, new_base):
			return false
		var uses_shared_rings := prefix.begins_with("walk_palm_") \
			or prefix.begins_with("front_palm_")
		if uses_shared_rings:
			shared_ring_count += 1

		var seat := palm.call("seat") as Vector3
		var height_gain := seat.y - source_height
		# The seat's offset across from the point straight above the foot.
		var lateral_offset := Vector3(seat.x, 0.0, seat.z)
		if prefix.begins_with("walk_palm_"):
			if height_gain < 0.849 or height_gain > 1.019:
				_fail("%s height gain %.3fm exceeds the taller arrival band" % [prefix, height_gain])
				return false
		elif not prefix.begins_with("front_palm_") \
				and new_base.get_node_or_null("arrival_accent_rings") != null:
			_fail("%s incorrectly carries the arrival/front-road planting rings" % prefix)
			return false
		elif height_gain < 0.099 or height_gain > 0.269:
			_fail("%s height gain %.3fm exceeds the non-arrival band" % [prefix, height_gain])
			return false
		var trunk_mesh := new_trunk.get_node("derived_trunk") as MeshInstance3D
		if trunk_mesh.mesh == null or trunk_mesh.mesh.get_surface_count() != 1:
			_fail("%s is missing its tapered trunk surface" % prefix)
			return false
		if prefix.begins_with("walk_palm_"):
			# The paired rows arch inward: the seat sits 55cm toward the opposite
			# row and hardly moves along the walk.
			if not is_equal_approx(lateral_offset.x, -signf(source_base.x) * 0.55) \
					or absf(lateral_offset.z) > 0.121:
				_fail("%s exceeds the restrained arrival-row lean" % prefix)
				return false
			var inward := Vector3(-signf(source_base.x), 0.0, 0.0)
			# Check the emitted shaft: ring six is near mid-height, where the bow
			# reaches its clearest offset from the straight foot-to-seat chord.
			var trunk_vertices := trunk_mesh.mesh.surface_get_arrays(0)[
				Mesh.ARRAY_VERTEX] as PackedVector3Array
			var middle_ring := 6
			var middle_center := Vector3.ZERO
			for side_index in 8:
				middle_center += trunk_mesh.to_global(
					trunk_vertices[middle_ring * 8 + side_index])
			middle_center /= 8.0
			var chord_point := palm.global_position.lerp(
				palm.to_global(seat), float(middle_ring) / 13.0)
			if (middle_center - chord_point).dot(inward) < 0.04:
				_fail("%s emitted shaft bends away from the opposite row" % prefix)
				return false
		elif lateral_offset.length() < 0.079 or lateral_offset.length() > 0.117:
			_fail("%s exceeds its restrained non-arrival lean" % prefix)
			return false

		# The Blender crown sits on the seat, and shows what its counts say.
		if not crown.position.is_equal_approx(seat) \
				or crown.scene_file_path != "res://scenes/world/palm_crown.tscn" \
				or crown.get_node_or_null("model") == null:
			_fail("%s crown is not the Blender palm crown on its trunk's seat" % prefix)
			return false
		if String(crown.get_meta("species_language", "")) != "classic_california_date_palm":
			_fail("%s crown lost its classic-California species language" % prefix)
			return false
		var fronds := int(crown.get("frond_count"))
		var stubs := int(crown.get("stub_count"))
		var dead := int(crown.get("dead_count"))
		var shown := crown.call("shown_counts") as Dictionary
		if int(shown["live"]) != fronds or int(shown["remnant"]) != stubs \
				or int(shown["dead"]) != dead or int(shown["density"]) != 0:
			_fail("%s crown shows %s, not its %d fronds, %d stubs and %d dead" % [
				prefix, shown, fronds, stubs, dead])
			return false
		saw_added_fronds = saw_added_fronds or fronds > 12
		if prefix.begins_with("walk_palm_"):
			if fronds < 30 or fronds > 32 or stubs < 10 or stubs > 12 or dead != 0:
				_fail("%s has no dense, groomed classic-California crown" % prefix)
				return false
		elif fronds < 12 or fronds > 14 or stubs < 8 or stubs > 12:
			_fail("%s has an invalid light crown or retained-frond collar" % prefix)
			return false
		elif prefix.begins_with("front_palm_") and dead > 1:
			_fail("%s carries more than one dead frond on the front road" % prefix)
			return false
		elif prefix.begins_with("deck_palm_") and (dead < 1 or dead > 3):
			_fail("%s Boardwalk palm lacks its one to three dead fronds" % prefix)
			return false
		# No two crowns alike: which fronds show and how the first is tipped.
		var key := []
		var chosen := []
		for part in crown.get_node("model").get_children():
			if part is MeshInstance3D and bool(part.get_meta("shown", false)):
				key.append(String(part.name))
				key.append((part as Node3D).transform.basis.x.snappedf(0.0001))
				chosen.append(String(part.name))
		frond_sets[chosen] = true
		if crowns_seen.has(key):
			_fail("%s carries the same crown as %s" % [prefix, crowns_seen[key]])
			return false
		crowns_seen[key] = prefix
	if not saw_added_fronds:
		_fail("%s has no denser crown variants" % place.name)
		return false
	print("%s: %d palms on their established feet, no generator stick palm, %d different choices of fronds, stubs and dead fronds" % [
		place.name, palms.get_child_count(), frond_sets.size()])
	var expected_ring_count := 26 if place.name == &"park_approach" else 0
	if shared_ring_count != expected_ring_count:
		_fail("%s expected %d shared-ring palm feet, found %d" % [
			place.name, expected_ring_count, shared_ring_count])
		return false
	return true


## How far a foot may sit from its record: far below any move made in the
## editor, far above float noise through the wrapper's transform.
const FOOT_TOLERANCE := 0.0005

## The 34 established feet, in the wrapper's frame, and the height of the stick
## trunk each used to carry, which the approved height bands are measured from.
## Taken on 2026-09-25 from the placements in `approach_palms.tscn` and
## `boardwalk_palms.tscn`, each within 0.02mm of the foot of the stick palm
## `gen_props.gd` emitted there, before the generator stopped emitting them.
## The sub-millimetre offsets are those sticks' seam displacement, kept as found.
const ESTABLISHED_FEET := {
	"approach_palms": {
		"walk_palm_0_w": [Vector3(-11.497, 0.0029997826, 224.00302), 8.5],
		"walk_palm_0_e": [Vector3(11.5, 0.0, 224.0), 9.9],
		"walk_palm_1_w": [Vector3(-11.497751, 0.0022501945, 212.00224), 10.6],
		"walk_palm_1_e": [Vector3(11.5045, 0.0044999123, 212.00449), 9.2],
		"walk_palm_2_w": [Vector3(-11.498499, 0.0015001297, 200.0015), 9.9],
		"walk_palm_2_e": [Vector3(11.50375, 0.0037498474, 200.00375), 8.5],
		"walk_palm_3_w": [Vector3(-11.49925, 0.000749588, 188.00075), 9.2],
		"walk_palm_3_e": [Vector3(11.503, 0.0029993057, 188.00302), 10.6],
		"walk_palm_4_w": [Vector3(-11.5, 0.0, 176.0), 8.5],
		"walk_palm_4_e": [Vector3(11.50225, 0.0022501945, 176.00224), 9.9],
		"walk_palm_5_w": [Vector3(-11.495501, 0.0044999123, 164.00449), 10.6],
		"walk_palm_5_e": [Vector3(11.501501, 0.0014996529, 164.0015), 9.2],
		"walk_palm_6_w": [Vector3(-11.496249, 0.0037493706, 152.00374), 9.9],
		"walk_palm_6_e": [Vector3(11.50075, 0.00075006485, 152.00073), 8.5],
		"walk_palm_7_w": [Vector3(-11.497, 0.0029997826, 140.00299), 9.2],
		"walk_palm_7_e": [Vector3(11.5, 4.7683716e-07, 140.0), 10.6],
		"front_palm_0": [Vector3(-73.99774, 0.0022501945, 242.00224), 8.0],
		"front_palm_1": [Vector3(-60.9955, 0.0044999123, 242.0045), 8.8],
		"front_palm_2": [Vector3(-47.998505, 0.0015001297, 242.0015), 9.6],
		"front_palm_3": [Vector3(-34.99625, 0.0037498474, 242.00374), 8.0],
		"front_palm_4": [Vector3(-21.99925, 0.00075006485, 242.00075), 8.8],
		"front_palm_7": [Vector3(17.003002, 0.0029997826, 242.00299), 8.8],
		"front_palm_8": [Vector3(30.0, -4.7683716e-07, 242.0), 9.6],
		"front_palm_9": [Vector3(43.002247, 0.0022501945, 242.00224), 8.0],
		"front_palm_10": [Vector3(56.0045, 0.0044999123, 242.0045), 8.8],
		"front_palm_11": [Vector3(69.0015, 0.0015001297, 242.0015), 9.6],
	},
	"boardwalk_palms": {
		"deck_palm_0": [Vector3(-104.99625, -5.99625, -65.99625), 8.0],
		"deck_palm_1": [Vector3(-104.99925, -5.99925, -51.99925), 8.9],
		"deck_palm_2": [Vector3(-104.996994, -5.9969997, -37.997), 9.8],
		"deck_palm_3": [Vector3(-105.0, -6.0, -24.0), 8.0],
		"deck_palm_4": [Vector3(-104.99776, -5.9977503, 20.00225), 8.9],
		"deck_palm_5": [Vector3(-104.9955, -5.9955, 34.0045), 9.8],
		"deck_palm_6": [Vector3(-104.9985, -5.9985, 48.0015), 8.0],
		"deck_palm_7": [Vector3(-104.99624, -5.99625, 62.003746), 8.9],
	},
}


func _check_footing(prefix: String, new_base: Node3D) -> bool:
	var flowers := new_base.get_node_or_null("flowers")
	var flower_clusters: Array[Node] = []
	if flowers != null:
		for flower_child in flowers.get_children():
			if String(flower_child.name).ends_with("_cluster"):
				flower_clusters.append(flower_child)
	if flowers == null or flower_clusters.size() != 3 \
			or flowers.get_node_or_null("planted_collar") == null:
		_fail("%s is missing its three landscaped flower clusters" % prefix)
		return false
	if not prefix.begins_with("deck_palm_"):
		var planted_collar := flowers.get_node("planted_collar") as MeshInstance3D
		if planted_collar.mesh is TorusMesh \
				or flowers.get_node_or_null("planted_lobe_east") == null \
				or flowers.get_node_or_null("planted_lobe_south") == null:
			_fail("%s has returned to a circular donut planting collar" % prefix)
			return false
		if new_base.get_node_or_null("soil_patch_east") == null \
				or new_base.get_node_or_null("soil_patch_south") == null:
			_fail("%s has returned to one circular soil disc" % prefix)
			return false
		var fern_pockets := new_base.get_node_or_null("fern_pockets")
		var rosettes := new_base.get_node_or_null("border_rosettes")
		if fern_pockets == null or fern_pockets.get_child_count() != 6 \
				or rosettes == null or rosettes.get_child_count() != 8:
			_fail("%s is missing its loose fern or rosette sweep" % prefix)
			return false
		var rosette_radii: Array[float] = []
		for rosette in rosettes.get_children():
			var rosette_position := (rosette as Node3D).position
			rosette_radii.append(Vector2(rosette_position.x,
				rosette_position.z).length())
		rosette_radii.sort()
		if rosette_radii[-1] - rosette_radii[0] < 0.08:
			_fail("%s rosettes have returned to an even circular ring" % prefix)
			return false
	for cluster in flower_clusters:
		var bloom_count := 0
		for part in cluster.get_children():
			if String(part.name).begins_with("bloom_"):
				bloom_count += 1
		if cluster.get_node_or_null("foliage") == null or bloom_count < 4:
			_fail("%s/%s is not a dense bedding cluster" % [
				prefix, cluster.name])
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
			_fail("%s is missing its Boardwalk timber tree box" % prefix)
			return false
		for accent_name in [&"hakone_nw", &"hakone_se", &"purple_ne", &"purple_sw"]:
			var accent := color_accents.get_node_or_null(NodePath(accent_name)) as Node3D
			if accent == null or accent.position.y < 0.37 or accent.scale.y < 0.5 \
					or Vector2(accent.position.x, accent.position.z).length() < 0.38:
				_fail("%s/%s does not preserve the open-center contrast pocket" % [
					prefix, accent_name])
				return false
		for fern in fern_ring.get_children():
			if (fern as Node3D).position.y < 0.38 or (fern as Node3D).scale.y < 1.0:
				_fail("%s/%s disappears below the Boardwalk cap rail" % [
					prefix, fern.name])
				return false
			if not _check_fern(fern as Node3D,
					"%s/%s" % [prefix, fern.name]):
				return false
		for rosette in border_rosettes.get_children():
			if (rosette as Node3D).position.y < 0.36 or (rosette as Node3D).scale.y < 0.78:
				_fail("%s/%s disappears below the Boardwalk cap rail" % [
					prefix, rosette.name])
				return false
		for cluster in flower_clusters:
			if (cluster as Node3D).position.y < 0.34:
				_fail("%s/%s disappears below the Boardwalk cap rail" % [
					prefix, cluster.name])
				return false
	else:
		var fern_pockets := new_base.get_node_or_null("fern_pockets")
		var border_rosettes := new_base.get_node_or_null("border_rosettes")
		if new_base.get_node_or_null("soil_patch") == null \
				or fern_pockets == null or fern_pockets.get_child_count() != 6 \
				or border_rosettes == null or border_rosettes.get_child_count() != 8:
			_fail("%s is missing its layered lawn planting" % prefix)
			return false
		for fern in fern_pockets.get_children():
			if not _check_fern(fern as Node3D,
					"%s/%s" % [prefix, fern.name]):
				return false
	var uses_shared_rings := prefix.begins_with("walk_palm_") \
		or prefix.begins_with("front_palm_")
	if uses_shared_rings:
		var arrival_rings := new_base.get_node_or_null("arrival_accent_rings")
		var arrival_fern_pockets := new_base.get_node_or_null("fern_pockets")
		var hakone_clumps := new_base.get_node_or_null(
			"arrival_accent_rings/japanese_forest_grass_inner_ring/clumps")
		var purple_sprigs := new_base.get_node_or_null(
			"arrival_accent_rings/purple_heart_outer_ring")
		if arrival_rings == null or hakone_clumps == null \
				or hakone_clumps.get_child_count() != 10 \
				or purple_sprigs == null or purple_sprigs.get_child_count() != 36:
			_fail("%s is missing its two arrival planting rings" % prefix)
			return false
		if (purple_sprigs as Node3D).scale.x > 0.71:
			_fail("%s Purple Heart ring is no longer tucked under the Hakone skirt" %
				prefix)
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
				prefix)
			return false
		if flowers.scale.y < 3.1 \
				or float(flowers.get_meta("arrival_height_scale", 0.0)) < 3.1:
			_fail("%s mixed center no longer rises above the forest grass" %
				prefix)
			return false
		if arrival_fern_pockets == null \
				or float(arrival_fern_pockets.get_meta(
					"arrival_fern_scale", 0.0)) < 1.99:
			_fail("%s arrival ferns are no longer doubled in size" %
				prefix)
			return false
		for fern in arrival_fern_pockets.get_children():
			if (fern as Node3D).scale.x < 1.35:
				_fail("%s/%s did not receive the doubled arrival scale" % [
					prefix, fern.name])
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
	var model := crown.get_node_or_null("model") as Node3D if crown != null else null
	var shown := crown.call("shown_counts") as Dictionary \
		if crown != null and crown.has_method("shown_counts") else {}
	# The second shell: each copy is its live frond carried by one transform,
	# which must lift it at least 0.38 m and draw it in to 0.86 or less.
	var density := model.get_node_or_null("density") if model != null else null
	var raised_density_fronds := 0
	if density != null:
		for copy in density.get_children():
			var source := model.get_node_or_null(
				String(copy.name).get_slice("_density_", 0)) as Node3D
			if source == null or int(copy.get_meta("density_copy", 0)) != 1:
				continue
			var shell := (copy as Node3D).transform * source.transform.affine_inverse()
			if shell.origin.y >= 0.379 and shell.basis.get_scale().x <= 0.861 \
					and shell.basis.get_scale().z <= 0.861:
				raised_density_fronds += 1
	if String(palm.get_meta("catalog_id", "")) != "PRP-PLANT-051" \
			or trunk == null or root_flare == null or flare_mesh == null \
			or crown == null or model == null \
			or crown.scene_file_path != "res://scenes/world/palm_crown.tscn" \
			or not is_equal_approx(trunk.scale.y, 10.4) \
			or flare_mesh.bottom_radius < 0.299 \
			or flare_mesh.top_radius < 0.229 \
			or not is_equal_approx(flare_mesh.height, 0.48) \
			or not is_equal_approx(root_flare.position.y, 0.24) \
			or not is_equal_approx(crown.position.y, 10.4) \
			or crown.scale.x * model.scale.x < 1.279 \
			or crown.scale.z * model.scale.z < 1.279 \
			or int(crown.get("frond_count")) != 32 \
			or int(crown.get("stub_count")) != 12 \
			or int(crown.get("dead_count")) != 0 \
			or int(crown.get("density_multiplier")) != 2 \
			or int(shown.get("live", 0)) != 32 or int(shown.get("extra", 0)) != 20 \
			or int(shown.get("live", 0)) + int(shown.get("density", 0)) != 64 \
			or raised_density_fronds != 32 \
			or int(shown.get("remnant", 0)) != 12 or int(shown.get("dead", -1)) != 0 \
			or String(crown.get_meta("species_language", "")) \
				!= "classic_california_date_palm":
		_fail("PRP-PLANT-051 does not preserve the approved dense whole-tree form: " \
			+ "crown shows %s, %d raised density fronds" % [shown, raised_density_fronds])
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
