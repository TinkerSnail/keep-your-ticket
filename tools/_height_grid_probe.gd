extends SceneTree
## Dev probe: the game's own ground heights on the height grid's 2m lattice, as
## a ray from above meets them, so the grid's swap can be measured against
## exactly what the game had. Written 2026-10-12 for Stage 0, Freeze, of
## `documentation/terrain-height-grid-plan-2026-10-12.md`; the baseline it wrote
## at `1926e71` is `documentation/terrain/heightfield-baseline-1926e71/`.
## `_heightfield_probe.gd` is the older, coarser survey of who owns the ground,
## written to CSV for the terrain master's build; this one is the record.
##
##   Godot --headless --path . --script res://tools/_height_grid_probe.gd -- --out=/abs/dir
##   Godot --headless --path . --script res://tools/_height_grid_probe.gd -- --compare=/abs/dir [--image=/abs/diff.png]
##
## `--out` probes and writes a baseline. `--compare` re-probes the lattices a
## baseline's header names and reports how the world now differs from it. With
## `--out` only, for a trial: `--bounds=x0,x1,z0,z1` and `--centres=all|half|none`.
##
## The lattices. `nodes`, on even metres from the plaza origin over x −1902..3660,
## z −2760..7118: the height-grid measurement's domain
## (`documentation/screenshots/terrain-heightfield-measure-2026-10-12/README.md`,
## z −2760..7117) rounded out to even metres, 2782 x 4940. `centres`, on odd
## metres, the middle of every cell, 2781 x 4939; `half` takes every other cell
## each way.
##
## The ray. Straight down from y 2500 to −1000 through `park_world.tscn` alone,
## no player. Default query parameters (bodies, not areas; back faces hit; not
## from inside) but for the mask, layer 1, `world`: the only other layer in use
## is 2, `people`, the crowd's guests, AnimatableBody3D that walk, and a record
## that held them would differ from run to run.
##
## Each sample: the first hit's y (float32, NaN for none); its owner class
## (uint8); and the y of the first world_terrain hit on the same ray (float32,
## NaN for none), the first hit's own y where that is world_terrain. A second
## ray finds it against world_terrain alone: the probe adds layer 32 to those
## bodies in memory, having checked that no other collider uses it.
##
## A ray that lies in a vertical face, a sample on a wall drawn along an even
## metre or a diagonal, is answered by that face at an arbitrary height with a
## flat normal: 34 samples at `1926e71`, all on world_terrain's walls, four of
## them at y 750, the ray's middle, where the ground is near −7. Such a sample,
## either ray, is cast again 1cm east (then 1cm south) and the header lists it.
##
## Owner classes, from the collider's path under `park_world`. A CSG shape is
## its own collider; a mesh imported with `-col` answers as its StaticBody3D
## child, `places/world_terrain/<mesh>/StaticBody3D`.
##   1  `places/world_terrain/` and below: the master's `Ground`.
##   2  generated ground. `places/park_groundworks/` and below, every body: the
##      road corridor, the tunnel lids, the east shoulder walls and the
##      promenade banks. And under `places/west_shell/`, `shore` and every
##      `bluff*` except `bluff_plinth*`, `bluff_pier_*` and `bluff_bed_*`,
##      which dress it.
##   3  every other body: structures, props, park floors, both anchors
##      (`places/west_stair`, `places/east_cascade` with NT-2's earth), the
##      city's roads and earthworks, the range's rocks. Not the towns: at
##      `1926e71` their 17 bodies hold no shape, so no ray meets them.
##   0  no hit: open sea, which has no collision, or a hole.
##
## Files, in the out directory: `header.json` (domain, lattices, rules, ray,
## commit, tallies, timings) and per lattice `<lattice>_top_y.f32.gz`,
## `<lattice>_class.u8.gz` and `<lattice>_terrain_y.f32.gz`: gzip streams of raw
## little-endian arrays, row-major, index iz * nx + ix, x fastest. numpy reads one
## as `np.frombuffer(gzip.open(p).read(), '<f4').reshape(nz, nx)`.
##
## `--compare` prints, for the first hit and for world_terrain, by the baseline's
## class: samples, how many changed, max, p99 and RMS of |now − then| where both
## hit, and how many gained or lost a hit or changed class; the area that changed
## by more than 0.01, 0.05, 0.25 and 1m; the 20 largest changes at least 100m
## apart; and writes a difference image, 4m a pixel, −z (north) up: grey by
## height, red where the first hit rose, blue where it fell, brighter from 1cm to
## 1m, magenta where a hit came or went. The image goes to `--image`, else
## `user://height_grid_compare.png`. Prints; returns 0, or 1 if it cannot run.

const SCENE := "res://scenes/world/park_world.tscn"
const SPACING := 2.0
const DOMAIN_X := Vector2(-1902.0, 3660.0)
const DOMAIN_Z := Vector2(-2760.0, 7118.0)
const RAY_TOP := 2500.0
const RAY_BOTTOM := -1000.0
const WORLD_MASK := 1
## Layer 32, set in memory on world_terrain's bodies for the second ray.
const TERRAIN_BIT := 1 << 31
const SETTLE_FRAMES := 8
## A hit whose normal is this flat came off a face the ray lies in.
const FLAT_NORMAL := 1e-4
const NUDGE := 0.01
const THRESHOLDS := [0.01, 0.05, 0.25, 1.0]
const CLASS_NAMES := ["none", "world_terrain", "generated ground", "other body"]
## Of the compare's top changes: the block each is the largest of, and how far
## apart two must stand.
const PLACE_BLOCK := 32
const PLACE_APART := 100.0

var _world: Node
var _space: PhysicsDirectSpaceState3D
## collider instance id -> [class, group index]
var _owners := {}
var _groups: PackedStringArray = []
## Second rays answered by anything but world_terrain: must stay 0.
var _stray := 0
## Samples cast again off a face the ray lay in: [x, z, which ray].
var _nudged := []


func _initialize() -> void:
	var out := ""
	var compare := ""
	var image := "user://height_grid_compare.png"
	var bounds := [DOMAIN_X.x, DOMAIN_X.y, DOMAIN_Z.x, DOMAIN_Z.y]
	var centres := "all"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):
			out = arg.trim_prefix("--out=")
		elif arg.begins_with("--compare="):
			compare = arg.trim_prefix("--compare=")
		elif arg.begins_with("--image="):
			image = arg.trim_prefix("--image=")
		elif arg.begins_with("--bounds="):
			bounds = Array(arg.trim_prefix("--bounds=").split_floats(","))
		elif arg.begins_with("--centres="):
			centres = arg.trim_prefix("--centres=")
	if (out == "") == (compare == ""):
		printerr("FAIL: pass one of --out=<abs dir> or --compare=<abs dir>")
		quit(1)
		return

	var t0 := Time.get_ticks_msec()
	_world = (load(SCENE) as PackedScene).instantiate()
	root.add_child(_world)
	var clock := root.get_node_or_null("ParkClock")
	if clock != null:
		clock.set("running", false)
	for i in SETTLE_FRAMES:
		await process_frame
		await physics_frame
	var load_s := (Time.get_ticks_msec() - t0) / 1000.0
	_space = root.world_3d.direct_space_state
	if not _index_colliders():
		quit(1)
		return
	for i in 2:
		await physics_frame

	if out != "":
		_record(out, bounds, centres, load_s)
	else:
		_compare(compare, image, load_s)
	quit(0)


## Every collider in the world, classed once by path; world_terrain's take layer 32.
func _index_colliders() -> bool:
	var found: Array[Node] = []
	_colliders(_world, found)
	var terrain := 0
	for n in found:
		var layer: int = n.get("collision_layer")
		if layer & TERRAIN_BIT:
			printerr("FAIL: %s already uses layer 32" % _world.get_path_to(n))
			return false
	for n in found:
		var path := str(_world.get_path_to(n)).split("/")
		var c := _class_of(path)
		_owners[n.get_instance_id()] = [c, _group_of(path, c)]
		if c == 1:
			n.set("collision_layer", int(n.get("collision_layer")) | TERRAIN_BIT)
			terrain += 1
	print("height grid probe: %d colliders indexed, %d of them world_terrain" % [found.size(), terrain])
	return terrain > 0


func _colliders(n: Node, found: Array[Node]) -> void:
	if n is CollisionObject3D:
		found.append(n)
	elif n is CSGShape3D and (n as CSGShape3D).is_root_shape() and (n as CSGShape3D).use_collision:
		found.append(n)
	for c in n.get_children():
		_colliders(c, found)


## The rules in the header.
func _class_of(path: PackedStringArray) -> int:
	if path.size() < 2 or path[0] != "places":
		return 3
	if path[1] == "world_terrain":
		return 1
	if path[1] == "park_groundworks":
		return 2
	if path[1] == "west_shell" and path.size() > 2:
		var own := path[2]
		if own == "shore":
			return 2
		if own.begins_with("bluff") and not (own.begins_with("bluff_plinth")
				or own.begins_with("bluff_pier_") or own.begins_with("bluff_bed_")):
			return 2
	return 3


## Tallies group by place, and inside world_terrain, park_groundworks and
## west_shell by the body's own name with its digits folded.
func _group_of(path: PackedStringArray, c: int) -> int:
	var depth := 2
	if path.size() > 2 and path[0] == "places" and path[1] in ["world_terrain", "park_groundworks", "west_shell"]:
		depth = 3
	var parts := path.slice(0, mini(depth, path.size()))
	if depth == 3 and parts.size() == 3:
		var rx := RegEx.create_from_string("[0-9]+")
		parts[2] = rx.sub(parts[2], "#", true)
	var key := "%d %s" % [c, "/".join(parts)]
	var i := _groups.find(key)
	if i < 0:
		_groups.append(key)
		i = _groups.size() - 1
	return i


func _lattices(bounds: Array, centres: String) -> Dictionary:
	var x0: float = floorf(bounds[0] / SPACING) * SPACING
	var x1: float = ceilf(bounds[1] / SPACING) * SPACING
	var z0: float = floorf(bounds[2] / SPACING) * SPACING
	var z1: float = ceilf(bounds[3] / SPACING) * SPACING
	var nx := int(roundf((x1 - x0) / SPACING)) + 1
	var nz := int(roundf((z1 - z0) / SPACING)) + 1
	var sets := {"nodes": {"origin": [x0, z0], "step": SPACING, "nx": nx, "nz": nz}}
	if centres != "none":
		var stride := 2 if centres == "half" else 1
		sets["centres"] = {"origin": [x0 + SPACING * 0.5, z0 + SPACING * 0.5],
			"step": SPACING * stride,
			"nx": (nx - 2) / stride + 1, "nz": (nz - 2) / stride + 1}
	return sets


## One lattice: [top_y, class, terrain_y, group index of the first hit].
func _probe(spec: Dictionary) -> Array:
	var ox := float(spec["origin"][0])
	var oz := float(spec["origin"][1])
	var step := float(spec["step"])
	var nx := int(spec["nx"])
	var nz := int(spec["nz"])
	var n := nx * nz
	var top := PackedFloat32Array()
	var ter := PackedFloat32Array()
	var cls := PackedByteArray()
	var grp := PackedInt32Array()
	top.resize(n)
	ter.resize(n)
	cls.resize(n)
	grp.resize(n)
	var q := PhysicsRayQueryParameters3D.new()
	q.collision_mask = WORLD_MASK
	var qt := PhysicsRayQueryParameters3D.new()
	qt.collision_mask = TERRAIN_BIT
	var i := 0
	for iz in nz:
		var z := oz + iz * step
		for ix in nx:
			var x := ox + ix * step
			var hit := _cast(q, x, z, "first")
			if hit.is_empty():
				top[i] = NAN
				ter[i] = NAN
				cls[i] = 0
				grp[i] = -1
			else:
				var y: float = (hit["position"] as Vector3).y
				var owner: Array = _owner(hit["collider_id"])
				top[i] = y
				cls[i] = owner[0]
				grp[i] = owner[1]
				if owner[0] == 1:
					ter[i] = y
				else:
					var under := _cast(qt, x, z, "world_terrain")
					if under.is_empty():
						ter[i] = NAN
					else:
						ter[i] = (under["position"] as Vector3).y
						if _owner(under["collider_id"])[0] != 1:
							_stray += 1
			i += 1
	if _stray > 0:
		printerr("FAIL: %d world_terrain rays answered by another body" % _stray)
	return [top, cls, ter, grp]


## One ray down at (x, z); off a face it lies in, again 1cm east, then 1cm south.
func _cast(q: PhysicsRayQueryParameters3D, x: float, z: float, which: String) -> Dictionary:
	q.from = Vector3(x, RAY_TOP, z)
	q.to = Vector3(x, RAY_BOTTOM, z)
	var hit := _space.intersect_ray(q)
	if hit.is_empty() or absf((hit["normal"] as Vector3).y) >= FLAT_NORMAL:
		return hit
	for o in [Vector2(NUDGE, 0.0), Vector2(0.0, NUDGE)]:
		q.from = Vector3(x + o.x, RAY_TOP, z + o.y)
		q.to = Vector3(x + o.x, RAY_BOTTOM, z + o.y)
		var again := _space.intersect_ray(q)
		if again.is_empty() or absf((again["normal"] as Vector3).y) >= FLAT_NORMAL:
			_nudged.append([x, z, which, "%+.2f,%+.2f" % [o.x, o.y],
				"%.3f" % (hit["position"] as Vector3).y,
				"none" if again.is_empty() else "%.3f" % (again["position"] as Vector3).y])
			return again
	_nudged.append([x, z, which, "unresolved", "%.3f" % (hit["position"] as Vector3).y, ""])
	return hit


func _owner(id: int) -> Array:
	if _owners.has(id):
		return _owners[id]
	# A collider the index missed: class it now by its path.
	var node := instance_from_id(id) as Node
	var path: PackedStringArray = str(_world.get_path_to(node)).split("/") if node != null else PackedStringArray()
	var c := _class_of(path)
	_owners[id] = [c, _group_of(path, c)]
	return _owners[id]


func _record(dir: String, bounds: Array, centres: String, load_s: float) -> void:
	DirAccess.make_dir_recursive_absolute(dir)
	var sets := _lattices(bounds, centres)
	var timings := {"load_s": load_s}
	var tallies := {}
	var total := 0
	for name in sets:
		var spec: Dictionary = sets[name]
		var t := Time.get_ticks_msec()
		var r := _probe(spec)
		timings[name + "_probe_s"] = (Time.get_ticks_msec() - t) / 1000.0
		t = Time.get_ticks_msec()
		var files := {}
		files["top_y"] = _write(dir, "%s_top_y.f32.gz" % name, (r[0] as PackedFloat32Array).to_byte_array())
		files["class"] = _write(dir, "%s_class.u8.gz" % name, r[1])
		files["terrain_y"] = _write(dir, "%s_terrain_y.f32.gz" % name, (r[2] as PackedFloat32Array).to_byte_array())
		timings[name + "_write_s"] = (Time.get_ticks_msec() - t) / 1000.0
		spec["files"] = files
		tallies[name] = _tally(r, spec)
		tallies[name]["cast_again_off_a_face_in_the_ray"] = _nudged.duplicate()
		_nudged.clear()
		total += int(spec["nx"]) * int(spec["nz"])
		print("%s: %d x %d = %d samples in %.1fs; %s" % [name, spec["nx"], spec["nz"],
			int(spec["nx"]) * int(spec["nz"]), timings[name + "_probe_s"], JSON.stringify(tallies[name]["class"])])
	var header := {
		"what": "The game's ground heights on the height grid's lattice, as a ray from above meets them.",
		"probe": "res://tools/_height_grid_probe.gd",
		"written": Time.get_datetime_string_from_system(true) + "Z",
		"commit": _git(["rev-parse", "HEAD"]),
		"modified_tracked_in_scenes_assets_scripts": Array(_git(["status", "--porcelain", "--untracked-files=no", "--", "scenes", "assets", "scripts"]).split("\n", false)),
		"godot": Engine.get_version_info()["string"],
		"physics_engine": str(ProjectSettings.get_setting("physics/3d/physics_engine")),
		"scene": SCENE,
		"axes": "Godot world metres, y up; x east, z south (north is -z); the plaza fountain at the origin",
		"spacing": SPACING,
		"domain": {"x": [bounds[0], bounds[1]], "z": [bounds[2], bounds[3]],
			"note": "nodes on even metres, rounded outward"},
		"sets": sets,
		"layout": "each file a gzip stream of one raw little-endian array, row-major, index iz * nx + ix, x fastest; sample (ix, iz) at origin + step * (ix, iz); top_y and terrain_y float32 (NaN: no hit), class uint8",
		"ray": {"from_y": RAY_TOP, "to_y": RAY_BOTTOM, "collision_mask": WORLD_MASK,
			"collide_with_bodies": true, "collide_with_areas": false,
			"hit_back_faces": true, "hit_from_inside": false,
			"terrain_y": "a second ray with mask layer 32, which the probe sets in memory on world_terrain's bodies only; equals top_y where class is 1"},
		"classes": {"0": "no hit", "1": "places/world_terrain/**: the master's Ground",
			"2": "places/park_groundworks/** (every body); places/west_shell/shore and places/west_shell/bluff* except bluff_plinth*, bluff_pier_*, bluff_bed_*",
			"3": "any other body (structures, props, park floors, both anchors, towns, city roads and earthworks, range rocks)"},
		"tallies": tallies,
		"samples": total,
		"timings": timings,
	}
	var f := FileAccess.open(dir.path_join("header.json"), FileAccess.WRITE)
	f.store_string(JSON.stringify(header, "  ", false) + "\n")
	f.close()
	print("height grid probe: %d samples, load %.1fs, wrote %s" % [total, load_s, dir])


## Class counts, and per owner group its first hits, how many have world_terrain
## under them, and the mean height they stand over it.
func _tally(r: Array, spec: Dictionary) -> Dictionary:
	var top: PackedFloat32Array = r[0]
	var cls: PackedByteArray = r[1]
	var ter: PackedFloat32Array = r[2]
	var grp: PackedInt32Array = r[3]
	var by_class := [0, 0, 0, 0]
	var under := [0, 0, 0, 0]
	var groups := {}
	for i in top.size():
		var c := cls[i]
		by_class[c] += 1
		var has_ter := not is_nan(ter[i])
		if has_ter:
			under[c] += 1
		if c == 0:
			continue
		var g := grp[i]
		var rec: Array = groups.get(g, [0, 0, 0.0])
		rec[0] += 1
		if has_ter:
			rec[1] += 1
			rec[2] += top[i] - ter[i]
		groups[g] = rec
	var named := {}
	for g in groups:
		var rec: Array = groups[g]
		named[_groups[g]] = {"first_hits": rec[0], "over_world_terrain": rec[1],
			"mean_height_over_it": snappedf(rec[2] / maxf(1.0, rec[1]), 0.001)}
	var area := pow(float(spec["step"]), 2.0)
	return {"class": {"0": by_class[0], "1": by_class[1], "2": by_class[2], "3": by_class[3]},
		"with_world_terrain_beneath": {"0": under[0], "1": under[1], "2": under[2], "3": under[3]},
		"area_m2_per_sample": area, "groups": named}


func _write(dir: String, file: String, bytes: PackedByteArray) -> Dictionary:
	var gz := bytes.compress(FileAccess.COMPRESSION_GZIP)
	var f := FileAccess.open(dir.path_join(file), FileAccess.WRITE)
	f.store_buffer(gz)
	f.close()
	return {"name": file, "raw_bytes": bytes.size(), "gzip_bytes": gz.size()}


func _read(dir: String, file: Dictionary) -> PackedByteArray:
	return FileAccess.get_file_as_bytes(dir.path_join(file["name"])).decompress(
		int(file["raw_bytes"]), FileAccess.COMPRESSION_GZIP)


func _git(args: Array) -> String:
	var out := []
	OS.execute("git", PackedStringArray(["-C", ProjectSettings.globalize_path("res://")] + args), out, true)
	return (out[0] as String).strip_edges(false, true) if not out.is_empty() else ""


func _compare(dir: String, image: String, load_s: float) -> void:
	var text := FileAccess.get_file_as_string(dir.path_join("header.json"))
	var header: Dictionary = JSON.parse_string(text) if text != "" else {}
	if header.is_empty():
		printerr("FAIL: no header.json in ", dir)
		return
	print("height grid compare: baseline %s at %s, now %s; load %.1fs" % [
		dir, header["commit"], _git(["rev-parse", "HEAD"]), load_s])
	var sets: Dictionary = header["sets"]
	var nodes_now := []
	var nodes_then := []
	var centres_now := []
	var centres_then := []
	var places := []
	for name in sets:
		var spec: Dictionary = sets[name]
		var t := Time.get_ticks_msec()
		var now := _probe(spec)
		var then := [
			_read(dir, spec["files"]["top_y"]).to_float32_array(),
			_read(dir, spec["files"]["class"]),
			_read(dir, spec["files"]["terrain_y"]).to_float32_array(),
		]
		print("")
		print("%s: %d x %d, re-probed in %.1fs, %.1f m2 a sample" % [name, spec["nx"], spec["nz"],
			(Time.get_ticks_msec() - t) / 1000.0, pow(float(spec["step"]), 2.0)])
		print("  cast again off a face in the ray: %d %s" % [_nudged.size(), str(_nudged.slice(0, 10))])
		_nudged.clear()
		_report(spec, then, now)
		places.append_array(_places(spec, then, now))
		if name == "nodes":
			nodes_now = now
			nodes_then = then
		else:
			centres_now = now
			centres_then = then
	places.sort_custom(func(a, b): return a[0] > b[0])
	var kept := []
	for p in places:
		var far := true
		for k in kept:
			if Vector2(p[1], p[2]).distance_to(Vector2(k[1], k[2])) < PLACE_APART:
				far = false
				break
		if far:
			kept.append(p)
		if kept.size() == 20:
			break
	print("")
	print("largest changes, at least %dm apart (x, z, then, now, class then -> now):" % int(PLACE_APART))
	if kept.is_empty():
		print("  none")
	for p in kept:
		var size := "hit came/went" if p[0] >= 1e9 else "%.3fm" % p[0]
		print("  %13s  (%7.0f, %7.0f)  %s -> %s  %s -> %s  %s" % [size, p[1], p[2],
			_num(p[3]), _num(p[4]), CLASS_NAMES[p[5]], CLASS_NAMES[p[6]], p[7]])
	_image(sets["nodes"], nodes_then, nodes_now, sets.get("centres", {}), centres_then, centres_now, image)


func _num(v: float) -> String:
	return "none" if is_nan(v) else "%.3f" % v


## By the baseline's class, for the first hit and for world_terrain.
func _report(spec: Dictionary, then: Array, now: Array) -> void:
	var area := pow(float(spec["step"]), 2.0)
	var cls_then: PackedByteArray = then[1]
	var cls_now: PackedByteArray = now[1]
	for k in [[0, "first hit"], [2, "world_terrain"]]:
		var a: PackedFloat32Array = then[k[0]]
		var b: PackedFloat32Array = now[k[0]]
		# One array per class; packed arrays held in an Array copy on write.
		var d0 := PackedFloat32Array()
		var d1 := PackedFloat32Array()
		var d2 := PackedFloat32Array()
		var d3 := PackedFloat32Array()
		var counts := [0, 0, 0, 0]
		var gained := [0, 0, 0, 0]
		var lost := [0, 0, 0, 0]
		var reclassed := [0, 0, 0, 0]
		var over := [0, 0, 0, 0]
		for i in a.size():
			var c := cls_then[i]
			counts[c] += 1
			if cls_now[i] != c:
				reclassed[c] += 1
			var na := is_nan(a[i])
			var nb := is_nan(b[i])
			if na and nb:
				continue
			if na != nb:
				if na:
					gained[c] += 1
				else:
					lost[c] += 1
				continue
			var d := absf(b[i] - a[i])
			if c == 1:
				d1.append(d)
			elif c == 3:
				d3.append(d)
			elif c == 2:
				d2.append(d)
			else:
				d0.append(d)
			for j in THRESHOLDS.size():
				if d > THRESHOLDS[j]:
					over[j] += 1
		print("  %s, by baseline class:" % k[1])
		var per_class := [d0, d1, d2, d3]
		for c in 4:
			if counts[c] == 0:
				continue
			var ds: PackedFloat32Array = per_class[c]
			ds.sort()
			var changed := 0
			var sum := 0.0
			for d in ds:
				sum += d * d
				if d > 0.0:
					changed += 1
			var mx := ds[ds.size() - 1] if ds.size() > 0 else 0.0
			var p99 := ds[int(floor(0.99 * (ds.size() - 1)))] if ds.size() > 0 else 0.0
			var rms := sqrt(sum / ds.size()) if ds.size() > 0 else 0.0
			print("    %-17s %9d samples, %9d with a height both times, %d changed; max %.4f, p99 %.4f, RMS %.5f; gained a hit %d, lost one %d, changed class %d" % [
				CLASS_NAMES[c], counts[c], ds.size(), changed, mx, p99, rms, gained[c], lost[c], reclassed[c]])
		var bits: Array[String] = []
		for j in THRESHOLDS.size():
			bits.append(">%sm %.2f ha" % [str(THRESHOLDS[j]), over[j] * area / 1e4])
		var flips := 0
		for c in 4:
			flips += gained[c] + lost[c]
		print("    area changed: %s; a hit came or went over %.2f ha" % [", ".join(bits), flips * area / 1e4])


## Each PLACE_BLOCK square of samples offers its largest change of either height.
func _places(spec: Dictionary, then: Array, now: Array) -> Array:
	var nx := int(spec["nx"])
	var ox := float(spec["origin"][0])
	var oz := float(spec["origin"][1])
	var step := float(spec["step"])
	var best := {}
	for k in [0, 2]:
		var a: PackedFloat32Array = then[k]
		var b: PackedFloat32Array = now[k]
		for i in a.size():
			var na := is_nan(a[i])
			var nb := is_nan(b[i])
			if na and nb:
				continue
			var d := INF if na != nb else absf(b[i] - a[i])
			if d == 0.0:
				continue
			var ix := i % nx
			var iz := i / nx
			var key := (iz / PLACE_BLOCK) * 100000 + ix / PLACE_BLOCK
			var size := 1e9 if is_inf(d) else d
			if not best.has(key) or size > best[key][0]:
				var group_now: int = now[3][i]
				best[key] = [size, ox + ix * step, oz + iz * step, a[i], b[i],
					int(then[1][i]), int(now[1][i]),
					("first hit" if k == 0 else "world_terrain") + (", now " + _groups[group_now].substr(2) if group_now >= 0 else "")]
	return best.values()


## 4m a pixel: the largest change of the first hit over the block's nodes and
## centres; grey by the baseline height where nothing changed.
func _image(nodes: Dictionary, nt: Array, nn: Array, centres: Dictionary, ct: Array, cn: Array, path: String) -> void:
	var nx := int(nodes["nx"])
	var nz := int(nodes["nz"])
	var w := (nx + 1) / 2
	var h := (nz + 1) / 2
	var change := PackedFloat32Array()
	change.resize(w * h)
	var height := PackedFloat32Array()
	height.resize(w * h)
	height.fill(NAN)
	var flip := PackedByteArray()
	flip.resize(w * h)
	_fold(nt, nn, nx, 1, w, change, height, flip)
	if not centres.is_empty():
		var stride := int(roundf(float(centres["step"]) / float(nodes["step"])))
		_fold(ct, cn, int(centres["nx"]), stride, w, change, height, flip)
	var data := PackedByteArray()
	data.resize(w * h * 3)
	for p in w * h:
		var r := 0
		var g := 0
		var b := 0
		var y := height[p]
		if is_nan(y):
			r = 24; g = 28; b = 40
		else:
			var v := int(clampf(70.0 + y * 0.35, 40.0, 200.0))
			r = v; g = v; b = v
		if flip[p] != 0:
			r = 255; g = 0; b = 255
		elif change[p] != 0.0:
			var s := clampf((log(absf(change[p])) / log(10.0) + 2.0) / 2.0, 0.0, 1.0)
			var lit := int(lerpf(110.0, 255.0, s))
			if change[p] > 0.0:
				r = lit; g = 0; b = 0
			else:
				r = 0; g = int(lit * 0.35); b = lit
		data[p * 3] = r
		data[p * 3 + 1] = g
		data[p * 3 + 2] = b
	var img := Image.create_from_data(w, h, false, Image.FORMAT_RGB8, data)
	var err := img.save_png(path)
	print("")
	print("difference image %d x %d, 4m a pixel, -z up: %s (%s)" % [w, h,
		ProjectSettings.globalize_path(path) if path.begins_with("user://") else path, error_string(err)])


## Folds one lattice's first-hit change into the 4m pixels. A centre (or a
## node) at lattice index (ix, iz) lies in node cell (ix * stride, iz * stride).
func _fold(then: Array, now: Array, nx: int, stride: int, w: int,
		change: PackedFloat32Array, height: PackedFloat32Array, flip: PackedByteArray) -> void:
	var a: PackedFloat32Array = then[0]
	var b: PackedFloat32Array = now[0]
	for i in a.size():
		var px := ((i % nx) * stride) / 2
		var pz := ((i / nx) * stride) / 2
		var p := pz * w + px
		if p >= change.size():
			continue
		var na := is_nan(a[i])
		if not na and is_nan(height[p]):
			height[p] = a[i]
		if na != is_nan(b[i]):
			flip[p] = 1
			continue
		if na:
			continue
		var d := b[i] - a[i]
		if absf(d) > absf(change[p]):
			change[p] = d
