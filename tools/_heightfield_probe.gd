extends Node

## Dev probe: what answers a ray dropped through the whole standing world, and at
## what height. Written 2026-10-01 for the world terrain pass: the ground is a
## patchwork (generated terrain pieces, the range, the city peninsula, roads laid
## over it, buildings), and before one heightfield is made of it we need to know
## which collider owns each cell and what is in the way.
##
## Args after the tool name: a region name or a bare step, then the CSV path,
## then an optional step that overrides the region's own.
##   _heightfield_probe world  out.csv        25m over the whole world box
##   _heightfield_probe park   out.csv        4m over the program envelope, padded
##   _heightfield_probe south_coast out.csv   10m, lagoon inlet to the south edge
##   _heightfield_probe 100 out.csv           the original form: world box, 100m
##   _heightfield_probe bounds x0 x1 z0 z1 step out.csv [up]   any box; no
##       park_floor; `up` appends up_y, up_owner, up_chain (see `_up_column`)
## The CSV defaults to `user://heightfield_probe.csv`. Samples sit at
## min + i * step for every i that stays inside max, so a grid's last row or
## column can fall short of max; the probe prints the dims it used.
##
## One row per cell: x, z, first-hit y and owner, then the ground y and owner,
## the number of colliders peeled to reach it, the ground's `kind`, the
## `surface` y and owner, and the `chain` of everything the ray met above the
## ground, `|`-separated, each entry `path@y`. The surface is the first
## collider down the ray that the park_floor rule below calls a floor, in every
## region, else the ground itself: in the park it is the earthwork, bluff or
## deck a person stands on where the terrain is buried under it (route F's
## embankment 8.7m over the lowland). Outside the park the rule is a guess;
## read the chain. Owner is
## the collider's path under `park_world`, cut to its first `OWNER_DEPTH`
## names; the chain carries `CHAIN_DEPTH` names so a cell can be judged later.
##
## Ground, and its kind:
##   terrain     the first collider with terrain, range, ground, coast,
##               peninsula, foothill or mainland in its own or an ancestor's
##               name (the plaza's floor is the CSG box `plaza/ground`, so it is
##               terrain here, at +0.00).
##   park_floor  park region only, where no terrain answered: the first
##               collider down the ray that is neither a road ribbon nor a
##               prop. Names are split into words at `_` and `/`, digits and a
##               plural `s` dropped. The collider's own name is read from its
##               last word back: if a `FLOOR_WORDS` word comes first it is a
##               floor whatever surrounds it and however steep its face, since
##               a cascade's earth bank is ground where it is not walkable
##               (`wheel_deck`, `pier_head_deck`, `west_shell/shore`, the ride
##               park's `walking_surface`, `east_earth_n`); if a `PROP_WORDS`
##               word comes first it is a prop (`basin_source_wall`,
##               `PL1_e_02_trunk`). Otherwise a `PROP_WORDS` word anywhere in its
##               path below `park_world` makes it a prop (`rides/R15_scrambler`,
##               `boardwalk_pavilion/.../wall_body`, `props/table_0_umb_top`,
##               `photo_hut_roof`, the fountain's `coping`). Anything else is a
##               floor if its face is walkable, normal y at least
##               `FLOOR_NORMAL_Y`. Words, not substrings, because `lighthouse`
##               is not a light, the ride park's deck is not a ride and
##               `pier_deck` is not a gate pier. As ground it acts only where
##               terrain is missing, so a prop misjudged over the plaza or the
##               reserve changes no ground_y, only a surface_y.
##   route_floor park region only, where neither terrain nor a park floor
##               answered but a walkable road ribbon did: a route over nothing
##               (Route B's north return ramp through the bluff cut).
##   unclassified  something was hit but nothing above qualified.
##   open        nothing collides on the whole ray (the sea has no collision).
## Prints a tally per ground owner and per kind. Returns 0; it is a measurement.

const REGIONS := {
	"world": {"min": Vector2(-300.0, -2800.0), "max": Vector2(3700.0, 3100.0),
		"step": 25.0, "park_floor": false},
	"park": {"min": Vector2(-272.0, -290.0), "max": Vector2(282.0, 280.0),
		"step": 4.0, "park_floor": true},
	"south_coast": {"min": Vector2(-300.0, 300.0), "max": Vector2(900.0, 2700.0),
		"step": 10.0, "park_floor": false},
}
const RAY_TOP := 2500.0
const RAY_BOTTOM := -300.0
const WORLD_LAYER := 1
const SETTLE_FRAMES := 30
const OWNER_DEPTH := 3
const CHAIN_DEPTH := 6
const MAX_PEELS := 32
const FLOOR_NORMAL_Y := 0.7
const GROUND_TOKENS := ["terrain", "range", "ground", "coast", "peninsula",
	"foothill", "mainland"]
## Words (see the header) that make a collider a prop for the park_floor rule.
const PROP_WORDS := ["prop", "furniture", "frontage", "kiosk", "stall", "booth",
	"hut", "shop", "building", "house", "roof", "wall", "parapet", "coping",
	"rail", "guard", "fence", "balustrade", "post", "lamp", "light", "sign",
	"bench", "bin", "tree", "palm", "plant", "planter", "hedge", "shrub",
	"tower", "arch", "beam", "pier", "perim", "shell", "fountain", "ride",
	"wheel", "coaster", "scrambler", "dodgem", "car", "train", "vehicle",
	"bandstand", "canopy", "awning", "umbrella", "umb", "table", "chair",
	"seat", "counter", "chain", "crowd", "guest", "wildlife", "pavilion",
	"shelter", "gate", "turnstile", "trunk", "funhouse"]
## Words that make a collider's own name a floor. The own name is read from its
## last word back and the first floor or prop word found decides.
const FLOOR_WORDS := ["deck", "floor", "surface", "walk", "walking", "apron",
	"court", "terrace", "tread", "ramp", "stair", "landing", "basin", "bowl",
	"shore", "bluff", "earth", "hill", "bed", "embankment", "platform",
	"paving", "threshold", "shelf", "berm", "bridge", "promenade", "lane",
	"queue", "path", "access", "entry", "sidewalk", "ground", "footbridge"]


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var region: Dictionary = REGIONS["world"].duplicate()
	region["step"] = 100.0
	var region_name := "world"
	if args.size() > 1:
		if REGIONS.has(args[1]):
			region_name = args[1]
			region = REGIONS[region_name].duplicate()
		else:
			region["step"] = float(args[1])
	var out_path := "user://heightfield_probe.csv"
	var up_rays := false
	if args.size() > 1 and args[1] == "bounds":
		if args.size() < 7:
			printerr("FAIL: bounds x0 x1 z0 z1 step [csv]")
			get_tree().quit(1)
			return
		region_name = "bounds"
		region = {"min": Vector2(float(args[2]), float(args[4])),
			"max": Vector2(float(args[3]), float(args[5])),
			"step": float(args[6]), "park_floor": false}
		if args.size() > 7:
			out_path = args[7]
		up_rays = args.size() > 8 and args[8] == "up"
	else:
		if args.size() > 2:
			out_path = args[2]
		if args.size() > 3:
			region["step"] = float(args[3])
	var step: float = region["step"]
	var lo: Vector2 = region["min"]
	var hi: Vector2 = region["max"]
	var nx := int(floor((hi.x - lo.x) / step + 1e-6)) + 1
	var nz := int(floor((hi.y - lo.y) / step + 1e-6)) + 1
	var fallback: bool = region["park_floor"]

	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in SETTLE_FRAMES:
		await get_tree().physics_frame
	ParkClock.running = false
	var world := get_tree().root.find_child("park_world", true, false)
	if world == null:
		printerr("FAIL: no park_world")
		get_tree().quit(1)
		return

	var space := get_viewport().get_world_3d().direct_space_state
	var f := FileAccess.open(out_path, FileAccess.WRITE)
	if f == null:
		printerr("FAIL: cannot write ", out_path)
		get_tree().quit(1)
		return
	f.store_line("x,z,top_y,top_owner,ground_y,ground_owner,peels,kind,surface_y,surface_owner,chain"
		+ (",up_y,up_owner,up_chain" if up_rays else ""))

	var tally := {}
	var kinds := {}
	var rays := 0
	var capped := 0
	var raised := 0
	for ix in nx:
		var x := lo.x + ix * step
		for iz in nz:
			var z := lo.y + iz * step
			var skip: Array[RID] = []
			var top_y := NAN
			var top_owner := ""
			var ground_y := NAN
			var ground_owner := ""
			var kind := "open"
			var floor_y := NAN
			var floor_owner := ""
			var floor_peels := 0
			var route_y := NAN
			var route_owner := ""
			var route_peels := 0
			var chain: PackedStringArray = []
			var peels := 0
			var reached_bottom := false
			for _i in MAX_PEELS:
				var q := PhysicsRayQueryParameters3D.create(
					Vector3(x, RAY_TOP, z), Vector3(x, RAY_BOTTOM, z), WORLD_LAYER)
				q.exclude = skip
				var hit := space.intersect_ray(q)
				rays += 1
				if hit.is_empty():
					reached_bottom = true
					break
				var body: Node = hit["collider"]
				var path := _path(world, body)
				var owner_name := _cut(path, OWNER_DEPTH)
				var y: float = hit["position"].y
				if is_nan(top_y):
					top_y = y
					top_owner = owner_name
					kind = "unclassified"
				if _is_ground(body):
					ground_y = y
					ground_owner = owner_name
					kind = "terrain"
					break
				if fallback and is_nan(route_y) and _is_ribbon(body) \
						and (hit["normal"] as Vector3).y >= FLOOR_NORMAL_Y:
					route_y = y
					route_owner = owner_name
					route_peels = peels
				if is_nan(floor_y) and _is_floor(body, path, hit):
					floor_y = y
					floor_owner = owner_name
					floor_peels = peels
				chain.append("%s@%.2f" % [_cut(path, CHAIN_DEPTH), y])
				skip.append(hit["rid"])
				peels += 1
			if kind != "terrain" and not reached_bottom and not is_nan(top_y):
				capped += 1
			var surface_y := floor_y
			var surface_owner := floor_owner
			if is_nan(surface_y):
				surface_y = ground_y
				surface_owner = ground_owner
			elif kind == "terrain" and surface_y > ground_y + 0.5:
				raised += 1
			if fallback and kind == "unclassified" and not is_nan(floor_y):
				ground_y = floor_y
				ground_owner = floor_owner
				kind = "park_floor"
				chain = chain.slice(0, floor_peels)
				peels = floor_peels
			elif fallback and kind == "unclassified" and not is_nan(route_y):
				ground_y = route_y
				ground_owner = route_owner
				kind = "route_floor"
				chain = chain.slice(0, route_peels)
				peels = route_peels
				surface_y = route_y
				surface_owner = route_owner
			kinds[kind] = int(kinds.get(kind, 0)) + 1
			if kind != "open":
				var key := ground_owner if ground_owner != "" else "(only non-ground)"
				var rec: Array = tally.get(key, [0, INF, -INF])
				rec[0] += 1
				if not is_nan(ground_y):
					rec[1] = minf(rec[1], ground_y)
					rec[2] = maxf(rec[2], ground_y)
				tally[key] = rec
			var line := "%d,%d,%s,%s,%s,%s,%d,%s,%s,%s,%s" % [
				x, z, _num(top_y), top_owner, _num(ground_y), ground_owner, peels,
				kind, _num(surface_y), surface_owner, "|".join(chain)]
			if up_rays:
				line += _up_column(space, world, x, z)
			f.store_line(line)
	f.close()

	print("")
	print("heightfield probe: region %s, step %sm, x %s..%s, z %s..%s, dims %d x %d = %d cells" % [
		region_name, str(step), str(lo.x), str(lo.x + (nx - 1) * step),
		str(lo.y), str(lo.y + (nz - 1) * step), nx, nz, nx * nz])
	print("rays cast %d, cells that hit MAX_PEELS without ground %d" % [rays, capped])
	print("terrain cells whose surface stands more than 0.5m above the terrain: %d" % raised)
	print("wrote ", ProjectSettings.globalize_path(out_path) if out_path.begins_with("user://") else out_path)
	print("kinds:")
	for k in kinds:
		print("  %7d  %s" % [int(kinds[k]), k])
	print("ground owner tally (cells, lowest y, highest y):")
	var keys := tally.keys()
	keys.sort_custom(func(a, b): return int(tally[a][0]) > int(tally[b][0]))
	for k in keys:
		var rec: Array = tally[k]
		print("  %7d  %9.2f %9.2f  %s" % [int(rec[0]), float(rec[1]), float(rec[2]), k])
	get_tree().quit(0)


## The `up` option: rays from `RAY_BOTTOM` upward, peeling every body, so each
## body answers once with its lowest face that looks down. A mesh exported
## inside out (its top wound to face down, its base cap to face up) is hollow to
## a ray from above, which falls through it to the base cap: on 2026-10-01 the
## southern range ridges, the southern lowland and the city foothills answered
## only at their -11m bases. From below, the same top answers. Writes the
## highest such hit, its owner, and every hit as `path@y`.
func _up_column(space: PhysicsDirectSpaceState3D, world: Node, x: float, z: float) -> String:
	var skip: Array[RID] = []
	var best_y := NAN
	var best_owner := ""
	var up_chain: PackedStringArray = []
	for _i in MAX_PEELS:
		var q := PhysicsRayQueryParameters3D.create(
			Vector3(x, RAY_BOTTOM, z), Vector3(x, RAY_TOP, z), WORLD_LAYER)
		q.exclude = skip
		var hit := space.intersect_ray(q)
		if hit.is_empty():
			break
		var path := _path(world, hit["collider"])
		var y: float = hit["position"].y
		up_chain.append("%s@%.2f" % [_cut(path, CHAIN_DEPTH), y])
		if is_nan(best_y) or y > best_y:
			best_y = y
			best_owner = _cut(path, CHAIN_DEPTH)
		skip.append(hit["rid"])
	return ",%s,%s,%s" % [_num(best_y), best_owner, "|".join(up_chain)]


func _num(v: float) -> String:
	if is_nan(v):
		return ""
	var t := "%.2f" % v
	return "0.00" if t == "-0.00" else t


func _path(world: Node, body: Node) -> PackedStringArray:
	return str(world.get_path_to(body)).split("/")


## The first names of a collider's path under `park_world`, so every mesh of one
## scene tallies together.
func _cut(path: PackedStringArray, depth: int) -> String:
	return "/".join(path.slice(0, mini(depth, path.size())))


## A road ribbon is a body carrying its centreline as `points`.
func _is_ribbon(body: Node) -> bool:
	return body.get_meta("points", PackedVector3Array()).size() >= 2


## Terrain: not a ribbon, and some name from the collider up holds a ground word.
func _is_ground(body: Node) -> bool:
	if _is_ribbon(body):
		return false
	var n: Node = body
	while n != null:
		var nm := String(n.name).to_lower()
		for t in GROUND_TOKENS:
			if nm.contains(t):
				return true
		n = n.get_parent()
	return false


## Park floor, for the fallback: the rule in the header.
func _is_floor(body: Node, path: PackedStringArray, hit: Dictionary) -> bool:
	if _is_ribbon(body):
		return false
	var own := _words(_own_name(path))
	for i in range(own.size() - 1, -1, -1):
		if own[i] in FLOOR_WORDS:
			return true
		if own[i] in PROP_WORDS:
			return false
	if (hit["normal"] as Vector3).y < FLOOR_NORMAL_Y:
		return false
	for seg in path:
		for w in _words(seg):
			if w in PROP_WORDS:
				return false
	return true


## The collider's own name, or its nearest ancestor's when the name is a bare
## type such as `StaticBody3D`.
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
