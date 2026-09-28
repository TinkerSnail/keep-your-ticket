@tool
extends EditorScenePostImport

## Import script for a model sent from Blender part by part (`kyt_keep_parts`):
## applies what a part's custom properties say that glTF cannot carry. A GLB
## names it in its import settings (`import_script/path`); the plaza fountain
## was the first, on 2026-09-27.
##
## - `kyt_shadow = "off"`: the part casts no shadow. Godot draws a translucent
##   part into the shadow map as if it were solid, so a veil of water would lay
##   a black ring on the pool it falls into and the plume a bar across the
##   plaza. `gen_props.gd` said so per node while it built the fountain; the
##   property says it per part now, and duplicating a part in Blender copies it.
##
## Send writes a part's custom properties as glTF extras, and Godot's importer
## keeps them as the node's `extras` metadata, which is where this reads them.


func _post_import(scene: Node) -> Object:
	var off := 0
	for n in scene.find_children("*", "GeometryInstance3D", true, false):
		var extras = n.get_meta("extras", null)
		if extras is Dictionary and str(extras.get("kyt_shadow", "")).to_lower() == "off":
			(n as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			off += 1
	print("kyt_part_import: %s: %d parts cast no shadow" % [get_source_file(), off])
	return scene
