@tool
extends Node3D

## The hardscape kit (landscape kit, 2026-09-30): her "time for fences and
## little retaining walls and curbs", with a photograph of a brick front-garden
## wall and its railing on a sidewalk. The shapes are
## assets/source/props/hardscape_kit.blend, built by
## tools/blender/hardscape_kit.py; Send to game writes every piece of every
## kind into assets/props/hardscape_kit.glb.
##
## Lay it out as the hedges are: the editor's one-metre snap and quarter turns.
## Each piece's origin is the middle of its first grid cell and the run goes
## along the cells' middles, so pieces meet open end to open end. Finish a run
## with an `end`, or its open end shows. A wall, its pier and its railing can
## be one placement (`pier`, `railing`), and so can the railing's post in the
## middle between two piers (`post`).

## Brick walls in the park (a little darker toward the ground) or in the
## beach town (sun, salt and history), or concrete; each at sitting height
## (coping 0.475 m) or her photograph's (0.70 m). The railing that stands on a
## wall's coping; the same railing as a fence on the ground; the street's curb
## and gutter, plain or painted red; a bed's edging curb.
@export_enum("wall_seat", "wall_garden", "town_wall_seat", "town_wall_garden", "concrete_wall_seat",
		"concrete_wall_garden", "railing_wall", "railing_fence", "curb_road", "curb_road_red", "curb_edging")
var kind := 1:
	set(value):
		kind = clampi(value, 0, KINDS.size() - 1)
		_build()

## Which piece: one, two or four metres straight, west to east; a square
## corner, west to north; a tee; a cross; an end, from the west; a bend, a
## curve and a large curve (radius 0.5, 1.5 and 2.5 m, as the hedges'). A wall
## also has a pier on its own; the wall railing a metre with posts either side
## of a pier, and a metre with a post in its middle; the fence a post. The road curb turns either way (`_in`: the road
## inside the turn) and has a driveway `cut`. A kind without the piece warns.
@export_enum("straight", "straight_2", "straight_4", "corner", "tee", "cross", "end", "bend", "curve",
		"curve_large", "pier", "post", "bend_in", "curve_in", "curve_large_in", "cut")
var piece := 0:
	set(value):
		piece = clampi(value, 0, PIECES.size() - 1)
		_build()

## A wall only: a pier over this piece's first cell.
@export var pier := false:
	set(value):
		pier = value
		_build()

## A wall only: the railing on its coping, the same piece; on a straight under
## a pier, the railing's metre with posts just off the pier's faces.
@export var railing := false:
	set(value):
		railing = value
		_build()

## A wall's railing only, on a straight without a pier: a post over this
## piece's first cell, as her photograph's in the middle between two piers.
## Lay the bay's middle cell as a one-metre straight to carry it.
@export var post := false:
	set(value):
		post = value
		_build()

## Which of the piece's three scatterings of bird droppings it wears (her
## "bird poop on the ledges", "and iron railings"). By grid square, the
## default, picks one from where it stands, so neighbours differ.
@export_enum("by grid square", "a", "b", "c", "none") var droppings := 0:
	set(value):
		droppings = clampi(value, 0, SETS.size() + 1)
		_build()

const KINDS := ["wall_seat", "wall_garden", "town_wall_seat", "town_wall_garden", "concrete_wall_seat",
		"concrete_wall_garden", "railing_wall", "railing_fence", "curb_road", "curb_road_red", "curb_edging"]
const PIECES := ["straight", "straight_2", "straight_4", "corner", "tee", "cross", "end", "bend", "curve",
		"curve_large", "pier", "post", "bend_in", "curve_in", "curve_large_in", "cut"]
## Each wall height's coping top at the face, where its railing stands
## (hardscape_kit.py, WALLS).
const COPING_TOPS := {"seat": 0.475, "garden": 0.70}
const MODEL := preload("res://assets/props/hardscape_kit.glb")
const PREFIX := "hardscape_kit_"
const SETS := ["a", "b", "c"]
## Each piece's body and its collision shape, what doesn't collide (pickets,
## curbs) and its droppings, taken once from one instance of the model and
## shared by every placement.
static var _parts := {}
## Each combination of layers and droppings as one mesh, so a placement is one
## draw.
static var _visuals := {}

var _shown: Array[Node] = []
var _shown_key := ""


func _ready() -> void:
	set_notify_transform(Engine.is_editor_hint())
	_build()


func _notification(what: int) -> void:
	# Moved in the editor: its droppings go by grid square.
	if what == NOTIFICATION_TRANSFORM_CHANGED and _key(_layers()) != _shown_key:
		_build()


func _key(layers: Array) -> String:
	return "%s:%s" % [str(layers), _drop_set()]


func _drop_set() -> String:
	if droppings == SETS.size() + 1:
		return ""
	if droppings > 0:
		return SETS[droppings - 1]
	# The same rule as the Blender sample street (hardscape_kit.py, `drop_set`).
	var cell := Vector2i(roundi(global_position.x), roundi(global_position.z))
	return SETS[posmod(cell.x * 7 + cell.y * 13, SETS.size())]


## What this placement shows: [part key, where it stands in the placement].
func _layers() -> Array:
	var kind_name: String = KINDS[kind]
	var piece_name: String = PIECES[piece]
	var key := "%s_%s" % [kind_name, piece_name]
	if _part(key).is_empty():
		return []
	var out := [[key, Transform3D.IDENTITY]]
	var size := kind_name.get_slice("_", kind_name.get_slice_count("_") - 1)
	if COPING_TOPS.has(size) and piece_name != "pier":
		if pier:
			out.append([kind_name + "_pier", Transform3D.IDENTITY])
		if railing:
			var rail := "railing_wall_" + piece_name
			if piece_name == "straight" and (pier or post):
				rail = "railing_wall_" + ("pier" if pier else "post")
			if not _part(rail).is_empty():
				out.append([rail, Transform3D(Basis.IDENTITY, Vector3(0.0, COPING_TOPS[size], 0.0))])
	return out


func _build() -> void:
	if not is_inside_tree():
		return  # a loading scene sets these before it is in the tree; _ready builds
	for node in _shown:
		node.free()
	_shown.clear()
	var layers := _layers()
	if layers.is_empty():
		push_warning("hardscape_kit: %s has no %s" % [KINDS[kind], PIECES[piece]])
		return
	_shown_key = _key(layers)
	var nodes: Array[Node] = []
	var mesh := MeshInstance3D.new()
	mesh.name = "hardscape"
	mesh.mesh = _visual(layers, _drop_set())
	nodes.append(mesh)
	var shapes := []
	for layer: Array in layers:
		var part := _part(layer[0])
		if part.get("shape") != null:
			shapes.append([part["shape"], layer[1]])
	if not shapes.is_empty():
		var solid := StaticBody3D.new()
		solid.name = "collision"
		for entry: Array in shapes:
			var shape := CollisionShape3D.new()
			shape.shape = entry[0]
			shape.transform = entry[1]
			solid.add_child(shape)
		nodes.append(solid)
	# Made again from the model on every load and never saved in a scene. In
	# the editor they are internal, so duplicating a placement doesn't copy
	# them; in the game they are ordinary children, so StaticMerge can fold a
	# run of them into one mesh.
	var mode := Node.INTERNAL_MODE_BACK if Engine.is_editor_hint() else Node.INTERNAL_MODE_DISABLED
	for node in nodes:
		add_child(node, false, mode)
		_shown.append(node)


static func _part(key: String) -> Dictionary:
	if _parts.is_empty():
		var model := MODEL.instantiate()
		for found in model.find_children("*", "MeshInstance3D", true, false):
			var mesh := found as MeshInstance3D
			var part_name := String(mesh.name).trim_prefix(PREFIX)
			if part_name.contains("_droppings_"):
				var entry: Dictionary = _parts.get_or_add(part_name.get_slice("_droppings_", 0), {})
				entry.get_or_add("droppings", {})[part_name.get_slice("_droppings_", 1)] = mesh.mesh
			elif part_name.ends_with("_visual"):
				_parts.get_or_add(part_name.trim_suffix("_visual"), {})["visual"] = mesh.mesh
			else:
				var entry: Dictionary = _parts.get_or_add(part_name, {})
				entry["body"] = mesh.mesh
				for shape in mesh.find_children("*", "CollisionShape3D", true, false):
					entry["shape"] = (shape as CollisionShape3D).shape
		model.free()
	return _parts.get(key, {})


static func _visual(layers: Array, set_name: String) -> Mesh:
	var id := "%s:%s" % [str(layers), set_name]
	if not _visuals.has(id):
		var tool := SurfaceTool.new()
		tool.begin(Mesh.PRIMITIVE_TRIANGLES)
		var material: Material = null
		for layer: Array in layers:
			var part := _part(layer[0])
			for mesh: Mesh in [part.get("body"), part.get("visual"), part.get("droppings", {}).get(set_name)]:
				if mesh == null:
					continue
				for surface in mesh.get_surface_count():
					tool.append_from(mesh, surface, layer[1])
					if material == null:
						material = mesh.surface_get_material(surface)
		tool.set_material(material)
		_visuals[id] = tool.commit()
	return _visuals[id]
