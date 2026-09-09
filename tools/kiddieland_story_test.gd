extends SceneTree

## Proves the approved five-beat Kiddieland cartridge against developed shutter
## facts. It does not write album files or change the park.

const Story = preload("res://scripts/kiddieland_story_cartridge.gd")
const StoryScene = preload("res://scenes/world/kiddieland_story.tscn")

var _failures: PackedStringArray = PackedStringArray()
var _checks_run := 0


func _initialize() -> void:
	_check_cast_and_shape()
	_check_field_trip()
	_check_jump_order()
	_check_favor_and_access()
	_check_after_close_residue()
	_check_keepsake()
	_check_runtime_bridge()

	if not _failures.is_empty():
		for failure in _failures:
			push_error(failure)
		print("KIDDIELAND STORY FAIL: %d issue(s)" % _failures.size())
		quit(1)
		return
	if _checks_run < 18:
		push_error("KIDDIELAND STORY FAIL: test stopped after %d checks" % _checks_run)
		quit(1)
		return
	print("KIDDIELAND STORY PASS: five beats, three cast, factual development, one residue, visible keepsake")
	quit()


func _check_cast_and_shape() -> void:
	var cast := Story.cast()
	var beats := Story.beats()
	_check(cast.size() == 3, "cartridge must have exactly three returning cast members")
	_check(cast.map(func(person: Dictionary) -> String: return String(person["name"])) == [
		"Teresa Ramos", "Eli Finch", "Gus Mercado"
	], "returning cast changed")
	_check(beats.size() == 5, "cartridge must have exactly five beats")
	_check(beats.map(func(item: Dictionary) -> String: return String(item["id"])) == [
		"field_trip_morning", "three_clean_jumps", "behind_the_head",
		"one_last_splash", "birthday_album"
	], "five-beat order changed")
	for definition in beats:
		_check(not definition.has("score"), "%s introduced a score" % definition["id"])
		_check(not definition.has("composition"), "%s introduced composition judgment" % definition["id"])


func _check_field_trip() -> void:
	var result := Story.resolve_developed(&"field_trip_morning", [
		_exposure(10.5, [{"kind": "event", "id": "field_trip_class", "state": "character_garden"}]),
		_exposure(11.0, [{"kind": "event", "id": "field_trip_group", "state": "carousel"}]),
		_exposure(11.5, [{"kind": "event", "id": "field_trip_group", "state": "mini_railway"}]),
	])
	_check(result["complete"], "Field Trip Morning did not resolve from its three ordinary stops")
	_check(not result.has("score"), "development result exposed a score")


func _check_jump_order() -> void:
	var out_of_order := Story.resolve_developed(&"three_clean_jumps", [
		_exposure(12.0, [_fact("water_moment", "kg1_frog_2", "jump")]),
		_exposure(12.1, [_fact("water_moment", "kg1_frog_1", "jump")]),
		_exposure(12.2, [_fact("water_moment", "kg1_frog_3", "jump")]),
	])
	_check(not out_of_order["complete"], "Three Clean Jumps accepted the frogs out of order")
	var ordered := Story.resolve_developed(&"three_clean_jumps", [
		_exposure(12.2, [_fact("water_moment", "kg1_frog_3", "jump")]),
		_exposure(12.0, [_fact("water_moment", "kg1_frog_1", "jump")]),
		_exposure(12.1, [_fact("water_moment", "kg1_frog_2", "jump")]),
	])
	_check(ordered["complete"], "Three Clean Jumps followed development order instead of shutter time")


func _check_favor_and_access() -> void:
	var result := Story.resolve_developed(&"behind_the_head", [
		_exposure(14.0, [_fact("subject", "eli_finch", "mascot_portrait")]),
		_exposure(14.2, [_fact("subject", "eli_finch", "face_board_portrait")]),
		_exposure(16.1, [_fact("subject", "eli_finch", "no_costume_portrait")]),
	])
	_check(result["complete"], "Behind the Head did not resolve from Eli's three ordinary portraits")
	_check(result["unlocks"] == [
		&"family_photo_workroom", &"r14_manual_turnout", &"p4_service_pocket"
	], "favor changed its access dividend")


func _check_after_close_residue() -> void:
	var facts := [
		_fact("water_system", "kg1", "pressure_bleed"),
		_fact("water_system", "kg1", "shared_timer_final_cycle"),
		_fact("water_moment", "kg1_frog_3", "final_jump"),
	]
	var daytime := Story.resolve_developed(&"one_last_splash", [_exposure(18.0, facts)])
	_check(not daytime["complete"], "One Last Splash accepted its final cycle during park hours")
	var night := Story.resolve_developed(&"one_last_splash", [_exposure(22.25, facts)])
	_check(night["complete"], "One Last Splash did not resolve after close")
	_check(night["developed_facts"] == [{
		"kind": &"residue", "id": &"younger_girl", "state": &"beside_third_frog"
	}], "developed image did not receive exactly the approved younger-girl residue")
	var source := _exposure(22.25, facts)
	Story.resolve_developed(&"one_last_splash", [source])
	_check(source["facts"].size() == 3, "development rewrote immutable shutter facts")


func _check_keepsake() -> void:
	var four := [
		&"field_trip_morning", &"three_clean_jumps", &"behind_the_head", &"one_last_splash"
	]
	_check(not Story.keepsake_available(four.slice(0, 3)), "Birthday Album appeared before all four earlier beats")
	_check(Story.keepsake_available(four), "Birthday Album did not become available after the first four beats")
	_check(Story.beat(&"birthday_album")["visible_at"] == &"kc3_pavilion", "keepsake moved away from the pavilion")


func _check_runtime_bridge() -> void:
	var runtime := StoryScene.instantiate()
	root.add_child(runtime)
	_check(not runtime.birthday_album.visible, "pavilion keepsake began visible")
	var index := 0
	var beat_exposures := {
		&"field_trip_morning": [
			_exposure(10.5, [_fact("event", "field_trip_class", "character_garden")]),
			_exposure(11.0, [_fact("event", "field_trip_group", "carousel")]),
			_exposure(11.5, [_fact("event", "field_trip_group", "mini_railway")]),
		],
		&"three_clean_jumps": [
			_exposure(12.0, [_fact("water_moment", "kg1_frog_1", "jump")]),
			_exposure(12.1, [_fact("water_moment", "kg1_frog_2", "jump")]),
			_exposure(12.2, [_fact("water_moment", "kg1_frog_3", "jump")]),
		],
		&"behind_the_head": [
			_exposure(14.0, [_fact("subject", "eli_finch", "mascot_portrait")]),
			_exposure(14.2, [_fact("subject", "eli_finch", "face_board_portrait")]),
			_exposure(16.1, [_fact("subject", "eli_finch", "no_costume_portrait")]),
		],
		&"one_last_splash": [_exposure(22.25, [
			_fact("water_system", "kg1", "pressure_bleed"),
			_fact("water_system", "kg1", "shared_timer_final_cycle"),
			_fact("water_moment", "kg1_frog_3", "final_jump"),
		])],
	}
	for beat_id in beat_exposures:
		_check(runtime.current_beat == beat_id, "runtime beat order diverged at %s" % beat_id)
		for exposure in beat_exposures[beat_id]:
			runtime.develop_exposure(index, exposure)
			index += 1
	_check(runtime.current_beat == &"birthday_album", "runtime did not reach the keepsake beat")
	_check(runtime.access_is_open(&"r14_manual_turnout"), "favor did not open its runtime access dividend")
	_check(runtime.developed_facts_for_photo(index - 1).size() == 1, "runtime lost the developed-image residue")
	_check(runtime.visit_pavilion(), "return visit did not resolve the Birthday Album")
	_check(runtime.birthday_album.visible, "resolved Birthday Album remained hidden")
	runtime.queue_free()


func _exposure(hour: float, facts: Array) -> Dictionary:
	return {
		"schema": 1,
		"park_seconds": hour * 3600.0,
		"facts": facts.duplicate(true),
	}


func _fact(kind: String, fact_id: String, state: String) -> Dictionary:
	return {"kind": kind, "id": fact_id, "state": state}


func _check(condition: bool, failure: String) -> void:
	_checks_run += 1
	if not condition:
		_failures.append(failure)
