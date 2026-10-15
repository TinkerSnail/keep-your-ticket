extends SceneTree
## Mounts the ground grid's built tiles as one scene (2026-10-13, Stage 2 of
## `documentation/terrain-height-grid-plan-2026-10-12.md`).
##
##   Godot --headless --path . --script res://tools/ground_mount.gd
##   Godot --headless --path . --script res://tools/ground_mount.gd -- [--tiles=res://<dir>]
##       [--textures=res://<dir>] [--out=res://<scene>.tscn] [--check]
##
## For every tile of `assets/source/world_ground/grid.json` whose mesh the build wrote,
## `<tiles>/x{tx}_z{tz}.glb` (one mesh object `ground_x{tx}_z{tz}` with `-col`, its node at the
## tile's (x0, 0, z0), its vertices tile-local, UV0 = ((x - x0) / 1000, (z - z0) / 1000)), it
## - makes the tile's colour texture from Christina's painted PNG,
##   `assets/source/world_ground/colour/x{tx}_z{tz}.png`, read bit for bit by
##   `Image.load_from_file`: premultiplied by its alpha, mipmapped, lossless, saved as
##   `<textures>/x{tx}_z{tz}.res`, and saved only if it changed. A PNG under `assets/source/` is
##   never imported (that folder's `.gdignore` keeps Godot out of the Blender sources), and a
##   `--script` run cannot import one anyway, so the texture is a resource written here, as
##   `gen_props.gd` writes its own;
## - instances the tile's GLB under `world_ground` and gives its mesh its own ShaderMaterial of
##   `assets/shaders/ground_grid.gdshader` with that texture;
## and writes `<out>`, by default `scenes/world/world_ground.tscn`. That scene is pure tool
## output, like the crowd scenes: never edit it by hand; change the tiles, the colour or this
## tool and run it again.
##
## Since Stage 4 (2026-10-14) it mounts the outer tier too, where `grid.json` has one: every
## `<outer>/x{ox}_z{oz}.glb` (`res://assets/world_ground/outer`; one mesh `ground_outer_x{ox}_z{oz}`,
## 4 km tiles, UV0 = local / 4000) as `outer_x{ox}_z{oz}`, its colour made the same way from
## `assets/source/world_ground/outer/colour/x{ox}_z{oz}.png` into `<textures>/outer_x{ox}_z{oz}.res`,
## and checks it the same way against its own tile size.
##
## A run that changes nothing writes nothing: a texture is saved only when what it would hold
## differs, and the scene only when it differs by more than its root's unique_id.
##
## Then it loads what it wrote, fresh, and checks every tile: mounted once, its mesh inside its
## own square, its UVs (x - x0) / 1000 and (z - z0) / 1000 at every vertex, its collision there,
## its material this shader with this tile's texture, and the texture's full-size level the PNG
## premultiplied, byte for byte. `--check` does only that, on the scene already written. Exits
## 1 if anything fails. The tile GLBs must have been imported first (`Godot --import`, under
## the import lock when other sessions share the tree).

const GRID := "res://assets/source/world_ground/grid.json"
const COLOUR := "res://assets/source/world_ground/colour"
const OUTER_COLOUR := "res://assets/source/world_ground/outer/colour"
const OUTER := "res://assets/world_ground/outer"
const SHADER := "res://assets/shaders/ground_grid.gdshader"
const TILES := "res://assets/world_ground/tiles"
const TEXTURES := "res://assets/world_ground/colour"
const OUT := "res://scenes/world/world_ground.tscn"
## How far a vertex may sit from where its UV says, and outside its tile, in metres: float32
## at 1000 m is 6e-5 m, so this only forgives mesh compression, which would show here.
const TOLERANCE := 0.01
const HEADER := [
	"; Pure output of tools/ground_mount.gd: never edit this file by hand. It mounts the ground",
	"; grid's tile meshes (assets/world_ground/tiles/) and gives each its own material of",
	"; assets/shaders/ground_grid.gdshader with its tile's colour, made from Christina's painted",
	"; assets/source/world_ground/colour/. Change those, or the tool, and run it again.",
]

var _failures := 0


func _initialize() -> void:
	var opts := {"tiles": TILES, "outer": OUTER, "textures": TEXTURES, "out": OUT, "check": false}
	for arg in OS.get_cmdline_user_args():
		if arg == "--check":
			opts["check"] = true
		elif arg.begins_with("--") and "=" in arg:
			var kv := arg.trim_prefix("--").split("=", true, 1)
			if not opts.has(kv[0]):
				_fail_out("unknown option %s" % arg)
				return
			opts[kv[0]] = kv[1]
		else:
			_fail_out("unknown option %s" % arg)
			return
	var grid := _grid()
	if grid.is_empty():
		_fail_out("cannot read %s" % GRID)
		return
	var tiles := _tiles_present(grid, opts)
	if tiles.is_empty():
		_fail_out("no tile GLBs in %s" % opts["tiles"])
		return
	if not opts["check"]:
		if not _mount(grid, tiles, opts):
			_fail_out("mount failed")
			return
	_check(grid, tiles, opts)
	print("ground_mount: %d tiles, %s" % [tiles.size(), "PASS" if _failures == 0 else "%d FAILURES" % _failures])
	quit(0 if _failures == 0 else 1)


func _fail_out(message: String) -> void:
	push_error("ground_mount: " + message)
	quit(1)


func _fail(message: String) -> void:
	_failures += 1
	printerr("  FAIL " + message)


## grid.json, with its tile ranges spelt out.
func _grid() -> Dictionary:
	var g = JSON.parse_string(FileAccess.get_file_as_string(GRID))
	if typeof(g) != TYPE_DICTIONARY:
		return {}
	var spacing := float(g["spacing_m"])
	var tile := float(g["tile_m"])
	var samples := int(g["tile_samples"])
	if absf((samples - 1) * spacing - tile) > 1e-9:
		push_error("grid.json: tile_samples does not span tile_m")
		return {}
	var out := {"spacing": spacing, "tile": tile, "samples": samples,
		"tiles_x": range(int(g["tiles_x"][0]), int(g["tiles_x"][1]) + 1),
		"tiles_z": range(int(g["tiles_z"][0]), int(g["tiles_z"][1]) + 1)}
	if g.has("outer"):
		var o: Dictionary = g["outer"]
		if absf((int(o["tile_samples"]) - 1) * float(o["spacing_m"]) - float(o["tile_m"])) > 1e-9:
			push_error("grid.json: the outer tier's tile_samples does not span its tile_m")
			return {}
		out["outer"] = {"tile": float(o["tile_m"]), "samples": int(o["tile_samples"]),
			"tiles_x": range(int(o["tiles_x"][0]), int(o["tiles_x"][1]) + 1),
			"tiles_z": range(int(o["tiles_z"][0]), int(o["tiles_z"][1]) + 1)}
	return out


## The grid's tiles that have a GLB, inner then outer, each a Dictionary of what mounting and
## checking it needs; a GLB the editor has not imported fails.
func _tiles_present(grid: Dictionary, opts: Dictionary) -> Array:
	var out := []
	var tiers := [["", grid, opts["tiles"], COLOUR]]
	if grid.has("outer"):
		tiers.append(["outer_", grid["outer"], opts["outer"], OUTER_COLOUR])
	for tier in tiers:
		var prefix: String = tier[0]
		var spec: Dictionary = tier[1]
		for tz in spec["tiles_z"]:
			for tx in spec["tiles_x"]:
				var glb := "%s/x%d_z%d.glb" % [tier[2], tx, tz]
				if not FileAccess.file_exists(glb):
					continue
				if not ResourceLoader.exists(glb):
					_fail("%s is not imported; run Godot --import first" % glb)
					continue
				var name := "%sx%d_z%d" % [prefix, tx, tz]
				out.append({"tx": tx, "tz": tz, "name": name, "mesh": "ground_" + name, "glb": glb,
					"png": "%s/x%d_z%d.png" % [tier[3], tx, tz], "texture": "%s/%s.res" % [opts["textures"], name],
					"tile": float(spec["tile"]), "samples": int(spec["samples"])})
	return out


## The tile's painted colour as the shader samples it: RGBA8, premultiplied, mipmapped.
func _colour_image(t: Dictionary) -> Image:
	var samples: int = t["samples"]
	var png := ProjectSettings.globalize_path(t["png"])
	var img := Image.load_from_file(png)
	if img == null or img.get_width() != samples or img.get_height() != samples:
		_fail("%s: missing or not %d x %d" % [png, samples, samples])
		return null
	if img.get_format() != Image.FORMAT_RGBA8:
		img.convert(Image.FORMAT_RGBA8)
	img.premultiply_alpha()
	img.generate_mipmaps()
	return img


## Saves the tile's texture if its pixels changed, and returns it as loaded from disk.
##
## "Changed" is against what the file would hold, not the image itself: the lossless packer
## stores each mip level without alpha when Godot's `Image.detect_alpha` finds none (it counts
## 254 as opaque), so a small level whose alphas are all 254 or 255 comes back with 255. That is
## why x-1_z6 (one 7 x 7 level's corner at 254) was rewritten on every run (2026-10-14). The
## image is compared first as it is; only when that differs is it packed and compared as it
## would read back, which is also what is saved.
func _texture(img: Image, path: String) -> Texture2D:
	var had: Image = null
	if ResourceLoader.exists(path):
		var old := ResourceLoader.load(path, "", ResourceLoader.CACHE_MODE_IGNORE) as Texture2D
		if old != null:
			had = old.get_image()
			if had != null and had.has_mipmaps() and had.get_data() == img.get_data():
				return ResourceLoader.load(path, "", ResourceLoader.CACHE_MODE_REPLACE) as Texture2D
	var tex := PortableCompressedTexture2D.new()
	# Without this the class drops its pixels once the GPU has them and saves an empty stub
	# (gen_props.gd, `_save_texture`).
	tex.keep_compressed_buffer = true
	tex.create_from_image(img, PortableCompressedTexture2D.COMPRESSION_MODE_LOSSLESS)
	if had != null and had.has_mipmaps():
		var packed := tex.get_image()
		if packed != null and packed.get_format() == had.get_format() and packed.get_data() == had.get_data():
			return ResourceLoader.load(path, "", ResourceLoader.CACHE_MODE_REPLACE) as Texture2D
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path.get_base_dir()))
	var err := ResourceSaver.save(tex, path)
	if err != OK:
		_fail("cannot save %s (%d)" % [path, err])
		return null
	print("  wrote %s" % path)
	return ResourceLoader.load(path, "", ResourceLoader.CACHE_MODE_REPLACE) as Texture2D


func _mount(grid: Dictionary, tiles: Array, opts: Dictionary) -> bool:
	var shader := load(SHADER) as Shader
	if shader == null:
		_fail("cannot load %s" % SHADER)
		return false
	var root := Node3D.new()
	root.name = "world_ground"
	root.editor_description = "Pure output of tools/ground_mount.gd; never edit by hand. The ground grid's tiles, each with its own material of ground_grid.gdshader and its tile's colour from assets/source/world_ground/colour/."
	for t in tiles:
		var img := _colour_image(t)
		if img == null:
			continue
		var tex := _texture(img, t["texture"])
		if tex == null:
			continue
		# GEN_EDIT_STATE_INSTANCE keeps the GLB's own state on the instance, as the editor does, so
		# packing saves only what differs from it (the material) and not a copy of the mesh.
		var inst := (load(t["glb"]) as PackedScene).instantiate(PackedScene.GEN_EDIT_STATE_INSTANCE)
		inst.name = t["name"]
		root.add_child(inst)
		inst.owner = root
		var mesh := inst.find_child(t["mesh"], true, false) as MeshInstance3D
		if mesh == null:
			_fail("%s has no mesh named %s" % [t["glb"], t["mesh"]])
			continue
		var mat := ShaderMaterial.new()
		mat.resource_name = "ground_colour_" + String(t["name"])
		mat.shader = shader
		mat.set_shader_parameter("colour", tex)
		mat.set_shader_parameter("tile_samples", float(t["samples"]))
		mesh.material_override = mat
		# The mesh is inside the tile's instance: its override is saved only if the instance's
		# children are editable, as the editor's Editable Children does.
		root.set_editable_instance(inst, true)
	var packed := PackedScene.new()
	var err := packed.pack(root)
	root.free()
	if err != OK:
		_fail("pack failed (%d)" % err)
		return false
	# If the scene differs from the one already there only by the unique_id Godot rolls on every
	# save, the old bytes go back: a run on unchanged tiles and colour leaves the file as it was
	# (2026-10-14). It is saved at its own path because the text saver's resource ids depend on it.
	var path: String = opts["out"]
	var had := FileAccess.get_file_as_string(path) if FileAccess.file_exists(path) else ""
	err = ResourceSaver.save(packed, path)
	if err != OK:
		_fail("cannot save %s (%d)" % [path, err])
		return false
	var text := _with_header(FileAccess.get_file_as_string(path))
	var same := had != "" and _without_ids(had) == _without_ids(text)
	if same:
		text = had
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		_fail("cannot write %s (%d)" % [path, FileAccess.get_open_error()])
		return false
	f.store_string(text)
	f.close()
	print("  %s %s, %d tiles" % ["unchanged:" if same else "wrote", path, tiles.size()])
	return true


## Puts HEADER under the scene's first line, where a .tscn keeps its comments.
func _with_header(text: String) -> String:
	var lines := text.split("\n")
	var out := PackedStringArray([lines[0], ""])
	out.append_array(PackedStringArray(HEADER))
	for i in range(1, lines.size()):
		out.append(lines[i])
	return "\n".join(out)


## The scene's text without the unique_id Godot gives each node on every save.
func _without_ids(text: String) -> String:
	var re := RegEx.create_from_string(" unique_id=[0-9]+")
	return re.sub(text, "", true)


func _check(grid: Dictionary, tiles: Array, opts: Dictionary) -> void:
	var packed := ResourceLoader.load(opts["out"], "", ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
	if packed == null:
		_fail("cannot load %s" % opts["out"])
		return
	var text := FileAccess.get_file_as_string(opts["out"])
	for kind in ["ArrayMesh", "ConcavePolygonShape3D", "StandardMaterial3D"]:
		if ('type="%s"' % kind) in text:
			_fail("%s holds a copy of a tile's %s; only the materials belong in it" % [opts["out"], kind])
	var scene := packed.instantiate()
	var worst_uv := 0.0
	var worst_out := 0.0
	var vertices := 0
	for t in tiles:
		var tile_m: float = t["tile"]
		var name: String = t["name"]
		var inst := scene.get_node_or_null(name) as Node3D
		if inst == null:
			_fail("%s is not mounted" % name)
			continue
		var mesh := inst.find_child(t["mesh"], true, false) as MeshInstance3D
		if mesh == null:
			_fail("%s has no mesh" % name)
			continue
		var x0: float = int(t["tx"]) * tile_m
		var z0: float = int(t["tz"]) * tile_m
		# Where the mesh's vertices are in the world: the scene's own transforms down to it.
		var xf := Transform3D.IDENTITY
		var n: Node = mesh
		while n != scene:
			xf = (n as Node3D).transform * xf if n is Node3D else xf
			n = n.get_parent()
		var tile_uv := 0.0
		var tile_out := 0.0
		for s in mesh.mesh.get_surface_count():
			# Godot's import compresses a mesh's attributes to 16 bits unless its GLB's import sets
			# meshes/force_disable_compression, which moves a vertex up to 1.5 cm in a 1 km tile.
			if mesh.mesh.surface_get_format(s) & Mesh.ARRAY_FLAG_COMPRESS_ATTRIBUTES:
				_fail("%s: its mesh is compressed on import; set meshes/force_disable_compression=true in its .import" % name)
			var arr := mesh.mesh.surface_get_arrays(s)
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var uv = arr[Mesh.ARRAY_TEX_UV]
			if uv == null or (uv as PackedVector2Array).size() != v.size():
				_fail("%s: surface %d has no UV0" % [name, s])
				continue
			vertices += v.size()
			for i in v.size():
				var w := xf * v[i]
				var lx := w.x - x0
				var lz := w.z - z0
				tile_out = maxf(tile_out, maxf(maxf(-lx, lx - tile_m), maxf(-lz, lz - tile_m)))
				tile_uv = maxf(tile_uv, maxf(absf(uv[i].x * tile_m - lx), absf(uv[i].y * tile_m - lz)))
		if tile_out > TOLERANCE:
			_fail("%s: its mesh reaches %.3f m outside its tile" % [name, tile_out])
		if tile_uv > TOLERANCE:
			_fail("%s: a vertex is %.4f m from where its UV says" % [name, tile_uv])
		worst_out = maxf(worst_out, tile_out)
		worst_uv = maxf(worst_uv, tile_uv)
		if mesh.find_children("*", "CollisionShape3D", true, false).is_empty():
			_fail("%s: no collision under its mesh (the GLB's -col)" % name)
		var mat := mesh.material_override as ShaderMaterial
		if mat == null or mat.shader == null or mat.shader.resource_path != SHADER:
			_fail("%s: its material is not %s" % [name, SHADER])
			continue
		var tex := mat.get_shader_parameter("colour") as Texture2D
		var want: String = t["texture"]
		if tex == null or tex.resource_path != want:
			_fail("%s: its colour is %s, not %s" % [name, "nothing" if tex == null else tex.resource_path, want])
			continue
		var got := tex.get_image()
		var img := _colour_image(t)
		if got == null or img == null:
			_fail("%s: no image to compare" % name)
			continue
		if not got.has_mipmaps():
			_fail("%s: the texture has no mipmaps" % name)
		var top := Image.create_from_data(got.get_width(), got.get_height(), false, got.get_format(),
			got.get_data().slice(0, got.get_width() * got.get_height() * 4))
		img.clear_mipmaps()
		if got.get_format() != Image.FORMAT_RGBA8 or top.get_data() != img.get_data():
			_fail("%s: the texture is not the painted PNG, premultiplied" % name)
	print("  checked %d tiles, %d vertices: furthest outside its tile %.5f m, UV against position %.6f m"
		% [tiles.size(), vertices, worst_out, worst_uv])
	scene.free()
