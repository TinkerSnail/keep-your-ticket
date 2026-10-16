extends RefCounted

## Reader for the Grand Circuit east station yard's two staff stairs, YC-R11 and
## YC-R12, editor-owned since 2026-10-16 (Christina: "Make them editor-owned").
## Their courses are the Marker3Ds saved in `scenes/world/yard_connections.tscn`,
## in literal Godot world metres; this turns them into the records the generator
## builds the stairs from (`_yard_connection` in `tools/gen_props.gd`) and never
## writes the scene. It names no autoload, so a `--script` run may preload it.
##
## The yard is S3's paving behind the east platform, at the lane's level. R11's
## service leaves its court, crosses route F square at grade and comes down three
## flights; R12's east service leaves its terminal's deck, bridges S3 and comes
## down a dog-leg (approved as drawn, the maps' `yardConnections` at e4e4273).
## Ride service, staff only, so each is a service stair: no flight steeper than
## 37 degrees or rising more than 3 m, a 1.2 m landing between flights, which the
## generator checks.
##
## A record is {id, ride, users, elements}. A stair is a child of the scene's root
## carrying `ride` and `users`; its elements are its children carrying `kind`, in
## order, each an axis `p` (from, to) widened to `w`. `kind` is walk, crossing (at
## grade over the route `over`), landing, flight (`p` its head and foot) or bridge
## (over `over`); a `raised` walk stands over the ground; `ends` names the paving
## the last element meets. An element's points are its Marker3Ds in order; one
## whose first marker is not `from` (or a flight's `head`) starts where the
## element before it ends, so the two share that joint.

const SCENE := "res://scenes/world/yard_connections.tscn"
const STARTS := [&"from", &"head"]


static func read() -> Array:
	var packed := load(SCENE) as PackedScene
	assert(packed != null, "the yard stairs' editor source %s is missing" % SCENE)
	var root := packed.instantiate() as Node3D
	assert(root != null, "the yard stairs' editor source is not a Node3D")
	var out := records(root)
	root.free()
	return out


static func records(root: Node3D) -> Array:
	assert(root.get_meta("coordinate_space", "") == &"godot_world_metres",
		"the yard stairs' editor source must stay in literal Godot world metres")
	var out: Array = []
	for stair in root.get_children():
		if not (stair is Node3D and stair.has_meta("ride")):
			continue
		var elements: Array = []
		var last := Vector3.INF
		for element in stair.get_children():
			if not (element is Node3D and element.has_meta("kind")):
				continue
			var record := {}
			for meta_name in element.get_meta_list():
				record[String(meta_name)] = element.get_meta(meta_name)
			record["kind"] = StringName(record["kind"])
			record["w"] = float(record["w"])
			var points: Array = []
			var markers := element.get_children().filter(func(c: Node) -> bool:
				return c is Marker3D)
			if markers.is_empty() or not StringName(markers[0].name) in STARTS:
				assert(last != Vector3.INF, "%s/%s has no start and nothing before it" % [
					stair.name, element.name])
				points.append(last)
			for marker in markers:
				points.append(_position(marker, root))
			assert(points.size() == 2, "%s/%s is %d points, not an axis's two" % [
				stair.name, element.name, points.size()])
			record["p"] = points
			last = points[-1]
			elements.append(record)
		out.append({"id": StringName(stair.name),
			"ride": StringName(stair.get_meta("ride")),
			"users": StringName(stair.get_meta("users", &"staff")),
			"elements": elements})
	return out


## A marker's position in the root's space, through every Node3D between, so a
## stair or an element moved or turned in the editor carries its markers with it.
static func _position(marker: Node3D, root: Node3D) -> Vector3:
	var xf := marker.transform
	var parent := marker.get_parent()
	while parent is Node3D and parent != root:
		xf = (parent as Node3D).transform * xf
		parent = parent.get_parent()
	assert(parent == root, "%s is not inside the yard stairs' source" % marker.name)
	return xf.origin
