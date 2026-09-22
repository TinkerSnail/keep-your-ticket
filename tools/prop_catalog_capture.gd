extends Node

## Isolated source renderer for the prop catalog. The Markdown registry owns
## labels and display names; documentation/prop-catalog.json only supplies the
## scene and selection recipe. Run with a real renderer through tools/run.tscn.

const MANIFEST := "res://documentation/prop-catalog.json"
const RAW_DIR := "res://documentation/images/prop-library/raw"
const RESULT := "res://documentation/images/prop-library/capture-result.json"

var _camera: Camera3D
var _display: Node3D
var _ground: MeshInstance3D
var _errors: Array[String] = []
var _captured := 0


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(RAW_DIR))
	_build_stage()
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
	if not parsed is Dictionary or not parsed.has("recipes"):
		_finish(["manifest is not a versioned recipe dictionary"])
		return
	var recipes: Dictionary = parsed["recipes"]
	var labels: Array = recipes.keys()
	labels.sort()
	var requested := OS.get_cmdline_user_args().slice(1)
	if not requested.is_empty():
		for requested_label in requested:
			if not recipes.has(String(requested_label)):
				_finish(["unknown requested catalog label: %s" % requested_label])
				return
		labels = labels.filter(func(label: Variant) -> bool:
			return requested.has(String(label)))
	for label_value in labels:
		var label := String(label_value)
		var recipe: Dictionary = recipes[label]
		if not recipe.has("source"):
			continue
		await _capture_one(label, recipe)
	_finish(_errors)


func _build_stage() -> void:
	var environment := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("c8d4d0")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("dce4df")
	env.ambient_light_energy = 0.85
	environment.environment = env
	add_child(environment)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48.0, -32.0, 0.0)
	sun.light_color = Color("fff1cf")
	sun.light_energy = 1.25
	sun.shadow_enabled = true
	add_child(sun)

	_ground = MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(200.0, 200.0)
	var ground_material := StandardMaterial3D.new()
	ground_material.albedo_color = Color("707a75")
	ground_material.roughness = 0.92
	plane.material = ground_material
	_ground.mesh = plane
	_ground.position.y = -0.012
	add_child(_ground)

	_camera = Camera3D.new()
	_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	_camera.near = 0.03
	_camera.far = 5000.0
	_camera.current = true
	add_child(_camera)


func _capture_one(label: String, recipe: Dictionary) -> void:
	var source_path := String(recipe["source"])
	var packed := load(source_path) as PackedScene
	if packed == null:
		_errors.append("%s: could not load %s" % [label, source_path])
		return
	_display = Node3D.new()
	_display.name = "catalog_display"
	add_child(_display)
	var instance := packed.instantiate() as Node
	if instance == null:
		_errors.append("%s: could not instantiate %s" % [label, source_path])
		await _clear_display()
		return
	_display.add_child(instance)
	for _frame in 3:
		await get_tree().process_frame

	var scope: Node = instance
	var anchor := String(recipe.get("anchor", ""))
	if not anchor.is_empty():
		scope = instance.find_child(anchor, true, false)
		if scope == null:
			_errors.append("%s: anchor '%s' is missing in %s" % [label, anchor, source_path])
			await _clear_display()
			return
	var names := _string_array(recipe.get("names", []))
	var prefixes := _string_array(recipe.get("prefixes", []))
	_filter_visuals(instance, scope, names, prefixes)
	await get_tree().process_frame
	var bounds := _visible_bounds(instance)
	if bounds.size == Vector3.ZERO:
		_errors.append("%s: selection has no visible geometry" % label)
		await _clear_display()
		return

	var centre := bounds.get_center()
	_display.position -= Vector3(centre.x, bounds.position.y, centre.z)
	await get_tree().process_frame
	bounds = _visible_bounds(instance)
	_frame_camera(bounds, recipe)
	for _frame in 2:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var output := "%s/%s.png" % [RAW_DIR, label.to_lower()]
	var save_error := get_viewport().get_texture().get_image().save_png(output)
	if save_error != OK:
		_errors.append("%s: could not save %s (%s)" % [label, output, error_string(save_error)])
	else:
		_captured += 1
		print("prop catalog saved ", output)
	await _clear_display()


func _string_array(value: Variant) -> Array[String]:
	var out: Array[String] = []
	if value is Array:
		for item in value:
			out.append(String(item))
	return out


func _filter_visuals(instance: Node, scope: Node, names: Array[String], prefixes: Array[String]) -> void:
	var selective := not names.is_empty() or not prefixes.is_empty()
	for node in instance.find_children("*", "GeometryInstance3D", true, false):
		var visual := node as GeometryInstance3D
		if not scope.is_ancestor_of(visual) and visual != scope:
			visual.visible = false
			continue
		if selective:
			visual.visible = _matches_selection(visual, scope, names, prefixes)
	for node in instance.find_children("*", "Light3D", true, false):
		var light := node as Light3D
		light.visible = false


func _matches_selection(node: Node, scope: Node, names: Array[String], prefixes: Array[String]) -> bool:
	var current: Node = node
	while current != null:
		var node_name := String(current.name)
		if names.has(node_name):
			return true
		for prefix in prefixes:
			if node_name.begins_with(prefix):
				return true
		if current == scope:
			break
		current = current.get_parent()
	return false


func _visible_bounds(instance: Node) -> AABB:
	var found := false
	var minimum := Vector3.ZERO
	var maximum := Vector3.ZERO
	for node in instance.find_children("*", "GeometryInstance3D", true, false):
		var visual := node as GeometryInstance3D
		if not visual.visible:
			continue
		var local := visual.get_aabb()
		for endpoint in 8:
			var point := visual.global_transform * local.get_endpoint(endpoint)
			if not found:
				minimum = point
				maximum = point
				found = true
			else:
				minimum = minimum.min(point)
				maximum = maximum.max(point)
	if not found:
		return AABB()
	return AABB(minimum, maximum - minimum)


func _frame_camera(bounds: AABB, recipe: Dictionary) -> void:
	var target := bounds.get_center()
	var yaw := deg_to_rad(float(recipe.get("yaw", 32.0)))
	var elevation := deg_to_rad(float(recipe.get("elevation", 22.0)))
	var horizontal := maxf(bounds.size.x, bounds.size.z)
	var frame_height := maxf(bounds.size.y * 1.3, horizontal * 0.82)
	_camera.size = maxf(frame_height, 0.8) * float(recipe.get("padding", 1.15))
	var radius := maxf(bounds.size.length() * 2.0, 4.0)
	var direction := Vector3(sin(yaw) * cos(elevation), sin(elevation), cos(yaw) * cos(elevation))
	_camera.global_position = target + direction * radius
	_camera.look_at(target, Vector3.UP)


func _clear_display() -> void:
	if _display != null and is_instance_valid(_display):
		_display.queue_free()
		await get_tree().process_frame
	_display = null


func _finish(errors: Array) -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(RAW_DIR))
	var file := FileAccess.open(RESULT, FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify({"captured": _captured, "errors": errors}, "  "))
	get_tree().quit(0 if errors.is_empty() else 1)
