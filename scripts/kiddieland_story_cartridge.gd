extends RefCounted

## The complete evidence contract for Kiddieland's first story cartridge,
## "Three Jumps and a Birthday". A photograph contributes only facts that were
## frozen when its shutter fired. This class is used later, when film develops;
## it never judges framing and it never changes an exposure record.

const AFTER_CLOSE_SECONDS := 22.0 * 3600.0
const OPEN_SECONDS := 10.0 * 3600.0

const CAST: Array[Dictionary] = [
	{
		"id": &"teresa_ramos",
		"name": "Teresa Ramos",
		"role": "Family Commons lead",
	},
	{
		"id": &"eli_finch",
		"name": "Eli Finch",
		"role": "mascot performer",
	},
	{
		"id": &"gus_mercado",
		"name": "Gus Mercado",
		"role": "miniature-railway operator",
	},
]

## Requirement ids are album-slot identities, not points. Their order matters
## only for `three_clean_jumps`, where the three water moments must have happened
## in sequence. The camera remains free aim throughout.
static func _beat_definitions() -> Array[Dictionary]:
	return [
	{
		"id": &"field_trip_morning",
		"name": "Field Trip Morning",
		"kind": &"postcard",
		"requirements": [
			_slot(&"class_at_character_garden", &"event", &"field_trip_class", &"character_garden"),
			_slot(&"group_at_carousel", &"event", &"field_trip_group", &"carousel"),
			_slot(&"group_at_mini_railway", &"event", &"field_trip_group", &"mini_railway"),
		],
	},
	{
		"id": &"three_clean_jumps",
		"name": "Three Clean Jumps",
		"kind": &"routine",
		"ordered": true,
		"requirements": [
			_slot(&"frog_one", &"water_moment", &"kg1_frog_1", &"jump"),
			_slot(&"frog_two", &"water_moment", &"kg1_frog_2", &"jump"),
			_slot(&"frog_three", &"water_moment", &"kg1_frog_3", &"jump"),
		],
	},
	{
		"id": &"behind_the_head",
		"name": "Behind the Head",
		"kind": &"favor",
		"requirements": [
			_slot(&"ordinary_mascot", &"subject", &"eli_finch", &"mascot_portrait"),
			_slot(&"face_in_hole", &"subject", &"eli_finch", &"face_board_portrait"),
			_slot(&"no_costume", &"subject", &"eli_finch", &"no_costume_portrait"),
		],
		"unlocks": [
			&"family_photo_workroom",
			&"r14_manual_turnout",
			&"p4_service_pocket",
		],
	},
	{
		"id": &"one_last_splash",
		"name": "One Last Splash",
		"kind": &"after_close",
		"after_close": true,
		"requirements": [
			_slot(&"pressure_bleed", &"water_system", &"kg1", &"pressure_bleed"),
			_slot(&"shared_timer", &"water_system", &"kg1", &"shared_timer_final_cycle"),
			_slot(&"third_frog", &"water_moment", &"kg1_frog_3", &"final_jump"),
		],
		"developed_residue": {
			"kind": &"residue",
			"id": &"younger_girl",
			"state": &"beside_third_frog",
		},
	},
	{
		"id": &"birthday_album",
		"name": "Birthday Album",
		"kind": &"keepsake",
		"return_payoff": true,
		"requires_beats": [
			&"field_trip_morning",
			&"three_clean_jumps",
			&"behind_the_head",
			&"one_last_splash",
		],
		"visible_at": &"kc3_pavilion",
	},
	]


static func cast() -> Array[Dictionary]:
	return CAST.duplicate(true)


static func beats() -> Array[Dictionary]:
	return _beat_definitions().duplicate(true)


static func beat(beat_id: StringName) -> Dictionary:
	for definition in _beat_definitions():
		if StringName(definition["id"]) == beat_id:
			return definition.duplicate(true)
	return {}


## Resolve a developed set of exposures against one beat. Returned `filled`
## values name album evidence slots; there is deliberately no score, quality or
## composition value. Callers may develop the photos in any order: the routine's
## temporal order comes from their shutter times.
static func resolve_developed(beat_id: StringName, exposures: Array) -> Dictionary:
	var definition := beat(beat_id)
	if definition.is_empty():
		return {"beat_id": beat_id, "complete": false, "filled": []}
	if definition.get("return_payoff", false):
		return {"beat_id": beat_id, "complete": false, "filled": []}

	var valid: Array[Dictionary] = []
	for exposure in exposures:
		if exposure is not Dictionary or exposure.get("legacy", false):
			continue
		if bool(definition.get("after_close", false)) and not _is_after_close(exposure):
			continue
		valid.append(exposure)

	var filled: Array[StringName] = []
	var chosen_times: Array[float] = []
	var after_time := -1.0
	for requirement in definition["requirements"]:
		var found_time := _matching_time(requirement["fact"], valid, after_time)
		if found_time < 0.0:
			continue
		filled.append(StringName(requirement["id"]))
		chosen_times.append(found_time)
		if bool(definition.get("ordered", false)):
			after_time = found_time

	var complete: bool = filled.size() == definition["requirements"].size()
	var result := {
		"beat_id": beat_id,
		"complete": complete,
		"filled": filled,
		"unlocks": definition.get("unlocks", []).duplicate(),
		"developed_facts": [],
	}
	if complete and definition.has("developed_residue"):
		# The residue belongs to the developed print, not the immutable exposure.
		result["developed_facts"] = [definition["developed_residue"].duplicate(true)]
	return result


## The pavilion album is a visible return-day change. It becomes available from
## story completion, without asking the player to take or submit another photo.
static func keepsake_available(completed_beats: Array) -> bool:
	var keepsake := beat(&"birthday_album")
	for required in keepsake["requires_beats"]:
		if not completed_beats.has(required) and not completed_beats.has(String(required)):
			return false
	return true


static func _slot(slot_id: StringName, kind: StringName, fact_id: StringName, state: StringName) -> Dictionary:
	return {
		"id": slot_id,
		"fact": {"kind": kind, "id": fact_id, "state": state},
	}


static func _matching_time(pattern: Dictionary, exposures: Array[Dictionary], after_time: float) -> float:
	var best := INF
	for exposure in exposures:
		var shutter_time := float(exposure.get("park_seconds", -1.0))
		if shutter_time <= after_time:
			continue
		for fact in exposure.get("facts", []):
			if fact is Dictionary and _matches(pattern, fact):
				best = minf(best, shutter_time)
	return -1.0 if is_inf(best) else best


static func _matches(pattern: Dictionary, fact: Dictionary) -> bool:
	for key in pattern:
		if String(fact.get(key, "")) != String(pattern[key]):
			return false
	return true


static func _is_after_close(exposure: Dictionary) -> bool:
	var shutter_time := float(exposure.get("park_seconds", -1.0))
	return shutter_time >= AFTER_CLOSE_SECONDS or (shutter_time >= 0.0 and shutter_time < OPEN_SECONDS)
