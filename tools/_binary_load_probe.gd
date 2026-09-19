extends Node

## Dev probe: how much of a generated scene's load time is parsing text? Loads
## the two slowest generated scenes as they are, saves a binary `.scn` copy of
## each to `user://` (nothing in the project is written), and times loading
## that in a fresh cache. Headless.


func _ready() -> void:
	for scene_name in ["park_groundworks", "park_approach"]:
		var source := "res://scenes/world/generated/%s.tscn" % scene_name
		var t0 := Time.get_ticks_msec()
		var packed := ResourceLoader.load(source, "", ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
		var as_text := Time.get_ticks_msec() - t0
		var copy := "user://_binary_load_probe_%s.scn" % scene_name
		ResourceSaver.save(packed, copy)
		packed = null
		t0 = Time.get_ticks_msec()
		var again := ResourceLoader.load(copy, "", ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
		var as_binary := Time.get_ticks_msec() - t0
		t0 = Time.get_ticks_msec()
		var node := again.instantiate()
		var made := Time.get_ticks_msec() - t0
		node.free()
		print("%-18s text %6d ms   binary %5d ms   instantiate %4d ms   text %5.1f MB  binary %5.1f MB" % [
			scene_name, as_text, as_binary, made,
			FileAccess.get_file_as_bytes(source).size() / 1048576.0,
			FileAccess.get_file_as_bytes(copy).size() / 1048576.0])
		DirAccess.remove_absolute(ProjectSettings.globalize_path(copy))
	get_tree().quit()
