extends SceneTree
## Dev probe: what in the generated park moved between two runs of the
## generator, and was it standing on ground that moved? Written 2026-10-05 for
## Stage 2 of `documentation/terrain-master-into-game-plan-2026-10-05.md`, to
## show that an edit to the world terrain master carries what stands on it.
##
##   Godot --headless --path . --script res://tools/_ground_follow_probe.gd -- --dump=/abs/dir
##   Godot --headless --path . --script res://tools/_ground_follow_probe.gd -- --compare=/abs/before,/abs/after
##
## `--dump` writes every generated scene's node positions and mesh vertices, in
## world space, to one file per scene. `--compare` reads two dumps and prints,
## per scene, how many nodes moved and meshes changed, the largest rise, and
## each moved thing's offset from what `scripts/world_terrain_source.gd` reads
## under it now: a thing that followed the ground moved by about that much.
## Writes nothing in the project.

const WorldTerrainSource := preload("res://scripts/world_terrain_source.gd")
const GENERATED := "res://scenes/world/generated"


func _init() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--dump="):
			_dump(arg.trim_prefix("--dump="))
		elif arg.begins_with("--compare="):
			var dirs := arg.trim_prefix("--compare=").split(",")
			_compare(dirs[0], dirs[1])
	quit()


func _dump(dir: String) -> void:
	DirAccess.make_dir_recursive_absolute(dir)
	for file in DirAccess.get_files_at(GENERATED):
		if not file.ends_with(".tscn"):
			continue
		var root := (ResourceLoader.load(GENERATED.path_join(file), "",
			ResourceLoader.CACHE_MODE_IGNORE) as PackedScene).instantiate()
		var record := {}
		_walk(root, root, Transform3D.IDENTITY, record)
		var out := FileAccess.open(dir.path_join(file.get_basename() + ".bin"), FileAccess.WRITE)
		out.store_var(record)
		out.close()
		root.free()
		print("dumped %s: %d nodes" % [file, record.size()])


func _walk(node: Node, root: Node, parent: Transform3D, record: Dictionary) -> void:
	var xf := parent
	if node is Node3D:
		xf = parent * (node as Node3D).transform
	var path := String(root.get_path_to(node))
	var entry := [xf.origin]
	if node is MeshInstance3D and (node as MeshInstance3D).mesh != null:
		var mesh := (node as MeshInstance3D).mesh
		var verts := PackedVector3Array()
		for s in mesh.get_surface_count():
			for v in (mesh.surface_get_arrays(s)[Mesh.ARRAY_VERTEX] as PackedVector3Array):
				verts.append(xf * v)
		entry.append(verts)
	record[path] = entry
	for child in node.get_children():
		_walk(child, root, xf, record)


func _compare(before: String, after: String) -> void:
	var ground := WorldTerrainSource.new()
	print(ground.summary())
	var total_moved := 0
	var total_off := 0
	for file in DirAccess.get_files_at(before):
		if not file.ends_with(".bin"):
			continue
		var a: Dictionary = FileAccess.open(before.path_join(file), FileAccess.READ).get_var()
		var b: Dictionary = FileAccess.open(after.path_join(file), FileAccess.READ).get_var()
		var moved := 0
		var reshaped := 0
		var gone := 0
		var rise := 0.0
		var fall := 0.0
		var off := 0
		var worst_off := 0.0
		var example := ""
		for path in a:
			if not b.has(path):
				gone += 1
				continue
			var ea: Array = a[path]
			var eb: Array = b[path]
			var pa: Vector3 = ea[0]
			var pb: Vector3 = eb[0]
			if pa != pb:
				moved += 1
				var d := pb.y - pa.y
				rise = maxf(rise, d)
				fall = minf(fall, d)
				var want := ground.delta_y(Vector2(pb.x, pb.z))
				if absf(d - want) > 0.05 or Vector2(pa.x, pa.z) != Vector2(pb.x, pb.z):
					off += 1
					if absf(d - want) > worst_off:
						worst_off = absf(d - want)
						example = "%s at (%.1f, %.1f) rose %+.3f where the ground rose %+.3f" % [
							path, pb.x, pb.z, d, want]
			if ea.size() > 1 and eb.size() > 1 and ea[1] != eb[1]:
				reshaped += 1
				var va: PackedVector3Array = ea[1]
				var vb: PackedVector3Array = eb[1]
				if va.size() == vb.size():
					for i in va.size():
						var d := vb[i].y - va[i].y
						rise = maxf(rise, d)
						fall = minf(fall, d)
		var added := 0
		for path in b:
			if not a.has(path):
				added += 1
		total_moved += moved + reshaped
		total_off += off
		if moved + reshaped + gone + added == 0:
			print("%-24s same" % file.get_basename())
			continue
		print("%-24s %d nodes moved, %d meshes changed, %d gone, %d new; %+.2f..%+.2fm; %d moved by other than the ground under them%s" % [
			file.get_basename(), moved, reshaped, gone, added, fall, rise, off,
			(" (worst %.2fm: %s)" % [worst_off, example]) if off > 0 else ""])
	print("ground_follow: %d things moved or changed; %d nodes moved by other than the ground under them" % [total_moved, total_off])
