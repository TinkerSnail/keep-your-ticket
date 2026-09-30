@tool
extends Node3D

## PRP-PLANT-049, the California coast live oak (2026-09-29, her "replace our
## live oaks with a new model in our signature cartoony style. using the
## spherical shrubs we made, create a simplified version of a mature oak").
## Its shape is assets/source/props/coastal_live_oak.blend, built by
## tools/blender/leaf_skin.py: the sphere shrubs' hats stacked in tiers, each
## held by its own branch. Send to game writes assets/props/coastal_live_oak.glb
## and the season canvases beside it. The Path3D oak this replaced is in git at
## 240d30f.

## Which of the model's oaks this is (her "we need to randomize the branches
## and stuff"): each is its own meshes, `coastal_live_oak_<variant>...`, with
## its own hats, branches, lean and acorns; the others are hidden and don't
## collide.
@export_enum("a", "b", "c") var variant := 0:
	set(value):
		variant = clampi(value, 0, VARIANTS.size() - 1)
		_show()

## The park's chapter (documentation/seasonal-missions-and-decor.md), as on
## the shrubs: spring, its buds on the spring canvas; summer, its green acorns
## on the model's own canvas; harvest, brown acorns and a few acorns and
## leaves on the ground on the fall canvas; winter, a few brown acorns on the
## winter canvas, a sixth of the leaves see-through. A season system can call
## `set_season` on the `seasonal_planting` group. It starts in High Summer,
## where the campaign opens (her "lets do summer and have the campaign start
## there").
@export_enum("spring", "summer", "harvest", "winter") var season := 1:
	set(value):
		season = clampi(value, 0, 3)
		_show()

const PREFIX := "coastal_live_oak_"
const VARIANTS := ["a", "b", "c"]
## Each chapter's merge groups (leaf_skin.py, `place_acorns`, `place_ground`).
const GROUPS := [["spring_buds"], ["summer_acorns"], ["fall_acorns", "fall_ground"], ["winter_acorns"]]
## The leaves' material, and each chapter's canvas for it (summer's is in
## the model).
const LEAF := "coastal_live_oak"
const CANVASES := [
	preload("res://assets/props/coastal_live_oak_colour_spring.png"),
	null,
	preload("res://assets/props/coastal_live_oak_colour_fall.png"),
	preload("res://assets/props/coastal_live_oak_colour_winter.png"),
]
static var _shared := {}


func _ready() -> void:
	add_to_group("seasonal_planting")
	_show()


func set_season(chapter: int) -> void:
	season = chapter


func _show() -> void:
	for found in find_children("*", "MeshInstance3D", true, false):
		var mesh := found as MeshInstance3D
		var part := String(mesh.name)
		if not part.begins_with(PREFIX):
			continue
		var rest := part.trim_prefix(PREFIX)
		var mine: bool = rest.get_slice("_", 0) == VARIANTS[variant]
		var group := rest.substr(2) if rest.length() > 2 else ""
		var shown := mine
		if group != "" and group != "visual":
			shown = shown and GROUPS[season].has(group)
		mesh.visible = shown
		for shape in mesh.find_children("*", "CollisionShape3D", true, false):
			(shape as CollisionShape3D).disabled = not mine
		_paint(mesh)


## The chapter's canvas on the leaves; every placement in one chapter shares
## its material, so they still draw together.
func _paint(mesh: MeshInstance3D) -> void:
	if mesh.mesh == null:
		return
	for surface in mesh.mesh.get_surface_count():
		var material := mesh.mesh.surface_get_material(surface) as StandardMaterial3D
		if material == null or material.resource_name != LEAF:
			continue
		if CANVASES[season] == null:
			mesh.set_surface_override_material(surface, null)
			continue
		if not _shared.has(season):
			var worn := material.duplicate() as StandardMaterial3D
			worn.albedo_texture = CANVASES[season]
			_shared[season] = worn
		mesh.set_surface_override_material(surface, _shared[season])
