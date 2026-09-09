extends Node

## Global store for captured photographs.
##
## Autoloaded as `PhotoAlbum`. Photos are written to `user://photos` as PNGs and
## kept in memory as thumbnails for the album grid. Nothing here counts up or
## down — the album is a set of filled and empty slots, not a score.

signal photo_added(index: int, thumbnail: Texture2D)

const Exposure = preload("res://scripts/photo_exposure.gd")
const PHOTO_DIR := "user://photos"
const THUMBNAIL_WIDTH := 384

var thumbnails: Array[Texture2D] = []
var paths: PackedStringArray = PackedStringArray()
var _exposures: Array[Dictionary] = []


func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(PHOTO_DIR)
	_load_existing()


func add_photo(image: Image, exposure: Dictionary = {}) -> void:
	var path := "%s/photo_%s_%03d.png" % [PHOTO_DIR, _date_stamp(), thumbnails.size()]
	var err := image.save_png(path)
	if err != OK:
		push_warning("Could not save photo to %s (error %d)" % [path, err])
		return
	var stored_exposure: Dictionary = Exposure.legacy() if exposure.is_empty() else Exposure.frozen_copy(exposure)
	paths.append(path)
	_exposures.append(stored_exposure)
	_save_exposure(path, stored_exposure)
	var thumbnail := _make_thumbnail(image)
	thumbnails.append(thumbnail)
	photo_added.emit(thumbnails.size() - 1, thumbnail)
	print("photo saved: ", ProjectSettings.globalize_path(path))


func count() -> int:
	return thumbnails.size()


## Returns a deep copy. The exposure itself is evidence and does not change
## when a brief resolves or a print is developed.
func exposure_at(index: int) -> Dictionary:
	if index < 0 or index >= _exposures.size():
		return {}
	return Exposure.frozen_copy(_exposures[index])


func photo_directory() -> String:
	return ProjectSettings.globalize_path(PHOTO_DIR)


func _make_thumbnail(image: Image) -> Texture2D:
	var copy := Image.new()
	copy.copy_from(image)
	var width := float(copy.get_width())
	var height := float(copy.get_height())
	if width <= 0.0 or height <= 0.0:
		return ImageTexture.create_from_image(copy)
	var target_height := int(round(THUMBNAIL_WIDTH * height / width))
	copy.resize(THUMBNAIL_WIDTH, maxi(target_height, 1), Image.INTERPOLATE_BILINEAR)
	return ImageTexture.create_from_image(copy)


func _load_existing() -> void:
	var dir := DirAccess.open(PHOTO_DIR)
	if dir == null:
		return
	var files := dir.get_files()
	files.sort()
	for file_name in files:
		if not file_name.ends_with(".png"):
			continue
		var path := "%s/%s" % [PHOTO_DIR, file_name]
		var image := Image.new()
		if image.load(path) != OK:
			continue
		paths.append(path)
		_exposures.append(_load_exposure(path))
		thumbnails.append(_make_thumbnail(image))


func _save_exposure(photo_path: String, exposure: Dictionary) -> void:
	var path := _exposure_path(photo_path)
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		push_warning("Could not save exposure record to %s (error %d)" % [path, FileAccess.get_open_error()])
		return
	file.store_string(JSON.stringify(exposure, "\t"))


func _load_exposure(photo_path: String) -> Dictionary:
	var path := _exposure_path(photo_path)
	if not FileAccess.file_exists(path):
		return Exposure.legacy()
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_warning("Could not read exposure record at %s (error %d)" % [path, FileAccess.get_open_error()])
		return Exposure.legacy()
	var decoded: Variant = JSON.parse_string(file.get_as_text())
	if decoded is not Dictionary:
		push_warning("Ignoring malformed exposure record at %s" % path)
		return Exposure.legacy()
	return Exposure.frozen_copy(decoded)


func _exposure_path(photo_path: String) -> String:
	return "%s.exposure.json" % photo_path.get_basename()


func _date_stamp() -> String:
	return Time.get_datetime_string_from_system(false, false).replace(":", "-").replace("T", "_")
