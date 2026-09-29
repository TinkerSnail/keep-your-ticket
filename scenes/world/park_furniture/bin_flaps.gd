extends Node3D

## The riveted bin's push flaps, working (Christina, 2026-09-27: "can the flap
## on the riveted bin function", then all three: the player pushes it, guests
## throw trash in, and the overflowing state holds it open).
##
## The model sends each flap as its own node, `flap_front` and `flap_back`,
## with its origin on its hinge, the flap's top edge (`kyt_hinge` on the part;
## Send splits it off). A push swings a flap in, into the bin's hollow shell,
## opening onto the inner can and its liner, and it falls back, bouncing a
## little off its frame. A flap never swings past `MAX_SWING_DEG`, which keeps
## the two apart when both are in.
##
## - The player pushes by walking into a flap, or with `interact` while looking
##   at one within reach (`try_push`, asked by `interact_tool.gd` before it
##   asks a guest).
## - A guest passing close in front now and then swings it, as if pushing
##   something through. This lives here, in the bin: the guest doesn't stop or
##   reach yet, which wants a guest errand once bins stand in the park.
## - `wedged_open_deg` is where the flaps rest: 0 shut; the overflowing state
##   sets it, trash holding them part-way open.

const MAX_SWING_DEG := 40.0

## How far a firm push swings a flap in.
@export_range(0.0, 40.0) var swing_deg := 34.0
## Where the flaps rest. The overflowing state wedges them open with this.
@export_range(0.0, 40.0) var wedged_open_deg := 0.0
## The spring back to rest, and how quickly the swing dies.
@export var stiffness := 38.0
@export var damping := 4.5
## A guest this close in front of a flap may push something through...
@export var guest_reach := 1.1
## ...once in this many seconds, per flap, while one is that close.
@export var guest_every := Vector2(20.0, 60.0)
## How close the player must be to push a flap with `interact`, and how far
## off the view's centre it may be.
@export var push_reach := 1.5
@export var push_cone_deg := 35.0

## One flap: its node, which way is in (+1 swings about +x, the front flap;
## -1 the back), its angle and speed in degrees, and the next time a guest may
## push it.
class Flap:
	var node: Node3D
	var sign := 1.0
	var rest := Basis.IDENTITY
	var angle := 0.0
	var speed := 0.0
	var next_guest := 0.0

var _flaps: Array[Flap] = []
var _clock := 0.0
var _guest_check := 0.0
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	add_to_group("bin_flaps")
	# Seeded by where the bin stands, so every bin keeps its own rhythm.
	_rng.seed = hash(Vector3i(global_position.round()))
	var model := get_parent().get_node_or_null("model")
	if model == null:
		return
	for pair in [["flap_front", 1.0], ["flap_back", -1.0]]:
		var node := model.find_child(pair[0], true, false) as Node3D
		if node == null:
			continue
		var flap := Flap.new()
		flap.node = node
		flap.sign = pair[1]
		flap.rest = node.basis
		flap.angle = wedged_open_deg
		flap.next_guest = _rng.randf_range(guest_every.x, guest_every.y)
		_flaps.append(flap)
		_add_bumper(flap)


## An area just outside the flap: the player walking into it pushes it.
func _add_bumper(flap: Flap) -> void:
	var area := Area3D.new()
	area.name = "%s_bumper" % flap.node.name
	area.collision_layer = 0
	area.collision_mask = 2  # the player
	area.monitorable = false
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(0.46, 0.40, 0.30)
	shape.shape = box
	area.add_child(shape)
	add_child(area)
	# Out from the flap's face, level with its middle; outside is +z for the
	# front flap and -z for the back one, in the bin's frame.
	var hinge := to_local(flap.node.global_position)
	area.position = hinge + Vector3(0.0, -0.18, 0.15 * flap.sign)
	area.body_entered.connect(func(body: Node) -> void:
		if body.is_in_group("player"):
			push(flap, 1.0))


func push(flap: Flap, strength := 1.0) -> void:
	# The kick of speed whose first swing peaks at `swing_deg` (times
	# `strength`) through the damping: a damped spring kicked at speed v peaks
	# at v / w * exp(-z w t), t the time of the peak.
	var w := sqrt(stiffness)
	var z := damping / (2.0 * w)
	var gain := 1.0
	if z < 1.0:
		var wd := w * sqrt(1.0 - z * z)
		gain = exp(z * w * atan(sqrt(1.0 - z * z) / z) / wd)
	flap.speed = max(flap.speed, swing_deg * w * gain * strength)


## Asked by the player's interact tool before it asks a guest: pushes the flap
## nearest the centre of the view within reach, on the side it is seen from.
## Returns whether it pushed one.
func try_push(from: Vector3, forward: Vector3) -> bool:
	var best: Flap = null
	var best_cos := cos(deg_to_rad(push_cone_deg))
	for flap in _flaps:
		var middle := flap.node.global_position + global_basis.y * -0.18
		var to := middle - from
		to.y = 0.0
		if to.length() > push_reach or to.length() < 0.01:
			continue
		# Only from outside: the flap's outward side faces the player.
		var outward := global_basis.z * flap.sign
		if outward.dot(from - middle) <= 0.0:
			continue
		var c := forward.normalized().dot(to.normalized())
		if c > best_cos:
			best_cos = c
			best = flap
	if best == null:
		return false
	push(best, 1.0)
	return true


func _physics_process(delta: float) -> void:
	_clock += delta
	_guest_check -= delta
	if _guest_check <= 0.0:
		_guest_check = 0.5
		_guests_passing()
	for flap in _flaps:
		var rest := wedged_open_deg
		var accel := -stiffness * (flap.angle - rest) - damping * flap.speed
		flap.speed += accel * delta
		flap.angle += flap.speed * delta
		# Shut against its frame: it bounces back a little.
		if flap.angle < 0.0:
			flap.angle = 0.0
			flap.speed = -flap.speed * 0.35
		elif flap.angle > MAX_SWING_DEG:
			flap.angle = MAX_SWING_DEG
			flap.speed = min(flap.speed, 0.0)
		flap.node.basis = flap.rest * Basis(Vector3.RIGHT, deg_to_rad(flap.angle * flap.sign))


## A guest close in front of a flap, now and then, pushes something through.
func _guests_passing() -> void:
	if _flaps.is_empty():
		return
	var guests := get_tree().get_nodes_in_group("guest")
	for flap in _flaps:
		if _clock < flap.next_guest:
			continue
		var middle := flap.node.global_position
		var outward := global_basis.z * flap.sign
		for guest in guests:
			var g := guest as Node3D
			if g == null or not g.visible:
				continue
			var off := g.global_position - middle
			off.y = 0.0
			if off.length() < guest_reach and outward.dot(off) > 0.1:
				push(flap, _rng.randf_range(0.6, 1.0))
				flap.next_guest = _clock + _rng.randf_range(guest_every.x, guest_every.y)
				break
