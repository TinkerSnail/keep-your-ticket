@tool
extends Area3D

## A place in the world where a section is loaded, or where one is crossed into.
##
## These come in pairs and the pair is the whole design. The first sits at the
## mouth of the corridor and only starts the load; the second sits at the seam,
## past the bend, and does the swap. The distance between them is how long the
## player spends walking, which is the budget the load gets — and it is why the
## corridor bends rather than running straight. `documentation/design.md` wants
## the bend for the reveal; the load wants it so that nothing pops where the
## player can see it happen.
##
## A gate to a section that is not built does nothing. Four of the plaza's six
## ways out are passages that bend and stop, and walking to the end of one has
## to be an anticlimax rather than a crash.

enum Role {
	## The mouth of the corridor. Starts pulling the section off disk and
	## nothing else. Crossing it back out is free and costs only the load
	## already done.
	PRELOAD,
	## The seam itself. The player crosses and is standing somewhere else.
	CROSS,
}

@export var role: Role = Role.PRELOAD

## Which section is on the other side.
@export var leads_to: StringName = &""

## Which section this gate is standing in. Told rather than asked, because at
## the moment the seam fires the answer is about to change and a gate that
## looked it up would report where the player is going instead of where they
## have been. This is what decides where they are put down coming back.
@export var belongs_to: StringName = &"plaza"

## The held shot, for a `CROSS` gate that wants one.
##
## With `hold_seconds` at zero the crossing is the old one: hand the walk over
## and fade. Above zero the camera cuts to `hold_from` looking at `hold_look`,
## the player walks `hold_walk` for that long, and only then does the screen go —
## so the swap happens with the player already out of frame.
##
## The pose is authored per seam rather than derived from the gate's transform,
## because a good one depends on what is behind the threshold as much as on the
## threshold: the arch wants to be seen three-quarter on from inside the plaza,
## and no rule about the volume's axes would have found that.
@export var hold_seconds: float = 0.0
@export var hold_from: Vector3 = Vector3.ZERO
@export var hold_look: Vector3 = Vector3.ZERO
## Which way the player is sent while the shot holds. Zero means "carry on the
## way you were already going", which is what a seam with no framing does.
@export var hold_walk: Vector3 = Vector3.ZERO


func _ready() -> void:
	if Engine.is_editor_hint():
		return
	if leads_to == &"":
		push_warning("section_gate: '%s' leads nowhere" % name)
		return
	body_entered.connect(_on_body_entered)


## By group rather than by collision mask. The player's layers are the player's
## business and have already changed once; what this needs to know is only
## whether the thing that walked in is the person playing.
func _on_body_entered(body: Node3D) -> void:
	if not body.is_in_group("player"):
		return
	if not ParkSections.is_built(leads_to):
		return

	match role:
		Role.PRELOAD:
			ParkSections.begin_preload(leads_to)
		Role.CROSS:
			var hold := {}
			if hold_seconds > 0.0:
				hold = {
					"seconds": hold_seconds,
					"from": hold_from,
					"look": hold_look,
					"walk": hold_walk,
				}
			ParkSections.enter(leads_to, belongs_to, hold)
