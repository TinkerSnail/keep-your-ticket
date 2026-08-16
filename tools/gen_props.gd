extends SceneTree

## Dev tool: builds the plaza's park residue and saves it as its own scene.
##
## Runs inside Godot on purpose. Transforms are built with Transform3D.rotated()
## and Basis(axis, angle) rather than written out by hand — the .tscn text format
## serialises basis *rows* while basis.x/y/z are the *columns*, and hand-writing
## the nine numbers silently produces the transpose, which for a rotation is the
## inverse. Letting the engine do the maths removes that whole class of mistake.
##
##   godot --headless --path . --script res://_gen_props.gd

## The park's plan. Everything below that says where something *is* reads from
## here rather than declaring it, so the generator and the things that draw the
## park cannot disagree about the same number.
##
## Preloaded rather than reached for by `class_name`, because this file runs
## under `--script` and that compiles before the project's script registry and
## autoloads are up. `park_plan.gd` is deliberately autoload-free — pure static
## data on a `RefCounted` — which is exactly what makes this preload safe. If
## anything global ever gets named in it, this line starts silently yielding a
## script that is not itself and the generator emits well-formed output with
## pieces missing.
const Plan := preload("res://scripts/park_plan.gd")

const OUT_PATH := "res://scenes/world/plaza_props.tscn"
const PAVING_PATH := "res://scenes/world/plaza_paving.tscn"
const SKYLINE_PATH := "res://scenes/world/plaza_skyline.tscn"

## The fountain, which used to be five stacked cylinders typed into
## `plaza.tscn` by hand and is now 190-odd parts and two shaders.
##
## Its own scene for the ordinary reason — that is too many parts to hand-author
## and keep straight — but moving it *out* of `plaza.tscn` is worth a line,
## because `plaza.tscn` is the one hand-authored world scene and the temptation
## is to say the plaza's centrepiece belongs in it. The perimeter is hand-laid
## because it is a *room shape* being designed: its runs are the thing the
## enclosure argument is about, and the frontage generator reads them back out.
## The fountain is not a room shape, it is an assembly, and every other assembly
## in the park is generated. What stays in `plaza.tscn` is the ground, the walls
## and the tower — the things the plaza *is*, rather than the things standing in
## it.
const FOUNTAIN_PATH := "res://scenes/world/plaza_fountain.tscn"
const STAIR_PATH := "res://scenes/world/west_stair.tscn"
const ENTRANCE_PATH := "res://scenes/world/entrance.tscn"
const THRESHOLD_PATH := "res://scenes/world/thresholds.tscn"

## The west, in three scenes rather than one, because the same ground has to be
## standing in two different sections and only one section is ever mounted.
##
## `plaza_skyline.tscn` used to hold the whole west — water, bluff, shore,
## frontage, pier, wheel — as a child of `plaza.tscn`. Which meant that crossing
## the gate at the foot of the stair freed the water the player was walking
## towards, the bluff they had just come down, and the pier they were looking at,
## and left the boardwalk floating over nothing. Nothing caught it: the section
## test only asks whether the player lands on a floor, and they did.
##
##   `west_shell.tscn`   water, bluff and shore. **Both sections instance this.**
##                       It is the ground and the horizon, it is identical seen
##                       from either side, and it is what makes the cut continuous.
##   `west_far.tscn`     the tableau — frontage, pier, wheel and coaster as cheap
##                       massing with no collision. **Plaza only.** What you look
##                       at from the overlook.
##   `boardwalk.tscn`    the same four things built for real, plus everything a
##                       person walking there needs. **Boardwalk only.**
##
## So the swap at the gate is: keep the shell, throw away the tableau, stand up
## the real thing. Which is the trade the design has been describing all along —
## "the real one replaces the west tableau outright" — made literal.
const WEST_SHELL_PATH := "res://scenes/world/west_shell.tscn"
const WEST_FAR_PATH := "res://scenes/world/west_far.tscn"
const BOARDWALK_PATH := "res://scenes/world/boardwalk.tscn"

var _root: Node3D
var mats: Dictionary = {}


func _initialize() -> void:
	_build_textures()
	_build_materials()

	_root = Node3D.new()
	_root.name = "props"
	_begin_scene()
	_dilate_plaza = true
	_benches()
	_lamps()
	_bins()
	_cafe()
	_queue()
	_bollards()
	_aframes()
	_newsboxes()
	_flagpoles()
	_cart()
	_stroller()
	_ladder()
	_balloons()
	_litter()
	_picnic()
	_crates()
	# Everything below is placed in final coordinates against the 104m plaza,
	# so the dilation comes off first. These were never in the 80m plaza and
	# have nothing to be mapped from — they exist because it grew.
	_dilate_plaza = false
	_trees()
	_outer_furniture()
	_picture_spots()
	_plaza_lights()
	if not _save(_root, OUT_PATH):
		return

	_root = Node3D.new()
	_root.name = "skyline"
	_begin_scene()
	_skyline()
	if not _save(_root, SKYLINE_PATH):
		return

	# The ground and the horizon of the west, shared by the two sections that
	# stand on it. Written before either, because both are laid out against it.
	_root = Node3D.new()
	_root.name = "west_shell"
	_begin_scene()
	_west_shell()
	if not _save(_root, WEST_SHELL_PATH):
		return

	# What the west looks like from the overlook, and only from there.
	_root = Node3D.new()
	_root.name = "west_far"
	_begin_scene()
	_west_far()
	if not _save(_root, WEST_FAR_PATH):
		return

	# The same view with a floor under it.
	_root = Node3D.new()
	_root.name = "boardwalk"
	_begin_scene()
	_boardwalk_section()
	if not _save(_root, BOARDWALK_PATH):
		return

	# The one thing west of the parapet the player can stand on, so unlike the
	# rest of it this one collides.
	_root = Node3D.new()
	_root.name = "west_stair"
	_begin_scene()
	_west_cascade()
	if not _save(_root, STAIR_PATH):
		return

	# The arrival. Everything south of the plaza's south wall.
	_root = Node3D.new()
	_root.name = "entrance"
	_begin_scene()
	_entrance()
	if not _save(_root, ENTRANCE_PATH):
		return

	# Scaffolding, and the first thing to delete when a real section attaches.
	_root = Node3D.new()
	_root.name = "thresholds"
	_begin_scene()
	_thresholds()
	if not _save(_root, THRESHOLD_PATH):
		return

	# The circulation, paved. Its own scene rather than a handful of nodes in
	# `plaza_props.tscn`, because paving is not a prop: the props are 214 things
	# scattered on a floor and this is the floor saying where the walking goes.
	#
	# **Built last, and that is load-bearing.** `_begin_scene` hands each scene a
	# seam seed five on from the last, so a scene inserted anywhere but the end
	# shifts the displacement of every scene after it — and a shifted ordinal is
	# how two untouched shapes end up sharing a plane. Adding this one at the top
	# of the run put a bulkhead and a door in `entrance.tscn` on the same face,
	# four scenes away and unedited. Nothing here is a CSG shape, so the seed it
	# gets does not matter to it; it matters to everything it would displace.
	_root = Node3D.new()
	_root.name = "paving"
	_begin_scene()
	_paving()
	if not _save(_root, PAVING_PATH):
		return

	# What the perimeter is made of. Last for the same reason paving was last —
	# a scene inserted before an existing one re-planes shapes in scenes nobody
	# edited — and last for a second reason of its own: it reads `plaza.tscn`,
	# so it must not be the thing that decides whether `plaza.tscn` can load.
	_root = Node3D.new()
	_root.name = "frontage"
	_begin_scene()
	_plaza_frontage()
	if not _save(_root, FRONTAGE_PATH):
		return

	# The fountain, and **last for the same reason paving and frontage are**: the
	# seam seed is handed out five per scene, so a scene inserted anywhere but
	# the end shifts the displacement of every scene after it and puts two
	# untouched shapes on the same plane, in a file nobody edited.
	#
	# It is the scene most exposed to that, too. 270 shapes stacked on one axis
	# is 270 top faces and 270 bottom faces, all concentric, and it is the only
	# object in the park where the coplanar rule is doing continuous work rather
	# than catching the odd corner.
	_root = Node3D.new()
	_root.name = "fountain"
	_begin_scene()
	_fountain()
	if not _save(_root, FOUNTAIN_PATH):
		return

	quit()


func _save(node: Node3D, path: String) -> bool:
	var packed := PackedScene.new()
	var err := packed.pack(node)
	if err != OK:
		push_error("pack failed: %d" % err)
		quit(1)
		return false
	err = ResourceSaver.save(packed, path)
	if err != OK:
		push_error("save failed: %d" % err)
		quit(1)
		return false
	print("wrote %d nodes to %s" % [node.get_child_count(), path])
	return true


# ---------------------------------------------------------------------------
# Ground textures
# ---------------------------------------------------------------------------

## The first textures in the project, and they are generated rather than painted
## for the same reason everything else here is: there is no art yet, and a
## greybox that waits for art gets no ground detail at all.
##
## What they are for is not decoration. A flat-shaded floor gives the eye nothing
## to measure against, so walking across 80m of plaza reads as sliding — there is
## no optical flow, and speed and distance both stop being legible. A joint
## pattern at a known size fixes that, and it is the cheapest thing in the park
## that says how big the park is.
##
## **Two surfaces, and which way round matters.** A real park paves its
## circulation in asphalt and its standing room in brick — the path is the cheap
## hard-wearing thing you walk along and the plaza is the expensive decorative
## thing it crosses. Built the other way round, with pavers on the walkways and
## flat ground either side, the plan reads inside out: the paths look like
## features and the plaza looks like the gap between them.
##
## So the walkways of `ParkPlan.WALKWAYS` are asphalt, and the ground they are
## laid over is brick. That is also what makes them legible at all — dark
## circulation against a warm floor is a stronger read than a lighter grey
## against a slightly different grey, and it is the read the reference parks use.
const TEX_DIR := "res://assets/textures"
const BRICK_ALBEDO_PATH := "res://assets/textures/brick_albedo.res"
const BRICK_NORMAL_PATH := "res://assets/textures/brick_normal.res"
const ASPHALT_ALBEDO_PATH := "res://assets/textures/asphalt_albedo.res"
const ASPHALT_NORMAL_PATH := "res://assets/textures/asphalt_normal.res"

## Decking, twice — once with the boards running east-west and once north-south.
##
## Two files rather than one, because the surface has to carry a direction and
## the material is world-space projected, so there is no way to turn it per
## surface. That direction is the whole reason planking is textured at all. The
## boardwalk cannot show its circulation the way the plaza does — the promenade
## *is* the path, and painting a walkway down the middle of 160m of decking
## would invent a distinction that is not there. What it can do is lay the boards
## across the direction of travel, which reads as "along" from any angle, and
## turn them where the walk turns. The strip changes direction twice, at the
## alley and at the pier, and both are reveals; boards that turn with them say so
## underfoot at the moment it happens.
const PLANK_ALBEDO_PATH := "res://assets/textures/plank_albedo.res"
const PLANK_NORMAL_PATH := "res://assets/textures/plank_normal.res"
const PLANK_X_ALBEDO_PATH := "res://assets/textures/plank_cross_albedo.res"
const PLANK_X_NORMAL_PATH := "res://assets/textures/plank_cross_normal.res"

## A 200x100mm clay paver, which is the real brick, at 512px over 3.2m: 16 across
## and 32 courses, both dividing the tile exactly. That last part is the whole
## trick — a brick that does not fit a whole number of times leaves a ruled line
## every 3.2m, and on open ground that line is the only thing you would see.
##
## 6.25mm to the pixel, so a 10mm joint is 1.6px. Fine, but the smallest the tile
## can go: at 256px the joint is under a pixel and the first mip erases it.
const BRICK_SIZE := 512
const BRICK_METRES := 3.2
const BRICK_COLS := 16
const BRICK_ROWS := 32

## Asphalt has no unit to fit, so it is sized by its grain instead. 512px over 3m
## is 5.9mm to the pixel, which is the coarsest the tile can be and still resolve
## aggregate: a chip is about a centimetre, and at the 256px/4m this started at
## that is under a pixel. Which is exactly how it looked — a flat grey road, the
## same nothing the untextured ground was, only greyer.
const ASPHALT_SIZE := 512
const ASPHALT_METRES := 3.0

## Sixteen 140mm boards over 2.24m, 32px each on a 512px tile. 4.4mm to the
## pixel, so the 6mm gap between boards is a pixel and a half — thin, and the
## thinnest the tile can be and still have the gap survive its own first mip.
const PLANK_SIZE := 512
const PLANK_METRES := 2.24
const PLANK_BOARDS := 16


# ---------------------------------------------------------------------------
# The lit materials
# ---------------------------------------------------------------------------

## The three materials that are allowed to *be* light rather than take it, and
## the only ones in the park written out as their own files.
##
## Everything else in `mats` is an in-memory `StandardMaterial3D`, so each scene
## packs its own copy and two scenes sharing a colour share nothing at runtime.
## That is fine for a bench slat and useless here, because a bulb has to change
## through the evening and there are 196 of them across four scenes. Externalised
## with `FLAG_CHANGE_PATH` — the same trick the ground textures use — one file is
## one resource, Godot's cache hands the same instance to every scene that
## references it, and `park_lights.gd` `load()`s that instance and sets
## `emission_energy_multiplier` on it once. One assignment lights the park.
##
## Which is also why these could not just be `defs` entries with emission turned
## on: `"yellow"` is the festoon bulbs *and* the awning stripes, the flagpole
## pennants and the parasol shades. Emission on that palette entry sets fire to
## every umbrella on the terrace.
const MAT_DIR := "res://assets/materials"
const BULB_MAT_PATH := Plan.BULB_MATERIAL
const LAMP_MAT_PATH := Plan.LAMP_MATERIAL
const EYE_MAT_PATH := Plan.EYE_MATERIAL
const TRIM_MAT_PATH := Plan.TRIM_MATERIAL

## Emission colours, and they are deliberately not the albedo.
##
## A bulb reads as *on* by being warmer than its own daytime colour, not just
## brighter — a lamp that scales its albedo up looks like a white ball in a dark
## park, and a lamp that shifts amber as it brightens looks like a filament. The
## festoon runs are the warmest thing in the park after dark and the promenade
## globes are a half-step cooler, so the strip has two temperatures in it rather
## than one.
const BULB_EMIT := Color(1.0, 0.72, 0.34)
const LAMP_EMIT := Color(1.0, 0.86, 0.62)
const EYE_EMIT := Color(1.0, 0.80, 0.50)

## Cool, and the only cool light in the park. The trim runs along the cascade's
## copings and the whole point is that it reads as *architecture* lit on purpose,
## against a park lit in tungsten — warm everywhere else, cold on the monument.
## Same colour the pavilion takes at the pier head, so the two cool things in the
## west are the two built things worth walking to.
## Saturated well past where it looks right in a swatch, because emission clips
## toward white as it brightens and these are the largest emissive surfaces in
## the park — 40m of coping down each wing, seen flat-on from the head of the
## flight. At (0.60, 0.82, 1.0) the capture came back with two white-hot slabs
## and no colour in them at all; the blue has to be deep enough to survive its
## own brightness.
const TRIM_EMIT := Color(0.24, 0.55, 1.0)


func _build_textures() -> void:
	DirAccess.make_dir_recursive_absolute(TEX_DIR)
	_brick_texture()
	_asphalt_texture()
	_plank_texture()


## Running bond, because stack bond reads as a grid and a grid at this size reads
## as tiling. Height first and albedo derived from it, so the shading and the
## relief cannot disagree about where a joint is.
func _brick_texture() -> void:
	var n := BRICK_SIZE
	var cw := float(n) / float(BRICK_COLS)
	var ch := float(n) / float(BRICK_ROWS)
	var joint := 1.6
	var bevel := 2.0

	var height := PackedFloat32Array()
	height.resize(n * n)
	var albedo := Image.create_empty(n, n, true, Image.FORMAT_RGB8)
	for py in n:
		var fy := float(py) + 0.5
		var row := int(floor(fy / ch))
		var ly := fy - float(row) * ch
		# Every other course shifted half a brick. 32 courses is even, so the
		# shift pattern wraps with the tile.
		var offx := 0.0 if row % 2 == 0 else cw * 0.5
		for px in n:
			var fx := fposmod(float(px) + 0.5 + offx, float(n))
			var col := int(floor(fx / cw))
			var lx := fx - float(col) * cw
			var d: float = min(min(lx, cw - lx), min(ly, ch - ly))
			var h: float = clampf((d - joint * 0.5) / bevel, 0.0, 1.0)
			height[py * n + px] = h

			# Brick varies far more from brick to brick than a cast slab does —
			# it is fired clay and the colour is the kiln — so the per-unit term
			# is wide on purpose. Under it, weathering that ignores the bond, and
			# grit that ignores everything.
			var tone := 0.80 + 0.34 * _hash01(col, row, 7)
			var mottle := 0.92 + 0.16 * _vnoise(float(px) / n, float(py) / n, 6, 11)
			var grit := 0.96 + 0.08 * _hash01(px, py, 3)
			# Mortar is paler and greyer than the brick it holds, so the joint
			# does not just go dark — it goes flat.
			var lit := 0.62 + 0.38 * h
			var v: float = clampf(tone * mottle * grit * lit, 0.0, 1.0)
			albedo.set_pixel(px, py, Color(v, v, v))
	albedo.generate_mipmaps()

	_save_texture(albedo, BRICK_ALBEDO_PATH, false)
	_save_texture(_normal_from(height, n, 2.0), BRICK_NORMAL_PATH, true)


## No unit at all, which is the point: asphalt is legible as asphalt precisely
## because nothing about it repeats at a size you could name. What it has is
## aggregate — pale stones in a dark binder — and blotching from where it was
## laid and what has worn it.
##
## The mean is kept near 0.8 rather than 1.0 so the bright stones have somewhere
## to go. Push the average up and every stone clips to white, which is the same
## as having no stones.
func _asphalt_texture() -> void:
	var n := ASPHALT_SIZE
	var height := PackedFloat32Array()
	height.resize(n * n)
	var albedo := Image.create_empty(n, n, true, Image.FORMAT_RGB8)
	for py in n:
		for px in n:
			var u := float(px) / float(n)
			var v := float(py) / float(n)
			# A 256-lattice on a 512px tile is two pixels a cell, which at this
			# scale is a 12mm chip. That is the real size of the stone in a
			# wearing course, and resolving it is the whole reason for 512.
			var chip := _vnoise(u, v, 256, 41)
			var grain := _hash01(px, py, 43)
			# Relief is deliberately coarser than the chips — 5cm and 20cm, the
			# undulation of a laid surface rather than the stones in it.
			#
			# Both finer attempts were wrong the same way. A height field with
			# per-pixel grain, or with the 12mm chips in it, is white noise as far
			# as the derivative is concerned: no mip level means anything, so it
			# glitters underfoot, and it will not compress — the asphalt normal
			# alone was 765KB of the repository, four times its own albedo. A
			# 1cm stone does not shade at eye height anyway. What does is the
			# dip and swell the roller left.
			height[py * n + px] = 0.7 * _vnoise(u, v, 64, 49) \
				+ 0.3 * _vnoise(u, v, 16, 51)

			var agg := 0.66 + 0.46 * chip
			# The few stones that catch the light. Without this the surface is
			# uniform noise, which reads as static rather than as a road.
			if chip > 0.78:
				agg += (chip - 0.78) * 1.5
			agg *= 0.97 + 0.06 * grain
			# Laid in passes and worn in patches. Kept gentle — asphalt that
			# blotches hard reads as mud, and the 3m repeat would start to show.
			var patch := 0.88 + 0.20 * _vnoise(u, v, 4, 45)
			var wear := 0.94 + 0.12 * _vnoise(u, v, 12, 47)
			var w: float = clampf(agg * patch * wear * 0.86, 0.0, 1.0)
			albedo.set_pixel(px, py, Color(w, w, w))
	albedo.generate_mipmaps()

	_save_texture(albedo, ASPHALT_ALBEDO_PATH, false)
	_save_texture(_normal_from(height, n, 0.9), ASPHALT_NORMAL_PATH, true)


## Weathered decking, generated once and written twice — the second copy
## transposed, which is what gives the pier and the alley boards at right angles
## to the promenade's.
##
## Transposed rather than rotated, and the difference is a mirror. It does not
## matter here because every asymmetry in the pattern is noise, and a mirrored
## random plank is still a random plank. It would matter the moment anything in
## the tile had a handedness — a diagonal, a printed mark — and then this has to
## become a rotation.
##
## Three things make planking read as planking rather than as stripes: the gap,
## which is a shadow and not a line; the butt joint, which is where one board
## stops and the next starts, and is the only thing that says a board has a
## length; and grain, which runs *along* the board and is therefore the one
## anisotropic term in any of these textures.
func _plank_texture() -> void:
	var n := PLANK_SIZE
	var bw := float(n) / float(PLANK_BOARDS)
	var gap := 1.5
	var bevel := 1.5

	var height := PackedFloat32Array()
	height.resize(n * n)
	var albedo := Image.create_empty(n, n, true, Image.FORMAT_RGB8)
	# `a` runs along the board, `b` across it. Everything below is written in
	# those terms and the mapping to pixels happens once, here, so the transpose
	# at the end is the only place the two orientations differ.
	for py in n:
		for px in n:
			var a := float(px) + 0.5
			var b := float(py) + 0.5
			var board := int(floor(b / bw))
			var across := b - float(board) * bw

			# The gap between boards, and the one butt joint on this board. The
			# joint sits at a per-board position so the ends do not line up into
			# a seam across the deck, which is the thing carpenters stagger to
			# avoid and the thing that makes a repeating tile obvious.
			var d_edge: float = min(across, bw - across)
			var joint_at := _hash01(board, 0, 61) * float(n)
			var d_joint := absf(fposmod(a - joint_at + float(n) * 0.5, float(n))
				- float(n) * 0.5)
			var h: float = clampf((d_edge - gap * 0.5) / bevel, 0.0, 1.0)
			h = minf(h, clampf((d_joint - 1.0) / bevel, 0.0, 1.0) * 0.4 + 0.6)
			# A shallow crown across each board, so a low sun catches the middle
			# of every one of them and the deck reads as boards from fifty metres
			# where the gaps have long since mipped away.
			h += 0.10 * sin(PI * across / bw)

			# Grain: slow along the board, fast across it. Phase-shifted per
			# board so no two are the same piece of wood.
			var ua := (a / float(n)) + float(board) * 0.137
			var ub := b / float(n)
			var grain := 0.6 * _vnoise2(ua, ub, 4, 128, 71) \
				+ 0.4 * _vnoise2(ua, ub, 12, 48, 73)
			height[py * n + px] = h + grain * 0.12

			# Weathered boards vary widely board to board — they were cut from
			# different trees and replaced in different decades.
			var tone := 0.78 + 0.34 * _hash01(board, 0, 63)
			var wear := 0.94 + 0.12 * _vnoise2(ua, ub, 3, 5, 75)
			var lit := 0.30 + 0.70 * clampf(h, 0.0, 1.0)
			var v: float = clampf(tone * wear * lit * (0.82 + 0.30 * grain),
				0.0, 1.0)
			albedo.set_pixel(px, py, Color(v, v, v))
	albedo.generate_mipmaps()

	# The cross-grain copy is built from a transposed *height field* rather than
	# by transposing the finished normal map. R and G encode the derivative along
	# U and V, so swapping the image's axes without swapping those two channels
	# produces a map whose relief runs one way and whose lighting runs the other
	# — grooves lit from along their own length, which reads as a smeared sheen
	# and not as anything.
	var height_t := PackedFloat32Array()
	height_t.resize(n * n)
	for py in n:
		for px in n:
			height_t[py * n + px] = height[px * n + py]

	_save_texture(albedo, PLANK_ALBEDO_PATH, false)
	_save_texture(_normal_from(height, n, 1.6), PLANK_NORMAL_PATH, true)
	_save_texture(_transposed(albedo), PLANK_X_ALBEDO_PATH, false)
	_save_texture(_normal_from(height_t, n, 1.6), PLANK_X_NORMAL_PATH, true)


## The same image with its two axes swapped. Mips are regenerated rather than
## transposed, because `get_pixel` only reads mip zero and a texture whose mips
## came from somewhere else is a texture that changes pattern with distance.
func _transposed(src: Image) -> Image:
	var n := src.get_width()
	var flat := src.duplicate() as Image
	flat.clear_mipmaps()
	var out := Image.create_empty(n, n, true, src.get_format())
	for py in n:
		for px in n:
			out.set_pixel(px, py, flat.get_pixel(py, px))
	out.generate_mipmaps()
	return out


## Central differences on a height field, wrapped, so the normal map tiles with
## the albedo instead of flattening at the tile edge.
func _normal_from(height: PackedFloat32Array, n: int, strength: float) -> Image:
	var normal := Image.create_empty(n, n, true, Image.FORMAT_RGB8)
	for py in n:
		for px in n:
			var l := height[py * n + posmod(px - 1, n)]
			var r := height[py * n + posmod(px + 1, n)]
			var u := height[posmod(py - 1, n) * n + px]
			var d := height[posmod(py + 1, n) * n + px]
			var vec := Vector3(-(r - l) * strength, -(d - u) * strength, 1.0).normalized()
			normal.set_pixel(px, py, Color(vec.x * 0.5 + 0.5, vec.y * 0.5 + 0.5,
				vec.z * 0.5 + 0.5))
	normal.generate_mipmaps()
	return normal


## Written as `.res` rather than `.png` on purpose. A PNG is an *imported* asset:
## it needs an editor pass to produce the `.import` file and the compressed
## texture beside it, so a generator that emits one writes something the next
## `--script` run cannot load. A `PortableCompressedTexture2D` saved as a native
## resource carries its own pixels and loads with no import step at all, which
## keeps the whole park one command to rebuild.
##
## Saved with `FLAG_CHANGE_PATH` so the texture in hand becomes the one on disk.
## Without it the in-memory copy stays pathless, every scene that uses it packs
## its own base64 duplicate, and the same tile lands several times in the
## repository as text.
##
## `keep_compressed_buffer` is the fifth way the tooling lies, and it is the same
## shape as the other four: it fails by succeeding. Outside the editor the class
## throws the compressed bytes away as soon as the GPU has them, because nothing
## at runtime is going to re-save a texture. So `ResourceSaver.save` returns OK
## and writes a well-formed 360-byte resource with no pixels in it, `load()`
## returns a texture object, the material accepts it, and the ground is untextured
## for a reason nothing anywhere reports. Held open, the same call writes 100KB.
func _save_texture(img: Image, path: String, is_normal: bool) -> void:
	var tex := PortableCompressedTexture2D.new()
	tex.keep_compressed_buffer = true
	tex.create_from_image(img, PortableCompressedTexture2D.COMPRESSION_MODE_LOSSLESS,
		is_normal)
	var err := ResourceSaver.save(tex, path, ResourceSaver.FLAG_CHANGE_PATH)
	if err != OK:
		push_error("texture save failed: %s (%d)" % [path, err])
		quit(1)
		return
	# Read back rather than trust the byte count. A grid of grooves is nearly all
	# flat, so the normal map losslessly compresses to about 2KB and any size
	# threshold big enough to catch the empty stub also rejects it. Dimensions
	# are the honest test: the stub reports none.
	var back := ResourceLoader.load(path, "", ResourceLoader.CACHE_MODE_IGNORE) as Texture2D
	if back == null or back.get_width() != img.get_width():
		push_error("texture %s came back %s — the pixels did not make it"
			% [path, "null" if back == null else str(back.get_size())])
		quit(1)
		return
	print("wrote %dx%d, %d mips, %d bytes to %s" % [img.get_width(), img.get_height(),
		img.get_mipmap_count(), FileAccess.get_file_as_bytes(path).size(), path])


## A stable 0..1 from a pair of integers. Deterministic across runs, which
## matters: the generator is re-run constantly and a texture that changed every
## time would put a new blob in the diff for every unrelated edit.
func _hash01(x: int, y: int, salt: int) -> float:
	var h := (x * 374761393 + y * 668265263 + salt * 2246822519) & 0x7fffffff
	h = ((h ^ (h >> 13)) * 1274126177) & 0x7fffffff
	return float(h % 65536) / 65535.0


## Value noise on a `g`x`g` lattice, wrapping at the tile edge.
func _vnoise(u: float, v: float, g: int, salt: int) -> float:
	return _vnoise2(u, v, g, g, salt)


## The same, with a different lattice count on each axis — which is the only way
## to get grain. Wood is the one surface here that is not the same in both
## directions: slow along the board and fast across it is what makes a streak
## instead of a blotch.
func _vnoise2(u: float, v: float, gx: int, gy: int, salt: int) -> float:
	var fx := u * float(gx)
	var fy := v * float(gy)
	var x0 := int(floor(fx))
	var y0 := int(floor(fy))
	var tx := fx - float(x0)
	var ty := fy - float(y0)
	tx = tx * tx * (3.0 - 2.0 * tx)
	ty = ty * ty * (3.0 - 2.0 * ty)
	var a := _hash01(posmod(x0, gx), posmod(y0, gy), salt)
	var b := _hash01(posmod(x0 + 1, gx), posmod(y0, gy), salt)
	var c := _hash01(posmod(x0, gx), posmod(y0 + 1, gy), salt)
	var d := _hash01(posmod(x0 + 1, gx), posmod(y0 + 1, gy), salt)
	return lerp(lerp(a, b, tx), lerp(c, d, tx), ty)


func _build_materials() -> void:
	var defs := {
		"wood": [Color(0.55, 0.42, 0.3), 0.9, 0.0],
		"metal": [Color(0.3, 0.31, 0.33), 0.55, 0.2],
		"white": [Color(0.87, 0.86, 0.82), 0.8, 0.0],
		"red": [Color(0.84, 0.27, 0.24), 0.7, 0.0],
		"yellow": [Color(0.93, 0.76, 0.24), 0.7, 0.0],
		"blue": [Color(0.27, 0.5, 0.72), 0.7, 0.0],
		"accent": [Color(0.78, 0.54, 0.42), 0.85, 0.0],
		# The perimeter's own masonry. Matches `mat_building` in `plaza.tscn`
		# exactly and has to: parapets and pediments are the wall carrying on
		# upward, and a shade out reads as a different building stacked on top.
		"building": [Color(0.72, 0.71, 0.69), 0.9, 0.0],
		# Washed toward the sky so distance reads without touching the environment.
		"far": [Color(0.66, 0.68, 0.72), 0.95, 0.0],
		"far_warm": [Color(0.72, 0.66, 0.63), 0.95, 0.0],
		"far_shade": [Color(0.55, 0.56, 0.62), 0.95, 0.0],
		# The one surface in the park that is supposed to be shiny. Low roughness
		# is the whole point: it is what turns a low sun into a glitter path, and
		# the reason the boardwalk went west in the first place.
		"water": [Color(0.34, 0.44, 0.52), 0.08, 0.1],
		# Shop glazing. Dark and a little slick, so a bay reads as a window
		# rather than as a differently-coloured piece of the same wall.
		"glass": [Color(0.2, 0.24, 0.29), 0.25, 0.0],
		# Awnings and the stripes on things. Saturated on purpose: the boardwalk is
		# the one section allowed to be loud, and it is what the late sun hits.
		"canvas": [Color(0.86, 0.4, 0.33), 0.85, 0.0],
		"canvas_alt": [Color(0.35, 0.55, 0.66), 0.85, 0.0],
		# The only green in the park, and it earns the exception: a canopy in
		# the grey palette reads as a boulder on a stick. Dusty olive rather
		# than leaf, so it sits with everything else rather than shouting.
		"foliage": [Color(0.5, 0.56, 0.42), 0.95, 0.0],
		# Planting, and the one place the park is allowed flowers. The cascade's
		# terraces are the reason it reads as a garden rather than as civil
		# engineering, so these are saturated where `foliage` is dusty.
		"planting": [Color(0.36, 0.47, 0.31), 0.95, 0.0],
		"bloom_warm": [Color(0.88, 0.62, 0.28), 0.9, 0.0],
		"bloom_pink": [Color(0.84, 0.46, 0.55), 0.9, 0.0],
		"bloom_pale": [Color(0.93, 0.9, 0.76), 0.9, 0.0],
	}
	for key in defs:
		var m := StandardMaterial3D.new()
		m.albedo_color = defs[key][0]
		m.roughness = defs[key][1]
		m.metallic = defs[key][2]
		mats[key] = m

	# The two ground surfaces. Brick is warm and a little dusty rather than new
	# terracotta — a park floor has had twenty summers on it.
	#
	# Asphalt is dark, and the first pass had it far too light on the theory that
	# faded asphalt is grey rather than black. It is, but "grey" in the sun is
	# still about a quarter of the light back, and 0.45 put the street somewhere
	# between concrete and dust. Under a bright sky the tint has to sit well
	# below where the surface looks right on paper.
	mats["brick"] = _ground_material(Color(0.64, 0.50, 0.43),
		BRICK_ALBEDO_PATH, BRICK_NORMAL_PATH, BRICK_METRES, 0.6, 0.94)
	mats["asphalt"] = _ground_material(Color(0.27, 0.268, 0.265),
		ASPHALT_ALBEDO_PATH, ASPHALT_NORMAL_PATH, ASPHALT_METRES, 0.9, 0.97)

	# Decking, in the two directions boards run down there. Greyer and cooler
	# than `wood`, which is furniture: planking that has had weather on it is not
	# the colour of a bench slat, and the promenade is 17m wide, so getting it
	# wrong is 2,700m² of wrong.
	#
	# Which one a surface takes is decided by which way you walk over it, not by
	# where it is — see `_boardwalk_paving`.
	mats["plank"] = _ground_material(Color(0.68, 0.62, 0.54),
		PLANK_ALBEDO_PATH, PLANK_NORMAL_PATH, PLANK_METRES, 0.8, 0.95)
	mats["plank_cross"] = _ground_material(Color(0.68, 0.62, 0.54),
		PLANK_X_ALBEDO_PATH, PLANK_X_NORMAL_PATH, PLANK_METRES, 0.8, 0.95)

	# The three that light up. Saved to disk, then loaded back — see MAT_DIR.
	DirAccess.make_dir_recursive_absolute(MAT_DIR)
	mats["bulb"] = _lit_material(Color(0.96, 0.88, 0.66), BULB_EMIT, BULB_MAT_PATH)
	mats["lamp_glass"] = _lit_material(Color(0.92, 0.90, 0.84), LAMP_EMIT, LAMP_MAT_PATH)
	mats["eye"] = _lit_material(Color(0.90, 0.88, 0.82), EYE_EMIT, EYE_MAT_PATH)
	# Albedo matched to `white`, because the trim is coping stone by day and has
	# to sit in the daylight palette exactly where it did before it could glow.
	mats["trim"] = _lit_material(Color(0.87, 0.86, 0.82), TRIM_EMIT, TRIM_MAT_PATH)

	_fountain_materials()


## The fountain's palette, and the only shaders in the park.
##
## Two stones and one metal first. The plaza's masonry is `building` at 0.72 grey
## and the fountain used to be that plus `accent`, alternating drum by drum,
## which is what made it read as a cake: the bands were the loudest thing about
## it and they went with the layers rather than across them. So the fountain gets
## its own two, close enough together that the *profile* is what separates the
## parts and not the colour — a dry stone and the same stone permanently wet,
## which is the honest difference between a basin's outside and its inside.
##
## Then the water. `mats["water"]` already exists and is the sea: flat, 0.08
## rough, and completely correct for 340m of shore seen from a bluff. It is
## useless for a fountain, because at three metres what says *water* is that it
## is moving, and a `StandardMaterial3D` cannot move.
##
## Both shaders are loaded from `res://assets/shaders`, which is safe under
## `--script` for the same reason the ground textures are safe as `.res`: a
## `.gdshader` is not an *imported* asset. It has no `.import` sidecar and no
## editor pass standing between the file and `load()`, so the park stays one
## command to rebuild.
##
## Four instances of two shaders rather than four shaders, because the uniforms
## are the whole difference: a basin is the pool with a shorter wavelength, and a
## jet is a sheet with its flow running the other way.
const POOL_SHADER_PATH := "res://assets/shaders/water_pool.gdshader"
const FALL_SHADER_PATH := "res://assets/shaders/water_fall.gdshader"


func _fountain_materials() -> void:
	# Warm limestone, and the warmth is the point rather than a preference. The
	# first build made this 0.74/0.72/0.68, which is `building` to within two
	# percent — so the fountain was a pale grey object standing against a
	# hundred and twenty metres of pale grey perimeter and did not separate from
	# it at any distance. The old fountain got away with the same value only
	# because half of it was `accent` salmon, which is the banding this rebuild
	# exists to remove; the fix is to move the *whole* object off the wall's
	# hue instead of striping it.
	mats["fount_stone"] = _plain(Color(0.72, 0.66, 0.57), 0.88, 0.0)
	# The wetted stone. Darker and much less rough, because that is what water
	# actually does to masonry, and it is the cheapest possible way to say which
	# surfaces the water has been over without drawing a stain on anything.
	mats["fount_wet"] = _plain(Color(0.48, 0.45, 0.40), 0.35, 0.0)
	mats["fount_bronze"] = _plain(Color(0.42, 0.40, 0.30), 0.45, 0.55)
	# The pool floor. Never really seen — the water above it is opaque — but a
	# fountain with nothing under its water is a fountain you can see the plaza
	# through from the one angle nobody checked.
	mats["fount_bed"] = _plain(Color(0.16, 0.26, 0.27), 0.8, 0.0)

	var pool := load(POOL_SHADER_PATH) as Shader
	var fall := load(FALL_SHADER_PATH) as Shader
	if pool == null or fall == null:
		push_error("gen_props: the water shaders did not load — the fountain "
			+ "would be built out of null materials")
		quit(1)
		return

	mats["water_pool"] = _shader_material(pool, {
		"tint": Color(0.10, 0.24, 0.28),
		"centre": Vector3(Plan.FOUNTAIN_AT.x, 0.0, Plan.FOUNTAIN_AT.y),
		"ring_scale": 1.0,
		"chop": 1.0,
		"rough": 0.06,
	})
	# The basins are 8m and 4m across against the pool's 17, so they take the
	# rings four and eight times as tight. At the pool's wavelength a basin has
	# one and a half waves on it, which does not read as water at all — it reads
	# as a dent.
	mats["water_basin"] = _shader_material(pool, {
		"tint": Color(0.13, 0.28, 0.31),
		"centre": Vector3(Plan.FOUNTAIN_AT.x, 0.0, Plan.FOUNTAIN_AT.y),
		"ring_scale": 4.5,
		"chop": 3.0,
		"rough": 0.05,
	})
	# `streaks` is radians per world metre, so it has to be read against how wide
	# the thing wearing it is. The falls take 64 and 80 where the jets take 34,
	# and that is not a taste difference: at 26 a rope is 24cm and a fall is
	# 36cm wide, so each fall came out as one translucent rod hanging off a
	# basin. At 64 the same fall has five ropes in it and reads as a curtain. A
	# jet is 15cm through and genuinely *is* one rope, so it keeps the low number.
	#
	# The two sheets. Heavy, slow, falling, and each faded over its own drop —
	# which is why they are two materials and not one. `fade_from` is the lip and
	# `fade_to` is a little above whatever the sheet lands in, so the last of the
	# fall is gone before it arrives and the froth ring takes the landing. That
	# is the trick that lets a veil run the full height of its drop: a sheet that
	# stopped in mid-air would read as a modelling mistake, and one drawn at full
	# strength all the way down reads as a glass tube.
	mats["water_veil_lo"] = _shader_material(fall, {
		"flow": 2.4, "streaks": 64.0, "grain": 2.2,
		"base_alpha": 0.30, "glow": 0.30,
		"fade_from": 3.16, "fade_to": 0.55,
	})
	mats["water_veil_hi"] = _shader_material(fall, {
		"flow": 2.6, "streaks": 80.0, "grain": 2.6,
		"base_alpha": 0.32, "glow": 0.32,
		"fade_from": 5.33, "fade_to": 3.45,
	})
	# Jets and the plume: the same substance with the flow reversed, thinner, and
	# breaking up faster the higher it gets.
	mats["water_jet"] = _shader_material(fall, {
		"flow": -4.2, "streaks": 34.0, "grain": 3.4,
		"base_alpha": 0.36, "glow": 0.45,
	})
	# The plume fades the other way — out at the *top*. It is the only part of
	# the fountain visible from the gate, and without this it ends in a flat disc
	# against the sky fifty-seven metres up the street.
	mats["water_plume"] = _shader_material(fall, {
		"flow": -4.8, "streaks": 30.0, "grain": 3.0,
		"base_alpha": 0.44, "glow": 0.55,
		"fade_from": 6.30, "fade_to": 7.95,
	})
	# What comes back down around the plume. Very faint, because two concentric
	# translucent drums at any real opacity are the wedding cake this rebuild
	# exists to stop being.
	mats["water_spray"] = _shader_material(fall, {
		"flow": 2.0, "streaks": 16.0, "grain": 1.8,
		"base_alpha": 0.13, "glow": 0.40,
		"fade_from": 6.60, "fade_to": 5.40,
	})
	# Froth. The pool shader rather than the fall shader, and that is not a
	# detail: `water_fall` travels by *height*, so on a flat horizontal patch
	# every fragment shares one value and the whole ring pulses in unison. The
	# pool shader travels across the surface, which is what froth does.
	mats["water_foam"] = _shader_material(pool, {
		"tint": Color(0.48, 0.63, 0.66),
		"centre": Vector3(Plan.FOUNTAIN_AT.x, 0.0, Plan.FOUNTAIN_AT.y),
		"ring_scale": 9.0,
		"chop": 7.0,
		"rough": 0.22,
		"spec": 0.7,
	})


func _plain(albedo: Color, roughness: float, metallic: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = albedo
	m.roughness = roughness
	m.metallic = metallic
	return m


## One `ShaderMaterial` per uniform set. Shared by every part that takes it, so
## the packed scene carries one copy and not one per node.
func _shader_material(shader: Shader, params: Dictionary) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = shader
	for key in params:
		m.set_shader_parameter(key, params[key])
	return m


## World-space triplanar rather than the surface's own UVs, and that is the whole
## reason this is one material instead of forty.
##
## A walkway is one quad per segment at whatever length the segment happens to
## be, so quad UVs would give every segment its own tiling rate and every joint
## in the polyline a visible break in the pattern. Projected from world position
## the pattern is continuous across the entire park, and two quads meeting at a
## corner line up because they are reading the same grid rather than each
## starting one. The same applies to the brick: the plaza's floor, the street's
## and the apron's are three separate slabs and one continuous bond.
func _ground_material(tint: Color, albedo_path: String, normal_path: String,
		metres: float, normal_scale: float, roughness: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = tint
	m.albedo_texture = load(albedo_path)
	m.normal_enabled = true
	m.normal_texture = load(normal_path)
	m.normal_scale = normal_scale
	m.roughness = roughness
	m.uv1_triplanar = true
	m.uv1_world_triplanar = true
	m.uv1_scale = Vector3.ONE / metres
	# Anisotropic, not because it is prettier but because a ground plane is seen
	# almost edge-on for most of its area, and trilinear alone turns the far half
	# of the plaza into flat grey.
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	return m


## A material that can be switched on, written to `path` and loaded back from it.
##
## Emission is left *enabled* and its multiplier left at zero rather than the
## flag being off, and that is the whole reason this works at runtime. Godot
## compiles `emission_enabled` into the shader; flipping it recompiles, so a
## park that turned its lights on at dusk by setting the flag would hitch on the
## one frame the player is most likely to be looking at the sky. The multiplier
## is a uniform, so sliding it from 0 to 1 over the twilight costs nothing and
## can be done every frame.
##
## At zero the surface is exactly its albedo, which is what a bulb in daylight
## is: a pale glass ball. Nothing about the day changes.
##
## The load-back is not a paranoia check like the texture one — a material has no
## buffer to drop. It is what makes the *identity* work: `ResourceSaver` with
## `FLAG_CHANGE_PATH` gives the in-hand copy a path, and `ResourceLoader` then
## returns that same cached instance to everyone who asks for the path later,
## including the running game. Skipping it leaves the generator holding an object
## whose path says one thing and whose cache entry does not exist.
func _lit_material(albedo: Color, emit: Color, path: String) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = albedo
	m.roughness = 0.45
	m.metallic = 0.0
	m.emission_enabled = true
	m.emission = emit
	m.emission_energy_multiplier = 0.0
	# A bulb is a light source, so it should not be shaded like a solid. Unshaded
	# would be wrong the other way — it would glow flat at noon — so this keeps
	# the daytime shading and only lifts the shadowed side, which is where a real
	# frosted globe picks up its own scatter.
	m.disable_ambient_light = false
	var err := ResourceSaver.save(m, path, ResourceSaver.FLAG_CHANGE_PATH)
	if err != OK:
		push_error("material save failed: %s (%d)" % [path, err])
		quit(1)
		return m
	var back := ResourceLoader.load(path) as StandardMaterial3D
	if back == null:
		push_error("material %s did not load back" % path)
		quit(1)
		return m
	return back


## Rotation about Y, then a tilt about the object's own X. Engine maths only.
func _xform(theta: float, phi: float, origin: Vector3) -> Transform3D:
	var t := Transform3D.IDENTITY.rotated(Vector3.UP, theta)
	if not is_zero_approx(phi):
		t = t.rotated_local(Vector3.RIGHT, phi)
	t.origin = origin
	return t


## Place a part sitting at `local` within an assembly whose base is at `base`
## and which is turned by `theta`. The offset uses the same rotation the part
## does, so parts cannot drift away from each other.
##
## When the plaza is being dilated the *base* moves and the offsets do not,
## which is the whole reason this indirection is worth having: every prop in the
## plaza is an assembly of parts hung off one base, so moving bases moves
## assemblies rigidly. Dilating each emitted part instead would stretch a bench
## away from its own legs.
func _place(base: Vector3, local: Vector3, theta: float) -> Vector3:
	return _plaza_out(base) + Basis(Vector3.UP, theta) * local


## True only while the plaza's prop scene is being built. Nothing else in the
## park is dilated — the west and the boardwalk moved by a flat translation, and
## the passages are laid out from the plan directly.
var _dilate_plaza := false


## How far the prop being built now has to stand clear of the paving, or 0 to
## leave it where it is written.
##
## Set around a group and cleared after, the way `_dilate_plaza` is. It is a
## property of the *prop* rather than of the plaza — a bench wants a metre and a
## bollard wants to be in the road — so it cannot live in the map.
var _stand_clear := 0.0


## The map itself lives in `ParkPlan`, because `gen_crowd.gd` needs the same one
## to know where these props ended up.
##
## This is handed an assembly's **base** and only its base — `_place` adds the
## part offsets afterwards — so pushing here moves a prop rigidly, and every part
## of it gets the same answer because the input is the same point every time.
func _plaza_out(p: Vector3) -> Vector3:
	var q := Plan.plaza_out(p) if _dilate_plaza else p
	if _stand_clear <= 0.0:
		return q
	var c := Plan.clear_of_walkways(Vector2(q.x, q.z), _stand_clear)
	_note_stood(c, _stand_clear)
	return Vector3(c.x, q.y, c.y)


## Where the plaza's hand-placed props actually finished, for the scatter that
## comes after them to sample against.
##
## Only the ones that were **pushed** are in here, and that is the whole point:
## a prop written where it stands can be avoided by reading the source, and a
## prop pushed off the paving cannot. Recorded from `_plaza_out` rather than by
## each caller so a group added later cannot forget to.
var _stood: Array = []


func _note_stood(at: Vector2, r: float) -> void:
	for o in _stood:
		if at.distance_to(o["at"]) < 0.01:
			o["r"] = maxf(float(o["r"]), r)
			return
	_stood.append({"at": at, "r": r})


## How far apart two shapes' faces have to be before the depth buffer can tell
## them apart, and how many distinct offsets there are to hand out. Reverse-Z
## with a float depth buffer resolves a few microns at forty metres, so a
## quarter of a millimetre is about a thousand times what is needed — small
## enough that nothing moves anywhere a player could see, large enough that it
## can never be a close call.
## 21 rather than a round 16 because the ring only fails when two shapes that
## meet are an exact multiple of it apart in build order, and assemblies are
## built in runs of even length — a power of two lines those runs up, and an
## odd number that shares no factor with them does not.
const SEAM_STEP := 0.00025
const SEAM_STEPS := 21

## Handed out in build order, which is what makes this work: the shapes that
## overlap are the ones assembled together, so they are always within a few of
## each other and never collide.
##
## **Re-seeded at the start of every scene, and not to zero.**
##
## It used to run straight through the generator, which made a scene's
## displacements depend on how many nodes every earlier scene happened to emit —
## so adding the three west scenes shifted the ordinals in `thresholds.tscn`,
## four scenes later and untouched, and landed a bulkhead and a door on the same
## plane. A failure in a file nothing had edited is the worst possible place to
## go looking for one.
##
## Resetting to zero fixes that and breaks something worse: scenes that *are*
## mounted together — `west_shell` under `boardwalk`, the stair under the plaza —
## then all start from the same offset, and their first few shapes get identical
## displacement. That put 97m² of bluff face against 97m² of bluff infill on
## exactly the same plane, which is the largest z-fight this project has had.
##
## So each scene gets its own seed, five apart. Five is coprime with 21, so eight
## scenes land on eight distinct offsets, and a scene's seams stay a function of
## that scene alone.
var _seam_ordinal := 0
var _scene_seed := 0


func _begin_scene() -> void:
	# No prop group spans two scenes, so a margin still set when a scene ends is
	# a `_stand_clear = 0.0` somebody forgot — and it would silently push the
	# west's props against the *plaza's* walkways, forty metres away and one
	# section over. Cleared here rather than trusted.
	_stand_clear = 0.0
	_seam_ordinal = _scene_seed
	_scene_seed = (_scene_seed + 5) % SEAM_STEPS


## Everything generated goes through here, which is the point. Shapes are meant
## to overlap — a coplanar butt leaves a zero-width seam for the capsule to
## catch on, so parts run into each other rather than meeting edge to edge. What
## they must not also do is *share a plane*: two faces pointing the same way at
## the same depth is z-fighting, and it is the vibration in the ground.
##
## GROUND_SEAM settled that one plane by hand. There turned out to be 394 of
## them, because the mistake is not really about the ground: anything built to
## the same height as the thing it overlaps shares its top and its bottom, and
## every wall corner in the park is two boxes 3m tall crossing at the corner.
##
## So the rule moves up a level. Overlaps stay; sharing a plane stops. Each
## shape is displaced by a hair nobody will ever see, and no two shapes that
## meet get the same hair.
func _add(node: Node3D, nm: String) -> void:
	node.name = nm
	var t := node.transform
	t.origin += Vector3.ONE * float(_seam_ordinal % SEAM_STEPS) * SEAM_STEP
	node.transform = t
	_seam_ordinal += 1
	_root.add_child(node)
	node.owner = _root


## Loaded on first use rather than preloaded, and that is not a style choice.
##
## This file is run with `--script`, which compiles it before the project's
## autoloads are registered. `section_gate.gd` names `ParkSections`, so a
## compile-time `preload` of it resolves to a script that never finished
## compiling — and the failure is silent in the worst way: the constant is not
## null, `set_script` accepts it and does nothing, `set("role", …)` writes to a
## property that does not exist, and the generator cheerfully emits bare
## `Area3D`s with no script and no gates on them. Which is what it did.
##
## By the time `_initialize` runs the autoloads exist and an ordinary `load`
## compiles cleanly. Anything here that touches a script naming an autoload has
## to be loaded late for the same reason.
var _section_gate: Script = null


func _gate_script() -> Script:
	if _section_gate == null:
		_section_gate = load("res://scenes/world/section_gate.gd")
	return _section_gate

## Added without the seam displacement `_add` applies. That offset exists to
## stop two CSG surfaces sharing a plane; a trigger volume and a spawn point are
## neither, and a marker the player is placed on wants to be exactly where it
## says it is.
func _attach(node: Node3D, nm: String) -> void:
	node.name = nm
	_root.add_child(node)
	node.owner = _root


## Mask 2, not the default 1. The player is on the "people" layer — layer 1 is
## the world, and a gate watching for the world fires on the ground it is
## standing on, or on nothing at all.
func _gate_area(nm: String, at: Vector3, size: Vector3, role: int,
		leads: StringName, belongs := &"plaza",
		hold_from := Vector3.ZERO, hold_look := Vector3.ZERO,
		hold_walk := Vector3.ZERO, hold_seconds := 0.0) -> void:
	var area := Area3D.new()
	area.position = at
	area.collision_layer = 0
	area.collision_mask = 2
	area.set_script(_gate_script())
	if area.get_script() == null:
		push_error("gen_props: section_gate.gd did not compile — '%s' would be a bare Area3D" % nm)
		return
	area.set("role", role)
	area.set("leads_to", leads)
	area.set("belongs_to", belongs)
	area.set("hold_from", hold_from)
	area.set("hold_look", hold_look)
	area.set("hold_walk", hold_walk)
	area.set("hold_seconds", hold_seconds)
	_attach(area, nm)

	var box := BoxShape3D.new()
	box.size = size
	var shape := CollisionShape3D.new()
	shape.shape = box
	shape.name = "shape"
	area.add_child(shape)
	shape.owner = _root


## Where `ParkSections` puts the player down coming the other way. Emitting this
## is what lets the hand-written fallback in `park_sections.gd` be deleted — a
## marker generated alongside the stair moves when the stair moves.
func _marker(nm: String, at: Vector3, yaw: float) -> void:
	var m := Marker3D.new()
	m.position = at
	m.rotation.y = yaw
	_attach(m, nm)


# ---------------------------------------------------------------------------
# Lights
# ---------------------------------------------------------------------------

## The group and the three kinds are the plan's, not this file's — they are a
## contract between this generator and `park_lights.gd`, which reads back out of
## the scenes written here. Aliased rather than used through `Plan.` at every
## call site only because these appear as default arguments about forty times.
const LIGHT_GROUP := Plan.LIGHT_GROUP
const LIGHT_FIXTURE := Plan.LIGHT_FIXTURE
const LIGHT_FEATURE := Plan.LIGHT_FEATURE
const LIGHT_SERVICE := Plan.LIGHT_SERVICE

## The park's lamps are tungsten and its floodlighting is not, and that gap is
## most of what makes uplighting read as *staged* rather than as more lamps.
const LIGHT_TINTS := {
	"warm": Color(1.0, 0.78, 0.48),
	"lamp": Color(1.0, 0.88, 0.68),
	# Floodlighting, a touch cooler than the lamps so a washed wall separates
	# from the pool of light at its foot instead of merging with it.
	"wash": Color(1.0, 0.92, 0.80),
	# The two on the boardwalk that are allowed to be a colour. A midway after
	# dark is not a white place, and the wheel and the pavilion are the two
	# things down there whose whole job is to be looked at from far away.
	"rose": Color(1.0, 0.62, 0.58),
	"cyan": Color(0.62, 0.86, 1.0),
	# The cascade's pair, and they only mean anything together. Drama in
	# architectural lighting is contrast rather than quantity: the first pass put
	# one near-white `wash` on every surface of the monument at moderate energy,
	# which is the most even and least dramatic thing available. Splitting it
	# gives the eye something to separate — cold on the stone that holds the
	# silhouette, warm on the ground people actually walk down.
	"moon": Color(0.55, 0.72, 1.0),
	"amber": Color(1.0, 0.63, 0.26),
	# For uplighting foliage, and pushed green because the target is not white.
	# `foliage` is a dusty olive chosen so a canopy does not read as a boulder on
	# a stick, and a warm lamp on a desaturated olive gives back a brown mass. A
	# light with green in it puts the green back and the crown reads as leaves.
	"foliage_up": Color(0.72, 1.0, 0.62),
}


## A pool of light hung on a fixture.
##
## Shadows default off and that is the important default. A shadow-casting omni
## costs a cubemap render per frame, and the park wants ~90 of these; the ones
## that earn a shadow are the few the player walks directly under. Everything
## else is filling in a floor that already has ambient on it.
##
## `_attach` rather than `_add`, so no seam displacement — that offset exists to
## stop two CSG faces sharing a plane, and a light is not a surface. It is the
## same reason gates and markers use it.
func _omni(nm: String, at: Vector3, tint: String, energy: float, rng: float,
		kind := LIGHT_FIXTURE, shadow := false) -> void:
	var l := OmniLight3D.new()
	l.position = at
	l.light_color = LIGHT_TINTS[tint]
	l.light_energy = energy
	l.omni_range = rng
	# Above 1.0 the falloff is steeper than physical, which is what a lamp pool
	# wants: a bright disc under the post that gives out well before the next
	# post's does. Linear falloff over a 14m range makes the whole plaza an even
	# grey and there is no point having lamps at all.
	l.omni_attenuation = 1.6
	l.light_specular = 0.4
	l.shadow_enabled = shadow
	if shadow:
		l.shadow_bias = 0.04
	_light(l, nm, energy, kind)


## Uplighting. A spot at the foot of something, pointed up it.
##
## The angle is wide and the range is long, which is the opposite of how a spot
## is usually set: this is not a beam picking out an object, it is a wash raking
## a face from below. What sells it is that the source sits *close* to the
## surface — a floodlight two metres out from a wall grazes it and every string
## course and window reveal on `plaza_frontage.tscn` throws a shadow up the
## building. The same fitting six metres out just makes the wall evenly bright,
## which is worth nothing.
##
## `Basis.looking_at` rather than `look_at`, because the node is not in a tree
## yet and `look_at` needs global transforms. It also cannot be handed an up
## vector parallel to its aim, and these aim very nearly straight up — hence the
## fallback. Without it every genuinely vertical uplight in the park comes out
## with a zero basis and lights nothing.
func _uplight(nm: String, at: Vector3, aim: Vector3, tint: String, energy: float,
		rng: float, degrees: float, kind := LIGHT_FEATURE, shadow := false) -> void:
	var dir := aim - at
	if dir.length_squared() < 0.0001:
		push_error("uplight '%s' aims at its own position" % nm)
		return
	dir = dir.normalized()
	var up := Vector3.UP if absf(dir.dot(Vector3.UP)) < 0.98 else Vector3.FORWARD
	var l := SpotLight3D.new()
	l.transform = Transform3D(Basis.looking_at(dir, up), at)
	l.light_color = LIGHT_TINTS[tint]
	l.light_energy = energy
	l.spot_range = rng
	l.spot_angle = degrees
	# Soft-edged. A hard cone edge on a building face draws an ellipse on the
	# masonry and reads as a projector rather than as light.
	#
	# Above 1.0, not below. This had it at 0.7 on the reasoning that less
	# attenuation is a gentler light, which is backwards: the value is how fast
	# the cone falls off *towards its own edge*, so a low number holds full
	# brightness right out to the rim and cuts. The first capture showed exactly
	# that — a crisp bright ellipse on the north range, which is the projector
	# this comment was already warning about.
	l.spot_angle_attenuation = 1.7
	l.spot_attenuation = 1.0
	l.light_specular = 0.25
	l.shadow_enabled = shadow
	if shadow:
		l.shadow_bias = 0.05
		l.shadow_normal_bias = 1.5
	_light(l, nm, energy, kind)


## The shared tail: remember what full brightness means, say what the light is
## for, and put it in the group.
##
## `base_energy` is stored because the driver scales rather than sets — a lamp
## and a floodlight are not the same brightness and the evening has to dim both
## by the same fraction. Without it the driver would have to hold a table of
## every light's intended energy, which is a second copy of a number that is
## already right here.
func _light(l: Light3D, nm: String, energy: float, kind: int) -> void:
	l.set_meta("base_energy", energy)
	l.set_meta("light_kind", kind)
	# Off as generated. Nothing in the park is lit until the driver says the sun
	# is down, and a scene that loads at noon with its lamps burning would be
	# wrong for the twelve hours the game actually spends open.
	l.light_energy = 0.0
	l.visible = false
	l.add_to_group(LIGHT_GROUP, true)
	_attach(l, nm)


func _box(nm: String, base: Vector3, local: Vector3, size: Vector3, mat: String,
		theta := 0.0, collide := true, phi := 0.0) -> void:
	var b := CSGBox3D.new()
	b.size = size
	b.material = mats[mat]
	b.use_collision = collide
	b.transform = _xform(theta, phi, _place(base, local, theta))
	_add(b, nm)


func _cyl(nm: String, base: Vector3, local: Vector3, radius: float, height: float,
		mat: String, theta := 0.0, sides := 12, collide := true, phi := 0.0) -> void:
	var c := CSGCylinder3D.new()
	c.radius = radius
	c.height = height
	c.sides = sides
	c.material = mats[mat]
	c.use_collision = collide
	c.transform = _xform(theta, phi, _place(base, local, theta))
	_add(c, nm)


## **`base` plus `local`, like `_box` and `_cyl`, and it took until 2026-08-14c
## to be.**
##
## It used to take a single finished world position, which made it the one
## primitive that did not go through `_place` — so it was also the one primitive
## that silently ignored `_dilate_plaza`. Every caller outside the plaza was
## fine, because out there the map is the identity; the three inside it were the
## balloons, and all three came out separated from their own strings. The red one
## floated 5.4m from its string, the yellow 5.6m, and the blue one — which is
## meant to be resting against a bollard — 13.2m, because its string was mapped
## from radius 30 to 43.5 and it was not.
##
## Nothing catches that. `coplanar_test.py` has no opinion about two shapes that
## have drifted *apart*, the walk test does not walk into balloons, and a
## screenshot of a plaza with a balloon in the wrong half of it looks like a
## plaza with a balloon in it. It was found by somebody looking at the pictures
## and asking why the balloons had no strings.
##
## The lesson is narrower than "test more": an assembly whose parts are built by
## two different helpers is only rigid if both helpers compose position the same
## way. The signature *is* the invariant, so the odd one out had to go.
func _sphere(nm: String, base: Vector3, local: Vector3, radius: float, mat: String,
		theta := 0.0, squash := 1.0) -> void:
	var s := CSGSphere3D.new()
	s.radius = radius
	s.radial_segments = 10
	s.rings = 6
	s.material = mats[mat]
	s.use_collision = false
	# A sphere has no orientation worth keeping, so `theta` only turns the offset
	# — which is exactly what it is for. Squash stays on the basis.
	s.transform = Transform3D(Basis.IDENTITY.scaled(Vector3(1.0, squash, 1.0)),
		_place(base, local, theta))
	_add(s, nm)


# ---------------------------------------------------------------------------
# Paving
# ---------------------------------------------------------------------------

## `ParkPlan.WALKWAYS` has been the park's circulation since the minimap needed
## something path-shaped to draw, and until now the only place it existed was on
## that minimap. Which is backwards: a plan the player can read on a map and not
## on the ground is a plan the park does not actually have.
##
## So this lays the same polylines as paving. Nothing new is decided here — the
## centre lines and the widths are read out of the plan, and if a walkway moves
## the paving moves with it.
##
## 12mm above the ground it sits on, and **no collision**. The lip is the reason
## for both: `CharacterBody3D` has no step-up, so paving the player could stand
## on would be a 12mm kerb around every path in the park, and a capsule catches
## on those. Laid over the floor rather than into it, the player walks on the
## ground and looks at the paving.
const PAVE_LIFT := 0.012

## Everything the plaza side walks on.
##
## The four threshold spokes are included even though what they lead to is
## scaffolding, because the paving is what makes a scaffolded passage read as a
## way out rather than as a gap in the wall.
##
## `west_stair` is not paved: it is a flight of steps, and a flat quad laid over
## treads would either float above them or cut through them. The boardwalk's runs
## are not paved either — down there the deck *is* the path, and a strip over it
## would be paving on planking.
func _paving() -> void:
	_walkway_paving([&"plaza_ring", &"spoke_south", &"spoke_nnw",
		&"spoke_ne", &"spoke_se", &"spoke_sw"], PAVE_LIFT, "asphalt")
	# The west spoke's plaza half only: ring, bend, and up to the gate house's
	# face. The tunnel past it is the plaza's own brick and the terrace past
	# *that* is laid by `_terrace_paving`, into this scene and the boardwalk both.
	_pave_run(&"spoke_west", PAVE_LIFT, "asphalt", 0, 2)
	_terrace_paving()
	# The plaza's floor is at y=0; `entrance_ground` is `GROUND_SEAM` lower, so
	# the street's asphalt comes down with it. Otherwise the two halves of the
	# same walk sit at different heights where they meet at z=38.
	_walkway_paving([&"street", &"apron"], GROUND_SEAM + PAVE_LIFT, "asphalt")


## The paving on the far side of the tunnel, laid into whichever scene is being
## written — which is both of them.
##
## The terrace is on the boardwalk's side of the seam and the plaza's side of the
## wall, so both sections have to show it: the plaza sees it framed by the arch
## from as far back as the ring, and the boardwalk stands on it. `plaza_paving`
## is not mounted past the arch and `boardwalk` is not mounted before it, so the
## only way for the ground to be the same in both is to lay it twice.
##
## Two stretches, and the second is the point. The west spoke's last segment runs
## out of the tunnel to the parapet, which is where the view is; the stair's first
## two run north to the head of the flight, which is where the player is actually
## going, and without asphalt on them the terrace was a bare brick balcony with
## nothing to say the way on was to the right. They stop at the head of the
## flight, because past that it is treads.
func _terrace_paving() -> void:
	_pave_run(&"spoke_west", PAVE_LIFT, "asphalt", 3, 1)
	_pave_run(&"west_stair", PAVE_LIFT, "asphalt", 0, 1)


func _walkway_paving(ids: Array, y: float, mat: String) -> void:
	for id in ids:
		_pave_run(id, y, mat)


## One walkway, or a range of its segments where a run is only partly ground.
##
## The range is what keeps `ParkPlan.WALKWAYS` honest. The west spoke runs from
## the ring through the arch and out onto the terrace, and three different things
## are true of three stretches of it: the plaza's half is paved into
## `plaza_paving`, the tunnel is not paved at all, and the terrace is paved into
## two scenes. Cutting the run up to match was tried and it put a hole in the
## map — the way west drew as a stub ending at a wall. So the run stays whole and
## this takes `first` and `count`.
func _pave_run(id: StringName, y: float, mat: String, first := 0,
		count := -1) -> void:
	var run: Array = Plan.WALKWAYS[id]
	var w: float = Plan.WALKWAY_WIDTH.get(id, 6.0)
	# A closed run — the ring — mitres its two ends into each other like any
	# other joint. An open one stops where the plan says it stops, because
	# the spokes end at the perimeter wall and any overhang there is paving
	# inside a building.
	var closed: bool = run.size() > 2 and run[0].distance_to(run[-1]) < 0.01
	var last := run.size() - 1
	var to: int = last if count < 0 else mini(first + count, last)
	for i in range(first, to):
		var a: Vector2 = run[i]
		var b: Vector2 = run[i + 1]
		var d := b - a
		var length := d.length()
		if length < 0.01:
			continue
		var ext_a := 0.0
		if i > first:
			ext_a = _mitre(run[i - 1], a, b, w)
		elif closed:
			ext_a = _mitre(run[last - 1], a, b, w)
		var ext_b := 0.0
		# Against the end of the range rather than the end of the run: paving
		# mitred into a segment nobody is laying would run on past whatever
		# made the range stop there.
		if i + 2 <= to:
			ext_b = _mitre(a, b, run[i + 2], w)
		elif closed:
			ext_b = _mitre(a, b, run[1], w)
		var dir := d / length
		var mid := (a + b) * 0.5 + dir * (ext_b - ext_a) * 0.5
		_pave_quad("pave_%s_%d" % [id, i], Vector3(mid.x, y, mid.y),
			Vector2(w, length + ext_a + ext_b), atan2(d.x, d.y), mat)


## How far past a corner each of the two quads meeting there has to run.
##
## Butted, a turn leaves a wedge of bare ground on the outside of the corner. The
## first attempt filled it by extending both quads half a width, which is right
## for a right angle and wildly too much for anything shallower — on the ring's
## twelve 30° joints it put 3m of overshoot on an 0.8m gap, and twelve of those
## turned a clean dodecagon into a cog. Which is what it looked like: the ring
## read as a blob of asphalt with corners, and every bend in every spoke had a
## diamond bulge on it.
##
## The exact answer is the mitre: half the width times the tangent of half the
## turn. Capped at a width, because the plan is allowed to contain a hairpin and
## the tangent is not bounded.
func _mitre(before: Vector2, at: Vector2, after: Vector2, w: float) -> float:
	var into := (at - before).normalized()
	var out_of := (after - at).normalized()
	var turn := absf(into.angle_to(out_of))
	if turn < 0.001:
		return 0.0
	return minf(w * 0.5 * tan(turn * 0.5), w)


## One segment of paving, as a plane rather than a slab.
##
## Two triangles and no sides, because nothing ever sees the edge of it: the
## quad is 12mm off the floor and the floor is opaque. Shadows are off for the
## same reason — a flat thing lying on the ground casting a shadow onto the
## ground is 12mm of dark outline around every path, and it is the one artefact
## that would give the trick away.
func _pave_quad(nm: String, centre: Vector3, size: Vector2, theta: float,
		mat: String) -> void:
	var plane := PlaneMesh.new()
	plane.size = size
	plane.material = mats[mat]
	var mi := MeshInstance3D.new()
	mi.mesh = plane
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.transform = _xform(theta, 0.0, centre)
	_add(mi, nm)


# ---------------------------------------------------------------------------
# The fountain
# ---------------------------------------------------------------------------

## The plaza's centrepiece, and until now the plaza's worst object.
##
## It was five concentric drums of decreasing radius, alternating grey and
## salmon, eighteen metres across and 7.9 tall. Everything about that is
## defensible one line at a time — it held the middle of the room, it cleared the
## clock tower, it was the right size — and the whole of it read as a cake. Two
## reasons, and they are separable:
##
##   1. **There was no water in it.** Not a plane, not a jet, nothing. The only
##      thing that makes a fountain a fountain was the one thing missing, and
##      calling it `fountain_base` in the scene tree did not put it there.
##   2. **The profile was monotone.** Five stacked cylinders each smaller than
##      the last is a shape with no incident in it: every silhouette from every
##      angle is the same staircase, and the alternating colour banded it *with*
##      the layers, which made the staircase louder rather than breaking it up.
##
## So: a real tiered fountain. A pool you could sit on the edge of, a pedestal, a
## basin, a column, a smaller basin, and water — falling from each lip to the one
## below it, jetting in a ring inside the pool, and a plume up the middle.
##
## **The height envelope is inherited and not renegotiated.** 2026-08-13b tuned
## this against the clock tower and wrote the numbers down: at 10.9m the fountain
## hid the bottom 24m of a 29m tower from the ring's edge, and coming down to
## 7.9m with the 18m basin untouched was what fixed it. So 7.9 and 18 stand.
##
## What *did* change is which 7.9. The tallest solid is now the nozzle at 6.3m
## and the top 1.6m is the plume — so the stone silhouette is 1.6m lower than
## before and gives the tower back more than it takes, while the object is the
## same height it was measured at. Being able to spend the top of the envelope on
## something thin and bright is most of the argument for the plume: from the gate
## the old fountain was a pale drum subtending 3.3 degrees against a pale
## building, and the new one has a white vertical against the sky.
##
## The other inherited number is `Plan.FOUNTAIN_RADIUS`, which is 9 and is the
## footprint the crowd's walkable graph cuts around. The coping's *outer* face is
## that radius exactly, so nothing about where guests may walk changes.

## Where the sections of the fountain sit, bottom to top. Written out rather than
## derived, because a fountain is a drawn profile and the numbers are the
## drawing: every one of these was pushed around against a screenshot, and a
## formula generating them would be a formula nobody could tune.
##
## The rule they all obey is that consecutive parts *overlap* by 1-3cm. That is
## the project's standing rule about coplanar faces — parts run into each other
## rather than meeting edge to edge — and it matters more here than anywhere,
## because this is 270 shapes stacked on one axis and every one of them has a top
## face and a bottom face that could line up with a neighbour's.
const FOUNT_R := Plan.FOUNTAIN_RADIUS

## The kerb, as a ring of blocks rather than as a cylinder. The whole reason is
## that a pool needs an *inside*: a solid drum at radius 9 is a disc with water
## painted on top of it, and the thing that reads as a basin is seeing the water
## sit down below a rim you could put a drink on.
##
## 36 blocks makes the outer face an inscribed 36-gon, so it bulges 3.4cm past
## radius 9 at each block's corner and sits exactly on it at each block's middle.
## Under 4cm over a metre and a half is a faceted stone kerb, which is what this
## is meant to be, and it is far too shallow for the capsule to catch on.
const KERB_SEGS := 36
const COPING_DEPTH := 0.80
## Derived rather than typed, so the coping's *outer* face is on the plan's
## radius by construction. That face is the one number the rest of the park
## agrees with — it is what the crowd's graph cuts around and what the ring
## walkway is set outside of — and a kerb radius typed independently is a kerb
## radius that drifts off it the first time the coping gets wider.
const KERB_R := FOUNT_R - COPING_DEPTH * 0.5
const KERB_TOP := 0.36

## The seat, and it is plan data rather than a number in this file because
## `gen_crowd.gd` seats nine guests on it and cannot read anything over here.
## See `ParkPlan.FOUNTAIN_RIM_TOP` for why it is half a metre.
const COPING_TOP := Plan.FOUNTAIN_RIM_TOP
const POOL_TOP := Plan.FOUNTAIN_POOL_TOP


func _fountain() -> void:
	# In final coordinates. The fountain is at the origin, so the dilation map
	# would return it unchanged anyway — but stating it is cheaper than the
	# reader having to prove that, and `_dilate_plaza` is a mode that persists
	# across scenes.
	_dilate_plaza = false
	var o := Vector3(Plan.FOUNTAIN_AT.x, 0.0, Plan.FOUNTAIN_AT.y)

	_fountain_pool(o)
	_fountain_pedestal(o)
	_fountain_basins(o)
	_fountain_plume(o)
	_fountain_jets(o)
	# No lights here, and that is deliberate rather than an omission. The
	# fountain's six uplights are `_fountain_lights` over in `_plaza_lights`,
	# where the tower's and the bandstand's are, because what a fitting is aimed
	# at is a decision about the *plaza after dark* and belongs with the rest of
	# that argument. It also keeps this scene to geometry, which is the only
	# reason it can be regenerated without touching what the night looks like.


## The pool: kerb, coping, bed and surface.
func _fountain_pool(o: Vector3) -> void:
	# Chord of one segment, plus 4% so neighbours overlap instead of butting.
	var chord := 2.0 * KERB_R * sin(PI / float(KERB_SEGS)) * 1.04
	for i in KERB_SEGS:
		var a := TAU * float(i) / float(KERB_SEGS)
		# The kerb collides and the coping collides, and nothing else in the
		# fountain does. That is the whole barrier: the player cannot get over a
		# 52cm wall without a step-up, so 260 shapes inside the pool need no
		# collision at all and 72 ring blocks are the cheapest possible fence.
		_box("kerb_%02d" % i, o, Vector3(0.0, KERB_TOP * 0.5, KERB_R),
			Vector3(chord, KERB_TOP, 0.62), "fount_stone", a)
		# Overhanging the kerb by 9cm each side, which is the entire reason the
		# coping is a separate course: the shadow line under a lip is what makes
		# masonry read as cut stone rather than as an extruded shape.
		_box("coping_%02d" % i, o, Vector3(0.0, (KERB_TOP + COPING_TOP) * 0.5, KERB_R),
			Vector3(chord * 1.04, COPING_TOP - KERB_TOP, COPING_DEPTH), "fount_wet", a)

	# Under the water and effectively never seen. It is here so that the one
	# grazing angle where the surface disappears shows a floor rather than the
	# plaza on the far side.
	_cyl("pool_bed", o, Vector3(0.0, 0.06, 0.0), 8.42, 0.12, "fount_bed",
		0.0, 40, false)
	# 0.30, so the water sits 22cm below the coping. Freeboard is what says the
	# pool has depth; brimmed to the rim it reads as a painted disc.
	_water_cyl("pool_water", o, Vector3(0.0, POOL_TOP - 0.10, 0.0), 8.26, 0.20,
		"water_pool", 48)


## The steps out of the water, and the pedestal on them.
##
## Three steps rather than one plinth, and the bottom two are `fount_wet`: the
## waterline is at 0.30 and the first step's top is at 0.46, so one of the three
## is genuinely half-submerged. Wetting two of them puts the tide mark a step
## above the water, which is what a fountain that has been running all summer
## actually looks like.
func _fountain_pedestal(o: Vector3) -> void:
	_cyl("step_1", o, Vector3(0.0, 0.23, 0.0), 3.60, 0.46, "fount_wet", 0.0, 32, false)
	_cyl("step_2", o, Vector3(0.0, 0.62, 0.0), 3.05, 0.36, "fount_wet", 0.0, 28, false)
	_cyl("step_3", o, Vector3(0.0, 0.94, 0.0), 2.55, 0.32, "fount_stone", 0.0, 24, false)

	# Foot, shaft, cap. Three shapes and the only three that matter: a bare drum
	# between the steps and the basin is the old fountain again in miniature,
	# and a moulding top and bottom is what turns it into a pedestal.
	_cyl("ped_foot", o, Vector3(0.0, 1.21, 0.0), 1.95, 0.26, "fount_stone", 0.0, 20, false)
	_cyl("ped_shaft", o, Vector3(0.0, 1.79, 0.0), 1.52, 0.92, "fount_stone", 0.0, 20, false)
	_cyl("ped_cap", o, Vector3(0.0, 2.35, 0.0), 1.92, 0.24, "fount_stone", 0.0, 20, false)


## The two basins, each built the same way: an underside that steps *outward*
## going up, a rim ring, and water inside the ring.
##
## The stepped underside is the load-bearing idea. A basin is a dish, and a dish
## seen from below — which is how you see both of these, standing on the plaza
## floor — is a curve. Three discs of increasing radius approximate that curve in
## silhouette, and unlike a single drum they catch light differently on each
## step, so the underside has shading in it at every hour rather than only when
## the sun happens to rake it.
##
## The rim is a ring of blocks for the same reason the coping is: a solid
## cylinder would be a lid over the water.
func _fountain_basins(o: Vector3) -> void:
	# Lower basin. 8.1m across at 3.35 — wider than the pedestal by a long way,
	# which is what makes the profile read as a fountain rather than as a column.
	_cyl("lb_under_1", o, Vector3(0.0, 2.59, 0.0), 2.48, 0.28, "fount_stone", 0.0, 24, false)
	_cyl("lb_under_2", o, Vector3(0.0, 2.83, 0.0), 3.26, 0.24, "fount_stone", 0.0, 28, false)
	_cyl("lb_under_3", o, Vector3(0.0, 3.04, 0.0), 3.82, 0.22, "fount_stone", 0.0, 28, false)
	_rim_ring("lb_rim", o, 28, 3.92, 3.24, 0.22, 0.30)
	_water_cyl("lb_water", o, Vector3(0.0, 3.19, 0.0), 3.80, 0.22, "water_basin", 32)

	_cyl("col_foot", o, Vector3(0.0, 3.40, 0.0), 1.02, 0.22, "fount_stone", 0.0, 16, false)
	_cyl("col_shaft", o, Vector3(0.0, 4.08, 0.0), 0.74, 1.15, "fount_stone", 0.0, 16, false)
	_cyl("col_cap", o, Vector3(0.0, 4.74, 0.0), 1.00, 0.22, "fount_stone", 0.0, 16, false)

	# Upper basin, 4.1m across at 5.46.
	_cyl("ub_under_1", o, Vector3(0.0, 4.95, 0.0), 1.30, 0.24, "fount_stone", 0.0, 20, false)
	_cyl("ub_under_2", o, Vector3(0.0, 5.16, 0.0), 1.78, 0.22, "fount_stone", 0.0, 20, false)
	_rim_ring("ub_rim", o, 20, 1.94, 5.36, 0.20, 0.26)
	_water_cyl("ub_water", o, Vector3(0.0, 5.30, 0.0), 1.84, 0.22, "water_basin", 24)

	# The falls. Each hangs from its own lip and runs the whole way down to what
	# it lands in, rather than stopping short — a fall that ends in mid-air is
	# the one artefact that would read as a modelling mistake instead of as
	# water. What makes the full drop affordable is the fade: the shader thins it
	# out over its length, so it is bright at the lip and a ghost by the time it
	# reaches the surface, where the froth ring takes over.
	_veil("lb_veil", o, 16, 4.03, 3.16, 0.40, 0.07, "water_veil_lo")
	_veil("ub_veil", o, 10, 2.03, 5.33, 3.30, 0.06, "water_veil_hi")

	# Where the lower falls land. Flat, 1cm proud of the surface, and the one
	# piece of water in the fountain that is neither falling nor still. One disc
	# per fall, on the same bearings, so the froth is under the water that made
	# it rather than being a decorative ring of its own.
	_foam_ring("pool_foam", o, 16, 4.03, POOL_TOP + 0.01, 0.52)


## The nozzle and what comes out of it.
##
## The plume is four tapering cylinders and it is the tallest thing on the
## fountain — 7.9m, which is the number the whole envelope was tuned to in
## 2026-08-13b. Spending it on water rather than on stone is the point: it is
## thin, so it hides almost none of the clock tower behind it, and it is the only
## bright vertical in a plaza built out of pale horizontal masonry.
##
## The spray skirt is two very faint drums flaring downward around it, standing
## in for the water coming back down into the upper basin. Faint on purpose —
## at any real opacity a pair of concentric translucent drums is a wedding cake
## made of ghosts, which is the shape this rebuild exists to get rid of.
func _fountain_plume(o: Vector3) -> void:
	_cyl("fin_foot", o, Vector3(0.0, 5.50, 0.0), 0.54, 0.20, "fount_stone", 0.0, 12, false)
	_cyl("fin_shaft", o, Vector3(0.0, 5.86, 0.0), 0.32, 0.55, "fount_stone", 0.0, 12, false)
	_cyl("nozzle", o, Vector3(0.0, 6.22, 0.0), 0.20, 0.22, "fount_bronze", 0.0, 10, false)

	_water_cyl("plume_1", o, Vector3(0.0, 6.55, 0.0), 0.28, 0.50, "water_plume", 10)
	_water_cyl("plume_2", o, Vector3(0.0, 7.01, 0.0), 0.21, 0.46, "water_plume", 10)
	_water_cyl("plume_3", o, Vector3(0.0, 7.42, 0.0), 0.14, 0.40, "water_plume", 8)
	_water_cyl("plume_4", o, Vector3(0.0, 7.74, 0.0), 0.075, 0.32, "water_plume", 8)

	# One skirt, not two. The second was a 2.9m drum sitting on top of the upper
	# basin and it was doing exactly what the veils were doing — reading as a
	# container rather than as its contents.
	_water_cyl("spray_1", o, Vector3(0.0, 5.95, 0.0), 0.86, 0.90, "water_spray", 16)


## The ring of jets in the pool.
##
## Twelve, at radius 6.5, leaning six degrees inward. Near-vertical rather than
## arcing, and that is a decision about what greybox can carry: an arc is four
## segments per jet and lands wherever the last one stops, and a jet that ends
## in mid-air over the water is worse than a straight one. Leaning them all
## slightly inward makes the ring converge on the plume, so the twelve of them
## and the one up the middle read as one arrangement instead of two.
##
## They stand well outside the lower basin's 4.05m rim, so from anywhere on the
## plaza floor there is water at three heights at once: the ring, the sheets off
## each lip, and the plume.
const JET_COUNT := 12
const JET_R := Plan.FOUNTAIN_JET_R
const JET_LEAN := -0.10


func _fountain_jets(o: Vector3) -> void:
	for i in JET_COUNT:
		var a := TAU * (float(i) + 0.5) / float(JET_COUNT)
		# Breaking the surface rather than sitting on the floor of the pool: the
		# nozzle's top is 9cm above the waterline, which is what stops the jet
		# looking as though it starts at nothing.
		_cyl("jet_%02d_nozzle" % i, o, Vector3(0.0, 0.26, JET_R), 0.14, 0.26,
			"fount_bronze", a, 8, false)
		var foot := Vector3(0.0, 0.34, JET_R)
		foot = _leaning("jet_%02d_a" % i, o, foot, 0.075, 1.25, "water_jet", a, JET_LEAN, 8)
		_leaning("jet_%02d_b" % i, o, foot, 0.050, 0.85, "water_jet", a, JET_LEAN, 6)
		_foam_patch("jet_%02d_foam" % i, o, Vector3(0.0, POOL_TOP + 0.01, JET_R),
			0.34, a)


## A ring of stone blocks standing on edge — a basin's lip.
func _rim_ring(nm: String, o: Vector3, segs: int, r: float, mid_y: float,
		height: float, depth: float) -> void:
	var chord := 2.0 * r * sin(PI / float(segs)) * 1.06
	for i in segs:
		var a := TAU * float(i) / float(segs)
		_box("%s_%02d" % [nm, i], o, Vector3(0.0, mid_y, r),
			Vector3(chord, height, depth), "fount_wet", a, false)


## A ring of falls hanging off a lip.
##
## **The slabs do not touch, and that is the whole design of this thing.** The
## first build ran them shoulder to shoulder all the way round, which is what a
## sheet coming off a rim actually does — and it came out as a translucent tube
## with the basins invisible inside it. Two separate faults produced that: the
## material was being drawn four times over (see `water_fall.gdshader`), and a
## closed ring of translucent slabs is *geometrically* a tube no matter how
## faint you make it. Fixing only the first gives a fainter tube.
##
## So each fall is 40% of its slot and 60% is air. You see the stone through the
## gaps, the ring reads as a set of falls rather than as a curtain, and the
## shader's streaking — which does nothing on a wide sheet — has something the
## width of a stream to run down. It is also closer to how a park fountain that
## has been running for twenty summers behaves: the sheet breaks up at the lip
## into the places where the lip has worn.
const VEIL_FILL := 0.34


func _veil(nm: String, o: Vector3, segs: int, r: float, top: float, bottom: float,
		thick: float, mat: String) -> void:
	# `2 r sin(pi/n)` is the whole chord — the width of one slot. The fill is a
	# fraction *of* that, not of half of it.
	var chord := 2.0 * r * sin(PI / float(segs)) * VEIL_FILL
	var h := top - bottom
	for i in segs:
		var a := TAU * float(i) / float(segs)
		_water_box("%s_%02d" % [nm, i], o, Vector3(0.0, bottom + h * 0.5, r),
			Vector3(chord, h, thick), mat, a)


## Froth, laid flat on a water surface where something is falling into it.
##
## Round, and the first build was square. A flat box on water is a *tile*: it
## has four straight edges and two of them are parallel to nothing, so a ring of
## them read as paving laid in the pool. Discs overlap into a scalloped band with
## no straight edge anywhere in it, which is what disturbed water looks like from
## six metres away, and they cost the same.
func _foam_ring(nm: String, o: Vector3, segs: int, r: float, y: float,
		radius: float) -> void:
	for i in segs:
		var a := TAU * float(i) / float(segs)
		_foam_patch("%s_%02d" % [nm, i], o, Vector3(0.0, y, r), radius, a)


func _foam_patch(nm: String, o: Vector3, local: Vector3, radius: float,
		a: float) -> void:
	_water_cyl(nm, o, local, radius, 0.04, "water_foam", 10, a)


## A cylinder standing on `foot` and leaning by `lean` about its own bearing.
## Returns the far end, so segments chain into each other.
##
## The arithmetic is here rather than at each call site because `_xform` rotates
## a shape about its *centre*: leaning a 1.25m jet by six degrees swings its
## bottom 6cm off the nozzle it is supposed to be coming out of, and the fix is
## to solve for the centre from the foot rather than to nudge the number until
## the screenshot looks right.
func _leaning(nm: String, o: Vector3, foot: Vector3, radius: float, height: float,
		mat: String, theta: float, lean: float, sides: int) -> Vector3:
	var up := Vector3(0.0, cos(lean), sin(lean))
	_water_cyl(nm, o, foot + up * (height * 0.5), radius, height, mat, sides,
		theta, lean)
	return foot + up * height


## The two water primitives. Identical to `_box` and `_cyl` except that nothing
## they make collides or casts a shadow.
##
## The shadow is the part worth stating. A translucent veil that casts an opaque
## shadow draws a solid black ring on the water it is falling into, and a plume
## casting one lays a bar across the plaza at four in the afternoon. Godot has no
## notion that a material is see-through when it renders the shadow map, so this
## has to be said per node.
func _water_cyl(nm: String, o: Vector3, local: Vector3, radius: float,
		height: float, mat: String, sides := 16, theta := 0.0, phi := 0.0) -> void:
	_cyl(nm, o, local, radius, height, mat, theta, sides, false, phi)
	_last_unlit()


func _water_box(nm: String, o: Vector3, local: Vector3, size: Vector3,
		mat: String, theta := 0.0) -> void:
	_box(nm, o, local, size, mat, theta, false)
	_last_unlit()


func _last_unlit() -> void:
	var last := _root.get_child(_root.get_child_count() - 1) as GeometryInstance3D
	if last == null:
		push_error("gen_props: the last node added was not geometry")
		return
	last.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


# ---------------------------------------------------------------------------
# Filling the outer room
# ---------------------------------------------------------------------------

## Trees. **The plaza had none**, which at 80m was a thin excuse and at 104m is
## the first thing missing from any photograph of it: the reference parks are
## full of planting and this was a paved floor with furniture on it.
##
## Three pieces each — a trunk and two offset crowns — because one sphere on a
## stick reads as a lollipop and two overlapping ones read as a tree from the
## only distance that matters here, which is across the plaza.
func _trees() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 0x7EE5
	# 5.5m apart rather than 6.0. The furniture register took the outer room's
	# spare ground down to where 28 trees no longer fitted at six, and half a
	# metre of spacing is a cheaper thing to give up than a tree.
	var spots := Plan.open_spots(28, 11, 21.0, 35.0, 3.0, 5.5, _stood)
	for i in spots.size():
		var p: Vector2 = spots[i]
		var b := Vector3(p.x, 0, p.y)
		var h := 3.4 + rng.randf() * 1.6
		var spread := 2.1 + rng.randf() * 0.8
		_cyl("tree_%d_trunk" % i, b, Vector3(0, h * 0.5, 0), 0.24, h, "wood", 0.0, 8)
		_sphere("tree_%d_crown_a" % i, b, Vector3(0, h + spread * 0.55, 0),
			spread, "foliage", 0.0, 0.72)
		_sphere("tree_%d_crown_b" % i, b,
			Vector3(spread * 0.4, h + spread * 0.95, -spread * 0.3),
			spread * 0.66, "foliage", 0.0, 0.8)


## Lamps, bins and benches for the outer room, on the same rules. The inner ring
## already has its own set placed against the fountain; this is everything the
## walk out to the perimeter needs and did not have, because until today there
## was no walk out to the perimeter.
func _outer_furniture() -> void:
	var lamps := Plan.open_spots(12, 21, 23.0, 33.0, 2.6, 9.0, _stood)
	for i in lamps.size():
		var b := Vector3(lamps[i].x, 0, lamps[i].y)
		_cyl("lamp_o%d_pole" % i, b, Vector3(0, 2.1, 0), 0.09, 4.2, "metal", 0.0, 8)
		_box("lamp_o%d_head" % i, b, Vector3(0, 4.13, 0), Vector3(0.5, 0.24, 0.5), "lamp_glass")
		_lamp_light("lamp_o%d_pool" % i, _place(b, Vector3(0, 3.98, 0), 0.0), false)

	var bins := Plan.open_spots(8, 31, 21.0, 34.0, 2.2, 8.0, _stood)
	for i in bins.size():
		var b := Vector3(bins[i].x, 0, bins[i].y)
		_cyl("bin_o%d_body" % i, b, Vector3(0, 0.42, 0), 0.32, 0.85, "metal")
		_cyl("bin_o%d_lid" % i, b, Vector3(0, 0.865, 0), 0.36, 0.1, "blue")

	# Round the ring's outer verge, facing the fountain, because that is where a
	# plaza puts benches and because the open ground belongs to the crowd's
	# routes. See `ParkPlan.ring_verge`.
	var seats := Plan.ring_verge(1.8, 2.2)
	for i in seats.size():
		var p := Vector3(seats[i].x, 0, seats[i].y)
		_bench("bench_o%d" % i, p, _facing(p, Vector3.ZERO))

	# Flower beds were tried here and taken out again. At 3.2m square they are
	# big enough to be obstacles, and scattered through open ground they land on
	# the crowd's wander graph — the validator threw out three nodes and four
	# edges at once. Open ground is what the graph is made of, so anything that
	# size has to hug a walkway or a wall rather than sit in the middle. The
	# budget went to trees instead, which are the thing actually missing, and
	# which a guest can walk past without the graph caring.

	var trash := Plan.open_spots(10, 61, 18.0, 36.0, 1.0, 3.0)
	for i in trash.size():
		var b := Vector3(trash[i].x, 0, trash[i].y)
		_box("litter_o%d" % i, b, Vector3(0, 0.006, 0), Vector3(0.22, 0.012, 0.16),
			"white", float(i), false)


## Picture-spot signs: the park telling you where its own best angle is.
##
## `design.md` has asked for these since before there was a plaza to put them
## in, and they are the one piece of density here that is content rather than
## furniture. Each stands where the park thinks you should stand and faces what
## it thinks you should point at. **Diegetic suggestion with nothing that
## completes** — free aim means the game never frames a shot, and half the point
## of a sign saying "photograph this" is being able to walk past it.
const PICTURE_SPOTS := [
	# where to stand, what to look at
	[Vector2(-1.5, 20.0), Vector2(-1.5, -32.0)],   # up the axis at the clock
	[Vector2(-19.0, 6.0), Vector2(-39.0, -2.0)],   # west through the arch
	[Vector2(14.0, 16.0), Vector2(0.0, 0.0)],      # across the fountain
	[Vector2(24.0, -22.0), Vector2(44.0, -44.0)],  # north-east at the coaster
]


## The sign has to stand *beside* the spot, not on it — which is the one prop in
## the plaza where being in the walkway is not carelessness but the definition.
## `PICTURE_SPOTS` names the ground the park wants you standing on, and two of
## the four are on a spoke's own centre line because that is where the view is:
## the axial one looks up the entrance street at the clock, which is `spoke_south`
## exactly. So the point stays what it is and the board is stood off it, and the
## aim is taken from where the board ends up rather than from where the spot is —
## a sign that has moved four metres and is still pointing from the old place is
## a sign pointing four degrees wide.
func _picture_spots() -> void:
	_stand_clear = 0.8
	for i in PICTURE_SPOTS.size():
		var at: Vector2 = PICTURE_SPOTS[i][0]
		var look: Vector2 = PICTURE_SPOTS[i][1]
		var b := Vector3(at.x, 0, at.y)
		var th := _facing(_plaza_out(b), Vector3(look.x, 0, look.y))
		_cyl("photospot_%d_post" % i, b, Vector3(0, 0.6, 0), 0.07, 1.2, "metal", th, 8)
		_box("photospot_%d_board" % i, b, Vector3(0, 1.35, 0),
			Vector3(0.9, 0.6, 0.06), "yellow", th)
		# A little dark rectangle for the camera pictogram, so it reads as a
		# photo sign rather than as a park map at ten metres.
		_box("photospot_%d_icon" % i, b, Vector3(0, 1.35, 0.05),
			Vector3(0.34, 0.24, 0.04), "far_shade", th, false)
	_stand_clear = 0.0


func _bench(nm: String, base: Vector3, theta: float) -> void:
	_box(nm + "_seat", base, Vector3(0, 0.45, 0), Vector3(1.8, 0.12, 0.55), "wood", theta)
	_box(nm + "_leg_l", base, Vector3(-0.78, 0.225, 0), Vector3(0.14, 0.45, 0.5), "metal", theta)
	_box(nm + "_leg_r", base, Vector3(0.78, 0.225, 0), Vector3(0.14, 0.45, 0.5), "metal", theta)
	_box(nm + "_back", base, Vector3(0, 0.72, -0.22), Vector3(1.8, 0.52, 0.11), "wood", theta)


## Turn so the assembly's local +Z faces `target`.
func _facing(from: Vector3, target: Vector3) -> float:
	var d := target - from
	return atan2(d.x, d.z)


## A bench is 1.8m long and 0.55 deep and faces something, so it wants about a
## metre of verge behind it and the walk in *front* of it rather than under it.
const BENCH_CLEAR := 1.2

## The hut's bench, hoisted out of `_benches` because `_balloons` ties two
## balloons to it and a second copy of these numbers is how the balloons came to
## be eight metres from the bench in the first place. Local to the hut, so it
## follows if the hut moves; the top of the back rail is what a string ties to.
const HUT_BENCH_AT := Plan.PHOTO_HUT_BENCH
const HUT_BENCH_YAW := Plan.PHOTO_HUT_BENCH_YAW
const HUT_BENCH_RAIL := 0.98


func _benches() -> void:
	# The ring of five round the fountain. They were on its skirt in the 80m
	# plaza and the dilation put them in the road: the hub grew by 1.8 and the
	# ring walkway moved out further than that, so radius 7.5 came out at 13.5
	# and the ring is paved from 12 to 20. `_stand_clear` walks them back onto
	# the skirt, which is where they were meant to be all along — a bench beside
	# a fountain, with the walk behind it.
	_stand_clear = BENCH_CLEAR
	var r := 7.5
	# The fourth bearing is 340 and not 235, and it took two goes to find out why.
	#
	# 235 put the bench on top of the snack cart, which is pushed onto the skirt
	# from the mouth of `spoke_nnw` and lands at 243. Moving it to 210 was worse
	# and instructively so: **the ring is a twelve-gon, and 210 is one of its
	# vertices.** A prop pushed inward off a corner is 5.2m clear of the segment
	# it was pushed from and only 0.8 clear of the next one round, so the rule
	# scored the inward candidate below the outward one and put the bench at
	# radius 21 — out in the open room, against the bandstand's own south bench.
	# The skirt is pinched every 30 degrees and the gaps between are what it has.
	#
	# So the ring gives up being even. It was never going to stay even anyway:
	# the cart, the stroller, the newspaper boxes, an a-frame and two bins are all
	# pushed onto the same three metres of skirt, and five benches spaced 72 apart
	# is a drawing rather than a plaza.
	var degs := [25.0, 95.0, 165.0, 305.0, 340.0]
	for i in degs.size():
		var a := deg_to_rad(degs[i])
		var p := Vector3(r * cos(a), 0.0, r * sin(a))
		_bench("bench_%d" % i, p, _facing(p, Vector3.ZERO))
	_bench("bench_south", Vector3(-5, 0, 19), deg_to_rad(186))

	# The hut's own bench, and the bandstand's three, are placed against things
	# that moved by hand rather than by `_plaza_out` — so they are placed by hand
	# too, in final coordinates, with the dilation off. Run through the map they
	# would each be dilated by their own radius and spread away from the object
	# they belong to: the bandstand's ring of benches would come out 24m across
	# around an 11m bandstand.
	_dilate_plaza = false
	var hut := Vector3(Plan.PHOTO_HUT_AT.x, 0.0, Plan.PHOTO_HUT_AT.y)
	_bench("bench_hut", hut + HUT_BENCH_AT, deg_to_rad(HUT_BENCH_YAW))

	# **The bandstand's three are re-beared rather than pushed, and that is the
	# line between the two fixes.** A prop standing on open ground can be moved
	# to the nearest clear metre and still be the same prop; a prop that belongs
	# to a building cannot — pushed out of `spoke_nnw`, the east bench came out
	# twelve metres away and stopped being one of a ring of three. So the ring
	# keeps its radius and gives up the bearing instead.
	#
	# The bearing it gives up is the east one, because `spoke_nnw` runs down that
	# side: from (−8, −13.86) to (−14, −30) it passes within four metres of the
	# bandstand's east face, which is the paving's own half-width. There is no
	# room for a bench there and there was not one before either — the old
	# arrangement simply put one in the road. South, west and north it is, so you
	# walk past the bandstand on one side and sit on the other three.
	_stand_clear = 0.0
	var band := Vector3(-20, 0, -20)
	var bdegs := [90.0, 180.0, 270.0]
	for i in bdegs.size():
		var a := deg_to_rad(bdegs[i])
		var p := band + Vector3(8.6 * cos(a), 0.0, 8.6 * sin(a))
		_bench("bench_band_%d" % i, p, _facing(p, band))
		# Told to the register by hand, because these are the one bench that is
		# not pushed and `_plaza_out` only records what it moves. Without it the
		# scatter that comes later cannot see them, and grew a tree through the
		# west one — which is what opting out of the rule costs.
		_note_stood(Vector2(p.x, p.z), BENCH_CLEAR)
	_dilate_plaza = true
	_stand_clear = BENCH_CLEAR
	_bench("bench_sw", Vector3(-11, 0, 20), deg_to_rad(120))
	_bench("bench_se", Vector3(2, 0, 22), deg_to_rad(200))
	_stand_clear = 0.0


## A lamp post is 18cm through and is *meant* to stand at the edge of a walk —
## which is what this number says. Small, because a lamp on the verge is right
## and a lamp two metres back in the grass is a lamp lighting nothing.
func _lamps() -> void:
	_stand_clear = 0.45
	var spots := [
		Vector2(13, -2), Vector2(9, -11), Vector2(-2, -13), Vector2(-13, -3),
		Vector2(-11, 6), Vector2(-3, 13), Vector2(7, 14), Vector2(14, 9),
		Vector2(-19, 2), Vector2(-19, 12), Vector2(-18, -14), Vector2(-16, 20),
	]
	for i in spots.size():
		var b := Vector3(spots[i].x, 0, spots[i].y)
		_cyl("lamp_%d_pole" % i, b, Vector3(0, 2.1, 0), 0.09, 4.2, "metal", 0.0, 8)
		_box("lamp_%d_head" % i, b, Vector3(0, 4.13, 0), Vector3(0.5, 0.24, 0.5), "lamp_glass")
		# Under the head rather than inside it: a light at the centre of its own
		# fitting lights the fitting's underside and nothing else, and the box is
		# opaque. 15cm down puts the source at the glass.
		_lamp_light("lamp_%d_pool" % i, _place(b, Vector3(0, 3.98, 0), 0.0), true)
	_stand_clear = 0.0


## The pool under a plaza lamp standard, and the one place in the park where a
## few lights carry shadows.
##
## `shadow` is passed for the twelve inner standards and not for the twelve outer
## ones, and the split is not arbitrary: the inner ring is where the crowd stands
## and where the player is at eye level with people, so a guest casting a long
## shadow across the brick is most of what makes the plaza read as lit rather
## than as tinted. Out at the perimeter the same shadow falls on empty paving.
##
## Twelve shadow-casting omnis is the number `perf_test.gd` is measuring; if it
## comes back expensive this is the line to turn down, because the pools stay.
func _lamp_light(nm: String, at: Vector3, shadow: bool) -> void:
	_omni(nm, at, "lamp", 2.6, 15.0, LIGHT_FIXTURE, shadow)


## The three things in the plaza that are worth floodlighting, and nothing else.
##
## Emitted with `_dilate_plaza` already false, because all three are hand-authored
## in `plaza.tscn` at final 104m coordinates and have nothing to be mapped from.
## Running these through `plaza_out` would push the tower's four uplights off the
## tower.
##
## Two of the three are *read out of* `plaza.tscn` rather than typed here, which
## is the same call the frontage makes and for the same reason: the perimeter and
## the landmarks are the only hand-authored geometry in the world, and a floodlight
## aimed at a literal is a floodlight that keeps pointing at where the tower used
## to be. The fountain is the exception and does not need the parse — it is round,
## so it is cylinders, and `_plaza_scene_boxes` only knows about boxes. Its
## position and radius are already in the plan.
func _plaza_lights() -> void:
	_tower_lights()
	_fountain_lights()
	_bandstand_lights()
	_cafe_lights()
	_tree_lights()
	_plaza_service_lights()


## The cafe terrace, and this one is a *mechanic* rather than a mood.
##
## The plaza has two instruments for telling the time without a HUD clock: how
## many people are standing in it, and whether the cafe tables are taken. That
## second one is the whole reason the tables disagree with the crowd — full at
## one and at six, half empty at four. All of it is invisible after sunset if the
## terrace is unlit, which quietly deletes an instrument at the exact hour the
## other one is hardest to read, because a thinning crowd in the dark looks like
## an empty plaza whatever the hour.
##
## So the terrace gets its own light, at table height, warm and close. It is also
## the plaza's only outdoor room and the thing the design keeps calling for the
## annulus to be wide enough to hold.
##
## Off `ParkPlan.PLAZA_CAFE`, which is the one copy of where the tables are —
## the same list `gen_props` builds them from and `gen_crowd` sits people at.
func _cafe_lights() -> void:
	for i in Plan.PLAZA_CAFE.size():
		var t: Dictionary = Plan.PLAZA_CAFE[i]
		var at: Vector2 = t["at"]
		var b := Plan.plaza_out(Vector3(at.x, 0.0, at.y))
		# Above the parasol rather than under it. A light under a canvas shade is
		# a light nobody can see from across the plaza, and the read this exists
		# for is "are those tables taken", made from thirty metres away.
		_omni("cafe_glow_%d" % i, b + Vector3(0, 3.1, 0), "warm", 2.2, 9.0,
			LIGHT_FIXTURE, i == 1)


## A handful of trees uplit from the root.
##
## Not all 28 — that would be a lit orchard, and the point of uplighting a tree
## is that it is one bright thing among dark ones. Every fourth, which lands
## seven of them scattered round the outer room by `open_spots`' own rejection
## sampling rather than by any pattern.
##
## They are the only vertical mass between the perimeter and the hub, so before
## this the middle distance was the darkest band in the plaza: pools of lamp
## light on the ground, a lit wall behind, and eight metres of black canopy in
## between. Uplighting a crown also does something no lamp does — it throws the
## branch shadows *up*, so the plaza has something on its ceiling.
func _tree_lights() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 0x7EE5
	var spots := Plan.open_spots(28, 11, 21.0, 35.0, 3.0, 5.5, _stood)
	for i in spots.size():
		# Consume the same two draws `_trees` does, in the same order, or the
		# heights this aims at are a different tree's. The generator is
		# deterministic and that is only useful if both readers step the stream
		# identically.
		var h := 3.4 + rng.randf() * 1.6
		var spread := 2.1 + rng.randf() * 0.8
		if i % 4 != 0:
			continue
		var p: Vector2 = spots[i]
		var b := _place(Vector3(p.x, 0, p.y), Vector3.ZERO, 0.0)
		_uplight("tree_up_%d" % i,
			b + Vector3(0.9, 0.12, 0.0),
			b + Vector3(0.2, h + spread * 0.6, 0.0),
			"foliage_up", 2.6, 9.0, 40.0)


## The two lights left on in the plaza after everyone has gone, and they are here
## because a test asked for them rather than because the plan did.
##
## `night_test.gd` walks the clock to two in the morning and checks that
## something is still burning. It failed: every `LIGHT_SERVICE` fitting in the
## park was in `_lane_lights`, which is in `boardwalk.tscn` — so the shut park
## read as powered only if you happened to be standing on the boardwalk, and the
## plaza, which is where the player actually is after close, went to absolute
## black. That is the power cut `night.md` explicitly does not want.
##
## Two, not a scheme. `night.md` asks for "a cart with its light still on", and
## the point of that image is that it is nearly the only one.
func _plaza_service_lights() -> void:
	# The photo hut, and it gets three rather than the one it had.
	#
	# The player works here. `night.md` names it as one of the two candidates for
	# what replaces the campfire — the anchor the shut park needs, the place you
	# leave from and come back to — and one dim window on one face is not an
	# anchor, it is a shed with a light on. What makes somewhere a place you
	# return to is that you can *find* it from across a dark 104m plaza, so this
	# is lit on the plaza side, over its counter, and under its own eaves.
	#
	# All three are SERVICE. The hut is the one building in the park that should
	# look the same at two in the morning as at nine in the evening, because the
	# thing it has to say after close is that it is still yours.
	var hut := _plaza_box("photo_hut")
	if not hut.is_empty():
		var at: Vector3 = hut["at"]
		var size: Vector3 = hut["size"]
		var west := at.x - size.x * 0.5
		# The serving window, facing the fountain.
		_omni("hut_window", Vector3(west - 0.4, at.y + 0.2, at.z),
			"warm", 2.4, 9.0, LIGHT_SERVICE, true)
		# Under the eaves at each end, so the building has an outline rather than
		# one bright patch. The roof sits at 3.85 with a 0.45 slab on it.
		for i in 2:
			var z: float = at.z + (-1.0 if i == 0 else 1.0) * (size.z * 0.5 - 0.8)
			_omni("hut_eave_%d" % i, Vector3(west - 0.2, 3.55, z),
				"warm", 1.2, 6.0, LIGHT_SERVICE)

	# The cart, with its light on. Placed against `_cart`'s own base and through
	# the same dilation, so it stays on the cart if the cart moves.
	_dilate_plaza = true
	_omni("cart_lamp", _place(Vector3(-6, 0, -10), Vector3(0, 1.8, 0), deg_to_rad(-18.0)),
		"warm", 1.5, 6.5, LIGHT_SERVICE)
	_dilate_plaza = false


func _plaza_box(nm: String) -> Dictionary:
	for box in _plaza_scene_boxes():
		if String(box["nm"]) == nm:
			return box
	return {}


## The clock tower, up all four faces.
##
## This is the one the whole park is aimed at — it stands on the gate axis, the
## 57m entrance street points at it, and it is dead centre in the turnstile
## opening from the apron. It is also the only readout the time has. A 40m tower
## that goes black at sunset takes the park's clock with it, so this is the
## uplighting that is doing a job rather than being handsome.
##
## Set 3.4m off a 5.6m shaft — close enough to graze, which is what puts the
## cap's overhang and the belfry in relief instead of flattening the whole shaft
## to one brightness. The beam runs past the top on purpose; a wash that stops
## exactly at the parapet draws a line across the masonry.
func _tower_lights() -> void:
	var shaft := _plaza_box("tower_shaft")
	if shaft.is_empty():
		push_error("no tower_shaft in %s — the tower would go dark" % PLAZA_SCENE_PATH)
		return
	var at: Vector3 = shaft["at"]
	var size: Vector3 = shaft["size"]
	var top := at.y + size.y * 0.5
	var out := size.x * 0.5 + 0.6
	var faces: Array[Vector3] = [Vector3(out, 0, 0), Vector3(-out, 0, 0),
		Vector3(0, 0, out), Vector3(0, 0, -out)]
	for i in faces.size():
		var p := Vector3(at.x, 0.25, at.z) + faces[i]
		# Aim just inside the far top corner, so the cone hugs the face rather
		# than standing off it. The tilt is small — this is very nearly straight
		# up, which is exactly the case `_uplight`'s up-vector fallback exists for.
		var aim := Vector3(at.x, top + 6.0, at.z) + faces[i] * 0.25
		# Only the face the street sees casts. One shadow-caster on a 40m tower
		# is what puts the clock's own hands and the cap's overhang onto the
		# shaft; four is four cubemaps for three views nobody takes.
		_uplight("tower_wash_%d" % i, p, aim, "wash", 7.0, 46.0, 24.0,
			LIGHT_FEATURE, faces[i].z > 0.0)

	# The clock face itself, lit from its own hood rather than from the ground.
	# A face washed from 30m below is legible as a bright square and not as a
	# time — the hands are thin and the uplight puts them in the same plane of
	# brightness as the dial behind them.
	#
	# **SERVICE, not FEATURE, and this is the one classification in the park that
	# is a game decision rather than a lighting one.** Everything else that
	# floodlights the tower goes out at close, and should: a floodlit tower at
	# two in the morning is the park still performing. But the clock is the only
	# readout the time has — there is no HUD clock, by design, and the whole
	# point of that decision is that knowing the hour is a small piece of knowing
	# the park. Switch the dial off with the rest of the tower and the after-close
	# park has no clock at all, which is not atmosphere, it is the removal of an
	# instrument at exactly the hour it gets interesting.
	#
	# It also gives the night its best image for free: a black 40m tower with a
	# lit face at the top of it.
	var dial_y := at.y + size.y * 0.5 - 6.0
	for i in faces.size():
		_omni("tower_dial_%d" % i,
			Vector3(at.x, dial_y + 2.2, at.z) + faces[i] * 1.35,
			"lamp", 1.6, 6.0, LIGHT_SERVICE)


## The fountain, from its own rim.
##
## Six stations round an 18m basin, each raking its own slice of the tiers rather
## than all six aiming at the middle — pointed at the centre they overlap into a
## single flat pool and the four tiers stop being four. Offset aim points keep a
## shadow under every lip.
func _fountain_lights() -> void:
	var c := Plan.FOUNTAIN_AT
	var r := Plan.FOUNTAIN_RADIUS
	for i in 6:
		var th := TAU * float(i) / 6.0
		var dir := Vector2(cos(th), sin(th))
		var p := Vector3(c.x + dir.x * (r - 1.4), 1.05, c.y + dir.y * (r - 1.4))
		# Up and inward, but not to the axis: a quarter of the way across keeps
		# the beam on the tier faces this station is actually in front of.
		var aim := Vector3(c.x + dir.x * r * 0.22, 7.4, c.y + dir.y * r * 0.22)
		_uplight("fountain_wash_%d" % i, p, aim, "wash", 2.8, 14.0, 38.0)


## The bandstand, lit from under its own roof.
##
## Uplighting would be wrong here and it is worth saying why: the bandstand is
## the one structure in the plaza the crowd goes *inside*, so the light belongs
## where the band would be. Washed from outside it reads as a monument; lit from
## within it reads as somewhere still open, which is what it is at nine in the
## evening.
func _bandstand_lights() -> void:
	var roof := _plaza_box("bandstand_roof")
	if roof.is_empty():
		push_error("no bandstand_roof in %s" % PLAZA_SCENE_PATH)
		return
	var at: Vector3 = roof["at"]
	var under := at.y - 0.5
	_omni("bandstand_glow", Vector3(at.x, under, at.z), "warm", 3.4, 16.0,
		LIGHT_FIXTURE, true)
	# And four at the eaves, so the roof's underside is not one flat disc of
	# light with a dark rim.
	var q: float = roof["size"].x * 0.5 - 1.4
	for i in 4:
		var th := TAU * float(i) / 4.0 + PI * 0.25
		_omni("bandstand_eave_%d" % i,
			Vector3(at.x + cos(th) * q, under - 0.2, at.z + sin(th) * q),
			"warm", 1.2, 8.0)


## The four inner bins sit on the fountain's skirt with the benches, and are
## written as bearings rather than as corners for that reason: on a circle they
## can be *interleaved* with the bench ring, and a bin pushed onto the skirt from
## a typed corner has no way of knowing a bench is already there. 60° off each
## bench at radius ten is six metres of daylight, which is a bin beside a bench
## rather than a bin in one.
func _bins() -> void:
	_stand_clear = 0.6
	var inner := [60.0, 130.0, 200.0, 270.0]
	var spots := []
	for a in inner:
		spots.append(Vector2(8.1 * cos(deg_to_rad(a)), 8.1 * sin(deg_to_rad(a))))
	# The last two moved off the picnic tables and the south planters. Both pairs
	# were 2–3m apart as written and both halves of each pair are pushed outward,
	# so they were converging rather than merely close.
	spots.append_array([
		Vector2(12, 12), Vector2(-14, 14), Vector2(3, -14),
		Vector2(-19, 7), Vector2(-21, 20), Vector2(-10, 22), Vector2(8, 20),
	])
	for i in spots.size():
		var b := Vector3(spots[i].x, 0, spots[i].y)
		_cyl("bin_%d_body" % i, b, Vector3(0, 0.42, 0), 0.32, 0.85, "metal")
		_cyl("bin_%d_lid" % i, b, Vector3(0, 0.865, 0), 0.36, 0.1, "blue")
	_stand_clear = 0.0


## Read out of `ParkPlan.PLAZA_CAFE` rather than declared here, because
## `gen_crowd.gd` has to put a guest on each of these chairs and was agreeing
## with this function by having the same three coordinates typed into it.
func _cafe() -> void:
	var shades := ["red", "yellow", "blue"]
	for i in Plan.PLAZA_CAFE.size():
		var spec: Dictionary = Plan.PLAZA_CAFE[i]
		var at: Vector2 = spec["at"]
		var b := Vector3(at.x, 0, at.y)
		var th := deg_to_rad(float(spec["theta"]))
		_cyl("table_%d_top" % i, b, Vector3(0, 0.74, 0), 0.6, 0.08, "white", th, 16)
		_cyl("table_%d_post" % i, b, Vector3(0, 0.37, 0), 0.07, 0.74, "metal", th, 8)
		_cyl("table_%d_umb_pole" % i, b, Vector3(0, 1.15, 0), 0.05, 2.3, "metal", th, 8)
		_cyl("table_%d_umb_top" % i, b, Vector3(0, 2.3, 0), 1.5, 0.12, shades[i], th, 12)
		var offs := Plan.CAFE_CHAIRS
		for j in offs.size():
			var cb: Vector3 = b + offs[j]
			var cth: float = th + deg_to_rad(30.0 * (j + 1))
			_cyl("chair_%d%d_post" % [i, j], cb, Vector3(0, 0.235, 0), 0.05, 0.47, "metal", cth, 8)
			_box("chair_%d%d_seat" % [i, j], cb, Vector3(0, 0.44, 0), Vector3(0.42, 0.07, 0.42), "white", cth)
			_box("chair_%d%d_back" % [i, j], cb, Vector3(0, 0.66, -0.16), Vector3(0.42, 0.48, 0.07), "white", cth)


## The queue belongs to the photo hut, so it is placed off `PHOTO_HUT_AT` rather
## than dilated. The hut is one of the few things that moved by decision instead
## of by the map — out to radius 28 because it was the one bearing with zero
## clearance — and a queue that followed the map would have ended up 6m from the
## door it is queuing at.
func _queue() -> void:
	_dilate_plaza = false
	var hut := Plan.PHOTO_HUT_AT
	var z := hut.y + 4.5
	var xs := [hut.x - 3.5, hut.x - 2.0, hut.x - 0.5, hut.x + 1.0, hut.x + 2.5]
	for i in xs.size():
		_cyl("stanchion_%d" % i, Vector3(xs[i], 0, z), Vector3(0, 0.5, 0), 0.06, 1.0, "metal", 0.0, 8)
	for i in xs.size() - 1:
		var mid: float = (xs[i] + xs[i + 1]) * 0.5
		_box("rope_%d" % i, Vector3(mid, 0, z), Vector3(0, 0.8, 0), Vector3(1.5, 0.05, 0.05), "red", 0.0, false)
	_dilate_plaza = true


func _bollards() -> void:
	for i in 5:
		_cyl("bollard_n_%d" % i, Vector3(-4 + i * 3.0, 0, -20), Vector3(0, 0.45, 0), 0.13, 0.9, "metal", 0.0, 8)
	for i in 5:
		_cyl("bollard_s_%d" % i, Vector3(-6 + i * 3.0, 0, 30), Vector3(0, 0.45, 0), 0.13, 0.9, "metal", 0.0, 8)
	# Neither the bollard lines nor the planters are pushed — a bollard line
	# crosses the walk because that is what bollards are for, and the planters
	# stand at the ends of it. The planters go on the register anyway: they are
	# 2.6m square, which is the largest thing in the plaza the tree scatter would
	# otherwise be free to grow through.
	var pl := [Vector2(-7, 26), Vector2(4, 26)]
	for i in pl.size():
		_box("planter_s_%d" % i, Vector3(pl[i].x, 0, pl[i].y), Vector3(0, 0.45, 0), Vector3(2.6, 0.9, 2.6), "accent")
		_note_stood(Plan.plaza_out2(pl[i]), 2.0)


## Two panels leaning together at the top. The tilt is about each panel's own
## X axis, and the offset is rotated by the same transform, so the tops meet.
func _aframes() -> void:
	_stand_clear = 0.8
	var spots := [Vector2(3, 10), Vector2(-9, -2), Vector2(12, -8)]
	var turns := [22.0, -40.0, 115.0]
	var lean := deg_to_rad(11.0)
	for i in spots.size():
		var b := Vector3(spots[i].x, 0, spots[i].y)
		var th := deg_to_rad(turns[i])
		_box("aframe_%d_a" % i, b, Vector3(0, 0.54, -0.16), Vector3(0.9, 1.1, 0.05), "wood", th, true, lean)
		_box("aframe_%d_b" % i, b, Vector3(0, 0.54, 0.16), Vector3(0.9, 1.1, 0.05), "yellow", th, true, -lean)
	_stand_clear = 0.0


## **One base with two boxes hung off it, where this was two bases 90cm apart.**
## They have to move together or not at all: pushed independently, two props that
## close together snap to nearly the same point on the same paved edge and end up
## inside each other, which is a worse fault than the one being fixed. Anything
## that reads as a pair gets built as a pair — see `_flagpoles` for the other.
func _newsboxes() -> void:
	_stand_clear = 0.8
	var b := Vector3(3.0, 0, 7.5)
	for i in 2:
		var th := deg_to_rad(12.0 + i * 20.0)
		# Shoulder to shoulder is right for newspaper boxes; inside each other is
		# not, and 0.45 apart with a 0.45 box is the second one.
		var at := Vector3(0.62 * (float(i) - 0.5), 0.0, 0.14 * (float(i) - 0.5))
		_box("newsbox_%d_body" % i, b, at + Vector3(0, 0.45, 0), Vector3(0.45, 0.9, 0.4), "red", th)
		_box("newsbox_%d_top" % i, b, at + Vector3(0, 0.9, 0), Vector3(0.5, 0.08, 0.45), "metal", th)
	_stand_clear = 0.0


## A pair, and built as one assembly for the reason `_newsboxes` gives — but here
## the failure is the opposite one and just as bad. The two poles stood 5m apart
## on the same line, and only the eastern one was in `spoke_ne`; pushed one at a
## time, one would move and one would not, and two flagpoles that no longer
## agree about where the line is are not a pair any more.
## `_stand_clear` is asked for on the **base**, so a wide assembly has to ask for
## its own half-width on top of the margin it wants. Five metres of pair is 2.5
## of that, and asking for 0.5 like a single pole would left the base clear and
## the east pole still half a metre inside `spoke_ne`.
func _flagpoles() -> void:
	_stand_clear = 3.0
	var b := Vector3(18.0, 0, -16.0)
	var shades := ["red", "yellow"]
	for i in shades.size():
		var at := Vector3(2.5 * (float(i) * 2.0 - 1.0), 0.0, 0.0)
		_cyl("flagpole_%d_pole" % i, b, at + Vector3(0, 3.0, 0), 0.07, 6.0, "white", 0.0, 8)
		_box("flagpole_%d_banner" % i, b, at + Vector3(0, 4.6, 0.35),
			Vector3(0.08, 2.2, 0.7), shades[i], 0.0, false)
	_stand_clear = 0.0


func _cart() -> void:
	_stand_clear = 1.5
	var c := Vector3(-6, 0, -10)
	var th := deg_to_rad(-18.0)
	_box("cart_body", c, Vector3(0, 0.6, 0), Vector3(2.0, 1.2, 1.1), "white", th)
	_box("cart_roof", c, Vector3(0, 1.55, 0), Vector3(2.4, 0.1, 1.5), "red", th)
	_cyl("cart_wheel_l", c, Vector3(-0.8, 0.22, 0.6), 0.22, 0.1, "metal", th + PI / 2, 10)
	_cyl("cart_wheel_r", c, Vector3(0.8, 0.22, 0.6), 0.22, 0.1, "metal", th + PI / 2, 10)
	_stand_clear = 0.0


func _stroller() -> void:
	_stand_clear = 0.9
	var s := Vector3(-3.2, 0, 8.4)
	var th := deg_to_rad(34.0)
	_box("stroller_basket", s, Vector3(0, 0.62, 0), Vector3(0.55, 0.5, 0.8), "blue", th)
	_box("stroller_handle", s, Vector3(0, 0.86, -0.28), Vector3(0.5, 0.06, 0.06), "metal", th)
	_cyl("stroller_leg", s, Vector3(0, 0.19, 0), 0.04, 0.38, "metal", th, 6)
	_cyl("stroller_wheel", s, Vector3(0, 0.1, 0.34), 0.1, 0.06, "metal", th + PI / 2, 8)
	_stand_clear = 0.0


## Leaning against the west face of building_east, which starts at x = 20.
func _ladder() -> void:
	var base := Vector3(19.3, 0, 2.0)
	var th := deg_to_rad(90.0)
	var lean := deg_to_rad(16.0)
	var half := 1.5
	# Where the rail's own +Y axis points once turned and tilted.
	var up: Vector3 = _xform(th, lean, Vector3.ZERO).basis * Vector3.UP
	var centre: Vector3 = _place(base, Vector3(0, 0, 0.28), th) + Vector3(0, half * up.y, 0)

	for s in [-1.0, 1.0]:
		var side: Vector3 = Basis(Vector3.UP, th) * Vector3(0.22 * s, 0, 0)
		var rail := CSGBox3D.new()
		rail.size = Vector3(0.06, 3.0, 0.06)
		rail.material = mats["metal"]
		rail.use_collision = true
		rail.transform = _xform(th, lean, centre + side)
		_add(rail, "ladder_rail_%s" % ("a" if s < 0 else "b"))

	# Rungs ride the rail axis, so they cannot drift off it.
	for r in 6:
		var t: float = -1.15 + r * 0.46
		var rung := CSGBox3D.new()
		rung.size = Vector3(0.5, 0.05, 0.05)
		rung.material = mats["metal"]
		rung.use_collision = false
		rung.transform = _xform(th, lean, centre + up * t)
		_add(rung, "ladder_rung_%d" % r)


## **All three of these were adrift, and re-anchoring them is the other half of
## the `_sphere` fix.**
##
## The bug in the primitive separated each balloon from its own string. What it
## hid was a second fault underneath: the balloons were *also* separated from the
## things they belong to, and fixing the strings alone would have left three
## correctly-assembled balloons tied to nothing in the middle of open paving.
##
## They were written as bare coordinates in the 80m plaza — (5.6, 4.9) for the
## pair, radius 7.4 — on the theory that the dilation would carry them along with
## whatever they were tied to. It does not, and could not: the hut's bench does
## not move by `plaza_out` at all. The hut went from radius 12 to radius 28 *by
## hand* on 2026-08-13, and `_benches` places its bench in final coordinates with
## the dilation switched off for exactly that reason. So the pair mapped to
## radius 12.8 and the bench they are tied to is at radius 20.9, eight metres
## away, and no amount of getting the string right would have joined them.
##
## The fix is the rule the project already has, applied one level up: hang each
## balloon off the *base of the thing it belongs to* and let the offset be local.
## The pair take the hut bench's base and yaw, so they follow it wherever it
## goes; the loose one takes `bollard_s_2`'s, which is a dilated position, so it
## goes on being in contact with the bollard rather than 15cm off it — the gap
## would have been scaled by the map along with everything else if it had been
## baked into the base.
func _balloons() -> void:
	# The pair, tied to the back rail of the bench by the photo hut. In final
	# coordinates with the dilation off, because that is where the bench is —
	# see `_benches`, which switches it off for the same three props.
	_dilate_plaza = false
	var bench := Vector3(Plan.PHOTO_HUT_AT.x, 0.0, Plan.PHOTO_HUT_AT.y) + HUT_BENCH_AT
	var th := deg_to_rad(HUT_BENCH_YAW)
	# `_bench` builds 1.8m long with its back at z −0.22 and its top at 0.98, so
	# these tie on just inside the left end of the rail and float above it.
	# Far enough apart to be two balloons. At 20cm they intersected — which the
	# overlap rule permits, but two 26cm spheres 20cm apart are one lumpy sphere,
	# and the pair of strings landed on top of each other as well.
	var tied := [
		{"local": Vector3(0.84, 0.0, -0.17), "y": 2.05, "mat": "red"},
		{"local": Vector3(0.42, 0.0, -0.28), "y": 2.34, "mat": "yellow"},
	]
	for i in tied.size():
		var d: Dictionary = tied[i]
		var l: Vector3 = d["local"]
		var y: float = d["y"]
		_sphere("balloon_%d" % i, bench, l + Vector3(0.0, y, 0.0), 0.26, d["mat"], th)
		# From the rail rather than from the ground. A string that runs to the
		# paving says the balloon is tied to the floor, which is not a thing
		# anybody does with a balloon.
		_box("balloon_%d_string" % i, bench,
			l + Vector3(0.0, (y + HUT_BENCH_RAIL) * 0.5, 0.0),
			Vector3(0.02, y - HUT_BENCH_RAIL, 0.02), "white", th, false)
	_dilate_plaza = true

	# One that came down, caught against a bollard at the south entrance with its
	# string trailing on the ground. Sitting loose on open concrete it read as
	# half-buried no matter where it was in Y — a ball resting on a plane and a
	# ball sunk into one have the same silhouette. Leaning it on something and
	# giving it a string is what makes it legible as a balloon.
	#
	# The base is the middle bollard of the south line, written the way
	# `_bollards` writes it so the two cannot disagree about where it is.
	var r := 0.22
	var bollard := Vector3(-6.0 + 2.0 * 3.0, 0.0, 30.0)
	var rest := Vector3(0.13 + r, 0.0, 0.06)
	_sphere("balloon_2", bollard, rest + Vector3(0.0, r, 0.0), r, "blue")
	# Trailing along z rather than at an angle, because the bollard line runs in
	# x: a string parallel to the line reads as part of it.
	_box("balloon_2_string", bollard, rest + Vector3(0.0, 0.012, 0.46),
		Vector3(0.018, 0.018, 0.9), "white", 0.0, false)


func _litter() -> void:
	var spots := [
		Vector3(2.3, 0, 12.4), Vector3(-4.6, 0, 6.2), Vector3(8.9, 0, -3.1),
		Vector3(-9.4, 0, 11.8), Vector3(11.2, 0, 6.7), Vector3(-2.1, 0, -9.6),
		Vector3(5.7, 0, 17.3), Vector3(-12.6, 0, -4.4), Vector3(14.8, 0, -12.2),
		Vector3(0.9, 0, -17.4), Vector3(-16.2, 0, 7.1), Vector3(17.6, 0, 15.9),
		Vector3(-15.4, 0, 3.2), Vector3(-11.8, 0, 16.4), Vector3(-18.9, 0, -8.7),
		Vector3(-7.3, 0, 22.6), Vector3(-20.4, 0, 11.2), Vector3(3.6, 0, 25.8),
		Vector3(-13.1, 0, -18.9), Vector3(10.4, 0, 22.1),
	]
	for i in spots.size():
		var th := deg_to_rad(float((i * 47) % 360))
		if i % 2 == 0:
			_cyl("litter_%d" % i, spots[i], Vector3(0, 0.06, 0), 0.055, 0.12, "white", th, 8, false)
		else:
			_box("litter_%d" % i, spots[i], Vector3(0, 0.006, 0), Vector3(0.22, 0.012, 0.16), "white", th, false)


func _picnic() -> void:
	_stand_clear = 1.4
	var spots := [Vector2(-13, 18), Vector2(-17, 15)]
	var turns := [25.0, -15.0]
	for i in spots.size():
		var b := Vector3(spots[i].x, 0, spots[i].y)
		var th := deg_to_rad(turns[i])
		_box("picnic_%d_top" % i, b, Vector3(0, 0.75, 0), Vector3(1.7, 0.09, 0.85), "wood", th)
		_box("picnic_%d_bench_a" % i, b, Vector3(0, 0.44, 0.72), Vector3(1.7, 0.08, 0.32), "wood", th)
		_box("picnic_%d_bench_b" % i, b, Vector3(0, 0.44, -0.72), Vector3(1.7, 0.08, 0.32), "wood", th)
		_box("picnic_%d_leg_a" % i, b, Vector3(-0.7, 0.37, 0), Vector3(0.1, 0.75, 1.7), "metal", th)
		_box("picnic_%d_leg_b" % i, b, Vector3(0.7, 0.37, 0), Vector3(0.1, 0.75, 1.7), "metal", th)
	_stand_clear = 0.0


func _crates() -> void:
	var c := Vector3(-19, 0, -6)
	_box("crate_a", c, Vector3(0, 0.4, 0), Vector3(0.9, 0.8, 0.9), "wood", deg_to_rad(12.0))
	_box("crate_b", c, Vector3(0.15, 1.12, 0.2), Vector3(0.85, 0.7, 0.85), "wood", deg_to_rad(-24.0))
	_box("crate_c", c, Vector3(1.05, 0.35, -0.3), Vector3(0.8, 0.7, 0.8), "wood", deg_to_rad(40.0))


# --- the park beyond the plaza ----------------------------------------------
#
# Silhouettes only. They sit well outside the perimeter walls, carry no
# collision, and are never reachable — this is the view of rides, not rides.
# Heights and distances are chosen so the perimeter buildings crop their bases,
# so they arrive as glimpses between rooflines rather than as a skyline.


## A box stretched between two points, oriented with Basis.looking_at so no
## matrix is written by hand.
func _strut(nm: String, a: Vector3, b: Vector3, thickness: float, mat: String) -> void:
	var d := b - a
	var len := d.length()
	if len < 0.001:
		return
	var up := Vector3.UP if absf(d.normalized().dot(Vector3.UP)) < 0.99 else Vector3.FORWARD
	var box := CSGBox3D.new()
	box.size = Vector3(thickness, thickness, len)
	box.material = mats[mat]
	box.use_collision = false
	box.transform = Transform3D(Basis.looking_at(d, up), a + d * 0.5)
	_add(box, nm)


func _far_cyl(nm: String, origin: Vector3, radius: float, height: float, mat: String, sides := 12) -> void:
	var c := CSGCylinder3D.new()
	c.radius = radius
	c.height = height
	c.sides = sides
	c.material = mats[mat]
	c.use_collision = false
	c.transform = Transform3D(Basis.IDENTITY, origin)
	_add(c, nm)


## The classic wooden out-and-back: lift hill, first drop, then camelbacks.
## Built as a profile of support columns with the track line running over them.
##
## `vscale` raises the profile without touching the footprint, and only the
## plaza's skyline uses it. The boardwalk's coaster and its twin in the far
## tableau must stay at 1.0 and stay identical to each other, or the silhouette
## jumps when the player walks through the gate.
func _wooden_coaster(origin: Vector3, heading: float, mat: String, vscale := 1.0) -> void:
	var profile := [3.0, 9.0, 15.0, 21.0, 26.0, 27.0, 9.0, 19.0, 8.0, 15.5, 7.0, 12.0, 6.5, 9.0, 5.0]
	var step := 7.0
	var dir := Basis(Vector3.UP, heading) * Vector3.FORWARD
	var prev := Vector3.ZERO
	for i in profile.size():
		var foot: Vector3 = origin + dir * (i * step)
		var h: float = profile[i] * vscale
		_far_cyl("coaster_col_%d" % i, foot + Vector3(0, h * 0.5, 0), 0.55, h, mat, 6)
		# cross-bracing, which is most of what reads as "wooden" at distance
		if h > 8.0 * vscale:
			_strut("coaster_brace_%d" % i, foot + Vector3(0, 1.0, 0), foot + Vector3(0, h - 1.0, 0) + dir * 2.5, 0.35, mat)
		var top: Vector3 = foot + Vector3(0, h, 0)
		if i > 0:
			_strut("coaster_track_%d" % i, prev, top, 0.7, mat)
		prev = top


## Slender shaft, observation deck, spire. The park's landmark.
func _tower(origin: Vector3, mat: String, accent: String) -> void:
	_far_cyl("tower_shaft", origin + Vector3(0, 21, 0), 1.7, 42.0, mat, 10)
	_far_cyl("tower_deck", origin + Vector3(0, 32, 0), 5.6, 2.4, accent, 14)
	_far_cyl("tower_deck_roof", origin + Vector3(0, 33.6, 0), 6.3, 0.7, mat, 14)
	_far_cyl("tower_spire", origin + Vector3(0, 46, 0), 0.45, 9.0, mat, 6)


## A wheel is a ring on two legs; the ring is what carries at distance.
##
## `heading` turns the whole assembly about Y. Standing the torus up alone
## leaves it facing north-south, which from the plaza is edge-on — a wheel seen
## edge-on is a line, and a line is not the seaside icon anybody came for.
func _wheel(origin: Vector3, mat: String, heading := 0.0) -> void:
	var hub := origin + Vector3(0, 18.0, 0)
	var turn := Basis(Vector3.UP, heading)
	var ring := CSGTorus3D.new()
	ring.inner_radius = 12.2
	ring.outer_radius = 13.2
	# sides walks the big circle, ring_sides is the tube cross-section.
	ring.sides = 28
	ring.ring_sides = 6
	ring.material = mats[mat]
	ring.use_collision = false
	# A torus lies flat by default; stand it up, then turn it to face the plaza.
	ring.transform = Transform3D(turn * Basis(Vector3.RIGHT, PI * 0.5), hub)
	_add(ring, "wheel_ring")

	_far_cyl("wheel_hub", hub, 1.0, 2.0, mat, 8)
	for i in 8:
		var a := TAU * i / 8.0
		var rim := hub + turn * Vector3(cos(a) * 12.7, sin(a) * 12.7, 0)
		_strut("wheel_spoke_%d" % i, hub, rim, 0.3, mat)
	_strut("wheel_leg_a", origin + turn * Vector3(-11, 0, 0), hub, 1.2, mat)
	_strut("wheel_leg_b", origin + turn * Vector3(11, 0, 0), hub, 1.2, mat)


## Everything west of the plaza wall, seen from the overlook and never reached.
##
## Laid out in bands running north-south, so that what the arch frames is a
## sequence receding rather than a backdrop: the shore below the parapet, a
## frontage of buildings one deep, the promenade behind them, then water.
## Santa Cruz is the reference for the ribbon being one building deep and for
## both ends of a strip needing to be closed by something.
## The boardwalk sits well below the plaza and well out from it. Both were wrong
## on the first pass — a strip a metre down and twelve metres out does not
## recede, it looms, and the frontage read as a wall across the view rather than
## as somewhere else. Down a bluff is also how the real ones are built: the park
## on the rise, the boardwalk at beach level.
const SHORE_TOP := Plan.SHORE_TOP
const WATER_TOP := Plan.WATER_TOP
const SHORE_EDGE := Plan.SHORE_EDGE
const SHORE_FROM_X := Plan.SHORE_FROM_X
const FRONT_X := Plan.FRONT_X
const FRONT_DEPTH := Plan.FRONT_DEPTH
const BACK_LANE_X := Plan.BACK_LANE_X
const PROMENADE_X := Plan.PROMENADE_X

## The frontage opens here, and the gap is aimed at the plaza arch. This is the
## whole composition: the arch frames a gap, the gap frames the pier, and the
## wheel sits off to one side where you have to move to uncover it.
const GAP_FROM := Plan.GAP_FROM
const GAP_TO := Plan.GAP_TO
const ALLEY_Z := Plan.ALLEY_Z

const WALK_FROM_Z := Plan.WALK_FROM_Z
const WALK_TO_Z := Plan.WALK_TO_Z
const FRONT_FROM_Z := Plan.FRONT_FROM_Z
const FRONT_TO_Z := Plan.FRONT_TO_Z
const WHEEL_AT := Plan.WHEEL_AT
const COASTER_STATION := Plan.COASTER_STATION
const COASTER_TO_Z := Plan.COASTER_TO_Z
const PIER_ROOT := Plan.PIER_ROOT
const PIER_LENGTH := Plan.PIER_LENGTH
const PIER_HALF_W := Plan.PIER_HALF_W
const PAVILION_AT := Plan.PAVILION_AT


const FRONTAGE := Plan.FRONTAGE_UNITS


# ---------------------------------------------------------------------------
# The west, part one: the shell both sections stand on
# ---------------------------------------------------------------------------

## Water, bluff and shore — the ground and the horizon, identical from either
## side of the seam, and therefore the only part of the west that is not built
## twice.
##
## The shore collides now. It did not when the whole west was scenery, and that
## was correct then: nothing could reach it. It is the boardwalk's floor.
func _west_shell() -> void:
	_box("water", Vector3.ZERO, Vector3(-198, WATER_TOP - 4.0, 0),
		Vector3(240, 8.0, 400), "water", 0.0, false)
	# The face the plaza stands on. Everything west of the parapet drops away
	# here, which is what turns the parapet into an overlook rather than a fence.
	#
	# **One piece since 2026-08-14.** It used to be cut into five — two long runs
	# with a slot between them, a floor under the slot and three fillers round it —
	# because the stair descended *inside* the bluff and the rock had to be taken
	# out of its way. The stair is hung on the face now, so the rock is just rock,
	# and the top of it is a ledge the player can walk out onto through the gap in
	# the parapet.
	_box("bluff", Vector3.ZERO,
		Vector3((Plan.BLUFF_FACE_X + Plan.BLUFF_BACK_X) * 0.5, -6.0 + GROUND_SEAM, 0.0),
		Vector3(Plan.BLUFF_BACK_X - Plan.BLUFF_FACE_X, 12.0, 341.0), "far_warm")
	# The face, dressed. Six metres of blank plane is what the player looks back at
	# from the lane, and until 2026-08-14 that is exactly what it was — the reason
	# the two sides of the descent did not read as the same place was half the
	# hidden stair and half this.
	#
	# A seawall, then: a coping along the top edge and buttresses down it at eight
	# metres. Only over the stretch the boardwalk can see; north and south of that
	# it is scenery at ninety metres and a blank cliff is correct.
	var face := Plan.BLUFF_FACE_X
	_box("bluff_coping", Vector3.ZERO, Vector3(face + 0.15, -0.35, 0.0),
		Vector3(1.1, 0.7, 150.0), "far_shade", 0.0, false)
	for i in 19:
		var bz := -72.0 + float(i) * 8.0
		_box("bluff_buttress_%d" % i, Vector3.ZERO,
			Vector3(face - 0.24, -3.43, bz), Vector3(0.5, 5.26, 1.2), "far_warm", 0.0, false)
	# The ground the boardwalk stands on: back lane, frontage, promenade. Runs
	# 2m east under the bluff's west face rather than butting against it.
	var width := SHORE_FROM_X - SHORE_EDGE
	_box("shore", Vector3.ZERO,
		Vector3((SHORE_FROM_X + SHORE_EDGE) * 0.5, SHORE_TOP - 3.0, 0),
		Vector3(width, 6.0, 340), "far_warm")


# ---------------------------------------------------------------------------
# The west, part two: the tableau
# ---------------------------------------------------------------------------

## What the west looks like from the overlook, and only from there.
##
## Laid out in bands running north-south, so that what the arch frames is a
## sequence receding rather than a backdrop: the shore below the parapet, a
## frontage of buildings one deep, the promenade behind them, then water.
## Santa Cruz is the reference for the ribbon being one building deep and for
## both ends of a strip needing to be closed by something.
##
## Everything in here has a full-fidelity twin in `boardwalk.tscn` standing in
## the same place, and the two are never in the tree together.
func _west_far() -> void:
	_frontage_far()
	_pier_far(Vector3(PIER_ROOT.x, SHORE_TOP, PIER_ROOT.y))
	# Turned to face the plaza. Off the arch's centre line on purpose: from the
	# fountain the north pier covers it, and a step or two north uncovers it.
	_wheel(Vector3(WHEEL_AT.x, SHORE_TOP, WHEEL_AT.y), "far", PI * 0.5)
	# The plaza's half of the west seam. Here because this scene is the plaza's
	# and only the plaza's — it is thrown away at the moment of the crossing,
	# which is exactly the life a gate pointing west should have.
	_arch_seam(&"plaza", &"boardwalk")
	# The north end of the strip, closed by the coaster rather than trailing off.
	# Same origin the section builds it at, or the silhouette shifts eight metres
	# when the player walks through the gate.
	_wooden_coaster(Vector3(FRONT_X, SHORE_TOP, COASTER_STATION.y - 2.0),
		0.0, "far_warm")

	# Masts along the promenade. In daylight they are the thing that says somebody
	# strung lights here, without a single light being modelled.
	var z := -46.0
	var n := 0
	var masts: Array[float] = []
	while z <= 46.0:
		if z < GAP_FROM - 3.0 or z > GAP_TO + 3.0:
			_cyl("mast_%d" % n, Vector3.ZERO, Vector3(PROMENADE_X + 4.0, SHORE_TOP + 4.0, z),
				0.22, 8.0, "far_shade", 0.0, 6, false)
			masts.append(z)
			n += 1
		z += 11.0

	_west_far_lights(masts)


## The tableau after dark, which the tableau did not have.
##
## This is the gap the night test could not see, because the test walks the clock
## in the plaza and counts lights, and the number it counts was right — the west
## was black for the opposite reason, that a whole scene had none. From the
## overlook at nine in the evening the arch framed a hole.
##
## Which would have broken the section's central trick. The far place is fake and
## permanently visible, the real one loads behind a threshold — and that only
## works while the fake one is worth looking at. An unlit tableau does not read as
## a boardwalk at night, it reads as the edge of the world.
##
## **Almost all of it is emissive geometry rather than lights, and that is the
## right answer here rather than a saving.** At 60 to 130m a light source is
## indistinguishable from a bright speck; what carries is the *pattern* of specks
## — a strung line, a wheel's circle, a row of shop windows. Real lights this far
## from the player would light massing that has no collision, no detail and no
## business being lit. Four are kept for the shapes big enough to hold a
## gradient.
##
## It is also the cheapest thing in the park to build, because the boardwalk's
## own night presentation established the vocabulary: same `bulb` material, same
## three-material driver, no new state.
func _west_far_lights(masts: Array[float]) -> void:
	# Festoons between the masts. The daylight comment above says the masts imply
	# strung lights; after dark the implication becomes the thing itself, and it
	# is the strongest read in the tableau because it is a *line* of points 90m
	# long and the eye follows it.
	for i in masts.size() - 1:
		var from_z: float = masts[i]
		var to_z: float = masts[i + 1]
		if to_z - from_z > 12.0:
			continue
		for b in 4:
			var t := (float(b) + 1.0) / 5.0
			_sphere("far_bulb_%d_%d" % [i, b],
				Vector3(PROMENADE_X + 4.0, SHORE_TOP + 7.4 - 0.5 * sin(PI * t),
					lerpf(from_z, to_z, t)), Vector3.ZERO, 0.16, "bulb")

	# The wheel's rim, which is the single most recognisable night silhouette in
	# the section and the reason the wheel was turned to face the plaza at all.
	# Same 24 as the real one, so walking down does not change its count.
	var hub := Vector3(WHEEL_AT.x, SHORE_TOP + 18.6, WHEEL_AT.y)
	for i in 24:
		var a := TAU * float(i) / 24.0
		_sphere("far_wheel_bulb_%d" % i, hub,
			Vector3(0, sin(a) * Plan.WHEEL_RADIUS, cos(a) * Plan.WHEEL_RADIUS),
			0.22, "bulb")

	# Lit windows along the frontage. One band per unit at first-floor height,
	# stopping short of the gap — the 24m opening the arch is aimed at has to
	# stay a dark slot, because it is the hole the real section is behind and a
	# lit band across it would close it.
	for i in FRONTAGE.size():
		var unit: Dictionary = FRONTAGE[i]
		var from: float = unit["from"]
		var to: float = unit["to"]
		var mid := (from + to) * 0.5
		if mid > GAP_FROM - 2.0 and mid < GAP_TO + 2.0:
			continue
		_box("far_front_lit_%s" % unit["nm"], Vector3.ZERO,
			Vector3(FRONT_X - FRONT_DEPTH * 0.5 - 0.3, SHORE_TOP + 2.6, mid),
			Vector3(0.3, 1.1, (to - from) * 0.62), "bulb", 0.0, false)

	# The pavilion at the pier head, lit the same cool it is up close so the two
	# versions of the same building are the same colour from either side of the
	# seam.
	var head := Vector3(PAVILION_AT.x, SHORE_TOP, PAVILION_AT.y)
	_omni("far_pavilion_glow", head + Vector3(0, 7.0, 0), "cyan", 3.0, 26.0)
	_omni("far_wheel_glow", hub, "rose", 3.0, 30.0)
	# And two down the strip, so the promenade has some fall-off along it rather
	# than being an even line of beads on black.
	for i in 2:
		_omni("far_prom_glow_%d" % i,
			Vector3(PROMENADE_X, SHORE_TOP + 5.0, -30.0 + float(i) * 46.0),
			"lamp", 2.0, 24.0)


func _frontage_far() -> void:
	for i in FRONTAGE.size():
		var unit: Dictionary = FRONTAGE[i]
		var from: float = unit["from"]
		var to: float = unit["to"]
		var height: float = unit["h"]
		var mid := (from + to) * 0.5
		var depth := to - from
		var mat := "far" if i % 2 == 0 else "far_warm"
		_box("front_%s" % unit["nm"], Vector3.ZERO,
			Vector3(FRONT_X, SHORE_TOP + height * 0.5, mid),
			Vector3(FRONT_DEPTH, height, depth), mat, 0.0, false)
		# A parapet lip, so the rooflines are edges rather than the tops of slabs.
		_box("front_%s_cap" % unit["nm"], Vector3.ZERO,
			Vector3(FRONT_X, SHORE_TOP + height + 0.25, mid),
			Vector3(FRONT_DEPTH + 1.0, 0.5, depth + 0.6), "far_shade", 0.0, false)


## What runs out over the water. A strip needs stops or it trails off, so this
## one ends in a pavilion rather than in nothing.
func _pier_far(root: Vector3) -> void:
	var deck := root + Vector3(-PIER_LENGTH * 0.5, 0.4, 0)
	_box("pier_deck", Vector3.ZERO, deck, Vector3(PIER_LENGTH, 0.5, PIER_HALF_W * 2.0),
		"far_warm", 0.0, false)
	_box("pier_rail_n", Vector3.ZERO, deck + Vector3(0, 0.7, -PIER_HALF_W + 0.1),
		Vector3(PIER_LENGTH, 0.9, 0.2), "far_shade", 0.0, false)
	_box("pier_rail_s", Vector3.ZERO, deck + Vector3(0, 0.7, PIER_HALF_W - 0.1),
		Vector3(PIER_LENGTH, 0.9, 0.2), "far_shade", 0.0, false)

	var piles := int(PIER_LENGTH / 5.0)
	for i in piles:
		var x := root.x - 3.0 - i * 5.0
		for side in [-3.0, 3.0]:
			_cyl("pile_%d_%s" % [i, "n" if side < 0.0 else "s"], Vector3.ZERO,
				Vector3(x, WATER_TOP - 0.4, root.z + side), 0.28, 4.0,
				"far_shade", 0.0, 6, false)

	var head := Vector3(PAVILION_AT.x, root.y, PAVILION_AT.y)
	_box("pier_pavilion", Vector3.ZERO, head + Vector3(0, 3.4, 0),
		Vector3(12.0, 6.0, 13.0), "far", 0.0, false)
	_box("pier_pavilion_roof", Vector3.ZERO, head + Vector3(0, 6.7, 0),
		Vector3(14.0, 0.6, 15.0), "far_shade", 0.0, false)
	_cyl("pier_pavilion_spire", Vector3.ZERO, head + Vector3(0, 9.5, 0),
		0.3, 5.0, "far_shade", 0.0, 6, false)


## The descent, and the whole of it is `_west_cascade` below. What used to live
## here — a 2.6m flight in a slot, then on the face, then a switchback ramp
## beside it — is all gone; see `ParkPlan.CASCADE_AXIS_Z` for the history and
## why the shape kept moving.
const FLIGHT_RISE := Plan.FLIGHT_RISE
const FLIGHT_GOING := Plan.FLIGHT_GOING


## The treads are scenery and the ramp under them is the floor.
##
## CharacterBody3D has no step-up: a quarter-metre riser is a ninety-degree wall,
## so a stair built out of boxes is walkable down and impassable coming back.
## Verified by driving the player at it rather than by looking at it, which a
## screenshot could not have told us. A ramp at the slope of the nosings is
## flush with every one of them and under forty-five degrees, so it is floor.
##
## **And it hid the stair completely, which no screenshot had been pointed at
## until 2026-08-14.** A ramp on the nosing line runs from the *back* of one
## tread to the front of the next, so over each tread it stands up to a full
## riser above it — and at the same width it covers every one. What the player
## walked on was a smooth slope, and what they said about it was "it snakes down
## a narrow ramp". They were describing it exactly.
##
## Two things put the steps back without putting a wall in front of the capsule.
## The ramp is **narrower than the treads**, so the treads stand out past it on
## both sides and the flight has a stepped edge — the west one outboard of the
## rail, where a body cannot reach it, and the east one buried in the bluff. And
## each nosing gets a strip three centimetres proud of the ramp, which is under
## the lip the ground planes already carry everywhere and reads as a step at any
## distance. Neither is load-bearing; the ramp is still the floor.
func _flight_ramp(nm: String, top_a: Vector3, top_b: Vector3, theta: float,
		width := 0.0, mat := "accent") -> void:
	var span := top_b - top_a
	var horizontal := Vector2(span.x, span.z).length()
	var phi := atan2(-span.y, horizontal)
	var mid := (top_a + top_b) * 0.5
	var thickness := 0.4
	# Back the slab off along its own up-axis so its top face lands on the line
	# the nosings sit on.
	var up := (Basis(Vector3.UP, theta) * Basis(Vector3.RIGHT, phi)).y
	_box(nm, mid - up * (thickness * 0.5), Vector3.ZERO,
		Vector3(width if width > 0.0 else 4.0, thickness, span.length()),
		mat, theta, true, phi)


## The cascade: the whole descent as one monument. See `ParkPlan.CASCADE_AXIS_Z`.
##
## Built rather than cut, because the park has no CSG subtraction in its
## vocabulary — the arched niches are a gap left between jambs with a stepped
## head over it, which at greybox scale reads as an arch and at any scale reads
## as deliberate.
func _west_cascade() -> void:
	var axis := Plan.CASCADE_AXIS_Z
	var top_x := Plan.CASCADE_TOP_X
	var drop := Plan.CASCADE_DROP
	var floor_y := SHORE_TOP
	var risers := int(round(drop / FLIGHT_RISE))
	var run := FLIGHT_GOING * risers
	var half := Plan.FLIGHT_W * 0.5

	# --- the middle flight, straight down the arch's axis ---
	for i in risers:
		var top := -FLIGHT_RISE * (i + 1)
		var x := top_x - FLIGHT_GOING * (i + 0.5)
		_box("cascade_tread_%d" % i, Vector3.ZERO, Vector3(x, top - 0.26, axis),
			Vector3(FLIGHT_GOING, 0.5, Plan.FLIGHT_W + 0.8), "accent", 0.0, false)
		_box("cascade_nosing_%d" % i, Vector3.ZERO,
			Vector3(top_x - FLIGHT_GOING * (i + 1), top + 0.015, axis),
			Vector3(0.16, 0.03, Plan.FLIGHT_W - 0.2), "far_shade", 0.0, false)
	_flight_ramp("cascade_ramp", Vector3(top_x, 0.0, axis),
		Vector3(top_x - run, -drop, axis), -PI * 0.5, Plan.FLIGHT_W, "far_shade")
	_box("cascade_foot", Vector3.ZERO,
		Vector3(top_x - run - 0.9, floor_y - 0.28, axis),
		Vector3(2.4, 0.5, Plan.FLIGHT_W + 0.8), "accent")
	# The apron at the bottom: two broad shallow steps spreading into the court,
	# which is what the Cascade does and what stops a flight ending in a line.
	for i in 2:
		_box("cascade_apron_%d" % i, Vector3.ZERO,
			Vector3(top_x - run - 2.2 - float(i) * 1.1, floor_y - 0.1 - float(i) * 0.1,
				axis),
			Vector3(1.1, 0.2 + float(i) * 0.2, Plan.FLIGHT_W + 2.4 + float(i) * 2.4),
			"accent")

	_cascade_wall(-1.0)
	_cascade_wall(1.0)
	_cascade_portal()
	_cascade_wing(-1.0, true)
	_cascade_wing(1.0, false)

	# --- the eyes ---
	#
	# Two globes level with each other and set either side of the flight, just
	# outboard of where the wings spring. On a ray that is exactly where the eyes
	# sit, and from the pier — 130m out, which is where this thing is meant to be
	# looked at — they are the two points that make the silhouette read as a face
	# rather than as masonry.
	#
	# **Moved outboard onto the wing's own coping**, off the head. They used to
	# stand at 6.6 off the axis, which is between the flight's edge and the wing's
	# springing — in other words squarely in the doorway, and a 32cm post in a 3m
	# gap is a bollard. `walk_test` walked into it from both sides. Out here they
	# stand on the strip of coping between the bluff and the wing's deck, which is
	# ground nobody crosses, and the wider spacing reads better at 130m anyway.
	for side in [-1.0, 1.0]:
		var ez: float = axis + side * 11.0
		_cyl("cascade_eye_post_%d" % int(side + 1), Vector3.ZERO,
			Vector3(top_x - 0.75, 1.5, ez), 0.16, 3.0, "metal", 0.0, 8)
		_sphere("cascade_eye_%d" % int(side + 1),
			Vector3(top_x - 0.75, 3.35, ez), Vector3.ZERO, 0.55, "eye")
		# The eyes are the one pair of fixtures in the park whose job is entirely
		# at distance, so they are bright and their range is long. From the pier
		# at 130m the pools they throw are invisible and only the globes read,
		# which is the point — a face needs two lights, not two lit walls.
		_omni("cascade_eye_%d_lamp" % int(side + 1),
			Vector3(top_x - 0.75, 3.35, ez), "lamp", 4.0, 20.0)

	_cascade_lights()


## The monument after dark, and the heaviest concentration of light in the park.
##
## Nothing else here is built to be looked at from 130m away and walked down at
## the same time, and those two want opposite things: distance wants a silhouette
## with bright points in it, and the descent wants to see where the treads are.
## So the fittings split by which job they do rather than by where they are.
##
## The rake across the flight is the one worth explaining. `CharacterBody3D` has
## no step-up, so a flight here is a ramp with treads laid over it and a nosing
## strip a few centimetres proud — a distinction that is legible in daylight only
## because the sun is somewhere off-axis. After dark, lit from straight on, the
## whole thing flattens back into the slope it actually is. Lighting it from the
## *side* puts every nosing's shadow across the tread below it, so the stair
## reads as a stair in the dark for the same reason it reads as one at four in
## the afternoon. It is the cheapest safety feature in the park and it is also
## the best-looking thing in it.
func _cascade_lights() -> void:
	var axis := Plan.CASCADE_AXIS_Z
	var top_x := Plan.CASCADE_TOP_X
	var floor_y := SHORE_TOP
	var half := Plan.FLIGHT_W * 0.5
	var foot_x := Plan.STAIR_FOOT.x

	# --- the aperture ---
	#
	# The portal lit from *behind*, and this is the change that does most of the
	# work. The first pass washed its west face from two floodlights out in the
	# court, which makes a bright arch on a dark ground — legible, and completely
	# inert. An arch is a hole, and the dramatic version of a hole is a dark mass
	# with light coming through it.
	#
	# So the fittings move to the east side, inside the opening, throwing light
	# out through it towards the court and the pier beyond. The mass reads as a
	# silhouette, the opening reads as luminous, and the three-arch alignment the
	# portal was moved off the wall to create — boardwalk entry, this, plaza
	# tunnel — becomes three lit apertures at rising heights instead of three
	# lit walls.
	var portal_x := foot_x - 4.2
	_omni("portal_aperture", Vector3(portal_x + 1.6, floor_y + 1.6, axis),
		"amber", 6.0, 16.0, LIGHT_FEATURE, true)
	# A second, low and further back, so the light through the opening has depth
	# rather than being one lamp visible as a dot from the court.
	_omni("portal_aperture_back", Vector3(portal_x + 4.4, floor_y + 0.9, axis),
		"amber", 3.0, 13.0)

	# The pediment and finial, picked out from close underneath. The top of the
	# portal is what breaks the skyline from the pier, and backlighting the
	# opening deliberately leaves it dark — so it gets its own pair, tight and
	# cold against the warm coming through the arch below.
	for side in [-1.0, 1.0]:
		_uplight("portal_crown_%d" % int(side + 1),
			Vector3(portal_x - 1.1, floor_y + 5.2, axis + side * 1.9),
			Vector3(portal_x, floor_y + 7.4, axis + side * 0.4),
			"moon", 3.4, 9.0, 30.0)

	# --- the descent ---
	#
	# Raking the flight. Six stations down each side, alternating so the light
	# crosses the treads rather than running down them — a pair facing each other
	# at the same station cancels the shadows they are both there to cast.
	#
	# Warm, and the warm is doing a job beyond looks: everything the player walks
	# on down here is amber and everything they walk *past* is cold, so the route
	# is legible as a route from the top of the bluff. That is the same argument
	# the plaza's asphalt-on-brick makes, made in light because the cascade has
	# no room for a painted walkway.
	for i in 6:
		var t := (float(i) + 0.5) / 6.0
		var lx: float = lerpf(top_x - 1.0, foot_x + 1.0, t)
		var side := 1.0 if i % 2 == 0 else -1.0
		var ly: float = lerpf(floor_y + Plan.CASCADE_DROP, floor_y, t)
		_uplight("cascade_rake_%d" % i,
			Vector3(lx, ly + 0.35, axis + side * (half - 0.2)),
			Vector3(lx - 2.5, ly + 0.9, axis - side * half),
			"amber", 3.2, 14.0, 42.0)

	# --- the wings ---
	#
	# Grazing the wall face from directly beneath the coping, rather than
	# floodlighting it from out in the court.
	#
	# The copings light themselves now — they are `trim`, and the two of them
	# draw the monument's silhouette on their own. What the wall below wants is
	# therefore the opposite of what it was given: not more brightness but a
	# gradient, bright directly under the coping and falling away down the face,
	# so the lit edge has something to sit on and the mass reads as mass. Close
	# in and narrow does that; five wide cones from 1.6m out did not.
	#
	# Placed off `Plan.wing_path`, so they follow the wing exactly instead of the
	# approximation this used to carry.
	#
	# **Both legs get them and only their west faces do**, which is the hairpin's
	# doing. West is the court, so those are the two faces anybody sees; the
	# outbound leg's east face is 30cm of slot against the bluff, and lighting it
	# would be eighteen metres of fittings aimed into rock.
	for side in [-1.0, 1.0]:
		var tag := "n" if side < 0.0 else "s"
		var path := Plan.wing_path(side)
		for leg in 2:
			var a: Vector3 = path[0] if leg == 0 else path[2]
			var b: Vector3 = path[1] if leg == 0 else path[3]
			var west := _wing_west(Vector2(b.x - a.x, b.z - a.z))
			for i in 6:
				var t := (float(i) + 0.5) / 6.0
				var p := a.lerp(b, t)
				# Just west of the wall face and just under the cap, aimed down
				# and out along the face.
				var at := Vector3(p.x + west.x * (Plan.WING_W * 0.5 + 1.9),
					p.y - 0.55, p.z + west.y * (Plan.WING_W * 0.5 + 1.9))
				var aim := Vector3(p.x + west.x * (Plan.WING_W * 0.5 + 1.5),
					p.y + 0.30, p.z + west.y * (Plan.WING_W * 0.5 + 1.5))
				_uplight("cascade_wing_%s_%d_%d" % [tag, leg, i], at, aim,
					"moon", 2.8, 7.0, 34.0)

	# --- the garden ---
	#
	# The planted terraces, from underneath. Four per side rather than two, and
	# warm against the cold wall: the planting is the reason this reads as a
	# garden rather than as civil engineering, and that is exactly the quality
	# that dies first when the sun goes down. It is also the only colour on the
	# monument, so it is worth more light than its area suggests.
	#
	# On the return leg's pocket side, which is where the beds are now. They used
	# to be strung down the inboard face of one long wing; the pocket the hairpin
	# encloses is a better place for a garden and a much better place to light
	# one, because the outbound leg above it is what the light lands on.
	for side in [-1.0, 1.0]:
		var tag := "n" if side < 0.0 else "s"
		var path := Plan.wing_path(side)
		var q: Vector3 = path[2]
		var c: Vector3 = path[3]
		var into := -_wing_west(Vector2(c.x - q.x, c.z - q.z))
		for i in 4:
			var t := 0.15 + float(i) * 0.23
			var p := q.lerp(c, t)
			var at := Vector3(p.x + into.x * (Plan.WING_W * 0.5 + 0.7),
				p.y + 0.15, p.z + into.y * (Plan.WING_W * 0.5 + 0.7))
			_uplight("cascade_planting_%s_%d" % [tag, i], at,
				at + Vector3(0.5, 2.4, 0.0), "amber", 2.2, 6.0, 56.0)

	# --- the ground ---
	#
	# Two in the arrival court, throwing the monument's own shadow west and
	# giving the 23m of open ground at its foot something other than spill.
	# Without them the court is the darkest place on the route and it is the
	# place the descent delivers you to.
	for side in [-1.0, 1.0]:
		_omni("court_pool_%d" % int(side + 1),
			Vector3(foot_x - 11.0, floor_y + 3.4, axis + side * 12.0),
			"lamp", 2.4, 18.0, LIGHT_FIXTURE)


## One half of the mass the flight is cut into, and the niche in its west face.
func _cascade_wall(side: float) -> void:
	var axis := Plan.CASCADE_AXIS_Z
	var top_x := Plan.CASCADE_TOP_X
	var drop := Plan.CASCADE_DROP
	var floor_y := SHORE_TOP
	var half := Plan.FLIGHT_W * 0.5
	var tag := "n" if side < 0.0 else "s"
	# The head of the wall, between the flight and where the wing springs — and
	# **it now stops exactly at the springing**, where it used to carry on 2.4m
	# past it. That overhang is a three-metre block of masonry sitting over the
	# first stretch of the wing's own ramp, which the ramp then descends into: the
	# north wing's `wing up 0` walked into its outer face from underneath while
	# the south wing's got away with it, because the garden stair's first landing
	# happens to be level for just long enough to clear. An asymmetry between two
	# mirrored things is the tell that one of them is passing by luck.
	var from_z := axis + side * (half + 0.2)
	var to_z := axis + side * Plan.WING_SPRING_Z
	_box("cascade_head_%s" % tag, Vector3.ZERO,
		Vector3(top_x - 1.6, -drop * 0.5, (from_z + to_z) * 0.5),
		Vector3(3.2, drop, absf(to_z - from_z)), "building")
	# **The head's top is the wing's doorway**, and that is the fact everything
	# else here follows from. The bluff top, this, and the wing's springing are
	# all at y = 0, so a player beside the flight walks straight west onto the
	# wing without a step — which is the only way onto a wing there is.
	#
	# So the trim comes off the top and hangs on the west face instead. It used to
	# be a lid over the whole 3.2 by 4.8, which is a 44cm kerb laid across the
	# doorway: you could step *down* onto a wing and never get back up, and
	# `walk_test` said so the moment its legs started aiming at the springing
	# rather than past it. Notching the lid does not work either — the wing's own
	# coping already occupies everything outboard of the springing, so what is
	# left to notch is exactly the doorway.
	#
	# The line still carries. It runs down the flight, along this band, and picks
	# up as the wing's coping where the two meet at the springing; the only
	# difference is that it is now at knee height on a wall rather than underfoot.
	#
	# It stops at the springing rather than running the head's full length. Past
	# that point the wing's own deck is what is out here, and a band hung on the
	# head's west face is a band hung a foot above the middle of a ramp.
	var band_in: float = axis + side * (Plan.FLIGHT_W * 0.5 - 0.2)
	var band_out: float = axis + side * Plan.WING_SPRING_Z
	_box("cascade_head_band_%s" % tag, Vector3.ZERO,
		Vector3(top_x - 3.35, -0.27, (band_in + band_out) * 0.5),
		Vector3(0.3, 0.44, absf(band_out - band_in)), "trim")
	# And the guard, because taking the lid off leaves the doorway's west edge as
	# an unfenced three-metre drop into the court. Splayed rather than square: it
	# runs from beside the flight out to where the wing's own outbound rail
	# begins, so the two are one handrail and the shape of it points at the wing.
	_wing_rail("cascade_head_guard_%s" % tag,
		Vector2(top_x - 3.0, axis + side * (Plan.FLIGHT_W * 0.5 + 0.6)), 0.0,
		Vector2(top_x - 5.2, axis + side * Plan.WING_SPRING_Z), 0.0)


## The portal: an arched gate standing in the court on the axis, a few metres
## west of the flight's foot.
##
## The arch was going to be a pair of niches flanking the flight, because the
## flight owns the axis and a niche cannot share it. Then the point of having an
## arch at all turned out to be **alignment**: the boardwalk's entry, this, and
## the plaza's tunnel are all on x = the same line, at rising heights, so from
## the head of the pier you look back east through three arches stacked one
## behind the other with the cascade's wings spread between them. Two niches off
## to the sides give you none of that. So it comes off the wall and stands in the
## court as a gate you actually walk through.
func _cascade_portal() -> void:
	var axis := Plan.CASCADE_AXIS_Z
	var floor_y := SHORE_TOP
	var risers := int(round(Plan.CASCADE_DROP / FLIGHT_RISE))
	var x := Plan.CASCADE_TOP_X - FLIGHT_GOING * risers - 5.4
	var clear := 2.8
	var opening := 4.4

	# Two piers and the mass over them, with a stepped head that reads as an arch
	# at greybox scale.
	for i in 2:
		var pz := axis + (-1.0 if i == 0 else 1.0) * (opening * 0.5 + 1.1)
		_box("portal_pier_%d" % i, Vector3.ZERO,
			Vector3(x, floor_y + 2.1, pz), Vector3(1.8, 4.2, 2.2), "building")
	for i in 3:
		var w := opening + 2.2 - float(i) * 0.7
		_box("portal_arch_%d" % i, Vector3.ZERO,
			Vector3(x, floor_y + clear + 0.16 + float(i) * 0.3, axis),
			Vector3(1.8, 0.3, w), "building")
	_box("portal_lintel", Vector3.ZERO,
		Vector3(x, floor_y + 4.3, axis), Vector3(1.8, 1.2, opening + 2.2), "building")
	_box("portal_cap", Vector3.ZERO,
		Vector3(x, floor_y + 5.0, axis), Vector3(2.4, 0.42, opening + 3.0), "trim")
	# A pediment over the middle, because the silhouette from the pier is most of
	# what this is for.
	_box("portal_pediment", Vector3.ZERO,
		Vector3(x, floor_y + 5.7, axis), Vector3(1.6, 1.0, opening * 0.7), "building")
	_box("portal_finial", Vector3.ZERO,
		Vector3(x, floor_y + 6.5, axis), Vector3(0.5, 0.7, 0.5), "accent")


## How far below the deck a wing's masonry reaches. Past the shore rather than
## down to it, so the mass is buried at every point on a tilted box rather than
## floating at one end and cut at the other.
const WING_BASE_Y := SHORE_TOP - 1.0


## The normal to a leg pointing west — out into the court, away from the bluff.
##
## Both legs of the hairpin run predominantly north–south, so "west" is an
## unambiguous answer where "outboard" was not. The old wing had to derive
## outboard from `side` and got it backwards on one of the two mirrored wings
## until somebody walked off the wrong edge; there is nothing left to get
## backwards here, because the court is west of both wings and always will be.
func _wing_west(span: Vector2) -> Vector2:
	var n := Vector2(-span.y, span.x).normalized()
	return n if n.x < 0.0 else -n


## One leg of a wing: the wall, the coping on it, and the deck riding on top.
##
## `smooth` makes the deck a ramp; otherwise it is the garden stair — two short
## flights with a long level landing, so both wings cover the same hairpin at the
## same average fall and only the surface differs.
func _wing_leg(tag: String, leg: int, a3: Vector3, b3: Vector3,
		smooth: bool) -> void:
	var a := Vector2(a3.x, a3.z)
	var b := Vector2(b3.x, b3.z)
	var span := b - a
	var length := span.length()
	var theta := atan2(span.x, span.y)
	var slope := atan2(a3.y - b3.y, length)
	var mid := (a3 + b3) * 0.5
	# The leg's own up-axis, so the wall can be backed off under the deck line
	# and the coping raised above it without either drifting off the slope.
	var up := (Basis(Vector3.UP, theta) * Basis(Vector3.RIGHT, slope)).y
	var run := sqrt(length * length + pow(a3.y - b3.y, 2.0))

	# The wall itself. Its top edge is one of the two diagonals that give the
	# monument its silhouette, so this is the piece that has to be right.
	var wall_h: float = mid.y - WING_BASE_Y
	_box("wing_wall_%s_%d" % [tag, leg], mid - up * (wall_h * 0.5), Vector3.ZERO,
		Vector3(Plan.WING_W + 2.6, wall_h, run), "building", theta, true, slope)
	# **The one piece of the monument that lights itself.** This coping's top edge
	# is the diagonal the whole shape is for, and an edge is a line — floodlighting
	# the wall under it makes an area bright and leaves the line exactly as
	# legible as everything around it, which is what the first night capture
	# showed. Lit from within, the copings draw the cascade's silhouette in the
	# dark as cold sweeping lines, and the wall below them can stay dim.
	#
	# **A parapet either side of the deck, not a slab over it.** It used to be one
	# box wider than the deck and 44cm proud of it, on the theory that the deck
	# would sit on top and leave a kerb showing at both edges — but the deck is
	# 40cm thick and hangs *below* its own top line, so what the box actually did
	# was lay a 44cm lid over the entire walking surface. The wing worked only
	# because the player walked on the coping instead of the ramp, and the price
	# came due at the springing, where that put the walking surface 44cm above the
	# bluff top it is supposed to be flush with: a step the player cannot climb,
	# across the only doorway onto the wing.
	#
	# The east strip is skipped on the outbound leg. Its east side is the bluff —
	# the wall runs to within 10cm of the rock — so a kerb there is invisible from
	# everywhere and stands square across the doorway, which is the same fault in
	# the same place by a different route.
	var west := _wing_west(span)
	for e in 2:
		if leg == 0 and e == 1:
			continue
		var n: Vector2 = west if e == 0 else -west
		_box("wing_cap_%s_%d_%d" % [tag, leg, e],
			mid + up * 0.22 + Vector3(n.x, 0.0, n.y) * 2.4, Vector3.ZERO,
			Vector3(1.2, 0.44, run), "trim", theta, true, slope)

	if smooth:
		_flight_ramp("wing_ramp_%s_%d" % [tag, leg], a3, b3, theta,
			Plan.WING_W, "far_shade")
		return

	for f in 2:
		var t0 := float(f) * 0.5
		var t1 := t0 + 0.5
		var y0: float = lerpf(a3.y, b3.y, t0)
		var y1: float = lerpf(a3.y, b3.y, t1)
		var p0 := a.lerp(b, t0)
		var p1 := a.lerp(b, t0 + 0.5 * 0.55)
		var p2 := a.lerp(b, t1)
		var lm := (p0 + p1) * 0.5
		_box("wing_tread_%s_%d_%d" % [tag, leg, f],
			Vector3(lm.x, y0 - 0.25, lm.y), Vector3.ZERO,
			Vector3(Plan.WING_W, 0.5, p0.distance_to(p1)), "accent", theta)
		_flight_ramp("wing_step_%s_%d_%d" % [tag, leg, f],
			Vector3(p1.x, y0, p1.y), Vector3(p2.x, y1, p2.y), theta,
			Plan.WING_W, "far_shade")
		for r in 3:
			var tr := float(r + 1) / 3.0
			var pr := p1.lerp(p2, tr)
			_box("wing_nosing_%s_%d_%d_%d" % [tag, leg, f, r], Vector3(pr.x,
				y0 + (y1 - y0) * tr + 0.015, pr.y), Vector3.ZERO,
				Vector3(Plan.WING_W - 0.2, 0.03, 0.16), "far_shade", theta, false)


## A run of rail: posts and a top rail rather than a slab, between two points at
## two heights. Level or raking, and every rail on the monument is one of these.
func _wing_rail(nm: String, a: Vector2, ya: float, b: Vector2, yb: float) -> void:
	var span := b - a
	var length := span.length()
	if length < 0.5:
		return
	var theta := atan2(span.x, span.y)
	var phi := atan2(ya - yb, length)
	var posts := maxi(2, int(length / 2.6))
	for i in posts + 1:
		var t := float(i) / float(posts)
		var p := a.lerp(b, t)
		_cyl("%s_post_%d" % [nm, i], Vector3.ZERO,
			Vector3(p.x, lerpf(ya, yb, t) + 0.55, p.y), 0.06, 1.1, "metal", 0.0, 6)
	var m := (a + b) * 0.5
	_box("%s_rail" % nm, Vector3(m.x, (ya + yb) * 0.5 + 1.02, m.y), Vector3.ZERO,
		Vector3(0.12, 1.0, sqrt(length * length + pow(ya - yb, 2.0))), "metal",
		theta, true, phi)


## A wing: the hairpin, and the whole of it. Out and down against the bluff, a
## level landing at the turn, and back in and down to the court beside the
## flight's own foot. See `ParkPlan.WING_SPRING_X` for what it replaced and why.
func _cascade_wing(side: float, smooth: bool) -> void:
	var tag := "n" if side < 0.0 else "s"
	var path := Plan.wing_path(side)
	var spring: Vector3 = path[0]
	var turn_in: Vector3 = path[1]
	var turn_out: Vector3 = path[2]
	var foot: Vector3 = path[3]
	var half_w := Plan.WING_W * 0.5

	# The legs stop at the landing's inner edge rather than at the turn vertex —
	# see `ParkPlan.WING_LAND_D`. Everything below is laid off those two points,
	# so the landing and the ramps meet exactly and neither overhangs the other.
	var end_out := Plan.wing_leg_end(side, 0)
	var end_ret := Plan.wing_leg_end(side, 1)
	_wing_leg(tag, 0, spring, end_out, smooth)
	_wing_leg(tag, 1, end_ret, foot, smooth)

	# --- the landing at the turn ---
	#
	# Level, and that is the whole trick: a landing carries none of the fall, so
	# folding thirty-six metres of run in half across one costs nothing in
	# gradient. It is also the only place on the descent you can stop, turn round
	# and look back up at the plaza, which is worth more than it cost.
	#
	# **It spans exactly the two leg ends and no further inward.** A landing deep
	# enough to reach past them is a level slab lying over a slope, and where the
	# ramp has dropped below it you meet its edge as a step — which is how both
	# `wing up` legs failed before the leg ends moved.
	var lx0: float = end_out.x + half_w
	var lx1: float = end_ret.x - half_w
	var lc := Vector2((lx0 + lx1) * 0.5, turn_in.z)
	var lw := absf(lx1 - lx0)
	var ld := Plan.WING_LAND_D
	var ly := turn_in.y
	_box("wing_landing_wall_%s" % tag,
		Vector3(lc.x, (ly + WING_BASE_Y) * 0.5, lc.y), Vector3.ZERO,
		Vector3(lw + 1.0, ly - WING_BASE_Y, ld + 0.8), "building")
	_box("wing_landing_%s" % tag, Vector3(lc.x, ly - 0.25, lc.y), Vector3.ZERO,
		Vector3(lw, 0.5, ld), "accent")
	# Coping as three strips rather than one frame, because a frame puts a 44cm
	# kerb across the two places the legs come in — and `CharacterBody3D` has no
	# step-up, so that is not a kerb, it is a wall closing the route the landing
	# exists to turn. These are the edges nothing walks over: the outer face, the
	# west face, and the pocket between the two leg mouths.
	var e_out: float = turn_in.z + side * (ld * 0.5 + 0.4)
	var e_in: float = turn_in.z - side * (ld * 0.5 + 0.4)
	var gap_from: float = end_out.x - half_w
	var gap_to: float = end_ret.x + half_w
	_box("wing_landing_cap_out_%s" % tag, Vector3(lc.x, ly + 0.22, e_out),
		Vector3.ZERO, Vector3(lw + 0.8, 0.44, 0.8), "trim")
	_box("wing_landing_cap_west_%s" % tag,
		Vector3(lx1 - 0.4, ly + 0.22, lc.y), Vector3.ZERO,
		Vector3(0.8, 0.44, ld + 0.8), "trim")
	_box("wing_landing_cap_in_%s" % tag,
		Vector3((gap_from + gap_to) * 0.5, ly + 0.22, e_in), Vector3.ZERO,
		Vector3(absf(gap_to - gap_from), 0.44, 0.8), "trim")

	# --- the rails ---
	#
	# Round the exposed perimeter and nowhere else, which is a shorter list than
	# the old wing's "both edges of everything". The outbound leg's east side is
	# the bluff — there is nothing to fall off a wall you are leaning against —
	# and rail there would have been 18m of posts inside the rock.
	#
	# **The last three metres of the return leg get none**, which is not an
	# oversight. By then the wing is flush with the court and there is nothing to
	# fall off, and a rail carried to the end fences the one place the wing is
	# supposed to deliver you to. It did exactly that once already: both
	# `wing -> court` legs timed out with the player sliding down the outside of
	# a rail instead of stepping off the end of the ramp.
	var out_span := Vector2(end_out.x - spring.x, end_out.z - spring.z)
	var out_w := _wing_west(out_span) * (half_w + 0.2)
	_wing_rail("wing_rail_%s_out" % tag,
		Vector2(spring.x, spring.z) + out_w, spring.y,
		Vector2(end_out.x, end_out.z) + out_w, end_out.y)

	var ret := Vector2(foot.x - end_ret.x, foot.z - end_ret.z)
	var ret_len := ret.length()
	var t_end: float = 1.0 - 3.0 / ret_len
	var ret_w := _wing_west(ret) * (half_w + 0.2)
	var ret_end := end_ret.lerp(foot, t_end)
	for e in 2:
		var off: Vector2 = ret_w if e == 0 else -ret_w
		_wing_rail("wing_rail_%s_ret%d" % [tag, e],
			Vector2(end_ret.x, end_ret.z) + off, end_ret.y,
			Vector2(ret_end.x, ret_end.z) + off, ret_end.y)
	# Round the landing: its outer face and its west face, which together with
	# the two leg rails close the whole open side of the hairpin.
	_wing_rail("wing_rail_%s_land_out" % tag,
		Vector2(lc.x - lw * 0.5, e_out), ly, Vector2(lc.x + lw * 0.5, e_out), ly)
	_wing_rail("wing_rail_%s_land_west" % tag,
		Vector2(turn_out.x - half_w - 0.4, lc.y - ld * 0.5), ly,
		Vector2(turn_out.x - half_w - 0.4, lc.y + ld * 0.5), ly)

	# --- the planting ---
	#
	# The terraces are what turn this from civil engineering into a garden, and
	# they are the reason the thing is worth looking back at from the pier.
	#
	# They go in the **pocket** the hairpin encloses — between the return leg and
	# the outbound leg above it — which is the shape's own reward for doubling
	# back and did not exist when the wing was one straight run. The pocket is a
	# wedge, 4.7m across at the springing and 2.4m at the turn, because the
	# outbound leg runs true north–south and the return leg sweeps away from it.
	# So the beds hang off the *return* leg's edge rather than sitting in the
	# middle of a gap whose middle moves, and each one carries a plinth down to
	# the court: consecutive plinths overlap, so the terrace wall is continuous
	# and the pocket has a floor rather than a slot down its length.
	var beds := 7
	var bed_n := -_wing_west(ret) * (half_w + 1.4)
	var bed_theta := atan2(ret.x, ret.y)
	for i in beds:
		var t := (float(i) + 0.5) / float(beds)
		var p := turn_out.lerp(foot, t)
		var bx := p.x + bed_n.x
		var bz := p.z + bed_n.y
		_box("wing_bed_plinth_%s_%d" % [tag, i],
			Vector3(bx, (p.y + WING_BASE_Y) * 0.5, bz), Vector3.ZERO,
			Vector3(2.4, p.y - WING_BASE_Y, 3.0), "building", bed_theta)
		_box("wing_bed_%s_%d" % [tag, i], Vector3(bx, p.y - 0.1, bz), Vector3.ZERO,
			Vector3(2.2, 0.5, 3.2), "accent", bed_theta)
		_box("wing_soil_%s_%d" % [tag, i], Vector3(bx, p.y + 0.2, bz), Vector3.ZERO,
			Vector3(1.8, 0.3, 2.8), "planting", bed_theta, false)
		for k in 5:
			var hx := bx + (_hash01(i * 7 + k, 3, 29) - 0.5) * 1.4
			var hz := bz + (_hash01(i * 7 + k, 5, 31) - 0.5) * 2.2
			var bloom: String = ["bloom_warm", "bloom_pink", "bloom_pale"][(i + k) % 3]
			_sphere("wing_bloom_%s_%d_%d" % [tag, i, k],
				Vector3(hx, p.y + 0.5, hz), Vector3.ZERO,
				0.26 + _hash01(k, 2, 17) * 0.14, bloom)


	# The seam used to be three nodes here — preload at the head of the flight,
	# crossing in front of the shut gate at the foot, and the whole turned stair
	# between them as the load's cover. It is at the arch now, and this scene is
	# mounted on both sides of it, so it can hold no gates at all: a gate here
	# would fire in whichever section happened to be standing.


func _skyline() -> void:
	# North, straight down the spawn sightline, cropped by building_north.
	#
	# A third taller than the boardwalk's, because the perimeter went to 13–19m
	# on 2026-08-13 and at its old 27m crest the roofline ate it: the sightline
	# from the fountain clears a 16m wall at 46m and passes 29m up by the time it
	# reaches the crest column, 88m out. Height is the only lever that works
	# here — moving the ride in or out barely changes the ratio of wall distance
	# to ride distance, which is what decides how much shows.
	_wooden_coaster(Vector3(-22, 0, -58), deg_to_rad(72.0), "far_warm", 1.3)
	# North-east, visible over the low corner between perim_ne and building_east.
	_tower(Vector3(54, 0, -40), "far", "far_warm")
	# The west used to be built here. It is three scenes of its own now — see
	# WEST_SHELL_PATH — because half of it has to survive the player crossing the
	# gate and the other half has to be replaced when they do.


## The arrival: everything south of the plaza's south wall.
##
## This is the Disney treatment, simplified. Disneyland runs Main Entrance Mall,
## gate, Town Square, Main Street, and only then the hub — five stages before
## you reach the middle. Three of those earn their place here: an apron outside
## the gate, the gate, and a street. Town Square is dropped; the apron does its
## job from the other side of the turnstiles.
##
## Length is the decision. Disneyland's Main Street is about 170m against a 60m
## hub. Straight scaling would put 230m in front of an 80m plaza, which is a
## walk the player repeats every session. 56m is the shortest run that still
## reads as a street rather than a passage — long enough that the plaza arrives
## as a widening, short enough that arriving is not a commute.
## The plaza's own `ground` owns y = 0. Every other surface that meets it sits
## a centimetre under, so that where the two overlap there is exactly one
## up-facing face at that height and nothing for the depth buffer to choose
## between.
##
## The overlaps are all deliberate — a coplanar butt leaves a zero-width seam
## for the capsule to catch on, so each of these runs back under the plaza's
## edge rather than meeting it. That is what made them z-fight: two up-facing
## floors, the same plane, different materials, tens of square metres of it.
##
## A centimetre is under the controller's step-up, so the lip where the plaza's
## ground ends is not something you can trip on in either direction.
const GROUND_SEAM := -0.01

## And a second offset for the *other* generated ground, because there is more
## than one of them and they meet.
##
## The four passages come out of the plaza's south-west corner near where the
## entrance street's ground runs, and both sit a centimetre under the plaza. Same
## height, same material, twenty square metres of overlap — and the build-order
## seam cannot separate them, because they are in different scenes and the
## ordinal only orders shapes within one.
##
## Three more millimetres down. Still far under the step-up, still one flat
## surface to walk on, and no longer the same plane as the street.
const PASSAGE_SEAM := GROUND_SEAM - 0.003

const ST_X := Plan.STREET_X
const ST_HALF := Plan.STREET_HALF
const ST_FROM := Plan.STREET_FROM_Z
const GATE_Z := Plan.GATE_Z
const APRON_Z := Plan.APRON_Z

## On the existing sightline rather than a new one. The gap in the plaza's south
## building line already sits at x -9..6, and the fountain is at x 0 — 1.5m off
## this centre, which at 56m is under two degrees and invisible. So the street
## costs the plaza one cut in one wall and nothing else.
func _entrance() -> void:
	# Top at y=0, matching the plaza ground. Overlapped by 2m rather than butted:
	# a coplanar butt can leave a zero-width seam for the capsule to catch on,
	# and two floors at exactly the same height cannot produce a lip.
	# Brick, the same bond as the plaza's floor, because it is the same floor —
	# the street's asphalt is laid over it and what shows either side is the walk
	# under the shopfronts and the apron outside the gate.
	# Spans the street from under the plaza's own floor to ten metres past the
	# apron. Derived rather than typed, because it was typed and then the street
	# moved 12m south without it: the apron ended up standing off the end of its
	# own ground, which the walk test reported as falling.
	var g_from := Plan.PLAZA_HALF - 6.0
	var g_to := Plan.APRON_Z + 10.0
	_box("entrance_ground", Vector3.ZERO,
		Vector3(ST_X, -0.5 + GROUND_SEAM, (g_from + g_to) * 0.5),
		Vector3(41, 1, g_to - g_from), "brick", 0.0, true)

	_street_frontage()
	_street_booths()
	_gate()
	_apron()
	_entrance_lights()


## The arrival, after dark — and until now there was none at all.
##
## `entrance.tscn` was the one scene on the plaza's side of the park with zero
## lights in it. Not dim: zero. Fifty-seven metres of street, ten shopfronts,
## three game booths, a walk-in arcade, the turnstiles and the apron outside
## them, all of it pitch black from about half past eight, while the plaza it
## leads to was fully lit. The gap survived a whole lighting pass and a capture
## run because no vantage in `night_capture.gd` pointed south.
##
## It matters more than its area suggests, for two reasons the design has
## already argued elsewhere. The street is the answer to "the hub is a junction,
## not a destination" — the thing that stops the park being gate-straight-into-
## plaza — and a corridor nobody can see is not a corridor. And it is a midway:
## small commerce, close frontage, awnings, booths. A midway that goes dark is
## just an alley you cross to get somewhere better.
func _entrance_lights() -> void:
	_street_shop_lights()
	_street_festoons()
	_booth_lights()
	_arcade_lights()
	_gate_lights()
	_apron_lights()


## The three game booths, lit.
##
## Emitted from here rather than from inside `_booth`, and that is not a matter
## of tidiness — it is the seam rule applied one level down. `_add` hands every
## shape a displacement by build order, so the bulbs *inside* `_booth` pushed the
## ordinal of every shape emitted after them: the prize walls, the two later
## booths, the gate, the apron and the whole parking lot. `coplanar_test` caught
## it immediately — `booth_hoops_counter` came to rest with its underside exactly
## on the street paving, 2.04m² of z-fight in the middle of the walk, in geometry
## nobody had touched.
##
## The same lesson the scene write order carries: append, never insert. Adding
## shapes at the end of a run is free; adding them in the middle re-planes
## everything downstream.
func _booth_lights() -> void:
	for row in STREET_BOOTHS:
		var nm: String = row[0]
		var base: Vector3 = row[1]
		var theta: float = row[2]
		var width: float = row[3]
		var n := width * 0.5
		var depth := 3.2
		# Bulbs along the valance. A game booth is the one thing on the street
		# that has to read as *staffed and open* after dark — it is a counter
		# somebody stands behind, and unlit it reads as shut for the season.
		# Same vocabulary as the threshold mouths and the alley: a row of lights
		# is what says a thing is open.
		var lamps: int = maxi(4, int(width * 1.2))
		for i in lamps:
			var t := (float(i) + 0.5) / float(lamps)
			_sphere(nm + "_bulb_%d" % i, base,
				Vector3(lerpf(-n + 0.3, n - 0.3, t), 2.72, depth * 0.5 + 0.62),
				0.11, "bulb", theta)
		# Warm and low, over the counter rather than the room — the prize wall
		# is the thing worth seeing and it is 3m back.
		_omni(nm + "_glow", _place(base, Vector3(0, 2.6, depth * 0.5 - 0.4), theta),
			"warm", 2.6, 8.0, LIGHT_FIXTURE, true)


## A lamp under every awning, both ranges.
##
## The awnings are already what make this a street rather than two walls — the
## comment in `_shopfronts` says so — and lighting *under* them rather than
## floodlighting the buildings keeps that true after dark. It puts a row of warm
## pools down each side at head height with dark above, so the street reads as a
## colonnade you walk along, and the shopfronts read as premises rather than as
## the sides of a corridor.
func _street_shop_lights() -> void:
	var n := 0
	for pair in [[STREET_WEST, -1.0], [STREET_EAST, 1.0]]:
		var rows: Array = pair[0]
		var side: float = pair[1]
		var face: float = ST_X + side * ST_HALF
		for row in rows:
			var z: float = row[0]
			var length: float = row[1]
			# Under the awning's outer lip, not against the wall. Against the
			# wall it lights the shopfront and leaves the walk in shadow, which
			# is backwards — the walk is where the player and the crowd are.
			_omni("street_awning_%d" % n,
				Vector3(face + side * 1.25, 2.82, z), "warm", 2.2, 8.5,
				LIGHT_FIXTURE, n % 3 == 0)
			# A second for the long units, or a 12m frontage gets one pool in the
			# middle and two dark ends.
			if length > 10.5:
				_omni("street_awning_%d_b" % n,
					Vector3(face + side * 1.25, 2.82, z + length * 0.3),
					"warm", 1.6, 7.0)
			n += 1


## Festoons strung across the street, gable to gable.
##
## The one move that says "midway" louder than anything else available, and it
## costs almost nothing: the bulbs are the same `bulb` material as the boardwalk
## masts and the threshold valances, so they come up with the rest of the park
## and need no light of their own. Overhead and *across* the street rather than
## along it, which is the whole difference — a line of lights down a street is
## street lighting, and a line of lights across it is a fair.
##
## Hung above the awnings and below the parapets, so they read against the sky
## from the gate and against the frontage from underneath.
const STREET_STRING_Y := 5.6
const STREET_STRING_SAG := 0.85
const STREET_STRING_STEPS := 8


func _street_festoons() -> void:
	var z := 58.0
	var i := 0
	while z <= 108.0:
		var x0 := ST_X - ST_HALF + 0.3
		var x1 := ST_X + ST_HALF - 0.3
		var points: Array[Vector3] = []
		for s in STREET_STRING_STEPS + 1:
			var t := float(s) / float(STREET_STRING_STEPS)
			points.append(Vector3(lerpf(x0, x1, t),
				STREET_STRING_Y - STREET_STRING_SAG * sin(PI * t), z))
		for s in STREET_STRING_STEPS:
			_strut("street_wire_%d_%d" % [i, s], points[s], points[s + 1], 0.045, "metal")
		for b in STREET_STRING_STEPS - 1:
			_sphere("street_bulb_%d_%d" % [i, b], points[b + 1], Vector3.ZERO, 0.13, "bulb")
		# One light per string at the sag, low, so the street's asphalt is warmer
		# under a string than between strings. The bulbs carry the look; this
		# only stops the middle of the street being the darkest part of it.
		_omni("street_string_%d_glow" % i,
			Vector3(ST_X, STREET_STRING_Y - STREET_STRING_SAG, z), "warm", 1.7, 12.0)
		z += 10.0
		i += 1


## Both sides of the street, one building deep, fronting the walk. This is the
## midway treatment the design calls for: the corridor between the gate and the
## plaza is where the small commerce lives, not a section of its own.
##
## Depths and heights vary per building so the run reads as a street of separate
## businesses. A constant depth gives two long walls, which is what the boardwalk
## frontage got wrong at close range.
## The street's two ranges: z, length, depth, height, material, kind.
##
## Hoisted out of `_street_frontage` because the lighting reads them too — every
## shop gets a lamp under its own awning, and an awning is at the building's z
## with the building's length. Left as locals they would have had to be typed a
## second time in `_entrance_lights`, which is the same duplication the cafe
## tables had before `ParkPlan.PLAZA_CAFE` collapsed them, at the same cost:
## move a shop and its light stays where the shop used to be.
##
## Kinds alternate across the street rather than down it, so neither side is a
## run of the same thing and the arcades face something other than each other.
const STREET_WEST := [
	[56.0, 10.0, 9.0, 6.5, "far_warm", "store"],
	[67.0, 11.0, 10.0, 5.0, "accent", "cafe"],
	[78.0, 10.0, 8.0, 7.0, "far_warm", "arcade"],
	[88.0, 9.0, 9.5, 5.5, "white", "store"],
	[99.0, 12.0, 8.5, 6.0, "accent", "cafe"],
]
const STREET_EAST := [
	[57.0, 11.0, 9.0, 5.5, "accent", "cafe"],
	[69.0, 12.0, 10.0, 7.0, "far_warm", "store"],
	[81.0, 11.0, 8.0, 5.0, "white", "arcade"],
	[92.0, 10.0, 9.0, 6.5, "accent", "store"],
	[102.0, 9.0, 8.5, 5.5, "far_warm", "cafe"],
]


func _street_frontage() -> void:
	_shopfronts(STREET_WEST, -1.0, 0)
	_shopfronts(STREET_EAST, 1.0, 10)


## `side` is -1 for the west range and +1 for the east. Buildings grow away from
## the street so the frontage line stays straight whatever the depth.
func _shopfronts(rows: Array, side: float, id_from: int) -> void:
	var face := ST_X + side * ST_HALF
	var n := id_from
	for row in rows:
		var z: float = row[0]
		var length: float = row[1]
		var depth: float = row[2]
		var height: float = row[3]
		var mat: String = row[4]
		var kind: String = row[5]
		var cx := face + side * depth * 0.5
		var walk_in: bool = kind == "arcade" and side < 0.0
		if walk_in:
			_arcade_room(face, z, length)
		else:
			_box("shop_%d" % n, Vector3.ZERO, Vector3(cx, height * 0.5, z),
				Vector3(depth, height, length), mat)
		# A parapet lip, so the roofline is an edge rather than the top of a slab.
		if not walk_in:
			_box("shop_%d_cap" % n, Vector3.ZERO, Vector3(cx, height + 0.2, z),
				Vector3(depth + 0.5, 0.4, length + 0.5), "far_shade", 0.0, false)
		# The canopy is what makes this a street instead of two walls. It sits
		# above head height and carries no collision — walking into shade should
		# not be walking into a wall.
		# Sunk 2cm into the frontage. Butted exactly against it the awning's back
		# face and the shop's face are the same plane, which fights.
		_box("shop_%d_awning" % n, Vector3.ZERO,
			Vector3(face + side * 0.88, 3.1, z),
			Vector3(1.8, 0.18, length - 1.5), "red", 0.0, false)
		_cyl("shop_%d_post_a" % n, Vector3.ZERO,
			Vector3(face + side * 1.7, 1.55, z - length * 0.5 + 1.0),
			0.08, 3.1, "metal", 0.0, 6, false)
		_cyl("shop_%d_post_b" % n, Vector3.ZERO,
			Vector3(face + side * 1.7, 1.55, z + length * 0.5 - 1.0),
			0.08, 3.1, "metal", 0.0, 6, false)
		# The front itself, turned to look across the street. Narrower than the
		# building so the frontage line has joints in it.
		var theta := -side * PI * 0.5
		_front("shop_%d" % n, Vector3(face, 0.0, z), theta,
			minf(length - 2.0, 7.5), kind, not walk_in)
		n += 1


## The arcade, which is the only interior on the street and the only room in the
## park the player can walk into.
##
## So it gets the one lighting scheme in the plaza that is not warm white, and
## the reason is diegetic rather than decorative: an arcade in 1997 is a dark
## room lit by forty CRTs, and the light coming out of its door is *blue*. That
## is a specific memory of a specific kind of place, and it is free — the room
## is already built, already walkable, and currently pitch dark.
##
## What it buys structurally is a reason to look sideways on the walk up the
## street. Everything else on the frontage is a face; this is an opening with
## light pouring out of it, and it is on the west side where the evening sun has
## already gone. Before this the arcade was indistinguishable from a shopfront
## after eight o'clock.
func _arcade_lights() -> void:
	# Only the walk-in one — the east range's arcade is a front, not a room.
	for row in STREET_WEST:
		if String(row[5]) != "arcade":
			continue
		var z: float = row[0]
		var face := ST_X - ST_HALF
		var mid := (face + ARC_BACK) * 0.5

		# The cabinets, down the back and the side walls. Cold and low, so the
		# room is lit from its own machines rather than from a ceiling it does
		# not have.
		for i in 3:
			var cz: float = z - 2.4 + float(i) * 2.4
			_omni("arc_glow_%d" % i, Vector3(ARC_BACK + 2.2, 1.5, cz),
				"cyan", 2.4, 9.0)
		_omni("arc_glow_mid", Vector3(mid, 2.6, z), "cyan", 1.8, 12.0)

		# At the mouth, throwing out onto the walk. This is the one the street
		# sees: a cold rectangle in a warm frontage, which is exactly what an
		# arcade door looks like from outside at night.
		_omni("arc_door_spill", Vector3(face - 1.4, 1.9, z), "cyan", 2.6, 8.0,
			LIGHT_FIXTURE, true)


## The turnstiles, which are the park's face.
##
## This is the first thing the player sees and the last thing they walk out
## through, and it stands on the gate axis with the 40m clock tower directly
## behind it — the tower is already floodlit and its clock already lit, so an
## unlit gate leaves a black band across the bottom of the park's best view from
## the apron.
##
## Lit from under its own canopy rather than washed from outside, for the same
## reason the bandstand is: a canopy with light under it reads as somewhere still
## open. The sign gets its own pair from below, because a name board is the one
## piece of the park that has to be *readable* rather than merely visible.
func _gate_lights() -> void:
	# Under the canopy, across the lanes. Three, so the opening is evenly bright
	# and the stiles cast down onto the brick rather than along it.
	for i in 3:
		var x := ST_X - 4.0 + float(i) * 4.0
		_omni("gate_canopy_glow_%d" % i, Vector3(x, 3.9, GATE_Z),
			"warm", 2.8, 10.0, LIGHT_FIXTURE, i == 1)

	# The name board, from below and close, on the apron side — it is read on the
	# way in. Cool against the canopy's warm so it separates from the structure
	# holding it up.
	for side in [-1.0, 1.0]:
		_uplight("gate_sign_wash_%d" % int(side + 1),
			Vector3(ST_X + side * 3.2, 1.0, GATE_Z + 4.4),
			Vector3(ST_X + side * 1.2, 5.6, GATE_Z + 2.9),
			"wash", 3.0, 12.0, 34.0)

	# A window in each booth. Somebody sells the tickets, and two lit windows
	# either side of the opening is what makes the gate read as staffed rather
	# than as an arch with a roof.
	for side in [-1.0, 1.0]:
		_omni("gate_booth_glow_%d" % int(side + 1),
			Vector3(ST_X + side * (ST_HALF - 2.25), 2.0, GATE_Z + 2.2),
			"warm", 1.5, 6.0, LIGHT_SERVICE)


## The apron and the lot beyond it.
##
## The six `apron_pole` cylinders have stood there since the entrance was built
## and have never been anything — 8m white posts with nothing on top, which in
## daylight read as flagpoles nobody hung a flag on. They are the car park's
## lighting and always were; this finishes them.
##
## Cool rather than warm, and that is the one place in the park where cold light
## is a *boundary* rather than a feature. Sodium and mercury vapour is what a
## real lot is lit with, it is nobody's idea of welcoming, and the step from that
## into the warm street under the turnstiles is the arrival doing its job. The
## park should feel warmer than the place you parked.
func _apron_lights() -> void:
	for i in range(6):
		var x := ST_X - 15.0 + float(i) * 6.0
		# A head on the pole, so there is something to be lit *by*. The pole tops
		# out at 8.0.
		_box("apron_head_%d" % i, Vector3.ZERO, Vector3(x, 7.86, GATE_Z + 9.0),
			Vector3(0.6, 0.22, 0.9), "lamp_glass", 0.0, false)
		_omni("apron_lamp_%d" % i, Vector3(x, 7.6, GATE_Z + 9.0),
			"lamp", 3.0, 22.0, LIGHT_FIXTURE, i == 2 or i == 3)

	# The lot itself, as backdrop. Four standards over the parked cars, tall and
	# far apart the way a real lot is lit. No shadows and no detail — this is
	# 40m past the rail the player cannot cross, and its whole job is to say the
	# world does not stop at the apron.
	for i in 4:
		var x := ST_X - 34.0 + float(i) * 23.0
		for j in 2:
			var z := 138.0 + float(j) * 24.0
			_cyl("lot_pole_%d_%d" % [i, j], Vector3.ZERO, Vector3(x, 5.0, z),
				0.16, 10.0, "far_shade", 0.0, 6, false)
			_box("lot_head_%d_%d" % [i, j], Vector3.ZERO, Vector3(x, 9.9, z),
				Vector3(0.8, 0.24, 1.2), "lamp_glass", 0.0, false)
			_omni("lot_lamp_%d_%d" % [i, j], Vector3(x, 9.6, z),
				"lamp", 2.2, 26.0)


## Turnstiles under a canopy. The threshold is a squeeze between two booths
## rather than a doorway: you can see the whole street through it from outside,
## which is the opposite of the west stair's job and deliberately so. Arrival
## should promise; a section boundary should hide.
func _gate() -> void:
	var west_c := ST_X - ST_HALF + 2.25
	var east_c := ST_X + ST_HALF - 2.25
	_box("gate_booth_west", Vector3.ZERO, Vector3(west_c, 1.75, GATE_Z),
		Vector3(4.5, 3.5, 4.0), "white")
	_box("gate_booth_east", Vector3.ZERO, Vector3(east_c, 1.75, GATE_Z),
		Vector3(4.5, 3.5, 4.0), "white")
	_box("gate_canopy", Vector3.ZERO, Vector3(ST_X, 4.3, GATE_Z),
		Vector3(ST_HALF * 2.0 + 1.0, 0.5, 5.5), "red", 0.0, false)
	_cyl("gate_post_west", Vector3.ZERO,
		Vector3(ST_X - ST_HALF - 0.2, 2.15, GATE_Z), 0.14, 4.3, "metal")
	_cyl("gate_post_east", Vector3.ZERO,
		Vector3(ST_X + ST_HALF + 0.2, 2.15, GATE_Z), 0.14, 4.3, "metal")
	# The name board, read from the apron on the way in.
	_box("gate_sign", Vector3.ZERO, Vector3(ST_X, 5.6, GATE_Z + 2.6),
		Vector3(9.0, 2.0, 0.3), "yellow", 0.0, false)
	# Stiles in the opening. Waist height and solid, so the gap reads as a count
	# of lanes rather than a hole.
	#
	# Two dividers, not three, and neither on ST_X. Three evenly spaced stiles
	# put one dead centre — a post in the middle of the doorway, on the exact
	# line the street is aimed down. Two put a lane on the axis instead, which
	# is what the walk into the park should find.
	for i in range(2):
		var x := ST_X - 1.0 + float(i) * 2.0
		_box("stile_%d" % i, Vector3.ZERO, Vector3(x, 0.5, GATE_Z),
			Vector3(0.25, 1.0, 3.4), "metal")


## Outside the turnstiles. This is the piece the star scheme kept pointing at —
## a place to arrive that is not yet the park. Closed at the south, because the
## player does not get to leave: the parking lot is a view, not a destination.
func _apron() -> void:
	for i in range(6):
		var x := ST_X - 15.0 + float(i) * 6.0
		_cyl("apron_pole_%d" % i, Vector3.ZERO, Vector3(x, 4.0, GATE_Z + 9.0),
			0.12, 8.0, "white", 0.0, 8)
	_box("apron_planter_west", Vector3.ZERO, Vector3(ST_X - 13.0, 0.3, GATE_Z + 5.0),
		Vector3(7.0, 0.6, 3.0), "accent")
	_box("apron_planter_east", Vector3.ZERO, Vector3(ST_X + 13.0, 0.3, GATE_Z + 5.0),
		Vector3(7.0, 0.6, 3.0), "accent")
	# The far edge. Waist-high so the parking beyond stays visible over it, and
	# solid because there is nothing walkable past it.
	_box("apron_rail", Vector3.ZERO, Vector3(ST_X, 0.55, APRON_Z),
		Vector3(41.0, 1.1, 0.4), "metal")
	_box("apron_wall_west", Vector3.ZERO, Vector3(ST_X - 20.3, 1.5, 116.0),
		Vector3(0.4, 3.0, 15.0), "far_shade")
	_box("apron_wall_east", Vector3.ZERO, Vector3(ST_X + 17.3, 1.5, 116.0),
		Vector3(0.4, 3.0, 15.0), "far_shade")

	# The parking lot, which is a backdrop. No collision, never reached.
	_box("lot_ground", Vector3.ZERO, Vector3(ST_X, -0.6, 157.0),
		Vector3(150.0, 1.0, 68.0), "far_shade", 0.0, false)
	var n := 0
	for row in range(4):
		for col in range(14):
			var x := ST_X - 45.0 + float(col) * 7.0
			var z := 132.0 + float(row) * 12.0
			_box("car_%d" % n, Vector3.ZERO, Vector3(x, 0.7, z),
				Vector3(1.9, 1.4, 4.4), "far" if (n % 3) else "far_warm",
				0.0, false)
			n += 1
	for i in range(9):
		_cyl("lot_tree_%d" % i, Vector3.ZERO,
			Vector3(ST_X - 48.0 + float(i) * 12.0, 3.5, 128.0),
			1.6, 7.0, "far_shade", 0.0, 6, false)


## Scaffolding: a short passage out of each of the four section openings.
##
## These exist to test one thing — whether an 80m plaza survives being punched
## six times. Enclosure is what makes it a room rather than a crossroads, and
## the milestone's "yes" was measured on a plaza with two ways out.
##
## Not gates. A park does not padlock its own paths during opening hours, and a
## shut gate across a main way reads as closed rather than as unbuilt — which is
## the wrong thing to say about a park whose whole pitch is that it is open and
## everyone is having a nice time.
##
## So each one turns instead. Nine metres out, a bend, seven more, and a wall
## you cannot see from the plaza. The player walks in, finds the way carries on
## somewhere, and does not find a refusal. It is the same trick the west stair
## plays, and it is where the section will attach: the bend is the seam.
##
## Bearings are approximate on purpose. The star is a skeleton — points anchor a
## section's centre line, edges are free — so these sit where the perimeter had
## room rather than on exact rays. From the fountain: roughly 342, 62, 121 and
## 211 degrees, against a west arch at 273 and the entrance street at 182.
const THRESHOLDS := Plan.THRESHOLDS

const REACH := Plan.REACH
const BEND := Plan.BEND


## Two passes, and not one loop doing both.
##
## `_add` hands out seam displacement in build order, so anything inserted into
## the middle of a run shifts everything after it — the same trap as adding a
## scene anywhere but the end of the generator, one level down. Building each
## mouth right after its own passage looked tidier and moved every ordinal in
## the file: it put a passage wall on the same plane as a plaza wall in a scene
## nobody had edited, twice, and a bulkhead on a door for good measure.
##
## Passages first, in their original order, then the mouths appended. The four
## passages keep exactly the displacement they had.
func _thresholds() -> void:
	for t in THRESHOLDS:
		_passage(t["name"], t["at"], t["theta"], t["width"], t["turn"])
	for t in THRESHOLDS:
		_threshold_mouth(t["name"], t["at"], t["theta"], t["width"])


## What each way in looks like from the fountain.
##
## Colour and height per land rather than four identical arches, because four
## identical arches at four bearings read as a pattern — one thing repeated —
## and the whole reason these exist is that the park should read as continuing
## in five *different* directions. Four ways that look alike say there is one
## kind of elsewhere.
##
## `sign` is the board, `valance` the canopy under the beam, `cap` the finial on
## the piers. The cap is doing most of the work at distance: at forty metres a
## colour is a smudge and a silhouette is still a shape.
##
## This is generator data and not `ParkPlan` data on purpose. Where a section is
## belongs to the plan; what colour its sign is belongs to a section that does
## not exist yet, and inventing plan facts about four unbuilt places is how the
## plan stops being a record of the park.
## `tint` is the colour the mouth *glows* after dark, and it carries the same
## argument the sign colours and cap shapes already carry, one step further.
##
## Four identical arches at four bearings read as one thing repeated; the point
## of these is that the park continues in five different directions, and the
## board colour and finial are how that is said in daylight. Both stop saying it
## at sunset — a red board and a yellow board are the same grey under one warm
## lamp. Giving each mouth its own colour of light keeps the four ways out
## distinguishable from the fountain at night, which is when the plaza most
## needs them to be: an unlit passage reads as closed, and four identically lit
## ones read as one exit repeated.
##
## Matched to the board rather than chosen freshly, so the mouth is the same
## place by day and by night.
const THRESHOLD_MOUTH := {
	"nnw": {"sign": "canvas_alt", "valance": "canvas", "h": 2.6, "cap": "spire",
		"tint": "cyan"},
	"ne": {"sign": "wood", "valance": "canvas", "h": 2.2, "cap": "block",
		"tint": "warm"},
	"se": {"sign": "yellow", "valance": "canvas_alt", "h": 1.8, "cap": "ball",
		"tint": "amber"},
	"sw": {"sign": "red", "valance": "canvas_alt", "h": 2.4, "cap": "drum",
		"tint": "rose"},
}


## Local space is the passage's: +Z out of the plaza, so everything here is at
## negative z — the mouth is read from inside.
##
## The passage walls are 3.5m, so a board topping out near 10.5m stands clear of
## the passage without competing with the wall it is set into. That height is the
## point of the whole thing: the sign is what you see from the fountain, forty
## metres away, and the opening itself is barely a dark notch at that range.
##
## `MOUTH_H` is a single vertical multiplier over the whole frontispiece, added
## when the perimeter went from 8–12m to 13–19m on 2026-08-13. At 1.0 the mouth
## read as a shopfront in a long wall from the fountain, where the west arch
## beside it still read as a gate — the arch's advantage being that it tops its
## wall and the mouth does not. The mouth cannot top a 14.5m wall without
## becoming a monument, so it gets proportion instead: everything scales
## together and the relationships that make it a gateway survive. Nothing
## horizontal moves, because the width belongs to the passage, not the sign.
const MOUTH_H := 1.3


func _threshold_mouth(nm: String, base: Vector3, theta: float, w: float) -> void:
	var n := w * 0.5
	var spec: Dictionary = THRESHOLD_MOUTH[nm]
	var sh: float = spec["h"] * MOUTH_H

	# Piers, set 5cm clear of the passage walls rather than flush with them.
	# Flush, the pier's inner face and the wall's inner face are the same plane
	# pointing the same way over a 1.6m² overlap, which is a z-fight at the one
	# place in the passage the player is looking at.
	for i in 2:
		var sx := (-1.0 if i == 0 else 1.0) * (n + 0.6)
		_box("way_%s_pier_%d" % [nm, i], base, Vector3(sx, 2.25 * MOUTH_H, -0.45),
			Vector3(1.1, 4.7 * MOUTH_H, 1.6), "far_warm", theta)
		_mouth_cap("way_%s_cap_%d" % [nm, i], base, sx, theta, spec["cap"])

	_box("way_%s_lintel" % nm, base, Vector3(0, 5.05 * MOUTH_H, -0.45),
		Vector3(w + 2.3, 1.1 * MOUTH_H, 1.6), "far_warm", theta, false)

	# Valance and bulbs, hung on the plaza side of the beam. Same trick as the
	# alley mouth: a row of lights is what says a thing is open.
	_box("way_%s_valance" % nm, base, Vector3(0, 4.35 * MOUTH_H, -1.15),
		Vector3(w + 1.2, 0.18, 1.0), spec["valance"], theta, false)
	var bulbs: int = maxi(5, int(w * 0.8))
	for i in bulbs:
		var t := (float(i) + 0.5) / float(bulbs)
		var bx: float = lerpf(-n + 0.5, n - 0.5, t)
		_sphere("way_%s_bulb_%d" % [nm, i], base,
			Vector3(bx, 4.1 * MOUTH_H, -1.5), 0.13, "bulb", theta)

	# One pool for the whole valance rather than one per bulb. Eleven omnis in a
	# row two metres apart produce a single even wash at a tenth of the price of
	# one, and the *reading* of a bulb run comes from the emissive spheres — the
	# light on the ground under it only has to say the mouth is open.
	_omni("way_%s_glow" % nm, _place(base, Vector3(0, 3.9 * MOUTH_H, -1.5), theta),
		spec["tint"], 3.2, 13.0)

	# And the passage behind it, which is the actual point. A threshold is a
	# bend you cannot see the end of; unlit after dark it is a black rectangle
	# and reads as closed rather than as somewhere the park continues. Set back
	# under the lintel so the source is not visible from the plaza.
	# The throat stays warm whatever the mouth is. The colour belongs to the
	# *sign* — it says which land this is — and carrying it down the passage
	# would say the land itself is lit that colour, which is a claim about four
	# places nobody has built. Warm light receding behind a coloured mouth also
	# reads as depth; the same colour twice reads as one flat plane.
	_omni("way_%s_throat" % nm, _place(base, Vector3(0, 3.4 * MOUTH_H, 2.6), theta),
		"warm", 2.2, 11.0)

	# The board, lapping the beam. Wide but not full width: a sign the width of
	# its own opening reads as a lid on it.
	var by := 5.45 * MOUTH_H + sh * 0.5
	_box("way_%s_board" % nm, base, Vector3(0, by, -0.55),
		Vector3(w * 0.8, sh, 0.6), spec["sign"], theta, false)
	_box("way_%s_board_panel" % nm, base, Vector3(0, by, -0.85),
		Vector3(w * 0.8 - 2.0, sh - 0.8, 0.4), "white", theta, false)


## A finial, four ways. Cheap, and the only thing distinguishing the four ways
## out at the distance most of them are seen from.
##
## Every height here is scaled by `MOUTH_H` along with its own thickness rather
## than on its own, because each of these sits on the pier top: scaling where a
## plinth is without scaling how deep it is opens a six-centimetre gap under it.
func _mouth_cap(nm: String, base: Vector3, sx: float, theta: float, kind: String) -> void:
	var k := MOUTH_H
	match kind:
		"block":
			_box(nm, base, Vector3(sx, 4.85 * k, -0.45), Vector3(1.5, 0.5 * k, 2.0),
				"far_shade", theta, false)
		"ball":
			_box(nm + "_plinth", base, Vector3(sx, 4.8 * k, -0.45),
				Vector3(1.3, 0.4 * k, 1.8), "far_shade", theta, false)
			_sphere(nm, base, Vector3(sx, 5.5 * k, -0.45), 0.55 * k, "white", theta)
		"drum":
			_box(nm + "_plinth", base, Vector3(sx, 4.8 * k, -0.45),
				Vector3(1.3, 0.4 * k, 1.8), "far_shade", theta, false)
			_cyl(nm, base, Vector3(sx, 5.4 * k, -0.45), 0.55 * k, 1.0 * k, "white",
				theta, 10, false)
		_:
			# A mast, which is the tallest of the four and reads as trees rather
			# than as masonry from a distance.
			_box(nm + "_plinth", base, Vector3(sx, 4.8 * k, -0.45),
				Vector3(1.3, 0.4 * k, 1.8), "far_shade", theta, false)
			_box(nm, base, Vector3(sx, 6.0 * k, -0.45), Vector3(0.35, 2.4 * k, 0.35),
				"far_shade", theta, false)


## Local +Z is out of the plaza, local +X is the direction of the turn, and
## `turn` flips which way that is. Built in local space and rotated once, so the
## four of them are the same shape rather than four hand-placed near-misses.
func _passage(nm: String, base: Vector3, theta: float, w: float, turn: float) -> void:
	var n := w * 0.5
	var t := turn

	# Floors. Tops at y=0 to match the plaza, and the first one overlaps back
	# under the wall line so there is no seam at the threshold.
	#
	# Brick, the same bond as the plaza's, and it lines up with it because the
	# material is world-space projected. Which makes the threshold a change of
	# surface as well as a change of shape: the asphalt spoke runs up to the
	# piers and stops, and under the arch you are on the plaza's own paving. The
	# same beat as the alley mouth's asphalt-to-decking line, the other way up.
	_box("way_%s_floor_a" % nm, base, Vector3(0, -0.5 + PASSAGE_SEAM, REACH * 0.5 - 0.5),
		Vector3(w, 1, REACH + 1.0), "brick", theta)
	_box("way_%s_floor_b" % nm, base,
		Vector3(t * (n + BEND * 0.5), -0.5 + PASSAGE_SEAM, REACH - w * 0.5),
		Vector3(BEND, 1, w), "brick", theta)

	# The wall on the outside of the bend runs the whole way; the one on the
	# inside stops short, and that gap is the turn.
	_box("way_%s_side_far" % nm, base, Vector3(-t * (n + 0.25), 1.75, REACH * 0.5),
		Vector3(0.5, 3.5, REACH), "far_warm", theta)
	_box("way_%s_side_near" % nm, base,
		Vector3(t * (n + 0.25), 1.75, (REACH - w) * 0.5),
		Vector3(0.5, 3.5, REACH - w), "far_warm", theta)

	# Straight ahead as you come through the opening. This is what makes the
	# passage a turn rather than a corridor: from the plaza it reads as a wall
	# with somewhere behind it, not as a view of a dead end.
	_box("way_%s_ahead" % nm, base, Vector3(t * BEND * 0.5, 1.75, REACH + 0.25),
		Vector3(w + BEND + 1.0, 3.5, 0.5), "far_warm", theta)
	_box("way_%s_inner" % nm, base,
		Vector3(t * (n + BEND * 0.5 + 0.25), 1.75, REACH - w - 0.25),
		Vector3(BEND + 0.5, 3.5, 0.5), "far_warm", theta)
	# The end, only visible once you have made the turn. Where a section joins.
	_box("way_%s_end" % nm, base,
		Vector3(t * (n + BEND + 0.25), 1.75, REACH - w * 0.5),
		Vector3(0.5, 3.5, w), "far_shade", theta)

	# What you meet on walking in. An arcade, because an open dark mouth says the
	# park carries on through here better than a sign saying so — and because a
	# blank wall at the head of a passage is the thing that made these read as
	# service alcoves rather than as somewhere to go.
	_front("way_%s_arcade" % nm, _place(base, Vector3(0, 0, REACH), theta),
		theta + PI, minf(w - 1.0, 7.0), "arcade")
	# And one along the flank, so the passage has two sides worth looking at.
	_front("way_%s_shop" % nm, _place(base, Vector3(-t * n, 0, REACH * 0.45), theta),
		theta + t * PI * 0.5, 5.0, "cafe" if t > 0.0 else "store")

## A frontage stamped onto an existing wall. Local +Z faces out into the space
## the front is read from.
##
## Three kinds, and they differ in how open they are, which is the whole point:
## a store is glazed and shut, a cafe spills furniture into the walk, an arcade
## has no front at all — just a dark mouth with machines in it. Read down a
## street they give the run a rhythm that varying the building heights cannot.
##
## Nothing stamped here collides. The wall behind already stops the player, and
## a bulkhead standing a quarter-metre proud would be a ledge running the length
## of the street — steppable, but a snag every few metres for nothing. Only
## furniture genuinely standing in the walkway collides.
##
## Recess is faked with relief rather than cut, because CSG in separate scenes
## cannot subtract: piers standing proud of a dark bay throw a shadow across it,
## and at street distance that reads as depth.
func _front(nm: String, at: Vector3, theta: float, width: float, kind: String,
		solid := true) -> void:
	var n := width * 0.5
	var open_front := kind == "arcade"

	# Every foot in this unit is buried, and each by a different amount.
	#
	# A shopfront has four things standing on the pavement — two piers, a
	# bulkhead, and either a mouth or a row of cabinets — and all four had their
	# underside at exactly y=0, which is also where the buildings' undersides
	# are. Undersides are invisible, but they are real faces on a real plane, and
	# with a thousand of these in the plaza the seam ring lines two of them up
	# roughly every regeneration. Four different depths, none of them a whole
	# number of seam steps from another, and there is nothing left to align.
	_box("%s_pier_l" % nm, at, Vector3(-n + 0.15, 1.68, 0.15), Vector3(0.3, 3.44, 0.3),
		"white", theta, false)
	_box("%s_pier_r" % nm, at, Vector3(n - 0.15, 1.68, 0.15), Vector3(0.3, 3.44, 0.3),
		"white", theta, false)

	if open_front:
		# A faked mouth only where there is nothing behind the wall. Where the
		# room is real the doorway is a real hole, and a hole is darker than any
		# panel imitating one.
		if solid:
			_box("%s_mouth" % nm, at, Vector3(0, 1.325, 0.02), Vector3(width - 0.7, 2.75, 0.06),
				"glass", theta, false)
		_box("%s_soffit" % nm, at, Vector3(0, 2.85, 0.24), Vector3(width - 0.7, 0.3, 0.5),
			"far_shade", theta, false)
		# Cabinets just inside, in a row facing out. Silhouettes at this size, but
		# they are the difference between a dark rectangle and somewhere to go.
		var cabs := 0 if not solid else maxi(2, int((width - 1.6) / 1.1))
		for i in range(cabs):
			var x := -n + 1.0 + float(i) * ((width - 2.0) / maxf(1.0, float(cabs - 1)))
			_box("%s_cab_%d" % [nm, i], at, Vector3(x, 0.77, 0.42),
				Vector3(0.72, 1.66, 0.6), "far_shade", theta, false)
			_box("%s_cab_%d_screen" % [nm, i], at, Vector3(x, 1.25, 0.73),
				Vector3(0.5, 0.42, 0.06), "blue", theta, false)
	else:
		# Glass, bulkhead and door are three layers of relief on one wall, and
		# all three had their back face at exactly 0 — the wall's plane and each
		# other's. Their fronts are what reads, so the backs sink into the wall
		# by differing amounts and nothing shares a plane with anything.
		_box("%s_glass" % nm, at, Vector3(0, 1.7, 0.04), Vector3(width - 0.7, 2.1, 0.12),
			"glass", theta, false)
		_box("%s_bulkhead" % nm, at, Vector3(0, 0.435, 0.1), Vector3(width - 0.7, 0.93, 0.28),
			"accent", theta, false)
		# Off to one side. Centred, a door makes the unit read as a symmetrical
		# shed; off-centre it reads as a building somebody laid out.
		#
		# Its foot goes well *under* the pavement rather than five millimetres
		# over it. Five millimetres is exactly twenty seam steps, so whenever the
		# bulkhead's ordinal landed on 20 and the door's wrapped to 0 the two
		# undersides came out on the same plane — invisible under a doorway, but
		# it is a real pair and the ring is supposed to make those impossible
		# rather than unlikely. Six centimetres and not one: the perimeter
		# buildings' own undersides sit a few millimetres below zero, so a door
		# buried a hair lands on those instead.
		_box("%s_door" % nm, at, Vector3(n - 1.1, 1.02, 0.055), Vector3(1.0, 2.17, 0.17),
			"wood", theta, false)

	# Marquee for an arcade, plain fascia for the rest. `food` is `cafe` without
	# the terrace: the plaza's perimeter wants the sign colour but not two tables
	# and four stools per bay standing out on the crowd's floor.
	var band := 0.9 if open_front else 0.55
	var y := 3.7 if open_front else 3.55
	var sign_mat := "red"
	if kind == "cafe" or kind == "food":
		sign_mat = "yellow"
	elif kind == "store":
		sign_mat = "blue"
	_box("%s_fascia" % nm, at, Vector3(0, y, 0.16), Vector3(width, band, 0.32),
		"white", theta, false)
	_box("%s_sign" % nm, at, Vector3(0, y, 0.36), Vector3(width * 0.6, band * 0.7, 0.1),
		sign_mat, theta, false)

	if kind == "cafe":
		for i in range(2):
			var x := -n + 1.4 + float(i) * (width - 2.8)
			_cyl("%s_table_%d" % [nm, i], at, Vector3(x, 0.37, 1.5), 0.36, 0.74,
				"white", theta, 10)
			_cyl("%s_table_%d_leg" % [nm, i], at, Vector3(x, 0.18, 1.5), 0.1, 0.36,
				"metal", theta, 6, false)
			for j in range(2):
				var sx := x + (-0.75 if j == 0 else 0.75)
				_cyl("%s_stool_%d_%d" % [nm, i, j], at, Vector3(sx, 0.24, 1.5),
					0.18, 0.48, "wood", theta, 8)

## An open-air booth. No door, no interior, no load — a counter facing the walk,
## a back wall of prizes, and a canopy over it.
##
## This is what most park games actually are, and it is the shape that suits
## this one best: the player and the crowd stay in the same space, so a game
## being played is a thing other guests stand and watch, which is a photograph.
## A door would take all of that indoors and leave the walk emptier.
##
## Doors are for what genuinely wants to be inside — the arcade is dark and
## loud, and that is the whole reason it gets one.
func _booth(nm: String, base: Vector3, theta: float, width: float, mat: String) -> void:
	var n := width * 0.5
	var depth := 3.2

	_box(nm + "_back", base, Vector3(0, 1.6, -depth * 0.5), Vector3(width, 3.2, 0.3), mat, theta)
	_box(nm + "_side_l", base, Vector3(-n + 0.15, 1.6, 0), Vector3(0.3, 3.2, depth), mat, theta)
	_box(nm + "_side_r", base, Vector3(n - 0.15, 1.6, 0), Vector3(0.3, 3.2, depth), mat, theta)
	# Waist high and solid: the counter is the thing that makes it a booth rather
	# than a shed, and the thing the player leans on to shoot across.
	_box(nm + "_counter", base, Vector3(0, 0.55, depth * 0.5 - 0.3),
		Vector3(width - 0.6, 1.1, 0.6), "wood", theta)
	_box(nm + "_counter_top", base, Vector3(0, 1.14, depth * 0.5 - 0.3),
		Vector3(width - 0.3, 0.1, 0.8), "white", theta, false)
	_box(nm + "_canopy", base, Vector3(0, 3.3, 0.1), Vector3(width + 0.8, 0.25, depth + 1.0),
		"red", theta, false)
	_box(nm + "_valance", base, Vector3(0, 2.95, depth * 0.5 + 0.55),
		Vector3(width + 0.8, 0.5, 0.15), "yellow", theta, false)

	# The prize wall. Rows of small blocks read as stuffed toys at ten metres,
	# which is the distance this is meant to be photographed from.
	var cols := maxi(3, int(width / 0.8))
	for r in range(2):
		for c in range(cols):
			var x := -n + 0.7 + float(c) * ((width - 1.4) / maxf(1.0, float(cols - 1)))
			_box("%s_prize_%d_%d" % [nm, r, c], base,
				Vector3(x, 1.7 + float(r) * 0.65, -depth * 0.5 + 0.35),
				Vector3(0.42, 0.5, 0.3),
				["yellow", "blue", "white", "red"][(r * cols + c) % 4], theta, false)


## Freestanding on the walk rather than against a wall, so the street has
## something in the middle of it and a reason to weave.
## Name, position, bearing, width, material. Hoisted for the same reason the two
## street ranges were: the lighting has to hang bulbs on these valances, and a
## second typed copy of three positions is how a booth ends up lit where it used
## to stand.
const STREET_BOOTHS := [
	["booth_ring", Vector3(ST_X - 4.2, 0.0, 64.0), PI * 0.5, 4.5, "far_warm"],
	["booth_darts", Vector3(ST_X + 4.2, 0.0, 75.0), -PI * 0.5, 4.5, "accent"],
	["booth_hoops", Vector3(ST_X - 4.2, 0.0, 91.0), PI * 0.5, 4.0, "accent"],
]


func _street_booths() -> void:
	for row in STREET_BOOTHS:
		_booth(row[0], row[1], row[2], row[3], row[4])


## The arcade, built where it stands rather than swapped in behind a door.
##
## First person means the room and the street are never both in view, so there
## is nothing to gain by loading one and unloading the other — and a doorway you
## walk straight through beats one that cuts. Zelda loaded its shops because the
## N64 had four megabytes, which is a fact about 1998 and not a design idea.
##
## CSG in separate scenes cannot subtract, so the doorway is not cut: the front
## wall is built as two cheeks and a lintel, and the gap between them is the way
## in. Everything here is one scene with the street, which is the whole point.
const ARC_BACK := -29.0
const ARC_TALL := 4.4
const ARC_DOOR := 5.0


func _arcade_room(face: float, z: float, length: float) -> void:
	var depth := face - ARC_BACK
	var mid := (face + ARC_BACK) * 0.5
	var half := length * 0.5
	var dn := z - ARC_DOOR * 0.5
	var ds := z + ARC_DOOR * 0.5

	# A centimetre proud of the street rather than flush with it. Both are
	# up-facing floors and the overlap is 130m², so at exactly the same height
	# they z-fight across the whole arcade mouth — the ground flickers between
	# the street's colour and the arcade's as the player walks. A centimetre is
	# under the step-up and invisible as a lip.
	_box("arc_floor", Vector3.ZERO, Vector3(mid, -0.24, z),
		Vector3(depth, 0.5, length), "far_shade")
	_box("arc_roof", Vector3.ZERO, Vector3(mid, ARC_TALL + 0.2, z),
		Vector3(depth + 0.6, 0.4, length + 0.6), "far_warm")
	_box("arc_back", Vector3.ZERO, Vector3(ARC_BACK - 0.25, ARC_TALL * 0.5, z),
		Vector3(0.5, ARC_TALL, length), "accent")
	_box("arc_wall_n", Vector3.ZERO, Vector3(mid, ARC_TALL * 0.5, z - half + 0.25),
		Vector3(depth, ARC_TALL, 0.5), "accent")
	_box("arc_wall_s", Vector3.ZERO, Vector3(mid, ARC_TALL * 0.5, z + half - 0.25),
		Vector3(depth, ARC_TALL, 0.5), "accent")

	# The front, in three pieces. The gap is the door.
	# Held 2cm clear of the side walls at each end. Run out to meet them and the
	# cheek's outer face lands in the same plane as the wall's, which fights.
	var cheek := (length - ARC_DOOR) * 0.5 - 0.02
	_box("arc_cheek_n", Vector3.ZERO, Vector3(face - 0.245, ARC_TALL * 0.5, dn - cheek * 0.5 - 0.01),
		Vector3(0.5, ARC_TALL, cheek), "far_warm")
	_box("arc_cheek_s", Vector3.ZERO, Vector3(face - 0.245, ARC_TALL * 0.5, ds + cheek * 0.5 + 0.01),
		Vector3(0.5, ARC_TALL, cheek), "far_warm")
	_box("arc_lintel", Vector3.ZERO, Vector3(face - 0.25, 3.5, z),
		Vector3(0.5, 1.8, ARC_DOOR), "far_warm")

	# Cabinets down both flanks, facing the aisle, clear of the door line.
	for row in range(2):
		var x := ARC_BACK + 1.1 if row == 0 else face - 1.1
		var facing := -1.0 if row == 0 else 1.0
		for i in range(4):
			var cz := z - half + 1.6 + float(i) * ((length - 3.2) / 3.0)
			if row == 1 and cz > dn - 0.8 and cz < ds + 0.8:
				continue
			var nm := "arc_cab_%d_%d" % [row, i]
			_box(nm, Vector3.ZERO, Vector3(x, 0.85, cz), Vector3(0.9, 1.7, 0.8), "far_shade")
			_box(nm + "_screen", Vector3.ZERO, Vector3(x + facing * 0.5, 1.3, cz),
				Vector3(0.1, 0.5, 0.6), "blue", 0.0, false)
			_box(nm + "_top", Vector3.ZERO, Vector3(x + facing * 0.1, 1.85, cz),
				Vector3(0.75, 0.3, 0.75), "red", 0.0, false)

	# The counter and the change machine, which is what anybody is actually
	# queueing for. Both are subjects before they are anything else.
	_box("arc_counter", Vector3.ZERO, Vector3(mid + 2.0, 0.55, z - half + 1.0),
		Vector3(4.5, 1.1, 0.9), "wood")
	_box("arc_counter_top", Vector3.ZERO, Vector3(mid + 2.0, 1.15, z - half + 1.0),
		Vector3(4.9, 0.12, 1.1), "white", 0.0, false)
	_box("arc_change", Vector3.ZERO, Vector3(ARC_BACK + 0.9, 0.9, z + half - 1.1),
		Vector3(0.9, 1.8, 0.7), "red")


# ---------------------------------------------------------------------------
# The west, part three: the boardwalk, built for real
# ---------------------------------------------------------------------------

## The deck sits a hair proud of the shore rather than flush with it.
##
## Flush is z-fighting across 2,800m² of promenade; proud is a step. Four
## centimetres is proud enough that the depth buffer is never asked and low
## enough that the controller never notices, and every walkable surface down here
## uses the same figure — so there is no step anywhere the player actually walks,
## only at the edges, which are all either a building, the bluff, or a rail.
const DECK_TOP := Plan.SHORE_TOP + 0.04
const DECK_THICK := 0.5

## The section, in the order the player meets it.
##
## The sequence is the whole design and it is worth reading as one: down the
## stair, out of a gate into a service lane with the bluff on one side and the
## backs of buildings on the other, north twelve metres, then left through a hole
## in the frontage — and the water, the pier, the wheel and the coaster all
## arrive at once, sideways, having been completely hidden by a row of sheds.
##
## That is the same trick the arch and the gap play from the terrace, at
## one-tenth the distance. It works twice because the two reveals are of
## different things: from above you are shown where you are going, and from the
## alley you are shown that you have arrived.
func _boardwalk_section() -> void:
	_boardwalk_paving()
	_boardwalk_frontage()
	_alley_mouth()
	_boardwalk_wheel()
	_boardwalk_coaster()
	_boardwalk_pier()
	_boardwalk_edges()
	_boardwalk_props()
	_boardwalk_lights()
	_plaza_from_below()
	# The terrace's own asphalt, on the plaza's floor, laid here as well as into
	# `plaza_paving.tscn` — see `_terrace_paving`. It goes after
	# `_plaza_from_below` because that is what puts the floor under it.
	_terrace_paving()

	_arch_seam(&"boardwalk", &"plaza")


## Everything the player can stand on, as three slabs: the promenade, the alley
## through the frontage, and the back lane behind it.
##
## **The boards run across the way you walk, and that is how this section shows
## its circulation.** The plaza can pave a walkway darker than the ground either
## side of it; the promenade cannot, because there is no ground either side —
## the deck *is* the path, all 160m of it, and a strip painted down the middle
## would be inventing a distinction the place does not have.
##
## What a deck has instead is a direction, and the boards are it. Laid across the
## walk they read as "along" from any angle and at any distance, long after a
## 6mm gap has mipped away — the crown on each board survives even that. And the
## strip turns twice: west through the alley, and west again out onto the pier.
## Both turns are reveals, so the floor changes direction under the player at the
## moment the view does.
func _boardwalk_paving() -> void:
	var prom_w := (FRONT_X - FRONT_DEPTH * 0.5) - SHORE_EDGE
	var prom_x := (SHORE_EDGE + FRONT_X - FRONT_DEPTH * 0.5) * 0.5
	# North-south walk, so the boards run east-west.
	_box("deck_promenade", Vector3.ZERO,
		Vector3(prom_x, DECK_TOP - DECK_THICK * 0.5, (WALK_FROM_Z + WALK_TO_Z) * 0.5),
		Vector3(prom_w, DECK_THICK, WALK_TO_Z - WALK_FROM_Z), "plank")

	# The alley is walked east-west, so its boards turn with it. This is the one
	# the player meets first and the one that earns the second texture: you come
	# out of the lane, turn through the frontage, and the deck under you has
	# turned as well.
	_box("deck_alley", Vector3.ZERO,
		Vector3(FRONT_X, DECK_TOP - DECK_THICK * 0.5, (GAP_FROM + GAP_TO) * 0.5),
		Vector3(FRONT_DEPTH, DECK_THICK, GAP_TO - GAP_FROM), "plank_cross")

	# The lane runs from the backs of the shops to the foot of the bluff, laid
	# from one to the other with a metre of tuck at each end rather than butting
	# against either. Spanned from the two edges rather than centred on
	# `BACK_LANE_X` and given a width: that constant is where the *walk* runs, and
	# the walk moved west of the stair on 2026-08-14 while the ground did not.
	#
	# **Asphalt.** It is a service road behind a row of shops with a bluff on the
	# other side, and nobody decks a service road. It is also the only surface in
	# the section that is not boards, which means the material alone tells the
	# player that the twenty metres before the reveal are back-of-house — and
	# makes stepping onto the planking at the alley mouth the moment the
	# boardwalk starts.
	var lane_w := FRONT_X - FRONT_DEPTH * 0.5 - Plan.BLUFF_FACE_X
	var lane_x := (FRONT_X - FRONT_DEPTH * 0.5 + Plan.BLUFF_FACE_X) * 0.5
	_box("deck_lane", Vector3.ZERO,
		Vector3(lane_x, DECK_TOP - DECK_THICK * 0.5, 3.0),
		Vector3(-lane_w + 2.0, DECK_THICK, 74.0), "asphalt")


## The row, built. Same spans as the tableau, read out of the same table.
##
## Each unit is a box with a face on it: a recessed bay in glass, an awning over
## it, a sign board above that, and a service door round the back. Five pieces is
## enough for a greybox building to read as a shop rather than as a crate — the
## bay says there is an inside, the awning says it is hot, and the sign says
## somebody is trying to sell you something.
func _boardwalk_frontage() -> void:
	var front_face := FRONT_X - FRONT_DEPTH * 0.5
	var back_face := FRONT_X + FRONT_DEPTH * 0.5
	for i in FRONTAGE.size():
		var unit: Dictionary = FRONTAGE[i]
		var nm: String = unit["nm"]
		var from: float = unit["from"]
		var to: float = unit["to"]
		var h: float = unit["h"]
		var kind: String = unit["kind"]
		var mid := (from + to) * 0.5
		var depth := to - from
		var wall := "white" if i % 2 == 0 else "accent"

		_box("shop_%s" % nm, Vector3.ZERO, Vector3(FRONT_X, SHORE_TOP + h * 0.5, mid),
			Vector3(FRONT_DEPTH, h, depth), wall)
		_box("shop_%s_cap" % nm, Vector3.ZERO,
			Vector3(FRONT_X, SHORE_TOP + h + 0.25, mid),
			Vector3(FRONT_DEPTH + 1.0, 0.5, depth + 0.6), "far_shade", 0.0, false)

		# A shuttered unit gets boards instead of a window, which is the one
		# thing on the row that has to read differently close up.
		var bay_mat := "wood" if kind == "shut" else "glass"
		_box("shop_%s_bay" % nm, Vector3.ZERO,
			Vector3(front_face + 0.12, SHORE_TOP + 1.9, mid),
			Vector3(0.3, 2.6, depth - 2.4), bay_mat, 0.0, false)

		if kind != "shut":
			var awn := "canvas" if i % 2 == 0 else "canvas_alt"
			_box("shop_%s_awning" % nm, Vector3.ZERO,
				Vector3(front_face - 1.1, SHORE_TOP + 3.5, mid),
				Vector3(2.6, 0.16, depth - 1.6), awn, 0.0, false, -0.18)
			_box("shop_%s_post_n" % nm, Vector3.ZERO,
				Vector3(front_face - 2.2, SHORE_TOP + 1.6, mid - depth * 0.5 + 1.0),
				Vector3(0.14, 3.2, 0.14), "metal")
			_box("shop_%s_post_s" % nm, Vector3.ZERO,
				Vector3(front_face - 2.2, SHORE_TOP + 1.6, mid + depth * 0.5 - 1.0),
				Vector3(0.14, 3.2, 0.14), "metal")

		# The sign is what makes a roofline a street. Sat above the parapet on
		# the tall units and flat on the wall on the short ones, because a row
		# where every sign is at the same height reads as a fence.
		var sign_mat := "red" if kind == "games" else ("yellow" if kind == "food" else "blue")
		if h >= 8.0:
			_box("shop_%s_sign" % nm, Vector3.ZERO,
				Vector3(front_face - 0.3, SHORE_TOP + h + 1.9, mid),
				Vector3(0.4, 3.0, minf(depth - 2.0, 9.0)), sign_mat, 0.0, false)
		else:
			_box("shop_%s_sign" % nm, Vector3.ZERO,
				Vector3(front_face - 0.15, SHORE_TOP + h - 0.9, mid),
				Vector3(0.3, 1.3, minf(depth - 2.0, 7.0)), sign_mat, 0.0, false)

		# The back. A door, and something left against the wall — the service
		# side is where a photographer finds the thing nobody meant them to see,
		# so it gets furniture rather than being a blank face.
		_box("shop_%s_door" % nm, Vector3.ZERO,
			Vector3(back_face - 0.1, SHORE_TOP + 1.05, mid + 1.0),
			Vector3(0.3, 2.1, 0.95), "metal", 0.0, false)
		if i % 3 == 0:
			_box("shop_%s_bin" % nm, Vector3.ZERO,
				Vector3(back_face + 1.1, SHORE_TOP + 0.6, mid - depth * 0.5 + 1.4),
				Vector3(1.4, 1.2, 1.1), "metal")
		if i % 3 == 1:
			_box("shop_%s_crate" % nm, Vector3.ZERO,
				Vector3(back_face + 0.9, SHORE_TOP + 0.35, mid - 1.6),
				Vector3(0.8, 0.7, 0.8), "wood")


## The hole in the frontage, made into a doorway.
##
## The floor was carrying the arrival on its own: asphalt stops, decking starts,
## and that line was the only thing saying you had got somewhere. It works, and
## it should not be working alone — the two buildings either side are plain
## slabs and read as a missing shopfront rather than as a way through.
##
## So: a beam across, legs under it, a valance with bulbs, and a sign standing
## proud of the 5.5m roofline so it is visible over the roofs from down the lane
## before the gap itself is. Both ends get one, because a hole with a header at
## only one end is a hole you came in by rather than a passage.
##
## **The lane end is the event and the promenade end is the acknowledgement**, so
## they are not the same: the arrival sign is taller and in the loud canvas red,
## the one facing the strip is lower and blue. Coming back east it should read as
## the way out and not as a second entrance.
##
## Nothing here goes into `west_far.tscn`, and that is deliberate rather than an
## oversight. The tableau's whole job from the overlook is "the arch frames a
## gap, the gap frames the pier" — and a sign board spanning eleven of the
## fourteen metres at that height sits exactly across the sightline to the
## pavilion. Measured from the parapet it would cover its top. So the mouth
## belongs only on the side you are close enough to walk under.
func _alley_mouth() -> void:
	var front_face := FRONT_X - FRONT_DEPTH * 0.5
	var back_face := FRONT_X + FRONT_DEPTH * 0.5
	var gap_w := GAP_TO - GAP_FROM
	# face x, which way is out, sign height, sign colour, valance colour, bulbs
	var faces := [
		[back_face, 1.0, 2.4, "canvas", "canvas_alt", 9, "lane"],
		[front_face, -1.0, 1.7, "canvas_alt", "canvas", 7, "strip"],
	]
	for f in faces:
		var fx: float = f[0]
		var out: float = f[1]
		var sh: float = f[2]
		var sign_mat: String = f[3]
		var valance_mat: String = f[4]
		var bulbs: int = f[5]
		var tag: String = f[6]

		# The beam, let into both buildings rather than butted against them —
		# 0.4m of lap at each end, which is also what keeps its end faces off
		# theirs. Nothing above head height collides: a box at 4.3m that the
		# player can walk into is a bug waiting for somebody to find it.
		_box("alley_beam_%s" % tag, Vector3.ZERO,
			Vector3(fx - out * 0.5, SHORE_TOP + 4.8, ALLEY_Z),
			Vector3(1.2, 1.0, gap_w + 0.8), "wood", 0.0, false)

		# Corbels at the ends, so the beam is carried rather than floating.
		for i in 2:
			var cz: float = GAP_FROM + 0.35 if i == 0 else GAP_TO - 0.35
			_box("alley_corbel_%s_%d" % [tag, i], Vector3.ZERO,
				Vector3(fx - out * 0.5, SHORE_TOP + 4.05, cz),
				Vector3(0.9, 0.6, 1.4), "wood", 0.0, false)

		# Legs, standing on the deck 0.6m in from each corner. They collide,
		# which is fine: the alley is 14m wide and its walkway is the middle 6,
		# so a post at 6.4m off centre is nowhere anybody walks.
		for i in 2:
			var pz: float = GAP_FROM + 0.6 if i == 0 else GAP_TO - 0.6
			_box("alley_post_%s_%d" % [tag, i], Vector3.ZERO,
				Vector3(fx + out * 0.45, SHORE_TOP + 2.15, pz),
				Vector3(0.28, 4.3, 0.28), "wood")

		# The valance, and the bulbs along its lip. Flat rather than raked: the
		# `_box` tilt turns about the part's own X, which cants a canopy along
		# the frontage instead of sloping it outward, and a flat soffit under a
		# beam is what this wants anyway.
		_box("alley_valance_%s" % tag, Vector3.ZERO,
			Vector3(fx + out * 0.75, SHORE_TOP + 4.18, ALLEY_Z),
			Vector3(1.5, 0.18, gap_w - 1.0), valance_mat, 0.0, false)
		for i in bulbs:
			var t := (float(i) + 0.5) / float(bulbs)
			var bz: float = lerpf(GAP_FROM + 1.2, GAP_TO - 1.2, t)
			_sphere("alley_bulb_%s_%d" % [tag, i],
				Vector3(fx + out * 1.2, SHORE_TOP + 3.95, bz), Vector3.ZERO,
				0.13, "bulb")

		# The mouth's own glow, one per end. The lane end is the event and the
		# promenade end is the acknowledgement — the same asymmetry the sign
		# heights and colours carry — so the brighter one goes on the side you
		# arrive from and the arrival stays a one-way reveal after dark.
		_omni("alley_glow_%s" % tag, Vector3(fx + out * 1.2, SHORE_TOP + 3.8, ALLEY_Z),
			"warm", 4.2 if tag == "lane" else 2.8, 15.0)

		# The sign, lapping the beam by 0.15 so it sits on it, and standing
		# 1.5m clear of the neighbours' rooflines so the lane sees it first.
		_box("alley_sign_%s" % tag, Vector3.ZERO,
			Vector3(fx + out * 0.2, SHORE_TOP + 5.15 + sh * 0.5, ALLEY_Z),
			Vector3(0.5, sh, gap_w - 3.0), sign_mat, 0.0, false)
		_box("alley_sign_panel_%s" % tag, Vector3.ZERO,
			Vector3(fx + out * 0.5, SHORE_TOP + 5.15 + sh * 0.5, ALLEY_Z),
			Vector3(0.25, sh - 0.8, gap_w - 5.0), "white", 0.0, false)


## The wheel, standing on the promenade with a fence round its feet.
##
## The ring, hub and spokes are the same assembly the tableau uses — it was
## always built at full size, because a wheel is a ring and a ring is legible at
## any distance, so there was never a cheap version to replace. What the section
## adds is everything that says it is a machine somebody operates: a deck, cars
## on the rim, a fence, a queue rail, and a booth with the lever in it.
func _boardwalk_wheel() -> void:
	var base := Vector3(WHEEL_AT.x, SHORE_TOP, WHEEL_AT.y)
	var half := Plan.WHEEL_PLATFORM * 0.5
	_box("wheel_deck", Vector3.ZERO, base + Vector3(0, 0.3, 0),
		Vector3(Plan.WHEEL_PLATFORM.x, 0.6, Plan.WHEEL_PLATFORM.y), "plank")
	_wheel(base + Vector3(0, 0.6, 0), "white", PI * 0.5)

	# Cars. Eight, on the rim the spokes already reach, hung below their pin so
	# they read as swinging rather than as bolted on. In the Z–Y plane, same as
	# the ring — a car placed in X would be a car threaded through the axle.
	var hub := base + Vector3(0, 18.6, 0)
	for i in 8:
		var a := TAU * i / 8.0
		var at := hub + Vector3(0, sin(a) * 12.7, cos(a) * 12.7)
		_box("wheel_car_%d" % i, Vector3.ZERO, at + Vector3(0, -1.1, 0),
			Vector3(2.0, 1.4, 1.6), "red" if i % 2 == 0 else "yellow", 0.0, false)

	# The fence round the platform, open on the east side where the queue and
	# the booth are. Posts along three sides, at 2m.
	var n := 0
	var z := base.z - half.y
	while z <= base.z + half.y:
		_box("wheel_fence_w_%d" % n, Vector3.ZERO,
			Vector3(base.x - half.x, SHORE_TOP + 1.2, z), Vector3(0.12, 1.2, 0.12), "metal")
		z += 2.0
		n += 1
	for side in [-1.0, 1.0]:
		var tag := "n" if side < 0.0 else "s"
		_box("wheel_fence_%s" % tag, Vector3.ZERO,
			Vector3(base.x, SHORE_TOP + 1.2, base.z + side * half.y),
			Vector3(Plan.WHEEL_PLATFORM.x, 1.2, 0.12), "metal")

	# The booth stands off the platform's east side, facing the promenade, with
	# the queue rail running back along the frontage.
	var booth := Vector3(base.x + half.x + 1.4, SHORE_TOP, base.z - 3.0)
	_box("wheel_booth", Vector3.ZERO, booth + Vector3(0, 1.3, 0),
		Vector3(2.2, 2.6, 2.6), "white")
	_box("wheel_booth_roof", Vector3.ZERO, booth + Vector3(0, 2.75, 0),
		Vector3(2.8, 0.3, 3.2), "blue", 0.0, false)
	_box("wheel_booth_sign", Vector3.ZERO, booth + Vector3(-1.2, 3.5, 0),
		Vector3(0.2, 1.4, 2.6), "red", 0.0, false)
	for i in 6:
		_box("wheel_queue_%d" % i, Vector3.ZERO,
			booth + Vector3(1.6, 0.5, 1.4 + i * 1.6), Vector3(0.08, 1.0, 0.08), "metal")


## The coaster closes the north end.
##
## Out-and-back along the shore, on the frontage's own line so it reads as the
## last building on the row and then keeps going for ninety metres. The player
## walks beside it and under nothing — the structure is fenced, because it is a
## lattice of six-sided columns with no collision on it and a fence is both
## cheaper and what a real park does.
##
## The station is the piece that matters at ten metres. It is the only building
## in the section with a roof you can see the underside of, and it is where the
## queue is, which is where the photographs are.
func _boardwalk_coaster() -> void:
	var origin := Vector3(FRONT_X, SHORE_TOP, COASTER_STATION.y - 2.0)
	_wooden_coaster(origin, 0.0, "wood")

	# North of where the frontage stops, so the station reads as the last
	# building on the row rather than as one crashed into the arcade.
	var st := Vector3(FRONT_X, SHORE_TOP, COASTER_STATION.y - 4.0)
	_box("station_floor", Vector3.ZERO, st + Vector3(0, 0.55, 0),
		Vector3(11.0, 1.1, 12.0), "plank")
	for i in 6:
		var x := st.x - 4.4 + (i % 3) * 4.4
		var z := st.z - 4.6 + floorf(i / 3.0) * 9.2
		_box("station_post_%d" % i, Vector3.ZERO, Vector3(x, SHORE_TOP + 3.2, z),
			Vector3(0.3, 5.2, 0.3), "wood")
	_box("station_roof", Vector3.ZERO, st + Vector3(0, 5.9, 0),
		Vector3(13.0, 0.4, 14.0), "far_shade", 0.0, false)
	_box("station_sign", Vector3.ZERO, st + Vector3(-6.6, 6.9, 0),
		Vector3(0.4, 2.4, 8.0), "red", 0.0, false)

	# The fence between the promenade and the structure, from the station north
	# to where the walk stops.
	var z := COASTER_STATION.y - 12.0
	var n := 0
	while z > WALK_FROM_Z:
		_box("coaster_fence_%d" % n, Vector3.ZERO,
			Vector3(FRONT_X - FRONT_DEPTH * 0.5, SHORE_TOP + 0.75, z),
			Vector3(0.1, 1.5, 3.6), "metal")
		z -= 4.0
		n += 1


## The pier: the second strip, at right angles to the first, and the only thing
## in the section that goes somewhere new.
##
## Santa Monica's half of the reference. Walking out on it puts the whole
## boardwalk broadside — the frontage, the wheel and the coaster all at once,
## from forty metres offshore — which is the section photographing itself, and
## the reason it is walkable rather than scenery.
func _boardwalk_pier() -> void:
	var root := Vector3(PIER_ROOT.x, SHORE_TOP, PIER_ROOT.y)
	var mid := root + Vector3(-PIER_LENGTH * 0.5, 0, 0)
	# Walked east-west, so the boards run north-south — the other way from the
	# promenade it leaves. Standing at the pier mouth, that turn in the decking
	# is the first thing that says the pier goes somewhere the strip does not.
	_box("pier_deck", Vector3.ZERO,
		Vector3(mid.x, DECK_TOP - DECK_THICK * 0.5, mid.z),
		Vector3(PIER_LENGTH, DECK_THICK, PIER_HALF_W * 2.0), "plank_cross")

	# Rails both sides, in posts and a top rail rather than as one long box, so
	# that the water reads between them from a low camera.
	var posts := int(PIER_LENGTH / 2.2)
	for i in posts + 1:
		var x := root.x - i * 2.2
		for side in [-1.0, 1.0]:
			var tag := "n" if side < 0.0 else "s"
			_box("pier_post_%d_%s" % [i, tag], Vector3.ZERO,
				Vector3(x, SHORE_TOP + 0.6, root.z + side * (PIER_HALF_W - 0.15)),
				Vector3(0.12, 1.2, 0.12), "wood")
	for side in [-1.0, 1.0]:
		var tag := "n" if side < 0.0 else "s"
		_box("pier_rail_%s" % tag, Vector3.ZERO,
			Vector3(mid.x, SHORE_TOP + 1.15, root.z + side * (PIER_HALF_W - 0.15)),
			Vector3(PIER_LENGTH, 0.14, 0.16), "wood")

	var piles := int(PIER_LENGTH / 5.0)
	for i in piles:
		var x := root.x - 3.0 - i * 5.0
		for side in [-3.0, 3.0]:
			_cyl("pile_%d_%s" % [i, "n" if side < 0.0 else "s"], Vector3.ZERO,
				Vector3(x, WATER_TOP - 0.4, root.z + side), 0.28, 4.0,
				"far_shade", 0.0, 6, false)

	# The pavilion at the head. Solid for now: it is the silhouette the sun sets
	# behind and the stop at the end of the strip, and an interior is a room
	# nobody has designed yet. The doors are on it so that it reads as closed
	# rather than as unfinished.
	var head := Vector3(PAVILION_AT.x, SHORE_TOP, PAVILION_AT.y)
	# Carries the pier's boards through to the end, because it is the pier's last
	# sixteen metres and not a separate place.
	_box("pavilion_apron", Vector3.ZERO,
		Vector3(head.x, DECK_TOP - DECK_THICK * 0.5, head.z),
		Vector3(16.0, DECK_THICK, 17.0), "plank_cross")
	_box("pavilion", Vector3.ZERO, head + Vector3(0, 3.4, 0),
		Vector3(12.0, 6.8, 13.0), "white")
	_box("pavilion_roof", Vector3.ZERO, head + Vector3(0, 7.1, 0),
		Vector3(14.0, 0.6, 15.0), "far_shade", 0.0, false)
	_box("pavilion_band", Vector3.ZERO, head + Vector3(0, 6.4, 0),
		Vector3(12.4, 0.7, 13.4), "canvas", 0.0, false)
	_cyl("pavilion_spire", Vector3.ZERO, head + Vector3(0, 10.2, 0),
		0.3, 5.6, "far_shade", 0.0, 6, false)
	_box("pavilion_doors", Vector3.ZERO, head + Vector3(6.1, 1.4, 0),
		Vector3(0.3, 2.8, 3.6), "wood", 0.0, false)


## The boardwalk after dark, which is the section the whole thing is for.
##
## The plaza at night is a lit room; the strip is a lit *object*, seen end-on
## down 160m of promenade and broadside from the overlook 40m above it. Its own
## day curve says so — the boardwalk is at 100% at seven in the evening when the
## plaza is falling, so this is the busiest place in the park at the exact hour
## the sun goes into the water behind it. Everything here is built for that hour.
##
## Which is also why this is the one section allowed colour. The palette note on
## `canvas` already says the boardwalk is the loud one; after dark that stops
## being a claim about awnings and becomes a claim about light.
func _boardwalk_lights() -> void:
	_wheel_lights()
	_pavilion_lights()
	_coaster_lights()
	_lane_lights()


## The wheel: outlined, then washed.
##
## The outline is the part that matters and it is geometry rather than lighting —
## twenty-four bulbs on the rim, on the `bulb` material like every other festoon
## in the park, so they come up with everything else. A wheel is the one ride
## whose real-world night presentation is *entirely* points of light on a circle,
## and no amount of floodlighting substitutes for it: washed but not outlined it
## reads as a large grey wheel that somebody has pointed a light at.
##
## In the Z–Y plane, because the wheel faces the plaza — the same constraint the
## cars are placed under, and a bulb placed in X is a bulb threaded through the
## axle.
func _wheel_lights() -> void:
	var base := Vector3(WHEEL_AT.x, SHORE_TOP, WHEEL_AT.y)
	var hub := base + Vector3(0, 18.6, 0)
	var r := Plan.WHEEL_RADIUS
	for i in 24:
		var a := TAU * float(i) / 24.0
		_sphere("wheel_bulb_%d" % i, hub,
			Vector3(0, sin(a) * r, cos(a) * r), 0.16, "bulb")

	# Washed from the platform, up both flanks of the disc. Rose, and it is the
	# one place in the park with a light this saturated: the wheel is the thing
	# you are meant to see from the overlook and from the far end of the strip,
	# and colour carries further than brightness once everything else is warm
	# white.
	var half := Plan.WHEEL_PLATFORM * 0.5
	for side in [-1.0, 1.0]:
		_uplight("wheel_wash_%s" % ["n" if side < 0.0 else "s"],
			Vector3(base.x, SHORE_TOP + 0.9, base.z + side * (half.y - 1.0)),
			Vector3(base.x, SHORE_TOP + 20.0, base.z + side * 3.0),
			"rose", 4.0, 34.0, 30.0)

	# The booth, which is where somebody is standing and therefore where the
	# photographs are. Small, warm, and a fixture rather than a feature — a ride
	# still selling tickets at half past nine is the park being open.
	_omni("wheel_booth_glow",
		Vector3(base.x + half.x + 1.4, SHORE_TOP + 2.5, base.z - 3.0),
		"warm", 2.4, 9.0)


## The pavilion at the pier head, which is what the sun sets behind.
##
## That is its whole job in the composition, and it means the pavilion has a
## handover to make rather than a state: it is a silhouette against the sunset,
## and then the sunset goes and it has to become the thing at the end of the pier
## that is worth walking out to. Lit, it is a lantern at 130m over black water —
## the only thing west of the frontage with any light on it at all, which is the
## strongest reason the player has to walk the pier after dark.
##
## Cyan against the promenade's warm white. Cool light reads as further away, so
## it separates from the strip behind it instead of joining the row.
func _pavilion_lights() -> void:
	var head := Vector3(PAVILION_AT.x, SHORE_TOP, PAVILION_AT.y)
	for i in 4:
		var a := TAU * float(i) / 4.0 + PI * 0.25
		var p := head + Vector3(cos(a) * 8.4, 0.35, sin(a) * 9.0)
		_uplight("pavilion_wash_%d" % i, p,
			head + Vector3(cos(a) * 4.0, 8.4, sin(a) * 4.2),
			"cyan", 3.2, 20.0, 40.0, LIGHT_FEATURE, i == 0)

	# The spire, its own light. It stands 3m clear of the roof and a wash aimed
	# at the box misses it entirely.
	_uplight("pavilion_spire_wash", head + Vector3(2.2, 7.6, 0.0),
		head + Vector3(0.0, 13.4, 0.0), "cyan", 2.0, 12.0, 22.0)

	# Under the roof overhang, so the building has a lit underside as well as a
	# lit face. Warm, unlike the wash — a cool building with a warm eave reads as
	# a lit place inside a floodlit shell, which is what a closed pavilion with
	# the lights left on should look like.
	for side in [-1.0, 1.0]:
		_omni("pavilion_eave_%s" % ["n" if side < 0.0 else "s"],
			head + Vector3(0.0, 6.6, side * 6.2), "warm", 1.8, 10.0)


## The coaster, which is a lattice and lights like one.
##
## Structure this open should be lit from *behind and below* rather than washed
## flat: what makes a wooden coaster read at night is the depth of the bents
## receding, and that only happens when the light is coming through it. So these
## sit on the seaward side aiming back inland, and the player walking the
## promenade sees ninety metres of timber with light between the members.
func _coaster_lights() -> void:
	var from_z := Plan.COASTER_FROM_Z
	var to_z := Plan.COASTER_TO_Z
	for i in 4:
		var t := (float(i) + 0.5) / 4.0
		var z: float = lerpf(from_z, to_z, t)
		_uplight("coaster_wash_%d" % i,
			Vector3(FRONT_X - 9.0, SHORE_TOP + 0.3, z),
			Vector3(FRONT_X - 1.0, SHORE_TOP + 15.0, z),
			"wash", 2.6, 26.0, 36.0)

	# The station, which is the piece that matters at ten metres and the only
	# roof in the section you see the underside of.
	_omni("coaster_station_glow",
		Vector3(FRONT_X, SHORE_TOP + 4.2, COASTER_STATION.y - 2.0),
		"warm", 3.0, 14.0, LIGHT_FIXTURE, true)


## The back lane, and the park's only lights that are still on at two in the
## morning.
##
## `night.md` asks for a park that is "powered, and awake" rather than switched
## off at the main — compressors running, a freezer humming, a cart with its
## light still on. These are the visual half of that. They are deliberately few
## and deliberately ugly: a service road lit by four bulkheads over ten back
## doors is not composed, and that is the difference between the park at eleven
## and the park at ten.
##
## They are also what keeps the arrival court from being a black hole after
## close, which matters because the cascade lands in it and the player coming
## down has to be able to see the ground.
func _lane_lights() -> void:
	var z := -40.0
	var n := 0
	while z < 60.0:
		_omni("lane_service_%d" % n, Vector3(BACK_LANE_X - 5.4, SHORE_TOP + 3.6, z),
			"lamp", 1.4, 11.0, LIGHT_SERVICE)
		z += 25.0
		n += 1
	# The cart in the lane, with its light left on. One prop, and it is the
	# single most load-bearing light in the after-close park: it is the thing
	# that says somebody was here a minute ago.
	_omni("lane_cart_glow", Vector3(BACK_LANE_X + 1.2, SHORE_TOP + 1.8, 22.0),
		"warm", 1.6, 7.0, LIGHT_SERVICE)


## What stops the player walking off the edges of the section.
##
## Three different edges and three different answers, on purpose. The water gets
## a rail because a rail is what a promenade has. The south end gets a chain and
## a sign, because the strip has to visibly carry on past where you may go —
## a wall there would say the world ends and a chain says the park does. The
## north end is the coaster's fence, already built.
func _boardwalk_edges() -> void:
	var n := 0
	var z := WALK_FROM_Z
	while z <= WALK_TO_Z:
		# The break for the pier. Everything else gets a post.
		if absf(z - PIER_ROOT.y) > 5.0:
			_box("edge_post_%d" % n, Vector3.ZERO,
				Vector3(SHORE_EDGE + 0.4, SHORE_TOP + 0.6, z),
				Vector3(0.14, 1.3, 0.14), "wood")
			n += 1
		z += 2.4
	# Two runs of rail, north and south of the pier mouth. **These collide.** The
	# posts are 2.4m apart and the player is 0.8 across, so a decorative rail
	# between colliding posts is a gap the player walks through and off the edge
	# — which looks exactly like a rail right up until somebody tries it.
	var runs := [[WALK_FROM_Z, PIER_ROOT.y - 5.0], [PIER_ROOT.y + 5.0, WALK_TO_Z]]
	for i in runs.size():
		var run: Array = runs[i]
		var from: float = run[0]
		var to: float = run[1]
		_box("edge_rail_%d" % i, Vector3.ZERO,
			Vector3(SHORE_EDGE + 0.4, SHORE_TOP + 1.2, (from + to) * 0.5),
			Vector3(0.16, 0.14, to - from), "wood")

	# Both ends of the strip. A chain rather than a wall, because the shore
	# visibly carries on past both and a wall there would say the world ends
	# where a chain says the park does. It collides for the same reason the rail
	# does: a barrier the player walks through is scenery, not a barrier.
	var east_edge := FRONT_X - FRONT_DEPTH * 0.5
	for end in [[WALK_TO_Z, "south"], [WALK_FROM_Z, "north"]]:
		var z_at: float = end[0]
		var tag: String = end[1]
		_box("%s_chain_post_w" % tag, Vector3.ZERO,
			Vector3(SHORE_EDGE + 1.0, SHORE_TOP + 0.55, z_at),
			Vector3(0.2, 1.1, 0.2), "metal")
		_box("%s_chain_post_e" % tag, Vector3.ZERO,
			Vector3(east_edge - 1.0, SHORE_TOP + 0.55, z_at),
			Vector3(0.2, 1.1, 0.2), "metal")
		_box("%s_chain" % tag, Vector3.ZERO,
			Vector3((SHORE_EDGE + east_edge) * 0.5, SHORE_TOP + 0.85, z_at),
			Vector3(16.4, 0.1, 0.1), "metal")
		_box("%s_sign" % tag, Vector3.ZERO,
			Vector3(SHORE_EDGE + 5.0, SHORE_TOP + 1.4, z_at),
			Vector3(1.6, 0.9, 0.1), "white", 0.0, false)

	# The east side of the promenade south of the row, so the strip is closed
	# rather than fraying into raw shore.
	var yz := FRONT_TO_Z
	var m := 0
	while yz < WALK_TO_Z:
		_box("yard_fence_%d" % m, Vector3.ZERO,
			Vector3(FRONT_X - FRONT_DEPTH * 0.5, SHORE_TOP + 0.75, yz),
			Vector3(0.1, 1.5, 3.6), "metal")
		yz += 4.0
		m += 1


## Furniture. Benches facing the water, lamps, bins, and the masts with the
## bulbs on them that were a silhouette in the tableau and are the section's
## whole night lighting plan up close.
func _boardwalk_props() -> void:
	# Benches face west, at the rail, because that is what the view is. The line
	# comes from the plan, so `gen_crowd.gd` can sit people on exactly these
	# rather than on a second copy of the same arithmetic.
	var line := Plan.bench_line()
	for n in line.size():
		var at: Vector2 = line[n]
		_bench("prom_bench_%d" % n, Vector3(at.x, SHORE_TOP, at.y), -PI * 0.5)

	# Lamp standards down the middle of the promenade.
	var m := 0
	var z := WALK_FROM_Z + 6.0
	while z < WALK_TO_Z:
		# The wheel's platform occupies the centre line for 26m; a lamp there is
		# a lamp inside the ride.
		if absf(z - WHEEL_AT.y) > 15.0:
			_cyl("prom_lamp_%d" % m, Vector3.ZERO,
				Vector3(PROMENADE_X, SHORE_TOP + 2.4, z), 0.11, 4.8, "metal", 0.0, 8)
			_sphere("prom_lamp_%d_globe" % m,
				Vector3(PROMENADE_X, SHORE_TOP + 5.0, z), Vector3.ZERO,
				0.34, "lamp_glass")
			# Inside the globe, unlike the plaza's — this fitting is a translucent
			# sphere rather than an opaque box, so the source belongs at its centre
			# and the geometry reads as lit from within.
			_omni("prom_lamp_%d_pool" % m,
				Vector3(PROMENADE_X, SHORE_TOP + 5.0, z), "lamp", 3.0, 16.0,
				LIGHT_FIXTURE, m % 2 == 0)
			m += 1
		z += 9.0

	# Masts, and a bulb every couple of metres between them. The bulbs are the
	# composition after dark — a string of points with silhouette in between is
	# the look-and-feel note made out of geometry.
	# The mast spacing lands one of them exactly on the pier's centre line, which
	# is a post planted in the only doorway in the section. Skipped there, and the
	# string of bulbs skips the span with it rather than hanging off nothing.
	var k := 0
	var prev_mast := 0.0
	var had_prev := false
	z = WALK_FROM_Z + 4.0
	while z < WALK_TO_Z:
		if absf(z - PIER_ROOT.y) > 5.0:
			_cyl("mast_%d" % k, Vector3.ZERO,
				Vector3(SHORE_EDGE + 1.6, SHORE_TOP + 4.0, z), 0.22, 8.0, "wood", 0.0, 6)
			if had_prev and z - prev_mast < 12.0:
				_light_string(k, prev_mast, z)
			prev_mast = z
			had_prev = true
			k += 1
		z += 11.0

	# Bins, and the two carts that say somebody works here.
	var b_at := [-30.0, -12.0, 8.0, 26.0, 46.0, 64.0]
	for i in b_at.size():
		_cyl("prom_bin_%d" % i, Vector3.ZERO,
			Vector3(PROMENADE_X + 3.2, SHORE_TOP + 0.45, b_at[i]), 0.38, 0.9, "metal", 0.0, 8)
	_box("prom_cart", Vector3.ZERO, Vector3(PROMENADE_X - 3.0, SHORE_TOP + 0.7, 18.0),
		Vector3(1.8, 1.4, 1.0), "blue")
	_box("prom_cart_roof", Vector3.ZERO, Vector3(PROMENADE_X - 3.0, SHORE_TOP + 2.1, 18.0),
		Vector3(2.4, 0.14, 1.6), "canvas", 0.0, false)
	_box("lane_cart", Vector3.ZERO, Vector3(BACK_LANE_X + 1.2, SHORE_TOP + 0.5, 22.0),
		Vector3(1.2, 1.0, 2.0), "metal")

	# Tables outside the two food units. Four of them, and they are the third
	# population down here — the boardwalk has no cafe, so without these the
	# crowd's "sitting at a table" curve has nowhere to put anybody and the
	# section reads the hour with one fewer instrument than the plaza does.
	#
	# Set 3m off the shopfronts rather than against them, because a table against
	# a wall is a wall with a table and a table with room round it is somewhere
	# people are eating.
	for i in Plan.TABLES.size():
		var at: Vector2 = Plan.TABLES[i]
		var base := Vector3(at.x, SHORE_TOP, at.y)
		_cyl("table_%d_top" % i, base, Vector3(0, 0.78, 0), 0.62, 0.08, "white", 0.0, 10)
		_cyl("table_%d_post" % i, base, Vector3(0, 0.39, 0), 0.09, 0.78, "metal", 0.0, 8)
		_cyl("table_%d_foot" % i, base, Vector3(0, 0.03, 0), 0.42, 0.06, "metal", 0.0, 10)
		# The umbrella is 2.2m up and overhangs rather than blocking, same as the
		# plaza's — which is why the crowd generator treats a table as a 1.15m
		# circle and ignores the shade entirely.
		_cyl("table_%d_pole" % i, base, Vector3(0, 1.5, 0), 0.05, 2.4, "metal", 0.0, 6)
		_cyl("table_%d_shade" % i, base, Vector3(0, 2.26, 0), 1.6, 0.1,
			"canvas" if i % 2 == 0 else "canvas_alt", 0.0, 10, false)
		for j in 2:
			var off := Vector3(0.95, 0.0, 0.2) if j == 0 else Vector3(-0.9, 0.0, -0.35)
			var seat := base + off
			_box("table_%d_chair_%d" % [i, j], seat, Vector3(0, 0.44, 0),
				Vector3(0.44, 0.06, 0.44), "wood")
			_box("table_%d_chair_%d_back" % [i, j], seat, Vector3(0, 0.7, -0.2),
				Vector3(0.44, 0.46, 0.06), "wood")
			_cyl("table_%d_chair_%d_leg" % [i, j], seat, Vector3(0, 0.22, 0),
				0.06, 0.44, "metal", 0.0, 6)


## A run of bulbs between two masts, and the cable they hang on.
##
## The cable was missing. The bulbs were placed on a sag curve and nothing was
## drawn between them, which reads as a string of lights from the far end of the
## strip and as five spheres floating in a row from underneath — and underneath
## is where the player walks.
##
## One curve, both things. The bulbs sit on the interior sample points and the
## cable joins all seven, so a bulb is on the wire by construction rather than
## near it. Straight segments rather than anything curved: at five centimetres
## across, the kink at each sample is smaller than the cable is thick.
##
## The ends land on the mast centre line 0.6m below its top, so each run
## terminates inside the pole rather than short of it.
const STRING_HEIGHT := 7.4
const STRING_SAG := 0.55
const STRING_STEPS := 6


func _light_string(index: int, from_z: float, to_z: float) -> void:
	var x := SHORE_EDGE + 1.6
	var span := to_z - from_z
	var points: Array[Vector3] = []
	for s in STRING_STEPS + 1:
		var t := float(s) / float(STRING_STEPS)
		points.append(Vector3(x,
			SHORE_TOP + STRING_HEIGHT - STRING_SAG * sin(PI * t),
			from_z + span * t))
	for s in STRING_STEPS:
		_strut("wire_%d_%d" % [index, s], points[s], points[s + 1], 0.05, "metal")
	for b in STRING_STEPS - 1:
		_sphere("bulb_%d_%d" % [index, b], points[b + 1], Vector3.ZERO, 0.11, "bulb")

	# One light for the span, at the sag. Five bulbs 2m apart is one wash, and
	# the emissive spheres are what carry the *look* of a festoon — this is only
	# here so the deck under it is warmer than the deck between spans, which is
	# what stops 160m of promenade being lit like a corridor.
	#
	# Low energy and long range on purpose. The masts stand at the water's edge,
	# so this is a rim light down the seaward side of the walk rather than
	# another lamp: it catches the rail, the benches and the backs of the crowd,
	# and leaves the shopfront side to the standards.
	_omni("string_%d_glow" % index, points[STRING_STEPS / 2], "warm", 1.8, 13.0)


## Everything west of here is on the skyline from the boardwalk. It is the
## plaza's own west range and the terrace in front of it; the bandstand at −20
## and the fountain at the origin are behind fifteen metres of wall and would
## never be seen even if they were emitted.
const BELOW_WEST_X := -30.0

## Thinner than this is detail at ninety metres. Drops the overlook's copings —
## 16cm bands on top of a parapet — and keeps the parapet.
const BELOW_MIN_H := 1.0


## The plaza, seen from below, as massing with nothing behind it.
##
## This exists because the plaza is *gone* down here. `ParkSections` frees the
## outgoing section, so the bluff the player just walked down, the parapet they
## looked over and the arch they walked through all cease to exist the moment
## they step through the gate — and the bluff top would be a clean horizon line
## with sky above it, which is the one thing that would say "this is a different
## level" out loud.
##
## **Read off `plaza.tscn` since 2026-08-13, and it had to be.** This used to be
## six literals, and the comment over them said the duplication was "the kind a
## test can hold: anything that moves the plaza's west face and not these will
## show up as the skyline sliding". No such test was ever written, and by today
## every one of the six was wrong: 7m walls against a real perimeter of 13–19,
## at x=−26 against a real west range at −44 to −33, and a 14m sign tower at
## x=18 against a 40m one at −1.5. The plaza had grown from 80m to 104m and gone
## taller twice underneath a stand-in nobody re-derived, which is exactly the
## failure the plan file exists to prevent — and the fix is the plan file's own
## first answer: generate it, rather than describe it a second time.
##
## Two things it deliberately does not carry. The **frontage** is applied to
## inner faces only, so from the west there is nothing of it to see — the outer
## faces are blank and the massing is right to be blank with them. And the
## **roof clutter** would show a metre or two of cupola over the roofline from
## the promenade; it is left off, because a stand-in that reproduces detail is a
## stand-in that has to be kept in step with detail.
func _plaza_from_below() -> void:
	var n := 0
	for box in _plaza_scene_boxes():
		var nm: String = box["nm"]
		var at: Vector3 = box["at"]
		var size: Vector3 = box["size"]
		if size.y < BELOW_MIN_H:
			continue
		# The tower by name rather than by position: it stands on the gate axis
		# in the middle of the plaza, and it is here because it is the one thing
		# tall enough to clear its own west wall from down on the promenade.
		var framed := _framed_by_arch(at, size)
		if not (nm.begins_with("tower_") or at.x < BELOW_WEST_X or framed):
			continue
		# The near boundary is no longer scenery. The seam moved to the arch on
		# 2026-08-14, so the player crosses onto the terrace and stands two
		# metres from this wall — it gets the plaza's own material and it
		# collides, or they walk through the back of the arch they just came
		# under. Everything else here is still a silhouette seen from ninety
		# metres down on the promenade and stays washed and passable.
		var near := _near_boundary(nm)
		var mat := "far_warm" if nm.begins_with("tower_") else "far"
		if near:
			mat = "accent" if nm.ends_with("_sign") else "building"
		# Snapped to the centimetre, and that is not tidiness.
		#
		# The plaza's shapes carry hand displacement, and it runs *downward and
		# inward* — on the west side each successive node is a quarter-millimetre
		# further out in −X. `_add` displaces in +X by the same step in the same
		# order. Copied verbatim, the two cancel exactly: the arch's two piers and
		# its lintel came out sharing three planes over ninety square metres, all
		# of it hand displacement that had been carefully arranged in the file
		# they were read from. Snapping throws that away and lets this scene's own
		# ring do the separating, which is the only ring that applies here.
		# Dropped a hand's width when it is only here to be seen down the tunnel.
		# The plaza's `ground` is one of these and it is 104m of up-facing floor
		# at exactly y=0, which is also `terrace_floor`'s — two floors on one
		# plane, five hundred square metres of it. Everything framed by the arch
		# is a silhouette between fifteen and a hundred metres off through a six
		# metre aperture, so a 12cm drop costs nothing and settles it for all of
		# them rather than special-casing the one that collides.
		var drop := 0.0 if (near or at.x < BELOW_WEST_X) else BELOW_FRAMED_DROP
		_box("far_%s" % nm, Vector3.ZERO,
			at.snapped(Vector3.ONE * 0.01) - Vector3(0.0, drop, 0.0), size,
			mat, 0.0, near)
		n += 1
	if n < 6:
		push_error("only %d plaza masses read for the view from below — " % n
			+ "the parse found nothing, or the west range has been renamed")

	# The floor the terrace stands on.
	#
	# It is the plaza's own ground seen from the far side of a seam that has
	# moved: up to today the player crossed at the bottom of the stair and never
	# stood up here without the plaza mounted. Now they cross under the arch, and
	# without this they would walk through it and fall six metres to the shore.
	#
	# Brick, which looks like it breaks "no brick west of the bluff" and does
	# not. That rule is about the strip *below* — the two sections disagreeing
	# about their material is what makes arriving down there feel like arriving.
	# The terrace is on top of the bluff, inside the plaza's own wall line, and
	# it is the plaza's floor: the player walks under the arch and the ground
	# under them must not change, because nothing about the ground did.
	_box("terrace_floor", Vector3.ZERO, Vector3(-42.5, -0.5, -2.5),
		Vector3(19.0, 1.0, 27.0), "brick")


## How far the arch-framed masses sit below where `plaza.tscn` puts them. See the
## drop in `_plaza_from_below` — it is the plaza floor and the terrace floor
## sharing a plane, settled once for everything that comes in this way.
const BELOW_FRAMED_DROP := 0.12


## Whether the tunnel points at this, standing on the terrace looking back east.
##
## The other half of `_plaza_from_below`'s own argument. That function exists
## because a bluff top with nothing above it says "different level" out loud;
## a tunnel with *sky* at the end of it says the same thing louder, because the
## player is two metres from the near end and it is the way they just came. The
## arch was 9m wide and 8.9m clear until 2026-08-14 and would have shown a great
## deal of nothing; at 6 by 5 it shows a small rectangle of nothing, which is
## still nothing.
##
## The cone is the aperture as seen from where they are put down: half the
## opening, opened out by how much further away a thing is than the far mouth.
## Anything whose footprint reaches into it is worth emitting. What that picks up
## is the ground, the fountain the arch is aimed at, and the east range ninety
## metres on that closes the view — which is all three of the things you would
## expect to see down a tunnel into a plaza.
func _framed_by_arch(at: Vector3, size: Vector3) -> bool:
	var stand: float = Plan.ARCH_ARRIVE_WEST.x
	var mouth: float = Plan.ARCH_MOUTH_X
	if at.x < mouth:
		return false
	var half := Plan.ARCH_WIDTH * 0.5 * (at.x - stand) / (mouth - stand)
	return absf(at.z - Plan.ARCH_AT.y) - size.z * 0.5 < half


const BELOW_NEAR := ["perim_w_", "arch_", "overlook_", "wall_west_"]


## Whether a piece of the plaza's boundary is one the player can now walk up to.
func _near_boundary(nm: String) -> bool:
	for prefix in BELOW_NEAR:
		if nm.begins_with(prefix):
			return true
	return false


# ---------------------------------------------------------------------------
# The plaza's frontage
# ---------------------------------------------------------------------------

## What the perimeter is made of, applied to walls that already exist.
##
## The perimeter went to 13–19m on 2026-08-13 and the enclosure came back with
## it, but a 19m greybox slab is a great deal of nothing — from the fountain the
## east wall was most of the frame with no incident in it at all. Height without
## frontage reads as a retaining wall rather than as buildings, and the taller
## the wall the more it reads that way.
##
## **Laid by rule off the walls themselves, not off a table.** The perimeter is
## the one hand-authored thing in the world and its runs live as baked literals
## in `plaza.tscn`, where no generator can reach them. A copy in `ParkPlan` would
## be the fourth survey of the same park, which is the mistake that file exists
## to stop. So this reads the scene as text and derives the frontage from what is
## actually standing: move a wall in the editor and the frontage follows on the
## next run, and a wall that is not there gets no shopfront.
##
## Text rather than `load()` because `plaza.tscn` instances the very scene this
## writes. Loading it would make the generator depend on its own output, and the
## first run after a clean checkout — or any run where the output is missing —
## would fail on a dependency it is in the middle of creating.
const FRONTAGE_PATH := "res://scenes/world/plaza_frontage.tscn"
const PLAZA_SCENE_PATH := "res://scenes/world/plaza.tscn"

## Bare wall left at each end of a run. Architecturally a quoin; practically the
## clearance that keeps the last pilaster off the threshold mouths, whose piers
## stand in the gaps the runs end at.
const FRONT_INSET := 0.9

## Top of the shopfront storey. `_front` builds to 3.83 with its fascia, so this
## is the first floor line and everything above it is upper storeys.
const FRONT_GROUND := 4.3

## The band under the roofline. Reserved out of the wall before the storeys are
## divided, so a cornice never lands on top of a row of windows.
const FRONT_CORNICE := 1.2

## Widest a bay is allowed to get before the run takes another one. Bays come out
## 5.4 to 8.4m across the perimeter, which is a shop unit rather than a warehouse
## door, and the count is per run so no two runs share a rhythm by accident.
const FRONT_BAY_MAX := 9.0

## How far the whole frontage is set into the wall it is applied to.
##
## Everything here is relief on a face, so the natural thing is to sit each
## element's back exactly on that face — which is fine along a wall and wrong at
## a corner, where the *next* building's end face is the same plane pointing the
## same way. The north range's east end and the east range's inner face are both
## x=36, so a shopfront pilaster on the east wall shared a plane with a building
## a quarter of the park away. Four centimetres in and no back face is on any
## plane at all; nothing that projects stops projecting.
const FRONT_SINK := 0.04


## Every box in `plaza.tscn`, by name, centre and size in world units.
##
## Read once and kept, because two things want it now: the frontage, which needs
## the perimeter runs, and the massing the boardwalk shows in the plaza's place,
## which needs everything on the plaza's west side. Only `CSGBox3D` — a node with
## no `size` is skipped, which is how the fountain's cylinders and the instanced
## sub-scenes drop out without being named here.
var _plaza_boxes: Array = []


func _plaza_scene_boxes() -> Array:
	if not _plaza_boxes.is_empty():
		return _plaza_boxes
	var f := FileAccess.open(PLAZA_SCENE_PATH, FileAccess.READ)
	if f == null:
		push_error("cannot read %s" % PLAZA_SCENE_PATH)
		return _plaza_boxes
	var text := f.get_as_text()
	f.close()

	var nm := ""
	var origin := Vector3.ZERO
	var size := Vector3.ZERO
	for raw in text.split("\n"):
		var line := raw.strip_edges()
		if line.begins_with("[node "):
			_keep_box(nm, origin, size)
			nm = _quoted(line, "name=\"")
			origin = Vector3.ZERO
			size = Vector3.ZERO
		elif line.begins_with("transform = Transform3D("):
			var n := _numbers(line)
			if n.size() >= 12:
				origin = Vector3(n[9], n[10], n[11])
		elif line.begins_with("size = Vector3("):
			var n := _numbers(line)
			if n.size() >= 3:
				size = Vector3(n[0], n[1], n[2])
	_keep_box(nm, origin, size)
	return _plaza_boxes


func _keep_box(nm: String, origin: Vector3, size: Vector3) -> void:
	if nm != "" and size.length() > 0.0:
		_plaza_boxes.append({"nm": nm, "at": origin, "size": size})


## The perimeter runs.
##
## Only `perim_*` — the arch piers, the lintel, the boundary fences and the
## overlook walls are named differently on purpose and get no frontage.
func _perimeter_runs() -> Array:
	var out: Array = []
	for box in _plaza_scene_boxes():
		if String(box["nm"]).begins_with("perim_"):
			out.append(box)
	return out


func _quoted(line: String, key: String) -> String:
	var a := line.find(key)
	if a < 0:
		return ""
	a += key.length()
	var b := line.find("\"", a)
	return line.substr(a, b - a) if b > a else ""


func _numbers(line: String) -> Array:
	var a := line.find("(")
	var b := line.rfind(")")
	if a < 0 or b <= a:
		return []
	var out: Array = []
	for part in line.substr(a + 1, b - a - 1).split(","):
		out.append(part.strip_edges().to_float())
	return out


func _plaza_frontage() -> void:
	var runs := _perimeter_runs()
	if runs.is_empty():
		push_error("no perim_* runs found in %s — the frontage would be empty, "
			% PLAZA_SCENE_PATH + "which means the parse broke rather than the wall moved")
		return
	for i in runs.size():
		_facade(runs[i], i)
	_gate_house()
	for i in runs.size():
		_facade_wash(runs[i], i)


## Floodlighting a perimeter run from close in against its own face.
##
## This is the change that decides whether the plaza is a room after dark. The
## enclosure argument the 104m plaza was rebuilt around is entirely about the
## walls: 13–19m of building at r≈36 subtends 23° from the hub, and that subtense
## is what makes the space read as enclosed rather than as an open square. None
## of it survives the sun going down unless the walls are lit — an unlit
## perimeter is not a low wall, it is *no* wall, and the plaza opens onto black
## in every direction.
##
## So the wash goes on the wall rather than on the ground in front of it, and the
## fittings sit 2.2m off the face. That distance is doing the same work here as
## on the cascade: `plaza_frontage.tscn` is 1,066 nodes of storey courses, window
## reveals, awnings, cornices and pediments, and grazing light is the only thing
## that turns relief into shadow. Lit from out in the plaza the same 1,066 nodes
## come back as one evenly bright surface, which is the greybox slab the frontage
## was laid to stop being.
##
## One station per 14m of run, which lands 2 to 5 on each of the perimeter's
## eight ranges. Inset by `FRONT_INSET * 2` so the end stations do not fire
## across a threshold gap into the passage behind it.
func _facade_wash(run: Dictionary, index: int) -> void:
	var at: Vector3 = run["at"]
	var size: Vector3 = run["size"]
	# Which way the run lies, and which way is into the plaza. A range's long
	# axis is whichever of x and z is bigger; the short one is its thickness, and
	# the inward normal points from the wall back towards the origin.
	var along_x := size.x >= size.z
	var length: float = size.x if along_x else size.z
	var face: float = size.z if along_x else size.x
	var inward := -signf(at.z if along_x else at.x)
	if is_zero_approx(inward):
		inward = 1.0

	var usable := length - FRONT_INSET * 4.0
	if usable <= 0.0:
		return
	var count: int = maxi(2, int(usable / 14.0))
	var top: float = at.y + size.y * 0.5
	for i in count:
		var t := (float(i) + 0.5) / float(count)
		var along: float = lerpf(-usable * 0.5, usable * 0.5, t)
		var off := face * 0.5 + 2.2
		var p: Vector3
		var aim: Vector3
		if along_x:
			p = Vector3(at.x + along, 0.3, at.z + inward * off)
			aim = Vector3(at.x + along, top - 1.5, at.z + inward * (face * 0.5 - 0.5))
		else:
			p = Vector3(at.x + inward * off, 0.3, at.z + along)
			aim = Vector3(at.x + inward * (face * 0.5 - 0.5), top - 1.5, at.z + along)
		# Aimed short of the parapet rather than over it. The roofline is meant
		# to be a broken silhouette against the sky — that is what the pediments
		# and the roof clutter are for — and washing it evenly to the top erases
		# the one thing up there worth having.
		_uplight("facade_wash_%d_%d" % [index, i], p, aim, "wash", 3.6, 26.0, 44.0)


## The arch's own face, which the perimeter's frontage does not reach.
##
## `_facade` works on `perim_*` runs, and the gate house is three `arch_*` boxes
## — so when the arch became a tunnel on 2026-08-14 and its mass came 2.5m
## forward of the wall line, what arrived in the plaza was fifteen metres of
## blank white slab standing proud between two dressed shopfronts. That is the
## same complaint the whole frontage pass was laid to answer, one building later.
##
## It is not given shopfronts, because it is not a shop: a plinth, a course at
## the height its neighbours put theirs, a cornice and a parapet, and a raised
## surround round the opening. What that does is make the arch read as a doorway
## into a building rather than a hole in a wall, which is also what makes the
## tunnel behind it read as a tunnel.
##
## Read out of `plaza.tscn` like everything else here, so moving the arch in the
## editor moves its dressing. The three boxes are named rather than found by
## shape — an arch is the one thing in the perimeter with a hole in it, and there
## is no rule over a box that says "this one is a gate".
func _gate_house() -> void:
	var mass := {}
	for box in _plaza_scene_boxes():
		var nm: String = box["nm"]
		if nm in ["arch_pier_north", "arch_pier_south", "arch_lintel"]:
			mass[nm] = box
	if mass.size() < 3:
		push_error("the arch's three masses were not all found in %s — "
			% PLAZA_SCENE_PATH + "the gate house would be dressed against nothing")
		return

	var north: Dictionary = mass["arch_pier_north"]
	var south: Dictionary = mass["arch_pier_south"]
	var lintel: Dictionary = mass["arch_lintel"]
	# The face you see from the plaza, the two outer edges, and the top.
	var face: float = north["at"].x + north["size"].x * 0.5
	var from_z: float = north["at"].z - north["size"].z * 0.5
	var to_z: float = south["at"].z + south["size"].z * 0.5
	var top: float = north["at"].y + north["size"].y * 0.5
	# The opening, as the two pier faces that make it and the lintel's underside.
	var open_n: float = north["at"].z + north["size"].z * 0.5
	var open_s: float = south["at"].z - south["size"].z * 0.5
	var head: float = lintel["at"].y - lintel["size"].y * 0.5
	var width := to_z - from_z
	var mid := (from_z + to_z) * 0.5

	# Plinth and ground-floor course, both broken at the opening because you walk
	# through it. The course sits at `FRONT_GROUND` so it runs on into the
	# shopfronts either side rather than starting a line of its own.
	for i in 2:
		var a: float = from_z if i == 0 else open_s
		var b: float = open_n if i == 0 else to_z
		_box("gate_plinth_%d" % i, Vector3.ZERO,
			Vector3(face + 0.09, 0.45, (a + b) * 0.5),
			Vector3(0.34, 0.9, b - a), "far_shade", 0.0, false)
		_box("gate_course_%d" % i, Vector3.ZERO,
			Vector3(face + 0.06, FRONT_GROUND, (a + b) * 0.5),
			Vector3(0.28, 0.34, b - a), "white", 0.0, false)

	# The surround. Two jambs and a head, each lapping 2cm into the opening so
	# that no face of theirs lands on a face of the piers'.
	for i in 2:
		var jz: float = (open_n - 0.33) if i == 0 else (open_s + 0.33)
		_box("gate_jamb_%d" % i, Vector3.ZERO,
			Vector3(face + 0.17, head * 0.5, jz),
			Vector3(0.36, head, 0.7), "white", 0.0, false)
	_box("gate_head", Vector3.ZERO,
		Vector3(face + 0.17, head + 0.36, Plan.ARCH_AT.y),
		Vector3(0.36, 0.72, Plan.ARCH_WIDTH + 1.6), "white", 0.0, false)

	# Cornice and parapet. The parapet stands on the roof rather than on the
	# face, which is what stops a 12.5m mass ending in a raw edge against the sky.
	_box("gate_cornice", Vector3.ZERO,
		Vector3(face + 0.14, top - FRONT_CORNICE * 0.5, mid),
		Vector3(0.5, FRONT_CORNICE, width + 0.52), "white", 0.0, false)
	_box("gate_parapet", Vector3.ZERO,
		Vector3(face - 0.52, top + 0.56, mid),
		Vector3(1.24, 1.12, width + 0.18), "building", 0.0, false)


## One run of perimeter, from the pavement to the skyline.
##
## Local space is the wall's: +X along it, +Z out of its inner face, so every
## number below is read the way you would read it standing in front of the
## building. Which face is the inner one is decided by which side of the run the
## fountain is on, so nothing here has to know which wall it is working on.
func _facade(run: Dictionary, idx: int) -> void:
	var c: Vector3 = run["at"]
	var s: Vector3 = run["size"]
	var along_x: bool = s.x > s.z
	var length: float = s.x if along_x else s.z
	var thick: float = s.z if along_x else s.x
	var h: float = s.y
	var normal := (Vector3(0.0, 0.0, -signf(c.z)) if along_x
		else Vector3(-signf(c.x), 0.0, 0.0))
	var theta := atan2(normal.x, normal.z)
	var base := Vector3(c.x, 0.0, c.z) + normal * (thick * 0.5 - FRONT_SINK)
	var tag := "f%02d" % idx

	var usable := length - FRONT_INSET * 2.0
	var bays: int = maxi(1, int(ceil(usable / FRONT_BAY_MAX)))
	var bw := usable / float(bays)

	# Every horizontal in this run is lifted by a few centimetres nobody will
	# read, and the amount is a function of which run it is.
	#
	# Two runs meeting at a corner overlap over about a third of a square metre,
	# and equal-height runs — there are several, the perimeter only has five
	# heights in it — put their floor lines, cornices and parapets at exactly the
	# same y. The seam ring cannot help: it separates shapes that are *near each
	# other in build order*, and a corner is two shapes sixty nodes apart. So the
	# runs disagree by construction instead. Real adjacent buildings do not share
	# a floor line either, which is the other reason to want this.
	var jog := 0.031 * float((idx * 3) % 5)

	# Storeys divide what is left after the shopfront and the cornice have taken
	# theirs, so the top floor is never a sliver and the courses always land on
	# the wall rather than through the roof. They do **not** divide it evenly —
	# see `_storey_heights`.
	var upper := h - FRONT_GROUND - jog - FRONT_CORNICE
	var storeys: int = clampi(int(round(upper / 3.0)), 1, 5)
	var floors := _storey_heights(upper, storeys)
	var ground := FRONT_GROUND + jog

	# Floor lines, one per storey including the shopfront's own cornice at 4.3.
	# Run the whole length rather than per bay: a course that stops at every
	# joint reads as a row of sheds, and the point of these is that a run is one
	# building with several shops in it.
	var y := ground
	for st in storeys:
		_box("%s_course_%d" % [tag, st], base, Vector3(0.0, y, 0.14),
			Vector3(length - 0.5, 0.26, 0.46), "white", theta, false)
		y += floors[st]

	for b in bays:
		_facade_bay(tag, base, theta, idx, b, bays, bw,
			-length * 0.5 + FRONT_INSET + bw * (float(b) + 0.5), floors,
			ground, h + jog)

	# The cornice oversails the parapet, which is what makes the roofline a shadow
	# line rather than an edge. Both sink into the wall by different amounts —
	# butted flush their back faces and the wall's face are one plane.
	#
	# The parapet runs *past* the wall it caps rather than stopping on it. Level
	# with the ends its side faces are the wall's own side faces, which is a
	# fight wherever a run's displacement happens to be zero — and it is also
	# what leaves a notch at the two places where runs butt instead of being
	# separated by a threshold gap.
	_box("%s_cornice" % tag, base, Vector3(0.0, h + jog - FRONT_CORNICE * 0.5, 0.2),
		Vector3(length - 0.2, FRONT_CORNICE * 0.6, 0.62), "white", theta, false)
	_box("%s_parapet" % tag, base, Vector3(0.0, h + jog + 0.45, 0.0),
		Vector3(length + 0.12, 1.1, 0.72), "building", theta, false)
	_box("%s_parapet_cap" % tag, base, Vector3(0.0, h + jog + 1.06, 0.03),
		Vector3(length + 0.24, 0.2, 0.94), "far_shade", theta, false)

	_roofline(tag, base, theta, idx, length, thick, h + jog)


## A bay: the shop at the bottom, windows above it, and on some of them the
## raised parapet that breaks the roofline.
## Storey heights, diminishing upward.
##
## This is forced perspective, and it is the one park-specific trick in the whole
## frontage. Main Street's buildings are about ten metres and read as three or
## four floors, because the ground floor is full height and everything above it
## is built at roughly five-eighths and then half. Divide a wall into equal
## storeys instead and every building reads at its true size — which is what the
## first pass did, and is most of why 13–19m came out looking like a civic
## office block rather than a park.
##
## So the same wall reads shorter than it measures, and the unevenly spaced floor
## lines are the visible signature of it. 0.78 per floor is gentler than Main
## Street's, because these are seen from forty metres across an open plaza rather
## than from a street eleven metres wide.
const FRONT_FALLOFF := 0.78


func _storey_heights(upper: float, storeys: int) -> Array:
	var weights: Array = []
	var total := 0.0
	for i in storeys:
		var k: float = pow(FRONT_FALLOFF, float(i))
		weights.append(k)
		total += k
	var out: Array = []
	for i in storeys:
		out.append(upper * weights[i] / total)
	return out


func _facade_bay(tag: String, base: Vector3, theta: float, idx: int, b: int,
		bays: int, bw: float, bx: float, floors: Array,
		ground: float, h: float) -> void:
	var at := _place(base, Vector3(bx, 0.0, 0.0), theta)
	var nm := "%s_b%d" % [tag, b]

	# Kinds walk across the perimeter rather than repeating per run, so no wall
	# is a row of the same shop and no two adjacent runs start on the same one.
	var kinds := ["store", "food", "store", "arcade"]
	_front(nm, at, theta, minf(bw - 1.4, 8.0), kinds[(idx * 3 + b) % kinds.size()])

	# Awnings on about half the bays. On all of them the wall reads as a market
	# stall; on none of it there is nothing at eye level but glass. No posts,
	# unlike the street's: a colonnade round the plaza would say arcade, and
	# anything standing on the floor here is something the crowd has to walk
	# round that the wander graph does not know about.
	if _hash01(idx, b, 17) < 0.55:
		var canvases := ["canvas", "canvas_alt", "red", "yellow"]
		var cm: String = canvases[int(_hash01(idx, b, 23) * 4.0) % 4]
		_box("%s_awning" % nm, at, Vector3(0.0, 3.98, 0.86),
			Vector3(bw - 1.9, 0.16, 1.7), cm, theta, false)
		for i in 2:
			var sx := (-1.0 if i == 0 else 1.0) * (bw * 0.5 - 1.15)
			_box("%s_bracket_%d" % [nm, i], at, Vector3(sx, 3.55, 0.34),
				Vector3(0.1, 0.86, 0.66), "metal", theta, false)

	# Windows, applied rather than punched. Nothing here is a CSG boolean — the
	# shapes are siblings, not a combiner — so a hole in a wall is not available
	# and a recess would simply be a box inside a solid. What reads as a window
	# is a dark panel standing a hair proud with a lighter head over it, which is
	# the same trick the street's glazing plays.
	# The windows shrink with their storey, in width as well as height. Height
	# alone would leave a row of letterboxes on the top floor; taking both keeps
	# each opening the same *shape* while the whole storey gets smaller, which is
	# what sells the lie.
	var wins := 2 if bw < 7.2 else 3
	var ww0 := minf(1.45, bw / (float(wins) * 2.15))
	var sill := ground
	for st in floors.size():
		var sh: float = floors[st]
		var ww := ww0 * pow(FRONT_FALLOFF, float(st) * 0.6)
		var wh := minf(2.2, sh - 1.05)
		var y := sill + sh * 0.52
		for w in wins:
			var t := (float(w) + 0.5) / float(wins)
			var wx := lerpf(-bw * 0.5 + ww0, bw * 0.5 - ww0, t)
			_box("%s_win_%d_%d" % [nm, st, w], at, Vector3(wx, y, 0.07),
				Vector3(ww, wh, 0.14), "glass", theta, false)
			_box("%s_head_%d_%d" % [nm, st, w], at, Vector3(wx, y + wh * 0.5 + 0.13, 0.11),
				Vector3(ww + 0.34, 0.2, 0.26), "white", theta, false)
		sill += sh

	# One bay per run carries a raised parapet. This is the piece doing the work
	# the whole pass is for: fifteen runs of different height already step the
	# roofline at every joint, and this steps it in the middle of a run as well,
	# so no single wall is a straight line against the sky.
	if b == idx % bays:
		var pw := minf(bw * 0.6, 5.2)
		_box("%s_ped" % nm, at, Vector3(0.0, h + 1.55, 0.0),
			Vector3(pw, 2.0, 0.78), "building", theta, false)
		_box("%s_ped_cap" % nm, at, Vector3(0.0, h + 2.62, 0.04),
			Vector3(pw + 0.3, 0.22, 1.0), "far_shade", theta, false)
		var signs := ["red", "blue", "yellow", "canvas_alt"]
		_box("%s_ped_sign" % nm, at, Vector3(0.0, h + 1.6, 0.44),
			Vector3(pw * 0.66, 1.05, 0.14), signs[idx % signs.size()], theta, false)


## What stands on the roof. Sparse on purpose — every run having something is a
## skyline, and a park's roofline is mostly flat with three or four things on it.
##
## Set back from the face so the parapet crops their feet, which is the same rule
## the skyline's coaster and tower are placed by: a silhouette whose base you can
## see is a model, and one you cannot is a building with more behind it.
func _roofline(tag: String, base: Vector3, theta: float, idx: int,
		length: float, thick: float, h: float) -> void:
	var pick := int(_hash01(idx, 7, 41) * 6.0)
	var back := -minf(thick * 0.5 - 1.4, 3.0)
	var x := lerpf(-length * 0.28, length * 0.28, _hash01(idx, 3, 53))
	match pick:
		0:
			# A cupola, which is the one that says park rather than high street.
			_box("%s_cup_base" % tag, base, Vector3(x, h + 1.1, back),
				Vector3(3.2, 1.0, 3.2), "building", theta, false)
			_cyl("%s_cup_drum" % tag, base, Vector3(x, h + 2.5, back), 1.15, 2.0,
				"white", theta, 10, false)
			_cyl("%s_cup_roof" % tag, base, Vector3(x, h + 3.75, back), 1.5, 0.5,
				"accent", theta, 10, false)
			_box("%s_cup_mast" % tag, base, Vector3(x, h + 4.85, back),
				Vector3(0.16, 1.8, 0.16), "far_shade", theta, false)
		1:
			# Water tank. Every park of this vintage has one and it is the
			# cheapest thing on this list that reads as machinery.
			for i in 4:
				var lx := x + (-1.0 if i < 2 else 1.0) * 1.15
				var lz := back + (-1.0 if i % 2 == 0 else 1.0) * 1.15
				_box("%s_tank_leg_%d" % [tag, i], base, Vector3(lx, h + 1.2, lz),
					Vector3(0.2, 2.4, 0.2), "far_shade", theta, false)
			_cyl("%s_tank" % tag, base, Vector3(x, h + 3.7, back), 1.7, 3.2,
				"wood", theta, 12, false)
			_cyl("%s_tank_cap" % tag, base, Vector3(x, h + 5.45, back), 1.55, 0.4,
				"far_shade", theta, 12, false)
		2:
			# A roof sign, seen from the far side of the plaza and blank from the
			# back, because half of them are.
			for i in 2:
				var px := x + (-1.0 if i == 0 else 1.0) * 2.4
				_box("%s_sign_post_%d" % [tag, i], base, Vector3(px, h + 1.6, back),
					Vector3(0.22, 3.2, 0.22), "metal", theta, false)
			_box("%s_sign_panel" % tag, base, Vector3(x, h + 3.0, back + 0.1),
				Vector3(6.0, 2.2, 0.2), "white", theta, false)
			_box("%s_sign_face" % tag, base, Vector3(x, h + 3.0, back + 0.26),
				Vector3(4.6, 1.5, 0.12), "red", theta, false)
		3:
			# Vents, which is what most park rooftops actually have on them.
			for i in 3:
				var vx := x + (float(i) - 1.0) * 1.6
				_cyl("%s_vent_%d" % [tag, i], base, Vector3(vx, h + 0.9, back),
					0.34, 1.8, "metal", theta, 8, false)
				_cyl("%s_vent_%d_cap" % [tag, i], base, Vector3(vx, h + 1.9, back),
					0.46, 0.2, "far_shade", theta, 8, false)
		_:
			# Two in six get a flat roof, and they are what makes the other four
			# read as incidents rather than as a pattern.
			pass


## The west seam, at the arch.
##
## Two of these exist and they stand in the same nine metres of air: one in the
## plaza's scenes pointing west, one in the boardwalk's pointing east. Only one
## is ever mounted, so they cannot see each other, and neither can go in a scene
## both sections share — which is why `west_stair.tscn` lost its gates when it
## became one of those.
##
## The preload volumes are not symmetric, because the two approaches are not. On
## the plaza side the spoke is open ground and the volume sits out on it,
## seventeen metres short. On the boardwalk side the approach is the terrace,
## which is a dead end with a stair at one corner and an arch at the other, so
## stepping off the head of the flight is already a commitment to the walk east.
func _arch_seam(belongs: StringName, leads: StringName) -> void:
	var westward := belongs == &"plaza"
	var hold: Dictionary = Plan.ARCH_HOLD_WEST if westward else Plan.ARCH_HOLD_EAST
	var walk := Vector3(-1.0, 0.0, 0.0) if westward else Vector3(1.0, 0.0, 0.0)

	if westward:
		_gate_area("preload_%s" % leads, Plan.ARCH_PRELOAD_AT, Plan.ARCH_PRELOAD_SIZE,
			0, leads, belongs)
	else:
		_gate_area("preload_%s" % leads,
			Vector3(-52.0, 1.5, Plan.ARCH_AT.y), Vector3(9.0, 3.0, 7.0),
			0, leads, belongs)

	_gate_area("cross_%s" % leads, Plan.ARCH_SEAM_AT, Plan.ARCH_SEAM_SIZE,
		1, leads, belongs, hold["from"], hold["look"], walk, Plan.ARCH_HOLD_SECONDS)

	# Named for where the player has come *from*, and put down a stride past the
	# wall on the far side of it — never inside the crossing volume, or arriving
	# trips the gate that sent them and bounces them straight back.
	if westward:
		_marker("arrival_from_%s" % leads, Plan.ARCH_ARRIVE_EAST,
			Plan.ARCH_ARRIVE_EAST_YAW)
	else:
		_marker("arrival_from_%s" % leads, Plan.ARCH_ARRIVE_WEST,
			Plan.ARCH_ARRIVE_WEST_YAW)
