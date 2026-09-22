@tool
extends Node3D

## The loop's artistic course is the editor-owned Curve3D in this scene. This
## script derives its wearing surface, collision, seaward fascia and guardrail;
## it never writes or replaces the source scene.

@export var deck_material: Material
@export var fascia_material: Material
@export var rail_material: Material
@export_range(6.0, 10.0, 0.25) var route_width := 8.0

const DECK_TOP := -5.958
const DECK_THICKNESS := 0.48
const RAIL_HEIGHT := 1.15
const RAIL_THICKNESS := 0.10

var _rebuild_queued := false


func _ready() -> void:
	var course := get_node_or_null("public_ride_loop") as Path3D
	if course != null and course.curve != null \
			and not course.curve.changed.is_connected(_queue_rebuild):
		course.curve.changed.connect(_queue_rebuild)
	var aprons := get_node_or_null("public_aprons")
	if aprons != null:
		for child in aprons.get_children():
			var apron := child as Path3D
			if apron != null and apron.curve != null \
					and not apron.curve.changed.is_connected(_queue_rebuild):
				apron.curve.changed.connect(_queue_rebuild)
	_queue_rebuild()


func _queue_rebuild() -> void:
	if _rebuild_queued or not is_inside_tree():
		return
	_rebuild_queued = true
	call_deferred("_rebuild")


func _rebuild() -> void:
	_rebuild_queued = false
	var course := get_node_or_null("public_ride_loop") as Path3D
	var derived := get_node_or_null("derived_deck") as Node3D
	if course == null or course.curve == null or derived == null:
		return
	for child in derived.get_children():
		child.free()

	var points: Array[Vector3] = []
	for i in course.curve.point_count:
		var p := course.curve.get_point_position(i)
		p.y = DECK_TOP
		points.append(p)
	if points.size() < 3:
		return

	var inner: Array[Vector3] = []
	var outer: Array[Vector3] = []
	for i in points.size():
		var here := points[i]
		var incoming := Vector3.ZERO
		var outgoing := Vector3.ZERO
		if i == 0 and not course.curve.closed:
			outgoing = Vector3(points[1].x - here.x, 0.0,
				points[1].z - here.z).normalized()
			incoming = outgoing
		elif i == points.size() - 1 and not course.curve.closed:
			incoming = Vector3(here.x - points[i - 1].x, 0.0,
				here.z - points[i - 1].z).normalized()
			outgoing = incoming
		else:
			var prev := points[(i - 1 + points.size()) % points.size()]
			var next := points[(i + 1) % points.size()]
			incoming = Vector3(here.x - prev.x, 0.0, here.z - prev.z).normalized()
			outgoing = Vector3(next.x - here.x, 0.0, next.z - here.z).normalized()
		var side_a := Vector3(-incoming.z, 0.0, incoming.x)
		var side_b := Vector3(-outgoing.z, 0.0, outgoing.x)
		var miter := (side_a + side_b).normalized()
		if miter.length_squared() < 0.25:
			miter = side_b
		var denom := maxf(absf(miter.dot(side_b)), 0.55)
		var offset := miter * minf(route_width * 0.5 / denom, route_width * 0.72)
		# Positive x/z area makes this course clockwise on the planning map:
		# +offset faces the ride infield and -offset faces the water/outer edge.
		inner.append(here + offset)
		outer.append(here - offset)

	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var segment_count := points.size() if course.curve.closed else points.size() - 1
	var chain := 0.0
	for i in segment_count:
		var j := (i + 1) % points.size()
		var next_chain := chain + points[i].distance_to(points[j])
		# The source texture's board joints run across U. Accumulating V along
		# the authored course keeps the boards transverse through every bend,
		# so their direction continues to carry the Boardwalk's flow.
		var uv_outer_a := Vector2(0.0, chain * 0.44642857)
		var uv_inner_a := Vector2(route_width * 0.44642857, chain * 0.44642857)
		var uv_inner_b := Vector2(route_width * 0.44642857, next_chain * 0.44642857)
		var uv_outer_b := Vector2(0.0, next_chain * 0.44642857)
		_add_triangle_uv(surface, outer[i], inner[i], inner[j],
			uv_outer_a, uv_inner_a, uv_inner_b)
		_add_triangle_uv(surface, outer[i], inner[j], outer[j],
			uv_outer_a, uv_inner_b, uv_outer_b)
		chain = next_chain
	surface.generate_tangents()
	var mesh := surface.commit()
	var deck := MeshInstance3D.new()
	deck.name = "wearing_surface"
	deck.mesh = mesh
	deck.material_override = deck_material
	deck.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	derived.add_child(deck)

	var body := StaticBody3D.new()
	body.name = "walking_surface"
	var collision := CollisionShape3D.new()
	collision.name = "surface_collision"
	var surface_shape := mesh.create_trimesh_shape() as ConcavePolygonShape3D
	# The route is an intentionally thin wearing course. Accept contact from
	# either side so a teleported test body and a real player crossing the 2mm
	# seam both settle onto it instead of falling through to the shore mesh.
	surface_shape.backface_collision = true
	collision.shape = surface_shape
	body.add_child(collision)
	derived.add_child(body)

	for i in segment_count:
		var j := (i + 1) % points.size()
		_beam(derived, "outer_fascia_%02d" % i,
			outer[i] - Vector3.UP * DECK_THICKNESS * 0.5,
			outer[j] - Vector3.UP * DECK_THICKNESS * 0.5,
			Vector3(0.18, DECK_THICKNESS, 1.0), fascia_material, false)
		for level in [0.38, 0.98]:
			_beam(derived, "outer_rail_%02d_%02d" % [i, int(level * 100.0)],
				outer[i] + Vector3.UP * level,
				outer[j] + Vector3.UP * level,
				Vector3(RAIL_THICKNESS, RAIL_THICKNESS, 1.0), rail_material, true)
		_beam(derived, "outer_post_%02d" % i, outer[i],
			outer[i] + Vector3.UP * RAIL_HEIGHT,
			Vector3(0.13, 0.13, 1.0), rail_material, true)

	_rebuild_public_aprons()


## The Santa Monica reference is used here as a spatial relationship: ride
## entrances meet one continuous timber pedestrian field. These two short
## ribbons are not routes and carry no rails; their editor-owned Path3Ds define
## the visible forecourts while this helper derives only planks and collision.
func _rebuild_public_aprons() -> void:
	var sources := get_node_or_null("public_aprons")
	var derived := get_node_or_null("derived_aprons") as Node3D
	if sources == null or derived == null:
		return
	for child in derived.get_children():
		child.free()
	for child in sources.get_children():
		var apron := child as Path3D
		if apron == null or apron.curve == null or apron.curve.point_count < 2:
			continue
		var a := apron.curve.get_point_position(0)
		var b := apron.curve.get_point_position(apron.curve.point_count - 1)
		a.y = DECK_TOP - 0.004
		b.y = DECK_TOP - 0.004
		var direction := Vector3(b.x - a.x, 0.0, b.z - a.z).normalized()
		var side := Vector3(-direction.z, 0.0, direction.x) \
			* float(apron.get_meta("width", route_width)) * 0.5
		var left_a := a + side
		var right_a := a - side
		var left_b := b + side
		var right_b := b - side
		var width := side.length() * 2.0
		var run := a.distance_to(b)
		var surface := SurfaceTool.new()
		surface.begin(Mesh.PRIMITIVE_TRIANGLES)
		# Godot treats clockwise faces as front-facing. The apron rectangle is
		# authored west-to-east, so its top face needs the opposite winding from
		# the main shoreline course; the former order produced collision but was
		# culled when viewed from above.
		_add_triangle_uv(surface, right_a, left_b, left_a,
			Vector2(0.0, 0.0), Vector2(width * 0.44642857, run * 0.44642857),
			Vector2(width * 0.44642857, 0.0))
		_add_triangle_uv(surface, right_a, right_b, left_b,
			Vector2(0.0, 0.0), Vector2(0.0, run * 0.44642857),
			Vector2(width * 0.44642857, run * 0.44642857))
		surface.generate_tangents()
		var mesh := surface.commit()
		var deck := MeshInstance3D.new()
		deck.name = "%s_wearing_surface" % apron.name
		deck.mesh = mesh
		deck.material_override = deck_material
		deck.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		derived.add_child(deck)
		var body := StaticBody3D.new()
		body.name = "%s_walking_surface" % apron.name
		var collision := CollisionShape3D.new()
		var shape := mesh.create_trimesh_shape() as ConcavePolygonShape3D
		shape.backface_collision = true
		collision.shape = shape
		body.add_child(collision)
		derived.add_child(body)


func _add_triangle_uv(surface: SurfaceTool, a: Vector3, b: Vector3, c: Vector3,
		uv_a: Vector2, uv_b: Vector2, uv_c: Vector2) -> void:
	surface.set_normal(Vector3.UP)
	surface.set_uv(uv_a)
	surface.add_vertex(a)
	surface.set_normal(Vector3.UP)
	surface.set_uv(uv_b)
	surface.add_vertex(b)
	surface.set_normal(Vector3.UP)
	surface.set_uv(uv_c)
	surface.add_vertex(c)


func _beam(parent: Node3D, node_name: String, a: Vector3, b: Vector3,
		size: Vector3, material: Material, collide: bool) -> void:
	var delta := b - a
	if delta.length_squared() < 0.0001:
		return
	var up := Vector3.UP if absf(delta.normalized().dot(Vector3.UP)) < 0.97 \
		else Vector3.FORWARD
	var basis := Basis.looking_at(delta.normalized(), up)
	var dimensions := Vector3(size.x, size.y, delta.length())
	var mesh := BoxMesh.new()
	mesh.size = dimensions
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.material_override = material
	instance.transform = Transform3D(basis, (a + b) * 0.5)
	parent.add_child(instance)
	if not collide:
		return
	var body := StaticBody3D.new()
	body.name = "%s_guard" % node_name
	body.transform = instance.transform
	var shape := BoxShape3D.new()
	shape.size = dimensions
	var collision := CollisionShape3D.new()
	collision.shape = shape
	body.add_child(collision)
	parent.add_child(body)
