extends SceneTree
## What has changed in the world's ground since the frozen copy the generator was measured from,
## and how far that moves the ground the generator builds on. Written 2026-10-05 for Stage 2 of
## `documentation/terrain-master-into-game-plan-2026-10-05.md`; the reading is
## `scripts/world_terrain_source.gd`, which `tools/gen_props.gd` uses.
##
##   Godot --headless --path . --script res://tools/world_terrain_delta.gd
##   Godot --headless --path . --script res://tools/world_terrain_delta.gd -- --self-check
##
## With no argument, prints the summary: unchanged, or how many of the height grid's nodes
## changed, where, and the largest rise and fall; then how long the reading took. Read it after a
## Photoshop or Blender save of a tile, or a `tools/ground_grid_edit.py` edit, before
## regenerating, to see what the generated park will follow. The Blender panel's Send ground to
## game (`tools/ground_send.py`) runs it and waits for its `world_terrain_delta: read` line.
##
## `--self-check` raises a smooth bump in a copy of `baseline/`'s nodes in memory (nothing is
## written) and checks the reading finds it: the bump's height at the nodes inside, exactly zero
## outside. Quits 1 on any miss.
##
## Since the height grid's Stage 5 (2026-10-15) the grid is the only reading. Until then it could
## also read the world terrain master's ground pieces against `assets/source/world_terrain_baseline.res`
## (`--faces`), and `--write-baseline` and `--extend-baseline` had written that frozen copy on
## 2026-10-05 and 2026-10-06; all three are in git up to `a8cd64b`.

const WorldTerrainSource := preload("res://scripts/world_terrain_source.gd")
## The self-check's bump: centre (x, z), radius and height, on the mainland reserve where it
## was the only ground before the grid, and still away from every held outline.
const BUMP := [Vector2(2000.0, 500.0), 30.0, 2.0]


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if "--self-check" in args:
		quit(_self_check_grid())
		return
	var source := WorldTerrainSource.new()
	print(source.summary())
	print("world_terrain_delta: read the height grid in %.1fs" % source.load_seconds)
	quit(0)


func _bump(p: Vector2) -> float:
	var d := p.distance_to(BUMP[0]) / float(BUMP[1])
	if d >= 1.0:
		return 0.0
	var s := 1.0 - d
	return float(BUMP[2]) * s * s * (3.0 - 2.0 * s)


## The grid's self-check: the bump raised at the nodes of a copy of `baseline/` in memory, read
## back at those nodes and exactly zero round it.
func _self_check_grid() -> int:
	var baseline := WorldTerrainSource.load_grid("baseline")
	var failures := 0
	var same := WorldTerrainSource.new(baseline, baseline)
	if same.changed():
		print("self-check (grid): the baseline reads as changed against itself; %s" % same.summary())
		failures += 1
	var spec := WorldTerrainSource.grid_spec()
	var step := float(spec["spacing_m"])
	var tile := float(spec["tile_m"])
	var n := int(spec["tile_samples"])
	var bumped := baseline.duplicate()
	var centre: Vector2 = BUMP[0]
	var radius := float(BUMP[1])
	var raised := {}
	for key in baseline:
		var k := key as Vector2i
		var x0 := k.x * tile
		var z0 := k.y * tile
		if centre.x + radius < x0 or centre.x - radius > x0 + tile \
				or centre.y + radius < z0 or centre.y - radius > z0 + tile:
			continue
		var h: PackedFloat32Array = (baseline[k] as PackedFloat32Array).duplicate()
		for r in range(maxi(0, floori((centre.y - radius - z0) / step)), mini(n - 1, ceili((centre.y + radius - z0) / step)) + 1):
			for c in range(maxi(0, floori((centre.x - radius - x0) / step)), mini(n - 1, ceili((centre.x + radius - x0) / step)) + 1):
				var p := Vector2(x0 + c * step, z0 + r * step)
				var b := _bump(p)
				var i := r * n + c
				if b > 0.0 and not is_nan(h[i]):
					var before := h[i]
					h[i] += b
					raised[p] = float(h[i]) - before
		bumped[k] = h
	var source := WorldTerrainSource.new(bumped, baseline)
	print("self-check (grid): raised %d nodes; %s" % [raised.size(), source.summary()])
	var worst := 0.0
	var worst_store := 0.0
	for p in raised:
		worst = maxf(worst, absf(source.delta_y(p) - _bump(p)))
		worst_store = maxf(worst_store, absf(source.delta_y(p) - float(raised[p])))
	print("self-check (grid): %d nodes inside the bump, worst miss %.4fm against the bump, %.9fm against the stored change" % [
		raised.size(), worst, worst_store])
	if raised.is_empty() or worst > 0.01 or worst_store != 0.0:
		failures += 1
	var stray := 0
	for i in 72:
		var a := TAU * float(i) / 72.0
		for r in [radius + 60.0, radius + 400.0]:
			var p: Vector2 = centre + Vector2(cos(a), sin(a)) * r
			if source.delta_y(p) != 0.0:
				stray += 1
	print("self-check (grid): %d of 144 points outside the bump read other than zero" % stray)
	if stray > 0:
		failures += 1
	print("self-check (grid): %s" % ("PASS" if failures == 0 else "FAIL"))
	return 0 if failures == 0 else 1
