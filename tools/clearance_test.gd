## Finds props standing in a walkway.
##
## `ParkPlan.open_spots` already refuses to put a scattered prop on the paving —
## it is the same `walkway_clearance` this reads. But **the hand-placed props
## were never checked against it**, and they are the majority: benches, bins,
## lamps, bollards, planters, the cart, the a-frames, the picnic tables. Worse,
## most of them are typed in the *old 80m* coordinates and run through
## `plaza_out`, so where they actually end up is not where they are written, and
## a coordinate that cleared a walkway before 2026-08-13 has no reason to now.
##
## So this reads the finished scene rather than the source. Every solid piece is
## measured against every walkway's paved edge and anything standing inside one
## is reported, worst first — which is the same shape of test as `walk_test`
## (a route is a claim) and `coplanar_test` (a surface is a claim), for the one
## claim neither of them makes: **paving is where the player walks, so nothing
## is standing on it.**
##
## Run: godot --headless --path . --script tools/clearance_test.gd
extends SceneTree

const Plan := preload("res://scripts/park_plan.gd")

## Which scenes hold things that could be standing in the way.
const SCENES := [
	"res://scenes/world/plaza_props.tscn",
	"res://scenes/world/thresholds.tscn",
	"res://scenes/world/entrance.tscn",
]

## Runs that are not corridors, and so cannot be intruded on.
##
## `street` and `apron` are 15m wide, and that width is **the whole street** —
## carriageway, pavements, shopfronts and all — where a spoke's width is the bit
## you walk down. Measured against them the entrance reports 25 faults and every
## one of them is the street doing its job: the turnstiles stand across it
## because that is what a turnstile is, the game booths and the cafe tables line
## it because that is what a street is. The distinction is real and the test has
## to know it, or the honest failures drown in it.
const NOT_CORRIDORS := [&"street", &"apron"]

## Props that are meant to be standing in a walkway.
##
## One entry so far and it earns its place: a bollard line crosses the walk on
## purpose. It is the only thing in the plaza whose whole function is to be in
## the road, so it is named here rather than given a rule.
const ALLOWED := ["bollard_n", "bollard_s"]

## Above this and a thing overhangs rather than blocks — an umbrella canopy, a
## lamp head, a valance, an awning. Measured to the piece's *underside*: the pole
## holding the canopy up is still a pole.
const HEAD := 2.0

## Under this and you walk over it rather than into it. `CharacterBody3D` has no
## step-up, so this is deliberately small — a 12mm litter square is scenery, a
## 120mm cup is a trip.
const TOE := 0.06

## How much of a piece may stand inside the paved edge before it is worth
## reporting. A bench set against the verge with a corner clipping the asphalt by
## a centimetre is a bench beside a path, which is what a bench is for.
const SLACK := 0.05

## The plaza's loose furniture, named. Only these take part in the second check.
##
## A list rather than a rule, and the reason is that the second check needs to
## know where one assembly *ends* and the flat scene it reads cannot say. The
## generator emits 360 sibling CSG nodes with no hierarchy at all, so the only
## thing separating a bench from the bin beside it is the naming convention —
## and the convention has two shapes in it, `bench_3_leg_l` and `cart_wheel_l`,
## which no single strip-the-suffix rule gets both of.
##
## It stays a list for a second reason, which is that the check is only
## meaningful for furniture anyway. A shopfront is an assembly 20m long and its
## bounding circle swallows the arcade next door; measured that way the entrance
## reports 200 faults and all of them are buildings being adjacent. Loose props
## are small, round-ish, and the only things `clear_of_walkways` moves.
const LOOSE := "^(bench_band_\\d+|bench_[a-z]+|bench_\\d+|bin_o?\\d+|lamp_o?\\d+" \
	+ "|tree_\\d+|aframe_\\d+|newsbox_\\d+|flagpole_\\d+|picnic_\\d+|photospot_\\d+" \
	+ "|planter_s_\\d+|table_\\d+|chair_\\d+|stanchion_\\d+|rope_\\d+" \
	+ "|cart|stroller|crate|ladder)"

## Pairs of assemblies that are meant to be inside each other. A chair tucks
## under its table and a rope runs between its two stanchions; both would read as
## faults and neither is one.
const NESTED := [
	["table_", "chair_"],
	["stanchion_", "rope_"],
]

var worst := {}
var solids := {}
var _loose := RegEx.new()


func _initialize() -> void:
	_loose.compile(LOOSE)
	for path in SCENES:
		var packed: PackedScene = load(path)
		if packed == null:
			printerr("cannot load %s" % path)
			quit(1)
			return
		var root := packed.instantiate()
		_walk(root, Transform3D.IDENTITY)
		root.free()

	var rows := []
	for nm in worst:
		rows.append(worst[nm])
	rows.sort_custom(func(a, b): return a["depth"] > b["depth"])

	print("\n--- props standing in a walkway ---")
	if rows.is_empty():
		print("none")
	for r in rows:
		print("%-24s %6.2fm into %-14s at (%7.2f, %7.2f)  [%s]" % [
			r["group"], r["depth"], r["run"], r["at"].x, r["at"].y, r["part"]])
	print("--- %d in a walkway ---" % rows.size())

	print("\n--- props standing in each other ---")
	var hits := _overlaps()
	if hits.is_empty():
		print("none")
	for h in hits:
		print("%-22s %-22s by %5.2fm  at (%7.2f, %7.2f)" % [
			h["a"], h["b"], h["depth"], h["at"].x, h["at"].y])
	print("--- %d pairs of %d assemblies ---\n" % [hits.size(), solids.size()])
	quit(1 if rows.size() + hits.size() > 0 else 0)


## The companion fault, and the one the walkway rule *creates*: two props pushed
## off the paving can be pushed to the same place. `clear_of_walkways` is a pure
## function of one point — deliberately, because two generators have to agree
## about it without sharing a register — so it cannot see what is already
## standing there, and something has to.
##
## Assemblies as circles rather than as shapes. It is coarse and it over-reports
## by design: the cost of a false positive is reading a line of output and the
## cost of a miss is a bench inside a cart.
func _overlaps() -> Array:
	var circles := {}
	for g in solids:
		var lo := Vector2(1e9, 1e9)
		var hi := Vector2(-1e9, -1e9)
		for part in solids[g]:
			lo = Vector2(minf(lo.x, part["at"].x), minf(lo.y, part["at"].y))
			hi = Vector2(maxf(hi.x, part["at"].x), maxf(hi.y, part["at"].y))
		var centre: Vector2 = (lo + hi) * 0.5
		var r := 0.0
		for part in solids[g]:
			r = maxf(r, centre.distance_to(part["at"]) + float(part["reach"]))
		circles[g] = {"at": centre, "r": r}

	var out := []
	var keys := circles.keys()
	for i in keys.size():
		for j in range(i + 1, keys.size()):
			if _nested(keys[i], keys[j]):
				continue
			var a: Dictionary = circles[keys[i]]
			var b: Dictionary = circles[keys[j]]
			var gap: float = a["at"].distance_to(b["at"]) - a["r"] - b["r"]
			if gap >= -SLACK:
				continue
			out.append({"a": keys[i], "b": keys[j], "depth": -gap,
				"at": (a["at"] + b["at"]) * 0.5})
	out.sort_custom(func(x, y): return x["depth"] > y["depth"])
	return out


func _nested(a: String, b: String) -> bool:
	for pair in NESTED:
		if (a.begins_with(pair[0]) and b.begins_with(pair[1])) \
				or (a.begins_with(pair[1]) and b.begins_with(pair[0])):
			return true
	return false


func _walk(n: Node, parent: Transform3D) -> void:
	var here := parent
	if n is Node3D:
		here = parent * (n as Node3D).transform
		_measure(n as Node3D, here)
	for c in n.get_children():
		_walk(c, here)


func _measure(n: Node3D, world: Transform3D) -> void:
	var half := Vector3.ZERO
	if n is CSGBox3D:
		half = (n as CSGBox3D).size * 0.5
	elif n is CSGCylinder3D:
		var c := n as CSGCylinder3D
		half = Vector3(c.radius, c.height * 0.5, c.radius)
	else:
		return
	if not n.get("use_collision"):
		return

	# The piece's own bottom and top, once turned. A lintel is high, a threshold
	# board's post is not, and the transform is the only thing that knows which.
	var ys := []
	for sx in [-1.0, 1.0]:
		for sy in [-1.0, 1.0]:
			for sz in [-1.0, 1.0]:
				ys.append((world * Vector3(half.x * sx, half.y * sy, half.z * sz)).y)
	var low: float = ys.min()
	var high: float = ys.max()
	if low > HEAD or high < TOE:
		return

	var group := _group(n.name)

	# The pieces of each loose assembly, for the second check to draw a circle
	# round once they are all in. Collected rather than accumulated because a
	# circle grown from whichever part happened to come first is centred on that
	# part, not on the prop.
	var m := _loose.search(n.name)
	if m != null:
		var g: String = m.get_string(1)
		if not solids.has(g):
			solids[g] = []
		solids[g].append({"at": Vector2(world.origin.x, world.origin.z),
			"reach": Vector2(half.x, half.z).length()})

	for ok in ALLOWED:
		if group.begins_with(ok):
			return

	# Corners of the footprint, in world XZ. Conservative for a cylinder, which
	# is what we want — a round bin blocking a walk blocks it.
	var deepest := 0.0
	var at := Vector2.ZERO
	var run := ""
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			var p := world * Vector3(half.x * sx, 0.0, half.z * sz)
			var q := Vector2(p.x, p.z)
			var hit := _deepest_run(q)
			if hit["depth"] > deepest:
				deepest = hit["depth"]
				at = q
				run = hit["run"]
	if deepest <= SLACK:
		return

	if not worst.has(group) or worst[group]["depth"] < deepest:
		worst[group] = {"group": group, "depth": deepest, "at": at,
			"run": run, "part": n.name}


## How far into a corridor a point stands, and which one. `walkway_clearance`
## would do the arithmetic but it measures every run, and two of them are not
## corridors — see `NOT_CORRIDORS`.
func _deepest_run(p: Vector2) -> Dictionary:
	var deepest := 0.0
	var id := ""
	for seg in Plan.walkway_segments():
		if seg["id"] in NOT_CORRIDORS:
			continue
		var a: Vector2 = seg["from"]
		var b: Vector2 = seg["to"]
		var d := b - a
		var l2 := d.length_squared()
		var t := 0.0 if l2 < 0.0001 else clampf((p - a).dot(d) / l2, 0.0, 1.0)
		var deep: float = float(seg["width"]) * 0.5 - (p - (a + d * t)).length()
		if deep > deepest:
			deepest = deep
			id = str(seg["id"])
	return {"depth": deepest, "run": id}


## `bench_3_leg_l` is one bench. Moving a prop means moving all of its boxes, so
## both reports are per assembly and this is what decides where one ends.
##
## The generator names a part `<assembly>_<part>` and an assembly `<what>_<n>`,
## so the rule is: **keep everything up to the last number, and if there is no
## number drop the final word.** `bench_band_0_seat` → `bench_band_0`,
## `bench_south_seat` → `bench_south`, `cart_wheel_l` → `cart`, `litter_5` →
## itself. It is a naming convention doing the work of a scene hierarchy, which
## is a fair description of the whole file — the generator emits one flat list of
## CSG nodes, so there is nothing else to read an assembly off.
func _group(nm: String) -> String:
	var parts := nm.split("_")
	var last := -1
	for i in parts.size():
		if str(parts[i]).is_valid_int():
			last = i
	if last >= 0:
		return "_".join(parts.slice(0, last + 1))
	return "_".join(parts.slice(0, maxi(1, parts.size() - 1)))
