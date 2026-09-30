@tool
extends Node3D

## The boxwood hedge kit (landscape kit, 2026-09-29): her "lets make some boxy
## hedges so we can make shapes like this", with a photograph of a boxwood
## knot garden, then "this will be the standard height but lets also have
## waist height and a taller than people version one for privacy". The shapes
## are assets/source/props/boxwood_hedge.blend, built by
## tools/blender/hedge_kit.py; Send to game writes every piece of every height
## into assets/props/boxwood_hedge.glb. Only the lid wears a hem of leaves (her
## "the tiers ... create their own horizontal line. can we put it only on the
## very top of the hedges like a lid?"); clumps of leaf sprigs break up the
## sides (her "then add random clusters of leaves").
##
## Lay a hedge out with the editor's one-metre snap and quarter turns: each
## piece's origin is the middle of its first grid cell and the hedge runs along
## the cells' middles, so pieces meet open end to open end. Finish a run with an
## `end`, or its open end shows.

## Standard is knee high (0.5 m, her photograph's parterre); waist 1 m;
## privacy 2.2 m, taller than a person.
@export_enum("standard", "waist", "privacy") var height := 0:
	set(value):
		height = clampi(value, 0, HEIGHTS.size() - 1)
		_build()

## Which piece: one, two or four metres straight, west to east; a square
## corner, west to north; a tee, west to east with a branch north; a cross; an
## end, from the west; a post on its own; a bend, a rounded corner in one cell;
## a curve over two cells by two (four make a ring 3 m across) and a large one
## over three by three (four make a ring 5 m across).
@export_enum("straight", "straight_2", "straight_4", "corner", "tee", "cross", "end", "post", "bend", "curve",
		"curve_large") var piece := 0:
	set(value):
		piece = clampi(value, 0, PIECES.size() - 1)
		_build()

## Which of the piece's three scatterings of leaf clusters it wears. By grid
## square, the default, picks one from where it stands, so neighbouring pieces
## differ and a long hedge doesn't repeat every metre; a, b or c chooses.
@export_enum("by grid square", "a", "b", "c") var leaf_clusters := 0:
	set(value):
		leaf_clusters = clampi(value, 0, SETS.size())
		_build()

const HEIGHTS := ["standard", "waist", "privacy"]
const PIECES := ["straight", "straight_2", "straight_4", "corner", "tee", "cross", "end", "post", "bend", "curve",
		"curve_large"]
const MODEL := preload("res://assets/props/boxwood_hedge.glb")
const PREFIX := "boxwood_hedge_"
const SETS := ["a", "b", "c"]
## Each piece's body, lid, cluster scatterings and collision shape, taken once
## from one instance of the model and shared by every placement, so a
## placement is its one piece and not the whole kit hidden but one.
static var _parts := {}
## Each piece and scattering as one mesh (body, lid and clusters share the one
## material), so a placement is one draw.
static var _visuals := {}

var _shown: Array[Node] = []
var _shown_set := ""


func _ready() -> void:
	# In the editor, a piece dragged to another square takes that square's
	# scattering.
	set_notify_transform(Engine.is_editor_hint())
	_build()


func _notification(what: int) -> void:
	if what == NOTIFICATION_TRANSFORM_CHANGED and leaf_clusters == 0 and _cluster_set() != _shown_set:
		_build()


func _cluster_set() -> String:
	if leaf_clusters > 0:
		return SETS[leaf_clusters - 1]
	# The same rule as the Blender sample garden (hedge_kit.py, `cluster_set`).
	var cell := Vector2i(roundi(global_position.x), roundi(global_position.z))
	return SETS[posmod(cell.x * 7 + cell.y * 13, SETS.size())]


func _build() -> void:
	if not is_inside_tree():
		return  # a loading scene sets these before it is in the tree; _ready builds
	for node in _shown:
		node.free()
	_shown.clear()
	var key := "%s_%s" % [HEIGHTS[height], PIECES[piece]]
	var part := _part(key)
	if part.is_empty():
		push_warning("boxwood_hedge: %s is not in the model" % key)
		return
	_shown_set = _cluster_set()
	var leaves := MeshInstance3D.new()
	leaves.name = "leaves"
	leaves.mesh = _visual(key, _shown_set)
	var solid := StaticBody3D.new()
	solid.name = "collision"
	var shape := CollisionShape3D.new()
	shape.shape = part.get("shape")
	solid.add_child(shape)
	# Made again from the model on every load and never saved in a scene. In
	# the editor they are internal, so duplicating a hedge doesn't copy them;
	# in the game they are ordinary children, so StaticMerge can fold a
	# garden of hedges into one mesh.
	var mode := Node.INTERNAL_MODE_BACK if Engine.is_editor_hint() else Node.INTERNAL_MODE_DISABLED
	for node: Node in [leaves, solid]:
		add_child(node, false, mode)
		_shown.append(node)


static func _part(key: String) -> Dictionary:
	if _parts.is_empty():
		var model := MODEL.instantiate()
		for found in model.find_children("*", "MeshInstance3D", true, false):
			var mesh := found as MeshInstance3D
			var part_name := String(mesh.name).trim_prefix(PREFIX)
			if part_name.contains("_clusters_"):
				var entry: Dictionary = _parts.get_or_add(part_name.get_slice("_clusters_", 0), {})
				entry.get_or_add("clusters", {})[part_name.get_slice("_clusters_", 1)] = mesh.mesh
			elif part_name.ends_with("_hat"):
				_parts.get_or_add(part_name.trim_suffix("_hat"), {})["hat"] = mesh.mesh
			else:
				var entry: Dictionary = _parts.get_or_add(part_name, {})
				entry["body"] = mesh.mesh
				for shape in mesh.find_children("*", "CollisionShape3D", true, false):
					entry["shape"] = (shape as CollisionShape3D).shape
		model.free()
	return _parts.get(key, {})


static func _visual(key: String, set_name: String) -> Mesh:
	var id := "%s:%s" % [key, set_name]
	if not _visuals.has(id):
		var part := _part(key)
		var tool := SurfaceTool.new()
		tool.begin(Mesh.PRIMITIVE_TRIANGLES)
		var material: Material = null
		for mesh: Mesh in [part.get("body"), part.get("hat"), part.get("clusters", {}).get(set_name)]:
			if mesh == null:
				continue
			for surface in mesh.get_surface_count():
				tool.append_from(mesh, surface, Transform3D.IDENTITY)
				if material == null:
					material = mesh.surface_get_material(surface)
		tool.set_material(material)
		_visuals[id] = tool.commit()
	return _visuals[id]
