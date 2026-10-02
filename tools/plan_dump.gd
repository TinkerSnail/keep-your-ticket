extends SceneTree

## Dump the parts of `ParkPlan` that the Blender terrain master's reference
## layer draws (`tools/blender/world_terrain.py`) to one JSON file. Written
## 2026-10-01. `ParkPlan` is a plain RefCounted that names no autoload, so it
## is safe to preload here and run with `--script`:
##
##   Godot --headless --path . --script res://tools/plan_dump.gd -- <out.json>
##
## Vectors become arrays ([x, y] or [x, y, z]), Rect2 becomes
## {x, z, w, h}; everything is in Godot world coordinates, x east, z south,
## y up, metres. Add a name to `CONSTANTS` or a call to `_calls` when the
## reference layer needs more; nothing here is read back by the game.

const Plan = preload("res://scripts/park_plan.gd")

const CONSTANTS := [
	"PLAZA_CENTRE", "PLAZA_HALF", "FOUNTAIN_RIM_SEAT_R",
	"WATER_TOP", "SHORE_TOP", "BEACH_TOP", "SHORE_EDGE", "SHORE_FROM_X", "BLUFF_FACE_X",
	"ARCH_AT", "ARCH_HEIGHT", "CASCADE_AXIS_Z", "CASCADE_TOP_X", "CASCADE_WALL_X",
	"STAIR_FOOT", "STAIR_FOOT_STAND", "CASCADE_WEST", "CASCADE_EAST",
	"PIER_Z", "PIER_ROOT", "PIER_LENGTH", "PIER_HALF_W", "PAVILION_AT", "PROMENADE_X",
	"WHEEL_AT", "WHEEL_RADIUS", "WHEEL_TOP",
	"COAST_NORTH_OUTLINE", "COAST_SOUTH_OUTLINE", "COAST_NORTH_FAR_FROM", "COAST_SOUTH_FAR_FROM",
	"BAY_WATER_FROM_Z", "BAY_WATER_TO_X", "NORTH_WATER_TO_Z", "EAST_WATER_FROM_X",
	"REBUILD_WORLD_LAND_FROM_X", "REBUILD_WORLD_LAND_TO_X",
	"REBUILD_WORLD_LAND_FROM_Z", "REBUILD_WORLD_LAND_TO_Z",
	"REBUILD_WORLD_WATER_FROM_X", "REBUILD_WORLD_WATER_TO_X", "REBUILD_WORLD_WATER_FAR_X",
	"REBUILD_WORLD_WATER_FROM_Z", "REBUILD_WORLD_WATER_TO_Z",
	"HIGHWAY_JUNCTION", "HIGHWAY_W", "HIGHWAY_CARRIAGEWAY_W", "HIGHWAY_VIEW",
	"HIGHWAY_CLEARINGS", "INTERCHANGE",
	"APPROACH_ROAD", "APPROACH_ROAD_W", "FRONT_ROAD_Z", "FRONT_ROAD_HALF_X", "FRONT_ROAD_W",
	"LOT_ENTRY_XS", "DROP_OFF",
	"FAR_CITY", "BEACH_TOWN_OUTLINE", "NORTH_TOWN_EXTENT_ST", "NORTH_TOWN_HOUSE_ST",
	"SOUTH_BLUFF_Z", "SOUTH_BLUFF_HEIGHT", "SOUTH_BLUFF_TO_X",
	"RIM_RANGE_CENTRE", "RIM_RANGE_INNER_R", "WORLD_JUNCTION", "WORLD_CLIFFS",
	"REBUILD_COASTAL_CREEK", "COASTER_STATION",
]


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.is_empty():
		push_error("plan_dump: give the output path after --")
		quit(1)
		return
	var d := _constants()
	d["highway_path"] = _j(Plan.highway_path())
	d["highway_path_raw"] = _j(Plan.highway_path_raw())
	d["approach_road_points"] = _j(Plan.approach_road_points())
	d["approach_crossing"] = _j(Plan.approach_crossing())
	d["north_town_outline"] = _j(Plan.north_town_outline())
	d["town_streets"] = _j(Plan.town_streets())
	d["range_toe_line"] = _j(Plan.range_toe_line())
	d["rebuild_coastal_creek"] = _j(Plan.rebuild_coastal_creek())
	d["promenade_ne_path"] = _j(Plan.promenade_ne_path())
	var f := FileAccess.open(args[0], FileAccess.WRITE)
	if f == null:
		push_error("plan_dump: cannot write " + args[0])
		quit(1)
		return
	f.store_string(JSON.stringify(d, "  "))
	f.close()
	print("plan_dump: wrote %d keys to %s" % [d.size(), args[0]])
	quit()


## `Plan.get(name)` is not allowed on the class, so every constant is spelled
## out once; the list above is the one to edit.
func _constants() -> Dictionary:
	var d := {}
	var inst = Plan.new()
	for n in CONSTANTS:
		d[n] = _j(inst.get(n))
	return d


func _j(v):
	match typeof(v):
		TYPE_VECTOR2:
			return [v.x, v.y]
		TYPE_VECTOR3:
			return [v.x, v.y, v.z]
		TYPE_RECT2:
			return {"x": v.position.x, "z": v.position.y, "w": v.size.x, "h": v.size.y}
		TYPE_ARRAY, TYPE_PACKED_VECTOR2_ARRAY, TYPE_PACKED_VECTOR3_ARRAY:
			var out := []
			for e in v:
				out.append(_j(e))
			return out
		TYPE_DICTIONARY:
			var out := {}
			for k in v:
				out[str(k)] = _j(v[k])
			return out
		_:
			return v
