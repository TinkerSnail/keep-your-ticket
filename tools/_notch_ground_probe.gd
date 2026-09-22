extends Node

## Dev probe: what ground stands in the north massif's highway notch?
##
##     godot --headless --path . tools/run.tscn -- _notch_ground_probe
##
## The editor-owned north massif is cut down to a 20m plateau where the
## highway's tunnel 1 and the open stretch to tunnel 2 cross it, so the ground
## a player sees there is the generator's own terrain and the road. Before a
## ridge is put back over the tunnel, this drops a ray on a 20m grid across
## the notch and along tunnel 1's centreline and prints, for each point, the
## first collision under it and which node owns it, in Godot coordinates. It
## reads the persistent world and changes nothing.

const WORLD := "res://scenes/world/park_world.tscn"
const WORLD_LAYER := 1
const RAY_TOP := 600.0
const GRID := 20.0
const X_MIN := -560.0
const X_MAX := -40.0
const Z_MIN := -1660.0
const Z_MAX := -900.0
## Tunnel 1's portals, Godot plan coordinates, from the generated approach scene.
const PORTAL_A := Vector2(-390.8, -1602.5)
const PORTAL_B := Vector2(-259.4, -1164.6)


func _ready() -> void:
	add_child((load(WORLD) as PackedScene).instantiate())
	for i in 20:
		await get_tree().physics_frame
	var space := get_viewport().get_world_3d().direct_space_state
	print("NOTCH_GRID_BEGIN x z y owner")
	var x := X_MIN
	while x <= X_MAX + 0.01:
		var z := Z_MIN
		while z <= Z_MAX + 0.01:
			_report(space, Vector2(x, z))
			z += GRID
		x += GRID
	print("NOTCH_GRID_END")
	print("TUNNEL1_BEGIN t x z y owner")
	for k in 23:
		var t := float(k) / 22.0
		var p := PORTAL_A.lerp(PORTAL_B, t)
		_report(space, p, "%.3f " % t)
	print("TUNNEL1_END")
	get_tree().quit(0)


func _report(space: PhysicsDirectSpaceState3D, p: Vector2, prefix := "") -> void:
	var query := PhysicsRayQueryParameters3D.create(Vector3(p.x, RAY_TOP, p.y),
		Vector3(p.x, -60.0, p.y), WORLD_LAYER)
	var hit := space.intersect_ray(query)
	if hit.is_empty():
		print("%s%.1f %.1f none none" % [prefix, p.x, p.y])
		return
	var owner := hit["collider"] as Node
	var label := owner.name
	var up := owner.get_parent()
	while up != null and up != self and label.length() < 90:
		label = up.name + "/" + label
		up = up.get_parent()
	print("%s%.1f %.1f %.2f %s" % [prefix, p.x, p.y, hit["position"].y, label])
