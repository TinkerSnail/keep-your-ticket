@tool
extends Node3D

## Hibiscus shrub (landscape kit, 2026-09-28). Its shape is
## assets/source/props/hibiscus_shrub.blend. Each flower is painted on one
## card (her "needs to be optimized for using textures"), each colourway
## painted side by side on the canvas (paint_canvas.py, PROP_LEAFLETS: red,
## pink, yellow-red, pink-white; her "for hibiscus we want yellow-red, red,
## and pink", "and pink white"), each a floor(width / 4) pixels right of the
## last. `bloom` slides this placement's `hibiscus_shrub_bloom` material there;
## every placement of one colourway shares it, so StaticMerge still draws them
## together.

@export_enum("red", "pink", "yellow-red", "pink-white") var bloom := 0:
	set(value):
		bloom = clampi(value, 0, SLOTS - 1)
		_paint()

const SLOTS := 4
## The park's chapter (documentation/seasonal-missions-and-decor.md). Her
## words: the flowers here are the baseline; "during the peak season for that
## flower the clusters should be increased three fold, and during winter we
## will treat these as evergreen shrubs". The model carries the baseline
## flowers and the peak's extra ones as their own meshes (`*_blooms`,
## `*_blooms_peak`); this shows the baseline outside Winter Lights and both in
## the peak chapter, High Summer. A season system can call `set_season`
## on the `seasonal_planting` group. It starts in High Summer, where the
## campaign opens (her "lets do summer and have the campaign start there").
@export_enum("spring", "summer", "harvest", "winter") var season := 1:
	set(value):
		season = clampi(value, 0, 3)
		_show_season()

## Her "can we also vary the size of the shrubs themselves, one smaller and
## one larger (flowers stay the same size)": the model carries each size as
## its own meshes (`<prop>_<size>`, `_<size>_blooms`, `_<size>_blooms_peak`);
## this shows one; a model without the chosen size shows its medium.
@export_enum("small", "medium", "large") var size := 1:
	set(value):
		size = clampi(value, 0, 2)
		_show_season()

const SIZES := ["small", "medium", "large"]
const PEAK := 1
const WINTER := 3
static var _shared := {}


func _ready() -> void:
	add_to_group("seasonal_planting")
	_paint()
	_show_season()


func set_season(chapter: int) -> void:
	season = chapter


func _show_season() -> void:
	var parts := find_children("*", "MeshInstance3D", true, false)
	var chosen: String = SIZES[size]
	if not parts.any(func(p: Node) -> bool: return _size_of(String(p.name)) == chosen):
		chosen = "medium"
	for part in parts:
		var mesh := part as MeshInstance3D
		var part_name := String(mesh.name)
		var shown := _size_of(part_name) == chosen
		if part_name.ends_with("_blooms_peak"):
			shown = shown and season == PEAK
		elif part_name.ends_with("_blooms"):
			shown = shown and season != WINTER
		mesh.visible = shown


## Which size a part belongs to, from its name: `azalea_bush_large_blooms`
## is large's; the tree's trunk and body are medium's.
func _size_of(part_name: String) -> String:
	for tag in SIZES:
		if part_name.contains("_%s" % tag):
			return tag
	return "medium"


func _paint() -> void:
	for found in find_children("*", "MeshInstance3D", true, false):
		_paint_mesh(found as MeshInstance3D)


func _paint_mesh(mesh: MeshInstance3D) -> void:
	if mesh.mesh == null:
		return
	for surface in mesh.mesh.get_surface_count():
		var material := mesh.mesh.surface_get_material(surface) as StandardMaterial3D
		if material == null or not material.resource_name.ends_with("_bloom"):
			continue
		if bloom == 0:
			mesh.set_surface_override_material(surface, null)
			continue
		var key := "%s:%d" % [material.resource_name, bloom]
		if not _shared.has(key):
			var slid := material.duplicate() as StandardMaterial3D
			var width := material.albedo_texture.get_width() if material.albedo_texture else 1
			slid.uv1_offset = Vector3(float(bloom * (width / SLOTS)) / width, 0.0, 0.0)
			_shared[key] = slid
		mesh.set_surface_override_material(surface, _shared[key])
