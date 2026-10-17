extends RefCounted

## Reader for the placements that stand on D2 Coastal Creek, editor-owned since
## 2026-10-16 (Christina: "Culvert D2"; the maquette rule, Christina 2026-09-24:
## generated placement moves to an owned source when it is next revised,
## lossless first and changed after). They are saved beside the creek's course in
## `scenes/world/fairground_layout.tscn`, under `water/CW-AQ`, in the layout's own
## rebuild source space (`ParkPlan.rebuild_expand_point` maps them to the world,
## as it maps the course); this turns them into records and never writes the
## scene. It names no autoload, so a `--script` run may preload it.
##
## - `course`: the creek's course markers in order (`points`), each its place,
##   `level`, the bed there in world metres (NAN where none is set), and `weir`
##   on the controlled weir's crest.
## - `drop`: the built drop between the creek's upper course and its last reach
##   (Christina, 2026-10-16: "Old levels + a drop"), its Marker3D at the crest on
##   the course, metadata `crest` (the bed there, world metres), `steps`, `run`
##   (the cascade's length along the course, metres) and `pool_depth` (the
##   plunge pool's bed under the last reach's head).
## - `pond`: the rain pond, its Marker3D at the pond's centre, metadata `radii`
##   (the water's half extents, x and z, world metres) and `bank_radii` (the
##   planted bank's), `water` and `bed` its levels in world metres.
## - `CB1`, `CB2`: the two footbridges, each a Marker3D at the deck's centre,
##   turned about y to the way its walk crosses; metadata `size` is the deck's
##   (across, along) in world metres, `guard_inset` how far each guard rail
##   stops short of the deck's ends.
## - `garden`: the pond garden loop (the funhouse garden loop, re-sited,
##   Christina 2026-10-16: "Approve, commit, build"), metadata `width` in world
##   metres; its `loop` and `stem` children hold their courses' Marker3Ds in
##   order. The loop's ends are CB1's; the stem leaves route B's south return.
## - `yard`: S2's staff yard by the Boardwalk station made solid and gated
##   (Christina, 2026-10-16: "Make it solid and gate it"). `north_fence`: `from`
##   and `to`, its two ends (the `west_end` and `east_end` markers); `gate`, the
##   staff gate's centre on it, `gate_width` the distance between its posts in
##   world metres, and `locked`. `S2_gate`: `posts`, its two gate posts in order
##   (`post_a`, on the bluff's side, then `post_b`), and `locked`.

const SCENE := "res://scenes/world/fairground_layout.tscn"
const RECORD := "water/CW-AQ"


static func read() -> Dictionary:
	var packed := load(SCENE) as PackedScene
	assert(packed != null, "the creek's editor source %s is missing" % SCENE)
	var root := packed.instantiate() as Node3D
	var out := records(root)
	root.free()
	return out


static func records(root: Node3D) -> Dictionary:
	assert(root.get_meta("coordinate_space", "") == "rebuild_source_before_expansion",
		"the creek's editor source must stay in rebuild source space")
	var creek := root.get_node(RECORD) as Node3D
	assert(creek != null, "the Fairground source has no Coastal Creek")
	var pond := creek.get_node("pond") as Node3D
	assert(pond != null and pond.has_meta("radii") and pond.has_meta("bank_radii"),
		"the creek's pond needs its marker, radii and bank_radii")
	var course: Array = []
	for marker in creek.get_node("points").get_children():
		if marker is Marker3D:
			course.append({"at": _plan(marker, root),
				"level": float(marker.get_meta("level", NAN)),
				"weir": bool(marker.get_meta("weir", false))})
	var out := {
		"course": course,
		"pond": {"at": _plan(pond, root),
			"radii": Vector2(pond.get_meta("radii")),
			"bank_radii": Vector2(pond.get_meta("bank_radii")),
			"water": float(pond.get_meta("water", NAN)),
			"bed": float(pond.get_meta("bed", NAN))},
		"crossings": {},
	}
	for id in [&"CB1", &"CB2"]:
		var bridge := creek.get_node(String(id)) as Node3D
		assert(bridge != null and bridge.has_meta("size"),
			"the creek's %s needs its marker and size" % id)
		out["crossings"][id] = {"at": _plan(bridge, root),
			"yaw": _yaw(bridge, root),
			"size": Vector2(bridge.get_meta("size")),
			"guard_inset": float(bridge.get_meta("guard_inset", 0.0))}
	var drop := creek.get_node_or_null("drop") as Node3D
	if drop != null:
		out["drop"] = {"at": _plan(drop, root), "crest": float(drop.get_meta("crest")),
			"steps": int(drop.get_meta("steps")), "run": float(drop.get_meta("run")),
			"pool_depth": float(drop.get_meta("pool_depth"))}
	var garden := creek.get_node_or_null("garden") as Node3D
	if garden != null:
		out["garden"] = {"width": float(garden.get_meta("width")),
			"loop": _course(garden.get_node("loop"), root),
			"stem": _course(garden.get_node("stem"), root)}
	var yard := creek.get_node_or_null("yard") as Node3D
	if yard != null:
		var fence := yard.get_node("north_fence") as Node3D
		var gate := fence.get_node("gate") as Node3D
		assert(gate != null and gate.has_meta("width"),
			"the yard's north fence needs its gate marker and width")
		var s2 := yard.get_node("S2_gate") as Node3D
		out["yard"] = {
			"north_fence": {"from": _plan(fence.get_node("west_end"), root),
				"to": _plan(fence.get_node("east_end"), root),
				"gate": _plan(gate, root), "gate_width": float(gate.get_meta("width")),
				"locked": bool(gate.get_meta("locked", true))},
			"S2_gate": {"posts": [_plan(s2.get_node("post_a"), root),
				_plan(s2.get_node("post_b"), root)],
				"locked": bool(s2.get_meta("locked", true))}}
	return out


static func _course(parent: Node, root: Node3D) -> Array[Vector2]:
	var out: Array[Vector2] = []
	for marker in parent.get_children():
		if marker is Marker3D:
			out.append(_plan(marker, root))
	return out


## A marker's place in the layout's plan (x, z), through every Node3D between.
static func _plan(marker: Node3D, root: Node3D) -> Vector2:
	var p := _xform(marker, root).origin
	return Vector2(p.x, p.z)


static func _yaw(marker: Node3D, root: Node3D) -> float:
	var b := _xform(marker, root).basis
	var along := b * Vector3.BACK
	return atan2(along.x, along.z)


static func _xform(marker: Node3D, root: Node3D) -> Transform3D:
	var xf := marker.transform
	var parent := marker.get_parent()
	while parent is Node3D and parent != root:
		xf = (parent as Node3D).transform * xf
		parent = parent.get_parent()
	assert(parent == root, "%s is not inside the creek's source" % marker.name)
	return xf
