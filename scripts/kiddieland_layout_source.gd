extends RefCounted

## The read boundary between the editor-owned Kiddieland scene and anything
## derived from it. No coordinate is repeated here: generator and validation
## code receive the positions currently saved on the scene's Marker3D nodes.
##
## Coordinates remain in rebuild-atlas source space. A consumer applies
## ParkPlan.rebuild_expand_point to an assembly base exactly once and derives
## its height from the owning terrain.

const Layout = preload("res://scenes/world/kiddieland_layout.tscn")


static func instantiate() -> Node3D:
	var root := Layout.instantiate() as Node3D
	assert(root != null, "kiddieland layout source did not instantiate")
	assert(root.get_meta("coordinate_space", "") == "rebuild_source_before_expansion",
		"kiddieland layout source has the wrong coordinate space")
	return root


static func route_runs(root: Node) -> Array:
	var out: Array = []
	for route in root.get_node("public_routes").get_children():
		out.append({
			"id": StringName(route.name),
			"route": StringName(route.get_meta("route")),
			"width": float(route.get_meta("width")),
			"build": bool(route.get_meta("build")),
			"closed": bool(route.get_meta("closed", false)),
			"owner": StringName(route.get_meta("owner", "")),
			"points": marker_points(route, root),
		})
	return out


## Complete R14 source. It also carries the later exit, service and manual-photo
## relationships even though the current greybox builder consumes only track,
## station, queue and photo-bay construction.
static func r14_site(root: Node) -> Dictionary:
	var ride := root.get_node("rides/R14")
	var station := ride.get_node("station") as Marker3D
	var photo := ride.get_node("manual_photo") as Marker3D
	return {
		"id": &"R14",
		"kind": StringName(ride.get_meta("kind")),
		"track": marker_points(ride.get_node("track"), root),
		"station": marker_point(station, root),
		"station_size": Vector2(station.get_meta("size")),
		"queue": marker_points(ride.get_node("queue"), root),
		"queue_width": float(ride.get_meta("queue_width", 2.6)),
		"exit": marker_points(ride.get_node("exit"), root),
		"service": marker_points(ride.get_node("service"), root),
		"photo": marker_point(photo, root),
		"photo_size": Vector2(photo.get_meta("size")),
		"max_lift": float(ride.get_meta("max_lift")),
	}


static func ride_sites(root: Node) -> Dictionary:
	var out := {&"R14": r14_site(root)}
	for ride in root.get_node("rides").get_children():
		if not ride is Marker3D:
			continue
		var site := {
			"id": StringName(ride.name),
			"kind": StringName(ride.get_meta("kind")),
			"at": marker_point(ride, root),
		}
		if ride.has_meta("radii"):
			site["radii"] = Vector2(ride.get_meta("radii"))
		if ride.has_meta("radius"):
			site["radius"] = float(ride.get_meta("radius"))
		if ride.has_meta("queue_width"):
			site["queue_width"] = float(ride.get_meta("queue_width"))
		if ride.has_node("queue"):
			site["queue"] = marker_points(ride.get_node("queue"), root)
		out[StringName(ride.name)] = site
	return out


static func p4_site(root: Node) -> Dictionary:
	var site := root.get_node("destinations/P4_play_garden") as Marker3D
	return {
		"id": &"P4",
		"kind": &"play_garden",
		"at": marker_point(site, root),
		"radii": Vector2(site.get_meta("radii")),
		"access": marker_points(site.get_node("access"), root),
	}


static func support_sites(root: Node) -> Dictionary:
	var out := {}
	for node in root.get_node("destinations").get_children():
		var id := String(node.name).get_slice("_", 0)
		var site := {
			"id": StringName(id),
			"at": marker_point(node, root),
			"shape": StringName(node.get_meta("shape")),
		}
		if node.has_meta("radii"):
			site["radii"] = Vector2(node.get_meta("radii"))
		if node.has_meta("size"):
			site["size"] = Vector2(node.get_meta("size"))
		if node.has_meta("water_system"):
			site["water_system"] = StringName(node.get_meta("water_system"))
		out[StringName(id)] = site
	return out


static func marker_points(parent: Node, root: Node3D) -> Array:
	var out: Array = []
	for child in parent.get_children():
		if child is Marker3D:
			out.append(marker_point(child, root))
	return out


## Read in source-root space so moving a whole ride, route or destination
## parent in the editor carries all of its child controls with it.
static func marker_point(marker: Node3D, root: Node3D) -> Vector2:
	var transform := marker.transform
	var parent := marker.get_parent()
	while parent is Node3D and parent != root:
		transform = (parent as Node3D).transform * transform
		parent = parent.get_parent()
	assert(parent == root, "%s is not inside the Kiddieland source root" % marker.name)
	return Vector2(transform.origin.x, transform.origin.z)
