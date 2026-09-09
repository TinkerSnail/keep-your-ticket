extends Node3D

## Runtime home for "Three Jumps and a Birthday". The persistent park mounts
## this exactly once. Development UI may hand it album exposures later; until
## then it owns no input and draws no mission interface.

signal beat_completed(beat_id: StringName)
signal developed_residue(photo_index: int, facts: Array)
signal keepsake_revealed

const Story = preload("res://scripts/kiddieland_story_cartridge.gd")

var completed_beats: Array[StringName] = []
var current_beat: StringName = &"field_trip_morning"
var _developed_by_beat: Dictionary = {}
var _developed_facts_by_photo: Dictionary = {}

var birthday_album: Node3D:
	get:
		return get_node("birthday_album")


func _ready() -> void:
	birthday_album.visible = Story.keepsake_available(completed_beats) \
		and completed_beats.has(&"birthday_album")


## Entry point for the future film-development interaction. This deliberately
## looks up the album dynamically so the cartridge remains testable through a
## `--script` run, where autoload names are unavailable at compile time.
func develop_album_photo(photo_index: int) -> Dictionary:
	var album := get_node_or_null("/root/PhotoAlbum")
	if album == null or not album.has_method("exposure_at"):
		return {}
	return develop_exposure(photo_index, album.call("exposure_at", photo_index))


## Store a copy beside this beat, then ask the pure cartridge to resolve the
## complete developed set. The source exposure is never retained or changed.
func develop_exposure(photo_index: int, exposure: Dictionary) -> Dictionary:
	if current_beat == &"birthday_album" or exposure.is_empty():
		return {}
	var key := String(current_beat)
	if not _developed_by_beat.has(key):
		_developed_by_beat[key] = []
	_developed_by_beat[key].append(exposure.duplicate(true))
	var result := Story.resolve_developed(current_beat, _developed_by_beat[key])
	if not result.get("complete", false):
		return result

	var finished := current_beat
	if not completed_beats.has(finished):
		completed_beats.append(finished)
		var residue: Array = result.get("developed_facts", []).duplicate(true)
		if not residue.is_empty():
			_developed_facts_by_photo[photo_index] = residue
			developed_residue.emit(photo_index, residue.duplicate(true))
		beat_completed.emit(finished)
		_advance()
	return result


## Birthday Album is a return-to-place payoff rather than another evidence
## brief. The call will eventually come from the pavilion's ordinary visit
## volume; it is public here so the vertical-slice probe can exercise it now.
func visit_pavilion() -> bool:
	if current_beat != &"birthday_album" or not Story.keepsake_available(completed_beats):
		return false
	if not completed_beats.has(&"birthday_album"):
		completed_beats.append(&"birthday_album")
		birthday_album.visible = true
		beat_completed.emit(&"birthday_album")
		keepsake_revealed.emit()
	return true


func developed_facts_for_photo(photo_index: int) -> Array:
	return _developed_facts_by_photo.get(photo_index, []).duplicate(true)


func access_is_open(access_id: StringName) -> bool:
	return completed_beats.has(&"behind_the_head") and access_id in [
		&"family_photo_workroom", &"r14_manual_turnout", &"p4_service_pocket"
	]


func _advance() -> void:
	var definitions := Story.beats()
	for index in definitions.size():
		if StringName(definitions[index]["id"]) != current_beat:
			continue
		if index + 1 < definitions.size():
			current_beat = StringName(definitions[index + 1]["id"])
		return
