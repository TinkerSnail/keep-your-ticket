@tool
extends Node3D

## R2's artistic course is the editor-owned Curve3D in this scene. This script
## derives only the repetitive rails, ties, catwalk and timber bents from that
## selectable source; it never writes or replaces the scene.

@export var timber_material: Material
@export var dark_timber_material: Material
@export var rail_material: Material
@export var catwalk_material: Material
@export var catch_material: Material
@export_range(1.0, 3.0, 0.1) var track_interval := 2.2
@export_range(3.0, 8.0, 0.25) var bent_interval := 7.0
@export_range(0.8, 1.5, 0.05) var rail_gauge := 1.05

const GROUND_Y := -6.0
const STATION_NORTH_Z := -67.0
const TRACK_BEAM := 0.16
const LEDGER_BEAM := 0.22
const TIE_SIZE := Vector3(2.25, 0.16, 0.24)
const PUBLIC_SCREEN_DROP := 0.58
const PUBLIC_SCREEN_WIDTH := 2.80

var _rebuild_queued := false


func _ready() -> void:
	var course := get_node_or_null("course") as Path3D
	if course != null and course.curve != null \
			and not course.curve.changed.is_connected(_queue_rebuild):
		course.curve.changed.connect(_queue_rebuild)
	_queue_rebuild()


func _queue_rebuild() -> void:
	if _rebuild_queued or not is_inside_tree():
		return
	_rebuild_queued = true
	call_deferred("_rebuild")


func _rebuild() -> void:
	_rebuild_queued = false
	var course := get_node_or_null("course") as Path3D
	var derived := get_node_or_null("derived_construction") as Node3D
	if course == null or course.curve == null or derived == null:
		return
	for child in derived.get_children():
		child.free()

	var curve := course.curve
	var length := curve.get_baked_length()
	if length <= track_interval:
		return

	var samples: Array[Dictionary] = []
	var count := maxi(2, ceili(length / track_interval))
	for i in count + 1:
		var distance := minf(float(i) * length / float(count), length)
		samples.append(_sample(curve, distance, length))

	_build_track(samples, derived)
	_build_bents(curve, length, derived)


func _sample(curve: Curve3D, distance: float, length: float) -> Dictionary:
	var epsilon := minf(0.35, length * 0.002)
	var before := curve.sample_baked(maxf(distance - epsilon, 0.0), true)
	var after := curve.sample_baked(minf(distance + epsilon, length), true)
	var direction := (after - before).normalized()
	if direction.length_squared() < 0.5:
		direction = Vector3.FORWARD
	var side := direction.cross(Vector3.UP).normalized()
	if side.length_squared() < 0.5:
		side = Vector3.RIGHT
	var up := side.cross(direction).normalized()
	return {
		"point": curve.sample_baked(distance, true),
		"direction": direction,
		"side": side,
		"up": up,
	}


func _build_track(samples: Array[Dictionary], parent: Node3D) -> void:
	for i in samples.size() - 1:
		var a: Dictionary = samples[i]
		var b: Dictionary = samples[i + 1]
		for rail_side in [-1.0, 1.0]:
			var rail_a: Vector3 = a["point"] + a["side"] * rail_side * rail_gauge * 0.5
			var rail_b: Vector3 = b["point"] + b["side"] * rail_side * rail_gauge * 0.5
			_beam(parent, "running_rail_%03d_%s" % [i, "l" if rail_side < 0.0 else "r"],
				rail_a, rail_b, TRACK_BEAM, rail_material)
			_beam(parent, "timber_ledger_%03d_%s" % [i, "l" if rail_side < 0.0 else "r"],
				rail_a - a["up"] * 0.22, rail_b - b["up"] * 0.22,
				LEDGER_BEAM, dark_timber_material)

		var point: Vector3 = a["point"] - a["up"] * 0.31
		_box(parent, "cross_tie_%03d" % i, point,
			Basis(a["side"], a["up"], -a["direction"]).orthonormalized(),
			TIE_SIZE, timber_material)

		# R2 crosses the public Boardwalk once, at one authored high-clearance
		# flyover. A narrow translucent catch net follows the live track there
		# if Christina reshapes the course in the editor.
		var midpoint: Vector3 = (a["point"] + b["point"]) * 0.5
		var crossing_id := _public_crossing_id(midpoint)
		if not crossing_id.is_empty():
			var screen_a: Vector3 = a["point"] - a["up"] * PUBLIC_SCREEN_DROP
			var screen_b: Vector3 = b["point"] - b["up"] * PUBLIC_SCREEN_DROP
			var screen_delta := screen_b - screen_a
			_box(parent, "public_catch_%s_%03d" % [crossing_id, i],
				(screen_a + screen_b) * 0.5,
				Basis(a["side"], a["up"], -a["direction"]).orthonormalized(),
				Vector3(PUBLIC_SCREEN_WIDTH, 0.025, screen_delta.length()),
				catch_material if catch_material != null else rail_material)

		# The northbound lift is the only place with a catwalk and chain. Its
		# public-side rail gives the tall first hill scale from route B.
		if midpoint.x < -74.0 and midpoint.z < -64.0 and midpoint.z > -94.0 \
				and Vector3(a["direction"]).y > 0.05:
			var walk_a: Vector3 = a["point"] + a["side"] * 1.28 - a["up"] * 0.18
			var walk_b: Vector3 = b["point"] + b["side"] * 1.28 - b["up"] * 0.18
			_beam(parent, "lift_catwalk_%03d" % i, walk_a, walk_b, 0.34,
				catwalk_material)
			_beam(parent, "lift_chain_%03d" % i,
				a["point"] - a["up"] * 0.08, b["point"] - b["up"] * 0.08,
				0.11, rail_material)
			_beam(parent, "catwalk_rail_%03d" % i,
				walk_a + Vector3(a["side"]) * 0.45 + Vector3.UP,
				walk_b + Vector3(b["side"]) * 0.45 + Vector3.UP,
				0.09, rail_material)
			if i % 2 == 0:
				var rail_bottom: Vector3 = walk_a + Vector3(a["side"]) * 0.45
				var rail_top: Vector3 = rail_bottom + Vector3.UP * 1.0
				_beam(parent, "catwalk_post_%03d" % i, rail_bottom, rail_top,
					0.09, rail_material)


func _public_crossing_id(point: Vector3) -> String:
	var controls := get_node_or_null("public_overhead_crossings")
	if controls == null:
		return ""
	var p := Vector2(point.x, point.z)
	for child in controls.get_children():
		if child is not Marker3D:
			continue
		var marker := child as Marker3D
		var radius := float(marker.get_meta("screen_radius", 0.0))
		if p.distance_to(Vector2(marker.position.x, marker.position.z)) <= radius:
			return String(marker.name)
	return ""


func _occupied_high_bay_id(point: Vector3) -> String:
	var controls := get_node_or_null("occupied_high_bays")
	if controls == null:
		return ""
	var p := Vector2(point.x, point.z)
	for child in controls.get_children():
		if child is not Marker3D:
			continue
		var marker := child as Marker3D
		var radius := float(marker.get_meta("clear_span_radius", 0.0))
		if p.distance_to(Vector2(marker.position.x, marker.position.z)) <= radius:
			return String(marker.name)
	return ""


func _build_bents(curve: Curve3D, length: float, parent: Node3D) -> void:
	var count := maxi(2, floori(length / bent_interval))
	for i in count:
		var distance := (float(i) + 0.35) * length / float(count)
		var sample := _sample(curve, distance, length)
		var top: Vector3 = sample["point"] - sample["up"] * 0.48
		if top.z > STATION_NORTH_Z or top.y < GROUND_Y + 2.0:
			continue
		# The waterfront flyover is a deliberate clear span. Standard timber
		# bents resume outside its authored radius instead of filling the public
		# route with posts and diagonal bracing.
		if not _public_crossing_id(top).is_empty():
			continue
		# Roofed midway uses may occupy only explicitly authored high bays. Skip
		# the standard close bent there so the roof and its public interior do
		# not share space with a post or brace; adjacent bents carry the span.
		if not _occupied_high_bay_id(top).is_empty():
			continue
		var side: Vector3 = sample["side"]
		var half_top := 1.72
		var half_foot := 2.75
		var beam_y := top.y - 0.28
		var left_top := Vector3(top.x, beam_y, top.z) - side * half_top
		var right_top := Vector3(top.x, beam_y, top.z) + side * half_top
		var left_foot := Vector3(top.x, GROUND_Y - 0.28, top.z) - side * half_foot
		var right_foot := Vector3(top.x, GROUND_Y - 0.28, top.z) + side * half_foot
		_beam(parent, "bent_%03d_post_l" % i, left_foot, left_top, 0.30,
			timber_material)
		_beam(parent, "bent_%03d_post_r" % i, right_foot, right_top, 0.30,
			timber_material)
		_beam(parent, "bent_%03d_cap" % i, left_top - side * 0.35,
			right_top + side * 0.35, 0.30, dark_timber_material)

		var brace_low_y := minf(GROUND_Y + 1.0, beam_y - 1.2)
		var left_low := Vector3(left_foot.x, brace_low_y, left_foot.z)
		var right_low := Vector3(right_foot.x, brace_low_y, right_foot.z)
		# Alternating braced and open bays keep the structure legible from the
		# Boardwalk instead of turning the whole parcel into one dark lattice.
		if beam_y - brace_low_y > 2.0 and i % 2 == 0:
			_beam(parent, "bent_%03d_brace_a" % i, left_low,
				right_top - Vector3.UP * 0.35, 0.18, dark_timber_material)
			_beam(parent, "bent_%03d_brace_b" % i, right_low,
				left_top - Vector3.UP * 0.35, 0.18, dark_timber_material)


func _box(parent: Node3D, node_name: String, at: Vector3, basis: Basis,
		size: Vector3, material: Material) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.material_override = material
	instance.transform = Transform3D(basis, at)
	parent.add_child(instance)
	return instance


func _beam(parent: Node3D, node_name: String, a: Vector3, b: Vector3,
		thickness: float, material: Material) -> MeshInstance3D:
	var delta := b - a
	if delta.length_squared() < 0.0001:
		return null
	var up := Vector3.UP if absf(delta.normalized().dot(Vector3.UP)) < 0.97 \
		else Vector3.FORWARD
	return _box(parent, node_name, (a + b) * 0.5,
		Basis.looking_at(delta.normalized(), up),
		Vector3(thickness, thickness, delta.length()), material)
