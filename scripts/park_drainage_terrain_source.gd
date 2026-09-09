extends RefCounted

## Construction reader for the four editor-owned drainage basins. The saved
## Marker3D rings remain the artistic source; this helper only turns each ring,
## its linked low point and a small derived joining apron into terrain heights.

const Controls = preload("res://scripts/park_vertical_controls_source.gd")
const OUTER_JOIN_RUN := 6.0

var _basins: Dictionary = {}


func _init(source_root: Node3D = null) -> void:
	var owns_root := source_root == null
	var root := source_root if source_root != null else Controls.instantiate()
	var records := Controls.drainage_basins(root)
	for id in records:
		var record: Dictionary = records[id]
		assert(record["status"] == &"approved_source_published",
			"%s is not published for terrain construction" % id)
		assert(record["shape_source"] == &"authored_in_godot_not_traced_from_svg",
			"%s must remain an editor-authored Godot shape" % id)
		var rim3: Array[Vector3] = record["rim"]
		assert(rim3.size() >= 3, "%s has no usable terrain ring" % id)
		var rim := PackedVector2Array()
		var rim_y := rim3[0].y
		for point in rim3:
			assert(absf(point.y - rim_y) < 0.001,
				"%s terrain ring is not level" % id)
			rim.append(Vector2(point.x, point.z))
		var low: Vector3 = record["low"]
		assert(Geometry2D.is_point_in_polygon(Vector2(low.x, low.z), rim),
			"%s low point is outside its editor-authored ring" % id)
		var saved := record.duplicate()
		saved["rim2"] = rim
		saved["rim_y"] = rim_y
		_basins[id] = saved
	if owns_root:
		root.free()


## Apply only the named basins. `vertical_offset` lets a lower supporting mesh
## follow the same depression without becoming coplanar with its visible owner.
func terrain_y(point: Vector2, standing_y: float, ids: Array,
		vertical_offset := 0.0) -> float:
	var y := standing_y
	for id in ids:
		assert(_basins.has(id), "unknown drainage basin %s" % id)
		y = _basin_y(point, y, _basins[id], vertical_offset)
	return y


func control_points(id: StringName) -> Array[Vector3]:
	assert(_basins.has(id), "unknown drainage basin %s" % id)
	var basin: Dictionary = _basins[id]
	var out: Array[Vector3] = [basin["low"]]
	for point in basin["rim"]:
		out.append(point)
	return out


func basin_ids() -> Array:
	return _basins.keys()


func _basin_y(point: Vector2, standing_y: float, basin: Dictionary,
		vertical_offset: float) -> float:
	var rim: PackedVector2Array = basin["rim2"]
	var edge_distance := _edge_distance(point, rim)
	var inside := edge_distance <= 0.001 \
		or Geometry2D.is_point_in_polygon(point, rim)
	var rim_y := float(basin["rim_y"]) + vertical_offset
	if not inside:
		if edge_distance >= OUTER_JOIN_RUN:
			return standing_y
		var join := _smooth(edge_distance / OUTER_JOIN_RUN)
		return lerpf(rim_y, standing_y, join)
	var low3: Vector3 = basin["low"]
	var low := Vector2(low3.x, low3.z)
	var low_distance := point.distance_to(low)
	# The ratio is one at the low and zero at the saved rim, independent of the
	# ring's irregular shape. It therefore honours every editor control exactly
	# without inventing a second hidden contour.
	var weight := edge_distance / maxf(edge_distance + low_distance, 0.0001)
	return lerpf(rim_y, low3.y + vertical_offset, _smooth(weight))


func _edge_distance(point: Vector2, rim: PackedVector2Array) -> float:
	var best := INF
	for index in rim.size():
		best = minf(best, point.distance_to(
			Geometry2D.get_closest_point_to_segment(point, rim[index],
				rim[(index + 1) % rim.size()])))
	return best


func _smooth(value: float) -> float:
	var t := clampf(value, 0.0, 1.0)
	return t * t * (3.0 - 2.0 * t)
