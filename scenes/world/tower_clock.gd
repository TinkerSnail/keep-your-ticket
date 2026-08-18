extends Node3D

## The clock faces on the sign tower, driven by `ParkClock`.
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
## **One face per side since 2026-08-18, and the node moved onto the tower's own
## axis to carry them.** It faced south alone, toward the gate, which is the
## approach the whole plaza is composed around — and made the time unreadable
## from three quarters of the room it is the instrument of. The plaza is 104m
## and the ring walkway goes all the way round the fountain; a player on the
## north side was looking at the back of the park's one clock. `design.md` asks
## for the time to be a thing you can look up and know, and a readout with a
## blind side is a readout you have to walk around.
##
## Faces are identical and yawed, never mirrored. A clock on the far side of a
## tower is the same machine seen from the other end, and its hands still run
## clockwise to the person standing in front of it.

const RADIUS := 0.7
const FACE_RADIUS := 0.62
const HOUR_HAND := 0.34
const MINUTE_HAND := 0.5
const RIM_THICK := 0.1

## The tower's wall in this node's own units. The shaft is 5.6m square and the
## node is scaled 2.7× — see the class comment on why the scale lives there and
## not in these constants — so its face stands 2.8 / 2.7 out from the axis.
const WALL_FACE := 2.8 / 2.7

## Sunk into the masonry by a hair. A rim laid flat on a wall shares a plane
## with it, which is the park's standing rule about coplanar faces; the same
## rule is why this is written as the wall plus the rim's own half-thickness
## less an embed rather than as the one number it works out to.
const EMBED := 0.02

var _hour_pivots: Array[Node3D] = []
var _minute_pivots: Array[Node3D] = []


func _ready() -> void:
	_build()
	_set_hands()


func _process(_delta: float) -> void:
	_set_hands()


func _set_hands() -> void:
	var h := float(ParkClock.hour() % 12) + float(ParkClock.minute()) / 60.0
	var m := fmod(ParkClock.seconds, ParkClock.HOUR) / ParkClock.HOUR
	# Twelve is up and the hands run toward the viewer's right, which is a
	# negative rotation about the face's own Z — and every face is built about
	# its own +Z, so the one sign is right for all four bearings.
	for pivot in _hour_pivots:
		pivot.rotation.z = -TAU * h / 12.0
	for pivot in _minute_pivots:
		pivot.rotation.z = -TAU * m


func _build() -> void:
	var dark := StandardMaterial3D.new()
	dark.albedo_color = Color(0.16, 0.16, 0.18)
	dark.roughness = 0.6

	var face_mat := StandardMaterial3D.new()
	face_mat.albedo_color = Color(0.93, 0.91, 0.85)
	face_mat.roughness = 0.85

	var stand_off := WALL_FACE + RIM_THICK * 0.5 - EMBED
	# South first, so the gate axis keeps the face it has always had; then west,
	# north, east.
	for i in 4:
		var yaw := TAU * float(i) / 4.0
		var root := Node3D.new()
		root.name = "face_%d" % i
		root.rotation.y = yaw
		root.position = Vector3(sin(yaw), 0.0, cos(yaw)) * stand_off
		add_child(root)
		_build_face(root, dark, face_mat)


## One face, built about its parent's origin and looking down its own +Z.
func _build_face(root: Node3D, dark: Material, face_mat: Material) -> void:
	var rim := CylinderMesh.new()
	rim.top_radius = RADIUS
	rim.bottom_radius = RADIUS
	rim.height = RIM_THICK
	rim.radial_segments = 28
	_add_mesh(root, rim, dark, Vector3.ZERO, 0.0)

	var face := CylinderMesh.new()
	face.top_radius = FACE_RADIUS
	face.bottom_radius = FACE_RADIUS
	face.height = RIM_THICK
	face.radial_segments = 28
	_add_mesh(root, face, face_mat, Vector3(0, 0, 0.03), 0.0)

	var quarter := BoxMesh.new()
	quarter.size = Vector3(0.05, 0.15, 0.02)
	var tick := BoxMesh.new()
	tick.size = Vector3(0.03, 0.08, 0.02)

	for i in 12:
		var angle := TAU * float(i) / 12.0
		var reach := FACE_RADIUS - 0.09
		var mesh: BoxMesh = quarter if i % 3 == 0 else tick
		var at := Vector3(sin(angle) * reach, cos(angle) * reach, 0.075)
		_add_mesh(root, mesh, dark, at, -angle)

	_hour_pivots.append(_add_hand(root, dark, HOUR_HAND, 0.055, 0.09))
	_minute_pivots.append(_add_hand(root, dark, MINUTE_HAND, 0.035, 0.105))


## A hand is a pivot at the centre of the face with the bar offset out along its
## own +Y, so that rotating the pivot sweeps the hand rather than orbiting it.
func _add_hand(root: Node3D, mat: Material, length: float, width: float, depth: float) -> Node3D:
	var pivot := Node3D.new()
	pivot.position = Vector3(0, 0, depth)
	root.add_child(pivot)

	var bar := BoxMesh.new()
	bar.size = Vector3(width, length, 0.02)
	var hand := MeshInstance3D.new()
	hand.mesh = bar
	hand.material_override = mat
	hand.position = Vector3(0, length * 0.5 - width * 0.5, 0)
	pivot.add_child(hand)
	return pivot


func _add_mesh(root: Node3D, mesh: Mesh, mat: Material, at: Vector3, roll: float) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.material_override = mat
	node.position = at
	# Cylinders are built about their own Y. A face looks down its own +Z, so
	# lay them onto Z first; boxes are already in the plane and only need the
	# roll.
	if mesh is CylinderMesh:
		node.rotation = Vector3(PI * 0.5, 0, 0)
	else:
		node.rotation = Vector3(0, 0, roll)
	root.add_child(node)
	return node
