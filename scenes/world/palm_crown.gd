@tool
extends Node3D

## The coastal palm crown, PRP-COAST-006. Every frond's shape is Christina's, in
## `assets/source/props/palm_crown.blend`, and arrives as one node per frond in
## `assets/props/palm_crown.glb` (`model`). This script only chooses which of
## them a tree shows and turns each a few degrees, from `variation_seed`, so the 34 coastal
## palms carry 34 different crowns. Nothing is random while the game runs: the
## same seed gives the same crown on every visit and in every photograph.
##
## Always shown: the heart and the three youngest fronds (the spear and the two
## young). `frond_count` past those three is filled from all 29 mature and old
## fronds, in the crown's own proportion of old to mature, spread evenly round
## the trunk from a starting angle the seed sets; `stub_count` stubs are spread
## the same way, and the seed picks which `dead_count` of the three hanging dead
## fronds show. A frond's kind is the `kyt_course_blade` it carried in Blender,
## which the GLB brings as metadata. The seed also turns every frond up to
## `jitter_degrees` round the trunk and up or down, and scales the whole crown by
## up to `size_variation`. The random draws are the same in number whatever the
## counts, so changing a count never reshuffles the rest of the crown.

@export var variation_seed := 0:
	set(value):
		variation_seed = value
		_queue_rebuild()
@export_range(12, 32, 1) var frond_count := 12:
	set(value):
		frond_count = value
		_queue_rebuild()
@export_range(0, 12, 1) var stub_count := 9:
	set(value):
		stub_count = value
		_queue_rebuild()
@export_range(0, 3, 1) var dead_count := 0:
	set(value):
		dead_count = value
		_queue_rebuild()
@export_range(0.0, 15.0, 0.5) var jitter_degrees := 4.0:
	set(value):
		jitter_degrees = value
		_queue_rebuild()
@export_range(0.0, 0.2, 0.01) var size_variation := 0.05:
	set(value):
		size_variation = value
		_queue_rebuild()
## Two interleaves a second, raised and inset copy of every live frond, as the
## Godot-course crown did for the 64-frond catalog date palm (PRP-PLANT-051).
@export_range(1, 2, 1) var density_multiplier := 1:
	set(value):
		density_multiplier = value
		_queue_rebuild()

const DENSITY_SCALE := 0.86
const DENSITY_LIFT := 0.38

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
	var model := get_node_or_null("model") as Node3D
	if model == null:
		return
	var parts: Array[MeshInstance3D] = []
	for child in model.get_children():
		if child is MeshInstance3D:
			parts.append(child)
	parts.sort_custom(func(a: Node, b: Node) -> bool: return String(a.name) < String(b.name))

	for part in parts:
		if not part.has_meta("rest"):
			part.set_meta("rest", part.transform)
	var by_kind := {}
	for part in parts:
		var kind := _kind(part)
		if not by_kind.has(kind):
			by_kind[kind] = []
		by_kind[kind].append(part)
	var mature: Array = by_kind.get("mature", [])
	var old: Array = by_kind.get("old", [])
	var always: Array = by_kind.get("spear", []) + by_kind.get("young", [])
	var wanted := clampi(frond_count - always.size(), 0, mature.size() + old.size())
	var old_wanted := mini(roundi(wanted * old.size() / float(maxi(mature.size() + old.size(), 1))),
		old.size())

	var rng := RandomNumberGenerator.new()
	rng.seed = variation_seed
	var shown := {}
	for part in always:
		shown[part] = true
	for part in _spread(mature, wanted - old_wanted, rng) + _spread(old, old_wanted, rng) \
			+ _spread(by_kind.get("stub", []), stub_count, rng):
		shown[part] = true
	var dead := _shuffled(by_kind.get("dead", []), rng)
	for index in mini(dead_count, dead.size()):
		shown[dead[index]] = true
	var size := 1.0 + rng.randf_range(-1.0, 1.0) * size_variation

	var live: Array[MeshInstance3D] = []
	for part in parts:
		var rest := part.get_meta("rest") as Transform3D
		# Two draws for every part, shown or not.
		var turn := deg_to_rad(rng.randf_range(-1.0, 1.0) * jitter_degrees)
		var tilt := deg_to_rad(rng.randf_range(-1.0, 1.0) * jitter_degrees)
		var part_name := String(part.name)
		if part_name == "heart":
			part.transform = rest
			part.set_meta("shown", true)
			continue
		part.visible = shown.get(part, false)
		# Kept apart from `visible`: in the game StaticMerge folds the shown
		# fronds into one mesh and hides them all.
		part.set_meta("shown", part.visible)
		# Each frond grows from the crown's centre, so it turns about the trunk's
		# axis and tips up or down about the level line square to its heading.
		var centre := rest * part.mesh.get_aabb().get_center()
		var heading := Vector3(centre.x, 0.0, centre.z).normalized()
		var basis := Basis(Vector3.UP, turn)
		if heading.length_squared() > 0.5:
			basis = basis * Basis(heading.cross(Vector3.UP).normalized(), tilt)
		part.transform = Transform3D(basis, Vector3.ZERO) * rest
		if part.visible and _kind(part) not in ["stub", "dead"]:
			live.append(part)
	model.scale = Vector3.ONE * size

	var density := model.get_node_or_null("density") as Node3D
	if density != null:
		model.remove_child(density)
		density.free()
	if density_multiplier > 1:
		density = Node3D.new()
		density.name = "density"
		model.add_child(density)
		# A second shell lifted and drawn inward, turned half a frond's spacing,
		# fills the head's upper volume: the rule the Godot-course crown used.
		var step := TAU / float(maxi(live.size() * density_multiplier, 1))
		for copy_index in range(1, density_multiplier):
			var shell := Transform3D(Basis(Vector3.UP, step * copy_index).scaled(
				Vector3(DENSITY_SCALE, 0.92, DENSITY_SCALE)), Vector3.UP * DENSITY_LIFT)
			for part in live:
				var copy := MeshInstance3D.new()
				copy.name = "%s_density_%d" % [part.name, copy_index]
				copy.mesh = part.mesh
				copy.transform = shell * part.transform
				copy.set_meta("density_copy", copy_index)
				density.add_child(copy)


## How many fronds, stubs and dead fronds this crown shows, for tests and tools.
func shown_counts() -> Dictionary:
	var counts := {"live": 0, "extra": 0, "remnant": 0, "dead": 0, "density": 0}
	var model := get_node_or_null("model")
	if model == null:
		return counts
	for child in model.get_children():
		if child is MeshInstance3D and bool(child.get_meta("shown", false)) \
				and child.name != &"heart":
			var part_name := String(child.name)
			if part_name.begins_with("remnant_"):
				counts["remnant"] += 1
			elif part_name.begins_with("dead_"):
				counts["dead"] += 1
			else:
				counts["live"] += 1
				if part_name.begins_with("extra_"):
					counts["extra"] += 1
	var density := model.get_node_or_null("density")
	if density != null:
		counts["density"] = density.get_child_count()
	return counts


## The frond's kind from Blender (`spear`, `young`, `mature`, `old`, `stub`,
## `dead`), or `heart`.
func _kind(part: MeshInstance3D) -> String:
	var extras = part.get_meta("extras", {})
	if extras is Dictionary and extras.has("kyt_course_blade"):
		return String(extras["kyt_course_blade"])
	return "heart" if part.name == &"heart" else "mature"


## `count` of `pool`, as evenly round the trunk as the pool allows: aim at
## `count` headings a whole turn apart from a seeded start, and take the unused
## frond nearest each. One draw, whatever the count.
func _spread(pool: Array, count: int, rng: RandomNumberGenerator) -> Array:
	var start := rng.randf() * TAU
	if count >= pool.size():
		return pool.duplicate()
	var left := pool.duplicate()
	var picked := []
	for index in count:
		var target := start + TAU * float(index) / float(count)
		var best := 0
		var best_gap := INF
		for j in left.size():
			var gap := absf(angle_difference(_heading(left[j]), target))
			if gap < best_gap:
				best_gap = gap
				best = j
		picked.append(left[best])
		left.remove_at(best)
	return picked


func _heading(part: MeshInstance3D) -> float:
	var centre := (part.get_meta("rest") as Transform3D) * part.mesh.get_aabb().get_center()
	return atan2(centre.z, centre.x)


## Fisher–Yates with this crown's own generator: one draw per element.
func _shuffled(items: Array, rng: RandomNumberGenerator) -> Array:
	var out := items.duplicate()
	for i in range(out.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var held = out[i]
		out[i] = out[j]
		out[j] = held
	return out
