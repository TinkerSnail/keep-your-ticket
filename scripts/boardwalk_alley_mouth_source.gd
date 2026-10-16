extends RefCounted

## Reader for the Boardwalk alley mouth's two festoon frames, editor-owned since
## 2026-10-16 (Christina: move the mouth's placement to a scene she can drag,
## then set the lane end's posts back toward the facade). Their placement is the
## Marker3Ds saved in `scenes/world/boardwalk_alley_mouth.tscn`, in literal
## Godot world metres; this turns them into the records the generator builds the
## frames from (`_alley_mouth` in `tools/gen_props.gd`) and never writes the
## scene. It names no autoload, so a `--script` run may preload it.
##
## One record per end of the alley, keyed by its node name (`lane`, the Grand
## Circuit's side; `strip`, the promenade's): `posts`, each post's foot, the
## post rising `post_size.y` from it; `valance`, the two ends of the valance's
## centreline at its own level, `valance_size` its depth across that line and
## its thickness; `bulbs`, the first and last bulb's centres, `bulb_count` bulbs
## evenly from one to the other at `bulb_radius`. The beam, corbels and sign are
## the facade's and the gap's, from the plan, and stay the generator's.

const SCENE := "res://scenes/world/boardwalk_alley_mouth.tscn"


static func read() -> Dictionary:
	var packed := load(SCENE) as PackedScene
	assert(packed != null, "the alley mouth's editor source %s is missing" % SCENE)
	var root := packed.instantiate() as Node3D
	assert(root != null, "the alley mouth's editor source is not a Node3D")
	var out := records(root)
	root.free()
	return out


static func records(root: Node3D) -> Dictionary:
	assert(root.get_meta("coordinate_space", "") == &"godot_world_metres",
		"the alley mouth's editor source must stay in literal Godot world metres")
	var out := {}
	for end in root.get_children():
		if not (end is Node3D and end.has_meta("post_size")):
			continue
		var valance := end.get_node("valance") as Node3D
		var bulbs := end.get_node("bulbs") as Node3D
		assert(valance != null and bulbs != null,
			"alley end %s needs its valance and bulbs" % end.name)
		var count := int(bulbs.get_meta("count"))
		assert(count >= 1, "alley end %s has no bulbs" % end.name)
		out[StringName(end.name)] = {
			"posts": [_position(end.get_node("post_0"), root),
				_position(end.get_node("post_1"), root)],
			"post_size": Vector3(end.get_meta("post_size")),
			"valance": [_position(valance.get_node("from"), root),
				_position(valance.get_node("to"), root)],
			"valance_size": Vector2(float(valance.get_meta("depth")),
				float(valance.get_meta("thickness"))),
			"bulbs": [_position(bulbs.get_node("first"), root),
				_position(bulbs.get_node("last"), root)],
			"bulb_count": count,
			"bulb_radius": float(bulbs.get_meta("radius")),
		}
	return out


## A marker's position in the root's space, through every Node3D between, so an
## end or a valance moved or turned in the editor carries its markers with it.
static func _position(marker: Node, root: Node3D) -> Vector3:
	assert(marker is Node3D, "an alley marker is missing")
	var xf := (marker as Node3D).transform
	var parent := marker.get_parent()
	while parent is Node3D and parent != root:
		xf = (parent as Node3D).transform * xf
		parent = parent.get_parent()
	assert(parent == root, "%s is not inside the alley mouth's source" % marker.name)
	return xf.origin
