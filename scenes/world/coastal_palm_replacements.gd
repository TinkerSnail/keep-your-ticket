@tool
extends Node3D

## Keeps every established palm foot while replacing the rod-like generated
## trunk and sphere-and-strut crown with directly editable shared sources.
## Variation is deterministic, small, and derived from each existing palm.

@export var crown_scene: PackedScene
@export var arrival_crown_scene: PackedScene
@export var trunk_scene: PackedScene
@export var arrival_trunk_scene: PackedScene
@export var ground_base_scene: PackedScene
@export var boardwalk_base_scene: PackedScene
@export var arrival_rings_scene: PackedScene
@export var source_root_path := NodePath("../..")

const StaticMerge := preload("res://scripts/static_merge.gd")

var _queued := false


func _ready() -> void:
	_queue_rebuild()


func _queue_rebuild() -> void:
	if _queued or not is_inside_tree():
		return
	_queued = true
	call_deferred("_rebuild")


func _rebuild() -> void:
	_queued = false
	var source_root := get_node_or_null(source_root_path) as Node3D
	var crown_output := get_node_or_null("generated_crowns") as Node3D
	var trunk_output := get_node_or_null("generated_trunks") as Node3D
	var base_output := get_node_or_null("generated_bases") as Node3D
	if source_root == null or crown_output == null or trunk_output == null \
			or base_output == null \
			or crown_scene == null or arrival_crown_scene == null \
			or trunk_scene == null \
			or arrival_trunk_scene == null or ground_base_scene == null \
			or boardwalk_base_scene == null or arrival_rings_scene == null:
		return
	for child in crown_output.get_children():
		child.free()
	for child in trunk_output.get_children():
		child.free()
	for child in base_output.get_children():
		child.free()
	for child in source_root.get_children():
		var crown := child as GeometryInstance3D
		if crown == null or not String(crown.name).contains("palm_") \
				or not String(crown.name).ends_with("_crown"):
			continue
		var prefix := String(crown.name).trim_suffix("_crown")
		var trunk := source_root.get_node_or_null(prefix + "_trunk") as CSGBox3D
		if trunk == null:
			continue
		var endpoints := _trunk_endpoints(trunk, crown.position)
		var base: Vector3 = endpoints[0]
		var old_top: Vector3 = endpoints[1]
		var signature := _signature(prefix)
		# Every palm gains 10–27cm; the arrival ends receive another 75cm of
		# common height while retaining the same small difference tree to tree.
		var height_gain := 0.10 + float(signature % 5) * 0.042
		var old_lateral := Vector3(old_top.x - base.x, 0.0, old_top.z - base.z)
		var lateral_offset := Vector3.ZERO
		if prefix.begins_with("walk_palm_"):
			height_gain += 0.75
			# The old rods leaned as much as 60cm in arbitrary directions. Reframe
			# the paired rows as a deliberate 55cm inward allée arch, with only a
			# trace of their former fore/aft variation.
			lateral_offset.x = -signf(base.x) * 0.55
			if old_lateral.length_squared() > 0.0001:
				lateral_offset.z = old_lateral.normalized().z * 0.12
		elif old_lateral.length_squared() > 0.0001:
			# Elsewhere the inherited lean direction survives, but at one fifth of
			# its old reach so the editable curved shaft does the visible work.
			lateral_offset = old_lateral.normalized() \
				* (0.08 + float(signature % 4) * 0.012)
		var top := base + Vector3.UP * (old_top.y - base.y + height_gain) \
			+ lateral_offset
		var direction := (top - base).normalized()
		var trunk_length := base.distance_to(top)

		crown.visible = false
		trunk.visible = false
		var first_frond := source_root.get_node_or_null(prefix + "_frond_0") as GeometryInstance3D
		var yaw := 0.0
		if first_frond != null:
			first_frond.visible = false
			var outward := first_frond.position - crown.position
			yaw = atan2(-outward.z, outward.x)
		for candidate in source_root.get_children():
			if String(candidate.name).begins_with(prefix + "_frond_") \
					and candidate is GeometryInstance3D:
				(candidate as GeometryInstance3D).visible = false

		var selected_trunk_scene := arrival_trunk_scene \
			if prefix.begins_with("walk_palm_") else trunk_scene
		var trunk_replacement := selected_trunk_scene.instantiate() as Node3D
		trunk_replacement.name = prefix + "_editor_trunk"
		var bend_strength := 0.65 + float(signature % 5) * 0.12
		if prefix.begins_with("walk_palm_"):
			bend_strength *= 1.15
		trunk_replacement.set("bend_strength", bend_strength)
		trunk_output.add_child(trunk_replacement)
		trunk_replacement.position = base
		trunk_replacement.quaternion = Quaternion(Vector3.UP, direction)
		if prefix.begins_with("walk_palm_"):
			# Aim the source curve's positive local X bow at the opposite row.
			# Strength still varies by tree, avoiding copied mirror pairs.
			var inward := Vector3(-signf(base.x), 0.0, 0.0)
			var bend_target := (inward - direction * inward.dot(direction)).normalized()
			# A positive local-Y rotation carries +X toward -Z. The old expression
			# omitted that minus sign, so the metadata said inward while the emitted
			# shaft bowed to the reflected, outward side of the tangent plane.
			var bend_yaw := atan2(-bend_target.dot(trunk_replacement.basis.z),
				bend_target.dot(trunk_replacement.basis.x))
			trunk_replacement.rotate_object_local(Vector3.UP, bend_yaw)
			trunk_replacement.set_meta("bend_direction", bend_target)
		else:
			trunk_replacement.rotate_object_local(Vector3.UP,
				fmod(float(signature) * 0.73, TAU))
		trunk_replacement.scale = Vector3.ONE * trunk_length
		trunk_replacement.set_meta("source_base", base)
		trunk_replacement.set_meta("source_top", old_top)
		trunk_replacement.set_meta("new_top", top)
		trunk_replacement.set_meta("height_gain", height_gain)
		trunk_replacement.set_meta("lateral_offset", lateral_offset)

		var selected_base_scene := boardwalk_base_scene \
			if prefix.begins_with("deck_palm_") else ground_base_scene
		var base_replacement := selected_base_scene.instantiate() as Node3D
		base_replacement.name = prefix + "_editor_base"
		base_output.add_child(base_replacement)
		base_replacement.position = base
		if not prefix.begins_with("deck_palm_"):
			base_replacement.rotation.y = fmod(float(signature) * 0.41, TAU)
		if prefix.begins_with("walk_palm_") or prefix.begins_with("front_palm_"):
			# The arrival allée and the front-road row share one directly editable
			# planted-ring source. The road feet keep their established positions and
			# lower trunks; only the planting hierarchy is carried across.
			var arrival_rings := arrival_rings_scene.instantiate() as Node3D
			arrival_rings.name = "arrival_accent_rings"
			base_replacement.add_child(arrival_rings)
			var flowers := base_replacement.get_node_or_null("flowers") as Node3D
			var center_height_scale := float(arrival_rings.get_meta(
				"center_height_scale", 1.0))
			if flowers != null:
				flowers.scale.y = center_height_scale
				flowers.set_meta("arrival_height_scale", center_height_scale)
			var fern_pockets := base_replacement.get_node_or_null(
				"fern_pockets") as Node3D
			var fern_scale := float(arrival_rings.get_meta("fern_scale", 1.0))
			if fern_pockets != null:
				for fern in fern_pockets.get_children():
					(fern as Node3D).scale *= fern_scale
				fern_pockets.set_meta("arrival_fern_scale", fern_scale)

		var selected_crown_scene := arrival_crown_scene \
			if prefix.begins_with("walk_palm_") else crown_scene
		var replacement := selected_crown_scene.instantiate() as Node3D
		replacement.name = prefix + "_editor_crown"
		if prefix.begins_with("walk_palm_"):
			# The entrance is the dense classic-California date-palm reading:
			# thirty to thirty-two live feather fronds in overlapping age
			# courses. Other coastal palms keep the lighter twelve-frond core.
			replacement.set("extra_frond_count", 18 + signature % 3)
			replacement.set("remnant_count", 10 + signature % 3)
		else:
			var density_bucket := signature % 8
			replacement.set("extra_frond_count",
				0 if density_bucket < 4 else (1 if density_bucket < 7 else 2))
			replacement.set("remnant_count", 8 + signature % 5)
		crown_output.add_child(replacement)
		replacement.position = top
		replacement.rotation.y = yaw
	# In the running game only: each crown and footing draws as one mesh. The
	# leaf-by-leaf sources stay in the tree, hidden, and the editor never merges.
	StaticMerge.merge_children_later(self, [crown_output, base_output])


func _trunk_endpoints(trunk: CSGBox3D, crown_position: Vector3) -> Array[Vector3]:
	var axis := trunk.basis.z.normalized()
	var end_a := trunk.position + axis * trunk.size.z * 0.5
	var end_b := trunk.position - axis * trunk.size.z * 0.5
	if end_a.distance_to(crown_position) < end_b.distance_to(crown_position):
		return [end_b, end_a]
	return [end_a, end_b]


func _signature(value: String) -> int:
	var result := 0
	for index in value.length():
		result = (result * 31 + value.unicode_at(index)) & 0x7fffffff
	return result
