class_name ParkWeather
extends Node3D

## A small authored weather pass over the persistent park.
##
## The schedule is deterministic because a photograph must never depend on
## waiting for an invisible random roll. The shower arrives just after opening,
## passes before lunch and leaves the Boardwalk wet while the day clears toward
## its protected western sunset. Later seasonal data can replace these stops
## without changing the rendering, sound or wet-surface machinery below.

signal weather_changed(cloudiness: float, rain: float, wetness: float, wind: float)

@export_category("Passing shower proof")
@export var enabled := true
@export var effects_enabled := true
@export_range(200, 1800, 50) var rain_particle_count := 900
@export_range(8.0, 40.0, 0.5) var rain_radius := 22.0
@export_range(8.0, 24.0, 0.5) var rain_height := 14.0
@export_range(-36.0, -10.0, 0.5) var rain_fall_speed := -26.0
@export_range(-30.0, 0.0, 0.5) var rain_volume_db := -15.0

## (hour, cloudiness, rain, retained wetness, wind). Linear transitions are
## intentional: the sky gives notice before the hard rain and the deck dries
## long after the last visible drop.
const SCHEDULE := [
	Vector4(0.0, 0.0, 0.0, 0.0),
	Vector4(9.5, 0.0, 0.0, 0.0),
	Vector4(10.0, 0.72, 0.25, 0.55),
	Vector4(10.35, 0.94, 1.0, 0.90),
	Vector4(11.15, 0.88, 0.78, 1.0),
	Vector4(11.75, 0.48, 0.0, 1.0),
	Vector4(13.25, 0.12, 0.0, 0.38),
	Vector4(19.5, 0.0, 0.0, 0.0),
	Vector4(24.0, 0.0, 0.0, 0.0),
]

const WIND := [0.0, 0.0, 0.35, 0.68, 0.58, 0.28, 0.14, 0.05, 0.0]
const WET_SURFACE_NAMES := {
	&"deck_promenade": true,
	&"deck_alley": true,
	&"deck_lane": true,
	&"wheel_deck": true,
	&"pier_deck": true,
	&"pier_head_deck": true,
	&"wearing_surface": true,
	&"R15_public_apron_wearing_surface": true,
	&"R16_public_apron_wearing_surface": true,
}

var cloudiness := 0.0
var rain := 0.0
var wetness := 0.0
var wind := 0.0

var _daylight: Node
var _player: Node3D
var _rain_particles: CPUParticles3D
var _rain_audio: AudioStreamPlayer
var _noise_rng := RandomNumberGenerator.new()
var _noise_slow := 0.0
var _noise_fast := 0.0
var _wet_surfaces: Array[Dictionary] = []
var _wet_surface_ids := {}
var _rescan_seconds := 0.0
var _wet_rescans_remaining := 3
var _last_state := Vector4(-1.0, -1.0, -1.0, -1.0)

## Set by the debug-only dev page (`scenes/ui/dev_view.gd`) to hold one state
## whatever the hour: (cloudiness, rain, wetness, wind). Negative x is none.
const NO_OVERRIDE := Vector4(-1.0, 0.0, 0.0, 0.0)
var dev_override := NO_OVERRIDE


func _ready() -> void:
	add_to_group("park_weather")
	_noise_rng.seed = 0x1998
	if effects_enabled:
		_build_rain()
		# Dummy/headless runs cannot audition sound and retain the active playback
		# until engine teardown, so audio belongs only to a real game session.
		if DisplayServer.get_name() != "headless":
			_build_audio()
	ParkClock.clock_jumped.connect(_on_clock_jumped)
	call_deferred("_bind_world")
	_apply_weather(true)


func _exit_tree() -> void:
	if _rain_audio != null:
		_rain_audio.stop()
		_rain_audio.stream = null


func _process(delta: float) -> void:
	if _player == null or not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group("player") as Node3D
	if _player != null:
		# The emitter follows in plan only. Existing drops remain in world space,
		# so walking does not drag a rectangular curtain of rain behind the player.
		global_position = Vector3(_player.global_position.x,
			_player.global_position.y + rain_height, _player.global_position.z)

	_rescan_seconds -= delta
	if _rescan_seconds <= 0.0 and _wet_rescans_remaining > 0:
		_collect_wet_surfaces()
		_wet_rescans_remaining -= 1
		_rescan_seconds = 2.0

	_apply_weather(false)


func _bind_world() -> void:
	_daylight = get_parent().get_node_or_null("daylight")
	_player = get_tree().get_first_node_in_group("player") as Node3D
	_collect_wet_surfaces()
	_apply_weather(true)


func _on_clock_jumped() -> void:
	_apply_weather(true)


func _apply_weather(force: bool) -> void:
	var state := sample(ParkClock.hours()) if enabled else Vector4.ZERO
	if dev_override.x >= 0.0:
		state = dev_override
	cloudiness = state.x
	rain = state.y
	wetness = state.z
	wind = state.w

	if not force and state.is_equal_approx(_last_state):
		return
	_last_state = state

	if _daylight != null and _daylight.has_method("set_weather"):
		_daylight.set_weather(cloudiness, rain)

	if _rain_particles != null:
		_rain_particles.emitting = rain > 0.015
		_rain_particles.color = Color(1.0, 1.0, 1.0, clampf(rain * 1.15, 0.0, 1.0))
	if _rain_particles != null:
		# A visible diagonal belongs to wind, not to a tilted screen overlay.
		_rain_particles.gravity = Vector3(7.0 * wind, rain_fall_speed, 2.4 * wind)

	if _rain_audio != null:
		_rain_audio.volume_db = rain_volume_db + linear_to_db(maxf(rain, 0.0001))
	_update_wet_surfaces()
	weather_changed.emit(cloudiness, rain, wetness, wind)


## Public and static so tools can verify the authored schedule without letting
## their own frame timing become part of the result.
static func sample(hour: float) -> Vector4:
	var h := fposmod(hour, 24.0)
	for i in SCHEDULE.size() - 1:
		var a: Vector4 = SCHEDULE[i]
		var b: Vector4 = SCHEDULE[i + 1]
		if h <= b.x:
			var t := inverse_lerp(a.x, b.x, h)
			var weather := a.lerp(b, t)
			var wind_level := lerpf(WIND[i], WIND[i + 1], t)
			return Vector4(weather.y, weather.z, weather.w, wind_level)
	return Vector4.ZERO


## Kept as a pure calculation so the wet look can be checked under Godot's
## dummy renderer, which cannot compile the park's real surface shaders.
static func wet_surface_values(base_color: Color, base_roughness: float,
		base_metallic: float, amount: float) -> Dictionary:
	var level := clampf(amount, 0.0, 1.0)
	return {
		"albedo": base_color.lerp(base_color.darkened(0.24), level),
		"roughness": lerpf(base_roughness, 0.22, level),
		"metallic": lerpf(base_metallic, maxf(base_metallic, 0.07), level),
	}


func _build_rain() -> void:
	var streak_material := StandardMaterial3D.new()
	streak_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	streak_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	streak_material.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	streak_material.billboard_keep_scale = true
	streak_material.albedo_color = Color(0.73, 0.84, 0.93, 0.58)
	streak_material.vertex_color_use_as_albedo = true

	var streak := QuadMesh.new()
	streak.size = Vector2(0.026, 1.35)
	streak.material = streak_material

	# CPU particles are deliberate here. On Metal, Godot 4.7.1 can crash while
	# compiling a runtime-created GPU particle process shader before the first
	# frame. Nine hundred simple streaks are cheap, stable and leave the GPU for
	# the persistent world's actual surfaces and lights.
	_rain_particles = CPUParticles3D.new()
	_rain_particles.name = "rain"
	_rain_particles.amount = rain_particle_count
	_rain_particles.lifetime = 0.82
	_rain_particles.randomness = 0.38
	_rain_particles.fixed_fps = 30
	_rain_particles.local_coords = false
	_rain_particles.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	_rain_particles.emission_box_extents = Vector3(rain_radius, 1.5, rain_radius)
	_rain_particles.direction = Vector3(0.0, -1.0, 0.0)
	_rain_particles.spread = 3.0
	_rain_particles.initial_velocity_min = 4.0
	_rain_particles.initial_velocity_max = 8.0
	_rain_particles.scale_amount_min = 0.72
	_rain_particles.scale_amount_max = 1.18
	_rain_particles.mesh = streak
	add_child(_rain_particles)


func _build_audio() -> void:
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = 22050
	stream.stereo = true
	stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
	var frame_count := stream.mix_rate * 6
	var samples := PackedFloat32Array()
	samples.resize(frame_count)
	for i in frame_count:
		var white := _noise_rng.randf_range(-1.0, 1.0)
		_noise_fast = lerpf(_noise_fast, white, 0.34)
		_noise_slow = lerpf(_noise_slow, white, 0.035)
		samples[i] = (_noise_fast - _noise_slow) * 0.19 + _noise_slow * 0.06
	# Crossfade the tail into the head so the six-second loop has no click.
	var crossfade_frames := 4096
	for i in crossfade_frames:
		var t := float(i) / float(crossfade_frames - 1)
		var tail_index := frame_count - crossfade_frames + i
		samples[tail_index] = lerpf(samples[tail_index], samples[i], t)
	var pcm := PackedByteArray()
	pcm.resize(frame_count * 4)
	for i in frame_count:
		var sample := clampi(roundi(samples[i] * 32767.0), -32768, 32767)
		pcm.encode_s16(i * 4, sample)
		pcm.encode_s16(i * 4 + 2, sample)
	stream.data = pcm
	stream.loop_begin = 0
	stream.loop_end = frame_count

	_rain_audio = AudioStreamPlayer.new()
	_rain_audio.name = "rain_sound"
	_rain_audio.stream = stream
	_rain_audio.volume_db = -80.0
	add_child(_rain_audio)
	_rain_audio.play()


func _collect_wet_surfaces() -> void:
	var boardwalk := get_parent().get_node_or_null("park_world/places/boardwalk")
	if boardwalk == null:
		return
	var stack: Array[Node] = [boardwalk]
	while not stack.is_empty():
		var node: Node = stack.pop_back() as Node
		for child: Node in node.get_children():
			stack.append(child)
		var node_name := StringName(node.name)
		if not WET_SURFACE_NAMES.has(node_name):
			continue
		var instance_id: int = node.get_instance_id()
		if _wet_surface_ids.has(instance_id):
			continue
		var material := _surface_material(node)
		if not material is StandardMaterial3D:
			continue
		var wet_material := (material as StandardMaterial3D).duplicate() as StandardMaterial3D
		_assign_surface_material(node, wet_material)
		_wet_surfaces.append({
			"material": wet_material,
			"albedo": wet_material.albedo_color,
			"roughness": wet_material.roughness,
			"metallic": wet_material.metallic,
		})
		_wet_surface_ids[instance_id] = true
	_update_wet_surfaces()


func _surface_material(node: Node) -> Material:
	if node is CSGPrimitive3D:
		return (node as CSGPrimitive3D).material
	if node is MeshInstance3D:
		var mesh_instance := node as MeshInstance3D
		if mesh_instance.material_override != null:
			return mesh_instance.material_override
		if mesh_instance.mesh != null and mesh_instance.mesh.get_surface_count() > 0:
			return mesh_instance.get_active_material(0)
	return null


func _assign_surface_material(node: Node, material: Material) -> void:
	if node is CSGPrimitive3D:
		(node as CSGPrimitive3D).material = material
	elif node is MeshInstance3D:
		(node as MeshInstance3D).material_override = material


func _update_wet_surfaces() -> void:
	for entry in _wet_surfaces:
		var material := entry["material"] as StandardMaterial3D
		var base_color := entry["albedo"] as Color
		var response := wet_surface_values(base_color, float(entry["roughness"]),
			float(entry["metallic"]), wetness)
		material.albedo_color = response["albedo"] as Color
		material.roughness = float(response["roughness"])
		material.metallic = float(response["metallic"])
