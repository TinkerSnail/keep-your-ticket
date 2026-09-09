extends RefCounted

## Generator-facing derivation of the editor-owned lighthouse Path3D. The
## Curve3D and its cross-section metadata remain the artistic source; this
## helper only samples that source for terrain construction and paving.

const Controls = preload("res://scripts/park_vertical_controls_source.gd")
const Plan = preload("res://scripts/park_plan.gd")

var _curve: Curve3D
var _curve_transform := Transform3D.IDENTITY
var _terrain_samples: Array[Vector3] = []
var _bed_half_width := 0.0
var _outer_seaward := 0.0
var _outer_landward := 0.0
var _bed_depth := 0.0
var _sample_spacing := 0.0
var _grid_step := 0.0


func _init(source_root: Node3D = null) -> void:
	var owns_root := source_root == null
	var root := source_root if source_root != null else Controls.instantiate()
	var handoff := Controls.lighthouse_regrade(root)
	assert(handoff["curve_status"] == &"approved_editor_curve",
		"P1 terrain may only derive from the approved editor curve")
	assert(handoff["path_status"] == &"approved_source",
		"P1 target Path3D is not approved for construction")
	var path := handoff["target_path"] as Path3D
	_curve = path.curve.duplicate(true) as Curve3D
	_curve_transform = Controls.lighthouse_curve_transform(root)
	_bed_half_width = float(handoff["terrain_bed_half_width"])
	_outer_seaward = float(handoff["terrain_outer_seaward"])
	_outer_landward = float(handoff["terrain_outer_landward"])
	_bed_depth = float(handoff["terrain_bed_depth"])
	_sample_spacing = float(handoff["terrain_sample_spacing"])
	_grid_step = float(handoff["terrain_grid_step"])
	assert(_curve != null and _curve.point_count >= 2,
		"P1 approved curve must have at least two controls")
	assert(_bed_half_width > 1.5,
		"P1 terrain bed must be wider than the three-metre path")
	assert(_outer_seaward > _bed_half_width
		and _outer_landward > _bed_half_width,
		"P1 terrain easing must extend beyond its bed")
	assert(_sample_spacing > 0.0 and _grid_step > 0.0,
		"P1 terrain sampling metadata must be positive")
	_bake_terrain_samples()
	if owns_root:
		root.free()


func terrain_y(point: Vector2, standing_y: float) -> float:
	var profile := profile_at(point)
	if not bool(profile["inside_length"]):
		return standing_y
	var distance := float(profile["distance"])
	var outer := float(profile["outer_width"])
	if distance >= outer:
		return standing_y
	var target := float(profile["centre_y"]) - _bed_depth
	if distance <= _bed_half_width:
		return target
	var t := clampf((distance - _bed_half_width) /
		(outer - _bed_half_width), 0.0, 1.0)
	t = t * t * (3.0 - 2.0 * t)
	return lerpf(target, standing_y, t)


func profile_at(point: Vector2) -> Dictionary:
	var best_distance := INF
	var best_centre := Vector2.ZERO
	var best_y := 0.0
	var best_tangent := Vector2.RIGHT
	var best_index := 0
	var best_along := 0.0
	for index in _terrain_samples.size() - 1:
		var a3 := _terrain_samples[index]
		var b3 := _terrain_samples[index + 1]
		var a := Vector2(a3.x, a3.z)
		var b := Vector2(b3.x, b3.z)
		var centre := Geometry2D.get_closest_point_to_segment(point, a, b)
		var distance := point.distance_to(centre)
		if distance >= best_distance:
			continue
		var run := a.distance_to(b)
		var along := a.distance_to(centre) / maxf(run, 0.001)
		best_distance = distance
		best_centre = centre
		best_y = lerpf(a3.y, b3.y, along)
		best_tangent = (b - a).normalized()
		best_index = index
		best_along = along
	var inside_length := true
	if best_index == 0 and best_along <= 0.0001:
		var start := Vector2(_terrain_samples[0].x, _terrain_samples[0].z)
		inside_length = (point - start).dot(best_tangent) >= -0.0001
	elif best_index == _terrain_samples.size() - 2 and best_along >= 0.9999:
		var finish := Vector2(_terrain_samples[-1].x, _terrain_samples[-1].z)
		inside_length = (point - finish).dot(best_tangent) <= 0.0001
	var lateral := Vector2(-best_tangent.y, best_tangent.x)
	var plus_is_seaward := Plan.coast_inland(best_centre + lateral) \
		< Plan.coast_inland(best_centre - lateral)
	var seaward := lateral if plus_is_seaward else -lateral
	var side_is_seaward := (point - best_centre).dot(seaward) >= 0.0
	return {
		"centre": best_centre,
		"centre_y": best_y,
		"distance": best_distance,
		"tangent": best_tangent,
		"seaward_direction": seaward,
		"outer_width": _outer_seaward if side_is_seaward else _outer_landward,
		"side_is_seaward": side_is_seaward,
		"inside_length": inside_length,
	}


func path_points(spacing := 0.5) -> Array[Vector3]:
	assert(spacing > 0.0, "P1 path sample spacing must be positive")
	var length := _curve.get_baked_length()
	var steps := maxi(1, ceili(length / spacing))
	var out: Array[Vector3] = []
	for index in steps + 1:
		var offset := minf(float(index) * length / float(steps), length)
		out.append(_curve_transform * _curve.sample_baked(offset, true))
	return out


func terrain_bounds() -> Rect2:
	var padding := maxf(_outer_seaward, _outer_landward)
	var lo := Vector2(_terrain_samples[0].x, _terrain_samples[0].z)
	var hi := lo
	for point in _terrain_samples:
		lo = Vector2(minf(lo.x, point.x), minf(lo.y, point.z))
		hi = Vector2(maxf(hi.x, point.x), maxf(hi.y, point.z))
	return Rect2(lo - Vector2.ONE * padding,
		hi - lo + Vector2.ONE * padding * 2.0)


func terrain_grid_step() -> float:
	return _grid_step


func bed_half_width() -> float:
	return _bed_half_width


func bed_depth() -> float:
	return _bed_depth


func seaward_outer_width() -> float:
	return _outer_seaward


func landward_outer_width() -> float:
	return _outer_landward


func _bake_terrain_samples() -> void:
	var length := _curve.get_baked_length()
	var steps := maxi(1, ceili(length / _sample_spacing))
	for index in steps + 1:
		var offset := minf(float(index) * length / float(steps), length)
		_terrain_samples.append(
			_curve_transform * _curve.sample_baked(offset, true))
