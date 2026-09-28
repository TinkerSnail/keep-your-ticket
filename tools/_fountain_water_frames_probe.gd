extends Node

## Probe, 2026-09-27: does the plaza fountain's water look the same from Blender
## as it did from the generator?
##
## `_fountain_migration_probe compare` proves the shapes, materials and shadow
## settings equal. What it cannot see is drawing: the falls, jets, plume and
## spray are blended and write no depth, so Godot sorts them object by object,
## and since the move each ring of falls or jets is one object where each fall
## and each jet was its own. This shoots the same views of either fountain at
## the same frames, so the two can be compared pixel by pixel.
##
##   open -n -a /Applications/Godot.app --args --path "$PWD" --fixed-fps 60 \
##       --resolution 1280x720 tools/run.tscn -- _fountain_water_frames_probe <which> <out_dir>
##
## `<which>` is `new` (`scenes/world/plaza_fountain.tscn`) or an absolute path to
## the old generated scene (`git show 2f02612:scenes/world/generated/plaza_fountain.tscn`).
## Needs the real renderer: not `--headless`. Writes `<out_dir>/<view>_<day|night>_<n>.png`
## and `<out_dir>/done` last. `--fixed-fps` keeps the water's clock the same
## from run to run, so two runs of one fountain give the same frames.

const VIEWS := {
	# From the ring walkway, eye height, the falls ringing the basins.
	"ring_south": [Vector3(0.0, 1.6, 14.0), Vector3(0.0, 3.0, 0.0)],
	# At the kerb looking up: near jets over far falls, the plume above.
	"kerb_up": [Vector3(3.0, 1.6, 9.8), Vector3(0.0, 4.5, 0.0)],
	# Diagonal, mid distance.
	"diagonal": [Vector3(-16.0, 1.6, -12.0), Vector3(0.0, 2.5, 0.0)],
	# From up the entrance street: the plume against the sky.
	"street": [Vector3(0.0, 1.6, 40.0), Vector3(0.0, 4.0, 0.0)],
	# Grazing along the pool: jets in a row, one behind another.
	"along_jets": [Vector3(11.0, 1.2, 1.7), Vector3(-6.5, 1.4, 1.7)],
}
const SETTLE_FRAMES := 90
const GAP_FRAMES := 7

var _out := ""


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 3:
		push_error("usage: -- _fountain_water_frames_probe <new|/abs/old.tscn> <out_dir>")
		get_tree().quit(2)
		return
	var which := args[1]
	_out = args[2]
	DirAccess.make_dir_recursive_absolute(_out)
	var path := "res://scenes/world/plaza_fountain.tscn" if which == "new" else which
	var fountain := (ResourceLoader.load(path, "", ResourceLoader.CACHE_MODE_IGNORE)
		as PackedScene).instantiate()
	add_child(fountain)
	_stage()
	var camera := Camera3D.new()
	camera.fov = 70.0
	camera.far = 500.0
	add_child(camera)
	camera.make_current()

	for night in [false, true]:
		RenderingServer.global_shader_parameter_set("park_night", 1.0 if night else 0.0)
		($Sun as DirectionalLight3D).light_energy = 0.08 if night else 1.4
		($Env as WorldEnvironment).environment.background_energy_multiplier = 0.05 if night else 1.0
		($Env as WorldEnvironment).environment.ambient_light_energy = 0.15 if night else 0.8
		for view in VIEWS:
			camera.look_at_from_position(VIEWS[view][0], VIEWS[view][1])
			await _frames(SETTLE_FRAMES)
			await _shoot("%s_%s_0" % [view, "night" if night else "day"])
			await _frames(GAP_FRAMES)
			await _shoot("%s_%s_1" % [view, "night" if night else "day"])
	FileAccess.open(_out.path_join("done"), FileAccess.WRITE).store_string("done")
	get_tree().quit()


## A plain floor in the plaza's brick colour, a sun with shadows, and a sky.
func _stage() -> void:
	var floor_mi := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(200, 200)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.62, 0.42, 0.34)
	mat.roughness = 0.9
	plane.material = mat
	floor_mi.mesh = plane
	floor_mi.position.y = -0.002
	add_child(floor_mi)

	var sun := DirectionalLight3D.new()
	sun.name = "Sun"
	sun.shadow_enabled = true
	sun.rotation_degrees = Vector3(-38.0, 35.0, 0.0)
	add_child(sun)

	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = Sky.new()
	env.sky.sky_material = ProceduralSkyMaterial.new()
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var world := WorldEnvironment.new()
	world.name = "Env"
	world.environment = env
	add_child(world)


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _shoot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(_out.path_join(name + ".png"))
