extends RefCounted

## Builds the immutable half of a photograph: what was true when the shutter
## fired. Development, assignment resolution and the eventual print are later
## states and must not rewrite this record.
##
## Facts are supplied by scene nodes in the `photo_fact_source` group. This file
## only normalizes them into JSON-safe values; it never judges framing, beauty
## or composition.

const SCHEMA_VERSION := 1
const DAY_SECONDS := 86400.0


static func capture(
	park_seconds: float,
	camera_transform: Transform3D,
	camera_fov: float,
	flash_fired: bool,
	viewport_size: Vector2i,
	picture_region: Rect2i,
	facts: Array
) -> Dictionary:
	return {
		"schema": SCHEMA_VERSION,
		"park_seconds": fposmod(park_seconds, DAY_SECONDS),
		"camera": {
			"position": _vector3(camera_transform.origin),
			"basis_x": _vector3(camera_transform.basis.x),
			"basis_y": _vector3(camera_transform.basis.y),
			"basis_z": _vector3(camera_transform.basis.z),
			"fov": camera_fov,
		},
		"frame": {
			"viewport": [viewport_size.x, viewport_size.y],
			"picture_region": [
				picture_region.position.x,
				picture_region.position.y,
				picture_region.size.x,
				picture_region.size.y,
			],
		},
		"flash_fired": flash_fired,
		"facts": _json_array(facts),
	}


## Old PNGs remain valid album photographs. They simply cannot resolve a
## fact-based brief because the game did not preserve their exposure facts.
static func legacy() -> Dictionary:
	return {
		"schema": SCHEMA_VERSION,
		"legacy": true,
		"facts": [],
	}


## Album callers receive copies, so mission or development code cannot alter
## the stored exposure by retaining a Dictionary reference.
static func frozen_copy(record: Dictionary) -> Dictionary:
	return _json_dictionary(record)


static func _json_dictionary(source: Dictionary) -> Dictionary:
	var out := {}
	for key in source:
		out[String(key)] = _json_value(source[key])
	return out


static func _json_array(source: Array) -> Array:
	var out: Array = []
	for value in source:
		out.append(_json_value(value))
	return out


static func _json_value(value: Variant) -> Variant:
	match typeof(value):
		TYPE_NIL, TYPE_BOOL, TYPE_INT, TYPE_FLOAT, TYPE_STRING:
			return value
		TYPE_STRING_NAME:
			return String(value)
		TYPE_VECTOR2:
			return [value.x, value.y]
		TYPE_VECTOR2I:
			return [value.x, value.y]
		TYPE_VECTOR3:
			return _vector3(value)
		TYPE_VECTOR3I:
			return [value.x, value.y, value.z]
		TYPE_RECT2:
			return [value.position.x, value.position.y, value.size.x, value.size.y]
		TYPE_RECT2I:
			return [value.position.x, value.position.y, value.size.x, value.size.y]
		TYPE_ARRAY:
			return _json_array(value)
		TYPE_DICTIONARY:
			return _json_dictionary(value)
		_:
			push_warning("photo exposure dropped unsupported fact value of type %s" % type_string(typeof(value)))
			return null


static func _vector3(value: Vector3) -> Array:
	return [value.x, value.y, value.z]
