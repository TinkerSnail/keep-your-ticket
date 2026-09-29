@tool
extends Node3D

## Lemon Zest Hakone grass (PRP-PLANT-018 to 021). The clump's blades are shaped
## in assets/source/props/hakone_grass.blend: a mature and a young blade, each
## bent along each of 12 courses, broad, chubby and round-tipped since
## Christina's "more cartoony" and "fewer and larger blades" (2026-09-27). They
## arrive as two meshes, the 9 blades of the outer and mature courses and the 3
## young ones, which only vB shows. Until
## then this script built every blade from Path3D courses here; git holds that
## version.

@export_enum("vA", "vB") var catalog_variant := 0:
	set(value):
		catalog_variant = clampi(value, 0, 1)
		_show_variant()


func _ready() -> void:
	_show_variant()


## The young blades are hidden, not freed, for vA; StaticMerge leaves hidden
## meshes out of the running game's merged mesh. Found by the end of their
## name, so the purple Hakone (purple_hakone_grass.tscn, the same clump in the
## Purple Heart's colours) wears this script too.
func _show_variant() -> void:
	var model := get_node_or_null("model")
	if model == null:
		return
	for part in model.get_children():
		if part is Node3D and String(part.name).ends_with("_young"):
			(part as Node3D).visible = catalog_variant >= 1
