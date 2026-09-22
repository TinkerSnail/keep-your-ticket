extends Node

## Physical guard for the unmounted interchange-segment forest experiments.
## It deliberately does not claim visual success: the matching capture is the
## view-space gate. This test only proves that a candidate has no collision,
## stays outside every live road centreline and remains absent from park_world.

const MIN_ROAD_CLEARANCE := 30.0
const ROAD_SCENE := "res://scenes/world/park_approach.tscn"
const WORLD_SCENE := "res://scenes/world/park_world.tscn"
const PROOFS := [
	"res://scenes/world/range_interchange_clustered_proof.tscn",
	"res://scenes/world/range_interchange_silhouette_proof.tscn",
]
const ROAD_NAMES := [
	"highway", "highway_b", "approach_road",
	"ramp_a_off", "ramp_a_on", "ramp_b_off", "ramp_b_on",
]

var _failures: Array[String] = []


func _ready() -> void:
	var road_root := load(ROAD_SCENE).instantiate() as Node3D
	add_child(road_root)
	var road_lines: Array[PackedVector3Array] = []
	for road_name in ROAD_NAMES:
		var road := road_root.find_child(road_name, true, false) as Node3D
		if road == null or not road.has_meta("points"):
			_failures.append("missing road points: %s" % road_name)
			continue
		var local_points: PackedVector3Array = road.get_meta("points")
		var world_points := PackedVector3Array()
		for point in local_points:
			world_points.append(road.global_transform * point)
		road_lines.append(world_points)
	for proof_path in PROOFS:
		_check_proof(proof_path, road_lines)
	var world_text := FileAccess.get_file_as_string(WORLD_SCENE)
	for proof_path in PROOFS:
		if proof_path in world_text:
			_failures.append("proof is mounted in park_world: %s" % proof_path)
	road_root.free()
	if _failures.is_empty():
		print("RANGE INTERCHANGE PROOF PHYSICAL GATE PASS")
		get_tree().quit(0)
	else:
		for failure in _failures:
			push_error(failure)
		get_tree().quit(1)


func _check_proof(path: String, road_lines: Array[PackedVector3Array]) -> void:
	var proof := load(path).instantiate() as Node3D
	add_child(proof)
	if proof.find_children("*", "CollisionObject3D", true, false).size() > 0 \
			or proof.find_children("*", "CollisionShape3D", true, false).size() > 0:
		_failures.append("proof contains collision: %s" % path)
	var min_clearance := INF
	var min_vertex := Vector3.ZERO
	var min_mesh := ""
	var vertex_count := 0
	for mesh_instance in proof.find_children("*", "MeshInstance3D", true, false):
		var instance := mesh_instance as MeshInstance3D
		if instance.mesh == null:
			continue
		for surface_index in instance.mesh.get_surface_count():
			var arrays := instance.mesh.surface_get_arrays(surface_index)
			var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			for vertex in vertices:
				var world_vertex := instance.global_transform * vertex
				var xz := Vector2(world_vertex.x, world_vertex.z)
				for line in road_lines:
					var clearance := _point_polyline_distance(xz, line)
					if clearance < min_clearance:
						min_clearance = clearance
						min_vertex = world_vertex
						min_mesh = String(instance.name)
				vertex_count += 1
	print("%s: %d vertices, minimum road-centreline clearance %.2fm at %s in %s" % [
		path.get_file(), vertex_count, min_clearance, min_vertex, min_mesh])
	if vertex_count == 0:
		_failures.append("proof has no mesh vertices: %s" % path)
	elif min_clearance < MIN_ROAD_CLEARANCE:
		_failures.append("%s road clearance %.2fm is below %.2fm" % [
			path.get_file(), min_clearance, MIN_ROAD_CLEARANCE])
	proof.free()


func _point_polyline_distance(point: Vector2, line: PackedVector3Array) -> float:
	var best := INF
	for index in line.size() - 1:
		var a := Vector2(line[index].x, line[index].z)
		var b := Vector2(line[index + 1].x, line[index + 1].z)
		var ab := b - a
		var t := 0.0
		if ab.length_squared() > 0.000001:
			t = clampf((point - a).dot(ab) / ab.length_squared(), 0.0, 1.0)
		best = minf(best, point.distance_to(a + ab * t))
	return best
