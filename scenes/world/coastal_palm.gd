@tool
extends Node3D

## One coastal palm, placed by its foot: trunk, crown and planting bed. Move the
## palm to move its foot; every other choice is a value here in the inspector.
## The trunk runs from the foot to the crown seat, `height` up and `lean` across,
## and bows the way `trunk_turn` points it. The crown sits on the seat, turned by
## `crown_turn`; `variation_seed` decides which fronds it shows and how each is
## tipped (see `palm_crown.gd`). The parts are built here, for the editor and the
## game alike, and are not saved: the values are.
##
## The values of the 34 coastal palms were taken on 2026-09-25 from what
## `coastal_palm_replacements.gd` (since retired; in git at `58c9ca8`) built
## at each generated foot, by
## `tools/_palm_placement_migration.gd`, which checked that every trunk, crown
## seat and bed landed where it had been.

const StaticMerge := preload("res://scripts/static_merge.gd")

@export var variation_seed := 0:
	set(value):
		variation_seed = value
		_queue_rebuild()

@export_group("Trunk")
@export var trunk_scene: PackedScene:
	set(value):
		trunk_scene = value
		_queue_rebuild()
## The crown seat's height above the foot, in metres.
@export_range(2.0, 16.0, 0.01, "or_greater") var height := 8.5:
	set(value):
		height = value
		_queue_rebuild()
## How far the crown seat sits off the foot: x and z, in metres.
@export var lean := Vector2.ZERO:
	set(value):
		lean = value
		_queue_rebuild()
## Turns the trunk about its own line, which turns the way its bow faces.
@export_range(-360.0, 360.0, 0.1, "degrees") var trunk_turn := 0.0:
	set(value):
		trunk_turn = value
		_queue_rebuild()
@export_range(0.25, 1.35, 0.01) var bend_strength := 1.0:
	set(value):
		bend_strength = value
		_queue_rebuild()

@export_group("Crown")
@export var crown_scene: PackedScene:
	set(value):
		crown_scene = value
		_queue_rebuild()
@export_range(-360.0, 360.0, 0.1, "degrees") var crown_turn := 0.0:
	set(value):
		crown_turn = value
		_queue_rebuild()
@export_range(12, 32, 1) var frond_count := 12:
	set(value):
		frond_count = value
		_queue_rebuild()
@export_range(0, 12, 1) var stub_count := 9:
	set(value):
		stub_count = value
		_queue_rebuild()
@export_range(0, 3, 1) var dead_count := 0:
	set(value):
		dead_count = value
		_queue_rebuild()

@export_group("Planting")
@export var footing_scene: PackedScene:
	set(value):
		footing_scene = value
		_queue_rebuild()
@export_range(-360.0, 360.0, 0.1, "degrees") var footing_turn := 0.0:
	set(value):
		footing_turn = value
		_queue_rebuild()
## The arrival and front-road palms' Hakone and Purple Heart rings; empty for none.
@export var accent_rings_scene: PackedScene:
	set(value):
		accent_rings_scene = value
		_queue_rebuild()

var _queued := false


func _ready() -> void:
	_queue_rebuild()


func _queue_rebuild() -> void:
	if _queued or not is_inside_tree():
		return
	_queued = true
	call_deferred("_rebuild")


## The crown seat in the palm's own frame.
func seat() -> Vector3:
	return Vector3(lean.x, height, lean.y)


func _rebuild() -> void:
	_queued = false
	for part_name in ["trunk", "crown", "footing"]:
		var old := get_node_or_null(part_name)
		if old != null:
			remove_child(old)
			old.free()
	var top := seat()

	if trunk_scene != null:
		var trunk := trunk_scene.instantiate() as Node3D
		trunk.name = "trunk"
		trunk.set("bend_strength", bend_strength)
		add_child(trunk)
		trunk.quaternion = Quaternion(Vector3.UP, top.normalized())
		trunk.rotate_object_local(Vector3.UP, deg_to_rad(trunk_turn))
		# The trunk source is one metre long and scales whole to the seat.
		trunk.scale = Vector3.ONE * top.length()

	if footing_scene != null:
		var footing := footing_scene.instantiate() as Node3D
		footing.name = "footing"
		add_child(footing)
		footing.rotation.y = deg_to_rad(footing_turn)
		if accent_rings_scene != null:
			var rings := accent_rings_scene.instantiate() as Node3D
			rings.name = "arrival_accent_rings"
			footing.add_child(rings)
			# The rings carry how much the bed's centre and ferns grow above them.
			var flowers := footing.get_node_or_null("flowers") as Node3D
			var height_scale := float(rings.get_meta("center_height_scale", 1.0))
			if flowers != null:
				flowers.scale.y = height_scale
				flowers.set_meta("arrival_height_scale", height_scale)
			var ferns := footing.get_node_or_null("fern_pockets") as Node3D
			var fern_scale := float(rings.get_meta("fern_scale", 1.0))
			if ferns != null:
				for fern in ferns.get_children():
					(fern as Node3D).scale *= fern_scale
				ferns.set_meta("arrival_fern_scale", fern_scale)

	if crown_scene != null:
		var crown := crown_scene.instantiate() as Node3D
		crown.name = "crown"
		crown.set("variation_seed", variation_seed)
		crown.set("frond_count", frond_count)
		crown.set("stub_count", stub_count)
		crown.set("dead_count", dead_count)
		add_child(crown)
		crown.position = top
		crown.rotation.y = deg_to_rad(crown_turn)

	# In the running game only: the crown and the bed each draw as one mesh.
	StaticMerge.merge_children_later(self, [self])
