extends Node

## Hands one greybox prop from the maquette to Blender as reference.
##
##     godot --headless --path . tools/run.tscn -- maquette_export \
##         <scene> <prefix> <out_name> [--whole] [--markers <scene>] [--also <scene>] [--floor W D]
##         [--set <property>=<value> ...] [--courses] [--mount <name>]
##
## `--whole` takes every mesh of `<scene>` as the prop instead of prefixed
## top-level parts, for a prop already built by hand in its own frame; the
## prefix is then ignored (pass `-`).
##
## Takes every top-level node of `<scene>` whose name starts with `<prefix>_`
## (the generator emits a prop as flat sibling parts, `bench_0_seat`,
## `bench_0_leg_l`, …), bakes CSG parts into meshes, and moves them into the
## prop's own frame: on the ground at the origin, turned so the prop faces +Z,
## which is how the game places it. The frame's yaw is the first part's, since
## all parts of one prop share it; its origin is the centre of their footprint
## at the height of their lowest point.
##
## Written to `assets/source/props/reference/<out_name>.glb`, where Godot does not
## import it (`assets/source/` carries a `.gdignore`); `tools/blender/add_reference.py`
## puts it in a prop file's locked `reference` collection. glTF is Y-up and
## Blender's importer turns it Z-up, so +Z here arrives as -Y there, the way the
## Check button expects.
##
## - `--markers <scene>` copies that scene's Marker3Ds in as named empties: the
##   seat contract of `park_furniture/plaza_bench.tscn`, so Blender measures the
##   modelled seat against the same two points the crowd uses.
## - `--also <scene>` adds another existing version beside it, 2.5 m along +X.
## - `--floor W D` adds a W × D metre floor plane at the ground, for scale.
## - `--set <property>=<value>` sets an exported property on the scene's root
##   before it builds, repeatable: the palm crown's `extra_frond_count=20`
##   exports every frond course, not only the core the scene saves with.
## - `--courses` writes every Path3D in the scene, with its transform in the
##   prop's frame, its control points and its baked points, to
##   `<out_name>_courses.json` beside the GLB, still in Godot's axes.
##   `tools/blender/add_courses.py` turns them into Blender curves.
## - `--mount <name>` adds an empty named `<name>` at the origin: the point a
##   hanging prop is placed by (a palm crown's `trunk_top`). Check reads it as
##   "this prop hangs here" instead of "this prop stands on the ground".

const OUT_DIR := "res://assets/source/props/reference"
const ALSO_OFFSET := Vector3(2.5, 0, 0)


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 4:
		push_error("usage: -- maquette_export <scene> <prefix> <out_name> [--markers <scene>] [--also <scene>] [--floor W D]")
		get_tree().quit(2)
		return
	var ok := await _export(args)
	get_tree().quit(0 if ok else 1)


## The part's mesh with the materials the *instance* gives it baked onto the
## mesh itself. Hand-built props colour a shared unit box through
## `material_override` or a surface override, and glTF only carries a mesh's
## own materials, so without this every part arrives in Blender with none.
func _with_instance_materials(mi: MeshInstance3D) -> Mesh:
	var mesh := mi.mesh
	if mesh == null:
		return null
	var overrides: Array[Material] = []
	var any := false
	for s in mesh.get_surface_count():
		var m: Material = mi.material_override
		if mi.get_surface_override_material(s) != null:
			m = mi.get_surface_override_material(s)
		overrides.append(m)
		any = any or m != null
	if not any:
		return mesh
	var copy := mesh.duplicate() as Mesh
	for s in overrides.size():
		var m := overrides[s]
		if m == null:
			continue
		if copy is PrimitiveMesh:
			(copy as PrimitiveMesh).material = m
		elif copy is ArrayMesh:
			(copy as ArrayMesh).surface_set_material(s, m)
	return copy


func _flag(args: PackedStringArray, flag: String, count := 1) -> PackedStringArray:
	var i := args.find(flag)
	if i < 0 or i + count >= args.size():
		return PackedStringArray()
	return args.slice(i + 1, i + 1 + count)


func _export(args: PackedStringArray) -> bool:
	var scene_path := args[1]
	var prefix := args[2] + "_"
	var out_name := args[3]

	var packed := load(scene_path) as PackedScene
	if packed == null:
		push_error("maquette_export: cannot load %s" % scene_path)
		return false
	var source := packed.instantiate()
	for i in args.size() - 1:
		if args[i] == "--set":
			var pair := args[i + 1].split("=", true, 1)
			source.set(pair[0], str_to_var(pair[1]))
			print("maquette_export: %s = %s" % [pair[0], source.get(pair[0])])
	add_child(source)
	# CSG shapes build their mesh on the next frame; bake after it.
	await get_tree().process_frame
	await get_tree().process_frame

	# `--whole`: the scene *is* one prop, built by hand in its own frame (on the
	# ground, at the origin, facing +Z), with its parts nested in groups. Every
	# mesh in it is a part and the frame is the scene's own.
	var whole := args.has("--whole")
	var parts: Array[Node3D] = []
	if whole:
		for n in source.find_children("*", "", true, false):
			if n is MeshInstance3D or n is CSGShape3D:
				parts.append(n)
	else:
		for child in source.get_children():
			if child is Node3D and String(child.name).begins_with(prefix):
				parts.append(child)
	if parts.is_empty():
		push_error("maquette_export: no parts in %s (prefix %s)" % [scene_path, prefix])
		return false

	var frame := Transform3D.IDENTITY
	if not whole:
		var yaw := Basis(Vector3.UP, parts[0].global_transform.basis.get_euler().y)
		frame = Transform3D(yaw, parts[0].global_position)

	var root := Node3D.new()
	root.name = out_name
	add_child(root)
	var greybox := Node3D.new()
	greybox.name = "%s_greybox" % out_name
	root.add_child(greybox)

	var low := INF
	var min_xz := Vector2(INF, INF)
	var max_xz := Vector2(-INF, -INF)
	for part in parts:
		var mesh: Mesh = null
		if part is CSGShape3D:
			mesh = (part as CSGShape3D).bake_static_mesh()
		elif part is MeshInstance3D:
			mesh = _with_instance_materials(part as MeshInstance3D)
		if mesh == null:
			continue
		var mi := MeshInstance3D.new()
		# Prefixed so the reference never takes a name the modeller will want
		# for the real part ("seat" would make hers "seat.001").
		mi.name = "greybox_" + String(part.name).trim_prefix(prefix)
		mi.mesh = mesh
		mi.transform = frame.affine_inverse() * part.global_transform
		greybox.add_child(mi)
		var box := mi.transform * mesh.get_aabb()
		low = minf(low, box.position.y)
		min_xz = min_xz.min(Vector2(box.position.x, box.position.z))
		max_xz = max_xz.max(Vector2(box.end.x, box.end.z))

	# Re-centre on the footprint and drop to the ground. A whole scene is already
	# in its own frame, and its seat contract is written against that frame, so
	# it is left exactly where it was built.
	var centre := (min_xz + max_xz) * 0.5
	var shift := Vector3.ZERO if whole else Vector3(-centre.x, -low, -centre.y)
	for mi in greybox.get_children():
		(mi as Node3D).position += shift
	print("maquette_export: %d parts of %s; frame moved by %s from the first part's origin" % [
		greybox.get_child_count(), prefix.trim_suffix("_"), shift.snappedf(0.001)])

	var markers_path := _flag(args, "--markers")
	if not markers_path.is_empty():
		var marker_scene := (load(markers_path[0]) as PackedScene).instantiate()
		for m in marker_scene.find_children("*", "Marker3D", true, false):
			var e := Node3D.new()
			e.name = m.name
			e.transform = (m as Node3D).transform
			root.add_child(e)
			print("maquette_export: marker %s at %s" % [e.name, e.position])
		marker_scene.free()

	var mount := _flag(args, "--mount")
	if not mount.is_empty():
		var e := Node3D.new()
		e.name = mount[0]
		root.add_child(e)
		print("maquette_export: mount %s at the origin" % e.name)

	if args.has("--courses") and not _write_courses(source, frame, shift, out_name):
		return false

	var also_path := _flag(args, "--also")
	if not also_path.is_empty():
		var also := (load(also_path[0]) as PackedScene).instantiate() as Node3D
		also.name = "%s_existing" % out_name
		also.position = ALSO_OFFSET
		for n in also.find_children("*", "", true, false):
			n.name = "existing_" + String(n.name)
		root.add_child(also)

	var floor_size := _flag(args, "--floor", 2)
	if floor_size.size() == 2:
		var plane := PlaneMesh.new()
		plane.size = Vector2(float(floor_size[0]), float(floor_size[1]))
		var floor_mi := MeshInstance3D.new()
		floor_mi.name = "floor"
		floor_mi.mesh = plane
		root.add_child(floor_mi)

	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT_DIR))
	var out := ProjectSettings.globalize_path("%s/%s.glb" % [OUT_DIR, out_name])
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	var err := doc.append_from_scene(root, state)
	if err == OK:
		err = doc.write_to_filesystem(state, out)
	if err != OK:
		push_error("maquette_export: glTF write failed (%s)" % error_string(err))
		return false
	print("maquette_export: wrote %s" % out)
	return true


## Every Path3D of the scene as data Blender can rebuild exactly: the course's
## transform in the prop's frame, its control points (position, in and out
## handles relative to the point, as Godot keeps them, and tilt) and its baked
## points already in the prop's frame, which `add_courses.py` measures its
## curves against. Courses that share one Curve3D resource share its id, so
## Blender can share the curve data the way the scene does.
func _write_courses(source: Node, frame: Transform3D, shift: Vector3, out_name: String) -> bool:
	var courses := []
	for n in source.find_children("*", "Path3D", true, false):
		var path := n as Path3D
		if path.curve == null:
			continue
		var t := frame.affine_inverse() * path.global_transform
		t.origin += shift
		var curve := path.curve
		var id := curve.resource_path.get_slice("::", 1) if curve.resource_path.contains("::") \
			else "curve_%d" % curve.get_instance_id()
		var points := []
		for i in curve.point_count:
			points.append({
				"position": _v(curve.get_point_position(i)),
				"in": _v(curve.get_point_in(i)),
				"out": _v(curve.get_point_out(i)),
				"tilt": curve.get_point_tilt(i),
			})
		var baked := []
		for p in curve.get_baked_points():
			baked.append(_v(t * p))
		var meta := {}
		for key in path.get_meta_list():
			meta[String(key)] = path.get_meta(key)
		courses.append({
			"name": String(path.name),
			"group": String(path.get_parent().name),
			"meta": meta,
			"curve": id,
			"transform": [_v(t.basis.x), _v(t.basis.y), _v(t.basis.z), _v(t.origin)],
			"points": points,
			"baked": baked,
			"length": curve.get_baked_length(),
		})
	var out := ProjectSettings.globalize_path("%s/%s_courses.json" % [OUT_DIR, out_name])
	var f := FileAccess.open(out, FileAccess.WRITE)
	if f == null:
		push_error("maquette_export: cannot write %s" % out)
		return false
	f.store_string(JSON.stringify({"axes": "godot", "courses": courses}, "\t"))
	f.close()
	print("maquette_export: %d courses to %s" % [courses.size(), out])
	return true


func _v(v: Vector3) -> Array:
	return [v.x, v.y, v.z]
