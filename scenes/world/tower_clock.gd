extends Node3D

## A clock face on the sign tower, driven by `ParkClock`.
##
## The design asks the player to learn a routine — the parade turns the corner
## at three, the lift hill catches the light around seven — which needs somewhere
## to read the time that is part of the park rather than part of a HUD. It is
## the only readout the clock gets, and it is deliberately a thing you have to
## look up at and be near enough to read.
##
## Built here rather than authored node by node, for the same reason the props
## are: sixty transforms of hand arithmetic is sixty chances to be wrong. It
## builds itself into the running scene and writes nothing to disk.
##
## Faces south, toward the gate.

const RADIUS := 0.7
const FACE_RADIUS := 0.62
const HOUR_HAND := 0.34
const MINUTE_HAND := 0.5

var _hour_pivot: Node3D
var _minute_pivot: Node3D


func _ready() -> void:
	_build()
	_set_hands()


func _process(_delta: float) -> void:
	_set_hands()


func _set_hands() -> void:
	var h := float(ParkClock.hour() % 12) + float(ParkClock.minute()) / 60.0
	var m := fmod(ParkClock.seconds, ParkClock.HOUR) / ParkClock.HOUR
	# Twelve is up and the hands run toward the viewer's right, which is a
	# negative rotation about Z when the face points south.
	_hour_pivot.rotation.z = -TAU * h / 12.0
	_minute_pivot.rotation.z = -TAU * m


func _build() -> void:
	var dark := StandardMaterial3D.new()
	dark.albedo_color = Color(0.16, 0.16, 0.18)
	dark.roughness = 0.6

	var face_mat := StandardMaterial3D.new()
	face_mat.albedo_color = Color(0.93, 0.91, 0.85)
	face_mat.roughness = 0.85

	var rim := CylinderMesh.new()
	rim.top_radius = RADIUS
	rim.bottom_radius = RADIUS
	rim.height = 0.1
	rim.radial_segments = 28
	_add_mesh(rim, dark, Vector3.ZERO, 0.0)

	var face := CylinderMesh.new()
	face.top_radius = FACE_RADIUS
	face.bottom_radius = FACE_RADIUS
	face.height = 0.1
	face.radial_segments = 28
	_add_mesh(face, face_mat, Vector3(0, 0, 0.03), 0.0)

	var quarter := BoxMesh.new()
	quarter.size = Vector3(0.05, 0.15, 0.02)
	var tick := BoxMesh.new()
	tick.size = Vector3(0.03, 0.08, 0.02)

	for i in 12:
		var angle := TAU * float(i) / 12.0
		var reach := FACE_RADIUS - 0.09
		var mesh: BoxMesh = quarter if i % 3 == 0 else tick
		var at := Vector3(sin(angle) * reach, cos(angle) * reach, 0.075)
		_add_mesh(mesh, dark, at, -angle)

	_hour_pivot = _add_hand(dark, HOUR_HAND, 0.055, 0.09)
	_minute_pivot = _add_hand(dark, MINUTE_HAND, 0.035, 0.105)


## A hand is a pivot at the centre of the face with the bar offset out along its
## own +Y, so that rotating the pivot sweeps the hand rather than orbiting it.
func _add_hand(mat: Material, length: float, width: float, depth: float) -> Node3D:
	var pivot := Node3D.new()
	pivot.position = Vector3(0, 0, depth)
	add_child(pivot)

	var bar := BoxMesh.new()
	bar.size = Vector3(width, length, 0.02)
	var hand := MeshInstance3D.new()
	hand.mesh = bar
	hand.material_override = mat
	hand.position = Vector3(0, length * 0.5 - width * 0.5, 0)
	pivot.add_child(hand)
	return pivot


func _add_mesh(mesh: Mesh, mat: Material, at: Vector3, roll: float) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.material_override = mat
	node.position = at
	# Cylinders are built about their own Y. The face points south, so lay them
	# down onto Z first; boxes are already in the plane and only need the roll.
	if mesh is CylinderMesh:
		node.rotation = Vector3(PI * 0.5, 0, 0)
	else:
		node.rotation = Vector3(0, 0, roll)
	add_child(node)
	return node
