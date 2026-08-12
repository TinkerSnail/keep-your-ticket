extends Node3D

## The photographer.
##
## Third person to move and first person to shoot, so this is what the player is
## looking at most of the time. The uniform on it is not decoration: the shirt
## with a logo on it is the whole reason the park tolerates someone wandering
## around pointing a camera at strangers, and in first person the player never
## once sees the thing that makes the fiction work.
##
## In first person the body drops to shadows only. Nothing renders into the
## photograph, but the photographer's shadow still reaches into the bottom of
## the frame — which is the most period-correct snapshot artefact available, and
## it costs one enum.
##
## Built to the crowd's proportions (`tools/gen_crowd.gd`, `_build_body`) so the
## player is visibly the same species as the guests. Those numbers are
## duplicated here rather than shared; a third figure is the point at which they
## should move to `scripts/`.

## The plaza's sightlines were all composed for an eye at 1.6m and the camera
## stays exactly where it is. This height is picked so the body's eye line
## arrives at the camera, rather than the camera being dragged to the body:
## eye height works out at 0.9472 of total height, and 1.6 / 0.9472 is this.
const HEIGHT := 1.689

const HEAD_H := HEIGHT * 0.132
const NECK_H := HEIGHT * 0.03
const TORSO_H := HEIGHT * 0.258
const HIPS_H := HEIGHT * 0.1
const LEG := HEIGHT - HEAD_H - NECK_H - TORSO_H - HIPS_H
const THIGH := LEG * 0.5
const SHIN := LEG * 0.5

const SHOULDER := HEIGHT * 0.245
const HIP_W := HEIGHT * 0.2
const DEPTH := HEIGHT * 0.115
const LIMB := HEIGHT * 0.055

## Split at the elbow, which the guests are not. They carry things; the
## photographer brings a camera to their face, and a rigid arm cannot do it.
const ARM := LEG * 0.82
const UPPER := ARM * 0.45
const FOREARM := ARM * 0.55

const HEAD_W := HEIGHT * 0.105
const HEAD_D := HEIGHT * 0.112

const CADENCE := 3.4
## A neck, not a turret. Same limit the guests use.
const HEAD_PITCH_LIMIT := deg_to_rad(32.0)

## Camera to the eye. Without an elbow this pose is impossible, and with one it
## is two numbers: the upper arm comes up and forward, the forearm folds back so
## the hands arrive at the face instead of out in front of it.
const RAISED_UPPER := 1.30
const RAISED_ELBOW := -1.62
const RAISE_RATE := 12.0

var _player: CharacterBody3D
var _head: Node3D

var _body: Node3D
var _head_pivot: Node3D
var _arm_l: Node3D
var _arm_r: Node3D
var _elbow_l: Node3D
var _elbow_r: Node3D
var _hip_l: Node3D
var _hip_r: Node3D
var _knee_l: Node3D
var _knee_r: Node3D

var _meshes: Array[MeshInstance3D] = []
var _box := BoxMesh.new()
var _mats: Dictionary = {}

var _phase := 0.0
var _stride := 0.0
var _idle_phase := 0.0
var _raise := 0.0
var _raised := false
var _seen := true


func _ready() -> void:
	_player = get_parent() as CharacterBody3D
	if _player == null:
		push_error("player_body: expected a CharacterBody3D parent")
		return
	_head = _player.get_node("head")
	_build_materials()
	_build()
	set_seen(false)


## Whether the body is actually drawn. False leaves it casting a shadow and
## nothing else, which is what first person wants — and what third person wants
## too on the frames where the arm has collapsed and the camera is inside it.
func set_seen(seen: bool) -> void:
	if seen == _seen:
		return
	_seen = seen
	var mode := (
		GeometryInstance3D.SHADOW_CASTING_SETTING_ON if seen
		else GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	)
	for mesh in _meshes:
		mesh.cast_shadow = mode


func set_raised(raised: bool) -> void:
	_raised = raised


func _physics_process(delta: float) -> void:
	_idle_phase += delta
	_raise = move_toward(_raise, 1.0 if _raised else 0.0, RAISE_RATE * delta)

	var speed := Vector2(_player.velocity.x, _player.velocity.z).length()
	_stride = lerpf(_stride, clampf(speed / _player.walk_speed, 0.0, 1.0), 8.0 * delta)
	_phase += speed * delta * CADENCE

	var swing := 0.62 * _stride
	var hip := sin(_phase)
	_hip_l.rotation.x = hip * swing
	_hip_r.rotation.x = -hip * swing
	# Knees bend one way, and only on the leg swinging through.
	_knee_l.rotation.x = -maxf(sin(_phase - 0.9), 0.0) * 0.85 * _stride
	_knee_r.rotation.x = -maxf(sin(_phase - 0.9 + PI), 0.0) * 0.85 * _stride

	# The arms stop swinging as the camera comes up. Someone walking with a
	# camera to their eye does not swing their arms, which is most of why the
	# shuffle the raise imposes reads as deliberate rather than as a debuff.
	var swing_arm := -hip * swing * 0.7 * (1.0 - _raise)
	_arm_l.rotation.x = lerpf(swing_arm, RAISED_UPPER, _raise)
	_arm_r.rotation.x = lerpf(-swing_arm, RAISED_UPPER, _raise)
	_elbow_l.rotation.x = RAISED_ELBOW * _raise
	_elbow_r.rotation.x = RAISED_ELBOW * _raise

	var bob := absf(sin(_phase)) * 0.022 * _stride
	var sway := sin(_idle_phase * 0.9) * 0.012 * (1.0 - _stride)
	_body.position.y = LEG + bob + sway
	_body.rotation.z = sin(_phase) * 0.03 * _stride

	_head_pivot.rotation.x = clampf(_head.rotation.x, -HEAD_PITCH_LIMIT, HEAD_PITCH_LIMIT)


# --- construction -----------------------------------------------------------


func _build_materials() -> void:
	# Staff green is a colour no guest wears. At forty metres in a crowd of
	# twelve shirt colours, being the one nobody else is wearing is the read.
	var defs := {
		"uniform": Color(0.16, 0.38, 0.34),
		"logo": Color(0.85, 0.68, 0.24),
		"badge": Color(0.9, 0.89, 0.86),
		"bottom": Color(0.71, 0.65, 0.5),
		"skin": Color(0.87, 0.7, 0.56),
		"hair": Color(0.36, 0.25, 0.17),
		"shoe": Color(0.22, 0.22, 0.24),
		"instamatic": Color(0.16, 0.16, 0.17),
		"lens": Color(0.3, 0.31, 0.33),
	}
	for key in defs:
		var m := StandardMaterial3D.new()
		m.albedo_color = defs[key]
		m.roughness = 0.9 if key == "skin" else 0.85
		if key == "lens":
			m.roughness = 0.45
			m.metallic = 0.3
		_mats[key] = m


func _build() -> void:
	_body = _node(self, "body", Vector3(0, LEG, 0))

	_part(_body, "hips", Vector3(HIP_W, HIPS_H, DEPTH), Vector3(0, HIPS_H * 0.5, 0), "bottom")
	_part(_body, "torso", Vector3(SHOULDER, TORSO_H, DEPTH),
		Vector3(0, HIPS_H + TORSO_H * 0.5, 0), "uniform")

	# Front and back, because the uniform has to read from behind — which in
	# third person is the angle it is read from almost all the time.
	var chest_y := HIPS_H + TORSO_H * 0.62
	_part(_body, "logo_front", Vector3(SHOULDER * 0.26, TORSO_H * 0.16, 0.01),
		Vector3(-SHOULDER * 0.2, chest_y, -DEPTH * 0.5 - 0.005), "logo")
	_part(_body, "badge", Vector3(SHOULDER * 0.2, TORSO_H * 0.1, 0.01),
		Vector3(SHOULDER * 0.22, chest_y, -DEPTH * 0.5 - 0.005), "badge")
	_part(_body, "logo_back", Vector3(SHOULDER * 0.55, TORSO_H * 0.3, 0.01),
		Vector3(0, HIPS_H + TORSO_H * 0.66, DEPTH * 0.5 + 0.005), "logo")

	_build_arms()
	_build_legs()
	_build_head()

	# A lanyard, not a shoulder strap. Shoulder-wide and horizontal it read as a
	# yoke on the shirt rather than as anything the player was carrying, and a
	# strap that runs to a camera held in the hand does not make sense anyway.
	# Neck-width, it is the thing every member of staff in a park is wearing.
	_part(_body, "lanyard", Vector3(LIMB * 1.9, TORSO_H * 0.05, LIMB * 1.9),
		Vector3(0, HIPS_H + TORSO_H * 0.94, 0), "instamatic")


func _build_arms() -> void:
	var shoulder_y := HIPS_H + TORSO_H - LIMB * 0.5
	for side in [-1.0, 1.0]:
		var nm := "arm_l" if side < 0.0 else "arm_r"
		var pivot := _node(_body, nm,
			Vector3(side * (SHOULDER * 0.5 + LIMB * 0.35), shoulder_y, 0))
		# Sleeve then forearm, so a short-sleeved shirt reads at distance.
		_part(pivot, nm + "_sleeve", Vector3(LIMB, UPPER, LIMB),
			Vector3(0, -UPPER * 0.5, 0), "uniform")

		var elbow := _node(pivot, "elbow_l" if side < 0.0 else "elbow_r",
			Vector3(0, -UPPER, 0))
		_part(elbow, "forearm", Vector3(LIMB * 0.88, FOREARM, LIMB * 0.88),
			Vector3(0, -FOREARM * 0.5, 0), "skin")

		if side > 0.0:
			# The Instamatic, in the hand, always. Held at the end of the
			# forearm so the raise pose carries it to the face on its own.
			_part(elbow, "instamatic", Vector3(0.115, 0.072, 0.055),
				Vector3(0, -FOREARM * 0.98, -0.05), "instamatic")
			_part(elbow, "lens", Vector3(0.032, 0.032, 0.012),
				Vector3(0, -FOREARM * 0.98, -0.083), "lens")

	_arm_l = _body.get_node("arm_l")
	_arm_r = _body.get_node("arm_r")
	_elbow_l = _arm_l.get_node("elbow_l")
	_elbow_r = _arm_r.get_node("elbow_r")


func _build_legs() -> void:
	for side in [-1.0, 1.0]:
		var nm := "hip_l" if side < 0.0 else "hip_r"
		var pivot := _node(_body, nm, Vector3(side * HIP_W * 0.26, 0, 0))
		_part(pivot, nm + "_thigh", Vector3(LIMB * 1.25, THIGH, LIMB * 1.25),
			Vector3(0, -THIGH * 0.5, 0), "bottom")
		var knee := _node(pivot, "knee_l" if side < 0.0 else "knee_r",
			Vector3(0, -THIGH, 0))
		_part(knee, "shin", Vector3(LIMB * 1.1, SHIN, LIMB * 1.1),
			Vector3(0, -SHIN * 0.5, 0), "bottom")
		_part(knee, "shoe", Vector3(LIMB * 1.25, LIMB * 0.5, LIMB * 2.0),
			Vector3(0, -SHIN, -LIMB * 0.45), "shoe")

	_hip_l = _body.get_node("hip_l")
	_hip_r = _body.get_node("hip_r")
	_knee_l = _hip_l.get_node("knee_l")
	_knee_r = _hip_r.get_node("knee_r")


func _build_head() -> void:
	var neck := _node(_body, "neck", Vector3(0, HIPS_H + TORSO_H, 0))
	_part(neck, "throat", Vector3(LIMB * 1.1, NECK_H * 2.0, LIMB * 1.1),
		Vector3(0, NECK_H * 0.4, 0), "skin")

	_head_pivot = _node(neck, "head_pivot", Vector3(0, NECK_H, 0))
	_part(_head_pivot, "head", Vector3(HEAD_W, HEAD_H, HEAD_D),
		Vector3(0, HEAD_H * 0.5, 0), "skin")
	# The eye bar is where the camera is. Everything above was sized to land it
	# there, so this is the one part whose position is a constraint.
	_part(_head_pivot, "eyes", Vector3(HEAD_W * 0.72, HEAD_H * 0.13, 0.02),
		Vector3(0, HEAD_H * 0.6, -HEAD_D * 0.5 - 0.01), "hair")
	_part(_head_pivot, "hair", Vector3(HEAD_W * 1.06, HEAD_H * 0.3, HEAD_D * 1.06),
		Vector3(0, HEAD_H * 0.9, 0), "hair")
	# The guests get away without this because most of them are bare-headed and
	# the top band is the whole haircut. Under a cap that band is covered, and
	# the back of the head — which is the angle third person spends all its time
	# at — comes out as a bare skin box.
	_part(_head_pivot, "hair_back", Vector3(HEAD_W * 1.02, HEAD_H * 0.6, HEAD_D * 0.26),
		Vector3(0, HEAD_H * 0.6, HEAD_D * 0.5), "hair")

	# Staff cap. From behind at distance it is the whole uniform.
	_part(_head_pivot, "cap", Vector3(HEAD_W * 1.12, HEAD_H * 0.22, HEAD_D * 1.12),
		Vector3(0, HEAD_H * 0.98, 0), "uniform")
	_part(_head_pivot, "cap_brim", Vector3(HEAD_W * 1.05, HEAD_H * 0.07, HEAD_D * 0.6),
		Vector3(0, HEAD_H * 0.9, -HEAD_D * 0.72), "uniform")
	_part(_head_pivot, "cap_logo", Vector3(HEAD_W * 0.3, HEAD_H * 0.12, 0.01),
		Vector3(0, HEAD_H * 0.99, -HEAD_D * 0.56 - 0.005), "logo")


# --- part helpers -----------------------------------------------------------


func _node(parent: Node3D, nm: String, pos: Vector3) -> Node3D:
	var n := Node3D.new()
	n.name = nm
	n.position = pos
	parent.add_child(n)
	return n


func _part(parent: Node3D, nm: String, size: Vector3, pos: Vector3, mat: String) -> void:
	var m := MeshInstance3D.new()
	m.name = nm
	m.mesh = _box
	m.material_override = _mats[mat]
	m.transform = Transform3D(Basis.IDENTITY.scaled(size), pos)
	parent.add_child(m)
	_meshes.append(m)
