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
			ParkSections.enter(leads_to, belongs_to)
