extends SceneTree
## Dev probe: the faces of the ground the generator still holds, exactly as Godot loads them.
## Written 2026-10-12 for Stage 1, Bake, of `documentation/terrain-height-grid-plan-2026-10-12.md`;
## since Stage 5 (2026-10-15) its reader is `tools/blender/ground_build.py`, which dumps them
## itself to stitch the grid's tiles to the held ground's edges.
##
##   Godot --headless --path . --script res://tools/_ground_faces_dump.gd -- --out=/abs/dir
##   Godot --headless --path . --script res://tools/_ground_faces_dump.gd -- --read=/abs/exr_dir,/abs/out_dir
##
## `--out` writes, each a raw little-endian float32 file, (x, y, z) a corner, Godot world metres:
##   `held.f32`      every collider of the ground the generator still holds and
##                   the grid meets: `places/park_groundworks` (the road
##                   corridor, the tunnel lids, the east shoulder walls, the
##                   promenade banks), `places/west_shell`, and the two anchors,
##                   `places/west_stair` (NT-1) and `places/east_cascade` (NT-2),
##                   from their collision shapes as the physics sees them (a CSG
##                   root's baked collision, a body's ConcavePolygonShape3D),
##                   three corners a face;
##   `held_open.f32` each held collider's open edges, two corners an edge: the
##                   edges one face uses, corners matched bit for bit.
## and `faces.json`: per file, its pieces in order (name or path, first face or
## edge, count), and the header (commit, Godot, what changed in the tree).
##
## Until Stage 5 `--out` also wrote the world terrain master's ground pieces and their frozen
## copy (`master.f32`, `baseline.f32`) for `tools/ground_bake.py`'s bake, and `--delta` read
## the generator's `delta_y` at given points for its proof; both are in git up to `a8cd64b`.
##
## `--read` loads every `.exr` in a folder with `Image.load_from_file` and
## writes `<name>.bin` (the image's raw data) and `<name>.json` (size and
## format) beside each other in the out folder: Godot's reading of the grid's
## tiles, to hold against another reader's.
##
## Writes nothing in the project. Prints one line per piece; returns 0, or 1.

const WorldTerrainSource := preload("res://scripts/world_terrain_source.gd")
const HELD := {
	"park_groundworks": "res://scenes/world/park_groundworks.tscn",
	"west_shell": "res://scenes/world/west_shell.tscn",
	"west_stair": "res://scenes/world/west_stair.tscn",
	"east_cascade": "res://scenes/world/east_cascade.tscn",
}


func _initialize() -> void:
	var code := 1
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):
			code = await _dump(arg.trim_prefix("--out="))
		elif arg.begins_with("--read="):
			var pair := arg.trim_prefix("--read=").split(",")
			code = _read(pair[0], pair[1])
	if code != 0:
		printerr("ground faces dump: pass --out=<dir> or --read=<dir>,<out>")
	quit(code)


func _dump(dir: String) -> int:
	DirAccess.make_dir_recursive_absolute(dir)
	var t0 := Time.get_ticks_msec()
	var index := {"header": _header()}

	# The held scenes as `park_world.tscn` mounts them (at the origin, under
	# `places`), in the tree, so every CSG root has built its shape.
	var places := Node3D.new()
	places.name = "places"
	root.add_child(places)
	for name in HELD:
		var scene := (load(HELD[name]) as PackedScene).instantiate()
		scene.name = name
		places.add_child(scene)
	for i in 4:
		await process_frame
		await physics_frame
	var held := {}
	var open := {}
	var kinds := {}
	for name in HELD:
		var scene := places.get_node(name)
		for n in [scene] + scene.find_children("*", "", true, false):
			var faces := _collision_faces(n)
			if faces.is_empty():
				continue
			var path := "places/" + str(places.get_path_to(n))
			held[path] = faces
			open[path] = _open_edges(faces)
			kinds[path] = "csg" if n is CSGShape3D else "body"
	index["held"] = _write_pieces(dir.path_join("held.f32"), held, 3)
	for rec in index["held"]:
		rec["kind"] = kinds[rec["name"]]
	index["held_open"] = _write_pieces(dir.path_join("held_open.f32"), open, 2)
	places.free()

	index["header"]["seconds"] = (Time.get_ticks_msec() - t0) / 1000.0
	var f := FileAccess.open(dir.path_join("faces.json"), FileAccess.WRITE)
	f.store_string(JSON.stringify(index, " ", false) + "\n")
	f.close()
	var faces_n := 0
	for rec in index["held"]:
		faces_n += int(rec["count"])
	var edges_n := 0
	for rec in index["held_open"]:
		edges_n += int(rec["count"])
	print("ground faces dump: held %d faces in %d colliders with %d open edges; %.1fs; %s" % [
		faces_n, held.size(), edges_n, index["header"]["seconds"], dir])
	return 0


func _header() -> Dictionary:
	return {
		"what": "The faces of the ground the generator still holds, as Godot loads them, for the height grid's tiles.",
		"probe": "res://tools/_ground_faces_dump.gd",
		"written": Time.get_datetime_string_from_system(true) + "Z",
		"commit": _git(["rev-parse", "HEAD"]),
		"modified_tracked_in_scenes_assets_scripts": Array(_git(["status", "--porcelain", "--untracked-files=no", "--", "scenes", "assets", "scripts"]).split("\n", false)),
		"godot": Engine.get_version_info()["string"],
		"layout": "raw little-endian float32; faces three corners each, open edges two; a corner is (x, y, z), Godot world metres, y up, x east, z south",
	}


func _write_pieces(path: String, pieces: Dictionary, per: int) -> Array:
	var out: Array = []
	var first := 0
	var f := FileAccess.open(path, FileAccess.WRITE)
	var names: Array = pieces.keys()
	names.sort()
	for name in names:
		var arr: PackedVector3Array = pieces[name]
		var n := arr.size() / per
		out.append({"name": name, "first": first, "count": n})
		f.store_buffer(arr.to_byte_array())
		first += n
	f.close()
	print("  %s: %d pieces, %d %s" % [path.get_file(), out.size(), first, "faces" if per == 3 else "edges"])
	return out


## A collider's faces in world space as the physics has them, or none.
func _collision_faces(n: Node) -> PackedVector3Array:
	var out := PackedVector3Array()
	if n is CSGShape3D:
		var csg := n as CSGShape3D
		if not (csg.is_root_shape() and csg.use_collision):
			return out
		var shape := csg.bake_collision_shape()
		if shape == null:
			return out
		var xf := WorldTerrainSource._world_xf(csg)
		for v in shape.get_faces():
			out.append(xf * v)
		return out
	if n is CollisionObject3D:
		for c in n.get_children():
			var cs := c as CollisionShape3D
			if cs == null or cs.disabled or cs.shape == null:
				continue
			var xf := WorldTerrainSource._world_xf(cs)
			if cs.shape is ConcavePolygonShape3D:
				for v in (cs.shape as ConcavePolygonShape3D).get_faces():
					out.append(xf * v)
			else:
				# A box or other convex shape: its debug mesh's faces are its faces.
				var mesh := cs.shape.get_debug_mesh()
				for v in mesh.get_faces():
					out.append(xf * v)
	return out


## The edges one face uses, corners matched bit for bit, each as its face gives it.
func _open_edges(faces: PackedVector3Array) -> PackedVector3Array:
	var count := {}
	var first := {}
	for t in range(0, faces.size(), 3):
		for k in 3:
			var a := faces[t + k]
			var b := faces[t + (k + 1) % 3]
			var key := _edge_key(a, b)
			count[key] = int(count.get(key, 0)) + 1
			if not first.has(key):
				first[key] = [a, b]
	var out := PackedVector3Array()
	for key in count:
		if int(count[key]) == 1:
			out.append(first[key][0])
			out.append(first[key][1])
	return out


func _edge_key(a: Vector3, b: Vector3) -> String:
	var ka := PackedVector3Array([a]).to_byte_array().hex_encode()
	var kb := PackedVector3Array([b]).to_byte_array().hex_encode()
	return ka + kb if ka <= kb else kb + ka


func _read(exr_dir: String, out_dir: String) -> int:
	DirAccess.make_dir_recursive_absolute(out_dir)
	var n := 0
	var files := Array(DirAccess.get_files_at(exr_dir))
	files.sort()
	for file in files:
		if not String(file).ends_with(".exr"):
			continue
		var img := Image.load_from_file(exr_dir.path_join(file))
		if img == null:
			printerr("ground faces dump: cannot read ", file)
			return 1
		var base := out_dir.path_join(String(file).get_basename())
		var f := FileAccess.open(base + ".bin", FileAccess.WRITE)
		f.store_buffer(img.get_data())
		f.close()
		var meta := {"width": img.get_width(), "height": img.get_height(),
			"format": img.get_format(), "format_name": _format_name(img.get_format()),
			"mipmaps": img.has_mipmaps()}
		f = FileAccess.open(base + ".json", FileAccess.WRITE)
		f.store_string(JSON.stringify(meta) + "\n")
		f.close()
		n += 1
	print("ground faces dump: read %d EXR into %s" % [n, out_dir])
	return 0 if n > 0 else 1


func _format_name(format: int) -> String:
	match format:
		Image.FORMAT_RF:
			return "RF"
		Image.FORMAT_RGF:
			return "RGF"
		Image.FORMAT_RGBF:
			return "RGBF"
		Image.FORMAT_RGBAF:
			return "RGBAF"
		Image.FORMAT_RH:
			return "RH"
		Image.FORMAT_RGBAH:
			return "RGBAH"
	return str(format)


func _git(args: Array) -> String:
	var out := []
	OS.execute("git", PackedStringArray(["-C", ProjectSettings.globalize_path("res://")] + args), out, true)
	return (out[0] as String).strip_edges(false, true) if not out.is_empty() else ""
