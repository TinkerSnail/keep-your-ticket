extends Node

## Dev probe: how long is each of the first frames after `main.tscn` mounts?
## Prints the load time and every frame over 50ms in the first 300. Headless is
## fine: the stalls it looks for are script and mesh building, not drawing.


func _ready() -> void:
	var t0 := Time.get_ticks_msec()
	var main := (load("res://scenes/main/main.tscn") as PackedScene).instantiate()
	print("load+instantiate %d ms" % (Time.get_ticks_msec() - t0))
	t0 = Time.get_ticks_msec()
	add_child(main)
	print("add_child %d ms" % (Time.get_ticks_msec() - t0))
	var last := Time.get_ticks_msec()
	for i in 300:
		await get_tree().process_frame
		var now := Time.get_ticks_msec()
		if now - last > 50:
			print("frame %3d  %d ms" % [i, now - last])
		last = now
	get_tree().quit()
