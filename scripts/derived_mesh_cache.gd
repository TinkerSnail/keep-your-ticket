extends RefCounted

## Build a derived mesh once and hand the same one to every placement that
## derives it from the same inputs, in the running game only.
##
## Written on 2026-09-18. The planting scripts (`hakone_grass`,
## `purple_heart_sprig`, `coastal_palm_fern_fill`, `coastal_palm_crown`) each
## rebuilt every blade, leaf and frond for every placement at launch: 260 grass
## clumps made the same 72 blades 260 times, about 13 seconds of the first
## frame, and 36,000 meshes that differed in nothing. A placed scene shares its
## Curve3D sub-resources with every other instance of that scene, so the curve's
## identity plus the numbers read off its Path3D say whether two meshes would
## come out the same.
##
## The key is an Array of plain values; pass a resource as its instance id and
## also in `keep`, which holds it alive so the id cannot be handed to something
## else. In the editor nothing is cached: a course being reshaped keeps its
## identity while its contents change, and the editor must always rebuild.

static var _meshes := {}


static func fetch(key: Array, keep: Array, build: Callable) -> Mesh:
	# KYT_NO_MESH_CACHE builds everything privately again, for comparison.
	if Engine.is_editor_hint() or OS.get_environment("KYT_NO_MESH_CACHE") != "":
		return build.call()
	var entry: Variant = _meshes.get(key)
	if entry == null:
		entry = [build.call(), keep]
		_meshes[key] = entry
	return entry[0]


static func id_of(resource: Resource) -> int:
	return 0 if resource == null else resource.get_instance_id()
