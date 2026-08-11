extends Node

## Global store for captured photographs.
##
## Autoloaded as `PhotoAlbum`. Photos are written to `user://photos` as PNGs and
## kept in memory as thumbnails for the album grid. Nothing here counts up or
## down — the album is a set of filled and empty slots, not a score.

signal photo_added(index: int, thumbnail: Texture2D)

const PHOTO_DIR := "user://photos"
const THUMBNAIL_WIDTH := 384

var thumbnails: Array[Texture2D] = []
var paths: PackedStringArray = PackedStringArray()


func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(PHOTO_DIR)
	_load_existing()


func add_photo(image: Image) -> void:
	var path := "%s/photo_%s_%03d.png" % [PHOTO_DIR, _date_stamp(), thumbnails.size()]
	var err := image.save_png(path)
	if err != OK:
		push_warning("Could not save photo to %s (error %d)" % [path, err])
		return
	paths.append(path)
	var thumbnail := _make_thumbnail(image)
	thumbnails.append(thumbnail)
	photo_added.emit(thumbnails.size() - 1, thumbnail)
	print("photo saved: ", ProjectSettings.globalize_path(path))


func count() -> int:
	return thumbnails.size()


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
		thumbnails.append(_make_thumbnail(image))


func _date_stamp() -> String:
	return Time.get_datetime_string_from_system(false, false).replace(":", "-").replace("T", "_")
