extends Node

## One-off, 2026-09-25: the 34 coastal palms that `coastal_palm_replacements.gd`
## built at the generated feet become editor-owned placements, one
## `coastal_palm.tscn` per palm in `approach_palms.tscn` and
## `boardwalk_palms.tscn`, with Christina's approval of that ownership move.
##
##     godot --headless --path . tools/run.tscn -- _palm_placement_migration
##
## It lets the replacement controller build each wrapper's palms, reads back
## exactly what it built (foot, crown seat, the trunk's turn about its own line,
## bend, crown turn and frond counts, bed and its turn, the accent rings) and
## writes those as each palm's values. The seed is the controller's own
## signature of the palm's name. Dead fronds, new with the Blender crown: none at
## the entrance, one on a quarter of the front-road palms, one to three on the
## Boardwalk. Then it mounts the written set beside the controller and fails if
## any trunk, crown seat or bed is more than a tenth of a millimetre, or 0.0002 in any basis vector,
## from where the controller put it.

const SETS := [
	["res://scenes/world/park_approach.tscn", "res://scenes/world/approach_palms.tscn", "approach_palms"],
	["res://scenes/world/boardwalk.tscn", "res://scenes/world/boardwalk_palms.tscn", "boardwalk_palms"],
]
const PALM := "res://scenes/world/coastal_palm.tscn"
const SET_SCRIPT := "res://scenes/world/coastal_palm_set.gd"
const POSITION_TOLERANCE := 0.0001
const BASIS_TOLERANCE := 0.0002


func _ready() -> void:
	var ok := await _run()
	get_tree().quit(0 if ok else 1)


func _run() -> bool:
	var palm_scene := load(PALM) as PackedScene
	for entry in SETS:
		var wrapper := (load(entry[0]) as PackedScene).instantiate() as Node3D
		add_child(wrapper)
		for _i in 4:
			await get_tree().process_frame
		var controller := wrapper.get_node("authored_additions/coastal_palm_replacements")
		var crowns := controller.get_node("generated_crowns")
		var trunks := controller.get_node("generated_trunks")
		var bases := controller.get_node("generated_bases")
		var set_root := Node3D.new()
		set_root.name = entry[2]
		set_root.set_script(load(SET_SCRIPT))
		set_root.set_meta("catalog_id", "GRP-PARK-007")
		set_root.editor_description = "Coastal palms, one per established foot. Select a palm to move its foot or change its height, lean, trunk bow, crown turn, frond counts or bed; its seed varies the crown."
		var records := {}
		for crown_node in crowns.get_children():
			var crown := crown_node as Node3D
			var prefix := String(crown.name).trim_suffix("_editor_crown")
			var trunk := trunks.get_node(prefix + "_editor_trunk") as Node3D
			var base := bases.get_node(prefix + "_editor_base") as Node3D
			var foot := trunk.position
			var top := crown.position - foot
			var align := Quaternion(Vector3.UP, top.normalized())
			var turn := (align.inverse() * trunk.basis.get_rotation_quaternion()).get_euler().y
			var seed_value := _signature(prefix)
			var walk := prefix.begins_with("walk_palm_")
			var front := prefix.begins_with("front_palm_")
			var deck := prefix.begins_with("deck_palm_")
			var dead := 0
			if deck:
				dead = 1 + seed_value % 3
			elif front and seed_value % 4 == 0:
				dead = 1

			var palm := palm_scene.instantiate(PackedScene.GEN_EDIT_STATE_INSTANCE) as Node3D
			palm.name = prefix
			palm.position = foot
			palm.set("variation_seed", seed_value)
			palm.set("trunk_scene", controller.get("arrival_trunk_scene") if walk
				else controller.get("trunk_scene"))
			palm.set("height", top.y)
			palm.set("lean", Vector2(top.x, top.z))
			palm.set("trunk_turn", rad_to_deg(turn))
			palm.set("bend_strength", float(trunk.get("bend_strength")))
			palm.set("crown_turn", rad_to_deg(crown.rotation.y))
			palm.set("frond_count", 12 + int(crown.get("extra_frond_count")))
			palm.set("stub_count", int(crown.get("remnant_count")))
			palm.set("dead_count", dead)
			palm.set("footing_scene", controller.get("boardwalk_base_scene") if deck
				else controller.get("ground_base_scene"))
			palm.set("footing_turn", rad_to_deg(base.rotation.y))
			if walk or front:
				palm.set("accent_rings_scene", controller.get("arrival_rings_scene"))
			set_root.add_child(palm)
			palm.owner = set_root
			records[prefix] = [trunk.global_transform, crown.global_transform, base.global_transform]

		var packed := PackedScene.new()
		var err := packed.pack(set_root)
		if err == OK:
			err = ResourceSaver.save(packed, entry[1])
		set_root.free()
		if err != OK:
			push_error("migration: could not write %s (%s)" % [entry[1], error_string(err)])
			return false
		print("migration: wrote %d palms to %s" % [records.size(), entry[1]])

		# Mount what was written where the controller sits, and compare.
		var written := (ResourceLoader.load(entry[1], "", ResourceLoader.CACHE_MODE_IGNORE)
			as PackedScene).instantiate() as Node3D
		wrapper.get_node("authored_additions").add_child(written)
		for _i in 4:
			await get_tree().process_frame
		var worst_position := 0.0
		var worst_basis := 0.0
		for prefix in records:
			var palm := written.get_node_or_null(NodePath(prefix)) as Node3D
			if palm == null:
				push_error("migration: %s missing from %s" % [prefix, entry[1]])
				return false
			var now := [palm.get_node("trunk").global_transform,
				palm.get_node("crown").global_transform,
				palm.get_node("footing").global_transform]
			for k in 3:
				var was: Transform3D = records[prefix][k]
				var is_now: Transform3D = now[k]
				worst_position = maxf(worst_position, was.origin.distance_to(is_now.origin))
				for axis in 3:
					worst_basis = maxf(worst_basis, (was.basis[axis] - is_now.basis[axis]).length())
		print("migration: %s: farthest trunk, crown seat or bed %.6f m and %.6f in basis from the controller's" % [
			entry[2], worst_position, worst_basis])
		wrapper.queue_free()
		await get_tree().process_frame
		if worst_position > POSITION_TOLERANCE or worst_basis > BASIS_TOLERANCE:
			push_error("migration: %s moved a palm" % entry[2])
			return false
	return true


## `coastal_palm_replacements.gd`'s signature of a palm's name.
func _signature(value: String) -> int:
	var result := 0
	for index in value.length():
		result = (result * 31 + value.unicode_at(index)) & 0x7fffffff
	return result
