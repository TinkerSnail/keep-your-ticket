extends Node

## Dev probe: what is the `main.tscn` load made of? Loads each scene that
## `park_world.tscn` and `main.tscn` instance, one at a time and uncached, and
## prints load and instantiate times with the file's size, slowest first.
## Headless. Times are for a cold ResourceLoader cache within this process, so a
## scene shared by two parents is charged to whichever loads first.


func _ready() -> void:
	var paths: Array[String] = []
	for parent in ["res://scenes/main/main.tscn", "res://scenes/world/park_world.tscn"]:
		for dep in ResourceLoader.get_dependencies(parent):
			var path := dep.get_slice("::", 2) if dep.contains("::") else dep
			if path.ends_with(".tscn") and not path.ends_with("park_world.tscn") \
					and not paths.has(path):
				paths.append(path)
	var rows: Array = []
	for path in paths:
		var t0 := Time.get_ticks_msec()
		var packed := ResourceLoader.load(path, "", ResourceLoader.CACHE_MODE_REUSE) as PackedScene
		var loaded := Time.get_ticks_msec() - t0
		t0 = Time.get_ticks_msec()
		var node := packed.instantiate()
		var made := Time.get_ticks_msec() - t0
		var count := node.find_children("*", "", true, false).size()
		node.free()
		var size := FileAccess.get_file_as_bytes(path).size() / 1024
		rows.append([loaded + made, loaded, made, count, size, path])
	rows.sort_custom(func(a, b): return a[0] > b[0])
	var total := 0
	for row in rows:
		total += row[0]
	print("total %d ms over %d scenes" % [total, rows.size()])
	for row in rows.slice(0, 14):
		print("  %6d ms  (load %6d, instantiate %5d)  %6d nodes  %6d KB  %s" % row)
	get_tree().quit()
