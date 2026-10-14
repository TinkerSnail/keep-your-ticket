extends Node

## Dev probe: where does the mounted ground come within 2 cm of a park floor's top, or stand
## above it? Written 2026-10-13 for Stage 2 of
## `documentation/terrain-height-grid-plan-2026-10-12.md`: the park's graded floors stand 8 to 12 cm
## over T2, T3, T6 and the reserve, and the ground built from the height grid must not come up
## through them. Run it on today's world for the baseline and again after the swap.
##
##   Godot --headless --path . tools/run.tscn -- _underlap_probe [--csv=<abs path>] [--step=1.0] [--clear=0.02]
##
## It mounts what `scenes/world/park_world.tscn` mounts under `places` and `shared`, but only:
##   the ground: `world_terrain` and `world_ground`, whatever they instance (today the master GLB;
##     after Stage 2 the built tiles), every collider in them, its faces of either winding no steeper
##     than `WorldTerrainSource`'s `MIN_UP`, as a ray dropped from above meets them;
##   the floors: `plaza` (hand-authored, with the generated paving and props it instances) and every
##     place whose wrapper has a generated twin in `scenes/world/generated/` (entrance, thresholds,
##     west shell, both anchors, boardwalk, groundworks, circulation, routes, program, landscape,
##     approach, towns, transit, skyline).
## A floor is a collider there (a body's shapes, or a CSG root's baked collision) that the word rule
## of `tools/_heightfield_probe.gd` calls a floor or does not call a prop and has a walkable face
## (normal y at least 0.7): route ribbons and their beds and embankments, junction floors, decks,
## aprons, courts, terraces, treads, ramps, stairs, landings, paving, lanes, platforms, service yards.
## Held ground is not a floor: colliders named `terrain_*` (the road corridor, the tunnel lids). The
## paving that has no collision (`pave_*`, `paving`, 12 mm proud of what it lies on) is a floor too,
## from its drawn faces, reported as such.
## Inside the developed envelope (`ParkPlan.REBUILD_FOOTPRINT_*`) each floor is sampled on a lattice
## (`step` metres, offset a quarter step so no sample lands on a whole-metre edge): its top walkable
## face there, and the top of the ground there. A sample is flagged where the ground stands within
## `clear` of the floor's top or above it. A flagged sample whose four lattice neighbours are also on
## the floor is `inside`; the rest are `edge`, where a floor meets the ground by design.
## Prints, per place and floor, samples and flags (above, within), the worst gap and where; totals
## for the paved floors, the earthworks and the paving without collision. `--csv` writes every
## flagged sample. Writes nothing in the project; returns 0, a measurement.

const ParkPlan := preload("res://scripts/park_plan.gd")
const WorldTerrainSource := preload("res://scripts/world_terrain_source.gd")
const PARK_WORLD := "res://scenes/world/park_world.tscn"
const GENERATED := "res://scenes/world/generated"
const GROUND_PLACES := ["world_terrain", "world_ground"]
const HAND_FLOOR_PLACES := ["plaza"]
const CELL := 4.0
const PAD := 8.0
const FLOOR_NORMAL_Y := 0.7
## As `tools/_heightfield_probe.gd`.
const PROP_WORDS := ["prop", "furniture", "frontage", "kiosk", "stall", "booth",
	"hut", "shop", "building", "house", "roof", "wall", "parapet", "coping",
	"rail", "guard", "fence", "balustrade", "post", "lamp", "light", "sign",
	"bench", "bin", "tree", "palm", "plant", "planter", "hedge", "shrub",
	"tower", "arch", "beam", "pier", "perim", "shell", "fountain", "ride",
	"wheel", "coaster", "scrambler", "dodgem", "car", "train", "vehicle",
	"bandstand", "canopy", "awning", "umbrella", "umb", "table", "chair",
	"seat", "counter", "chain", "crowd", "guest", "wildlife", "pavilion",
	"shelter", "gate", "turnstile", "trunk", "funhouse"]
const FLOOR_WORDS := ["deck", "floor", "surface", "walk", "walking", "apron",
	"court", "terrace", "tread", "ramp", "stair", "landing", "basin", "bowl",
	"shore", "bluff", "earth", "hill", "bed", "embankment", "platform",
	"paving", "threshold", "shelf", "berm", "bridge", "promenade", "lane",
	"queue", "path", "access", "entry", "sidewalk", "ground", "footbridge"]
## Words that make a floor earthworks rather than paved or decked, for the totals.
const EARTH_WORDS := ["embankment", "earth", "bank", "berm", "bluff", "hill", "shore", "soil",
	"slope", "batter", "mound"]

var _step := 1.0
var _clear := 0.02
var _lo := Vector2.ZERO
var _hi := Vector2.ZERO
var _ground := PackedVector3Array()
var _ground_owner := PackedStringArray()
var _ground_cells := {}


func _ready() -> void:
	var csv := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--csv="):
			csv = arg.trim_prefix("--csv=")
		elif arg.begins_with("--step="):
			_step = float(arg.trim_prefix("--step="))
		elif arg.begins_with("--clear="):
			_clear = float(arg.trim_prefix("--clear="))
	_lo = Vector2(ParkPlan.REBUILD_FOOTPRINT_MIN_X, ParkPlan.REBUILD_FOOTPRINT_MIN_Z)
	_hi = Vector2(ParkPlan.REBUILD_FOOTPRINT_MAX_X, ParkPlan.REBUILD_FOOTPRINT_MAX_Z)
	var t0 := Time.get_ticks_msec()

	# What park_world mounts, as it mounts it.
	var state := (load(PARK_WORLD) as PackedScene).get_state()
	var mounts := []
	for i in state.get_node_count():
		var parent := String(state.get_node_path(i, true))
		if not (parent.ends_with("places") or parent.ends_with("shared")):
			continue
		var inst := state.get_node_instance(i)
		if inst == null:
			continue
		var name := String(state.get_node_name(i))
		var base := inst.resource_path.get_file().get_basename()
		var role := ""
		if name in GROUND_PLACES or base in GROUND_PLACES:
			role = "ground"
		elif name in HAND_FLOOR_PLACES or FileAccess.file_exists(GENERATED.path_join(base + ".tscn")):
			role = "floor"
		if role == "":
			continue
		var xf := Transform3D.IDENTITY
		for p in state.get_node_property_count(i):
			if state.get_node_property_name(i, p) == &"transform":
				xf = state.get_node_property_value(i, p)
		mounts.append([name, inst, xf, role])
	var places := Node3D.new()
	places.name = "places"
	add_child(places)
	for m in mounts:
		var node := (m[1] as PackedScene).instantiate() as Node3D
		node.name = m[0]
		node.transform = m[2]
		places.add_child(node)
	for i in 4:
		await get_tree().process_frame
		await get_tree().physics_frame

	var ground_names := []
	var floor_names := []
	for m in mounts:
		(ground_names if m[3] == "ground" else floor_names).append(m[0])
	for name in ground_names:
		_add_ground(places.get_node(NodePath(name)))
	for t in range(0, _ground.size(), 3):
		for key in _cells(_ground[t], _ground[t + 1], _ground[t + 2]):
			if not _ground_cells.has(key):
				_ground_cells[key] = []
			(_ground_cells[key] as Array).append(t)
	print("underlap: ground %s, %d faces near the envelope; floors in %s" % [
		", ".join(ground_names), _ground.size() / 3, ", ".join(floor_names)])

	var rows := PackedStringArray()
	var totals := {}
	var excluded := {"held ground": 0, "props": 0, "not walkable": 0, "outside": 0}
	for place_name in floor_names:
		var place := places.get_node(NodePath(place_name))
		var place_lines := PackedStringArray()
		var place_samples := 0
		var place_flags := 0
		for n in [place] + place.find_children("*", "", true, false):
			var floor := _floor_of(n, place, excluded)
			if floor.is_empty():
				continue
			var r := _sample(floor["faces"])
			if int(r["samples"]) == 0:
				excluded["outside"] += 1
				continue
			var kind: String = floor["kind"]
			if not totals.has(kind):
				totals[kind] = {"floors": 0, "samples": 0, "inside_above": 0, "inside_within": 0,
					"edge_above": 0, "edge_within": 0, "flagged_floors": 0}
			var t: Dictionary = totals[kind]
			t["floors"] += 1
			t["samples"] += int(r["samples"])
			for k in ["inside_above", "inside_within", "edge_above", "edge_within"]:
				t[k] += int(r[k])
			place_samples += int(r["samples"])
			var flags := int(r["inside_above"]) + int(r["inside_within"]) + int(r["edge_above"]) + int(r["edge_within"])
			if flags == 0:
				continue
			t["flagged_floors"] += 1
			place_flags += flags
			var path := String(places.get_path_to(n))
			place_lines.append("    %s [%s]: %d samples; inside %d above, %d within; edge %d above, %d within; worst %+.3fm at (%.1f, %.1f) under %s" % [
				path, kind, r["samples"], r["inside_above"], r["inside_within"], r["edge_above"],
				r["edge_within"], r["worst"], r["worst_at"].x, r["worst_at"].y, r["worst_owner"]])
			for row in r["rows"]:
				rows.append("%s,%s,%s" % [path, kind, row])
		print("  %s: %d samples, %d flagged%s" % [place_name, place_samples, place_flags,
			"" if place_lines.is_empty() else ":\n" + "\n".join(place_lines)])
	for kind in totals:
		var t: Dictionary = totals[kind]
		print("underlap %s: %d floors, %d samples at %.2fm; inside: ground above at %d, within %.0f cm at %d; edge: above %d, within %d; %d floors flagged" % [
			kind, t["floors"], t["samples"], _step, t["inside_above"], _clear * 100.0, t["inside_within"],
			t["edge_above"], t["edge_within"], t["flagged_floors"]])
	print("underlap: not floors: %s; %.1fs" % [str(excluded), (Time.get_ticks_msec() - t0) / 1000.0])
	if csv != "":
		var f := FileAccess.open(csv, FileAccess.WRITE)
		f.store_string("floor,kind,x,z,floor_y,ground_y,gap,where,ground\n" + "\n".join(rows) + "\n")
		f.close()
		print("underlap: %d flagged samples written to %s" % [rows.size(), csv])
	places.free()
	get_tree().quit(0)


## The ground's faces near the envelope, either winding, steeper than `MIN_UP` skipped.
func _add_ground(place: Node) -> void:
	for n in [place] + place.find_children("*", "", true, false):
		var faces := _collision_faces(n)
		if faces.is_empty():
			continue
		var owner_name := String(place.get_path_to(n)).get_slice("/", 0) if n != place else String(place.name)
		if n.get_parent() != null and n.get_parent() != place and n is CollisionObject3D:
			owner_name = String(n.get_parent().name)
		for t in range(0, faces.size(), 3):
			var a := faces[t]
			var b := faces[t + 1]
			var c := faces[t + 2]
			if maxf(a.x, maxf(b.x, c.x)) < _lo.x - PAD or minf(a.x, minf(b.x, c.x)) > _hi.x + PAD \
					or maxf(a.z, maxf(b.z, c.z)) < _lo.y - PAD or minf(a.z, minf(b.z, c.z)) > _hi.y + PAD:
				continue
			var nrm := (b - a).cross(c - a)
			if absf(nrm.y) < nrm.length() * WorldTerrainSource.MIN_UP:
				continue
			_ground.append(a)
			_ground.append(b)
			_ground.append(c)
			_ground_owner.append(owner_name)


## A floor under `place`, as {faces, kind}, or empty; counts what it turns away.
func _floor_of(n: Node, place: Node, excluded: Dictionary) -> Dictionary:
	var faces := PackedVector3Array()
	if n is Area3D:
		return {}
	var collides := n is CollisionObject3D or (n is CSGShape3D and (n as CSGShape3D).is_root_shape() \
		and (n as CSGShape3D).use_collision)
	var path := String(place.get_path_to(n)).split("/", false) if n != place else PackedStringArray([String(place.name)])
	var own := _own_name(path)
	var own_words := _words(own)
	var paving := false
	if not collides:
		if not (n is MeshInstance3D and (n as MeshInstance3D).mesh != null):
			return {}
		if not ("paving" in own_words or "pave" in own_words):
			return {}
		if not (n as MeshInstance3D).find_children("*", "CollisionObject3D", true, false).is_empty():
			return {}
		paving = true
	if own.begins_with("terrain_"):
		excluded["held ground"] += 1
		return {}
	var verdict := ""
	for i in range(own_words.size() - 1, -1, -1):
		if own_words[i] in FLOOR_WORDS:
			verdict = "floor"
			break
		if own_words[i] in PROP_WORDS:
			verdict = "prop"
			break
	if verdict == "":
		for seg in path:
			for w in _words(seg):
				if w in PROP_WORDS:
					verdict = "prop"
		if verdict == "":
			verdict = "walkable"
	if verdict == "prop":
		excluded["props"] += 1
		return {}
	if paving:
		var mi := n as MeshInstance3D
		var xf := mi.global_transform
		for v in mi.mesh.get_faces():
			faces.append(xf * v)
	else:
		faces = _collision_faces(n)
	var walk := PackedVector3Array()
	for t in range(0, faces.size(), 3):
		var nrm := (faces[t + 1] - faces[t]).cross(faces[t + 2] - faces[t])
		if absf(nrm.y) >= nrm.length() * FLOOR_NORMAL_Y and nrm.length() > 0.0:
			walk.append(faces[t])
			walk.append(faces[t + 1])
			walk.append(faces[t + 2])
	if walk.is_empty():
		excluded["not walkable"] += 1
		return {}
	var kind := "paving without collision" if paving else "paved and decked"
	if not paving:
		for w in own_words:
			if w in EARTH_WORDS:
				kind = "earthworks"
	return {"faces": walk, "kind": kind}


## One floor on the lattice: its top at each sample inside the envelope, the ground's top there.
func _sample(faces: PackedVector3Array) -> Dictionary:
	var top := {}
	for t in range(0, faces.size(), 3):
		var a := faces[t]
		var b := faces[t + 1]
		var c := faces[t + 2]
		var i0 := ceili((maxf(minf(a.x, minf(b.x, c.x)), _lo.x) - _step * 0.25) / _step)
		var i1 := floori((minf(maxf(a.x, maxf(b.x, c.x)), _hi.x) - _step * 0.25) / _step)
		var j0 := ceili((maxf(minf(a.z, minf(b.z, c.z)), _lo.y) - _step * 0.25) / _step)
		var j1 := floori((minf(maxf(a.z, maxf(b.z, c.z)), _hi.y) - _step * 0.25) / _step)
		for i in range(i0, i1 + 1):
			for j in range(j0, j1 + 1):
				var p := Vector2(i * _step + _step * 0.25, j * _step + _step * 0.25)
				var y := _on(a, b, c, p)
				if is_nan(y):
					continue
				var key := Vector2i(i, j)
				if not top.has(key) or y > float(top[key]):
					top[key] = y
	var out := {"samples": top.size(), "inside_above": 0, "inside_within": 0, "edge_above": 0,
		"edge_within": 0, "worst": INF, "worst_at": Vector2.ZERO, "worst_owner": "", "rows": []}
	for key in top:
		var p := Vector2(key.x * _step + _step * 0.25, key.y * _step + _step * 0.25)
		var g := _ground_top(p)
		if is_nan(float(g[0])):
			continue
		var y: float = top[key]
		var gap := y - float(g[0])
		if gap >= _clear:
			continue
		var inside: bool = top.has(key + Vector2i(1, 0)) and top.has(key + Vector2i(-1, 0)) \
			and top.has(key + Vector2i(0, 1)) and top.has(key + Vector2i(0, -1))
		var where := "inside" if inside else "edge"
		var how := "above" if gap < 0.0 else "within"
		out[where + "_" + how] += 1
		if gap < out["worst"]:
			out["worst"] = gap
			out["worst_at"] = p
			out["worst_owner"] = g[1]
		(out["rows"] as Array).append("%.2f,%.2f,%.4f,%.4f,%.4f,%s,%s" % [p.x, p.y, y, g[0], gap, where, g[1]])
	return out


## The ground's top at `p` and whose it is, or [NAN, ""].
@warning_ignore("integer_division")
func _ground_top(p: Vector2) -> Array:
	var key := Vector2i(floori(p.x / CELL), floori(p.y / CELL))
	if not _ground_cells.has(key):
		return [NAN, ""]
	var best := -INF
	var who := ""
	for t in (_ground_cells[key] as Array):
		var y := _on(_ground[t], _ground[t + 1], _ground[t + 2], p)
		if not is_nan(y) and y > best:
			best = y
			who = _ground_owner[t / 3]
	return [best if best > -INF else NAN, who]


## The height of face abc over `p` (x, z), or NAN outside it; `WorldTerrainSource._top`'s test.
static func _on(a: Vector3, b: Vector3, c: Vector3, p: Vector2) -> float:
	var e0 := Vector2(b.x - a.x, b.z - a.z)
	var e1 := Vector2(c.x - a.x, c.z - a.z)
	var e2 := Vector2(p.x - a.x, p.y - a.z)
	var den := e0.x * e1.y - e1.x * e0.y
	if absf(den) < 1e-9:
		return NAN
	var u := (e2.x * e1.y - e1.x * e2.y) / den
	var v := (e0.x * e2.y - e2.x * e0.y) / den
	if u < -WorldTerrainSource.INSIDE_EPS or v < -WorldTerrainSource.INSIDE_EPS \
			or u + v > 1.0 + WorldTerrainSource.INSIDE_EPS:
		return NAN
	return a.y + u * (b.y - a.y) + v * (c.y - a.y)


func _cells(a: Vector3, b: Vector3, c: Vector3) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for x in range(floori(minf(a.x, minf(b.x, c.x)) / CELL), floori(maxf(a.x, maxf(b.x, c.x)) / CELL) + 1):
		for z in range(floori(minf(a.z, minf(b.z, c.z)) / CELL), floori(maxf(a.z, maxf(b.z, c.z)) / CELL) + 1):
			out.append(Vector2i(x, z))
	return out


## A collider's faces in world space as the physics has them, or none
## (`tools/_ground_faces_dump.gd`'s rule).
func _collision_faces(n: Node) -> PackedVector3Array:
	var out := PackedVector3Array()
	if n is CSGShape3D:
		var csg := n as CSGShape3D
		if not (csg.is_root_shape() and csg.use_collision):
			return out
		var shape := csg.bake_collision_shape()
		if shape == null:
			return out
		var xf := csg.global_transform
		for v in shape.get_faces():
			out.append(xf * v)
		return out
	if n is CollisionObject3D and not n is Area3D:
		for c in n.get_children():
			var cs := c as CollisionShape3D
			if cs == null or cs.disabled or cs.shape == null:
				continue
			var xf := cs.global_transform
			var faces := PackedVector3Array()
			if cs.shape is ConcavePolygonShape3D:
				faces = (cs.shape as ConcavePolygonShape3D).get_faces()
			elif cs.shape is BoxShape3D:
				var box := BoxMesh.new()
				box.size = (cs.shape as BoxShape3D).size
				faces = box.get_faces()
			elif cs.shape is CylinderShape3D:
				var cyl := CylinderMesh.new()
				cyl.top_radius = (cs.shape as CylinderShape3D).radius
				cyl.bottom_radius = cyl.top_radius
				cyl.height = (cs.shape as CylinderShape3D).height
				faces = cyl.get_faces()
			else:
				faces = cs.shape.get_debug_mesh().get_faces()
			for v in faces:
				out.append(xf * v)
	return out


## The collider's own name, or its nearest ancestor's when the name is a bare type.
func _own_name(path: PackedStringArray) -> String:
	for i in range(path.size() - 1, -1, -1):
		var nm := path[i]
		if not (nm.begins_with("StaticBody") or nm.begins_with("@") \
				or nm.begins_with("CollisionShape") or nm == "col"):
			return nm
	return ""


## Lower-case words of one name: split at `_`, digits dropped, a plural `s` cut.
func _words(name: String) -> PackedStringArray:
	var out: PackedStringArray = []
	for part in name.to_lower().split("_", false):
		var w := ""
		for ch in part:
			if not (ch >= "0" and ch <= "9"):
				w += ch
		if w.length() > 3 and w.ends_with("s") and not w.ends_with("ss"):
			w = w.substr(0, w.length() - 1)
		if w != "":
			out.append(w)
	return out
