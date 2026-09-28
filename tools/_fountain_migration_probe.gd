extends Node

## Probe, 2026-09-27: did the plaza fountain move from `gen_props.gd` to Blender
## unchanged?
##
##   godot --headless --path . tools/run.tscn -- _fountain_migration_probe materials
##   godot --headless --path . tools/run.tscn -- _fountain_migration_probe compare
##
## Until then `_fountain()` built it as 208 CSG shapes into
## `generated/plaza_fountain.tscn`. Its shape now comes from
## `assets/source/props/plaza_fountain.blend`, sent to `assets/props/plaza_fountain.glb`.
##
## `materials` reads the maquette and writes what the move needs from it: each
## of its eleven materials, named as `_fountain_materials` named them, to
## `assets/materials/plaza_fountain/<name>.tres` (the GLB's import settings use
## these in place of the glTF's), and `plaza_fountain_parts.json` beside the
## maquette reference: every part's material, collision and shadow, which
## `tools/blender/parts_from_maquette.py` gives the Blender parts. It ran once,
## on 2026-09-27, and refuses to run again over existing `.tres` files: they
## are the fountain's materials now, edited in the inspector.
##
## `compare` mounts `scenes/world/plaza_fountain.tscn` as the game does and
## measures it against the maquette. The Blender file joins each ring of parts
## that differ only in a two-digit index (`kerb_00` … `kerb_35`) into one object,
## so a maquette part is compared with the object of its ring: the surfaces both
## ways, the normals, the area, the material property by property, the shadow
## and other instance settings, and the collision surface and layers. UVs are
## measured and not judged: nothing in the fountain reads them. Only
## meaningful while the Blender file holds the maquette's shapes (the lossless
## step); after a reshape it reports how far the fountain strays from the old one.
##
## The maquette was `generated/plaza_fountain.tscn`, which the generator no
## longer writes. Restore it from git to a file and name that file:
##   git show 2f02612:scenes/world/generated/plaza_fountain.tscn > /tmp/f.tscn
##   FOUNTAIN_MAQUETTE=/tmp/f.tscn godot … -- _fountain_migration_probe compare
## `FOUNTAIN_PROBE_WHERE=1` also prints, per ring, the mounted vertex farthest
## from the maquette.

const MAQUETTE := "res://scenes/world/generated/plaza_fountain.tscn"
const MOUNTED := "res://scenes/world/plaza_fountain.tscn"
const MATERIAL_DIR := "res://assets/materials/plaza_fountain"
const PARTS_JSON := "res://assets/source/props/reference/plaza_fountain_parts.json"

## Each material by the part `_fountain_materials` made it for. Every other part
## must carry one of these eleven, which is how a name reaches all of them.
const NAMED_BY := {
	"fount_stone": "kerb_00",
	"fount_wet": "coping_00",
	"fount_bed": "pool_bed",
	"fount_bronze": "nozzle",
	"water_pool": "pool_water",
	"water_basin": "lb_water",
	"water_veil_lo": "lb_veil_00",
	"water_veil_hi": "ub_veil_00",
	"water_jet": "jet_00_a",
	"water_plume": "plume_1",
	"water_spray": "spray_1",
}

## A vertex further than this from the other side's surface, or a normal
## turned further, fails the comparison.
const POSITION_TOLERANCE := 0.0001
const NORMAL_TOLERANCE_DEG := 0.5

var _ring := RegEx.create_from_string("_\\d\\d(?=_|$)")
var _fails: Array[String] = []


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var mode := args[1] if args.size() > 1 else ""
	if mode not in ["materials", "compare"]:
		push_error("usage: -- _fountain_migration_probe materials|compare")
		get_tree().quit(2)
		return
	var maquette := await _mount(_maquette_path())
	if maquette == null:
		get_tree().quit(1)
		return
	if mode == "materials":
		_write_materials(maquette)
	else:
		var mounted := await _mount(MOUNTED)
		if mounted != null:
			_compare(maquette, mounted)
	for f in _fails:
		print("FAIL: %s" % f)
	print("PASS" if _fails.is_empty() else "FAIL: %d problems" % _fails.size())
	get_tree().quit(0 if _fails.is_empty() else 1)


func _maquette_path() -> String:
	var named := OS.get_environment("FOUNTAIN_MAQUETTE")
	return named if named != "" else MAQUETTE


func _mount(path: String) -> Node3D:
	var packed := ResourceLoader.load(path, "", ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
	if packed == null:
		_fails.append("cannot load %s" % path)
		return null
	var root := packed.instantiate() as Node3D
	add_child(root)
	# CSG shapes build their mesh on the next frame.
	await get_tree().process_frame
	await get_tree().process_frame
	return root


func _parts(maquette: Node) -> Array[CSGShape3D]:
	var out: Array[CSGShape3D] = []
	for n in maquette.find_children("*", "CSGShape3D", true, false):
		out.append(n as CSGShape3D)
	return out


## The eleven materials, keyed by name, and each part's name for its material.
func _material_names(parts: Array[CSGShape3D]) -> Dictionary:
	var by_name := {}
	for part in parts:
		for material_name in NAMED_BY:
			if String(part.name) == NAMED_BY[material_name]:
				by_name[material_name] = part.get("material")
	var names := {}
	for material_name in by_name:
		names[by_name[material_name]] = material_name
	if names.size() != NAMED_BY.size():
		_fails.append("the eleven named parts carry %d distinct materials" % names.size())
	return {"by_name": by_name, "names": names}


func _write_materials(maquette: Node) -> void:
	if DirAccess.dir_exists_absolute(ProjectSettings.globalize_path(MATERIAL_DIR)) \
			and not DirAccess.get_files_at(MATERIAL_DIR).is_empty():
		_fails.append("%s already holds the fountain's materials; not overwriting them" % MATERIAL_DIR)
		return
	var parts := _parts(maquette)
	var named := _material_names(parts)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(MATERIAL_DIR))
	for material_name in named.by_name:
		var copy := (named.by_name[material_name] as Material).duplicate()
		copy.resource_name = material_name
		var path := "%s/%s.tres" % [MATERIAL_DIR, material_name]
		var err := ResourceSaver.save(copy, path)
		if err != OK:
			_fails.append("could not write %s (%s)" % [path, error_string(err)])
		else:
			print("wrote %s" % path)
	var rows := []
	for part in parts:
		var m: Material = part.get("material")
		if not named.names.has(m):
			_fails.append("%s carries a material none of the named parts does" % part.name)
			continue
		rows.append({
			"name": String(part.name),
			"material": named.names[m],
			"collide": part.use_collision,
			"cast_shadow": part.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF,
		})
	var colours := {}
	for material_name in named.by_name:
		colours[material_name] = _display(named.by_name[material_name])
	var f := FileAccess.open(ProjectSettings.globalize_path(PARTS_JSON), FileAccess.WRITE)
	f.store_string(JSON.stringify({"parts": rows, "materials": colours}, "\t"))
	f.close()
	print("wrote %s: %d parts, %d materials" % [PARTS_JSON, rows.size(), colours.size()])


## What Blender shows for a material: its albedo, or a water shader's tint.
## Blender's viewport only; the game uses the `.tres`.
func _display(m: Material) -> Dictionary:
	if m is StandardMaterial3D:
		var s := m as StandardMaterial3D
		return {"srgb": [s.albedo_color.r, s.albedo_color.g, s.albedo_color.b],
			"alpha": 1.0, "metallic": s.metallic, "roughness": s.roughness}
	var tint = (m as ShaderMaterial).get_shader_parameter("tint")
	var c: Color = tint if tint is Color else Color(0.78, 0.88, 0.92)
	return {"srgb": [c.r, c.g, c.b], "alpha": 0.45, "metallic": 0.0, "roughness": 0.05}


# ---------------------------------------------------------------------------
# compare
# ---------------------------------------------------------------------------

class Surface:
	var positions := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	## Three indices into the arrays above per triangle, and each triangle's
	## bounds, for rejecting it cheaply.
	var tris := PackedInt32Array()
	## For a vertex of a drum, the drum's axis and a point on it; zero otherwise.
	var axes := PackedVector3Array()
	var centres := PackedVector3Array()
	var lows := PackedVector3Array()
	var highs := PackedVector3Array()
	var area := 0.0

	func add_triangle(a: int, b: int, c: int) -> void:
		tris.append_array([a, b, c])
		var pa := positions[a]
		var pb := positions[b]
		var pc := positions[c]
		lows.append(pa.min(pb).min(pc))
		highs.append(pa.max(pb).max(pc))
		area += (pb - pa).cross(pc - pa).length() * 0.5


func _compare(maquette: Node, mounted: Node) -> void:
	var parts := _parts(maquette)
	var named := _material_names(parts)

	var objects := {}
	for n in mounted.find_children("*", "MeshInstance3D", true, false):
		objects[String(n.name)] = n
	var rings := {}
	for part in parts:
		var ring := _ring.sub(String(part.name), "", true)
		if not rings.has(ring):
			rings[ring] = []
		rings[ring].append(part)
	print("maquette: %d parts in %d rings; mounted: %d objects" % [
		parts.size(), rings.size(), objects.size()])
	for extra in objects:
		if not rings.has(extra):
			_fails.append("mounted object %s has no maquette parts" % extra)

	var worst := {"to": 0.0, "from": 0.0, "normal": 0.0, "uv": 0.0, "area": 0.0,
		"skew_old": 0.0, "skew_now": 0.0}
	var totals := {"maquette": 0, "mounted": 0}
	for ring in rings:
		if not objects.has(ring):
			_fails.append("no mounted object for %s" % ring)
			continue
		var mi := objects[ring] as MeshInstance3D
		var old := Surface.new()
		for part in rings[ring]:
			var xf := (part as Node3D).global_transform
			_add_mesh(old, (part as CSGShape3D).bake_static_mesh(), xf,
				xf.basis.y.normalized() if part is CSGCylinder3D else Vector3.ZERO)
		var now := Surface.new()
		_add_mesh(now, mi.mesh, mi.global_transform)
		totals.maquette += old.tris.size() / 3
		totals.mounted += now.tris.size() / 3
		var m := _measure(old, now)
		for k in m:
			worst[k] = maxf(worst[k], m[k])
		var area_gap := absf(old.area - now.area) / maxf(old.area, 1e-9)
		worst.area = maxf(worst.area, area_gap)
		if m.to > POSITION_TOLERANCE or m.from > POSITION_TOLERANCE \
				or m.normal > NORMAL_TOLERANCE_DEG or m.skew_now > NORMAL_TOLERANCE_DEG \
				or area_gap > 1e-4:
			_fails.append("%s: surface %.4f/%.4f mm, normal %.3f deg, drum side off radial %.3f deg, area %.5f%%" % [
				ring, m.to * 1000.0, m.from * 1000.0, m.normal, m.skew_now, area_gap * 100.0])
		_compare_material(ring, rings[ring], mi, named.names)
		_compare_instance(ring, rings[ring], mi)
		_compare_collision(ring, rings[ring], mi, old)
	print("triangles: maquette %d, mounted %d" % [totals.maquette, totals.mounted])
	print("farthest maquette vertex from the mounted surface: %.4f mm" % (worst.to * 1000.0))
	print("farthest mounted vertex from the maquette surface: %.4f mm" % (worst.from * 1000.0))
	print("largest normal turn: %.4f deg; largest area change: %.6f%%" % [
		worst.normal, worst.area * 100.0])
	print("drum sides, farthest normal from radial: maquette %.4f deg, mounted %.4f deg" % [
		worst.skew_old, worst.skew_now])
	# Measured, not judged: no material of the fountain reads UVs (plain colours,
	# and water mapped in world space), and the maquette's own cap UVs change
	# from one triangle of a fan to the next.
	print("largest UV move (nothing reads them): %.4f" % worst.uv)


func _add_mesh(into: Surface, mesh: Mesh, xf: Transform3D, axis := Vector3.ZERO) -> void:
	if mesh == null:
		return
	var nb := xf.basis.inverse().transposed()
	for s in mesh.get_surface_count():
		var arrays := mesh.surface_get_arrays(s)
		var v: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var n: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
		var uv = arrays[Mesh.ARRAY_TEX_UV]
		var idx = arrays[Mesh.ARRAY_INDEX]
		var base := into.positions.size()
		for i in v.size():
			into.positions.append(xf * v[i])
			into.normals.append((nb * n[i]).normalized())
			into.uvs.append(uv[i] if uv != null else Vector2.ZERO)
			into.axes.append(axis)
			into.centres.append(xf.origin)
		var count: int = idx.size() if idx != null else v.size()
		for t in range(0, count, 3):
			into.add_triangle(base + (idx[t] if idx != null else t),
				base + (idx[t + 1] if idx != null else t + 1),
				base + (idx[t + 2] if idx != null else t + 2))


## Surface against surface, both ways: each vertex's distance to the nearest
## triangle of the other side. The Blender parts are welded and their flat
## faces joined, so their vertices are a subset of the maquette's and the
## triangulation differs; a vertex-to-vertex match would miss both. For each
## maquette vertex, also the normal and UV the mounted surface has at the same
## point, interpolated across its triangle; where several triangles meet there
## (a sharp edge), the one whose normal agrees best.
##
## **A drum's side is judged against radial, not against the maquette.** Godot's
## CSG averages a smooth corner's normal over the triangles meeting there, and a
## drum's side quad is two triangles, so a rim corner touched by two triangles
## of one quad and one of the next leans a sixth of a segment toward the first:
## 7.9 degrees on an eight-sided plume. Blender's normals are radial. So on a
## drum's side the maquette's lean is measured and reported, and what must hold
## is that the mounted normal is radial.
func _measure(old: Surface, now: Surface) -> Dictionary:
	var to := 0.0
	var normal := 0.0
	var uv := 0.0
	var skew_old := 0.0
	var skew_now := 0.0
	for i in old.positions.size():
		var hit := _closest(now, old.positions[i], old.normals[i])
		to = maxf(to, hit.distance)
		uv = maxf(uv, old.uvs[i].distance_to(hit.uv))
		var axis := old.axes[i]
		if axis != Vector3.ZERO and absf(old.normals[i].dot(axis)) < 0.99:
			var r := old.positions[i] - old.centres[i]
			var radial := (r - axis * r.dot(axis)).normalized()
			skew_old = maxf(skew_old, rad_to_deg(old.normals[i].angle_to(radial)))
			skew_now = maxf(skew_now, rad_to_deg((hit.normal as Vector3).angle_to(radial)))
		else:
			normal = maxf(normal, hit.turn)
	var from := 0.0
	var where := Vector3.ZERO
	for p in now.positions:
		var d: float = _closest(old, p, Vector3.ZERO).distance
		if d > from:
			from = d
			where = p
	if from > 0.00001 and OS.get_environment("FOUNTAIN_PROBE_WHERE") != "":
		print("  farthest mounted vertex %s: %.4f mm" % [where, from * 1000.0])
	return {"to": to, "from": from, "normal": normal, "uv": uv,
		"skew_old": skew_old, "skew_now": skew_now}


## The nearest point of `surface` to `p`: its distance, and the normal and UV
## the surface has there. Where several triangles lie within tolerance (a
## corner on a sharp edge), the normal and UV are those of the one whose normal
## turns least from `want_normal`; the distance is always the least.
func _closest(surface: Surface, p: Vector3, want_normal: Vector3) -> Dictionary:
	var best := {"distance": INF, "turn": 180.0, "uv": Vector2.ZERO, "normal": Vector3.ZERO}
	var chosen_within := false
	for pass_ in 2:
		# First only the triangles whose bounds reach p; if none is near, all.
		var reach := POSITION_TOLERANCE if pass_ == 0 else INF
		for t in surface.lows.size():
			var low := surface.lows[t] - Vector3.ONE * reach
			var high := surface.highs[t] + Vector3.ONE * reach
			if pass_ == 0 and (p.x < low.x or p.y < low.y or p.z < low.z
					or p.x > high.x or p.y > high.y or p.z > high.z):
				continue
			var a := surface.tris[t * 3]
			var b := surface.tris[t * 3 + 1]
			var c := surface.tris[t * 3 + 2]
			var w := _barycentric_closest(p, surface.positions[a], surface.positions[b],
				surface.positions[c])
			var q: Vector3 = surface.positions[a] * w.x + surface.positions[b] * w.y \
				+ surface.positions[c] * w.z
			var d := p.distance_to(q)
			var n := (surface.normals[a] * w.x + surface.normals[b] * w.y
				+ surface.normals[c] * w.z).normalized()
			var turn := rad_to_deg(want_normal.angle_to(n)) if want_normal != Vector3.ZERO else 0.0
			var within := d <= POSITION_TOLERANCE
			var take: bool
			if within:
				take = not chosen_within or turn < best.turn
			else:
				take = not chosen_within and d < best.distance
			best.distance = minf(best.distance, d)
			if take:
				chosen_within = within
				best.turn = turn
				best.normal = n
				best.uv = surface.uvs[a] * w.x + surface.uvs[b] * w.y + surface.uvs[c] * w.z
		if chosen_within:
			break
	return best


## Barycentric weights of the point of triangle abc nearest p (Ericson,
## Real-Time Collision Detection, 5.1.5).
func _barycentric_closest(p: Vector3, a: Vector3, b: Vector3, c: Vector3) -> Vector3:
	var ab := b - a
	var ac := c - a
	var ap := p - a
	var d1 := ab.dot(ap)
	var d2 := ac.dot(ap)
	if d1 <= 0.0 and d2 <= 0.0:
		return Vector3(1, 0, 0)
	var bp := p - b
	var d3 := ab.dot(bp)
	var d4 := ac.dot(bp)
	if d3 >= 0.0 and d4 <= d3:
		return Vector3(0, 1, 0)
	var vc := d1 * d4 - d3 * d2
	if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
		var v := d1 / (d1 - d3)
		return Vector3(1.0 - v, v, 0)
	var cp := p - c
	var d5 := ab.dot(cp)
	var d6 := ac.dot(cp)
	if d6 >= 0.0 and d5 <= d6:
		return Vector3(0, 0, 1)
	var vb := d5 * d2 - d1 * d6
	if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
		var w := d2 / (d2 - d6)
		return Vector3(1.0 - w, 0, w)
	var va := d3 * d6 - d5 * d4
	if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
		var w := (d4 - d3) / ((d4 - d3) + (d5 - d6))
		return Vector3(0, 1.0 - w, w)
	var denom := 1.0 / (va + vb + vc)
	var v := vb * denom
	var w := vc * denom
	return Vector3(1.0 - v - w, v, w)


func _compare_material(ring: String, parts: Array, mi: MeshInstance3D, names: Dictionary) -> void:
	var want: Material = (parts[0] as CSGShape3D).get("material")
	for part in parts:
		if (part as CSGShape3D).get("material") != want:
			_fails.append("%s: its maquette parts carry different materials" % ring)
	for s in mi.mesh.get_surface_count():
		var got := mi.get_active_material(s)
		var a := _signature(want)
		var b := _signature(got)
		if a != b:
			_fails.append("%s surface %d: material %s differs from the maquette's %s: %s" % [
				ring, s, got.resource_path if got else "none", names.get(want, "?"), _first_gap(a, b)])


func _signature(m: Material) -> Dictionary:
	var out := {}
	if m == null:
		return out
	out["class"] = m.get_class()
	for p in m.get_property_list():
		if not (p.usage & PROPERTY_USAGE_STORAGE):
			continue
		var key: String = p.name
		if key.begins_with("resource_") or key == "script":
			continue
		var value = m.get(key)
		out[key] = value.resource_path if value is Resource else var_to_str(value)
	return out


func _first_gap(a: Dictionary, b: Dictionary) -> String:
	for k in a:
		if not b.has(k) or a[k] != b[k]:
			return "%s: %s against %s" % [k, a[k], b.get(k, "missing")]
	for k in b:
		if not a.has(k):
			return "%s: missing against %s" % [k, b[k]]
	return ""


const INSTANCE_PROPERTIES := ["cast_shadow", "gi_mode", "visibility_range_begin",
	"visibility_range_end", "transparency", "extra_cull_margin", "lod_bias",
	"ignore_occlusion_culling", "layers"]


func _compare_instance(ring: String, parts: Array, mi: MeshInstance3D) -> void:
	for key in INSTANCE_PROPERTIES:
		for part in parts:
			if part.get(key) != mi.get(key):
				_fails.append("%s: %s is %s, the maquette's %s is %s" % [
					ring, key, mi.get(key), part.name, part.get(key)])
				break


func _compare_collision(ring: String, parts: Array, mi: MeshInstance3D, old: Surface) -> void:
	var collide := (parts[0] as CSGShape3D).use_collision
	for part in parts:
		if (part as CSGShape3D).use_collision != collide:
			_fails.append("%s: some of its maquette parts collide and some do not" % ring)
			return
	var bodies := mi.find_children("*", "CollisionObject3D", true, false)
	if not collide:
		if not bodies.is_empty():
			_fails.append("%s collides; its maquette parts did not" % ring)
		return
	if bodies.size() != 1:
		_fails.append("%s: %d collision bodies, expected one" % [ring, bodies.size()])
		return
	var body := bodies[0] as CollisionObject3D
	var csg := parts[0] as CSGShape3D
	if body.collision_layer != csg.collision_layer or body.collision_mask != csg.collision_mask:
		_fails.append("%s: collision layer/mask %d/%d, the maquette's %d/%d" % [
			ring, body.collision_layer, body.collision_mask, csg.collision_layer, csg.collision_mask])
	var solid := Surface.new()
	for shape in body.find_children("*", "CollisionShape3D", true, false):
		var cs := shape as CollisionShape3D
		var concave := cs.shape as ConcavePolygonShape3D
		if concave == null:
			_fails.append("%s: collision is %s, expected a trimesh" % [ring, cs.shape.get_class()])
			continue
		for p in concave.get_faces():
			solid.positions.append(cs.global_transform * p)
			solid.normals.append(Vector3.UP)
			solid.uvs.append(Vector2.ZERO)
		for t in range(solid.tris.size(), solid.positions.size(), 3):
			solid.add_triangle(t, t + 1, t + 2)
	var to := 0.0
	for p in old.positions:
		to = maxf(to, _closest(solid, p, Vector3.ZERO).distance)
	var from := 0.0
	for p in solid.positions:
		from = maxf(from, _closest(old, p, Vector3.ZERO).distance)
	print("%s collision: %d faces (area %.3f m², maquette %.3f); surface %.4f/%.4f mm from the maquette's" % [
		ring, solid.tris.size() / 3, solid.area, old.area, to * 1000.0, from * 1000.0])
	if to > POSITION_TOLERANCE or from > POSITION_TOLERANCE or absf(solid.area - old.area) > 1e-4 * old.area:
		_fails.append("%s: collision strays %.4f/%.4f mm, area %.4f against %.4f" % [
			ring, to * 1000.0, from * 1000.0, solid.area, old.area])
