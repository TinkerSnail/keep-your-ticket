@tool
extends Node3D

## R15's footprint and machine proportions are editor controls. Only the six
## repeated sweeps and twelve cars are derived here.

@export var arm_material: Material
@export var car_material_a: Material
@export var car_material_b: Material
@export var hub_material: Material
@export_range(5.5, 8.0, 0.1) var sweep_radius := 6.5
@export_range(3, 8, 1) var arm_count := 6
@export_range(0.05, 0.5, 0.01) var open_speed := 0.16


func _ready() -> void:
	_rebuild()


func _process(delta: float) -> void:
	if Engine.is_editor_hint():
		return
	var clock := get_node_or_null("/root/ParkClock")
	if clock != null and bool(clock.call("is_open")):
		$derived_machine.rotate_y(delta * open_speed)


func _rebuild() -> void:
	var derived := get_node_or_null("derived_machine") as Node3D
	if derived == null:
		return
	for child in derived.get_children():
		child.free()
	_cylinder(derived, "rotor_hub", Vector3(0, 0.95, 0), 1.35, 0.75,
		hub_material)
	for i in arm_count:
		var angle := TAU * float(i) / float(arm_count)
		var direction := Vector3(cos(angle), 0.0, sin(angle))
		_beam(derived, "sweep_arm_%02d" % i, Vector3(0, 1.05, 0),
			direction * sweep_radius + Vector3.UP * 0.15, 0.24, arm_material)
		for side in [-1.0, 1.0]:
			var tangent: Vector3 = Vector3(-direction.z, 0.0, direction.x)
			var at: Vector3 = direction * sweep_radius + tangent * float(side) * 1.05 + Vector3.UP * 0.72
			_box(derived, "car_%02d_%s" % [i, "a" if side < 0.0 else "b"], at,
				Basis.looking_at(tangent * side, Vector3.UP), Vector3(1.35, 0.72, 1.65),
				car_material_a if (i + int(side > 0.0)) % 2 == 0 else car_material_b)


func _box(parent: Node3D, node_name: String, at: Vector3, basis: Basis,
		size: Vector3, material: Material) -> void:
	var mesh := BoxMesh.new()
	mesh.size = size
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.material_override = material
	instance.transform = Transform3D(basis, at)
	parent.add_child(instance)


func _cylinder(parent: Node3D, node_name: String, at: Vector3, radius: float,
		height: float, material: Material) -> void:
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = 18
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.material_override = material
	instance.position = at
	parent.add_child(instance)


func _beam(parent: Node3D, node_name: String, a: Vector3, b: Vector3,
		thickness: float, material: Material) -> void:
	var delta := b - a
	var up := Vector3.UP if absf(delta.normalized().dot(Vector3.UP)) < 0.97 \
		else Vector3.FORWARD
	_box(parent, node_name, (a + b) * 0.5,
		Basis.looking_at(delta.normalized(), up),
		Vector3(thickness, thickness, delta.length()), material)
