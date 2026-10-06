extends SceneTree
## What has changed in the world terrain master since it was copied from the
## generator, and how far that moves the ground the generator builds on.
## Written 2026-10-05 for Stage 2 of
## `documentation/terrain-master-into-game-plan-2026-10-05.md`; the reading is
## `scripts/world_terrain_source.gd`, which `tools/gen_props.gd` uses.
##
##   Godot --headless --path . --script res://tools/world_terrain_delta.gd
##   Godot --headless --path . --script res://tools/world_terrain_delta.gd -- --self-check
##   Godot --headless --path . --script res://tools/world_terrain_delta.gd -- --write-baseline
##   Godot --headless --path . --script res://tools/world_terrain_delta.gd -- --extend-baseline
##
## With no argument, prints the summary: unchanged, or how many faces changed,
## where, and the largest rise and fall. Run it after exporting and importing an
## edit to the master, before regenerating, to see what the generated park will
## follow.
##
## `--self-check` raises a smooth bump in a copy of the baseline's faces in
## memory (nothing is written) and checks the reading finds it: the bump's height
## at its corners inside, exactly zero outside. Quits 1 on any miss.
##
## `--write-baseline` froze the master as `assets/source/world_terrain_baseline.res`
## on 2026-10-05, while it was still the generator's ground exactly; it refuses
## to overwrite. `--extend-baseline` added the range's and city's landforms to it
## on 2026-10-06, as they joined the master (`WorldTerrainSource.JOINED`); it
## refuses to add them twice.

const WorldTerrainSource := preload("res://scripts/world_terrain_source.gd")
## The self-check's bump: centre (x, z), radius and height, on the mainland
## reserve where it is the only ground. It was at (700, -200) until the range's
## landforms joined the master (2026-10-06): the middle range stands over the
## reserve there, and the reading at a reserve corner is then the range face's.
const BUMP := [Vector2(2000.0, 500.0), 30.0, 2.0]


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if "--write-baseline" in args:
		var err := WorldTerrainSource.write_baseline()
		print("world_terrain_delta: baseline %s (%s)" % [
			WorldTerrainSource.BASELINE, "written" if err == OK else "not written: %d" % err])
		quit(0 if err == OK else 1)
		return
	if "--extend-baseline" in args:
		var ext := WorldTerrainSource.extend_baseline()
		print("world_terrain_delta: baseline %s (%s)" % [
			WorldTerrainSource.BASELINE, "extended with the joined landforms" if ext == OK else "not extended: %d" % ext])
		quit(0 if ext == OK else 1)
		return
	if "--self-check" in args:
		quit(_self_check())
		return
	var source := WorldTerrainSource.new()
	print(source.summary())
	quit(0)


func _bump(p: Vector2) -> float:
	var d := p.distance_to(BUMP[0]) / float(BUMP[1])
	if d >= 1.0:
		return 0.0
	var s := 1.0 - d
	return float(BUMP[2]) * s * s * (3.0 - 2.0 * s)


func _self_check() -> int:
	# The bump goes on a copy of the baseline, not the master, so the check holds however
	# far the master has been edited since.
	var baseline := WorldTerrainSource.load_baseline()
	var master := baseline.duplicate(true)
	var same := WorldTerrainSource.new(master, baseline)
	var failures := 0
	if same.changed():
		print("self-check: the baseline reads as changed against itself; %s" % same.summary())
		failures += 1
	var bumped := {}
	var raised := 0
	for body in master:
		var faces: PackedVector3Array = (master[body] as PackedVector3Array).duplicate()
		for i in faces.size():
			var h := _bump(Vector2(faces[i].x, faces[i].z))
			if h > 0.0:
				faces[i].y += h
				raised += 1
		bumped[body] = faces
	var source := WorldTerrainSource.new(bumped, baseline)
	print("self-check: raised %d corners; %s" % [raised, source.summary()])
	# At every raised corner of the top ground the reading is the bump there.
	var worst := 0.0
	var probed := 0
	var top := {}
	for body in bumped:
		var faces: PackedVector3Array = bumped[body]
		for i in faces.size():
			var p := Vector2(faces[i].x, faces[i].z)
			var key := Vector2i(roundi(p.x * 100.0), roundi(p.y * 100.0))
			if not top.has(key) or faces[i].y > (top[key] as Vector3).y:
				top[key] = faces[i]
	for key in top:
		var corner: Vector3 = top[key]
		var p := Vector2(corner.x, corner.z)
		var want := _bump(p)
		if want <= 0.0:
			continue
		probed += 1
		worst = maxf(worst, absf(source.delta_y(p) - want))
	print("self-check: %d top corners inside the bump, worst miss %.4fm" % [probed, worst])
	if probed == 0 or worst > 0.01:
		failures += 1
	# A ring of points just outside it, and far away, read exactly zero.
	var stray := 0
	for i in 72:
		var a := TAU * float(i) / 72.0
		for r in [float(BUMP[1]) + 60.0, float(BUMP[1]) + 400.0]:
			var p: Vector2 = BUMP[0] + Vector2(cos(a), sin(a)) * r
			if source.delta_y(p) != 0.0:
				stray += 1
	print("self-check: %d of 144 points outside the bump read other than zero" % stray)
	if stray > 0:
		failures += 1
	print("self-check: %s" % ("PASS" if failures == 0 else "FAIL"))
	return 0 if failures == 0 else 1
