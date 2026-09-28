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
## fronds show. The seed also mirrors about `mirror_share` of the fronds across
## their own midrib, on a stream of its own, so the leaves' tears and paint (one
## island per blade kind on the canvas) don't repeat frond to frond. A frond's
## midrib lies within about 20 cm of the upright plane through the trunk and
## its heading, so a mirrored frond fills the same space. A frond's kind is the
## `kyt_course_blade` it carried in Blender, which the GLB brings as metadata.
## The seed also turns every frond up to `jitter_degrees` round the trunk and up
## or down, and scales the whole crown by up to `size_variation`. The random
## draws are the same in number whatever the counts, so changing a count never
## reshuffles the rest of the crown.

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
## The share of fronds shown mirrored across their midrib (2026-09-27: the torn
## leaves otherwise repeat their tears on every frond of a kind).
@export_range(0.0, 1.0, 0.05) var mirror_share := 0.5:
	set(value):
		mirror_share = value
		_queue_rebuild()
## Two interleaves a second, raised and inset copy of every live frond, as the
## Godot-course crown did for the 64-frond catalog date palm (PRP-PLANT-051).
@export_range(1, 2, 1) var density_multiplier := 1:
	set(value):
		density_multiplier = value
		_queue_rebuild()

const DENSITY_SCALE := 0.86
## [frond mesh id, mirrored] -> [the copy it shows, the frond mesh held alive]
## (`_variant`).
static var _variants := {}
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
			part.set_meta("rest_mesh", part.mesh)
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
	# Mirroring draws from its own stream, so adding it left every crown's
	# choice of fronds, turns and tips as it was.
	var mirror_rng := RandomNumberGenerator.new()
	mirror_rng.seed = hash([variation_seed, "mirror"])

	var live: Array[MeshInstance3D] = []
	for part in parts:
		var rest := part.get_meta("rest") as Transform3D
		# Two draws for every part, shown or not.
		var turn := deg_to_rad(rng.randf_range(-1.0, 1.0) * jitter_degrees)
		var tilt := deg_to_rad(rng.randf_range(-1.0, 1.0) * jitter_degrees)
		# One draw for every part, shown or not.
		var mirrored := mirror_rng.randf() < mirror_share
		var part_name := String(part.name)
		if part_name == "heart":
			part.mesh = _variant(part.get_meta("rest_mesh") as Mesh, rest, Vector3.ZERO, _tone(part))
			part.transform = rest
			part.set_meta("shown", true)
			continue
		part.visible = shown.get(part, false)
		# Kept apart from `visible`: in the game StaticMerge folds the shown
		# fronds into one mesh and hides them all.
		part.set_meta("shown", part.visible)
		# Each frond grows from the crown's centre, so it turns about the trunk's
		# axis and tips up or down about the level line square to its heading.
		var rest_mesh := part.get_meta("rest_mesh") as Mesh
		var centre := rest * rest_mesh.get_aabb().get_center()
		var heading := Vector3(centre.x, 0.0, centre.z).normalized()
		var basis := Basis(Vector3.UP, turn)
		var mirror_side := Vector3.ZERO
		if heading.length_squared() > 0.5:
			var side := heading.cross(Vector3.UP).normalized()
			basis = basis * Basis(side, tilt)
			if mirrored:
				mirror_side = side
		part.mesh = _variant(rest_mesh, rest, mirror_side, _tone(part))
		part.set_meta("mirrored", mirror_side != Vector3.ZERO)
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


## A frond's own tone, 0 to 1 from its name, the same on every crown. The leaf
## shader (assets/shaders/palm_leaf.gdshader) leans that frond's green toward
## yellow or blue-green by it, offset by where the crown stands, so the same
## frond on two palms differs too.
static func _tone(part: Node) -> float:
	# `hash` alone gives neighbouring names neighbouring values (mature_0 to
	# mature_3 all came out 0.282); a generator seeded by it scatters them.
	var scatter := RandomNumberGenerator.new()
	scatter.seed = hash(String(part.name))
	return scatter.randf()


## The mesh a frond shows: a copy of `mesh` carrying `tone` in its vertex
## colour's red for the leaf shader, and, given `side` (the normal of the upright
## plane through the trunk and the frond's heading, in the crown's space; zero
## for none), reflected across that plane: the same frond, its left and right
## swapped, so its tears and paint fall the other way. The reflection is built
## into the mesh, vertices and normals reflected and every triangle's winding
## reversed, rather than put in a mirrored transform: Godot lights a mirrored
## instance of a double-sided material from the wrong side, which showed as
## pale, washed-out fronds (2026-09-27). `rest` is the frond's rest transform.
## One of each per frond, shared by every crown.
static func _variant(mesh: Mesh, rest: Transform3D, side: Vector3, tone: float) -> ArrayMesh:
	var mirror := side != Vector3.ZERO
	var key := [mesh.get_instance_id(), mirror]
	if _variants.has(key):
		return _variants[key][0]
	var reflect := Basis(Vector3.RIGHT - 2.0 * side.x * side, Vector3.UP - 2.0 * side.y * side,
		Vector3.BACK - 2.0 * side.z * side)
	var to_mesh := rest.affine_inverse() * Transform3D(reflect, Vector3.ZERO) * rest
	var normal_basis := to_mesh.basis.inverse().transposed()
	var variant := ArrayMesh.new()
	for s in mesh.get_surface_count():
		var arrays := mesh.surface_get_arrays(s)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var colours := PackedColorArray()
		colours.resize(vertices.size())
		colours.fill(Color(tone, 0.0, 0.0, 1.0))
		arrays[Mesh.ARRAY_COLOR] = colours
		if not mirror:
			variant.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
			variant.surface_set_material(s, mesh.surface_get_material(s))
			continue
		for i in vertices.size():
			vertices[i] = to_mesh * vertices[i]
		arrays[Mesh.ARRAY_VERTEX] = vertices
		if arrays[Mesh.ARRAY_NORMAL] != null:
			var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
			for i in normals.size():
				normals[i] = (normal_basis * normals[i]).normalized()
			arrays[Mesh.ARRAY_NORMAL] = normals
		if arrays[Mesh.ARRAY_TANGENT] != null:
			# The reflection flips which way the bitangent runs: the sign.
			var tangents: PackedFloat32Array = arrays[Mesh.ARRAY_TANGENT]
			for i in range(0, tangents.size(), 4):
				var t := (to_mesh.basis * Vector3(tangents[i], tangents[i + 1], tangents[i + 2])).normalized()
				tangents[i] = t.x
				tangents[i + 1] = t.y
				tangents[i + 2] = t.z
				tangents[i + 3] = -tangents[i + 3]
			arrays[Mesh.ARRAY_TANGENT] = tangents
		# Imported meshes are indexed; an unindexed one is given its own order.
		var indices := PackedInt32Array(range(vertices.size())) if arrays[Mesh.ARRAY_INDEX] == null \
			else arrays[Mesh.ARRAY_INDEX] as PackedInt32Array
		for t in range(0, indices.size() - 2, 3):
			var held := indices[t + 1]
			indices[t + 1] = indices[t + 2]
			indices[t + 2] = held
		arrays[Mesh.ARRAY_INDEX] = indices
		variant.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
		variant.surface_set_material(s, mesh.surface_get_material(s))
	_variants[key] = [variant, mesh]
	return variant


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
	var centre := (part.get_meta("rest") as Transform3D) * (part.get_meta("rest_mesh") as Mesh).get_aabb().get_center()
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
