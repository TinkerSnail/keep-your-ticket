extends SceneTree

## The exposure is the evidence a later developed print resolves against. This
## test guards its serializable shape and, more importantly, that it snapshots
## provider facts instead of retaining mutable references.

const Exposure = preload("res://scripts/photo_exposure.gd")
const Album = preload("res://scripts/photo_album.gd")

var _failures: PackedStringArray = PackedStringArray()


func _initialize() -> void:
	var facts := [{
		"kind": &"subject",
		"id": &"eli_finch",
		"state": "no_costume_portrait",
		"position": Vector3(43.0, 7.5, 115.0),
	}]
	var pose := Transform3D(
		Basis.from_euler(Vector3(0.1, -0.6, 0.0)),
		Vector3(49.0, 8.0, 68.0)
	)
	var record := Exposure.capture(
		13.0 * 3600.0 + 17.0 * 60.0,
		pose,
		60.0,
		false,
		Vector2i(1280, 720),
		Rect2i(160, 90, 960, 540),
		facts
	)

	# Mutating a provider's live state after the shutter cannot rewrite history.
	facts[0]["state"] = "walking_away"
	_check(record["facts"][0]["state"] == "no_costume_portrait", "fact snapshot changed with its provider")
	_check(record["park_seconds"] == 47820.0, "park time was not preserved")
	_check(record["camera"]["position"] == [49.0, 8.0, 68.0], "camera position was not preserved")
	_check(record["frame"]["picture_region"] == [160, 90, 960, 540], "picture crop was not preserved")
	_check(record["flash_fired"] == false, "flash state was not preserved")
	_check(not record.has("score"), "exposure record must not contain a score")
	_check(not record.has("composition"), "exposure record must not judge composition")

	var encoded := JSON.stringify(record)
	var decoded: Variant = JSON.parse_string(encoded)
	_check(decoded is Dictionary, "exposure record did not survive JSON")
	if decoded is Dictionary:
		_check(decoded["facts"][0]["id"] == "eli_finch", "StringName fact id did not normalize")
		_check(decoded["facts"][0]["position"] == [43.0, 7.5, 115.0], "Vector3 fact did not normalize")

	var copy := Exposure.frozen_copy(record)
	copy["facts"][0]["state"] = "edited"
	_check(record["facts"][0]["state"] == "no_costume_portrait", "frozen_copy retained nested references")

	var album := Album.new()
	album._exposures.append(record)
	var album_copy: Dictionary = album.exposure_at(0)
	album_copy["facts"][0]["state"] = "resolved"
	_check(album.exposure_at(0)["facts"][0]["state"] == "no_costume_portrait", "album exposed its stored record by reference")
	album.free()

	if not _failures.is_empty():
		for failure in _failures:
			push_error(failure)
		print("PHOTO EXPOSURE FAIL: %d issue(s)" % _failures.size())
		quit(1)
		return
	print("PHOTO EXPOSURE PASS: immutable, JSON-safe, factual and score-free")
	quit()


func _check(condition: bool, failure: String) -> void:
	if not condition:
		_failures.append(failure)
