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
const EAST_CASCADE_PATH := "res://scenes/world/east_cascade.tscn"
## How far east the terraces' massing copy of the plaza stands from the
## boardwalk's. See `_plaza_from_the_east`, which explains what it is for.
##
## **It separates the two copies from each other and nothing else, and it took a
## run of false starts to establish that it cannot do more.** The obvious reading
## is that it is also what keeps a massing box off `plaza_frontage.tscn`, which
## is mounted alongside both — and that is not a job an offset can do at any
## value. Every frontage face sits at a wall's inner face plus some multiple of
## 5mm, and the seam ring's own swing is 5.25mm, *wider than that pitch*: for any
## nudge there is a frontage plane the ring can walk onto. Raising this from 6mm
## to 37mm to clear the ring duly moved one 15m² pair off `efar_perim_w_north`
## and put a 2.7m² one onto `efar_perim_n_far_east`, sixty metres away.
##
## What actually carries that separation is `_mass_thinned`, which moves every
## far run's inner face five and a half metres back into the wall. This is left
## at six millimetres because the only planes it still has to keep apart are the
## two copies' own, and they are identical shapes in scenes that are never
## mounted together anyway — the pair is real arithmetic about an impossible
## frame, and the report is what it is being kept quiet for.
const EAST_FAR_NUDGE := 0.006
const TERRACES_FAR_PATH := "res://scenes/world/terraces_far.tscn"
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


## Set when a material came out wrong. `_save` refuses to write anything once it
## is up — see there for why `quit()` alone is not enough.
var _fatal := false


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
	_cascade(Plan.CASCADE_WEST)
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

	# The east cascade: the same monument as `west_stair`, at the other site.
	#
	# **Appended at the very end, and that is not where it reads best.** It
	# belongs next to the west cascade, twenty lines up, where somebody looking
	# for it would find it. It cannot go there: `_begin_scene` hands each scene a
	# seam seed five on from the last, so a scene inserted anywhere but the end
	# shifts the displacement of every scene after it — and the ordinal wraps at
	# 21, so a shift of ten is not a shift of nothing. Inserting this beside its
	# twin would re-plane shapes in a dozen files nobody edited. See the note on
	# `paving` above, which is here for the same reason and says so.
	_root = Node3D.new()
	_root.name = "east_cascade"
	_begin_scene()
	_cascade(Plan.CASCADE_EAST)
	# After the monument and not before it: this scene's shapes take their seam
	# displacement in build order, so a slab laid first would move all 460 of the
	# cascade's nodes one ordinal on.
	_east_court()
	# And the hill the monument is cut into, after the court for the same reason
	# the court is after the monument: this scene's shapes take their seam
	# displacement in build order, and anything laid ahead of the cascade moves
	# all 460 of its nodes one ordinal on.
	_east_hill()
	# And the climb cut into it. Last of all: this is the final scene written, so
	# nothing downstream can have its seam ordinal moved by what this emits.
	_east_climb()
	_climb_rails()
	# The ground itself, over the mass the two above laid. After both, because it
	# is sampled from where the cut ends up rather than the other way round —
	# `_east_inner` reads the reaches and `_climb_bank_d` reads the floor, so the
	# skin is a consequence of the climb and not a thing the climb is fitted to.
	# It is also two nodes against their several hundred, which makes it the
	# cheapest possible place to add to an ordinal-sensitive build order.
	_east_earth(-1.0, "n")
	_east_earth(1.0, "s")
	# The way back, which belongs to the section on this side of the wall.
	_east_seam(&"terraces", &"plaza")
	# The shoulders, after everything: two meshes and a handful of walls at the
	# end of the build, so nothing already in this scene moves an ordinal.
	_east_shoulder(-1.0, "n")
	_east_shoulder(1.0, "s")
	# No toe seal any more: the ground meshes run to `EARTH_TO_X`, past where
	# the rim's face climbs above them, so their open east edges hang inside
	# the ridge's body and the rim itself is the seal — see `EARTH_TO_X`.
	# The crest terraces last: the walled court that used to sit mid-climb,
	# moved to the head when the landings narrowed to pauses.
	_climb_crest_courts()
	# And the head landing, appended after everything for the ordinal reason:
	# the terrace `CLIMB_HEAD_TO_X` has named since the climb doubled, drawn at
	# last — see `_east_head_landing`.
	_east_head_landing()
	if not _save(_root, EAST_CASCADE_PATH):
		return

	# The plaza as massing, for the section that has just deleted it. Its own
	# scene rather than a pass inside `east_cascade.tscn`, because that file is
	# mounted by the plaza too and the plaza does not want a ghost of itself
	# standing inside it. Written last: nothing comes after, so nothing downstream
	# can have its seam ordinal moved by what this emits.
	_root = Node3D.new()
	_root.name = "terraces_far"
	_begin_scene()
	_plaza_from_the_east()
	if not _save(_root, TERRACES_FAR_PATH):
		return

	quit()


func _save(node: Node3D, path: String) -> bool:
	# Nothing is written after a material lost a uniform. `quit()` only asks the
	# main loop to stop, and the whole park is built inside one call before the
	# loop gets a turn — so on its own it reports the fault and then writes every
	# scene anyway, which is the same silence this check exists to break.
	if _fatal:
		return false

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

## The ridge. See `RIM_SIZE` for why this one is not sized like the others.
const RIM_ALBEDO_PATH := "res://assets/textures/rim_albedo.res"
const RIM_NORMAL_PATH := "res://assets/textures/rim_normal.res"

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

## The rim's own surface, and the one texture in the park sized by *viewing
## distance* rather than by the thing it depicts.
##
## Every other tile here is measured against an object with a real size — a
## 200x100 paver, a 140mm board, a 12mm chip — and the tile is then made fine
## enough to resolve it. That reasoning gives the wrong answer for a landform.
## The rim is 150 to 230m out, and the park's own 3m ground tile subtends about
## twenty pixels at that range: every feature in it lands under the first mip or
## two, the whole tile averages to its own mean, and the surface comes back
## exactly as flat as it started. A texture that mips away is not a texture, it
## is a slower way of writing the albedo down.
##
## So the tile is 48m and the structure inside it is 3 to 12m — features that
## still span two or three hundred pixels from the plaza, which is what makes
## them survive minification and shade. That is coarse enough to be nothing at
## all up close, and nothing ever is: the ridge has no collision, the shelf that
## would take a player near the toe is not built, and the cascade stops them at
## x 70. **Anything that puts a camera near this face wants a second, finer
## layer** — the ridge has no detail of its own at arm's length.
##
## 512px over 48m is 9.4cm to the pixel. Kept at 512 rather than dropped, because
## the cost of a tile is its compressed size and a field this smooth compresses
## to almost nothing.
const RIM_SIZE := 512
const RIM_METRES := 48.0

## What the albedo tile averages to, and the reason `mats["rim"]` is not built
## in the `defs` table with the other flat colours.
##
## `_ground_material` multiplies its tint by the texture, so a tile with a mean
## of 0.85 darkens whatever colour it is handed by 15%. The rim's colour is
## argued for in the palette — bluer rather than paler, sitting between `far` and
## `far_shade` so the crest shows against the sky — and none of that argument is
## about this texture. So the tint is the palette colour *divided* by the mean
## and the ridge's average value is unchanged: this pass adds variation to the
## surface and does not repaint it.
##
## The swing is deliberately small — ±17% about the mean, so nothing in it clips
## and the tile needs no headroom. A hillside at this range wants relief that
## shades, not albedo that patches; the normal map is what does the work here and
## the albedo only keeps it company. Pushed harder it reads as snow.
const RIM_TEX_MEAN := 0.85

## **It was a haze colour, and the east stopped being far away.**
##
## This was `Color(0.56, 0.60, 0.69)` until 2026-08-21 — a blue-grey sitting
## between `far` and `far_shade`, argued for at the 150 to 230 metres the ridge
## stands at *from inside the plaza*, with the hue rather than the value doing
## the distance so the crest would still show over the east roofline.
##
## Every word of that was sound and it was answering one viewing distance out of
## two. `RIM_FOOT_X` is 120, which is `TERRACE_TWO_TO_X` — the toe of the ridge
## begins exactly where the east hill's own ground stops, **ten metres from the
## head of the climb** and forty-odd from the belvedere. A player who walks up
## the basin staircase ends up nearer to this than they ever are to the plaza's
## own perimeter wall, looking at full aerial haze from arm's reach. Measured off
## `hill_j_shelf_east`, it rendered at 211/216/227 against a sky of 119/170/213:
## lighter than the sky it was supposed to read against, which is why it came
## back as a snowfield rather than as land, and why the east looked like six
## unrelated materials in one frame.
##
## There is no fog anywhere in this project — `daylight.gd` drives sun, sky and
## ambient and nothing else — so distance is *painted*, and a painted distance
## can only ever be right for one standpoint. This is now a land colour: an
## olive-grey drier and greyer than `planting`, which separates from the hill in
## front of it on saturation the way a real ridge does, rather than on value.
##
## **What it costs is the plaza's east skyline**, and that is a real trade rather
## than a free win. From the fountain the ridge is now a dark olive band instead
## of a pale one. The old entry's fear was a pale ridge lost against a pale
## horizon; darker is *more* legible against that sky, not less, so the plan's
## argument for the crest height still holds — but the composition is different
## and it was checked from both ends before this was changed.
const RIM_TINT := Color(0.43, 0.45, 0.36)

## How hard the relief is baked into the normal *map*, which is not the
## material's `normal_scale` and must not be handed to it — `_normal_from` takes
## a gradient multiplier in height-units-per-pixel and `normal_scale` takes a
## small runtime factor around one. The material gets 1.0; all of the slope is in
## the tile.
##
## Much larger than the ground tiles' 0.6–2.0, and it is a unit difference rather
## than a taste one. `_normal_from` works on the height field's gradient *per
## pixel*, and the field is 0..1 across the tile whatever the tile measures — so
## the same numbers over 48m instead of 3m describe a slope sixteen times
## gentler.
##
## **Set by looking, after the ratio argument alone came out too low.** Sixteen
## times the ground's figure is about 14, and 14 renders as a faint cloud on the
## face rather than as ground: the estimate had counted the tile ratio and not
## the *feature* ratio, and a 12m swell spread over 128 pixels has a far shallower
## per-pixel gradient than a 5cm one over eight. 40 lands the coarse features
## somewhere near thirty degrees off the face's own normal, which is a gully. It
## can go higher before it reads as noise — at 3 to 12m the features are far too
## broad to sparkle — but past here the ridge starts to look eroded rather than
## grassed.
const RIM_RELIEF := 40.0


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

## Cool, and the only cool light in the park. It reads as *architecture* lit on
## purpose against a park lit in tungsten — warm everywhere else, cold on the
## things worth walking to. Same colour the pavilion takes at the pier head.
##
## **It came off the cascade's facade and the saturation is the fossil of that.**
## It used to run 40m of coping down each wing plus the landing's own 7m, which
## made it far and away the largest emissive surface in the park and seen flat-on
## from the head of the flight; at (0.60, 0.82, 1.0) the capture came back with
## two white-hot slabs and no colour in them at all, because emission clips toward
## white as it brightens. Hence a blue deep enough to survive its own brightness.
## The string course is gone — a second outline parallel to the chevron's own,
## see `_cascade_landing` — so nothing that large wears this any more and the
## value is now conservative rather than load-bearing. Left as it is: the pavilion
## and the apron edge are the remaining callers, the deep blue suits both, and
## re-tuning a colour because its worst case retired is how a palette drifts.
const TRIM_EMIT := Color(0.24, 0.55, 1.0)


func _build_textures() -> void:
	DirAccess.make_dir_recursive_absolute(TEX_DIR)
	_brick_texture()
	_asphalt_texture()
	_plank_texture()
	_rim_texture()


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


## The rim's hillside: mottling and coarse relief, and nothing that has a
## direction.
##
## **Isotropic on purpose, and the reason is the failure it is being laid over.**
## The obvious thing to draw on a ridge is gullies running down the slope, and it
## is the one thing this must not do. The face is 34 slabs each tilted to its own
## band angle, so it already reads as a fan of flat facets — a folded screen
## rather than a hill — and a pattern of parallel lines running down every facet
## is what a folded screen is made of. Blotches break the plane; stripes would
## agree with the fold.
##
## It could not carry a direction reliably anyway. The material is world-space
## triplanar, which is not a preference here but the only option: a band is a
## slab in its own rotated frame and there are 34 of them overlapping, so surface
## UVs would give every band its own tiling rate and put a visible break at every
## one of the 33 seams. Projected from world position the pattern runs straight
## through the seams and the ridge is one surface. What triplanar costs is
## control of the in-plane direction — a face this steep is read mostly off the
## x-facing and the top-down projections at once, and their axes disagree.
##
## The albedo is derived from the relief rather than rolled beside it, for the
## reason the brick is: a gully that is dark in the shading and pale in the
## texture is two surfaces disagreeing about where it is. Partially, though, not
## wholly — the broad patch layer is independent, because what actually varies
## the colour of a hillside is scrub and bare ground, and that does not follow the
## contours.
func _rim_texture() -> void:
	var n := RIM_SIZE
	var height := PackedFloat32Array()
	height.resize(n * n)
	var albedo := Image.create_empty(n, n, true, Image.FORMAT_RGB8)
	for py in n:
		for px in n:
			var u := float(px) / float(n)
			var v := float(py) / float(n)
			# 12m, 6m and 3m over the 48m tile. Nothing finer: the asphalt's
			# lesson is that grain below the scale the surface is actually seen
			# at is white noise to the derivative — it will not compress, no mip
			# level means anything, and it glitters. Down here that threshold is
			# not a centimetre, it is metres, because the nearest standpoint is
			# a hundred and fifty of them away.
			var relief := 0.55 * _vnoise(u, v, 4, 61) \
				+ 0.30 * _vnoise(u, v, 8, 63) \
				+ 0.15 * _vnoise(u, v, 16, 65)
			height[py * n + px] = relief
			# Scrub against bare ground, at 16m. Independent of the relief, so
			# the colour patches cross the spurs instead of tracing them.
			var patch := _vnoise(u, v, 3, 67)
			# The only fine layer, and it is there for the mips rather than for
			# the first frame: 2m features average out honestly into the coarse
			# ones instead of leaving the tile perfectly smooth between them.
			var fine := _vnoise(u, v, 24, 69)
			# Zero-mean by construction, so the tile averages exactly
			# `RIM_TEX_MEAN` and `RIM_TINT` can be divided by it. Amplitudes sum
			# to 0.34, so the tile spans 0.70 to 1.00 and never clips.
			var swing := 0.20 * (relief - 0.5) \
				+ 0.09 * (patch - 0.5) \
				+ 0.05 * (fine - 0.5)
			var w: float = clampf(RIM_TEX_MEAN * (1.0 + swing), 0.0, 1.0)
			albedo.set_pixel(px, py, Color(w, w, w))
	albedo.generate_mipmaps()

	_save_texture(albedo, RIM_ALBEDO_PATH, false)
	_save_texture(_normal_from(height, n, RIM_RELIEF), RIM_NORMAL_PATH, true)


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
		# **The cascade's facade, and the one painted wall in the park.**
		#
		# Everything else that holds a silhouette here is `building`, which is
		# the perimeter's grey — so the monument was the same colour as the
		# hundred and twenty metres of wall it is nowhere near, and the only
		# thing separating it from the bluff behind was that the bluff is also
		# grey. A park paints the thing it wants you to look at.
		#
		# Blue for two reasons beyond taste. It is the one hue in the palette
		# nothing else down here is using — the deck is `plank`, the court is
		# asphalt, the treads are `accent` salmon and the planting is the only
		# green — so the facade cannot be confused with anything it stands
		# against. And it is what makes the night work: the monument is lit
		# `moon` on the stone and `amber` on the route, and amber on blue goes
		# to mud while moon on blue goes deeper. The cold/warm split was already
		# there; the paint is what gives it something to bite on.
		#
		# Held back from the `blue` in this same table, which is signage: 0.27,
		# 0.50, 0.72 at 0.7 roughness is enamel on a board 2m across, and a
		# 24m-wide wall in it reads as a bouncy castle. This is that hue with
		# the chroma pulled toward the park's dustiness and masonry roughness,
		# which is what painted stucco twenty summers old actually looks like.
		"cascade_face": [Color(0.31, 0.46, 0.62), 0.88, 0.0],
		# **The back of the niche**, and only the back: the same wall carried into
		# the recess, at a different value. Which way that value goes was settled
		# by building both and looking, and the reasoning that went in first was
		# wrong twice.
		#
		# **The arch head's corbels are `cascade_face`, not this.** They wore this
		# for about an hour and it was the wrong reading of what they are: the
		# stepped head is the *frame* of the opening rather than something inside
		# it, cut from the same wall as the reveals either side — which have been
		# `cascade_face` since the facade was painted, because they are the flanks
		# of `landing_face`. Putting the corbels in the darker blue split the frame
		# into a lighter surround and a darker head, and an arch whose head is a
		# different colour from its jambs is two things rather than one. The value
		# change belongs at the back plane, where the recess actually begins.
		#
		# The argument for going *lighter* was that a 1.5m recess in a west-facing
		# wall is in its own shadow for most of the day, that shadow is worth
		# about half the albedo, and a dark blue in there would land on near-black
		# and cost the arch its head. Built at 0.50/0.66/0.79, none of that
		# happened. The stepped head reads *better* dark, because what draws a
		# corbel is the skylight on its upward face, and that face is bright
		# against a dark reveal and invisible against a light one. And the recess
		# stopped being a recess: at that value the niche reads as a patch of
		# paler paint on the facade rather than as a hole in it, which is the one
		# thing the depth was bought for.
		#
		# After dark it was worse and in the opposite direction. `niche_glow` is
		# an amber lamp tucked behind the basin, and a light blue under it goes to
		# cream — the blue disappears entirely and the whole opening blows out to
		# a bright blob. Dark, the same lamp reads as warm light *inside* a blue
		# box, which is the "an arch is a hole and the dramatic version of a hole
		# is light coming out of it" that `_cascade_lights` claims to be doing and
		# could not do against a pale back.
		#
		# The fountain in front separates on **hue** rather than value either way
		# — `fount_stone` is a warm pale limestone against a cool wall, which is
		# the argument the whole monument's lighting makes. Dark simply gives it
		# more of both.
		"niche_face": [Color(0.21, 0.32, 0.46), 0.88, 0.0],
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

	# The rim, and the one textured surface that is not ground. It is here rather
	# than in `defs` because it needs the same treatment the ground does and for
	# the same reason: it is a single continuous surface built as many separate
	# pieces, so the pattern has to come from the world and not from each piece's
	# own UVs. See `_rim_texture`.
	#
	# The colour is unchanged and the arithmetic is what keeps it that way.
	# `RIM_TINT` is further back in the haze than anything the west tableau wears
	# — `far` is 87m away and this is 150 to 230 — and bluer rather than paler,
	# which is a choice against the physics: aerial perspective washes a distant
	# ridge toward the sky, and a pale ridge against a pale horizon is a ridge
	# nobody can see. The plan's whole argument for the crest height is that it
	# *shows* over the east roofline, so the value sits between `far` and
	# `far_shade` and the hue does the distance. Dividing by the tile's mean is
	# what stops a texture pass quietly moving it.
	mats["rim"] = _ground_material(
		Color(RIM_TINT.r / RIM_TEX_MEAN, RIM_TINT.g / RIM_TEX_MEAN,
			RIM_TINT.b / RIM_TEX_MEAN),
		RIM_ALBEDO_PATH, RIM_NORMAL_PATH, RIM_METRES, 1.0, 0.97)

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

	# **The cascade's fountain is terracotta and the plaza's is not**, which is
	# why these are two more materials rather than a change to the two above.
	# `fount_stone` is shared, and it was chosen against a specific problem: the
	# plaza's fountain stands in the middle of a hundred and twenty metres of
	# `building` grey, so it is warm limestone to get off that grey by a measured
	# margin. Recolour it here and the park's centrepiece moves with it.
	#
	# The niche's fountain has the opposite problem. It stands in a recess painted
	# `niche_face`, against a facade painted `cascade_face`, on an `accent` apron
	# — nothing near it is grey any more, and a warm pale limestone against a cool
	# blue separates on hue but barely on value, so from the court it reads as a
	# pale smudge in a blue hole. Clay is the same hue family as the apron it
	# stands on and the pots either side of it, and it is the complement of the
	# wall behind it.
	#
	# Redder and darker than `accent`, deliberately: the apron under it is that
	# salmon, and a fountain the colour of its own floor is a fountain with no
	# bottom edge.
	mats["niche_stone"] = _plain(Color(0.68, 0.38, 0.28), 0.88, 0.0)
	# The wetted courses, standing in the same relation to `niche_stone` that
	# `fount_wet` stands to `fount_stone` — darker and much less rough, because
	# that is what water does to masonry. A terracotta fountain with grey wet
	# stone on it is two materials pretending to be one object.
	mats["niche_wet"] = _plain(Color(0.44, 0.26, 0.21), 0.35, 0.0)
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

	# **Twelve lamps under the twelve jets**, drawn by the water rather than laid
	# on it — see `lamp_ring` in the shader, and the cascade's niche for the three
	# builds it took to learn that a patch on a surface is a second surface.
	#
	# Under the jets rather than anywhere else because that is where a fountain
	# puts them and because of what it does to the jets: `water_jet` carries its
	# own `glow`, so a jet is already bright, and a jet rising out of unlit water
	# is a bright rope with nothing at the bottom of it. Lighting the water it
	# comes out of is what roots it.
	#
	# 0.55m of halo on a 6.5m ring, so no two of the twelve reach each other and
	# the pool reads as twelve lamps rather than as a lit ring.
	mats["water_pool"] = _shader_material(pool, {
		"tint": Color(0.10, 0.24, 0.28),
		"centre": Vector3(Plan.FOUNTAIN_AT.x, 0.0, Plan.FOUNTAIN_AT.y),
		"ring_scale": 1.0,
		"chop": 1.0,
		"rough": 0.06,
		"lamp_ring": Vector4(Plan.FOUNTAIN_JET_R, 12.0, 0.55, 1.0),
		# A froth patch where each of the lower basin's falls lands, and the count
		# is **negative** because `_veil` spaces them at `i` steps while the jets
		# are at `i + 0.5`. See the shader.
		"foam_ring": Vector4(LB_VEIL_R, -float(LB_VEIL_N), 0.52, 1.0),
		# **The glow, and this is the restrained end of it.** The plaza's fountain
		# is a civic one in a room with 1,066 nodes of lit frontage round it, so
		# it wants to be the brightest thing in the square rather than the only
		# one — at 1.6 it reads as a lit fountain and at 3 it reads as a portal.
		# The grotto in the cascade's niche takes nearly twice this, because it
		# is a dark alcove with one lamp in it and nothing to compete with.
		"night_glow": 1.6,
	})
	# The basins are 8m and 4m across against the pool's 17, so they take the
	# rings four and eight times as tight. At the pool's wavelength a basin has
	# one and a half waves on it, which does not read as water at all — it reads
	# as a dent.
	#
	# **And neither basin gets a landing ring, which was tried and measured.** The
	# upper lip sheds ten falls onto the lower basin at radius 2.03, so a froth
	# ring there is the obvious companion to the pool's — it was built, and then
	# it was looked at. The lower basin's water is at 3.30 and its rim stands 5cm
	# proud of it; the eye is at 1.60. Every sightline that reaches the height of
	# that surface is already travelling upward and keeps going, so the surface is
	# not merely hard to see from the plaza floor, it cannot be seen from anywhere
	# below it — and there is nowhere in the park above it to stand. Rendered from
	# a camera at 6.6m, where it *is* visible, 0.70 froth against `ring_scale` 4.5
	# was still barely a haze.
	#
	# So the falls between the basins are drawn and their landing is not, which is
	# the honest split: the veils hang in plain sight from the floor and the water
	# they hit is over the horizon of the rim they are behind.
	mats["water_basin"] = _shader_material(pool, {
		"tint": Color(0.13, 0.28, 0.31),
		"centre": Vector3(Plan.FOUNTAIN_AT.x, 0.0, Plan.FOUNTAIN_AT.y),
		"ring_scale": 4.5,
		"chop": 3.0,
		"rough": 0.05,
		# Brighter than the pool, because the basins are what the falls come off
		# and a lit sheet leaving an unlit lip is a rope with nothing at the top
		# of it — the same argument the pool's own lamps were put in for, at the
		# other end of the water.
		"night_glow": 2.1,
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
	# --- the wall fountain in the cascade's niche ---
	#
	# **Its own materials, and the reason is one uniform.** `centre` is a world
	# position: the pool shader radiates its rings from it, so a surface wearing
	# `water_basin` sixty metres west of the plaza gets rings that have long
	# since flattened into parallel stripes travelling in one direction. It would
	# have read as brushed metal, and it would have read that way in a screenshot
	# without looking wrong — which is the same blind spot the flow direction sat
	# in. Water is centred on the thing it is in.
	#
	# The trough is 1.7m by 2.0 against the plaza pool's 17, so the rings go
	# tighter again than the basins': at the basin's 4.5 there is barely one wave
	# on it.
	#
	# **Four per site, and that is what the loop is for.** There are two cascades
	# and the argument above is exactly the argument against sharing one set
	# between them: the east's niche stands 128m east of the west's and six metres
	# above it, so a shared `centre` would hand it the same flattened stripes this
	# whole block exists to avoid, and a shared fade band would sit six metres over
	# the spout it is meant to dissolve.
	#
	# **The lamps made that argument twice over.** `lamp_*` and `foam_*` are world
	# positions packed into a `Plane` as (x, z, radius, 1) — so they are the same
	# class of uniform as `centre`, and sharing a material between the two
	# *surfaces* would have put the trough's pair under the basin. Sharing one
	# between the two *sites* puts the west's pair 128m from the water they are
	# meant to be lighting, which is the same mistake at ninety times the distance
	# and the one nothing would have printed an error about.
	#
	# Everything else below is shape and is shared: every tint, ring scale, chop
	# and offset is identical at both sites, and the only things read out of `cs`
	# are the three coordinates the site is.
	for cs in [Plan.CASCADE_WEST, Plan.CASCADE_EAST]:
		var ct: String = cs["tag"]
		var niche_c := Vector3(cs["wall_x"], 0.0, cs["axis_z"])
		# The positions are the site's own, plus the same offsets
		# `_cascade_niche` builds the lamps at, and that duplication is the one
		# thing here worth watching: a lamp that moves in the geometry and not in
		# the shader goes dark with no error anywhere. They are written next to
		# each other for that reason.
		var nx: float = float(cs["wall_x"]) - Plan.CASCADE_WALL_THICK * 0.5
		var nz: float = cs["axis_z"]
		mats["water_niche_%s" % ct] = _shader_material(pool, {
			"tint": Color(0.12, 0.27, 0.30),
			"centre": niche_c,
			"ring_scale": 11.0,
			"chop": 6.0,
			"rough": 0.05,
			"lamp_a": Vector4(nx + 0.52, nz - 0.34, 0.30, 1.0),
			"lamp_b": Vector4(nx + 0.52, nz + 0.34, 0.30, 1.0),
			# And the two places the basin's falls land.
			"foam_a": Vector4(nx + 0.90, nz - 0.62, 0.22, 1.0),
			"foam_b": Vector4(nx + 0.90, nz + 0.62, 0.22, 1.0),
			# A grotto rather than a civic fountain, so nearly twice the plaza's.
			# It is a 1.5m recess with one amber omni in it and a dark blue plate
			# behind — there is nothing else in the frame for it to be brighter
			# than, and the whole reason the niche was deepened was to make the
			# opening read as occupied.
			"night_glow": 2.8,
		})
		# The basin: one lamp, and a tighter ring scale because it is 0.44m by
		# 1.28 against the trough's 1.48 by 1.82.
		mats["water_niche_%s_bowl" % ct] = _shader_material(pool, {
			"tint": Color(0.12, 0.27, 0.30),
			"centre": niche_c,
			"ring_scale": 26.0,
			"chop": 14.0,
			"rough": 0.05,
			"lamp_a": Vector4(nx + 1.30, nz, 0.17, 1.0),
			# Where the spout lands in it.
			"foam_a": Vector4(nx + 1.10, nz, 0.15, 1.0),
			# The brightest water in the park. It is the highest of the three
			# stages, it is the one the spout lands in, and it is what the two
			# falls leave — so it is where the eye goes and the only one small
			# enough that the whole surface is a highlight.
			"night_glow": 3.2,
		})
		# Two falls and not one, because `fade_from`/`fade_to` are **absolute
		# world Y** and the two drops are at different heights. The plaza's pair
		# got away with a fountain standing on y=0; the west niche is 6m under it
		# and the east's 6m over it, so a fade copied off anybody else's numbers
		# puts the whole band clear of the water. Hence `nf`, which is the site's
		# own floor. Both streams are round and about 10cm through, so `streaks`
		# is set to put roughly one rope on that width — 70 rather than the veils'
		# 64–80 across a 40cm slab, which is the same rope, not a coarser one.
		var nf: float = cs["floor_y"]
		mats["water_niche_%s_spout" % ct] = _shader_material(fall, {
			"flow": 2.0, "streaks": 70.0, "grain": 3.2,
			"base_alpha": 0.34, "glow": 0.40,
			"fade_from": nf + 2.66, "fade_to": nf + 2.12,
		})
		mats["water_niche_%s_fall" % ct] = _shader_material(fall, {
			"flow": 2.3, "streaks": 70.0, "grain": 2.8,
			"base_alpha": 0.32, "glow": 0.34,
			"fade_from": nf + 1.76, "fade_to": nf + 0.86,
		})


	# The basin chain, and **one material pair per basin, which is the
	# architecture demanding it rather than laziness.** `water_pool`'s `centre` is
	# a world XZ and `water_fall`'s fade band is an absolute world Y; twelve bowls
	# two metres apart and half a metre down from each other share neither. One
	# shared pair would hand every bowl the rings of a centre twelve metres away,
	# which arrive as parallel stripes — the brushed-metal failure the pool
	# shader's own comment is about — and a fade band six metres off its water.
	#
	# The honest fix is an object-space variant so a repeated object can carry a
	# repeated material. That is shader work and this is not it; what this does is
	# pay the real cost visibly rather than share a material that cannot be
	# shared. Twenty-five materials, and every one of them is a place.
	var cax: float = Plan.ARCH_AT.y
	for i in Plan.BASIN_COUNT:
		var bx: float = Plan.CLIMB_FROM_X + Plan.BASIN_STEP * (float(i) + 0.5)
		# The channel line, and it must agree with `_climb_channel_y` to the
		# millimetre — these are the world-space centres and fade bands the
		# bowls' own shaders radiate from, and a band computed off a different
		# head constant is the six-metres-of-sunken-garden bug wearing water.
		var by: float = Plan.CLIMB_HEAD_Y \
			- (Plan.CLIMB_TO_X - bx) * (Plan.CLIMB_RISE / Plan.CLIMB_RUN)
		mats["basin_pool_%d" % i] = _shader_material(pool, {
			# Lifted from the trough family's 0.12 dark: the bowls are read from
			# the court at forty metres and the fountain at ninety, and a dark
			# disc at that range is a hole in the plinth. The collecting pool
			# below keeps the dark tint on purpose — it is the ground the
			# chain's value reads against.
			"tint": Color(0.17, 0.36, 0.38),
			"centre": Vector3(bx, by, cax),
			# A 1.5m bowl. 10 puts about two rings across the surface; the 24 it
			# wore first put six, and from play the whole chain read as coiled
			# rope — at this diameter the rings alias into a moiré spiral well
			# before they read as ripples. The trough family's 11 was always
			# the right neighbourhood.
			"ring_scale": 10.0,
			"chop": 7.0,
			"rough": 0.05,
			# One lamp at the bowl's own centre. `Vector4` and not `Plane`: a
			# Plane here serialises to null and the lamp is dark in the saved
			# scene while being correct in this process.
			"lamp_a": Vector4(bx, cax, 0.34, 1.0),
			# Where the spill off the bowl above enters, just inside the
			# upstream rim — `basin_%d_spill`'s own low end.
			"foam_a": Vector4(bx + 0.60, cax, 0.20, 1.0),
			# **Turquoise and luminous, and the tint is what does it.** `gc` runs
			# from `tint` toward `lamp_tint` over the lit patch, and `lamp_tint`
			# defaults to the fitting's own warm amber — so a bowl could be turned
			# up as far as it liked and only got brighter, not bluer. Raising the
			# glow without moving the tint is how you get a hot yellow puddle.
			#
			# `glow_body` carries most of the lift rather than `glow_lamp`,
			# because a lit *lamp* on a dark pool is a torch under water and a lit
			# *pool* is what the historic plates show — the whole surface reading
			# as the brightest thing on the hillside.
			"lamp_tint": Color(0.42, 1.0, 0.94),
			"foam_tint": Color(0.72, 1.0, 0.98),
			# **Weighted onto the moving terms, and that is the whole of "fairy
			# fountain but grounded".** `glow_body` is the one flat part; the
			# other two ride `lit` and `froth`, which move with the surface. Buy
			# the brightness with the flat term and you get a sheet of light lying
			# on water — the shader's own comment says so, and it is the same
			# mistake three builds of the submerged lamps made in geometry. Buy it
			# with the moving terms and the pool glows *and ripples*, which is the
			# only thing keeping it a fountain rather than a portal.
			"glow_body": 0.30,
			"glow_lamp": 2.4,
			"glow_froth": 2.8,
			"night_glow": 7.0,
		})
		# The fall arriving in this bowl, off the lip of the one above. Its band
		# is this bowl's own surface and the half-metre over it, so every one of
		# the twelve is a different absolute Y.
		# **White water, and it is a value decision measured at the court's own
		# distance.** At 0.36 alpha and a glassy teal the falls were honest
		# close up and nearly absent at forty metres — the grey rails carried
		# more contrast than the water, and the plate's ribbon is the opposite:
		# white lips against dark planting are the brightest thing on the hill.
		# Opacity and a near-white tint are what survive distance; glow is the
		# night half and only nudges.
		# Worn only by the spill ribbons since the standing tubes went. Denser
		# and more opaque than the monument's veils on purpose: a ribbon lies
		# on a slope over terracotta, so the shader's translucent gaps show
		# plinth through it, and at the old 2.9 grain the bands came back as a
		# zebra ramp. Fine grain and high alpha read as white water with
		# streaks in it; the night glow rides the same uniform it always did.
		mats["basin_fall_%d" % i] = _shader_material(fall, {
			"flow": 2.1, "streaks": 72.0, "grain": 5.5,
			"base_alpha": 0.78, "glow": 1.0,
			"tint": Color(0.86, 0.97, 0.95),
			"fade_from": by + Plan.BASIN_FALL, "fade_to": by,
		})
	# The collecting pool at the mouth, and the discharge into it.
	var pcx: float = (Plan.POOL_FROM_X + Plan.CLIMB_FROM_X) * 0.5
	mats["basin_pool_head"] = _shader_material(pool, {
		"tint": Color(0.11, 0.26, 0.30),
		"centre": Vector3(pcx, Plan.POOL_TOP_Y, cax),
		"ring_scale": 7.0,
		"chop": 5.0,
		"rough": 0.05,
		"foam_a": Vector4(Plan.CLIMB_FROM_X - 0.7, cax, 0.34, 1.0),
		"lamp_a": Vector4(pcx - 1.6, cax - 1.9, 0.42, 1.0),
		"lamp_b": Vector4(pcx - 1.6, cax + 1.9, 0.42, 1.0),
		"lamp_tint": Color(0.42, 1.0, 0.94),
		"foam_tint": Color(0.72, 1.0, 0.98),
		# A shade under the bowls': it is 4.5m by 8.4 against their 1.5, and equal
		# glow on unequal areas makes the big one the subject. The chain is the
		# subject and the pool is what it arrives in.
		"glow_body": 0.26,
		"glow_lamp": 2.1,
		"glow_froth": 2.6,
		"night_glow": 6.0,
	})
	mats["basin_fall_head"] = _shader_material(fall, {
		"flow": 2.4, "streaks": 54.0, "grain": 2.6,
		"base_alpha": 0.58, "glow": 1.0,
		"tint": Color(0.86, 0.97, 0.95),
		# `CLIMB_HEAD_Y`, the datum-fork family's fourth member: written off
		# `TERRACE_TWO_Y` this band sat six metres under the spill it fades,
		# fully faded before its own water started.
		"fade_from": Plan.CLIMB_HEAD_Y - (Plan.CLIMB_RUN - Plan.BASIN_STEP * 0.5) \
			* (Plan.CLIMB_RISE / Plan.CLIMB_RUN),
		"fade_to": Plan.POOL_TOP_Y,
	})


func _plain(albedo: Color, roughness: float, metallic: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = albedo
	m.roughness = roughness
	m.metallic = metallic
	return m


## One `ShaderMaterial` per uniform set. Shared by every part that takes it, so
## the packed scene carries one copy and not one per node.
##
## **A `vec4` uniform must be given a `Vector4`, never a `Plane`.** A `Plane` is
## what a `vec4` took in Godot *3*. In 4 the mismatch fails in the worst way
## available: `set_shader_parameter` takes the Plane, `get_shader_parameter`
## hands it straight back, and nothing anywhere says no — so the material is
## correct in this process and every check made inside the generator passes. It
## does not survive `ResourceSaver.save`: the parameter is written into the
## `.tscn` as `null`, `load()` returns null, and the uniform falls back to its
## declared default with no error at any point. The game reads the saved scene,
## so the value only ever exists in the one process that cannot use it.
##
## That is how every `vec4` in both water shaders — the cascades' submerged
## lamps, the froth patches, the plaza fountain's `lamp_ring` and `foam_ring` —
## was dark in every built scene on the day it was written: eight call sites, all
## of them `Plane`, with the generator running clean and printing its node counts
## the whole time. They were in the source, in the shader and in the commit
## message, and had never once been on screen. It is the same shape as
## `PortableCompressedTexture2D` dropping its own pixels: it fails by succeeding.
##
## **So the read-back below is not belt and braces, it is the only thing that
## catches a dropped uniform — and it has to go through `get_property_list`.**
## Asking the material for the parameter straight after setting it returns the
## Plane, because the value is sitting in the cache, wrong type and all. It is
## fetching the property list that discards it, because that is where the
## declared type is compared against what is held. `ResourceSaver` asks for the
## list and then for each value, in that order, so a check that skips the list is
## asking a question the saver never asks, and gets an answer the saved file will
## not agree with. Walk the list, exactly as the saver walks it — and grep the
## emitted scene for `= null` after adding a uniform.
func _shader_material(shader: Shader, params: Dictionary) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = shader
	for key in params:
		m.set_shader_parameter(key, params[key])

	for pi in m.get_property_list():
		var prop := String(pi["name"])
		if not prop.begins_with("shader_parameter/"):
			continue
		var key := prop.trim_prefix("shader_parameter/")
		# Only what this call asked for. Every other uniform reads back null by
		# design — that is what "left at the shader's default" looks like here.
		if params.has(key) and m.get(prop) == null:
			push_error(("gen_props: %s did not survive on %s. The shader declares "
				+ "it as %s and it was given a %s, so it would have saved as null "
				+ "and drawn as the shader's default.")
				% [key, shader.resource_path, type_string(pi["type"]),
					type_string(typeof(params[key]))])
			_fatal = true
			quit(1)
			return m
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
	# The east spoke, laid whole: ring, passage, forecourt, one unbroken surface
	# from the fountain to the foot of the climb.
	#
	# **The passage used to be left as brick**, on the theory that crossing onto
	# the plaza's own material gave the opening a floor of its own and made it
	# read deeper. That is the same theory the west tunnel was built on and it
	# lost there for the same reason: walked rather than looked at, the asphalt
	# reads as giving up at the wall. `_terrace_paving` carries the note.
	#
	# `EAST_GAP_WIDTH` for that range rather than the spoke's 8m, and the width
	# override exists for exactly this: the opening is 6m clear, so the extra
	# metre either side would be asphalt buried in a pier.
	#
	# **One height for the whole run, and it is the plaza's.** The last leg was
	# laid a centimetre lower because it ends out in the forecourt, which is
	# where `GROUND_SEAM` puts the court's brick — but the ground underfoot does
	# not change at the segment boundary. The plaza's own 104m slab runs to
	# `PLAZA_HALF`, five metres *past* the gate's outer face, so the low leg was
	# floating 2mm over plaza brick for its first stretch and the step between
	# the two heights would have landed at x=47, in the middle of continuous
	# ground — a hairline of brick across the walk at the one joint this whole
	# change is about. At one height the asphalt stands 12mm over the plaza and
	# 22mm over the court, and a quad with no side faces and no shadow shows
	# neither.
	_pave_run(&"spoke_east", PAVE_LIFT, "asphalt", 0, 2)
	_pave_run(&"spoke_east", PAVE_LIFT, "asphalt", 2, 1, Plan.EAST_GAP_WIDTH)
	_pave_run(&"spoke_east", PAVE_LIFT, "asphalt", 3, 1)


## The paving on the far side of the tunnel. **Into `plaza_paving.tscn` only,
## since 2026-08-19.**
##
## The terrace is on the boardwalk's side of the seam and the plaza's side of the
## wall, so both sections have to show it: the plaza sees it framed by the arch
## from as far back as the ring, and the boardwalk stands on it. That used to
## mean laying it twice, because `plaza_paving` was not mounted past the arch and
## `boardwalk` was not mounted before it.
##
## The boardwalk mounts `plaza_paving.tscn` now — it is in that section's own
## list, with the frontage, the fountain, the props and the clock — so the second
## copy became two identical quads a quarter-millimetre apart underfoot. One
## description again, and it is the mounted one.
##
## Two stretches, and the second is the point. The west spoke's last segment runs
## out of the tunnel to the parapet, which is where the view is; the stair's first
## two run north to the head of the flight, which is where the player is actually
## going, and without asphalt on them the terrace was a bare brick balcony with
## nothing to say the way on was to the right. They stop at the head of the
## flight, because past that it is treads.
func _terrace_paving() -> void:
	# **Through the tunnel too, at the arch's own width.** The paving used to stop
	# at the piers and pick up on the far side, on the theory that crossing onto
	# the plaza's brick gave the tunnel a floor of its own and made it read deeper.
	# Walked rather than looked at, it read as the path giving up.
	#
	# Six metres rather than the spoke's eight, because the tunnel is 6m clear and
	# the extra would be a metre of asphalt buried in each pier — which is the
	# reason this needed a width override rather than widening the range.
	_pave_run(&"spoke_west", PAVE_LIFT, "asphalt", 2, 1, Plan.ARCH_WIDTH)
	_pave_run(&"spoke_west", PAVE_LIFT, "asphalt", 3, 1)
	_pave_run(&"west_stair", PAVE_LIFT, "asphalt", 0, 1)
	# **The fork.** The route splits at the landing and rejoins in the lane, so the
	# asphalt does too: across the landing out to each wing's head, then nothing
	# down the flights, then again at the foot running west to where the two meet.
	#
	# The flights themselves stay bare for the reason every flight in the park
	# does — a flat quad laid over treads either floats above them or cuts through
	# them, and on the north wing it would bury the ramp it is meant to mark. What
	# carries the route down is the deck's own material; what the asphalt does is
	# say where the fork is and where it closes.
	#
	# **The two ends are at different heads.** The fork is on the landing, which is
	# level with the bluff top, so it takes `PAVE_LIFT` like everything on the
	# plaza. The spur is in the court six metres below, and paving it at the same
	# lift hung two quads in mid-air over the boardwalk — which is what `PAVE_LIFT`
	# is: a lift above *the plaza's* ground, not above whatever ground a run
	# happens to cross.
	# **The landing is paved whole, not forked across.** Running a 3m quad from a
	# point on the axis out to each wing's head drew two thin diagonals splaying
	# from one spot — a snake's tongue laid over a fourteen-metre landing. A fork
	# drawn as two prongs from a point is a tongue; what makes a junction read is
	# the ground being continuous and the ways off it being obvious.
	#
	# So the asphalt arrives, covers the landing, and the two wings lead off its
	# outer corners. The fork is a fact about the route rather than a shape
	# painted on the floor.
	# **East to where the approach actually stops, not to the bluff face.**
	#
	# The slab used to run `CASCADE_WALL_X` to `CASCADE_TOP_X` inset 0.2 a side,
	# and `west_stair`'s quad ends at `CASCADE_TOP_X + 1.0` — the walkway is one
	# metre longer than the landing it arrives on. So the two missed each other
	# by 1.2m and the walk west came off the terrace onto a strip of bare brick
	# before the asphalt picked up again. On the ground that reads as the path
	# being broken, which is what it was.
	#
	# Read off the walkway rather than retyped, so the two stay met if the run's
	# end moves. Butted rather than overlapped, unlike the rule everywhere else
	# in this generator: that rule is about volumes a capsule can catch on, and
	# these are two flat quads with no collision between them.
	# **A quad like every other piece of paving, not a box.**
	#
	# It was a `_box`, which is a CSG solid with `cast_shadow` on — so a 2cm slab
	# lying on the ground drew a dark outline all the way round itself, which is
	# the one artefact `_pave_quad` exists to avoid and the reason every other
	# run in the park is a shadowless `PlaneMesh`. It also shaded differently
	# from the quad it butts against, so the joint with the approach showed as a
	# line across the path even once the two were touching.
	var head: float = Plan.WALKWAYS[&"west_stair"][1].x
	var back: float = Plan.CASCADE_WALL_X + 0.2
	_pave_quad("pave_landing",
		Vector3((head + back) * 0.5, PAVE_LIFT, Plan.CASCADE_AXIS_Z),
		Vector2(absf(head - back), Plan.LANDING_HALF_W * 2.0 - 0.4),
		0.0, "asphalt")
	for id in [&"west_wing_north", &"west_wing_south"]:
		_pave_run(id, SHORE_TOP + PAVE_LIFT, "asphalt", 4, 1)


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
## `width` overrides the run's own width for this range, which the tunnel needs
## and nothing else does: `spoke_west` is 8m and the arch is 6m clear, so paving
## the tunnel at the spoke's width buries a metre of asphalt in each pier.
func _pave_run(id: StringName, y: float, mat: String, first := 0,
		count := -1, width := 0.0) -> void:
	var run: Array = Plan.WALKWAYS[id]
	var w: float = width if width > 0.0 else Plan.WALKWAY_WIDTH.get(id, 6.0)
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


## Where each ring of falls hangs from, and how many falls are in it.
##
## Here rather than at the two `_veil` calls because the lower ring's froth needs
## the same two numbers: a landing ring is drawn at the radius the falls come off
## with one patch per fall. Typed twice they drift, and the failure is quiet —
## a ring of froth 20cm inside a ring of falls still looks like a ring of froth.
##
## The upper pair is here for symmetry rather than for a second reader. It is
## worth the two lines anyway: the next person to reach for a landing ring under
## the upper falls should find its radius already named, and the note in
## `_fountain_materials` saying why there isn't one.
const LB_VEIL_R := 4.03
const LB_VEIL_N := 16
const UB_VEIL_R := 2.03
const UB_VEIL_N := 10


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
	_veil("lb_veil", o, LB_VEIL_N, LB_VEIL_R, 3.16, 0.40, 0.07, "water_veil_lo")
	_veil("ub_veil", o, UB_VEIL_N, UB_VEIL_R, 5.33, 3.30, 0.06, "water_veil_hi")

	# Where the lower sixteen land is `foam_ring` on the pool's material, off
	# `LB_VEIL_R`/`LB_VEIL_N` so the froth cannot drift from the falls that make
	# it — not sixteen discs laid on the water. See the shader: froth is a patch
	# of water that is white and broken, not an object floating on one. The upper
	# ten land in the lower basin, which no eye in the park is high enough to see
	# into; `_fountain_materials` has the measurement.


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


## How far a film lying on water stands proud of it, and how thick it is.
##
## **Ten millimetres and thirteen, where the first build of the niche's lamps was
## thirty and forty.** A disc 4cm thick centred 2cm above an 18cm-deep trough
## stands 4.6cm out of it — its rim shows, it takes its own shading, and it reads
## as a puck lying on the water, which is what "they look like two light saucers"
## and then "why are they floating on top" were both about. Measured off the
## numbers rather than argued: the water's top face is at 0.83 and the lens
## spanned 0.826 to 0.876.
##
## It cannot be flush, because two faces at one depth z-fight and that is the one
## rule this generator enforces. It only has to clear `SEAM_STEP * SEAM_STEPS`,
## which is 5.25mm — every shape's displacement is inside that — so ten
## millimetres is comfortable at any distance and invisible at all of them.
const FILM_PROUD := 0.010
const FILM_THICK := 0.013


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


## `_foam_ring`, `_foam_patch` and `_water_film` were here and are gone, with the
## `FILM_PROUD`/`FILM_THICK` pair that tuned them. All three laid discs on a water
## surface — froth in the plaza's pool, the glow over a submerged lamp in the
## cascade's niche — and all of it is `water_pool.gdshader`'s job now: see
## `foam_a`/`foam_ring`/`lamp_ring` there. They are removed rather than left
## unused because the next person to want a patch on water should not find a
## helper that makes one out of geometry; that is the mistake, not the API.
##
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


## A sloped ribbon of water: `_flight_ramp`'s construction at a water sheet's
## thickness, with the top face on the line from `top_a` to `top_b`. Water
## weight — no collision, no shadow — which is why it does not simply call
## `_flight_ramp`. A thin sheet tilted is a face, not a tall box; the rotated
## -box rule is about the other case.
func _water_ramp(nm: String, top_a: Vector3, top_b: Vector3, width: float,
		mat: String) -> void:
	var span := top_b - top_a
	var horizontal := Vector2(span.x, span.z).length()
	var phi := atan2(-span.y, horizontal)
	var theta := PI * 0.5 if absf(span.x) >= absf(span.z) else 0.0
	var mid := (top_a + top_b) * 0.5
	var up := (Basis(Vector3.UP, theta) * Basis(Vector3.RIGHT, phi)).y
	_box(nm, mid - up * 0.035, Vector3.ZERO,
		Vector3(width, 0.07, span.length()), mat, theta, false, phi)
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

	# --- and from inside the water ---
	#
	# The six above stand *outside* the kerb at 1.05m and rake the tiers from the
	# plaza floor, which is floodlighting a monument. These are the other half and
	# they are a different job: down in the pool, under the waterline, throwing
	# light up the inside of the thing. It is what the plaza's fountain has never
	# had and the one place a fountain is allowed to be theatrical.
	#
	# **Submerged, and the water does not stop them.** `_uplight` builds a spot
	# with `shadow := false` and a shadowless light in Godot is occluded by
	# nothing at all — measured in the cascade's niche, where sinking the sources
	# under an opaque surface changed 0.77% of the frame. So these sit at the
	# pool floor where a real lens does. What contains them is range and cone,
	# never the water.
	#
	# Six, not twelve, and at every other jet: the shader's `lamp_ring` is what
	# makes all twelve read, and these are for what the light *lands* on — the
	# undersides of the two basins, which are stepped discs specifically so they
	# have something to catch it. Twelve spots would be twelve times the cost for
	# a second copy of the same wash.
	var jr := Plan.FOUNTAIN_JET_R
	for i in 6:
		var th := TAU * (float(i * 2) + 0.5) / 12.0
		var dir := Vector2(cos(th), sin(th))
		_uplight("fountain_pool_up_%d" % i,
			Vector3(c.x + dir.x * jr, Plan.FOUNTAIN_POOL_TOP - 0.16, c.y + dir.y * jr),
			Vector3(c.x + dir.x * jr * 0.30, 4.6, c.y + dir.y * jr * 0.30),
			"lamp", 2.0, 7.5, 46.0)

	# --- and the surface itself ---
	#
	# **The water was black and sad after dark, and none of the above was ever
	# going to fix it.** Six washes rake the *tiers* from outside the kerb and the
	# six spots above throw light *up* the inside — every fitting on this fountain
	# points at stone. Meanwhile the pool is `tint` 0.10/0.24/0.28 at roughness
	# 0.06: a dark mirror, and what a mirror shows at eleven at night is a dark
	# sky. Seventeen metres of it in the middle of the plaza.
	#
	# The shader's `lamp_ring` cannot rescue it either, because that term is
	# albedo and gloss rather than emission — deliberately, so it does not glow at
	# noon — which means it is only ever as bright as what falls on it. It needed
	# something to fall on it.
	#
	# A bead over each jet, just above the film, very short-ranged: this is what
	# makes the twelve lamps read as twelve lamps rather than as twelve slightly
	# paler patches. It is the same fitting the cascade's niche needed for exactly
	# the same reason, one fountain and sixty metres apart.
	for i in JET_COUNT:
		var th := TAU * (float(i) + 0.5) / float(JET_COUNT)
		_omni("fountain_bead_%02d" % i,
			Vector3(c.x + cos(th) * jr, Plan.FOUNTAIN_POOL_TOP + 0.05, c.y + sin(th) * jr),
			"lamp", 1.3, 2.4, LIGHT_FIXTURE)
	# And one broad soft one over the middle, which is the difference between a
	# lit ring on black water and a lit pool. Hung at the lower basin's underside
	# so it reads as the fountain's own light spilling down rather than as a lamp
	# standard nobody can see; wide and weak, because the drama is the ring and
	# this is only meant to stop the rest being a hole.
	# **Two of them, high and wide.** One at 1.7 over 11m did not touch it: the
	# pool is 17m across, so a single source at the middle falls off to nothing by
	# the kerb, and the tint is dark enough that "nothing" is black. A pair hung
	# at the two basins' undersides covers the whole disc and reads as the
	# fountain's own light spilling down it, which is where a real one comes from.
	_omni("fountain_pool_fill", Vector3(c.x, 2.60, c.y), "lamp", 2.6, 13.5,
		LIGHT_FIXTURE)
	_omni("fountain_pool_fill_hi", Vector3(c.x, 5.10, c.y), "lamp", 2.0, 12.0,
		LIGHT_FIXTURE)


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
## **In final coordinates, with the dilation off, and it was not until
## 2026-08-14c.**
##
## `Plan.PLAZA_CAFE` is where the terrace *is* — its doc says so in as many
## words, "moved out with everything else when the plaza grew". Running it
## through `plaza_out` on top of that moved it out a second time: radius 26.8
## became 40.8, which is four metres past the perimeter's inner faces, so every
## table, chair and umbrella on the terrace has been standing inside a shopfront.
##
## What made it survive is that it broke the *furniture* and nothing else.
## `gen_crowd.gd` reads the same constant and does not dilate it, so the guests
## sat at 26.8 and the walkability validator kept the corridor clear at 26.8 —
## both correct, both agreeing with the plan, and both disagreeing only with the
## one file that draws the thing. The visible symptom was seven guests sitting on
## thin air in the middle of the annulus with their chairs fourteen metres away
## inside a building, and it was reported by somebody walking past them.
##
## This is the exact hazard `_queue` calls out two functions down — the hut moved
## by *decision* rather than by the map, so its queue must not be mapped either.
## The terrace is the same case and did not get the same treatment.
func _cafe() -> void:
	_dilate_plaza = false
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
		# Told to the register by hand, for the same reason the bandstand's
		# benches are: nothing here is pushed, so `_plaza_out` records nothing,
		# and the tree scatter would otherwise be free to grow one through the
		# middle of the terrace. A table and its two chairs is 2.2m across.
		_note_stood(at, 2.2)
	_dilate_plaza = true


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
const COASTER_EMBED := 0.5

func _wooden_coaster(origin: Vector3, heading: float, mat: String, vscale := 1.0) -> void:
	var profile := [3.0, 9.0, 15.0, 21.0, 26.0, 27.0, 9.0, 19.0, 8.0, 15.5, 7.0, 12.0, 6.5, 9.0, 5.0]
	var step := 7.0
	var dir := Basis(Vector3.UP, heading) * Vector3.FORWARD
	var prev := Vector3.ZERO
	for i in profile.size():
		var foot: Vector3 = origin + dir * (i * step)
		var h: float = profile[i] * vscale
		# Footed *into* the ground rather than onto it, which is both what a
		# coaster's footings do and the only thing that keeps these fifteen
		# columns off the underside of every building standing on the same shore.
		# The seam displacement only guarantees a gap between shapes assembled
		# near each other in build order — it wraps at 21 — and a column bottomed
		# at exactly SHORE_TOP is a shape that overlaps something two hundred
		# nodes away. Growing the wheel by nine nodes was enough to roll
		# `coaster_col_0`'s underside onto `front_arcade`'s, eighty metres from
		# the edit and in a scene nobody had otherwise touched.
		_far_cyl("coaster_col_%d" % i,
			foot + Vector3(0, (h - COASTER_EMBED) * 0.5, 0),
			0.55, h + COASTER_EMBED, mat, 6)
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
##
## **`ground` is the surface the wheel stands on, not the axle's base**, and the
## deck and the cars are built here rather than by the caller because for a
## while they were not. The section built its own deck, raised the ring 0.6m
## onto it and hung eight cars off the rim; the tableau called this function on
## the bare shore and got neither. So the wheel the plaza looks at all day stood
## 0.6m low and was a bare hoop, and the one you walk up to is a wheel with cars
## on it — which is not a fidelity difference, it is a different ride. The
## tableau is allowed to be cheap and is not allowed to be a *different shape*:
## the eight cars are most of what says "wheel" at 87m, and they are eight boxes.
##
## Only the palette differs now. Structure, deck and cars each take a material
## so the tableau can stay inside its own three-tone haze band while carrying the
## same silhouette. The clutter round its feet — fence, queue rail, booth — is
## still the section's alone: it is 1.2m tall behind an 8m frontage, so it says
## nothing from the far side and is not part of the shape.
func _wheel(ground: Vector3, mat: String, deck_mat: String, car_a: String,
		car_b: String, heading := 0.0) -> void:
	var turn := Basis(Vector3.UP, heading)
	var plat := Plan.WHEEL_PLATFORM
	# Deck, axle and rim all come off the plan rather than being typed here, so
	# that `Plan.WHEEL_TOP` is a statement about this geometry and not a second
	# survey of it. An arch was sized against a guess at that number once.
	var deck := Plan.WHEEL_DECK
	var r := Plan.WHEEL_RADIUS
	# The rim is a tube half a metre thick, so the circle the spokes end on and
	# the cars hang from sits half a metre inside the radius the plan publishes.
	const TUBE := 0.5
	_box("wheel_deck", Vector3.ZERO, ground + Vector3(0, deck * 0.5, 0),
		Vector3(plat.x, deck, plat.y), deck_mat)
	var origin := ground + Vector3(0, deck, 0)
	var hub := origin + Vector3(0, Plan.WHEEL_HUB, 0)
	var ring := CSGTorus3D.new()
	ring.inner_radius = r - TUBE * 2.0
	ring.outer_radius = r
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
		var rim := hub + turn * Vector3(cos(a) * (r - TUBE), sin(a) * (r - TUBE), 0)
		_strut("wheel_spoke_%d" % i, hub, rim, 0.3, mat)
	_strut("wheel_leg_a", origin + turn * Vector3(-11, 0, 0), hub, 1.2, mat)
	_strut("wheel_leg_b", origin + turn * Vector3(11, 0, 0), hub, 1.2, mat)

	# Cars. Eight, on the rim ends the spokes already reach — through `turn`,
	# like the spokes, rather than hard-coded into the Z–Y plane the way the
	# section's copy was. Hung below their pin so they read as swinging rather
	# than as bolted on.
	for i in 8:
		var a := TAU * i / 8.0
		var at := hub + turn * Vector3(cos(a) * (r - TUBE), sin(a) * (r - TUBE), 0)
		_box("wheel_car_%d" % i, Vector3.ZERO, at + Vector3(0, -1.1, 0),
			Vector3(2.0, 1.4, 1.6), car_a if i % 2 == 0 else car_b, 0.0, false)


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

## How far either side of the pier's centre line the promenade's own furniture
## stands off. `PIER_HALF_W` plus a stride — the deck is 8m wide and what has to
## be clear is the deck plus the room to turn onto it. Read by the edge posts,
## the lamp masts and the lamp standards, which used to carry it as three
## separate 5.0s and one omission.
const PIER_MOUTH_CLEAR := Plan.PIER_HALF_W + 1.0


## Whether the promenade's west edge at this z is the wheel's jetty rather than
## the water.
##
## The rail, the posts and the masts all stand a hand inside `SHORE_EDGE`, and
## the jetty's east face *is* `SHORE_EDGE`, so across its 26m they would run
## along the front of a boarding platform — a rail across the ride, and a mast
## in the middle of it. Nothing can be walked off there either: the platform
## deck stands 0.6m proud and `CharacterBody3D` has no step-up, so its own east
## face is the guard the rail would have been. The break is the honest shape and
## it is also the safe one.
func _over_the_jetty(z: float) -> bool:
	return z > Plan.WHEEL_FROM_Z - 0.4 and z < Plan.WHEEL_TO_Z + 0.4
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
	_bluff_face()
	# The ground the boardwalk stands on: back lane, frontage, promenade. Runs
	# 2m east under the bluff's west face rather than butting against it.
	var width := SHORE_FROM_X - SHORE_EDGE
	_box("shore", Vector3.ZERO,
		Vector3((SHORE_FROM_X + SHORE_EDGE) * 0.5, SHORE_TOP - 3.0, 0),
		Vector3(width, 6.0, 340), "far_warm")


## How far either side of the axis the bluff's face is dressed.
##
## The face runs 341m and the boardwalk can see about 150 of it. Beyond that it
## is scenery at ninety metres, where a blank cliff is correct and cheaper.
const BLUFF_DRESS_Z := 75.0

## The buttresses, at eight metres, and the stretch they cover.
const BLUFF_BUTTRESS_STEP := 8.0
const BLUFF_BUTTRESS_FROM := -72.0
const BLUFF_BUTTRESS_COUNT := 19

## The coping's underside and top, which four other things are laid off.
const BLUFF_COPING_TOP := 0.0
const BLUFF_COPING_DEEP := 0.7


## The face, dressed: coping, plinth, buttresses, and an end at each end.
##
## Six metres of blank plane is what the player looks back at from the lane, and
## until 2026-08-14 that is exactly what it was — the reason the two sides of the
## descent did not read as the same place was half the hidden stair and half
## this. A seawall was the answer and still is; what follows is the rest of it.
##
## **The buttresses did not reach the coping.** Every one of the nineteen stopped
## at −0.797 under a coping whose underside is at −0.697, so the whole row has
## been standing in a 100mm shadow gap since the day it went in. At six metres
## and in the sun it reads as a row of posts leaning on a shelf rather than as
## masonry, which is the opposite of the point. They are laid off the coping's
## own underside now, with 20mm of overlap, so the two cannot part again — the
## same fix as everywhere else in this file, which is to derive the number rather
## than type it in two places.
##
## **A plinth, because a wall has to stand on something.** The face met the shore
## at a hard right angle for the full 150m. Nothing in the park does that: the
## kerb, the coping and every retaining wall on the cascade are all thicker at
## the bottom than the thing above them. A course 0.8m high and 0.65m proud is
## what carries the buttresses down to the ground and gives the foot a shadow
## line, and it is the single cheapest shape on the face — one box for 150m.
##
## **And the dressing stops rather than ends.** The coping runs to z ±75 and is
## sawn off square against 341m of continuing cliff, which is exactly what you
## are looking down from the pier. A terminal pier at each end is the ordinary
## answer: heavier than a buttress, deeper than the coping, and the coping dies
## into it instead of into air.
func _bluff_face() -> void:
	var face := Plan.BLUFF_FACE_X
	_box("bluff_coping", Vector3.ZERO,
		Vector3(face + 0.15, BLUFF_COPING_TOP - BLUFF_COPING_DEEP * 0.5, 0.0),
		Vector3(1.1, BLUFF_COPING_DEEP, BLUFF_DRESS_Z * 2.0), "far_shade", 0.0, false)

	# The plinth, a touch longer than the coping so it reads as running under it
	# rather than as a second course of the same length stopping at the same
	# place. Sunk into the shore rather than sat on it, for the reason every
	# ground-meeting shape in this file is: a face flush with the floor is a
	# coplanar pair waiting for the displacement to be one step the wrong way.
	# **This one collides, and the coping and buttresses do not.** The plinth is
	# the proudest thing on the face at standing height, so it is what a body
	# actually meets; the buttresses sit behind its outer face and the coping is
	# six metres up. Before it existed the player stopped against the bluff at
	# −58.3 and stood 190mm inside every buttress they passed, which is the sort
	# of thing that only shows up in a screenshot taken from the right place.
	_box("bluff_plinth", Vector3.ZERO,
		Vector3(face - 0.175, SHORE_TOP - 0.1, 0.0),
		Vector3(0.95, 1.4, BLUFF_DRESS_Z * 2.0 + 0.8), "far_shade")

	# **Laid off the coping, not off a typed height.** Top is the coping's
	# underside plus an overlap; bottom is under the shore. The height is what
	# falls out of the two, so moving either end moves the buttress with it.
	var top := BLUFF_COPING_TOP - BLUFF_COPING_DEEP + 0.02
	var bottom := SHORE_TOP - 0.06
	for i in BLUFF_BUTTRESS_COUNT:
		var bz := BLUFF_BUTTRESS_FROM + float(i) * BLUFF_BUTTRESS_STEP
		_box("bluff_buttress_%d" % i, Vector3.ZERO,
			Vector3(face - 0.24, (top + bottom) * 0.5, bz),
			Vector3(0.5, top - bottom, 1.2), "far_warm", 0.0, false)

	# The ends. Set in from the coping's own end so the coping oversails it in
	# plan, which is what stops the pier reading as a buttress that grew.
	#
	# **And standing 120mm above the coping rather than flush with it.** Flush is
	# what it was, and flush meant the pier's top face and the coping's top face
	# were the same plane — `coplanar_test` caught it as a 1.01m² pair at y 0.003,
	# which is the whole reason that test exists. The displacement in `_add`
	# separates shapes that merely touch; two shapes *authored* onto one plane are
	# a coincidence it cannot be expected to undo. A pier that caps its coping is
	# also simply what a pier does.
	var pier_top := BLUFF_COPING_TOP + 0.12
	for side in [-1.0, 1.0]:
		var tag := "n" if side < 0.0 else "s"
		_box("bluff_pier_%s" % tag, Vector3.ZERO,
			Vector3(face - 0.36, (pier_top + bottom) * 0.5,
				side * (BLUFF_DRESS_Z - 1.1)),
			Vector3(0.8, pier_top - bottom, 2.4), "far_shade")

	_bluff_beds()


## Where the foot planting starts and how far it runs, either side of the axis.
##
## It starts clear of the wings — `WING_TURN_Z` is 10.3, so nothing before 12
## can foul the turn — and stops well short of the dressed stretch's ends. The
## point is a monument whose landscaping runs out along the foot of the cliff,
## not a planted cliff.
const BLUFF_BED_FROM := 12.0
const BLUFF_BED_SEGS := 4
const BLUFF_BED_LEN := 4.4
const BLUFF_BED_GAP := 0.4


## The planting at the foot of the face, flanking the cascade.
##
## `_cascade_bank` plants the wedge behind the outbound leg and `_cascade_bed`
## the foot of the return leg, and both stop dead where the wings stop — so the
## terracing that makes the descent read as a cut hillside ends exactly at the
## monument's own footprint, and the face either side of it meets the shore at a
## bare right angle. From the lane that is the join you actually look at: an
## elaborate planted object with nothing growing within twenty metres of it.
##
## So the same three-part vocabulary the other two beds use — kerb, soil, blooms
## — carried out along the foot and **stepping down as it goes**. Four segments a
## side, each lower than the last, ending at half the height it started. That is
## the half that matters: a run of equal beds would read as a planted promenade
## and make the whole lane ornamental, and the lane is the service side. Beds
## that get shallower and stop say the planting belongs to the cascade and is
## running out of reasons to be there, which is what is true.
##
## Not carried past `BLUFF_BED_FROM + 4 * (LEN + GAP)`, about 31m out. Beyond
## that the face is buttresses and plinth, which is what a working seawall is.
func _bluff_beds() -> void:
	var face := Plan.BLUFF_FACE_X
	# In front of the plinth, overlapping it, so the two read as one base rather
	# than as a planter parked against a wall.
	var x1 := face - 0.6
	var x0 := x1 - 1.4
	for side in [-1.0, 1.0]:
		var tag := "n" if side < 0.0 else "s"
		for i in BLUFF_BED_SEGS:
			# Stepping down: full height at the monument, half of it at the end.
			var rise: float = lerpf(0.95, 0.5, float(i) / float(BLUFF_BED_SEGS - 1))
			var top: float = SHORE_TOP + rise
			var za: float = side * (BLUFF_BED_FROM + float(i) * (BLUFF_BED_LEN + BLUFF_BED_GAP))
			var zb: float = za + side * BLUFF_BED_LEN
			_box("bluff_bed_%s_%d" % [tag, i], Vector3.ZERO,
				Vector3((x0 + x1) * 0.5, (top + SHORE_TOP - 1.0) * 0.5,
					(za + zb) * 0.5),
				Vector3(x1 - x0, top - SHORE_TOP + 1.0, absf(zb - za)), "building")
			_box("bluff_bed_soil_%s_%d" % [tag, i], Vector3.ZERO,
				Vector3((x0 + x1) * 0.5, top + 0.16, (za + zb) * 0.5),
				Vector3(x1 - x0 - 0.36, 0.32, absf(zb - za) - 0.24), "planting",
				0.0, false)
			for k in 5:
				var hx: float = lerpf(x0 + 0.35, x1 - 0.35, _hash01(i * 29 + k, 13, 61))
				# `min`/`max` rather than `za`/`zb`, because the north run counts
				# down in z and the naive form widens the range instead of
				# insetting it — the same trap `_cascade_bank` documents.
				var hz: float = lerpf(minf(za, zb) + 0.35, maxf(za, zb) - 0.35,
					_hash01(i * 29 + k, 17, 67))
				var bloom: String = ["bloom_pale", "bloom_warm", "bloom_pink"][(i + k) % 3]
				_sphere("bluff_bloom_%s_%d_%d" % [tag, i, k],
					Vector3(hx, top + 0.33, hz), Vector3.ZERO,
					0.15 + _hash01(k, 5, 31) * 0.13, bloom)


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
	#
	# Structure in the haze band and the cars in their real colours, which is
	# the one place the tableau is allowed out of its three tones. Built in
	# `far_shade` and `far_warm` first, on the argument that the band is what
	# makes the west read as distance — and side by side with the section's own
	# wheel from the same camera the cars simply were not there. Grey beads on a
	# grey ring at 87m are a grey ring. The pavilion's night lighting already
	# settled this case: what identifies a thing has to be the same colour from
	# both sides of the seam, or the two versions are two rides.
	_wheel(Vector3(WHEEL_AT.x, SHORE_TOP, WHEEL_AT.y),
		"far", "far_shade", "red", "yellow", PI * 0.5)
	# The plaza's half of the west seam. Here because this scene is the plaza's
	# and only the plaza's — it is thrown away at the moment of the crossing,
	# which is exactly the life a gate pointing west should have.
	_arch_seam(&"plaza", &"boardwalk")
	_east_seam(&"plaza", &"terraces")
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


## How far below its deck a wing's masonry reaches. Past the floor rather than
## down to it, so a box is buried at every point rather than floating at one end
## and cut at the other.
##
## **A function of the site rather than a constant, since the east cascade.** It
## was `SHORE_TOP - 1.4`, which is the west's floor and nobody else's; the east
## one stands on the plaza at y 0 and its masonry has to reach 1.4 below *that*.
## The 1.4 is the shared part and the floor is the sited part, which is the split
## every other number in these functions makes.
func _wing_base_y(site: Dictionary) -> float:
	return float(site["floor_y"]) - 1.4

## How far above the court a wing's west edge has to be before it wants a rail.
## A step, near enough — under this the edge is a kerb and a guard on it is a
## fence across the bottom of the descent. It is the *only* thing that decides
## where the return leg's rail stops, and it is a height rather than a length on
## purpose: a length has to be re-checked every time the monument's proportions
## move, and the last one was not.
const RAIL_FREEBOARD := 0.6


## The forecourt the east cascade stands in: the ground between the plaza's east
## wall and the foot of the climb.
##
## **It is the plaza's own ground carried through the gate**, not a section's
## floor, which is why it is brick and why it sits at `GROUND_SEAM` under y=0
## exactly as `entrance_ground` does. Two ground planes that meet have to
## disagree by something or they z-fight over every square metre they share, and
## the established answer in this park is that the newer one gives way downward.
## The step lands at x=52, where the plaza's own 104m slab runs out, and is a
## centimetre — the same one the street has had since it was laid.
##
## Fourteen metres from the wall's outer face to the westmost masonry, which is
## what makes the monument a monument rather than a retaining wall you walk into:
## a 6m face seen from fourteen is a 24° elevation, near enough what the
## reference photographs are taken at.
##
## **Its north, south and east edges are raw, and will be until the scarp and the
## shelf are built.** They are outside the cone the gap frames — from the near
## standpoint the opening shows z −9.9..5.9 at the far side of the court, against
## a slab running −28..24 — so nothing you can see through the gate can see the
## end of it. Standing *in* the court is another matter, and that is the hill's
## job rather than the gate's.
func _east_court() -> void:
	# Extents out of the plan since 2026-08-18, because the hill behind now
	# stands on this slab and the two have to end together. See
	# `ParkPlan.EAST_GROUND_HALF_Z`.
	var x0 := Plan.EAST_GROUND_FROM_X
	var x1 := Plan.EAST_GROUND_TO_X
	var hz := Plan.EAST_GROUND_HALF_Z
	var axis: float = Plan.ARCH_AT.y
	_box("east_court", Vector3.ZERO,
		Vector3((x0 + x1) * 0.5, -1.0 + GROUND_SEAM, axis),
		Vector3(x1 - x0, 2.0, hz * 2.0), "brick", 0.0, true)


## The hill the east cascade climbs into: the scarp, the shelf at its head, and
## the terrace above that.
##
## **The plan has described all of this since the cascade was sited and none of
## it existed until 2026-08-18.** `HILL_FACE_X`, `HILL_TOP`, `SHELF_*` and
## `TERRACE_TWO_*` were written the day the east cascade went in, and the effect
## was a six metre monument standing in open ground with a crest you could climb
## onto and then walk off the world from. The rim went in first because it is
## what the gate frames; this is what the gate frames the *foot* of.
##
## **The shelf is a notch, not a plateau, and that is the shape decision.** The
## plan calls it "a belvedere at the head of a climb", and the honest reading of
## that is a bay cut into a hillside rather than a terrace with a fence around
## it. So the hill stands a full twelve metres at the scarp line everywhere
## except across `SHELF_FROM_Z … SHELF_TO_Z`, where it is cut back to six and
## eight metres deep — sixteen until 2026-08-22, halved because the flat pause
## at exactly the crest's height was what hid the whole climb from the plaza;
## see `SHELF_TO_X`. What that buys is that every edge of the shelf is
## finished by construction: hill on the north, hill on the south, the second
## scarp on the east, and one parapet on the west where the view is. There is
## nothing to fall off and nothing raw to see, which the alternative — a six
## metre deck with a rail round three sides of it — could not say.
##
## It also settles what the belvedere is *for*. From up here you look west, back
## down over the court and through the gate at the fountain, with the rim over
## your shoulder. North and south are walls. A view has to be pointed somewhere
## or it is just elevation.
##
## The way on and off is the cascade and only the cascade. The parapet's gap is
## the landing's own width, so you come up a wing, cross the head of the monument
## and step through — see `_east_hill_sill` for why that step is its own box.
func _east_hill() -> void:
	var axis: float = Plan.ARCH_AT.y
	var hz := Plan.EAST_GROUND_HALF_Z
	var gz0 := axis - hz
	var gz1 := axis + hz
	var x0 := Plan.HILL_FACE_X
	var x1 := Plan.SHELF_TO_X
	var x2 := Plan.TERRACE_TWO_TO_X
	var y1 := Plan.HILL_TOP
	var y2 := Plan.TERRACE_TWO_Y
	var sz0 := Plan.SHELF_FROM_Z
	var sz1 := Plan.SHELF_TO_Z

	# The mass, in three pieces around the notch. Footed below the ground for
	# the reason `COASTER_EMBED` and the rim's blocks are: a box bottomed at
	# exactly y = 0 shares its underside with everything else standing on y = 0,
	# and that is the coplanar case the build-order ordinal cannot reach because
	# the two shapes can be four scenes apart.
	var base := -HILL_EMBED
	_hill_block("hill_north", x0, x2, base, y2, gz0, sz0)
	_hill_block("hill_south", x0, x2, base, y2, sz1, gz1)
	# From the head of the climb, not from the scarp: x1..CLIMB_TO_X is the
	# ravine, and nothing subtracts here — these are sibling CSG boxes, so the
	# void has to be left rather than cut. `_east_climb` lays the mass either
	# side of it, tapering as the opening closes.
	_hill_block("hill_back", Plan.CLIMB_TO_X, x2, base, y2, sz0, sz1)

	# Under the shelf. Its top stops a deck's thickness short rather than level,
	# so the deck laid over it is the only up-facing surface at six metres —
	# 576m² of coplanar-but-displaced floor is a thing the seam ordinal would
	# survive and nobody should ask it to.
	#
	# Run a metre into the two blocks either side, because a floor that butts a
	# wall exactly leaves the zero-width seam a capsule catches on. Everything
	# past `sz0`/`sz1` is buried.
	_box("shelf_fill", Vector3.ZERO,
		Vector3((x0 + x1) * 0.5, (base + y1 - SHELF_DECK_T) * 0.5, (sz0 + sz1) * 0.5),
		Vector3(x1 - x0, y1 - SHELF_DECK_T - base, sz1 - sz0 + 2.0), "building")
	# Brick, and the same brick as the court below and the plaza beyond it. The
	# east is one continuous floor that happens to climb; changing material at
	# the top of a climb would say the shelf belongs to something else, and
	# there is nothing else here yet for it to belong to.
	# **In three pieces, around the collecting pool.** The deck used to be one
	# slab over the whole belvedere, and the pool is cut into that slab — so the
	# water sat 35cm under a continuous brick floor and the thing the chain
	# discharges into was invisible from every standpoint. Nothing subtracts here;
	# a basin in a deck is three pieces of deck.
	var ppz: float = Plan.POOL_HALF_Z + 0.25
	var pfx: float = Plan.POOL_FROM_X
	_box("shelf_deck_w", Vector3.ZERO,
		Vector3((x0 - 0.3 + pfx) * 0.5, y1 - SHELF_DECK_T * 0.5, (sz0 + sz1) * 0.5),
		Vector3(pfx - x0 + 0.3, SHELF_DECK_T, sz1 - sz0 + 1.2), "brick")
	for k in 2:
		var a: float = sz0 - 0.6 if k == 0 else axis + ppz
		var b: float = axis - ppz if k == 0 else sz1 + 0.6
		_box("shelf_deck_%s" % ("n" if k == 0 else "s"), Vector3.ZERO,
			Vector3((pfx + x1 + 0.6) * 0.5, y1 - SHELF_DECK_T * 0.5, (a + b) * 0.5),
			Vector3(x1 - pfx + 0.6, SHELF_DECK_T, b - a), "brick")
	_east_hill_sill(axis, x0, y1)

	# The parapet, either side of the way in.
	for k in 2:
		var a: float = sz0 - 0.6 if k == 0 else axis + Plan.LANDING_HALF_W
		var b: float = axis - Plan.LANDING_HALF_W if k == 0 else sz1 + 0.6
		_box("shelf_parapet_%s" % ("n" if k == 0 else "s"), Vector3.ZERO,
			Vector3(x0 + Plan.SHELF_PARAPET_T * 0.5,
				y1 + Plan.SHELF_PARAPET_H * 0.5, (a + b) * 0.5),
			Vector3(Plan.SHELF_PARAPET_T, Plan.SHELF_PARAPET_H, b - a), "building")
		# A coping, because a parapet you lean on wants a top rather than an
		# edge, and because from the court six metres below this line is the
		# only thing drawn on the scarp at all.
		_box("shelf_coping_%s" % ("n" if k == 0 else "s"), Vector3.ZERO,
			Vector3(x0 + Plan.SHELF_PARAPET_T * 0.5 - 0.06,
				y1 + Plan.SHELF_PARAPET_H + 0.06, (a + b) * 0.5),
			Vector3(Plan.SHELF_PARAPET_T + 0.28, 0.12, b - a), "accent", 0.0, false)

	# **The terrace above used to be capped in flat planting here and is a mesh
	# now.** Three `_terrace_cap` plates at `TERRACE_TWO_Y` gave the hill a top
	# that was level to the millimetre over fifty metres by fifty, so from the
	# court its skyline was a ruled line and from anywhere above it the east was
	# a green table with a trench in it. The blocks above stay — they are the
	# mass and the collision and the thing the notch's walls are cut out of — but
	# they stop a cap's thickness short of the plateau and `_east_earth` lays the
	# ground itself over them. See `_hill_roll`.
	#
	# Last, so nothing above it moves an ordinal.
	_shelf_buttresses(x0, x1, y1, y2, sz0, sz1)
	_hill_brick(x0, x1, y1, gz0, gz1, sz0, sz1)


## How far below the ground the hill is footed. See `COASTER_EMBED`: a mass
## bottomed at exactly y = 0 shares its underside with every other thing
## standing on y = 0, and those can be four scenes away where the seam ordinal
## cannot reach them.
const HILL_EMBED := 3.0

## The deck laid over the shelf's fill, and the cap laid over the terrace's
## mass. Both exist so that a level has exactly one up-facing surface at its own
## height — the mass beneath each stops short by this much, so there is never a
## second floor a quarter of a millimetre away pretending to be the same one.
const SHELF_DECK_T := 0.4
const TERRACE_CAP_T := 0.5


## The hill's own ground, as a swell rising behind the scarp.
##
## **The plateau was a table and this is what stops it being one.** `_east_hill`
## laid its top as one flat `planting` cap at `TERRACE_TWO_Y` across the whole
## east, so from the court the skyline of a twelve metre hill was a ruled
## horizontal line and from the air it was a green tabletop with a trench cut in
## it. Neither reads as a hill, and no amount of dressing on the scarp fixes a
## silhouette — the same finding the rim reached on 2026-08-18 from the other
## direction, and for the same reason: shape is what says "land", and a box has
## none.
##
## **It rises rather than falls, and the scarp is why.** The retaining wall's top
## is at `TERRACE_TWO_Y`, so ground that dipped below it would leave the wall's
## own coping as the highest thing on the hill and put the ruled line back
## exactly where it was, one course lower. Earth rising *behind* a wall is what
## every reference photograph of a terraced hillside is of.
##
## Zero at the scarp line, so the surface meets the wall's top cleanly rather
## than standing proud of it, and eased in over `HILL_SWELL_RUN` so the rise
## reads as ground rather than as a step behind a parapet.
const HILL_SWELL := 2.2
const HILL_SWELL_FROM := 4.0
const HILL_SWELL_RUN := 26.0
const HILL_JAG := 1.1

## How far outside the ravine's widest opening the swell fades in over. Inside
## that the ground is flat at `TERRACE_TWO_Y` — see `_hill_roll`, where the
## reason is arithmetic rather than taste.
const HILL_ROLL_GUARD := 6.0

## The head landing's extent: the flat half-width in z across its band, and
## where the band ends short of the rim's toe. 22 spans the hill's own ground
## less a verge to the skin edge at 26, which is "the length of the east
## section" as the section is built today; 118 leaves two metres of meadow
## before `RIM_FOOT_X` so the terrace ends in ground rather than in the ridge.
const HEAD_LAND_HALF := 22.0
const HEAD_LAND_TO_X := 118.0

## Where the east's ground meshes stop, and it is **not** `TERRACE_TWO_TO_X`
## any more. The sections still end at 120, but the ground now stands at
## `CLIMB_HEAD_Y` there while the rim's face crosses that line at its own 12m
## foot — so a mesh ending at 120 is an open edge six metres over the face,
## which is the see-through slot one storey up. The rim's face reaches 18 by
## x 126 at its shallowest gradient, so the ground runs to 127 and its open
## edge hangs *inside* the ridge's body, below the face — sealed by the rim
## itself, which is what retired `east_toe_fill`.
const EARTH_TO_X := 127.0

## How finely the landform is sampled along the climb.
##
## A smoothness decision rather than a shape one, which is the whole point of
## building it as a mesh — see `_rim_mesh`, which this construction comes from
## and where the argument is written out. As bands it was a shape decision, and
## finer bands only ever bought more seams.
const EARTH_STEP := 1.25

## How many intermediate rows the plateau strip carries between the brow and
## the edge. Nine puts a row roughly every 2.5m across the widest span, which
## resolves the roll's shortest wavelength (23m) comfortably — see the note in
## `_east_earth` on why two rows was a shape bug and not a smoothness one.
const EARTH_MID_ROWS := 9

## How far the skin's edge is buried into the masonry behind it where the two
## meet on a plateau edge.
##
## Landing the skirt exactly on a wall's face is the coplanar case rather than
## the tidy one: `climb_bayhill`'s inner face and a skirt dropped to the same
## plane are two surfaces pointing the same way at the same depth, which is the
## house rule's whole subject. Buried, there is nothing to fight.
const EARTH_INSET := 0.15

## How far the middle of a planted bank stands proud of the straight line
## between its foot and its brow. See `_east_bank_y`.
const BANK_BOW := 0.45

## How far the skin floats over the mass it lies on.
##
## **The swell opened a hole and this is what closes it.** The blocks under the
## hill used to stop a cap's thickness below `TERRACE_TWO_Y`, because a flat
## `planting` plate went on top of them. The skin that replaced that plate rises
## up to 2.9m above the same level and the mass did not follow, so there was
## daylight under the ground — invisible from anywhere anyone would think to look
## and unmissable from the one place nobody poses a camera. An eye a little
## *below* a near-horizontal surface sees it edge-on, as a thin green blade with
## sky under it, which is what fifty metres of plateau over a half-metre slot
## looks like from the flight.
##
## So the mass tops out at `TERRACE_TWO_Y` — the skin's own floor, since the roll
## only ever adds — and the skin sits this far above it. Two centimetres rather
## than nothing, because nothing is the coplanar case: the west four metres of
## the hill carry no swell at all and would otherwise lay 8m by 4m of skin
## exactly on the block beneath it.
const GROUND_LIFT := 0.02


## The undulation on the hill's top surface.
##
## **Held at exactly zero inside the ravine corridor, and that guard is
## load-bearing rather than tidy.** The bank's outer edge *is* the plateau, and
## `_climb_open_half` derives the opening from the depth the bank has to lay back
## over — which is `TERRACE_TWO_Y` minus the floor. Letting the plateau roll over
## the cut would feed a moving number straight back into an opening width that
## the belvedere's east wall is sized against, which is `CLIMB_OPEN_HALF`'s only
## job. So the roll fades in outside the widest opening and the ravine keeps the
## arithmetic it was designed with.
##
## A fixed pair of sines rather than an RNG, for `_rim_jag`'s reason: the hill
## has to come out the same on every run, or the coplanar report changes under
## whoever is reading it.
##
## The jag is scaled by the same ease as the swell so that both are zero at the
## scarp. A hill that arrives at its own retaining wall already undulating puts a
## wave in the one line the wall is there to draw.
func _hill_roll(x: float, z: float) -> float:
	var axis: float = Plan.ARCH_AT.y
	# The flat zone is the ravine corridor for most of the climb, and the whole
	# terrace across the head landing's band: `CLIMB_HEAD_TO_X` has named the
	# landing between the head of the cutting and the rim's toe since the climb
	# doubled, and a promenade cut through rolling swell is a trench rather than
	# a landing. Eased over 4m at both ends so the meadow hands over instead of
	# stepping — see `_east_head_landing`, which paves what this flattens.
	var hb := clampf((x - (Plan.CLIMB_TO_X - 2.0)) / 4.0, 0.0, 1.0) \
		* clampf((HEAD_LAND_TO_X + 2.0 - x) / 4.0, 0.0, 1.0)
	hb = hb * hb * (3.0 - 2.0 * hb)
	var flat_half := lerpf(Plan.CLIMB_OPEN_HALF, HEAD_LAND_HALF, hb)
	var guard := clampf((absf(z - axis) - flat_half)
		/ HILL_ROLL_GUARD, 0.0, 1.0)
	if guard <= 0.0:
		return 0.0
	var t := clampf((x - Plan.HILL_FACE_X - HILL_SWELL_FROM) / HILL_SWELL_RUN,
		0.0, 1.0)
	var ease := t * t * (3.0 - 2.0 * t)
	# Faded out again over the last few metres before the rim's toe, and this is
	# a closure rather than a taste: the ground's east edge is an open
	# single-sided boundary at `TERRACE_TWO_TO_X`, and the swell stood it up to
	# three metres proud of the rim's own face there — a slot you could look
	# through into the inside of the ridge, from anywhere on the meadow. A
	# ridge's bench meets its toe in a dip anyway; `east_toe_fill` seals what
	# millimetres remain.
	var efade := clampf((EARTH_TO_X - 3.0 - x) / 8.0, 0.0, 1.0)
	efade = efade * efade * (3.0 - 2.0 * efade)
	var jag := (sin(z * 0.113) * 0.6 + sin(z * 0.271 + 1.3) * 0.4) * HILL_JAG
	return (HILL_SWELL * ease + jag * ease * guard) * efade


## The finished level of the hill's top at a point on it. The base is the
## plan's own ramp — bench at `TERRACE_TWO_Y`, rising behind the scarp to
## `CLIMB_HEAD_Y` — and the roll rides on top of it.
func _east_ground_y(x: float, z: float) -> float:
	return Plan.east_ground_base(x) + GROUND_LIFT + _hill_roll(x, z)


## The level of the planted bank at a point on it: the batter between the
## retaining wall's top and the plateau.
##
## **The one description of that surface**, because two things stand on it and
## they must not each derive it. `_east_earth` builds the skin off these same two
## endpoints, and the blooms are placed with this — laid out separately they
## agreed until the batter changed, which is the failure mode `ParkPlan`'s wing
## accessors were pulled out of `walk_test` to prevent.
##
## **`TERRACE_TWO_Y - bank_d` for the wall's top, not `floor + wall_h`.** They are
## the same number and this one cannot drift: the wall's height is exactly the
## depth the bank could not lay back inside `CLIMB_OPEN_HALF`, so its top is the
## plateau less what the bank took. Written the other way round it is two
## subtractions that have to agree with each other.
func _east_bank_y(x: float, z: float) -> float:
	var axis: float = Plan.ARCH_AT.y
	var w := _climb_open_half(x)
	var half: float = Plan.CLIMB_HALF_Z
	var d := clampf(absf(z - axis), half, w)
	var t := (d - half) / maxf(w - half, 0.001)
	# **The top end is the plateau's own level, lift included.** The bank's brow
	# row and the plateau's inner row are the same vertices, so a bank arriving at
	# a bare `TERRACE_TWO_Y` would leave a two centimetre crack along the top of
	# every cut — the crease between the two strips being exactly the line where a
	# gap is least visible and most certainly a hole.
	var y := lerpf(Plan.east_ground_base(x) - _climb_bank_d(x),
		Plan.east_ground_base(x) + GROUND_LIFT, t)
	# **The bow, and it is what stops the batter reading as a ramp.** Welded and
	# smooth, the bank came out as one perfectly planar green wedge — which is an
	# honest section through a cut slope and still not land, because a plane has
	# one normal and therefore one tone across its whole face. Earth on a slope
	# slumps convex, and the shading that comes off a convex surface is the whole
	# difference between a hillside and a wheelchair ramp.
	#
	# `sin(t * PI)` is zero at both ends by construction, which is the property
	# that matters: the foot has to stay on the retaining wall's top and the brow
	# has to stay on the plateau at `TERRACE_TWO_Y`, because those two lines are
	# where the masonry meets the ground and `CLIMB_OPEN_HALF` is measured. The
	# bow lives entirely in the middle of the batter, where nothing is derived
	# from it.
	#
	# Modulated along the climb so it is not one extrusion repeated — a constant
	# bow swept up a hill is a moulding.
	#
	# **And scaled by the bank's own depth**, because the bow did not die with
	# the bank: near the head the three rows converge to one line as the cut
	# runs out, and a bow still pumping 0.3m of height into a strip of zero
	# width folds it into sliver-fins — the grey paper darts among the last
	# flight's blooms in the 2026-08-23 play reports, found by hiding node
	# families until they vanished. Full bow above 2m of depth, dying linearly
	# with the cut below it.
	return y + sin(t * PI) * BANK_BOW * (0.62 + 0.38 * sin(x * 0.41)) \
		* clampf(_climb_bank_d(x) * 0.5, 0.0, 1.0)


## The plateau's inner edge at a station: how far off the axis the hill's own
## ground begins, and what is holding it up there.
##
## Four regions west to east, and each hands off to different masonry. Beside the
## belvedere it is the notch's own buttressed wall; up a flight it is the top of
## the planted bank, which is the one case where the skin carries the slope
## itself; at a terrace it is the back of a bay; past the head of the climb there
## is no cut left and the ground runs across the axis.
##
## `bank` is what the caller needs to know rather than which region it is in: a
## bank means the skin drops to the retaining wall's top and the wall closes it,
## and anything else means the skin ends at plateau height and needs a skirt.
func _east_inner(x: float) -> Dictionary:
	var axis: float = Plan.ARCH_AT.y
	if x < Plan.CLIMB_FROM_X:
		return {"half": Plan.SHELF_TO_Z - axis, "bank": false}
	if x > Plan.CLIMB_TO_X:
		return {"half": 0.0, "bank": false}
	for r in Plan.climb_reaches():
		if x > float(r[1]) + 0.001:
			continue
		# A narrow landing is a pause in the stair and not a room off it, so
		# its sides stay banked and the hillside runs unbroken past it — see
		# `CLIMB_BAY_MIN_T`, which is where the rule is stated.
		if bool(r[4]) or float(r[1]) - float(r[0]) < Plan.CLIMB_BAY_MIN_T:
			return {"half": _climb_open_half(x), "bank": true}
		return {"half": Plan.CLIMB_HALF_Z + Plan.CLIMB_BAY_D, "bank": false}
	return {"half": 0.0, "bank": false}


## Where the landform is sampled along x.
##
## Every **bay** boundary appears **twice**, a hair either side of itself, and
## that is what builds the end wall of a bay. The inner edge jumps outward by
## metres at a bay's mouth — `CLIMB_BAY_D` is 6.5 against an opening near 12 —
## so two columns 4mm apart put a vertical face there, which is the cut face the
## banks either side used to draw with their own ends. One column would have
## sloped it across the whole reach. Boundaries where the bank simply continues
## — flight into narrow landing — are not doubled: the surface is continuous
## across them, and a doubled column on a continuous surface is a pair of
## 4mm quads with no reliable normal to hand the weld.
func _east_columns() -> PackedFloat32Array:
	var out := PackedFloat32Array()
	# At `CLIMB_TO_X` the inner edge falls from the head's own half-width to
	# nothing at one level — the ground closing across the axis rather than a
	# face — so that one interpolates over a step like everything else.
	# `CLIMB_FROM_X` stays doubled: the notch's own half-width hands off to the
	# ravine's there, and that jump is the notch's east reveal.
	var edges := PackedFloat32Array([Plan.CLIMB_FROM_X])
	var reaches := Plan.climb_reaches()
	for i in reaches.size():
		var r: Array = reaches[i]
		if bool(r[4]) or float(r[1]) - float(r[0]) < Plan.CLIMB_BAY_MIN_T:
			continue
		edges.append(float(r[0]))
		edges.append(float(r[1]))
	var x: float = Plan.HILL_FACE_X
	while x < EARTH_TO_X:
		out.append(x)
		for e in edges:
			if e > x and e < x + EARTH_STEP:
				out.append(e - 0.002)
				out.append(e + 0.002)
		x += EARTH_STEP
	out.append(EARTH_TO_X)
	return out


## The hill, as one welded surface per side.
##
## **A hillside cannot be made of boxes, which is the rim's finding arriving at
## the other end of the east.** The bank up each flight was four `planting`
## plates per third of a reach — twelve to a flight, each one flat on top with a
## vertical riser — so a slope battered at 1.4 came out as a giant green
## staircase standing beside a real one, and the bays cut into it read as more of
## the same rather than as the one deliberate step in the row. Above it the hill
## was `_terrace_cap`, one flat plate at `TERRACE_TWO_Y` across the whole east.
##
## Every artefact `_rim_mesh` lists is here for the same reason and none of them
## could be tuned out: a box is rigid, so its top is a straight horizontal line
## and a slope therefore steps at every boundary; the plates lapped rather than
## butted, which is the house rule and correct, and the lap showed as a line the
## full height of the face because the two either side stood at different levels.
## Finer plates buy finer steps and three times the nodes. The fix is to stop
## having boundaries.
##
## **Three strips, and which of their edges is a crease is the whole shape.** The
## bank is a plane laid back off the retaining wall's top; the plateau is the
## ground above it; the skirt closes the plateau's outer edge down onto the mass.
## The break of slope between bank and plateau is a *crease* — it is the top of
## the cut, and rounding it off turns a ravine into a valley — and Godot's
## `generate_normals` welds by position and smooth group only, so two strips is
## not enough to keep it and the groups are what do it. `_rim_mesh` measured that
## the hard way and the note there is the one to read before touching this.
##
## The surface itself is smooth along the climb, which is the entire point: a
## column shares its vertices with its neighbour, so the sampling rate is a
## smoothness decision and there is nothing at a column to see.
##
## **It carries its own collision, and that is new here.** Everything else in
## this park collides because it is a `CSGBox3D` with `use_collision`; a mesh has
## none, and the boxes this replaces were what stopped the player walking off the
## belvedere sideways and into the hill. So the skin gets a trimesh body on the
## world's own layer — layer 1, not the player's 2, see `_gate_area`.
func _east_earth(side: float, tag: String) -> void:
	var axis: float = Plan.ARCH_AT.y
	var out_z: float = axis + side * Plan.EAST_GROUND_HALF_Z
	var mass_top: float = Plan.TERRACE_TWO_Y
	var cols := _east_columns()

	# Four lines down the hill, sampled together so a column is one place on it
	# rather than four independent ones: the foot of the bank at the retaining
	# wall's top, the break of slope, the outer edge, and the skirt's foot.
	var foot := PackedVector3Array()
	var waist := PackedVector3Array()
	var brow := PackedVector3Array()
	var edge := PackedVector3Array()
	var hem := PackedVector3Array()
	var banked := PackedByteArray()
	for x in cols:
		var inner := _east_inner(x)
		var is_bank: bool = bool(inner["bank"])
		var ih: float = float(inner["half"])
		# The break of slope. On a bank it is the top of the batter and the skin
		# carries the slope below it; anywhere else the skin simply ends, buried
		# a little way into whatever masonry is holding the ground up there.
		var bz: float = axis + side * (ih if is_bank else ih + EARTH_INSET)
		if x > Plan.CLIMB_TO_X:
			# Past the head there is no cut and the two sides meet on the axis.
			# No inset, so their edges butt with identical normals rather than
			# leaving a 30cm slot down the middle of the ground.
			bz = axis
		brow.append(Vector3(x, _east_ground_y(x, bz), bz))
		# Through the shared accessor rather than inlined, so the skin and the
		# blooms standing on it cannot come to disagree about where the slope is.
		# Three lines and not two, because a bow needs a row of vertices in the
		# middle of the batter to be carried on — sampled at the same half-way
		# station `_east_bank_y` puts its own crown at.
		var fz: float = axis + side * Plan.CLIMB_HALF_Z
		var wz: float = axis + side * (Plan.CLIMB_HALF_Z + _climb_open_half(x)) * 0.5
		foot.append(Vector3(x, _east_bank_y(x, fz), fz))
		waist.append(Vector3(x, _east_bank_y(x, wz), wz))
		edge.append(Vector3(x, _east_ground_y(x, out_z), out_z))
		hem.append(Vector3(x, mass_top, out_z))
		banked.append(1 if is_bank else 0)

	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	# Group 0: the banks. Skipped wherever there is no cut to lay back into, so
	# the strip is broken at every bay rather than running through it.
	# Group 0: the banks, in two strips about the waist so the bow has a row to
	# ride on. **One group across both**, because the bow is a curve and not a
	# break — the crease is the brow, where the cut stops, and putting the waist
	# in a group of its own would draw a second line down the middle of every
	# bank saying nothing.
	st.set_smooth_group(0)
	_earth_strip(st, foot, waist, side, 0.0, banked)
	_earth_strip(st, waist, brow, side, 1.0, banked)
	# Group 3: the cut face at each end of a bank, which is the one surface on
	# this hill that was described in prose and never built. See `_earth_cap`.
	st.set_smooth_group(3)
	for j in banked.size():
		if banked[j] == 0:
			continue
		if j == 0 or banked[j - 1] == 0:
			_earth_cap(st, foot[j], waist[j], brow[j], -1.0, side)
		if j == banked.size() - 1 or banked[j + 1] == 0:
			_earth_cap(st, foot[j], waist[j], brow[j], 1.0, side)
	# Group 1: the ground above. Its inner row is the banks' outer row, position
	# for position — the weld is what would round the top of the cut off, and the
	# group is what stops it.
	#
	# **Subdivided in z since 2026-08-23, and the reason is arithmetic rather
	# than smoothness.** Two rows meant one quad spanning brow to edge — up to
	# 26m — so `_hill_roll`'s guard, fade and swell were only ever *sampled at
	# the edge row* and the profile between came back as a straight ramp off the
	# brow: the flat corridor never existed in the mesh, the crest courts
	# drowned in interpolated swell with only their wall caps showing, and from
	# inside a court the underside of that ramp is a culled backface — you
	# looked straight through the hillside at the fill masses, which is where
	# the grey staircases in the 2026-08-23 play reports were standing. A
	# function sampled at two points is a line, whatever it does in between.
	st.set_smooth_group(1)
	var prev := brow
	for k in range(1, EARTH_MID_ROWS + 1):
		var t := float(k) / float(EARTH_MID_ROWS + 1)
		var row := PackedVector3Array()
		for j in cols.size():
			var rz := lerpf(brow[j].z, edge[j].z, t)
			row.append(Vector3(cols[j], _east_ground_y(cols[j], rz), rz))
		_earth_strip(st, prev, row, side, 2.0 + t, PackedByteArray())
		prev = row
	_earth_strip(st, prev, edge, side, 3.0, PackedByteArray())
	# Group 2: the skirt down onto the mass at the world's edge.
	st.set_smooth_group(2)
	_earth_strip(st, edge, hem, side, 4.0, PackedByteArray())
	st.generate_normals()
	st.generate_tangents()
	var mesh := st.commit()

	var body := StaticBody3D.new()
	_add(body, "east_earth_%s" % tag)
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = mats["planting"]
	mi.name = "skin"
	body.add_child(mi)
	mi.owner = _root
	var shape := CollisionShape3D.new()
	shape.shape = mesh.create_trimesh_shape()
	shape.name = "shape"
	body.add_child(shape)
	shape.owner = _root


## One strip of the hill between two of its lines.
##
## `keep` is what breaks the banks at a bay: an empty array means every quad, and
## otherwise a quad is laid only where **both** its columns are banked. Testing
## one end lays a quad from a bank into a bay and puts a skewed plane across the
## mouth of it.
##
## Winding follows the side, because the two halves of the hill face opposite
## ways and a strip wound for one is inside out on the other — which does not
## look like a winding bug at all. It looks like the south half of the hill
## failing to generate.
func _earth_strip(st: SurfaceTool, low: PackedVector3Array,
		high: PackedVector3Array, side: float, v0: float,
		keep: PackedByteArray) -> void:
	var cols := low.size()
	for j in cols - 1:
		if keep.size() > 0 and (keep[j] == 0 or keep[j + 1] == 0):
			continue
		# A quad whose two rows coincide is zero area, and `generate_normals`
		# hands zero-area triangles junk — which renders as lit-white slivers,
		# not as nothing. Distance and not z-span, because the skirt's two rows
		# share their z on purpose and differ only in height.
		if low[j].distance_squared_to(high[j]) < 0.0004 \
				and low[j + 1].distance_squared_to(high[j + 1]) < 0.0004:
			continue
		var u0 := float(j) / float(cols - 1)
		var u1 := float(j + 1) / float(cols - 1)
		if side < 0.0:
			_rim_tri(st, low[j], u0, v0, high[j], u0, v0 + 1.0,
				low[j + 1], u1, v0)
			_rim_tri(st, high[j], u0, v0 + 1.0, high[j + 1], u1, v0 + 1.0,
				low[j + 1], u1, v0)
		else:
			_rim_tri(st, low[j], u0, v0, low[j + 1], u1, v0,
				high[j], u0, v0 + 1.0)
			_rim_tri(st, high[j], u0, v0 + 1.0, low[j + 1], u1, v0,
				high[j + 1], u1, v0 + 1.0)


## The cut face where a bank stops: the triangle of earth left standing when the
## batter is sliced across.
##
## **`_east_climb` has described this surface since the day the bays went in and
## nothing ever built it.** Its comment says a bay's "ends are the cut faces of
## the banks either side", and the banks are a zero-thickness single-sided skin —
## so what was actually there was an open edge with the inside of the hill behind
## it. `climb_bankcore` was believed to close it and cannot: the core is topped at
## the retaining wall's own level, which is the *lowest* the skin gets, so it sits
## under the batter and the whole wedge between the two is air. Every one of the
## eight bank ends was a hole four and a half metres tall, and because a skin
## shows nothing from behind, standing in a bay you looked through the hillside at
## the plaza with the blooms hanging in the sky over it.
##
## Nothing could have caught it. `coplanar_test.py` has no opinion about a surface
## that is missing — the same blind spot the cascade's unguarded handrail sat in —
## `walk_test` asks whether something is in the way and never whether it is there,
## and from the axis, which is where every shot of this climb has been taken, the
## banks are edge-on ribbons that read as ending in front of the rim rather than
## through it.
##
## The low edge is `foot.y` rather than a level of its own, and that is not
## shorthand: `_east_bank_y` puts the foot at `TERRACE_TWO_Y - _climb_bank_d(x)`
## with the bow at zero, which is the retaining wall's top where there is a wall
## and the landing's own floor where the bank has run out of depth to retain. So
## the face is full height at the brow and closes to nothing at the foot, which is
## what a slice through a batter is, and it lands on masonry at both ends by
## construction rather than by a number that has to be kept in step.
##
## Winding turns on `facing * side`, for `_earth_strip`'s reason doubled: the two
## halves of the hill face opposite ways and the two ends of a run do as well, so
## the four cases are two windings. Wrong, a cut face is invisible from the bay it
## walls and solid from inside the hill, which is the same failure it is here to
## fix and would look exactly like this one still being unfixed.
func _earth_cap(st: SurfaceTool, foot: Vector3, waist: Vector3, brow: Vector3,
		facing: float, side: float) -> void:
	var y0 := foot.y
	# The head of the climb, where the cut has closed and the bank is already
	# nothing. Both tests, and the second is the one that matters: at
	# `CLIMB_TO_X` the batter has no width at all but the brow is still
	# `GROUND_LIFT` over the foot, so a height-only guard passes and emits a
	# zero-area triangle — which has no reliable normal to hand the weld.
	#
	# 0.3 rather than 0.01 since 2026-08-23: over the last flight the bank
	# tapers through knee height, and a cap under 30cm is a paper sliver lying
	# on the grass with a near-degenerate normal — white confetti along the
	# head in the play reports. A cut face that shallow closes nothing the eye
	# can see through; the real faces at the bays are 2m and more.
	if brow.y - y0 < 0.3 or absf(brow.z - foot.z) < 0.01:
		return
	var top := [foot, waist, brow]
	var flip := facing * side < 0.0
	for k in 2:
		var a: Vector3 = top[k]
		var b: Vector3 = top[k + 1]
		var la := Vector3(a.x, y0, a.z)
		var lb := Vector3(b.x, y0, b.z)
		var u0 := float(k) * 0.5
		var u1 := u0 + 0.5
		if b.y - y0 > 0.001:
			if flip:
				_rim_tri(st, la, u0, 6.0, b, u1, 7.0, lb, u1, 6.0)
			else:
				_rim_tri(st, la, u0, 6.0, lb, u1, 6.0, b, u1, 7.0)
		# Skipped at the foot, where `la` and `a` are the same point.
		if a.y - y0 > 0.001:
			if flip:
				_rim_tri(st, la, u0, 6.0, a, u0, 7.0, b, u1, 7.0)
			else:
				_rim_tri(st, la, u0, 6.0, b, u1, 7.0, a, u0, 7.0)


## The shoulders: the hill's ground carried north and south across the two
## unbuilt sections' footprints until the rim takes over, and the west face that
## brings it down to the park.
##
## **The hill was an island until these went in.** Its flanks at the ground's
## edge were `hill_north` and `hill_south` seen bare — twelve metres of vertical
## `building` wall under a green lid, standing on nothing, with the rim behind
## reading as land and the hill in front reading as a warehouse. `ParkPlan` has
## said since the terraces were sited that `frontier` and `kiddieland` stand *on*
## the hill at `TERRACE_TWO_Y`; nothing drew their ground, so the plan's east
## shelf existed for thirty metres of its hundred-and-ninety and stopped at a
## sawn face on both sides.
##
## The shoulder is that shelf: the plateau's own rolled ground continuing to each
## footprint's far edge, a west face coming down at the ravine's own
## `CLIMB_BANK_BATTER`, and a descent at the far end so the landform ends by
## reaching the ground rather than by being cut off. The built terraces are then
## cuts *in* the hillside rather than architecture in front of it, which is what
## the plan's prose always described.
##
## **The west face cannot reach the ground where the `ne` and `se` passages
## stand, and the ravine's own rule answers it**: a slope that cannot fit stands
## up as a wall. Behind each passage the foot of the slope is a retaining wall at
## `SHOULDER_FOOT_X`, tall enough that the batter above it still lands on the
## plateau at `HILL_FACE_X`; past the passage the wall steps down and the batter
## runs out to its natural toe. The wall line is chosen off the emitted
## thresholds scene, not off the plan: the passages reach x 61.0 at their
## furthest (`way_ne_ahead`, `way_se_ahead`), and the wall's west face at 60.7
## laps their back walls without entering anybody's interior.
##
## **One height function and everything reads it.** `_shoulder_y` is min() of
## three surfaces — the west face, the plateau via `_east_ground_y`, the far
## descent — so the hips where they meet are a consequence rather than a seam,
## and the masonry samples the same function the mesh does, which is
## `_east_bank_y`'s rule about two things standing on one slope.
const SHOULDER_BATTER := 1.4
const SHOULDER_FOOT_X := 61.55
const SHOULDER_TRANS_D := 6.0
const SHOULDER_STEP_Z := 2.0
const SHOULDER_WEST_X := 50.3
const SHOULDER_BOW := 0.7


## Where the west face's foot stands at a station, as (x, y).
##
## Inside the wall band it is the retaining wall's earth line at the wall's own
## top; past it the foot eases out to the natural toe over `SHOULDER_TRANS_D`,
## which is the span the stepped end of the wall covers. The wall-top height is
## derived, not chosen: it is exactly the height the batter cannot lay back over
## the run between the wall and the brow, so the face always lands on the
## plateau at `HILL_FACE_X` — `CLIMB_BANK_MAX_D`'s arithmetic at the other scale.
func _shoulder_foot(dist: float, wall_to: float) -> Vector2:
	var top: float = Plan.TERRACE_TWO_Y + GROUND_LIFT
	var wall_y: float = top - (Plan.HILL_FACE_X - SHOULDER_FOOT_X) / SHOULDER_BATTER
	var toe_x: float = Plan.HILL_FACE_X - top * SHOULDER_BATTER
	if dist <= wall_to:
		return Vector2(SHOULDER_FOOT_X, wall_y)
	var t := clampf((dist - wall_to) / SHOULDER_TRANS_D, 0.0, 1.0)
	t = t * t * (3.0 - 2.0 * t)
	return Vector2(lerpf(SHOULDER_FOOT_X, toe_x, t), wall_y * (1.0 - t))


## The finished level of the shoulder at a point on it.
##
## Three surfaces, lowest wins. The west face and the descent are both bowed for
## `_east_bank_y`'s reason — a welded planar batter has one normal and therefore
## one tone, which is a ramp and not land — and the bow is zero at the foot and
## the brow by the same construction, because those lines are where the masonry
## and the plateau are. The descent's brow carries a fixed-sine jag so the far
## end of the landform is not a ruled line, which is `_hill_roll`'s reason for
## being deterministic: the coplanar report must not change under its reader.
func _shoulder_y(x: float, z: float, side: float, prm: Dictionary) -> float:
	var axis: float = Plan.ARCH_AT.y
	var dist := (z - axis) * side
	var top: float = Plan.TERRACE_TWO_Y + GROUND_LIFT
	var f := _shoulder_foot(dist, float(prm["wall_to"]))
	var fw := f.y + (x - f.x) / SHOULDER_BATTER
	if fw > f.y and fw < top:
		var t := (fw - f.y) / maxf(top - f.y, 0.001)
		fw += sin(t * PI) * SHOULDER_BOW * (0.62 + 0.38 * sin(z * 0.37))
	# The descent is cut from the *local* ground, not from the bench height:
	# the plateau ramps from 12 at the bench to 18 behind the head, and a
	# descent measured off the constant 12 would clamp the entire shoulder to
	# bench level and the ramp would never have existed east of the brow.
	var p := _east_ground_y(x, z)
	var nd := p
	var brow: float = float(prm["brow"]) \
		+ (sin(x * 0.17) * 0.6 + sin(x * 0.29 + 1.7) * 0.4) * 1.6
	if dist > brow:
		nd = p - (dist - brow) / SHOULDER_BATTER
		var tn := clampf((p - nd) / maxf(p, 0.001), 0.0, 1.0)
		nd += sin(tn * PI) * SHOULDER_BOW * (0.62 + 0.38 * sin(x * 0.31))
	return minf(minf(fw, p), nd)


## The two sides differ in more than sign, and the differences are all read off
## the neighbours rather than chosen. North: the court's own north-east corner is
## open ground (the court slab reaches z -28 but the walkable court stops at the
## ne passage's flank), so the shoulder carries a corner band of bank rows over
## it, and the wall band runs to one metre past the passage's north end at
## z -42.9. South: the se passage's flank *is* the court's south edge, so there
## is no corner band, and the hill skin's own edge at z +24 is the boundary. The
## far edges are `frontier`'s and `kiddieland`'s footprints less the descent.
func _shoulder_prm(side: float) -> Dictionary:
	if side < 0.0:
		return {
			"corner": true,
			"rows_head": PackedFloat32Array([-18.8, -20.6, -22.4, -24.2,
				-26.0, -27.85, -28.9]),
			"wall_to": 42.0,
			"brow": 92.0,
			"end": 124.0,
			"ret_z": -18.8,
			"ret_face": 1.0,
			"wall_z0": -44.0,
			"wall_z1": -18.4,
		}
	return {
		"corner": false,
		"rows_head": PackedFloat32Array([23.9, 24.55, 26.4]),
		"wall_to": 48.5,
		"brow": 90.0,
		"end": 122.0,
		# 24.6 rather than the wall band's own 24.9: the hill skin's south edge is
		# z 24.0, and a return wall centred with the retaining wall left a 0.4m
		# slot between its north face and the scarp's south jamb that read as a
		# green slit from the court. 0.1m of clearance to the skin edge closes it.
		"ret_z": 24.6,
		"ret_face": -1.0,
		"wall_z0": 24.4,
		"wall_z1": 46.5,
	}


## One shoulder: the mesh, the masonry at its foot, and the planting on it.
##
## The mesh is `_east_earth`'s construction — an x-sweep of shared columns,
## strips laid by `_earth_strip`, one trimesh body — with the rows in z instead
## of four named lines, because a shoulder is all ground and has no crease to
## keep. Where it meets the hill skin it tucks 7cm *under* the skin's last tenth
## of a metre rather than sharing the edge line vertex for vertex: two meshes
## that sample one function still normal their shared boundary from their own
## quads only, and a tucked lap hides that seam the way every butt joint in the
## park hides its own.
##
## The open west edge is handled three ways by band, and each edge lands in
## masonry or below the world: wall-band rows stop at the column inside the
## retaining wall; transition rows stop at the moving foot, inside the stepped
## end; open rows run their batter past y 0 to a buried toe, `RIM_TOE_BURY`'s
## trick at a tenth of the depth.
func _east_shoulder(side: float, tag: String) -> void:
	var axis: float = Plan.ARCH_AT.y
	var prm := _shoulder_prm(side)
	var wall_to := float(prm["wall_to"])

	var cols := PackedFloat32Array()
	var cx: float = SHOULDER_WEST_X
	while cx < EARTH_TO_X - 0.6:
		cols.append(cx)
		cx += EARTH_STEP
	cols.append(EARTH_TO_X)

	var rows := PackedFloat32Array()
	for r in prm["rows_head"]:
		rows.append(float(r))
	var d: float = absf(rows[rows.size() - 1] - axis)
	while d + SHOULDER_STEP_Z < float(prm["end"]):
		d += SHOULDER_STEP_Z
		rows.append(axis + side * d)
	rows.append(axis + side * float(prm["end"]))

	var lines: Array[PackedVector3Array] = []
	for zi in rows.size():
		var z: float = rows[zi]
		var dist := (z - axis) * side
		var line := PackedVector3Array()
		for c in cols:
			var h := _shoulder_y(c, z, side, prm)
			# The tuck under the hill skin. 26.05 is just past the skin's own
			# half-width of 26, so only rows lying under its edge dip.
			if dist < 26.05 and c > 69.9:
				h -= 0.07
			line.append(Vector3(c, h, z))
		lines.append(line)

	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.set_smooth_group(0)
	for j in lines.size() - 1:
		var dmid := ((rows[j] + rows[j + 1]) * 0.5 - axis) * side
		var wlim := -1.0e9
		var elim := 1.0e9
		if dmid <= wall_to:
			wlim = SHOULDER_FOOT_X - 0.15
		elif dmid < wall_to + SHOULDER_TRANS_D:
			wlim = _shoulder_foot(dmid, wall_to).x - 0.2
		if bool(prm["corner"]) and dmid < 25.95:
			# The corner band reaches the tuck column and no further: east of it
			# the skin already owns the ground.
			elim = 71.6
		if not bool(prm["corner"]) and dmid < 26.35:
			# The south's one sliver of tuck strip. Bank quads here would hang
			# over the court's own lip, so only the plateau lap is laid.
			wlim = 69.9
		var keep := PackedByteArray()
		for c in cols:
			keep.append(1 if c >= wlim and c <= elim else 0)
		_earth_strip(st, lines[j], lines[j + 1], side, float(j), keep)
	st.generate_normals()
	st.generate_tangents()
	var mesh := st.commit()

	var body := StaticBody3D.new()
	_add(body, "east_shoulder_%s" % tag)
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = mats["planting"]
	mi.name = "skin"
	body.add_child(mi)
	mi.owner = _root
	var shape := CollisionShape3D.new()
	shape.shape = mesh.create_trimesh_shape()
	shape.name = "shape"
	body.add_child(shape)
	shape.owner = _root

	_shoulder_masonry(side, tag, prm)
	_shoulder_blooms(side, tag, prm)


## The retaining wall behind the passage, its stepped end, and the return wall
## at the court corner — the masonry that lets the hillside stop where walkable
## ground needs the room.
##
## Every top is sampled from `_shoulder_y` plus a freeboard rather than written
## down, which is the setback lesson: a height written as a number has to be
## re-checked every time the slope behind it changes, and nobody ever does.
func _shoulder_masonry(side: float, tag: String, prm: Dictionary) -> void:
	var axis: float = Plan.ARCH_AT.y
	var z0 := float(prm["wall_z0"])
	var z1 := float(prm["wall_z1"])
	var wall_top := _shoulder_foot(0.0, float(prm["wall_to"])).y + 0.42
	_box("shoulder_wall_%s" % tag, Vector3.ZERO,
		Vector3(61.225, (wall_top - 0.55) * 0.5 - 0.275, (z0 + z1) * 0.5),
		Vector3(1.05, wall_top + 0.55, absf(z1 - z0)), "building")
	# Brick to head height on the exposed face, `_hill_brick`'s decision carried
	# to the one new retaining face the ground level can see.
	_box("shoulder_wall_brick_%s" % tag, Vector3.ZERO,
		Vector3(60.68, 1.1, (z0 + z1) * 0.5),
		Vector3(HILL_FACE_T, 3.0, absf(z1 - z0) - 0.6), "brick", 0.0, false)

	# The stepped end, three boxes walking the foot down to the toe. Spans and
	# tops both come off `_shoulder_foot`, laps are generous on purpose: these
	# cover the mesh's masked edge columns, and a step that stops where the edge
	# is leaves the edge showing the day the foot moves.
	var wall_to := float(prm["wall_to"])
	for k in 3:
		var d0 := wall_to + float(k) * 2.0
		var d1 := d0 + 2.4
		var f0 := _shoulder_foot(d0, wall_to)
		var f1 := _shoulder_foot(d1, wall_to)
		var xe: float = 61.75 if k == 0 else _shoulder_foot(d0 - 2.0, wall_to).x + 0.5
		var top := f0.y + 1.1
		var za := axis + side * d0
		var zb := axis + side * d1
		_box("shoulder_step_%s_%d" % [tag, k], Vector3.ZERO,
			Vector3((f1.x - 0.45 + xe) * 0.5, (top - 0.55) * 0.5 - 0.275,
				(za + zb) * 0.5),
			Vector3(xe - f1.x + 0.45, top + 0.55, absf(zb - za)), "building")

	# The return wall at the court corner: the cut face between the shoulder's
	# bank and the court floor, stepped up from the retaining wall to the scarp.
	# The court side gets the brick base the scarp's own faces wear.
	var rz := float(prm["ret_z"])
	var face := float(prm["ret_face"])
	var xs := PackedFloat32Array([60.7, 64.0, 67.2, 70.4])
	for k in 3:
		var xa := xs[k]
		var xb := xs[k + 1]
		var top := _shoulder_y(xb, rz + side * 1.1, side, prm) + 0.38
		_box("shoulder_ret_%s_%d" % [tag, k], Vector3.ZERO,
			Vector3((xa + xb) * 0.5, (top - 0.62) * 0.5 - 0.31, rz),
			Vector3(xb - xa, top + 0.62, 1.0), "building")
	_box("shoulder_ret_brick_%s" % tag, Vector3.ZERO,
		Vector3((60.9 + 70.2) * 0.5, 1.1, rz + face * 0.44),
		Vector3(70.2 - 60.9, 3.0, HILL_FACE_T), "brick", 0.0, false)


## Clumps on the bank, the ravine's planting rule at the shoulder's scale:
## groups of three small blooms, never singles, because one opaque sphere on a
## bare green plane is an egg on a lawn.
func _shoulder_blooms(side: float, tag: String, prm: Dictionary) -> void:
	var axis: float = Plan.ARCH_AT.y
	var d_from: float = 17.5 if bool(prm["corner"]) else 27.5
	var d_to := float(prm["brow"]) - 8.0
	for i in 14:
		var dist := lerpf(d_from, d_to, _hash01(i, 7, 43))
		var f := _shoulder_foot(dist, float(prm["wall_to"]))
		var hx := lerpf(f.x + 1.4, Plan.HILL_FACE_X - 1.0, _hash01(i, 11, 47))
		var hz := axis + side * dist
		var bloom: String = ["bloom_pale", "bloom_warm", "bloom_pink"][i % 3]
		for q in 3:
			var qx := hx + (_hash01(i * 7 + q, 19, 53) - 0.5) * 0.4
			var qz := hz + (_hash01(i * 7 + q, 23, 59) - 0.5) * 0.4
			_sphere("shoulder_bloom_%s_%d_%d" % [tag, i, q],
				Vector3(qx, _shoulder_y(qx, qz, side, prm) + 0.03, qz),
				Vector3.ZERO,
				0.055 + _hash01(q * 5 + i, 3, 29) * 0.055, bloom)


## The crest terraces: the walled garden court, moved from mid-climb to the
## head when the landings narrowed to pauses. One either side of the axis on
## the flat ground behind the last flight — the reference plate has structures
## at its crest, and an overlook is the honest first tenant for ground nothing
## is built on yet. Parapet-height brick with a coping, open toward the stair;
## the deck is paving-style — 12mm proud and no collision, because
## `CharacterBody3D` has no step-up and a kerb round a court is a wall.
func _climb_crest_courts() -> void:
	var axis: float = Plan.ARCH_AT.y
	var gy: float = Plan.CLIMB_HEAD_Y + GROUND_LIFT
	for s in 2:
		var side := -1.0 if s == 0 else 1.0
		var tag := "n" if s == 0 else "s"
		# East of the climb's head — the last flight tops out at `CLIMB_TO_X`
		# and a court overlapping the stair is a wall across it.
		var x0 := 109.6
		var x1 := 115.6
		var z0: float = axis + side * 7.5
		var z1: float = axis + side * 12.6
		_box("crest_court_deck_%s" % tag, Vector3.ZERO,
			Vector3((x0 + x1) * 0.5, gy - 0.058, (z0 + z1) * 0.5),
			Vector3(x1 - x0, 0.14, absf(z1 - z0)), "brick", 0.0, false)
		# Three parapets: the outer flank, the back, the west lip over the
		# climb. The stair side stays open — the court is entered off the head.
		var top := gy + 1.05
		for w in 3:
			var nm: String = ["flank", "back", "west"][w]
			var c: Vector3
			var sz: Vector3
			if w == 0:
				c = Vector3((x0 + x1) * 0.5, 0.0, z1 - side * 0.25)
				sz = Vector3(x1 - x0 + 0.0, 0.0, 0.5)
			elif w == 1:
				c = Vector3(x1 - 0.25, 0.0, (z0 + z1) * 0.5 + side * 0.06)
				sz = Vector3(0.5, 0.0, absf(z1 - z0) - 0.38)
			else:
				c = Vector3(x0 + 0.25, 0.0, (z0 + z1) * 0.5 + side * 0.06)
				sz = Vector3(0.5, 0.0, absf(z1 - z0) - 0.38)
			_box("crest_court_%s_%s" % [nm, tag], Vector3.ZERO,
				Vector3(c.x, (gy - 0.42 + top) * 0.5, c.z),
				Vector3(sz.x, top - gy + 0.42, sz.z), "brick")
			_box("crest_court_%scap_%s" % [nm, tag], Vector3.ZERO,
				Vector3(c.x, top + 0.055, c.z),
				Vector3(sz.x + 0.12, 0.12, sz.z + 0.12), "accent", 0.0, false)


## The head landing: the terrace at the top of the whole feature, between the
## head of the cutting and the rim's toe. `CLIMB_HEAD_TO_X` has named it since
## the climb doubled, and until 2026-08-23 nothing drew it — the ground past
## the head was rolling meadow to the toe, so the climb arrived at nothing in
## particular. `_hill_roll` holds the ground flat across the band
## (`HEAD_LAND_HALF` either side of the axis, out to `HEAD_LAND_TO_X`); this
## lays the floor: brick, because the east is one floor that happens to climb,
## in five slabs set out around the two crest courts so the courts stand *on*
## the terrace rather than beside it.
##
## Paving-style — 12mm proud of the skin, no collision, the crest court deck's
## own construction — because the skin underneath already collides and a slab
## the player could stand on is a kerb round the whole terrace. The slabs are
## gapped 15cm rather than butted or lapped: a butt is the zero-width seam, a
## lap of two identical tops is a coplanar pair, and at this depth the joints
## read as planting lines between pavements.
func _east_head_landing() -> void:
	var axis: float = Plan.ARCH_AT.y
	var gy: float = Plan.CLIMB_HEAD_Y + GROUND_LIFT
	var x0: float = Plan.CLIMB_TO_X + 0.25
	var x1: float = HEAD_LAND_TO_X
	# [tag, x0, x1, dz0, dz1] with dz off the axis. The margins clear the
	# courts' copings by at least 0.12 on every side — measured against
	# `_climb_crest_courts`' own offsets, not guessed.
	var slabs := [
		["w", x0, 109.40, -12.70, 12.70],
		["mid", 109.55, 115.55, -7.32, 7.32],
		["e", 115.78, x1, -12.70, 12.70],
		["n", x0, x1, -HEAD_LAND_HALF, -12.85],
		["s", x0, x1, 12.85, HEAD_LAND_HALF],
	]
	for s in slabs:
		var sx0 := float(s[1])
		var sx1 := float(s[2])
		var sz0: float = axis + float(s[3])
		var sz1: float = axis + float(s[4])
		_box("head_land_%s" % s[0], Vector3.ZERO,
			Vector3((sx0 + sx1) * 0.5, gy - 0.058, (sz0 + sz1) * 0.5),
			Vector3(sx1 - sx0, 0.14, sz1 - sz0), "brick", 0.0, false)


## How far up a retaining face the brick carries.
##
## **`_rear`'s finding, at the other end of the park.** The perimeter's back
## elevations were a grey cliff for the same reason these faces were: half of
## "featureless" is that a CSG box has no surface at all, and `brick` is the one
## warm material the park already has that is *textured* and world-triplanar, so
## it needs no UVs on a vertical face and tiles across a run's own joints.
##
## At the bottom rather than over the whole face, for `_rear`'s reason as well:
## it is the part the player is standing in front of, and the silhouette against
## the sky is left alone. Above head height, so that from the court and from
## inside the notch you are looking at brick and from the belvedere's parapet or
## the head of the climb you are looking down on grey.
const HILL_BRICK_H := 2.6

## How far a bay's paving is laid below the landing it opens off. See the note at
## `climb_bay_deck`, which is where the reasoning is.
## 0.019 rather than 0.012 since 2026-08-22: at the steeper climb the first
## south bay's deck top landed on the same plane as the neighbouring flight's
## first tread, in the 6cm strip where the deck laps the reach boundary. Still
## a construction tolerance underfoot, still far above the tester's floor.
const BAY_DECK_DROP := 0.019

## How far a bed's mass stops below the slab laid over it: half a basin's fall
## plus the slab's own thickness, so a flat top clears a falling one across its
## whole span. See the note in the garden block.
const BED_MASS_DROP := 0.42

## How far short of `CLIMB_BED_TO` the planting stops, so that the kerb standing
## on that line is the outermost thing rather than sharing its face.
const BED_KERB_TUCK := 0.06

## How far a landing's mass stops below its own paving, and how far that paving
## laps past the mass on each side. See `climb_land`.
const LAND_MASS_DROP := 0.02
const LAND_TOP_LAP := 0.2

## How far a facing stands proud of the wall it faces, and how thick it is.
##
## Proud rather than flush, because flush is the coplanar case and the house rule
## is that parts run into each other. The thickness is more than the projection,
## so the back of every facing is buried in the mass rather than sitting on it.
const HILL_FACE_OUT := 0.10
const HILL_FACE_T := 0.24


## The brick to head height on every face that retains the east hill.
##
## Five surfaces, and they are one decision rather than five: the scarp either
## side of the monument, the notch's three walls, and — by recolour rather than
## by facing, since it is shorter than the brick would be — the low wall at the
## foot of each bank in the ravine. What they have in common is that they are all
## the cut face of the same hill, and until now they all wore `building`, which
## is the *plaza perimeter's* grey. So the thing the whole east sequence climbs
## into was the colour of the wall it had just walked through.
##
## **It is the forecourt that makes this more than a preference.** Standing in
## the court you have the plaza's own rear elevations behind you — brick to the
## first floor since 2026-08-20 — and this scarp in front, fourteen metres apart
## and facing each other. Two retaining greys with one brick base between them
## read as two places; brick on both reads as one.
func _hill_brick(x0: float, x1: float, y1: float, gz0: float, gz1: float,
		sz0: float, sz1: float) -> void:
	var axis: float = Plan.ARCH_AT.y
	var out := HILL_FACE_OUT
	var t := HILL_FACE_T
	# The scarp, north and south of the monument. Twelve metres of it either
	# side, and the largest blank surface anywhere in the east.
	#
	# Bottomed below the court's own slab rather than on it: at y = 0 its
	# underside lands on the court's top face, and a plinth that stops exactly at
	# the ground is the one that looks wrong anyway. `_rear` says the same.
	for k in 2:
		var a: float = gz0 if k == 0 else sz1
		var b: float = sz0 if k == 0 else gz1
		_box("scarp_brick_%s" % ("n" if k == 0 else "s"), Vector3.ZERO,
			Vector3(x0 + t * 0.5 - out, (HILL_BRICK_H - 0.3) * 0.5,
				(a + b) * 0.5),
			Vector3(t, HILL_BRICK_H + 0.3, b - a - 0.4), "brick", 0.0, false)
	# The notch's two side walls, from the shelf's deck up. Started clear of the
	# parapet at the west end so the facing stops short of it rather than running
	# into its back.
	for k in 2:
		var z: float = sz0 if k == 0 else sz1
		var side := 1.0 if k == 0 else -1.0
		_box("notch_brick_%s" % ("n" if k == 0 else "s"), Vector3.ZERO,
			Vector3((x0 + Plan.SHELF_PARAPET_T + x1) * 0.5,
				y1 + (HILL_BRICK_H - 0.3) * 0.5, z + side * (t * 0.5 - out)),
			Vector3(x1 - x0 - Plan.SHELF_PARAPET_T - 0.3, HILL_BRICK_H + 0.3, t),
			"brick", 0.0, false)
	# The notch's east wall, in two pieces either side of the ravine's mouth —
	# the same five metres of jamb `_shelf_buttresses` keeps its pilasters on. A
	# facing run the full width would cross the opening as a band hanging in it,
	# which is what `shelf_course_e` is already in two pieces to avoid.
	var mouth: float = Plan.CLIMB_OPEN_HALF
	for k in 2:
		var a: float = sz0 if k == 0 else axis + mouth
		var b: float = axis - mouth if k == 0 else sz1
		if b - a < 0.5:
			continue
		_box("notch_brick_e_%s" % ("n" if k == 0 else "s"), Vector3.ZERO,
			Vector3(x1 - t * 0.5 + out, y1 + (HILL_BRICK_H - 0.3) * 0.5,
				(a + b) * 0.5),
			Vector3(t, HILL_BRICK_H + 0.3, b - a - 0.3), "brick", 0.0, false)


## One piece of the hill's mass, given the finished level of its top.
##
## **It lays its mass to a cap's thickness below that level**, which is the whole
## reason it takes the finished number rather than its own. Every call site then
## reads as the terrace height the plan states, and the offset that keeps the cap
## and the mass off one plane lives in one place instead of at three call sites
## where the fourth would eventually be written without it.
func _hill_block(nm: String, x0: float, x1: float, y0: float, top: float,
		z0: float, z1: float) -> void:
	# **To the finished level, not a cap's thickness under it.** It stopped short
	# while a flat `planting` plate went on top; the plate is a mesh now and floats
	# `GROUND_LIFT` over this, so stopping short only leaves a slot.
	var y1 := top
	_box(nm, Vector3.ZERO,
		Vector3((x0 + x1) * 0.5, (y0 + y1) * 0.5, (z0 + z1) * 0.5),
		Vector3(x1 - x0, y1 - y0, z1 - z0), "building")




## The one step from the monument onto the hill.
##
## Its own box because the shelf's deck stops dead on the scarp line: the deck's
## west face *is* the top of the scarp, which is what lets the parapet stand on
## the line rather than inboard of it, and what keeps brick out of the cascade's
## planted banks for the other forty metres of that edge. So the doorway is the
## one place the two floors have to meet, and this is the piece that laps them.
##
## A coplanar butt leaves a zero-width seam for the capsule to catch on, and this
## is the single stride every route onto the shelf passes through — the worst
## possible place to leave one. It runs two metres back over the landing's deck
## and a metre out over the shelf's, and all three tops sit at `HILL_TOP` with
## only the build-order displacement between them, which is exactly the case that
## displacement is for.
func _east_hill_sill(axis: float, x0: float, y1: float) -> void:
	var half := Plan.LANDING_HALF_W
	_box("shelf_sill", Vector3.ZERO,
		Vector3(x0 - 0.5, y1 - SHELF_DECK_T * 0.5, axis),
		Vector3(3.0, SHELF_DECK_T, half * 2.0), "brick")


## Pilasters up the notch's three walls.
##
## **The same answer the bluff already gave to the same question.** A retaining
## face gets a coping and buttresses on the stretch that is seen and nothing on
## the stretch that is not, and this hill inverted that by accident: the wall a
## player can put their hand on is the one inside the notch, and it went in as
## 36m by 6m of flat grey. Blank is honest for a surface at eighty metres and it
## is the boardwalk's back-lane problem at twelve.
##
## They stop at the terrace cap's underside rather than at the terrace level. A
## buttress run the full height would stand half a metre proud of the green
## above the wall, which reads as a post somebody left there rather than as the
## wall thickening — the same lump that killed four separate shoulders at the
## cascade's wing junction.
func _shelf_buttresses(x0: float, x1: float, y1: float, y2: float,
		sz0: float, sz1: float) -> void:
	const W := 1.0
	const D := 0.4
	var top := y2 - TERRACE_CAP_T
	var mid := (y1 - 0.2 + top) * 0.5
	var h := top - y1 + 0.2
	# North and south, across the notch's depth. Started clear of the parapet so
	# the first one is not half-buried in it.
	for k in 2:
		var z: float = sz0 + D * 0.5 if k == 0 else sz1 - D * 0.5
		var tag := "n" if k == 0 else "s"
		for i in 4:
			var x := x0 + 2.6 + float(i) * 4.3
			_box("shelf_butt_%s_%d" % [tag, i], Vector3.ZERO,
				Vector3(x, mid, z), Vector3(W, h, D), "building", 0.0, false)
	# The east wall, which is the one you face when you turn round — and which
	# has the ravine's mouth in it since the climb went in, so five of the seven
	# stood in open air. Skipped rather than re-spaced: the survivors are the
	# jambs, and moving them to spread evenly over what is left would put a
	# pilaster where the wall stops instead of where the opening starts.
	var mouth: float = Plan.CLIMB_OPEN_HALF
	for i in 7:
		var z: float = sz0 + 3.0 + float(i) * 5.0
		if absf(z - Plan.ARCH_AT.y) < mouth + D:
			continue
		_box("shelf_butt_e_%d" % i, Vector3.ZERO,
			Vector3(x1 - D * 0.5, mid, z), Vector3(D, h, W), "building", 0.0, false)

	# **And a string course, because the pilasters alone drew nothing.**
	#
	# Built, shot, and invisible: 0.4m of relief in the wall's own colour, on a
	# west-facing face at half past three with the sun straight down it. No
	# shadow, no value change, no line — a flat grey wall with flat grey lumps
	# on it. Depth was the wrong lever and more depth would have been more of the
	# wrong lever, because the thing missing was not shape.
	#
	# The cascade settled this already and the note is in `trim`: a string course
	# is the most legible thing in every photograph of the reference, and it works
	# by *value* rather than by relief. So this is `accent` — the parapet's own
	# coping colour, carried round the other three sides, which also stops the
	# notch reading as a brick floor in a grey box with one terracotta edge.
	#
	# The pilasters stay. They do nothing at noon and they do the whole job at
	# ten and at seven, when the sun rakes this wall instead of facing it — which
	# is exactly the two hours a photographer is up here.
	var cy := y1 + (top - y1) * 0.62
	const CD := 0.26
	const CH := 0.3
	for k in 2:
		var z: float = sz0 + CD * 0.5 if k == 0 else sz1 - CD * 0.5
		_box("shelf_course_%s" % ("n" if k == 0 else "s"), Vector3.ZERO,
			Vector3((x0 + x1) * 0.5, cy, z),
			Vector3(x1 - x0, CH, CD), "accent", 0.0, false)
	# In two pieces, either side of the ravine's mouth. A course that ran the
	# full width would cross the opening as a bar hanging in it.
	var eax: float = Plan.ARCH_AT.y
	for k in 2:
		var a: float = sz0 if k == 0 else eax + Plan.CLIMB_OPEN_HALF
		var b: float = eax - Plan.CLIMB_OPEN_HALF if k == 0 else sz1
		if b - a < 0.3:
			continue
		_box("shelf_course_e_%s" % ("n" if k == 0 else "s"), Vector3.ZERO,
			Vector3(x1 - CD * 0.5, cy, (a + b) * 0.5),
			Vector3(CD, CH, b - a), "accent", 0.0, false)


## The cascade: a landing at the head, a trapezoid facade under it, and a wing
## hairpinning down each side. See `ParkPlan.LANDING_D` for the plan and why
## every earlier version failed to read.
##
## **There are two of these, and this builds either.** `ParkPlan.CASCADE_WEST`
## falls off the bluff to the boardwalk; `ParkPlan.CASCADE_EAST` climbs the rim
## to the first terrace. They are the same object at two sites rather than two
## objects, because a cascade's face is always on its low side — so both face
## west, downhill is −x on both, and the east one is the west one *translated*
## rather than mirrored. See `ParkPlan.CASCADE_EAST`.
##
## Which means everything below reads its position out of `site` and its shape
## out of the shared constants. If you find yourself adding a number here that
## differs between the two, it belongs in the site dict.
func _cascade(site: Dictionary) -> void:
	# Cleared rather than trusted, for the reason `_begin_scene` clears
	# `_stand_clear`: this is the only scene that fills it, and a leftover entry
	# would hang a lamp in mid-air over a wing that no longer exists. **And with
	# two sites it is no longer merely hygiene** — the register is filled by one
	# cascade and read by the next one built, so without this the east's lamps
	# would stand on the west's rails.
	_cascade_rails.clear()
	# **The east's treads are brick and the west's are not.** The east cascade
	# stands on the plaza's own floor and its court, forecourt and belvedere are
	# all brick, so a flat `accent` tread reads as orange plastic laid on a
	# textured ground. The west may not have it at any price: "no brick west of
	# the bluff" is a rule about the two sections disagreeing, and the boardwalk's
	# whole floor argument depends on it. Same monument, two grounds.
	_tread_mat = "brick" if String(site["tag"]) == "east" else "accent"
	_cascade_posts.clear()
	_cascade_landing(site)
	_cascade_wing(site, -1.0, true)
	_cascade_wing(site, 1.0, false)
	# **After the wings, because the crest reads off what they build.** It takes
	# the wing's gradient from `wing_leg_end` rather than from a number repeated
	# out of `wing_path`, so it wants a wing that already exists. The order also
	# matters to `_begin_scene`'s displacement, which is drawn in build order —
	# see the note there before moving any of these.
	_cascade_crest(site)
	_cascade_bank(site, -1.0)
	_cascade_bank(site, 1.0)
	_cascade_bed(site, -1.0)
	_cascade_bed(site, 1.0)
	# **Last of the geometry, and it belongs to the landing.** It is built here
	# rather than inside `_cascade_landing` for the reason `_begin_scene` states:
	# the seam displacement is handed out in build order and wraps at 21, so
	# thirty-odd nodes inserted at the head of this scene move every shape after
	# them cyclically and can put two untouched surfaces on one plane eighty
	# metres away. Adding at the end shifts nothing. Read `_cascade_landing`
	# first — that is where the hole this fills is cut.
	_cascade_niche(site)
	_cascade_lights(site)


## The landing at the head, the wall under it, the niche in that wall, and the
## three steps at its foot.
##
## The landing is **level with the bluff top**, so walking west off the terrace
## you step onto it without a riser and the drop begins only when you turn. Its
## west face is the trapezoid's middle horizontal.
func _cascade_landing(site: Dictionary) -> void:
	var axis: float = site["axis_z"]
	var wx: float = site["wall_x"]
	var half := Plan.LANDING_HALF_W
	# **`head` is the one addition the second site needed here**, and it is
	# invisible in the west's own numbers because the west's head is zero. Every
	# height in this function was written as a small negative — the deck at −0.25,
	# the string course at −0.52, the facing topping out at −0.15 — and all of them
	# meant "just under the head", not "just under sea level". At the east site the
	# head is +6 and a literal −0.25 would have built the landing six metres
	# underground. The floor is the other end of the same story: `base` and the
	# apron hang off it.
	var head: float = site["head_y"]
	var floor_y: float = site["floor_y"]
	var base := floor_y - 0.8
	var thick := Plan.CASCADE_WALL_THICK
	var face := wx - thick * 0.5

	# The deck, from the ground behind out to the wall — the bluff face at the
	# west site and the scarp at the east.
	#
	# **The fill's west face is the back of the niche, and that is why it is
	# written off `NICHE_DEEP` rather than off `wx`.** The recess is a hole in
	# this mass, not a rebate in the facing in front of it — so when the niche
	# got deep enough to stand a fountain in, the thing that had to move was the
	# fill. At 0.6 the two happened to coincide (`wx` is `face + 0.8`, which was
	# `NICHE_DEEP + 0.2`), and writing it as `wx` made a coincidence look like a
	# derivation. The 0.2 is a void behind the facing, left deliberately: butting
	# the fill against the facing's back would put the fill's ±Z faces on the
	# facing's over an overlapping span, and that is a fight rather than an
	# overlap.
	var d0: float = site["top_x"]
	var fill_x: float = face + Plan.NICHE_DEEP + 0.2
	_box("landing_fill", Vector3.ZERO,
		Vector3((d0 + fill_x) * 0.5, (base - 0.3 + head) * 0.5, axis),
		Vector3(absf(fill_x - d0), head - base + 0.3, half * 2.0), "building")
	_box("landing_deck", Vector3.ZERO,
		Vector3((d0 + wx) * 0.5, head - 0.25, axis),
		Vector3(absf(wx - d0), 0.5, half * 2.0), "accent")

	# The wall's facing, with the niche left out of it: two returns and a head.
	# Built rather than cut — the park has no CSG subtraction in its vocabulary.
	var nh: float = floor_y + Plan.NICHE_H
	for k in 2:
		var s := -1.0 if k == 0 else 1.0
		var z0: float = axis + s * Plan.NICHE_W * 0.5
		var z1: float = axis + s * half
		_box("landing_face_%d" % k, Vector3.ZERO,
			Vector3(face + Plan.NICHE_DEEP * 0.5, (base + head - 0.15) * 0.5,
				(z0 + z1) * 0.5),
			Vector3(Plan.NICHE_DEEP, head - 0.15 - base, absf(z1 - z0)),
			"cascade_face")
	_box("landing_face_head", Vector3.ZERO,
		Vector3(face + Plan.NICHE_DEEP * 0.5, (nh + head - 0.15) * 0.5, axis),
		Vector3(Plan.NICHE_DEEP, head - 0.15 - nh, Plan.NICHE_W), "cascade_face")
	# The head of the niche, stepped so it reads as an arch at greybox scale.
	#
	# **The inset grows with height, and it used to grow with `i`, which runs
	# downward.** `i` is the course index from the crown, so `0.26 + i * 0.28`
	# put the deepest corbel at the *bottom* of the head and the shallowest at
	# the top: the opening pinched as it went down and flared at the crown, which
	# is an arch upside down. It sat that way from the day it was written and was
	# invisible until the wall came in to 7m — at 14m the whole head was 17% of
	# the wall and read as a smudge, and the narrowing is what made it big enough
	# to see. A detail too small to check is a detail too small to be right.
	#
	# **They run the whole depth of the reveal, which is new and is the deep
	# niche's doing.** At 0.6 a corbel 1.2m through was mostly buried and it did
	# not matter what it did behind the face. At 1.5 the reveal is the biggest
	# thing about the opening, and a head that stops partway along it is an arch
	# with no soffit — from the court you would see the courses at the mouth and
	# a flat ceiling behind them.
	# **Scaled with the opening, because an inset written as a length stops being
	# an arch when the thing it is set into grows.** These were 0.26/0.54/0.82,
	# which took 68% of a 2.4m opening out at the top course and left 0.76m clear
	# — a strong arch. Left as absolutes against a 3.3m opening they would leave
	# 1.66m, and three small brackets under a wide flat head is a lintel, not an
	# arch. The ratio to `NICHE_W` is the thing that was actually chosen, so it is
	# the thing written down.
	var corbel_scale: float = Plan.NICHE_W / 2.4
	for i in 3:
		var inset := (0.26 + float(2 - i) * 0.28) * corbel_scale
		for k in 2:
			var s := -1.0 if k == 0 else 1.0
			_box("landing_niche_%d_%d" % [i, k], Vector3.ZERO,
				Vector3(face + (Plan.NICHE_DEEP + 0.2) * 0.5,
					nh - 0.2 * (float(i) + 0.5),
					axis + s * (Plan.NICHE_W * 0.5 - inset * 0.5)),
				Vector3(Plan.NICHE_DEEP + 0.2, 0.2, inset), "cascade_face")
	# **There is no string course, and its absence is the composition.** A `trim`
	# band ran the landing's full 7m at `head - 0.52` and carried on down both
	# wings from there — the brightest, most legible thing in every photograph of
	# the reference, and by that argument the last thing anybody would take off.
	#
	# What the argument left out is what this facade is *of*. `ParkPlan` says the
	# shape reads from the bottom as a ray with its wings spread, and a ray is one
	# unbroken surface: a horizontal across the middle falling away at both ends,
	# with two lit eyes on it and a mouth in the centre. A pale band tracing that
	# top edge a hand below it does not draw the creature's outline, it draws a
	# second outline parallel to the first — and where it crossed the globes it
	# turned two eyes into two beads threaded on a line. Dropping the globes clear
	# of it fixed the crossing and left the parallel line, which is the half of
	# the problem the band *is*.
	#
	# So the edge is drawn by the crest coping and the sky by day, and after dark
	# by the six `moon` floods and the two grazers that already exist for exactly
	# that job — see `_cascade_lights`, where the whole facade block was written
	# because the chevron had no light on it. Nothing there depended on the band;
	# the grazing aim did throw its shadow up the plane, and now it rakes a plane
	# with nothing on it to shadow, which is the one thing this costs.
	# The guard along the landing's own lip is `_cascade_crest` now — a parapet
	# between two piers rather than a rail across the whole 7m. See there.

	# The apron at the foot: one slab, wall to wing-feet, filling the pocket
	# between the two wings.
	#
	# **It was three.** `FOOT_STEPS` built three nested boxes, each a metre
	# further west and a metre wider, and every one of them topped out at the
	# same height — so they were never steps at all, they were one 3m plinth with
	# a staircase-shaped *plan*. Seen from the court that drew a zigzag edge with
	# a notch at each side, and a 20cm strip of asphalt between the plinth and
	# the wall it was supposed to be levelling up to. Nobody could have read it
	# as anything; it was three boxes doing one box's job in the wrong shape.
	#
	# The width comes from the block and the depth from the wings, so it meets
	# both by construction rather than by a number that has to be kept in step:
	# `half` either side of the axis lands it flush against the wing masses, and
	# the return leg's own foot slab sets how far west it reaches.
	#
	# **A hand past the feet, not flush with them, and the flush version was a
	# coplanar pair by derivation.** `wing_foot`'s west face is
	# `wing_path[3].x - (WING_W + 0.7) * 0.5`, and this was that same expression —
	# so the two slabs did not merely happen to line up, they were equal to the
	# bit. That is the one kind of fight the build-order hair cannot break: the
	# hair is a fraction of a millimetre handed out by ordinal, and it had been
	# hiding this pair for as long as the two shapes happened to land on different
	# ordinals. Taking the string course off the facade removed five nodes ahead of
	# them, every ordinal after it moved by five, and the pair surfaced in both
	# sites at once. 0.12 is enough to be an overlap and too little to be a step.
	var apron_far: float = Plan.wing_path(site, -1.0)[3].x \
		- (Plan.WING_W + 0.7) * 0.5 - 0.12
	# **Carried back to the back of the niche, not stopped at the wall's face.**
	# The apron used to end level with the front of the recess, which left a dark
	# strip of asphalt across the bottom of the opening — the one part of the
	# floor the arch actually frames. It now runs to `fill_x`, so the recess has
	# a stone floor for its whole depth; that was a nicety at 0.6 and is the
	# fountain's foundation at 1.5.
	var apron_near := fill_x
	# Brick, for the same reason the turn landings are: this is the ground in
	# front of the niche, it runs back under the fountain, and it is what the
	# arch of the recess frames along its bottom edge. In `accent` it was a slab
	# of plain orange under a warm-lit alcove and the two warms fought.
	_box("cascade_apron", Vector3.ZERO,
		Vector3((apron_near + apron_far) * 0.5, floor_y - 0.143, axis),
		Vector3(absf(apron_near - apron_far), 0.36, half * 2.0), "brick")
	# A band along its west edge. Without it the slab stops dead against the
	# asphalt and the court reads as having a rectangle painted on it; with it
	# the apron has an edge and the edge is the thing you see.
	_box("cascade_apron_edge", Vector3.ZERO,
		Vector3(apron_far + 0.09, floor_y - 0.128, axis),
		Vector3(0.18, 0.3, half * 2.0 - 0.1), "trim")


## The wall fountain in the niche.
##
## `ParkPlan` has said "the centre is water and the niche is blind — it is where
## the water comes out" since the flight came out of the middle, and until now
## nothing came out of it. The niche was a dark rectangle with a lamp in it.
##
## It is a **wall fountain**, not a scaled-down version of the plaza's: a bronze
## spout high under the arch, a bracketed half-basin catching it at chest height,
## two streams off that basin's ends, and a trough on the ground taking both. The
## plaza's is a free-standing object you walk round and the vocabulary that
## builds it is radial — rings of blocks, rings of falls, everything hung off one
## axis. Nothing here is radial, because a wall fountain has a back, and the back
## is the point: every part of it is cantilevered off one plane and the water
## falls down that plane in three stages. Reusing `_rim_ring` and `_veil` would
## have produced a small round fountain standing in a recess, which is a
## different object.
##
## What it does share is the **materials**, and that is deliberate rather than
## lazy. `fount_stone` is off the perimeter's hue by a measured margin and
## `fount_wet` is what says a surface has had water over it — the two of them are
## the park's existing answer to "this is masonry with water on it", and a second
## answer would just be a second warm grey. The water materials are its own; see
## `_fountain_materials` for why `centre` makes that mandatory.
##
## **Depth is what makes it a fountain rather than a relief.** At the old 0.6m
## recess every one of these parts would have stood proud of the facade: the
## trough alone is 1.65m deep. `NICHE_DEEP` went to 1.5 for this, and the whole
## assembly then sits *inside* the arch with only the trough's lip crossing the
## facade plane — which is what the reference photograph does and why the recess
## reads as having been hollowed out to hold something.
##
## Nothing above the trough collides. The trough is 0.89m of stone across the
## mouth of a recess nobody has any business standing in, so it is the barrier
## and the six parts behind it can be scenery. That is the fountain kerb's
## argument — 260 shapes inside the plaza's pool need no collision because 72
## ring blocks are a fence — made with three boxes instead of seventy-two.
func _cascade_niche(site: Dictionary) -> void:
	# The niche's own frame: the wall's west face, the floor it stands on, the
	# axis. Every number below is depth into the recess, height off the apron, and
	# offset from the axis, which is the only way this stays legible against a
	# wall at x = −63.8 on ground at y = −6, and the only reason the same
	# arithmetic serves a wall at x = 58.6 on ground at y = 0.
	var face: float = float(site["wall_x"]) - Plan.CASCADE_WALL_THICK * 0.5
	var o := Vector3(face, site["floor_y"], site["axis_z"])
	# **The water materials are the site's own**, for the reason written where
	# they are built: two of the four carry a world XZ centre and two a world Y
	# fade band, so there is a set per cascade and this picks the one belonging to
	# the cascade being built. The stones above are shared, because a
	# `StandardMaterial3D` carries no coordinates at all.
	var wet := "water_niche_%s" % site["tag"]
	# Where the recess ends. `_cascade_landing` cuts the fill back to
	# `NICHE_DEEP + 0.2`; the plate stands 0.025 west of that and is what the
	# player actually sees, so the clear depth is 1.475.
	var back := Plan.NICHE_DEEP - 0.025

	# --- the back ---
	#
	# A dressed panel rather than the bare fill, and wider than the opening so it
	# closes the 0.2m slot behind the reveals at both sides. It is also the one
	# surface in the recess that is lit, so it wants to be stone the fountain is
	# made of rather than the wall it is cut into.
	#
	# **Its height is `NICHE_H + 0.2`, and it was the literal 3.40 that number
	# happened to equal.** The plate has to reach past the head of the opening or
	# the top of the recess shows `landing_fill` — five metres of `building` grey
	# behind a lit terracotta panel. That held for as long as the opening was 3.2
	# and nothing said so; the width beside it was already written as a relation
	# to `NICHE_W`, which is the tell that the height was the odd one out.
	var plate_h: float = Plan.NICHE_H + 0.2
	_box("niche_plate", o, Vector3(back + 0.275, plate_h * 0.5, 0.0),
		Vector3(0.55, plate_h, Plan.NICHE_W + 0.5), "niche_face")
	# The wetted band down the middle of it, standing 5cm proud. It costs one box
	# and it is the only thing that says the water has been running for twenty
	# summers — the alternative was staining the stone, which greybox cannot do.
	# From the bowl's underside to the trough's lip, because that is the stretch
	# the two falls run past rather than the whole plate.
	_box("niche_stain", o, Vector3(back - 0.03, 1.30, 0.0),
		Vector3(0.06, 1.48, 1.50), "niche_wet", 0.0, false)

	# --- the trough ---
	#
	# Body, bed, and three rim walls. Three and not four: the fourth is the plate
	# and a rim against it would be a course of stone nobody can see from any
	# standpoint in the park.
	var tw := 0.675  # centre of the trough in depth
	_box("trough_body", o, Vector3(tw, 0.30, 0.0), Vector3(1.65, 0.60, 2.00),
		"niche_stone")
	_box("trough_bed", o, Vector3(0.70, 0.65, 0.0), Vector3(1.40, 0.14, 1.76),
		"fount_bed", 0.0, false)
	# Overhanging the body by 7cm, for the reason the plaza pool's coping does:
	# the shadow line under a lip is what makes masonry read as cut stone.
	_box("trough_rim_w", o, Vector3(-0.14, 0.74, 0.0), Vector3(0.16, 0.30, 2.14),
		"niche_wet")
	for k in 2:
		var s := -1.0 if k == 0 else 1.0
		_box("trough_rim_%d" % k, o, Vector3(tw, 0.74, s * 0.99),
			Vector3(1.79, 0.30, 0.16), "niche_wet")
	# 6cm of freeboard. Brimmed to the rim a trough reads as a painted panel.
	#
	# `trough_top` is published for everything that lies on this water — the
	# froth, the lamp glows — because those were typed as absolute heights and one
	# of them was then written against a surface that had already moved.
	var trough_top := 0.74 + 0.18 * 0.5
	_water_box("trough_water", o, Vector3(0.70, 0.74, 0.0),
		Vector3(1.48, 0.18, 1.82), wet)

	# --- the basin on the wall ---
	#
	# A corbel, a stepped underside and three rim walls, all cantilevered off the
	# plate. The underside is the part that does the work: this is seen from
	# below by anybody standing in the court, so what reads is its shadow and its
	# projection, not the dish.
	#
	# **It sits a quarter-metre higher than the first build put it.** At 1.6 the
	# gap between the basin's underside and the trough's lip was 0.6m and the two
	# falls in it were shorter than they were wide apart — three stages that read
	# as two objects with a smear between them. Falling water needs *height* to
	# be falling water, and the niche is 3.2m tall with nothing else asking for
	# the top of it.
	_box("bowl_corbel", o, Vector3(1.32, 1.56, 0.0), Vector3(0.42, 0.34, 0.85),
		"niche_stone", 0.0, false)
	_box("bowl_under", o, Vector3(1.24, 1.82, 0.0), Vector3(0.58, 0.20, 1.36),
		"niche_stone", 0.0, false)
	_box("bowl_rim_w", o, Vector3(1.02, 2.05, 0.0), Vector3(0.14, 0.28, 1.42),
		"niche_wet", 0.0, false)
	for k in 2:
		var s := -1.0 if k == 0 else 1.0
		_box("bowl_rim_%d" % k, o, Vector3(1.24, 2.05, s * 0.64),
			Vector3(0.58, 0.28, 0.14), "niche_wet", 0.0, false)
	var bowl_top := 2.04 + 0.16 * 0.5
	_water_box("bowl_water", o, Vector3(1.31, 2.04, 0.0),
		Vector3(0.44, 0.16, 1.28), "%s_bowl" % wet)

	# --- the spout ---
	#
	# A boss on the wall and a lip out of it, 2.5m up under the arch's head. Two
	# boxes rather than a cylinder, and that is a limit of the primitives rather
	# than a choice: `_cyl` stands on its own Y and pointing one west would mean
	# composing the offset in a rotated frame for a fitting 30cm long. A
	# flattened bronze tongue is what the reference has anyway.
	_box("spout_boss", o, Vector3(1.42, 2.80, 0.0), Vector3(0.22, 0.30, 0.34),
		"fount_bronze", 0.0, false)
	_box("spout_lip", o, Vector3(1.20, 2.72, 0.0), Vector3(0.30, 0.12, 0.26),
		"fount_bronze", 0.0, false)

	# --- the water in the air ---
	#
	# Three streams, all vertical. An arc is what the photograph shows and what
	# this cannot have: an arc is four segments per stream and it lands wherever
	# the last one stops, which is the argument `_fountain_jets` already settled
	# for the plaza's ring. Vertical, each one starts inside the thing above it
	# and fades out just above the thing below it, so neither end is an edge.
	_water_cyl("spout_stream", o, Vector3(1.10, 2.40, 0.0), 0.055, 0.58,
		"%s_spout" % wet, 8)


	for k in 2:
		var s := -1.0 if k == 0 else 1.0
		# **West of the basin's front rim, not behind it.** They started at the
		# corners of the well, which is where a real overflow would be and which
		# put both of them behind 14cm of stone: from the court — the standpoint
		# the whole monument is judged from — the middle stage of the fountain was
		# simply missing, and it was visible only from close enough to be looking
		# up into the basin. A fall has to clear the lip it comes off.
		_water_cyl("bowl_fall_%d" % k, o, Vector3(0.90, 1.28, s * 0.62),
			0.048, 0.98, "%s_fall" % wet, 8)
		# Smaller than they were. At 0.20 a pair of 40cm discs on a 1.5m trough
		# read as two lily pads rather than as the water being disturbed.


	# --- the lights in the water ---
	#
	# **There is no geometry here, and that is the fix.** Three builds put the
	# glow on a disc lying on the surface — 4cm thick, then 13mm, then a small
	# lens inside a rippling halo — and every one came back with the same note:
	# they sit on top of the water. They did. A patch laid on a surface is a
	# second surface, with its own height, its own rim, its own shading and, once
	# the halo wore the pool shader, its own rings radiating from its own centre
	# while the water's radiated from the fountain's.
	#
	# The water draws them now: see `lamps` in `water_pool.gdshader` and the two
	# materials in `_fountain_materials`. Nothing can float, because nothing is
	# there. What is left in this function is the *stone* the light comes out
	# from under, and the spots that do the uplighting are in `_cascade_lights`.

	# --- what stands either side of it ---
	#
	# Two pots against the facade, flanking the opening. They are outside the
	# reveals rather than in the recess, so they frame the arch instead of
	# crowding what is in it, and they are the same `planting`/`bloom` vocabulary
	# `_cascade_bed` uses twenty metres away — which is the point. The monument's
	# planting is what makes it a garden rather than civil engineering, and the
	# fountain is the one part of it at arm's length.
	for k in 2:
		var s := -1.0 if k == 0 else 1.0
		var z := s * (Plan.NICHE_W * 0.5 + 0.52)
		_cyl("niche_pot_%d" % k, o, Vector3(-0.48, 0.29, z), 0.36, 0.58,
			"niche_stone", 0.0, 12)
		_cyl("niche_pot_soil_%d" % k, o, Vector3(-0.48, 0.60, z), 0.30, 0.10,
			"planting", 0.0, 12, false)
		for i in 4:
			var a := TAU * (float(i) + 0.5) / 4.0
			_sphere("niche_bloom_%d_%d" % [k, i], o,
				Vector3(-0.48 + cos(a) * 0.17, 0.72 + _hash01(k * 7 + i, 3, 31) * 0.14,
					z + sin(a) * 0.17),
				0.16 + _hash01(i, 5, 37) * 0.10,
				["bloom_pale", "bloom_warm", "bloom_pink"][(k + i) % 3])


## The crest: the line along the top of the whole monument, and the one thing in
## the reference photographs your eye actually follows.
##
## It used to be a single handrail straight across the landing's lip for the full
## 7m, which is the one arrangement the photograph does not show. What is there
## instead is three parts:
##
## 1. **Two piers**, standing taller than the crest and a little proud of it,
##    framing the middle. They are what makes the centre read as an opening
##    rather than as the blank part of a wall.
## 2. **A rail** filling the whole span between them. With no parapet in that
##    span the rail is the guard on a 6m drop rather than decoration on top of
##    one, which is why it is three horizontals and six posts.
## 3. **A globe under each pier**, and it is the only fitting on the monument
##    whose geometry is its own light source.
##
## **There is no shoulder, and this docstring described one for longer than the
## code had one.** Four were built into the gap outboard of the piers on
## 2026-08-16 — a quadratic fillet, a concave flare, a cubic S rolling off a
## raised ledge, and a straight bevel — and all four came out. Every one of them
## needed a lump of raised wall carried out over the wing to spring from, and the
## lump was the fault each time: from the court it read as a block sitting on the
## wing rather than as the wing's own top edge doing something. Removing only the
## curve and leaving the ledge it stood on does not help; that was tried.
##
## The junction is a plain corner. The block's top is the landing deck, the wings
## spring straight off it, and nothing stands outboard of the piers.
##
## Two things worth keeping from the attempts, because both are true and neither
## is in the code any more. A quadratic tangent to the horizontal at one end and
## to the wing at the other has its control point where those two tangents cross,
## which is fixed at `crest height / gradient` inboard of the wing head — so the
## curve silently decides how far out the piers may stand, and moving a pier past
## it puts the control point behind the start of the curve. And a curve sampled
## into upright slices draws a staircase when the sampled edge *is* the
## silhouette; it needs thin plates laid along each chord, which is only safe
## because a slice is short enough that tilting swings its corners by
## centimetres. See `_cascade_wing` for the version of that argument where the
## box was 5.9m tall and it went the other way.
func _cascade_crest(site: Dictionary) -> void:
	var axis: float = site["axis_z"]
	var half := Plan.LANDING_HALF_W
	var face: float = site["wall_x"] - Plan.CASCADE_WALL_THICK * 0.5
	# Everything in this function stands *on* the block's top, so every height
	# below is measured up from `head` rather than from zero. At the west site the
	# two are the same number, which is exactly why they were never distinguished.
	var head: float = site["head_y"]

	# The band the whole crest is cut from, standing 5cm proud of the wall face
	# so it reads as a coping and — the reason it is 5cm and not 0 — so its west
	# face is not on the same plane as the wall's and the wing mass's, which both
	# land at `face`.
	var px := face - 0.05
	var pd := 0.61
	var cx := px + pd * 0.5

	# **The piers stand at the block's own corners, not partway in.** They were
	# at 46% of the half-width with a metre and a half of parapet outboard of
	# each, and in the photograph they are at about 80% with the wing springing
	# almost straight off them. Pushing them out is most of what makes the middle
	# read as an opening: the gap between them is the recess the stair comes up
	# through, and at 3.2m it read as a slot in a wall rather than the whole
	# centre of the composition.
	# **Thicker than they were, and the thickness is measured off the block.** In
	# the photograph each pier is about an eighth of the central block's width;
	# ours were a twelfth, which from the court read as two fins rather than as
	# two piers, and left the opening between them too wide for the block to hold
	# it. 1.05m of a 7m block is that eighth. They move *in* by the thickness they
	# gain, because what is fixed is the outer face sitting on the block's corner
	# — that is where the wing springs from — and not the centre line.
	var horn_w := 1.05
	# The setback from the block's corner. 0.195 put each pier as far out as it
	# could go without hanging over the wing; a foot in from that reads better,
	# because the block's corner then shows past the pier and the pier stands
	# *on* the block rather than terminating it.
	#
	# **A foot in from the corner, not a foot in from anywhere else.** The piers
	# spent part of 2026-08-16 at 1.6m from the axis — 46% of the half-block,
	# with a metre and a half of parapet outboard of each — and that is the
	# position this is measured *away* from, not towards. Written as a setback
	# rather than as a distance from the axis so it stays tied to the corner if
	# the block is ever resized again.
	var horn_z: float = half - 0.50 - horn_w * 0.5
	var horn_top := 1.72
	# **Two heights, not one, and that is the whole geometry of this junction.**
	# Between the piers the crest is low, because what fills that span is rail and
	# the opening wants to read as open. *Outboard* of each pier it is high, and
	# that is the top of the block — the line the flare falls from. A single
	# height for both is what made the flare a 0.5m notch nobody could read as a
	# curve: it had nothing to fall from. The pier is where the two heights meet,
	# which is what a pier is for.
	# **Nothing stands outboard of the piers.** Four shoulders were built into
	# that gap over one night — a quadratic fillet, a concave flare, an S rolling
	# off a raised ledge, and a straight bevel — and every one of them needed a
	# lump of raised wall carried out over the wing to spring from. The lump was
	# always the problem: from the court it read as a block sitting on the wing
	# rather than as the wing's own top edge doing something. The junction is a
	# plain corner now. The block's top is the landing deck, the wings spring
	# from it, and the only things above that line are the two piers and the rail
	# between them.
	var kerb_top := 0.32

	# The kerb, pier to pier, and the piers on top of it.
	#
	# **`cascade_face`, and it was the last pale thing on the facade.** It stayed
	# `building` on the argument that a grey coping in the opening with blue either
	# side of it *was* the contrast — which is a good argument about a wall and the
	# wrong one about this wall. Once the string course came off, the kerb was the
	# only horizontal light band left, sitting exactly where the head's leading
	# edge is, and it inherited the whole of the job the course had just been taken
	# off for: a pale line drawn across the top of the chevron, parallel to the
	# chevron's own edge. The contrast that is left is the rail and the globes,
	# which are objects rather than lines, and the sky behind the crest.
	var kz: float = horn_z + horn_w * 0.5
	_box("crest_kerb", Vector3.ZERO, Vector3(cx, head + kerb_top * 0.5, axis),
		Vector3(pd, kerb_top, kz * 2.0), "cascade_face")
	for k in 2:
		var s := -1.0 if k == 0 else 1.0
		# `cascade_face`, like the wall under them. The piers are the top of the
		# facade rather than something standing on it — the wing springs off the
		# outer face of each — so painting the wall and leaving these grey put a
		# pale block at both ends of the blue, which read as the crest being a
		# different structure bolted across the top. The kerb between them is
		# `cascade_face` too now, so the whole crest is one colour; see there for
		# why the pale-coping-in-the-opening reading did not survive the string
		# course coming off.
		_box("crest_horn_%d" % k, Vector3.ZERO,
			Vector3(cx - 0.05, head + horn_top * 0.5, axis + s * horn_z),
			Vector3(pd + 0.14, horn_top, horn_w), "cascade_face")

		# A globe under each pier, on a stub bracket off the wall face.
		#
		# Hung *below* the crest rather than stood on top of it, which is the
		# whole point of them: a lamp on the parapet is a lamp, and a lamp under
		# the parapet is the pier having something. It is also the only fitting on
		# the monument whose geometry is its own light source — everything else
		# here is an uplight aimed at masonry.
		#
		# `lamp_glass` and the omni at the sphere's own centre, like the
		# promenade's standards: a translucent ball reads as lit from within, and
		# an omni offset from it reads as a ball with a lamp near it.
		var globe_face: float = cx - 0.05 - (pd + 0.14) * 0.5
		#
		# **0.33 and not 0.11.** A soccer ball is the right object and the wrong
		# size for a wall 7m across seen from 12m out — it read as a doorknob.
		# The stand-off goes with the radius rather than staying put, because
		# what has to hold is the gap between the sphere and the masonry: at 0.28
		# out a 0.33 globe buries a third of itself in the wall.
		#
		# **Clear of the string course from the court, which is a longer drop than
		# the elevation asks for.** It hung at `head - 1.05`, whose top sits 5cm
		# under the band's soffit: clear in a front elevation and clear from
		# nowhere a player stands. The globe hangs 0.76m proud of the band's own
		# west face and the court is six metres below, so the nearer object rides
		# up the view — from the apron's west edge at x −67.35 with the eye at 1.7,
		# the sphere's silhouette tops out at 52.1° against the band's lower edge
		# at 47.0°, and the two lit globes cross the one bright line on the facade.
		# **That line is the leading edge and these are the eyes.** From the bottom
		# the monument reads as a ray with its wings spread — `CASCADE_AXIS_Z`'s
		# block in `ParkPlan` says so, and it is the reference's whole silhouette —
		# which makes the course the front edge of the wing and the globes the eyes
		# under it. An eye sitting *on* the leading edge turns the line into a
		# necklace and the globe into a bead threaded on it. That is what the old
		# note here asked for in as many words, and it is the one reading the shape
		# cannot afford.
		#
		# 1.95 is where the overlap clears with air left over at the worst
		# standpoint: apparent top 43.4° against the band's 47.0°, about three and
		# a half degrees of facade between them at the apron and four and a half by
		# the back of the court. Measured against the parallax rather than the
		# elevation — anything picked off a front view clears by centimetres and
		# reads as touching, which is how 1.05 survived.
		var globe_at := Vector3(globe_face - 0.46, head - 1.95, axis + s * horn_z)
		_box("crest_globe_%d_arm" % k, Vector3.ZERO,
			Vector3(globe_face - 0.13, globe_at.y, globe_at.z),
			Vector3(0.28, 0.12, 0.12), "metal")
		_sphere("crest_globe_%d" % k, globe_at, Vector3.ZERO, 0.33, "lamp_glass")
		_omni("crest_globe_%d_pool" % k, globe_at, "lamp", 2.2, 8.0,
			LIGHT_FIXTURE, false)

	# The rail, filling the whole span between the piers and standing to just
	# under their tops.
	#
	# **It is the guard now, so it is built like one.** It used to be two thin
	# horizontals over a solid 0.86m parapet, which did the guarding and left the
	# rail decorative; with the parapet gone from between the piers the rail is
	# what stops somebody walking off a six-metre drop, and it is also — at 5.9m
	# across, head-on, with nothing else fine-grained near it — the most looked-at
	# object on the monument. Three horizontals to 1.34m against the piers' 1.42,
	# which is the proportion the photograph holds: the rail reads as filling the
	# opening rather than as a line drawn across it.
	var rz0: float = axis - horn_z + horn_w * 0.5
	var rz1: float = axis + horn_z - horn_w * 0.5
	var rspan: float = absf(rz1 - rz0)
	for i in 3:
		var ry := head + 0.62 + float(i) * 0.32
		_box("crest_rail_%d" % i, Vector3.ZERO,
			Vector3(cx - 0.10 - float(i) * 0.012, ry, axis),
			Vector3(0.10, 0.08 + float(i) * 0.008, rspan), "metal")
	for i in 6:
		var t := float(i) / 5.0
		_cyl("crest_rail_post_%d" % i, Vector3.ZERO,
			Vector3(cx - 0.10, head + 0.81, lerpf(rz0 + 0.14, rz1 - 0.14, t)),
			0.048, 1.02, "metal", 0.0, 6)


## A wing: out and down from the landing's outer corner, a level turn, and back
## in and down to the court beside the middle.
##
## The outbound leg runs *behind* the facade plane and the return leg in front of
## it, which is what puts two rails at two angles on each side — the thing the
## daylight photograph shows and the thing that took all day to see.
func _cascade_wing(site: Dictionary, side: float, smooth: bool) -> void:
	var tag := "n" if side < 0.0 else "s"
	var path := Plan.wing_path(site, side)
	var half := Plan.WING_W * 0.5
	var base_y := _wing_base_y(site)

	for leg in 2:
		# **Off `wing_leg_end`, not off the path vertices.** The vertex is where
		# the route turns; the leg's slope stops a full landing short of it, and
		# the landing below covers the difference. Building the legs to the vertex
		# and the landing outboard of it is two different answers to where a leg
		# ends, and the gap between them is exactly the slot that showed at the
		# turn.
		var a := Plan.wing_leg_end(site, side, leg, 0)
		var b := Plan.wing_leg_end(site, side, leg, 1)
		var span := Vector2(b.x - a.x, b.z - a.z)
		var length := span.length()
		var theta := atan2(span.x, span.y)
		var slope := atan2(a.y - b.y, length)
		var mid := (a + b) * 0.5
		var run := sqrt(length * length + pow(a.y - b.y, 2.0))
		var up := (Basis(Vector3.UP, theta) * Basis(Vector3.RIGHT, slope)).y
		var h: float = mid.y - base_y

		# The mass under the flight. Its west face is the facade plane on the
		# outbound leg, which is what makes the diagonal you see from the court.
		#
		# **Stepped vertical boxes, and it used to be one box tilted to the
		# slope.** That is the shape everything else here is built from — the
		# ramp, the band, the treads all ride the chord — and it is wrong for
		# this one thing, because this is the only part that reaches all the way
		# down to the court. Tilting a box swings its corners by `height ×
		# sin(slope)` along the run, and at 5.9m tall and 32° that is 3.1m at
		# *each* end of every leg: the outbound legs' top corners swung 3.1m
		# inboard and met each other behind the niche, which is the hourglass
		# that showed through the arched opening, and the bottom corners swung
		# the same distance out past the turn. It read as a shadow and held
		# still through three clocks, which is what proved it was geometry.
		#
		# A wedge is not a rotated box. The profile wanted here is a triangle —
		# sloping top, vertical ends, horizontal bottom at the court — so it is
		# built the way `_cascade_bank` is built: one upright box per tread,
		# each topped at the chord height of its own *lower* edge so it never
		# breaks the walking surface, and the ends land exactly on the leg's
		# ends because nothing is rotated at all. The legs run pure north-south
		# (`wing_path` puts both ends of each at one x), so there is no rotation
		# to lose.
		#
		# **Every one of them is padded, and the pad differs by leg.** One box per
		# tread puts the mass's own end faces on the tread joints, and the two legs
		# of a wing carry the same number of steps over the same run, so leg 0's
		# boundaries land on leg 1's as well — 7 coplanar pairs the first time this
		# was built, between the mass and the treads and between the two legs where
		# their 4.6m widths overlap. Overlapping is the house rule and sharing a
		# plane is what it forbids, so each box runs a little past its own span and
		# the two legs run past by different amounts. The base is dropped per leg
		# for the same reason: both masses bottom out under the court, and two
		# buried faces at one depth still z-fight.
		var mass_steps := maxi(1, int(round((a.y - b.y) / Plan.WING_RISE)))
		var pad := 0.11 + float(leg) * 0.07
		# **The one derivation of the wing's gradient**, off `ParkPlan.wing_slope`
		# rather than recomputed here. It was `(a.y - b.y) / maxf(0.01, absf(b.z -
		# a.z))` written out in three places — here, in `_cascade_crest` and in the
		# rail — which is three chances for `WING_SLOPE_RUN` to move and leave one
		# behind. This one is load-bearing rather than cosmetic: it takes the pad's
		# own fall back off each mass step's top, and getting it wrong stands the
		# mass proud of the ramp by centimetres, which `CharacterBody3D` cannot
		# climb.
		var grad: float = Plan.wing_slope(site)
		var mass_base: float = base_y - float(leg) * 0.15
		for j in mass_steps:
			var t0 := float(j) / float(mass_steps)
			var t1 := float(j + 1) / float(mass_steps)
			var dir := signf(b.z - a.z)
			var z0: float = lerpf(a.z, b.z, t0) - dir * pad
			var z1: float = lerpf(a.z, b.z, t1) + dir * pad
			# **Dropped by the pad's own fall, and that is not cosmetic.** A box
			# topped at the chord height of its downhill edge is flush there and
			# below the chord everywhere above it — but the pad carries it a
			# further `pad` downhill, where the chord has fallen another
			# `pad × gradient`, so the top stands that much *proud* of the ramp.
			# 7cm on leg 0 and 11cm on leg 1, and `CharacterBody3D` has no
			# step-up: `walk_test` blocked all four ascending legs, one of them
			# naming `wing_wall_s_1_9` outright. Take the pad's fall back off the
			# top and the mass is under the walking surface everywhere again. The
			# extra 2cm is for the same reason the whole family of numbers here
			# has one: `wing_land_wall` caps the turn at a round −3.5 and leg 1's
			# steps used to land on it exactly.
			var top: float = lerpf(a.y, b.y, t1) - pad * grad - 0.02 - float(leg) * 0.004
			_box("wing_wall_%s_%d_%d" % [tag, leg, j],
				Vector3(mid.x, (top + mass_base) * 0.5, (z0 + z1) * 0.5),
				Vector3.ZERO,
				# Wider than the separation between the legs, so the two walls
				# interpenetrate instead of leaving a 20cm slot running the whole
				# way down. Shapes may overlap; they may not share a plane.
				# The 4cm on leg 1 is the same argument as the pad: leg 1's east
				# face landed on `landing_face`'s at −63.2. Widening rather than
				# shifting keeps leg 0's west face on the facade plane, which is
				# the one alignment here that is wanted.
				Vector3(Plan.WING_W + Plan.WING_SEP + 0.6 + float(leg) * 0.04,
					top - mass_base, absf(z1 - z0)), "cascade_face")
		# **The cap, and it is what makes one of these a ramp.** The mass under a
		# leg steps once per tread, which is right for the south wing and wrong
		# for the north: the north is the smooth one, and a sawtooth top edge
		# turned it into a staircase with no treads on it — the ramp read as a
		# bad stair rather than as a ramp. So a thin plate rides the chord and
		# covers the sawtooth on both wings, which is also what the reference
		# actually shows: one clean straight diagonal of wall, with whatever the
		# surface is — treads or slope — sitting up behind it.
		#
		# Thin is the whole point. This is the one part of the wing that has to
		# be tilted, and tilting swings a box's corners by `thickness ×
		# sin(slope)`; at 0.34m that is 0.18m, which buries itself in the landing
		# above and the court below. The 5.9m version of exactly this box is what
		# put an hourglass behind the niche.
		var cap_half: float = (Plan.WING_W + Plan.WING_SEP + 0.6 + float(leg) * 0.04) * 0.5 + 0.03
		_box("wing_cap_%s_%d" % [tag, leg], mid - up * 0.19, Vector3.ZERO,
			Vector3(cap_half * 2.0, 0.34, run + 0.2), "cascade_face", theta, true, slope)

		# **No string course down the diagonal either**, and it goes with the
		# landing's — see `_cascade_landing`, which carries the argument. A
		# `wing_band` rode 0.52 under the cap on each leg, and it spent most of its
		# life laid 1.92m out from the leg's centre line while the mass either side
		# reached 2.3m, so the brightest line in the reference was buried inside the
		# masonry and drew nothing at all. Measuring it off the cap's face finally
		# put it where it could be seen, and seeing it is what showed it was a
		# second outline running parallel to the wing's own top edge.
		#
		# The cap is the edge now. It is `cascade_face` like the mass under it, so
		# the wing is one surface from spring to toe and what draws it is the blue
		# meeting the sky.

		# The treads, and the ramp under them that is the actual floor.
		# `CharacterBody3D` has no step-up, so a stair here is a slab on the
		# nosing line with the treads standing out past it on both sides.
		var risers := maxi(1, int(round((a.y - b.y) / Plan.WING_RISE)))
		var going := length / float(risers)
		# **One surface per wing, both legs the same.** The north wing is a ramp and
		# the south a garden stair, and each carries its own surface the whole way
		# down. Building the treads unconditionally made every leg a stair, so the
		# two wings stopped differing at all — and worse, a wing that changed type
		# at its own turn would read as two different structures bolted together.
		# The path is shared and only the surface riding on it differs; that is the
		# whole trick, and it only works if the surface is consistent along a wing.
		if not smooth:
			_wing_treads(tag, leg, a, b, theta, risers, going)
		# **Run the slab a stride past the bottom of its own leg.** Its end face is
		# perpendicular to the slope, so where it stops is a lip standing proud of
		# whatever it lands on — and walking *up* a leg from its very bottom means
		# walking into that lip rather than onto the slope. Both `up` legs failed
		# exactly there. Overshooting downhill buries the face under the landing or
		# the court; overshooting uphill would raise it above the deck above, which
		# is why only one end gets it.
		# Run the slab a stride past the *bottom* of its own leg, and only the
		# bottom. Its end face is perpendicular to the slope, so where it stops it
		# leaves a lip standing proud of whatever it lands on. Overshooting
		# downhill buries that face under the landing or the court.
		#
		# **Not uphill.** Tried, and it is worse: a leg's uphill end is the turn,
		# and a slab extended past it keeps climbing — 45cm of lip on the landing
		# instead of at the foot, failing the leg in both directions rather than
		# one.
		var eb := b + (b - a).normalized() * 0.9
		_flight_ramp("wing_ramp_%s_%d" % [tag, leg], a, eb, theta,
			Plan.WING_W, "far_shade")
		# A slab where the leg lands, flush with what it lands on. Without it the
		# ramp's own end face is perpendicular to the slope and stands proud of the
		# floor at the bottom — a lip the player walks into rather than onto, which
		# is how both `up 2` legs failed.
		if leg == 1:
			# Base, not offset — see `_wing_treads`. This is the same fault and
			# it is only ever emitted on the return leg, which is the leg whose
			# theta is pi on the south wing, so it went with the treads.
			_box("wing_foot_%s" % tag,
				Vector3(b.x, b.y - 0.28, b.z + signf(a.z - b.z) * -0.9),
				Vector3.ZERO,
				Vector3(Plan.WING_W + 0.7, 0.5, 2.4), _tread_mat, theta)

		# The handrail on the west edge, which is the brightest line in every
		# photograph of the reference and the thing that draws the diagonal.
		#
		# **Both ends stop short, and both for the same reason.** The outbound
		# leg's far end is where you step west onto the turn, and a rail carried to
		# it is a fence across the hairpin — `walk_test` walked into it from both
		# directions. The return leg's far end is the court, and a rail carried to
		# *that* fences the one place the descent is supposed to deliver you to.
		# Rails go round the edges nobody crosses, which is a shorter list than it
		# looks.
		# **The rail runs the whole leg now, and stops short only at the very
		# bottom.** It used to be cut back a full `WING_W` at both ends of both
		# legs, which was written when a leg ran all the way to the turn vertex and
		# the rail had to be kept out of the hairpin. Since `wing_leg_end` the legs
		# already stop a landing short of the turn, so the cut was being applied on
		# top of a setback that had already been made — three metres of unguarded
		# edge at every turn end, and the rail visibly not reaching the landing.
		#
		# The one cut that stays is at the bottom of the return leg. By then the
		# wing is flush with the court and a rail carried to the end fences the
		# one place the descent is supposed to deliver you to; it did exactly that
		# once already and both `wing -> court` legs timed out with the player
		# sliding down the outside of it.
		#
		# **It was a flat three metres and that number stopped being right when
		# the monument narrowed.** Three metres was most of a leg when a leg was
		# long; `LANDING_HALF_W` went 7.0 → 3.5 and `WING_SLOPE_RUN` came to 4.8,
		# and the same constant then ate 3 of 4.8 — the rail ran 1.8m and quit,
		# with the steepest, highest end of the descent unguarded and the line the
		# reference is famous for drawn along a third of its diagonal. Nothing
		# caught it: `walk_test` asks whether a rail is in the way, never whether
		# it is there, and from the court a short rail is a rail.
		#
		# So it is derived from the thing it is for. A rail guards a drop, so it
		# stops where the drop stops being one — `RAIL_FREEBOARD` above the court,
		# which at this gradient is about a metre of run rather than three. Steepen
		# the leg and the setback shrinks with it; that is the point of writing it
		# this way rather than picking a smaller number.
		var ra := a
		var rb := b
		if leg == 1:
			var d := Vector2(b.x - a.x, b.z - a.z).length()
			var fall := a.y - b.y
			# Never more than half a leg, whatever the arithmetic says. A guard
			# that has argued itself down to nothing is the failure this replaces,
			# run the other way.
			var back: float = minf(d * 0.5, RAIL_FREEBOARD * d / fall) if fall > 0.01 else 0.0
			rb = a.lerp(b, 1.0 - back / d)
		_wing_rail("wing_rail_%s_%d" % [tag, leg],
			Vector2(ra.x - half - 0.2, ra.z), ra.y,
			Vector2(rb.x - half - 0.2, rb.z), rb.y, true)

	# The turn: level, spanning both legs and the wall between them. The only
	# place on the descent you can stop, turn round and look back up.
	var p1: Vector3 = path[1]
	var p2: Vector3 = path[2]
	var x0: float = p1.x + half
	var x1: float = p2.x - half
	var cx := (x0 + x1) * 0.5
	var w := absf(x1 - x0)
	# From where both legs stop to a little past the turn, so it meets each leg
	# exactly and overhangs neither. Both edges come from `wing_leg_end`, so the
	# landing cannot drift from the legs the way it did when it was laid out from
	# the vertex with its own depth.
	var stop_z: float = Plan.wing_leg_end(site, side, 0, 1).z
	var out_z: float = p1.z + side * 0.9
	var far_z := (stop_z + out_z) * 0.5
	var land_d: float = absf(out_z - stop_z)
	var y := p1.y
	# **Its top stops half a metre under the slab's**, which is the slab's own
	# thickness. It used to reach the same height *and* run 0.4m further toward
	# the legs than the slab does, so where a leg was still sloping down to meet
	# the landing the wall stood a full riser proud of it — a ledge across the top
	# of both flights that you had to jump.
	#
	# Found by raycasting the floor down the leg at 20cm and printing where it
	# stepped, after three fixes reasoned from the constants had all been wrong.
	# The constants said these surfaces were flush; they were not, and only a
	# measurement said so.
	_box("wing_land_wall_%s" % tag, Vector3.ZERO,
		Vector3(cx, (y - 0.5 + base_y) * 0.5, far_z),
		Vector3(w + 0.8, y - 0.5 - base_y, land_d + 0.8), "cascade_face")
	# **Brick, not `accent`.** The turn is a floor you stand on, and it was the
	# park's terracotta with nothing on it — a flat orange rectangle six metres
	# up a blue wall, which from the court read as a painted panel rather than as
	# ground. The court below it is brick and so is the apron at the foot, so the
	# whole of what the descent delivers you onto is now one material and the
	# only thing that changes down the route is your height. The treads stay
	# `accent`: a tread is a piece of the stair, not a piece of the ground.
	_box("wing_land_%s" % tag, Vector3.ZERO, Vector3(cx, y - 0.25, far_z),
		Vector3(w, 0.5, land_d), "brick")
	# Coping on the two edges nothing walks over — the far end and the west face.
	# Never the near edge: that is where both legs come in, and a 40cm kerb across
	# it is a wall closing the turn the landing exists to make.
	_box("wing_land_cap_end_%s" % tag, Vector3.ZERO,
		Vector3(cx, y + 0.2, out_z + side * 0.4),
		Vector3(w + 0.8, 0.4, 0.8), "trim")
	_box("wing_land_cap_west_%s" % tag, Vector3.ZERO,
		Vector3(x1 - 0.4, y + 0.2, far_z), Vector3(0.8, 0.4, land_d + 0.8), "trim")
	# **On the leg rails' own line, `x1 - 0.2`, where this was `x1 - 0.5`.** The
	# outer guard of a hairpin is one line — down leg 1, across the turn, and
	# nothing about the corner makes it two — but the landing's was set out
	# independently and landed 0.3m west of the legs'. That is far enough apart to
	# read as two rails passing each other and near enough that their end posts
	# stood in each other, which after the globes went on was two lamps 30cm apart
	# at the one place on the descent you stop and look. It was also 0.1m past the
	# outer face of `wing_land_wall`, so the last post had nothing under it.
	# `_wing_rail` merges the shared corner post; see there.
	#
	# **It runs a hand past the slab's far edge and then turns.** The west run
	# used to stop dead on the outer corner at `out_z`, which is the far end of
	# the whole hairpin — the outermost point of the monument, the one place the
	# descent gives you to stand and look back up it, and a 3m drop over a 40cm
	# kerb. The guard was continuous down leg 1 and across the turn and then
	# simply ended, at the corner, in the air. Carrying it round the end is what
	# the outer edge of a switchback is: one line from the head of the return leg
	# round the turn and back, rather than a line that quits where the direction
	# changes.
	#
	# Both runs sit `0.2` outboard of the slab, on their own coping, so the
	# corner is a right angle with one post in it rather than two lines passing
	# 20cm apart — the same fault `POST_MERGE` was written for, one corner along.
	# The end run reaches `x0 + 0.2`, which is the far side of leg 0: east of
	# that the planted bank comes up and there is no drop left to guard.
	var corner_z: float = out_z + side * 0.2
	_wing_rail("wing_land_rail_%s" % tag,
		Vector2(x1 - 0.2, stop_z), y,
		Vector2(x1 - 0.2, corner_z), y, true)
	_wing_rail("wing_land_rail_end_%s" % tag,
		Vector2(x1 - 0.2, corner_z), y,
		Vector2(x0 + 0.2, corner_z), y, true)


## The treads on the south wing, and only the south wing.
##
## **A tread is centred on its own going and topped at its downhill nosing.**
## Centring it on the nosing instead puts half of every tread standing proud of
## the ramp on the downhill side, and the ramp is the floor — so walking *up* a
## leg means walking into a 25cm riser every half metre, which is a wall, not a
## step. `CharacterBody3D` has no step-up. Both `up` legs failed on it and no
## screenshot would have shown it: from above, a tread 25cm too high looks like a
## tread.
func _wing_treads(tag: String, leg: int, a: Vector3, b: Vector3, theta: float,
		risers: int, going: float) -> void:
	# **The point goes in as the base, not as the offset.**
	#
	# These read `_box(nm, Vector3.ZERO, world_point, …, theta)`, and `_place`
	# turns the *offset* by `theta` — so a leg running back the other way, at
	# theta = pi, had every tread negated in x and z. The outbound leg is at
	# theta = 0 where that is the identity, so it looked right; the return leg
	# was built 127m away on the far side of the plaza. What you saw on the
	# ground was a wing with a stair down one leg and a bare ramp down the
	# other, which is exactly what it was.
	#
	# Only the *south* wing shows it, and that is the same accident that hid it:
	# the north wing is the smooth one and emits no treads at all, so there was
	# nothing over there to come out wrong.
	#
	# `theta` still goes in, and still should — it is what keeps each tread
	# square to the flight it belongs to. It just has nothing left to rotate.
	for i in risers:
		var tm := a.lerp(b, (float(i) + 0.5) / float(risers))
		var tn := a.lerp(b, float(i + 1) / float(risers))
		_box("wing_tread_%s_%d_%d" % [tag, leg, i],
			Vector3(tm.x, tn.y - 0.26, tm.z), Vector3.ZERO,
			Vector3(Plan.WING_W + 0.7, 0.5, going), _tread_mat, theta)
		_box("wing_nosing_%s_%d_%d" % [tag, leg, i],
			Vector3(tn.x, tn.y + 0.015, tn.z), Vector3.ZERO,
			Vector3(Plan.WING_W - 0.2, 0.03, 0.16), "far_shade", theta, false)


## The planting either side, which is **what makes a wing make sense**.
##
## A retaining wall is legible because of what is behind it. There was a version
## of this with nothing behind it and it read as scenery no matter what the
## measurements said. Here the bank fills the wedge between the outbound leg and
## the bluff face, its surface following the flight down, and it is the planted
## hillside the reference's flanking stairs are cut into.
## How far the bank's far end runs into what it backs onto. Buried either way —
## the second exists only so the west site's does not land on the bluff plinth's
## own embed, which is `BLUFF_FACE_X + 0.3` and reached from the other file.
const BANK_EMBED := 0.3
const BANK_EMBED_AT_PLINTH := 0.45


func _cascade_bank(site: Dictionary, side: float) -> void:
	var tag := "n" if side < 0.0 else "s"
	var path := Plan.wing_path(site, side)
	var a: Vector3 = path[0]
	var b: Vector3 = path[1]
	var base_y := _wing_base_y(site)
	# The bank's surface is capped just under the head, because past that it would
	# stand above the ground it is retaining. `-0.25` meant that at the west site
	# and meant "a quarter metre below sea level" everywhere else.
	var head: float = site["head_y"]
	var x0: float = a.x + Plan.WING_W * 0.5 + 0.4
	# **The far end is buried, and it may not be buried by the same amount as the
	# bluff's plinth.** `CASCADE_TOP_X` *is* `BLUFF_FACE_X`, so at the west site
	# `top_x + 0.3` and the plinth's own 0.3 embed are not two numbers that
	# happen to be close — they are one number arrived at twice, and the two east
	# faces became one plane the moment the plinth was built. Neither face is
	# visible: both sit inside the bluff mass, which is why nothing showed and
	# why `coplanar_test.py` reported it anyway. It reports it *forever*, though,
	# and a permanently-red line hides the next real one.
	#
	# So the bank goes in deeper than the plinth rather than level with it. The
	# east site has no plinth to miss — its `top_x` is `HILL_FACE_X` — and takes
	# the plain embed.
	var x1: float = float(site["top_x"]) + BANK_EMBED
	if is_equal_approx(float(site["top_x"]), Plan.BLUFF_FACE_X):
		x1 = float(site["top_x"]) + BANK_EMBED_AT_PLINTH
	if x1 - x0 < 1.0:
		return
	var cx := (x0 + x1) * 0.5
	var w := x1 - x0
	# **Six steps down the slope and a seventh across the turn, and the seventh
	# is the whole reason this is a list of segments rather than a lerp.**
	#
	# The row used to run `a → wing_path[1]` in six, which is the leg's *vertex*
	# — and the turn landing reaches `side * 0.9` past that vertex (see
	# `_cascade_wing`, where `out_z` is written). So the last 0.7m of the strip
	# between the wing and the bluff carried nothing: a notch at the end of a
	# marching row, on the one stretch the row is ever seen end-on from, which is
	# standing on the turn looking back up the descent.
	#
	# It is not a seventh of a longer lerp, and that is the point of the extra
	# structure. The slope's six steps are laid on the slope and the turn is
	# level, so extending the interpolation would tilt a landing that is flat and
	# quietly re-space the six steps that were already right. The seventh is laid
	# on the landing's own level — `b.y`, so it steps down once more from the
	# sixth and stops there.
	#
	# **A bay past each end, so the row runs out rather than stopping.** Six on
	# the slope and one on the turn is the structure exactly, and from the court
	# that read as a row of planters cut off square at both ends — the hillside
	# beginning where the wing begins and ending where its masonry does, which is
	# not how a hillside behaves. One more bay at the head carries the planting
	# in past the spring of the wing onto the top deck, where it is a bed rather
	# than a retained bank (the `head - 0.25` cap already flattens it there, so it
	# arrives as planting let into the deck rather than as a wall standing on it);
	# one more past the turn tucks a last bay into the strip against the bluff and
	# steps it down a further half metre, so the row leaves the frame falling
	# instead of stopping level.
	#
	# Both are laid at the slope's own going, which is the only reason they read
	# as more of the same row rather than as two extra objects.
	var going: float = (b.z - a.z) / 6.0
	var fall: float = (a.y - b.y) / 6.0
	var segs: Array = []
	segs.append([a.z - going, a.z, a.y])
	for i in 6:
		var p0 := a.lerp(b, float(i) / 6.0)
		var p1 := a.lerp(b, float(i + 1) / 6.0)
		segs.append([p0.z, p1.z, (p0.y + p1.y) * 0.5])
	segs.append([b.z, b.z + side * 0.9, b.y])
	segs.append([b.z + side * 0.9, b.z + side * 0.9 + going, b.y - fall])
	for i in segs.size():
		var z0: float = segs[i][0]
		var z1: float = segs[i][1]
		var y: float = minf(head - 0.25, float(segs[i][2]) + 1.4)
		if y <= base_y + 0.4:
			continue
		var cz := (z0 + z1) * 0.5
		var d := absf(z1 - z0) + 0.4
		_box("bank_%s_%d" % [tag, i], Vector3.ZERO,
			Vector3(cx, (y + base_y - 0.4) * 0.5, cz),
			Vector3(w, y - base_y + 0.4, d), "building")
		_box("bank_soil_%s_%d" % [tag, i], Vector3.ZERO,
			Vector3(cx, y + 0.17, cz), Vector3(w - 0.4, 0.34, d - 0.2),
			"planting", 0.0, false)
		for k in 6:
			var hx: float = lerpf(x0 + 0.4, x1 - 0.4, _hash01(i * 19 + k, 3, 43))
			# `min`/`max` rather than `z0`/`z1`, which `_cascade_bed` has always
			# done and this had not: the north bank runs in −z, so `z0 + 0.3` and
			# `z1 − 0.3` *widened* the range there instead of insetting it and put
			# the odd bloom over the edge of its own planter.
			var hz: float = lerpf(minf(z0, z1) + 0.3, maxf(z0, z1) - 0.3,
				_hash01(i * 19 + k, 5, 47))
			var bloom: String = ["bloom_warm", "bloom_pink", "bloom_pale"][(i + k) % 3]
			_sphere("bank_bloom_%s_%d_%d" % [tag, i, k],
				Vector3(hx, y + 0.34, hz), Vector3.ZERO,
				0.15 + _hash01(k, 2, 23) * 0.13, bloom)


## The lower tier of planting: a raised bed along the foot of each wing, in the
## court.
##
## `_cascade_bank` plants the hillside *behind* the descent, which is the strip
## between the outbound leg and the bluff face — 1.9m wide, and there is no more
## room back there for a second tier. But the bank only covers the upper leg, so
## everything the court actually sees of the lower half is blank: the return
## leg's west face and the turn landing's retaining wall, which together are the
## largest unbroken surface on the monument and are exactly what you are looking
## at while you walk down.
##
## So the second tier is not above the first, it is below and in front of it —
## which is what a park does at the foot of a retaining wall anyway, and what
## makes the two read as one terraced hillside rather than as a planted top and a
## bare bottom. It steps with the leg it hugs, so the bed rises as the wall it
## sits against rises.
##
## It stops well short of the foot on purpose. The last stride of the descent is
## where the wing delivers you into the court, and `walk_test` walks it; a bed
## carried to the end would be a planter in the doorway.
func _cascade_bed(site: Dictionary, side: float) -> void:
	var tag := "n" if side < 0.0 else "s"
	var path := Plan.wing_path(site, side)
	var turn: Vector3 = path[2]
	var foot: Vector3 = path[3]
	var base_y := _wing_base_y(site)
	# The bed stands in the court, so its kerbs are measured off the court floor.
	# That was `SHORE_TOP` written out — correct at the west site and meaningless
	# at any other, since the east cascade's court is the plaza at y 0.
	var floor_y: float = site["floor_y"]
	# The west face of the return leg's mass, which is what the bed leans on.
	var face: float = turn.x - (Plan.WING_W + Plan.WING_SEP + 0.64) * 0.5
	var x1 := face + 0.25
	var x0 := x1 - 1.7
	var z0: float = foot.z + side * 1.9
	var z1: float = turn.z + side * 1.1
	var segs := 4
	for i in segs:
		var t0 := float(i) / float(segs)
		var t1 := float(i + 1) / float(segs)
		var a: float = lerpf(z0, z1, t0)
		var b: float = lerpf(z0, z1, t1)
		# The kerb steps with the wall behind it — the leg falls from the turn to
		# the foot, so the tier furthest out is the tallest.
		var top: float = floor_y + 0.42 + 0.34 * float(i)
		_box("bed_%s_%d" % [tag, i], Vector3.ZERO,
			Vector3((x0 + x1) * 0.5, (top + base_y) * 0.5, (a + b) * 0.5),
			Vector3(x1 - x0, top - base_y, absf(b - a) + 0.3), "building")
		_box("bed_soil_%s_%d" % [tag, i], Vector3.ZERO,
			Vector3((x0 + x1) * 0.5, top + 0.16, (a + b) * 0.5),
			Vector3(x1 - x0 - 0.36, 0.32, absf(b - a) - 0.06), "planting", 0.0, false)
		for k in 7:
			var hx: float = lerpf(x0 + 0.35, x1 - 0.35, _hash01(i * 23 + k, 7, 53))
			var hz: float = lerpf(minf(a, b) + 0.3, maxf(a, b) - 0.3,
				_hash01(i * 23 + k, 11, 59))
			var bloom: String = ["bloom_pale", "bloom_warm", "bloom_pink"][(i + k) % 3]
			_sphere("bed_bloom_%s_%d_%d" % [tag, i, k],
				Vector3(hx, top + 0.33, hz), Vector3.ZERO,
				0.16 + _hash01(k, 3, 29) * 0.14, bloom)


## The monument after dark.
##
## Two jobs that want opposite things: a silhouette read from the pier at 130m,
## and treads you can see under your feet. So the fittings split by which job
## they do rather than by where they are.
##
## The rake across each flight is the one worth explaining. `CharacterBody3D` has
## no step-up, so a stair here is a ramp with treads laid over it and a nosing a
## few centimetres proud — a distinction legible in daylight only because the sun
## is off-axis. Lit from straight on after dark the whole thing flattens back
## into the slope it actually is. Lighting it from the *side* puts every nosing's
## shadow across the tread below it, so the stair reads as a stair in the dark
## for the same reason it does at four in the afternoon. It is the cheapest
## safety feature in the park and the best-looking thing in it.
func _cascade_lights(site: Dictionary) -> void:
	var axis: float = site["axis_z"]
	var floor_y: float = site["floor_y"]
	var wx: float = site["wall_x"]
	var face: float = wx - Plan.CASCADE_WALL_THICK * 0.5

	# --- the niche ---
	#
	# Lit from inside, so the opening reads as luminous against a dark mass. An
	# arch is a hole, and the dramatic version of a hole is light coming out of
	# it — truer here than when this was a doorway, because now there is water
	# coming out of it too.
	#
	# **Behind and above the basin rather than out in the middle**, which is the
	# deep niche's doing. At 0.6m of recess there was nowhere for a fitting to be
	# except in the opening; at 1.5 there is a whole depth to hide one in, and a
	# lamp tucked up behind the bowl throws the bowl's underside and the spout's
	# shadow down the back plate. One in the middle of a 1.5m recess lights the
	# back wall flat and puts the fitting itself in the frame.
	_omni("niche_glow", Vector3(face + 1.25, floor_y + 2.40, axis),
		"amber", 4.0, 9.0, LIGHT_FEATURE, true)
	# And the falls from underneath, off the trough's own rim. Three stages of
	# falling water in a dark alcove is the one thing on this monument that is
	# better after dark than before it, and none of it shows unless something is
	# under it — `water_fall` carries its brightness in `EMISSION`, but the stone
	# behind it does not, and a lit stream against an unlit wall is a stripe.
	_uplight("niche_wash", Vector3(face + 0.15, floor_y + 0.92, axis),
		Vector3(face + 1.35, floor_y + 2.30, axis), "moon", 2.6, 5.0, 46.0)
	# The lights in the water, which are `trough_lamp_*` and `bowl_lamp` over in
	# `_cascade_niche` — the discs are the fitting and these are what it does.
	#
	# **Below the waterline**, at the bed, where a real lens sits. Opaque water
	# hides the disc and does not stop the light, because these carry no shadow;
	# see `_cascade_niche` for the measurement that settled it.
	#
	# Warm rather than the `moon` above, and that is the one place on this
	# monument the cold/warm rule inverts. Everywhere else cold is the stone that
	# holds the silhouette and warm is the ground you walk on; here the niche is a
	# warm pocket in a cold monument, and light coming *up* through water onto
	# terracotta is the whole reason the fountain stopped being limestone. Cool
	# uplighting in here would be a swimming pool.
	#
	# Tight cones and short range, because these are fittings in a 2.4m alcove
	# and not floodlights: past the arch they would spill onto the facade and
	# compete with the flood that is drawing the chevron.
	for k in 2:
		var s := -1.0 if k == 0 else 1.0
		_uplight("trough_lamp_%d_up" % k,
			Vector3(face + 0.52, floor_y + 0.76, axis + s * 0.34),
			Vector3(face + 1.30, floor_y + 1.85, axis + s * 0.26),
			"lamp", 1.8, 4.0, 52.0)
	# Up at the spout and the underside of the arch head, which is the one part of
	# the recess `niche_glow` lights from behind and therefore leaves flat.
	_uplight("bowl_lamp_up", Vector3(face + 1.30, floor_y + 1.99, axis),
		Vector3(face + 1.42, floor_y + 3.00, axis), "lamp", 1.6, 3.5, 44.0)
	# And a bead of light **just above** each lamp, which is the half the shader
	# cannot do for itself. `water_pool`'s lamp term is albedo and gloss rather
	# than emission — deliberately, because an emissive would glow flat at noon
	# the way `_lit_material`'s doc block warns — so at night the lit patch is only
	# as bright as whatever falls on it, and what falls on it is `niche_glow` from
	# behind the basin. These are tiny and very short-ranged: not lighting
	# anything, just giving the surface over each lamp something to be pale in.
	# Driven by the clock like every other fitting, so they cost nothing by day.
	for k in 2:
		var s := -1.0 if k == 0 else 1.0
		_omni("trough_lamp_%d_bead" % k,
			Vector3(face + 0.52, floor_y + 0.86, axis + s * 0.34),
			"lamp", 0.9, 1.1, LIGHT_FIXTURE)
	_omni("bowl_lamp_bead", Vector3(face + 1.30, floor_y + 2.15, axis),
		"lamp", 0.7, 0.8, LIGHT_FIXTURE)
	# And the face either side of it, grazed from below so the trapezoid reads as
	# one plane rather than as three lit patches.
	#
	# **Four sources and not two, which is the same argument one level down.** A
	# 34° cone at 3.6 from one standpoint per flank put a hard-edged disc of light
	# on each side of the niche — two lit patches on a wall whose whole point is
	# to be one plane, which is exactly the fault this comment claims to be
	# fixing. Two per flank at lower energy and a wider cone overlap into a wash,
	# and the overlap is what hides where any of them start.
	for side in [-1.0, 1.0]:
		for i in 2:
			var z: float = axis + side * (1.9 + float(i) * 1.4)
			_uplight("landing_face_%d_%d" % [int(side + 1), i],
				Vector3(face - 1.5, floor_y + 0.5, z),
				Vector3(face - 0.5, floor_y + 4.2, z - side * 0.6),
				"moon", 2.3, 9.0, 46.0)

	# --- the facade ---
	#
	# **The chevron, which is the whole shape and had no light on it.** Everything
	# above washes a *part* — the niche, the flanks of the middle wall, the
	# treads, the planting — and the thing those parts add up to is a top edge
	# running horizontal across the middle and falling away at both ends. By day
	# that edge is drawn by the crest coping and the sky. After dark it was drawn
	# by nothing, so the monument stopped being a shape at sunset and became a set
	# of lit patches at the bottom of a black bluff.
	#
	# So: a row of floods standing in the court, at the toe of what they light,
	# raking up the face. Grazing rather than flooding — the aim point is only
	# 1.2m out from the wall over 4m of rise. That aim was chosen to throw the
	# string course's own shadow up the plane, and the course has since come off
	# the facade — see `_cascade_landing` — so the graze now rakes a plane with
	# nothing on it to shadow. Kept at 1.2m regardless: grazing is also what puts
	# a gradient on a flat surface, and it is the crest coping's underside and the
	# niche's reveals that catch it now. Cold, because the facade is painted and
	# `moon` on that blue goes
	# deeper while the route's amber would take it to mud. That is the split the
	# tints were written for and it now has a colour to work against.
	#
	# **On the return legs and not the outbound ones**, which is a fact about the
	# hairpin rather than a saving. Leg 0's mass stands on the facade plane at
	# `face` and leg 1's stands 4m west of it over the same stretch of z — so
	# from anywhere in the court leg 1 hides leg 0 completely, and a flood aimed
	# at the outbound leg lights the back of the return one.
	for side in [-1.0, 1.0]:
		var tag := "n" if side < 0.0 else "s"
		var p2: Vector3 = Plan.wing_path(site, side)[2]
		var p3: Vector3 = Plan.wing_path(site, side)[3]
		# The return leg's own west face, off the mass width rather than off
		# `WING_W`: what you see is the mass, and it is a metre and a half wider
		# than the leg walked down the middle of it.
		var fx: float = p2.x - (Plan.WING_W + Plan.WING_SEP + 0.64) * 0.5
		for i in 3:
			var t := (float(i) + 0.5) / 3.0
			var p := p2.lerp(p3, t)
			_uplight("wing_face_%s_%d" % [tag, i],
				Vector3(fx - 1.1, floor_y + 0.35, p.z),
				Vector3(fx - 0.1, p.y + 1.6, p.z),
				"moon", 3.2, 11.0, 38.0)

	# The crest, from the landing deck. The piers and the rail between them are
	# the top of the chevron and the only part of the monument seen against sky
	# rather than against the bluff — which means it is the one part a wash from
	# below cannot reach, because everything below it is what the wash is
	# standing on.
	for side in [-1.0, 1.0]:
		_uplight("crest_graze_%d" % int(side + 1),
			Vector3(face + 1.6, 0.15, axis + side * 2.4),
			Vector3(face + 0.2, 2.2, axis + side * 1.2),
			"moon", 2.4, 7.0, 30.0)

	# --- the descent ---
	#
	# Raking each leg from alternating sides so the light crosses the treads
	# rather than pouring down them. Warm, and the warm is doing a job beyond
	# looks: everything the player walks on down here is amber and everything
	# they walk past is cold, so the route is legible as a route from the top of
	# the bluff. That is the argument the plaza's asphalt-on-brick makes, made in
	# light because the wings have no room for a painted walkway.
	for side in [-1.0, 1.0]:
		var tag := "n" if side < 0.0 else "s"
		var path := Plan.wing_path(site, side)
		for leg in 2:
			var a: Vector3 = path[0] if leg == 0 else path[2]
			var b: Vector3 = path[1] if leg == 0 else path[3]
			for i in 4:
				var t := (float(i) + 0.5) / 4.0
				var p := a.lerp(b, t)
				var e := 1.0 if i % 2 == 0 else -1.0
				_uplight("wing_rake_%s_%d_%d" % [tag, leg, i],
					Vector3(p.x - e * (Plan.WING_W * 0.5 - 0.2), p.y + 0.35, p.z),
					Vector3(p.x + e * Plan.WING_W * 0.5, p.y + 0.9,
						p.z - side * 2.0),
					"amber", 3.0, 9.0, 42.0)

	# --- the garden ---
	#
	# The banks either side, from underneath. Warm against the cold face: the
	# planting is the reason this reads as a garden rather than as civil
	# engineering, and that is the quality that dies first when the sun goes down.
	for side in [-1.0, 1.0]:
		var tag := "n" if side < 0.0 else "s"
		for i in 3:
			var t := 0.2 + float(i) * 0.3
			var p := Plan.wing_point(site, side, t * 0.5)
			_uplight("bank_light_%s_%d" % [tag, i],
				Vector3(p.x + 1.6, p.y + 0.6, p.z),
				Vector3(p.x + 3.4, p.y + 2.2, p.z), "amber", 2.2, 6.0, 54.0)

	# --- the path ---
	#
	# **Fittings, and they are the first ones on the descent.** Everything above
	# is an uplight buried at the foot of the thing it points at: staged light
	# with no visible source, which is right for a monument and wrong for a
	# route. Six metres of stair with no lamp *on* it reads as a lit sculpture
	# you are not invited onto, and the wings are the way down.
	#
	# A globe on top of a rail post, which is the crest's motif carried down —
	# `lamp_glass` with an omni at the sphere's own centre, the only fittings on
	# this monument whose geometry is their own light source. Repeating it is
	# what makes the two piers at the top and the run down each wing read as one
	# scheme instead of as a feature and some safety lighting.
	#
	# **Since 2026-08-18 they are the monument's decoration and not only its route
	# lighting.** The facade lost its string course and its pale crest kerb that
	# day, both of them lines drawn parallel to the chevron's own top edge, which
	# is the one kind of ornament this shape cannot carry — see `_cascade_landing`.
	# What is left articulating it is eighteen glass globes: sixteen down the
	# wings and two under the piers. Points on a blank surface rather than lines
	# across it, which is the whole distinction the facade argument turned on. A
	# later pass wanting more detail here should add fittings, not stripes.
	#
	# `lamp` rather than `amber`: the rakes across the treads are the staged
	# warm, and a fitting has to be tungsten or it stops reading as a fitting.
	# Short range on purpose — 7m keeps each globe a pool you walk through
	# rather than a wash that flattens the raking light it is standing in.
	#
	# The positions are **read out of `_cascade_rails`**, filled by `_wing_rail`
	# while the wings were built. Nothing here knows where a leg ends or how far
	# the bottom rail is set back, which is the point: those two numbers have
	# both moved this week.
	for i in _cascade_rails.size():
		var at: Vector3 = _cascade_rails[i] + Vector3(0.0, 0.16, 0.0)
		_sphere("wing_globe_%d" % i, at, Vector3.ZERO, 0.13, "lamp_glass")
		_omni("wing_globe_%d_pool" % i, at, "lamp", 1.5, 7.0, LIGHT_FIXTURE)

	# --- the ground ---
	#
	# Two in the court, throwing the monument's own shadow west and giving the
	# open ground at its foot something other than spill. Without them the court
	# is the darkest place on the route and it is where the descent delivers you.
	for side in [-1.0, 1.0]:
		_omni("court_pool_%d" % int(side + 1),
			Vector3(face - 12.0, floor_y + 3.4, axis + side * 12.0),
			"lamp", 2.4, 18.0, LIGHT_FIXTURE)


## A run of rail: posts and a top rail rather than a slab, between two points at
## two heights. Level or raking, and every rail on the monument is one of these.
## Where every rail post on the monument ended up, in world coordinates, at the
## height of its own top.
##
## `_cascade_lights` hangs a globe on some of these, and it is a **record rather
## than a recomputation** on purpose. The alternative is the lamp pass solving
## the rail's arithmetic for itself — the leg ends, `half + 0.2` outboard, the
## `RAIL_FREEBOARD` setback at the bottom of leg 1 — which is a second copy of a
## thing that has already moved twice this week, and `walk_test` carrying its own
## copy of the wing path is exactly how a test came to be walking a wing it had
## computed for itself. The lamps are emitted last for seam-order reasons, and
## this is what lets them be emitted last without knowing anything.
## Which material the cascade's treads wear, set per site by `_cascade`. See
## there for why the east is brick and the west may never be.
var _tread_mat := "accent"
var _cascade_rails: Array = []

## Every post `_wing_rail` has put down this scene, lamped or not, so that two
## runs meeting at a corner can share the one at the join.
var _cascade_posts: Array = []

## How close two posts have to be before they are the same post.
##
## A hairpin's outer guard is one line — down the return leg, across the turn —
## and it is built as two runs because the leg falls and the turn is level, which
## is the same reason the planted bank's seventh step is not a seventh of a
## longer lerp. Two runs sharing an endpoint otherwise stand two posts in each
## other, and once the globes went on that was two lamps 30cm apart at the one
## place on the descent you stop and look back. Half a metre catches the join and
## nothing else — **measured off the emitted scene rather than reasoned about**:
## with the corner merged, the closest two posts that are genuinely different
## were 1.445m apart, which was the turn landing's 2.9m rail over its two spans.
## That run is 3.1m now that the guard turns the outer corner, so the arithmetic
## says 1.55 — **arithmetic, not a measurement**, and it wants re-checking off
## the emitted scene the next time one is written. Half a metre has room either
## way. The
## first draft of this comment said 1.9m from arithmetic done in the head, and
## the whole of this monument's recent history is numbers that were never checked
## against the file they describe.
const POST_MERGE := 0.5


func _wing_rail(nm: String, a: Vector2, ya: float, b: Vector2, yb: float,
		lamps := false) -> void:
	var span := b - a
	var length := span.length()
	if length < 0.5:
		return
	var theta := atan2(span.x, span.y)
	var phi := atan2(ya - yb, length)
	# **`ceili`, not `int`.** Truncating makes the spacing *grow* with the run
	# once it passes 5.2m: a 7.4m rail asks for 2 bays of 3.7m rather than 3 of
	# 2.47, and with a globe on every post that is the difference between a line
	# of lamps and three lamps. Nothing on the monument was long enough to show
	# it until the guard turned the corner and picked up the landing's whole
	# width. Inert for every run that existed before — the legs are 4.8 and 3.84
	# and the turn 3.1, and `maxi(2, …)` already floors all three at two bays.
	var posts := maxi(2, ceili(length / 2.6))
	for i in posts + 1:
		var t := float(i) / float(posts)
		var p := a.lerp(b, t)
		var top: float = lerpf(ya, yb, t) + 1.1
		var at := Vector3(p.x, top, p.y)
		var shared := false
		for q in _cascade_posts:
			if at.distance_to(q) < POST_MERGE:
				shared = true
				break
		if shared:
			continue
		_cascade_posts.append(at)
		_cyl("%s_post_%d" % [nm, i], Vector3.ZERO,
			Vector3(at.x, top - 0.55, at.z), 0.06, 1.1, "metal", 0.0, 6)
		if lamps:
			_cascade_rails.append(at)
	var m := (a + b) * 0.5
	# **Nine centimetres, not one metre.** The doc above says "posts and a top rail
	# rather than a slab" and the size said otherwise: a 1m tall panel spanning the
	# whole run, which on the cascade's diagonals read as two heavy dark slabs
	# where the reference has a slender chrome line. It is the brightest and most
	# legible thing in every photograph of the original, and we were drawing it
	# with a fence.
	_box("%s_rail" % nm, Vector3(m.x, (ya + yb) * 0.5 + 1.06, m.y), Vector3.ZERO,
		Vector3(0.11, 0.09, sqrt(length * length + pow(ya - yb, 2.0))), "metal",
		theta, true, phi)


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
	# East, and the largest thing in the park. Last in this scene rather than
	# first, so that adding it moves nobody's seam ordinal: the coaster and the
	# tower keep the displacement they were built with.
	_rim()


# ---------------------------------------------------------------------------
# The rim
# ---------------------------------------------------------------------------

## How finely the ridge is sampled along its length: one column of the mesh
## every 2.5m, so 137 of them over the 340m the profile spans.
##
## **This replaced 34 ten-metre bands on 2026-08-18, and the change is what the
## number means rather than what it is.** A band was a *slab* — a rigid box laid
## on its own chord at its own slope angle — so the sampling rate was also the
## rate at which the surface was allowed to be a different shape, and every
## boundary between two of them was a real discontinuity: a step in the crest,
## a lap edge drawing a dark line the full height of the face, and a toe cut
## perpendicular to its own chord leaving a tooth against the ground. 33 seams,
## and once the face was textured they were the loudest thing on it. A column is
## not a slab. It is two vertices, its neighbour is welded to it, and there is no
## boundary to see — so this can be as fine as the crest curve wants and costs
## nothing but vertices.
##
## 2.5m is well past the point where it matters. `_rim_jag`'s faster term has a
## 19m wavelength, so eight columns carry it; at 150m one column is about half a
## degree. The old 10m was chosen against a 1.1m step it could not avoid, which
## is a constraint that no longer exists.
const RIM_STEP := 2.5

## How far the ridge runs east of the crest before its back is underground.
##
## It used to be the depth of a separate block behind each band, there so the
## crest was an edge on something rather than the top of a plane. It is the back
## slope of the mesh now, which does the same job by being the same object: the
## crest is a crease between two strips rather than a line where one strip stops.
## Nothing has ever seen it and nothing can — the plaza is 150m west and 48m
## below the crest.
const RIM_BACK_D := 24.0

## How far below its own foot the chord keeps going before it stops, so that the
## ridge comes out of the ground rather than standing on it.
##
## **It was `RIM_TOE_Y := -2.0`, an absolute height, and an absolute height only
## works while the whole ridge stands on one level.** Down the east arm the foot
## is `TERRACE_TWO_Y` and −2 is fourteen metres under it — spare geometry for
## terrace two to bury, which on the axis is everything from about x 110 out to
## 120. The same −2 on the headland, whose foot is `WATER_TOP`, would have been
## five metres *above* the ground it was supposed to be buried in.
##
## Fourteen, so the east arm comes out exactly where it always did.
const RIM_TOE_BURY := 14.0


## The relief, and how quickly it comes in off the axis. See `_rim_jag`.
const RIM_JAG := 1.2
const RIM_JAG_TAPER := 30.0


## The park sits in a breached crater, and this is the wall of it: 340m of ridge
## climbing out of the east, open to the west because that is the bearing the sun
## sets on and `daylight.gd` computes rather than poses.
##
## **`ParkPlan` has held the whole of it since the east cascade went in and
## nothing had ever drawn it.** Foot, crest, the seven-point profile and the
## `rim_crest` accessor were all written, and `rim_crest` had no callers at all —
## so the east gate has been framing a six metre monument with open sky behind
## it, and the plan's claim that the ridge stands over the whole east roofline
## was a claim about a file rather than about the park.
##
## **Massing, never reachable, no collision**, like the coaster and the tower it
## shares this scene with. The player cannot get near the toe: the shelf that
## would take them there is not built either, and the cascade stops them at x 70.
##
## Two views see two different halves of it, which is what the plan is arranged
## around. From inside the plaza an eye at 1.7 clears the east wall's 11.5m top
## on a shallow ray, so the fountain sees the top seven metres of a crest of 50
## and the plaza's west side sees about twenty-four — the ridge opens up as you
## back away from it, which is the right way round for distance. Through the east
## gap you get the foot and the lower slope instead, cropped near 29m by the
## beam. **Nothing sees the crest from above and nothing sees the back**, and the
## mass below is allowed to assume that.
##
## What is deliberately not here: the north arm, which `RIM_PROFILE` stops short
## of because a rim that wraps north has to decide what it does about the grove
## and about the coaster standing forty metres in front of it, and neither is
## decided. The ends at z ±170 are raw cuts for the same reason the east court's
## are — from the fountain the far end of the ridge sits under a ray that clears
## the wall at y 63, so there is no standpoint in the park that can see one.
func _rim() -> void:
	# **Swept along a path in plan since 2026-08-21, not along z.** Every
	# coordinate below used to be a constant or a function of z, which is what a
	# straight wall is; `ParkPlan.rim_samples` hands over the crest line, its
	# inward normal and its arc length, and the cross-section is taken off that.
	var samples: Array = Plan.rim_samples(RIM_STEP)

	# Three lines down the ridge, sampled together so a column is one place on
	# it rather than three independent ones: the toe, buried; the crest; and the
	# back foot, buried again. The mesh is the two strips between them.
	var toe := PackedVector3Array()
	var crest := PackedVector3Array()
	var back := PackedVector3Array()
	# Kept so `_rim_unfolded` can compare each column's reach against the curve
	# it is standing on. Recorded rather than recomputed, for `_cascade_rails`'
	# reason: the offset is arithmetic on `alpha`, and a second derivation of it
	# would agree until one of them changed.
	var offs := PackedFloat32Array()
	for sm in samples:
		var at: Vector2 = sm["at"]
		var inward: Vector2 = sm["inward"]
		var foot_y: float = sm["foot"]
		var top: float = float(sm["crest"]) + _rim_jag(sm)
		# The slope the plan actually states, measured between the two points it
		# names: the foot, and the crest `RIM_RUN` outboard of it. The toe below
		# the foot is an extension of the same line, never a second gradient.
		var alpha := atan2(top - foot_y, Plan.RIM_RUN)
		var toe_y := foot_y - RIM_TOE_BURY
		var reach: float = Plan.RIM_RUN + RIM_TOE_BURY / tan(alpha)
		offs.append(reach)
		var toe_at: Vector2 = at + inward * reach
		var back_at: Vector2 = at - inward * RIM_BACK_D
		toe.append(Vector3(toe_at.x, toe_y, toe_at.y))
		crest.append(Vector3(at.x, top, at.y))
		back.append(Vector3(back_at.x, toe_y, back_at.y))

	if not _rim_unfolded(samples, offs):
		return
	_rim_mesh("rim", toe, crest, back)


## No column may reach further inward than the curve it stands on can carry.
##
## **A swept profile folds wherever the sweep turns tighter than the profile
## reaches**, and the fold is not subtle once you know to look for it: the toe
## line crosses its own neighbours, the triangles between them invert, and it
## comes out as a dark pleat running up the face with a V notch bitten out of the
## silhouette at the bottom. It looks like a modelling mistake in a landform,
## which is exactly what it is.
##
## It went unnoticed on the first build of the wrap because nothing in the data
## says it. The control points are fine, the crest line is smooth, the mesh is
## well formed, the winding and the crease both pass, and the AABB is right — the
## defect only exists in the *relationship* between the offset and the curvature,
## and neither of those is written down anywhere. Two separate causes were live
## at once: a turn eyeballed at 38-43m of radius against a 44m reach, and uniform
## Catmull-Rom overshooting on unevenly spaced control points, which put a 27m
## wiggle into a stretch of the headland that is nearly straight.
##
## Measured over a plus-or-minus four column stencil — ten metres either side —
## rather than over neighbours, because at 2.5m spacing three adjacent points are
## nearly collinear and the circumradius of a sliver is numerical noise. The
## first version of this check used neighbours and reported a 1.5m radius on a
## curve that does not go below 58.
func _rim_unfolded(samples: Array, offs: PackedFloat32Array) -> bool:
	const W := 4
	var worst := INF
	var at := Vector2.ZERO
	var rad_at := 0.0
	for i in range(W, samples.size() - W):
		var p: Vector2 = samples[i - W]["at"]
		var q: Vector2 = samples[i]["at"]
		var r: Vector2 = samples[i + W]["at"]
		var area: float = absf((q.x - p.x) * (r.y - p.y)
			- (q.y - p.y) * (r.x - p.x)) * 0.5
		if area < 0.000001:
			continue
		var rad: float = p.distance_to(q) * q.distance_to(r) \
			* p.distance_to(r) / (4.0 * area)
		if rad - offs[i] < worst:
			worst = rad - offs[i]
			at = q
			rad_at = rad
	if worst < 0.0:
		push_error(("gen_props: the rim folds at %s — the crest turns on a "
			+ "%.1fm radius there and the section reaches %.1fm inward, so the "
			+ "toe crosses itself and the face pleats. Open the turn out "
			+ "(`RIM_TURN_R`), or steepen the gradient so the buried toe is "
			+ "shorter.") % [at, rad_at, rad_at - worst])
		_fatal = true
		quit(1)
		return false
	return true


## The ridge as one welded surface, and the reason it is the only thing in the
## park built this way.
##
## **A ridge cannot be made of boxes.** It was 34 of them until 2026-08-18 — one
## slab per band, each laid on its own chord at its own slope angle — and every
## artefact that made the thing read as a folded paper screen rather than as land
## came from that and could not be tuned out of it. A box is rigid, so its top
## edge is a straight horizontal line in z; a ridge whose crest rises and falls
## therefore steps at every boundary. The slabs lapped 0.4m so as not to butt,
## which is the house rule and correct, and the lap showed as a dark line the
## full height of the face because the two slabs either side of it were at
## different angles and one stood proud. The bottom of each slab was cut
## perpendicular to its own chord, so the row of toes came out as teeth. None of
## those is a bug in the band code. They are what a band *is*.
##
## Finer bands do not help — 33 seams become 99 fainter ones, and the node count
## triples. The fix is to stop having boundaries: a column here shares its
## vertices with its neighbour, so there is nothing at a column to see, and the
## sampling rate stops being a shape decision and becomes a smoothness one.
##
## **The crest is a crease and the face is not, and what holds that is the smooth
## group.** Normals are averaged along z so the face shades as a continuous
## surface; that is the whole point of building it this way. But the same
## averaging carried across the crest rounds the ridge line off into a soft hump,
## and the crest is the one line on this object the entire east composition is
## aimed at.
##
## Two `_rim_strip` calls do not prevent that, and neither do distinct UVs.
## Godot 4's `generate_normals` welds by **position and smooth group only** — it
## hashes a `SmoothGroupVertex`, which carries no UV at all — so the front
## strip's crest row and the back strip's crest row are the same positions and
## are averaged together whatever else differs about them. Measured, not assumed:
## built without the groups, 813 of the 816 vertices on the crest plane came back
## with a normal pointing *east*, which is the mean of a west-facing face at 51
## degrees and an east-facing back at 64. Every way a scene can be inspected said
## it was fine — right node, right vertex count, right AABB, no error anywhere.
##
## So the two strips are given different smooth groups and the crest stays an
## edge. The V offset between them is kept as well, because it costs nothing and
## a tangent frame that does not flip across the crease is worth having, but it
## is not what does this job and must not be mistaken for it.
##
## `_rim_creased` is the guard, and it is here rather than in a test because
## nothing outside this file knows the crest is supposed to be sharp.
##
## UVs are laid out but never sampled — the material is world-space triplanar, so
## they exist only because `generate_tangents` needs them, and without tangents
## the normal map has no frame to be applied in and the relief silently does
## nothing. That is the same shape of failure as the uniforms that save as null:
## a well-formed scene with the important part missing.
##
## **The winding is asserted rather than reasoned about.** Front faces are a
## convention, and a surface built the wrong way round is invisible from the one
## direction it exists to be seen from — which on a 340m ridge behind a wall
## reads as "the rim did not generate" rather than as a winding bug. The check
## costs one dot product.
func _rim_mesh(nm: String, toe: PackedVector3Array, crest: PackedVector3Array,
		back: PackedVector3Array) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	# Two groups, and this is the line that keeps the crest sharp.
	st.set_smooth_group(0)
	_rim_strip(st, toe, crest, 0.0)
	st.set_smooth_group(1)
	_rim_strip(st, crest, back, 2.0)
	st.generate_normals()
	st.generate_tangents()
	var mesh := st.commit()

	var arrays := mesh.surface_get_arrays(0)
	var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]

	# The face has to point at the park. Sampled at the toe, which is the one row
	# on the front strip that cannot have been contaminated by the crest even if
	# the crease has failed — checking a crest vertex here would have passed while
	# the ridge was rounding off.
	#
	# **Anchored to the toe on the park's own axis rather than to whichever vertex
	# is lowest.** Lowest was safe while the whole ridge was footed at one height
	# and is not now: `RIM_TOE_BURY` hangs off each column's own foot, so the
	# deepest vertex is the headland's, two hundred metres away and pointing a
	# different way — and toe and back share that height anyway, so "lowest" could
	# always have picked a back vertex and failed a sound mesh. Here the direction
	# is known, because on the axis inward is due west and always has been.
	var pick := 0
	for j in toe.size():
		if Vector2(toe[j].x, toe[j].z).distance_to(Plan.RIM_AXIS_AT) \
				< Vector2(toe[pick].x, toe[pick].z).distance_to(Plan.RIM_AXIS_AT):
			pick = j
	var lowest := -1
	for i in verts.size():
		if verts[i].distance_squared_to(toe[pick]) < 1e-6:
			lowest = i
			break
	if lowest < 0:
		push_error("gen_props: the rim's axis toe vertex is not in the mesh")
		_fatal = true
		quit(1)
		return
	var probe: Vector3 = normals[lowest]
	if probe.x > -0.2 or probe.y < 0.0:
		push_error(("gen_props: the rim's face is wound backwards — its normal "
			+ "came out %s, and it has to point west and up. The strip is "
			+ "invisible from the plaza built this way round.") % probe)
		_fatal = true
		quit(1)
		return

	if not _rim_creased(verts, normals, crest):
		return

	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = mats["rim"]
	_add(mi, nm)


## One strip between two lines of the ridge, in world coordinates.
##
## `v0` is where this strip starts in the V direction. It is the only thing the
## two calls differ by, and it is load-bearing rather than cosmetic: it is what
## keeps the crest rows of the two strips from welding into one. See `_rim_mesh`.
func _rim_strip(st: SurfaceTool, low: PackedVector3Array,
		high: PackedVector3Array, v0: float) -> void:
	var cols := low.size()
	for j in cols - 1:
		var u0 := float(j) / float(cols - 1)
		var u1 := float(j + 1) / float(cols - 1)
		# Wound so that `generate_normals` puts the normal on the outside — see
		# the assertion in `_rim_mesh`, which is what actually holds this.
		_rim_tri(st, low[j], u0, v0, high[j], u0, v0 + 1.0,
			low[j + 1], u1, v0)
		_rim_tri(st, high[j], u0, v0 + 1.0, high[j + 1], u1, v0 + 1.0,
			low[j + 1], u1, v0)


## Every vertex on the crest plane should carry one of two normals — the face's
## and the back's — and never their average.
##
## This exists because the failure it catches is invisible. A welded crest is a
## well-formed mesh: it loads, it draws, it has the right vertex count and the
## right bounds, and from the plaza it is a 340m ridge whose top edge is very
## slightly soft at a range where nobody would think to look for a normal bug.
## The only cheap way to know is to ask the geometry, so this asks it.
func _rim_creased(verts: PackedVector3Array, normals: PackedVector3Array,
		crest: PackedVector3Array) -> bool:
	# **By membership of the crest line, not by a plane.** This used to ask
	# whether a vertex sat at `RIM_CREST_X`, which is a fine question about a
	# straight wall and meaningless about a ridge that turns west — past the bend
	# no crest vertex is at that x at all, so the test would have found only the
	# east arm's and quietly stopped covering two hundred and fifty metres of the
	# thing it exists to check. `SurfaceTool` does not move positions, so the
	# crest rows are still exactly the vectors handed to it and a millimetre key
	# matches them outright.
	var keys := {}
	for c in crest:
		keys[_rim_key(c)] = true
	# Inward and outward rather than west and east, for the same reason. On the
	# axis these are the same statement; on the north arm inward is south.
	var inward := 0
	var outward := 0
	for i in verts.size():
		if not keys.has(_rim_key(verts[i])):
			continue
		var to_park := Vector2(-verts[i].x, -verts[i].z)
		if to_park.length() < 0.001:
			continue
		to_park = to_park.normalized()
		if normals[i].x * to_park.x + normals[i].z * to_park.y > 0.0:
			inward += 1
		else:
			outward += 1
	# Both rows are laid the same way, so a sound crease is an even split. A
	# weld collapses one of them onto the other and leaves a handful of strays.
	if inward < 1 or outward < 1 \
			or absf(inward - outward) > maxi(inward, outward) / 4:
		push_error(("gen_props: the rim's crest is not a crease — %d of its "
			+ "vertices face the park and %d face away, where an even split is "
			+ "wanted. The two strips have been welded and the ridge line is "
			+ "rounding off. Check the smooth groups in `_rim_mesh`.")
			% [inward, outward])
		_fatal = true
		quit(1)
		return false
	return true


## A vertex as a millimetre key, for asking whether the mesh still contains a
## point the generator put into it.
func _rim_key(v: Vector3) -> String:
	return "%d,%d,%d" % [roundi(v.x * 1000.0), roundi(v.y * 1000.0),
		roundi(v.z * 1000.0)]


func _rim_tri(st: SurfaceTool, a: Vector3, au: float, av: float,
		b: Vector3, bu: float, bv: float,
		c: Vector3, cu: float, cv: float) -> void:
	st.set_uv(Vector2(au, av))
	st.add_vertex(a)
	st.set_uv(Vector2(bu, bv))
	st.add_vertex(b)
	st.set_uv(Vector2(cu, cv))
	st.add_vertex(c)


## The relief on the crest line.
##
## A fixed pair of sines rather than an RNG because the generator has none and
## does not want one: the ridge has to come out the same on every run or the
## coplanar report changes under whoever is reading it.
##
## **It used to have a second job and no longer does.** While the ridge was 34
## slabs, two adjacent bands at the same crest were two parallel faces a hair
## apart, and a crest that never repeats was what stopped them lining up. There
## are no bands now, so that argument is retired — and so is the claim that this
## buys the ridge its only tonal variation, which was true when a band was a flat
## facet meeting the sun at its own angle. The surface is welded and smooth in z
## now, and what shades it is the normal map. This is left in because the *shape*
## reason still stands on its own: a ridge interpolated straight off seven
## control points is a swept curve, and a swept curve at this size reads as a
## tarpaulin over something rather than as land.
##
## **Zero on the park's own axis**, and that is not tidiness. `ParkPlan` states
## what a crest of 50 shows from the fountain and from the plaza's west side, and
## those two numbers were measured off that 50. A metre of jag forty metres north
## costs nothing; a metre of it on the axis would quietly make a documented
## figure wrong, which is how the wheel's height went wrong for a week.
func _rim_jag(sm: Dictionary) -> float:
	# **Phased on arc length and tapered on distance in plan.** It used to be both
	# of those in z, which is the same thing on a straight wall and useless on a
	# ridge that turns: the west arm holds z at about −200 for two hundred and
	# fifty metres, so a jag phased on z would have been one constant offset along
	# the whole of it, and a taper on `absf(z - axis)` would have pinned it at full
	# strength the entire way.
	var at: Vector2 = sm["at"]
	var taper := clampf(at.distance_to(Plan.RIM_AXIS_AT) / RIM_JAG_TAPER, 0.0, 1.0)
	var a: float = sm["arc"]
	return (sin(a * 0.137) * 0.62 + sin(a * 0.331 + 1.7) * 0.38) * RIM_JAG * taper


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
## **Each end is tied to the wall it is tied to, and that took until
## 2026-08-16.** The run was hung at a flat 5.6m between x's inset 0.3m from
## both frontage faces, which meant no string in the street touched a building.
## Every end stopped short of the masonry; three of them stopped *above* the
## parapet they were nailed to — the west arcade tops out at 4.8 and its string
## floated 0.8m over the roof — and the sixth, at z=108, spanned the turnstiles
## at `GATE_Z` 107, where there is no frontage on either side at all.
##
## One cause under all three: a constant height across a frontage whose heights
## are a table of six different values. It is the setback-written-as-a-length
## trap in another costume — 5.6 was true of the buildings that happened to be
## tall enough on the day it was typed, and nothing re-checked it for the ones
## that were not, because a festoon photographs as a festoon whichever end of it
## is in the sky.
##
## So an anchor is a relationship: a hand below its own building's wall head,
## under the coping lip, with a pin lapping through the face so the wire ends on
## something. A string between a 6.5m shop and a 5.5m one comes out tilted, and
## should — the frontage table's whole job is to say these are separate
## premises, and a run that leans to meet each roof says it again overhead.
const STREET_STRING_DROP := 0.3
const STREET_STRING_SAG := 0.85
const STREET_STRING_STEPS := 8
## The wire runs a hand *into* each wall rather than butting on its face: a butt
## is a coplanar pair, and the pin is what the eye reads at the junction anyway.
const STREET_STRING_LAP := 0.15
## How far a pin laps back into the masonry, and how far it stands out of it.
const STREET_STRING_PIN_IN := 0.35
const STREET_STRING_PIN_OUT := 0.3


## What a festoon can be tied to on one side of the street at `z`, as the height
## of the wall head there, or -1.0 if there is no building at that z to tie to.
##
## Read off what is *built* rather than off the row's height column, which is
## the same distinction `_shopfronts` itself draws: the west arcade's row says
## 7.0 and `_arcade_room` ignores it, standing at `ARC_TALL`. A string hung on
## the table's figure ends 2.6m above the roof it is fixed to.
func _street_wall_top(rows: Array, side: float, z: float) -> float:
	for row in rows:
		var half: float = float(row[1]) * 0.5
		if z < float(row[0]) - half or z > float(row[0]) + half:
			continue
		if side < 0.0 and String(row[5]) == "arcade":
			return ARC_TALL
		return float(row[3])
	return -1.0


func _street_festoons() -> void:
	var z := 58.0
	var i := 0
	while z <= 108.0:
		var tops := [_street_wall_top(STREET_WEST, -1.0, z),
			_street_wall_top(STREET_EAST, 1.0, z)]
		# Nothing to tie to on one side or the other. Past z≈105 the ranges have
		# run out and the gate takes over, so a string there is two ends in open
		# sky. Skipped rather than errored: the sweep is a rhythm and the
		# frontage is a list of premises, and they are allowed to disagree at the
		# ends of the street.
		if tops[0] < 0.0 or tops[1] < 0.0:
			z += 10.0
			continue
		var a := Vector3(ST_X - ST_HALF, tops[0] - STREET_STRING_DROP, z)
		var b := Vector3(ST_X + ST_HALF, tops[1] - STREET_STRING_DROP, z)

		# A pin per end, lapping through the face, so the wire ends on something
		# rather than merely reaching a wall. The same fitting the cutting's run
		# has had since the day it was built — see `_gate_festoons`.
		#
		# The position goes in as the **base** with a zero offset, because the
		# `theta` that lays the cylinder along X is the same `theta` `_place`
		# turns the local offset by: passed as an offset it comes out at
		# (z, y, -x), which is the mistake that built the south wing's treads on
		# the far side of the park.
		for e in 2:
			var p: Vector3 = a if e == 0 else b
			var side := -1.0 if e == 0 else 1.0
			_cyl("street_string_%d_pin_%d" % [i, e],
				Vector3(p.x + side * (STREET_STRING_PIN_IN - STREET_STRING_PIN_OUT)
					* 0.5, p.y, p.z), Vector3.ZERO,
				0.06, STREET_STRING_PIN_IN + STREET_STRING_PIN_OUT, "metal",
				PI * 0.5, 8, false, PI * 0.5)

		var x0: float = a.x - STREET_STRING_LAP
		var x1: float = b.x + STREET_STRING_LAP
		var points: Array[Vector3] = []
		for s in STREET_STRING_STEPS + 1:
			var t := float(s) / float(STREET_STRING_STEPS)
			points.append(Vector3(lerpf(x0, x1, t),
				lerpf(a.y, b.y, t) - STREET_STRING_SAG * sin(PI * t), z))
		for s in STREET_STRING_STEPS:
			_strut("street_wire_%d_%d" % [i, s], points[s], points[s + 1], 0.045, "metal")
		for bl in STREET_STRING_STEPS - 1:
			_sphere("street_bulb_%d_%d" % [i, bl], points[bl + 1], Vector3.ZERO, 0.13, "bulb")
		# One light per string at the sag, low, so the street's asphalt is warmer
		# under a string than between strings. The bulbs carry the look; this
		# only stops the middle of the street being the darkest part of it.
		# At the chord's own mid-height, which is the whole point of the change:
		# on a tilted string a constant y is a pool that drifts off its own wire.
		_omni("street_string_%d_glow" % i,
			Vector3(ST_X, (a.y + b.y) * 0.5 - STREET_STRING_SAG, z), "warm", 1.7, 12.0)
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
			# Sunk 6cm, like the booths, the tables and the stools. See `PAVE_LIFT`:
			# a generated thing whose underside sits at exactly y=0 shares a plane
			# with the paving, and stays invisible until an unrelated quad is added
			# and shifts the displacement counter. Four in one evening.
			_box("shop_%d" % n, Vector3.ZERO, Vector3(cx, height * 0.5 - 0.03, z),
				Vector3(depth, height + 0.06, length), mat)
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
	# Both sunk 6cm rather than standing on the ground, for the same reason the
	# cafe tables are: their undersides sat at exactly y=0, on the same plane as
	# the street paving's, and nothing showed until a paving quad was added
	# elsewhere and shifted every displacement after it. A building that ends at
	# the floor is a building that will find the floor eventually — give way
	# downward.
	_box("gate_booth_west", Vector3.ZERO, Vector3(west_c, 1.72, GATE_Z),
		Vector3(4.5, 3.56, 4.0), "white")
	_box("gate_booth_east", Vector3.ZERO, Vector3(east_c, 1.72, GATE_Z),
		Vector3(4.5, 3.56, 4.0), "white")
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
			# Sunk 6cm rather than standing on the ground. This is one cylinder for
			# the pedestal and the top together, so its underside sat at exactly
			# y=0 — on the same plane as the street paving's. Nothing showed until
			# the tunnel gained a paving quad and shifted every displacement after
			# it, which is the failure mode CLAUDE.md predicts for adding a shape
			# anywhere but the end. Give way downward.
			_cyl("%s_table_%d" % [nm, i], at, Vector3(x, 0.34, 1.5), 0.36, 0.80,
				"white", theta, 10)
			_cyl("%s_table_%d_leg" % [nm, i], at, Vector3(x, 0.18, 1.5), 0.1, 0.36,
				"metal", theta, 6, false)
			for j in range(2):
				var sx := x + (-0.75 if j == 0 else 0.75)
				_cyl("%s_stool_%d_%d" % [nm, i, j], at, Vector3(sx, 0.21, 1.5),
					0.18, 0.54, "wood", theta, 8)

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
	# **The terrace's asphalt is not laid here any more**, and the reason is a
	# change in what this section mounts rather than a change of mind about the
	# ground. `plaza_paving.tscn` is in the boardwalk's own scene list since
	# 2026-08-19 — see `ParkSections` — so its six terrace runs are already
	# standing when this scene is, and laying them again put two identical quads
	# a quarter-millimetre apart on ground the player walks on. That is under
	# `coplanar_test.py`'s floor and over the eye's, which is the worst of both.
	#
	# Laying it twice was right for as long as neither section mounted the other's
	# paving. It stopped being right the moment one of them did.

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
## How far an awning reaches out from the frontage, how far it falls doing it,
## and how thick it is. `AWN_FALL` is in radians and it is a fall *outward*,
## which is the only direction an awning has ever sloped.
const AWN_PROJ := 2.6
const AWN_FALL := 0.18
const AWN_THICK := 0.16
const AWN_SINK := 0.02


## An awning over a boardwalk shopfront, on two posts.
##
## **It sloped sideways until 2026-08-20, and the cause is `_xform`.** The call
## passed `phi = -0.18` for a fall outward and got a 10 degree *roll along the
## frontage* instead: `_xform` pitches about the box's own local RIGHT, and with
## no `theta` that is world X, which runs across the awning's projection rather
## than along it. So the rotation landed in the y-z plane. A 10.4m awning rolled
## 10 degrees drops 0.93m at one end and lifts 0.93m at the other — a 1.86m
## fall across a shopfront, which is what made these read as parallelograms
## stuck to the wall.
##
## `theta = PI * 0.5` is the fix and it is the same quarter turn `_rim_band`
## needs for the same reason: it swaps the box's local X onto world -Z, so the
## pitch that follows happens in x-y where the fall belongs. `size` swaps with
## it — local X is now the run along the frontage and local Z is the
## projection. The position goes in as `base` with a zero `local`, because
## `_place` rotates a local offset by `theta` and a world point handed in as an
## offset is the bug that built twelve treads on the far side of the park.
##
## Two more faults went with it, both of the same family — a part written by its
## own centre and never checked against what it meets:
##
## - The back edge stood at `front_face - 1.1 + 1.3 = front_face + 0.2`, which
##   is 20cm *short of* the wall rather than into it. A gap, not a butt, and
##   visible as daylight between the canvas and the shopfront. It is sunk
##   `AWN_SINK` now, which is what the entrance street's awnings have always
##   done, in a comment that says why: butted exactly, the awning's back face
##   and the shop's face are the same plane and fight.
## - The posts topped out at `SHORE_TOP + 3.2` under an awning at
##   `SHORE_TOP + 3.42`. They held nothing up, and they never could have, since
##   they were a fixed height under a surface that was supposed to slope. They
##   are derived off the awning's underside at their own x now, and they
##   overlap into it rather than meeting it.
func _awning(nm: String, front_face: float, mid: float, run: float,
		mat: String) -> void:
	var fall := sin(AWN_FALL)
	var reach := cos(AWN_FALL)
	# The wall end, and the outer end derived from it. Every other number here
	# is one of these two.
	var back_x := front_face + AWN_SINK
	var back_y := SHORE_TOP + 3.72
	var out_x := back_x - AWN_PROJ * reach
	var out_y := back_y - AWN_PROJ * fall
	_box("%s_awning" % nm, Vector3((back_x + out_x) * 0.5, (back_y + out_y) * 0.5, mid),
		Vector3.ZERO, Vector3(run, AWN_THICK, AWN_PROJ), mat, PI * 0.5, false,
		-AWN_FALL)

	# The posts stand a little inboard of the lip, so the canvas oversails them
	# the way a real one does. Their height is whatever reaches the underside
	# *at their own x* — the surface slopes, so a shared height is wrong for at
	# least one of them by construction.
	var post_x := out_x + 0.25
	var under := out_y + 0.25 * (fall / reach) - (AWN_THICK * 0.5) / reach
	var top := under + 0.06
	for side in [-1.0, 1.0]:
		var tag := "n" if side < 0.0 else "s"
		_box("%s_post_%s" % [nm, tag], Vector3.ZERO,
			Vector3(post_x, (SHORE_TOP + top) * 0.5, mid + side * (run * 0.5 - 0.2)),
			Vector3(0.14, top - SHORE_TOP, 0.14), "metal")


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
			_awning("shop_%s" % nm, front_face, mid, depth - 1.6, awn)

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
## The whole machine — deck, ring, hub, spokes, legs and cars — is `_wheel`, and
## the tableau builds the same call in the haze palette, so the shape cannot
## drift between the two sides of the seam. What the section adds is everything
## that says it is a machine somebody *operates*: a fence, a queue rail, and a
## booth with the lever in it. None of that reads from the plaza — it is 1.2m
## tall behind an 8m frontage — which is why it is the one part that stays here.
func _boardwalk_wheel() -> void:
	var base := Vector3(WHEEL_AT.x, SHORE_TOP, WHEEL_AT.y)
	var half := Plan.WHEEL_PLATFORM * 0.5
	_wheel(base, "white", "plank", "red", "yellow", PI * 0.5)

	# The jetty stands in the water, so it stands on piles — the pier's, at the
	# pier's spacing and in the pier's material, because they are the same
	# structure doing the same job forty metres apart and two different answers
	# would read as two different piers. Four rows: the platform is 8m across
	# and the pier is 8m across, and the pier uses two rows at ±3, so this uses
	# the same inset off each edge and fills between.
	#
	# The wheel's own legs come down at z ±11 from the axle, which lands between
	# rows either way; they are carried by the deck rather than by a pile of
	# their own, which is what the deck is for.
	var pn := 0
	var pz := Plan.WHEEL_FROM_Z + 2.5
	while pz <= Plan.WHEEL_TO_Z - 2.4:
		for px in [base.x - half.x + 1.0, base.x - 1.4, base.x + 1.4,
				base.x + half.x - 1.0]:
			_cyl("wheel_pile_%d" % pn, Vector3.ZERO,
				Vector3(px, WATER_TOP - 0.4, pz), 0.28, 4.0, "far_shade", 0.0, 6, false)
			pn += 1
		pz += 5.0

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
	#
	# **North, since 2026-08-20, and it used to run south.** Which way a queue
	# lies is not decoration: it is 8m of the promenade's width committed to
	# standing still, and it was committed to the eight metres immediately north
	# of the alley — z -17.6 to -9.6, which is the stretch everybody coming
	# through the gap walks into. Turned about the booth it lies alongside the
	# platform instead, on the quiet run between the wheel and the coaster,
	# where the only thing behind it is more wheel. Same rail, same length, same
	# distance off the frontage; the whole change is the sign of one term.
	var booth := Vector3(base.x + half.x + 1.4, SHORE_TOP, base.z - 3.0)
	_box("wheel_booth", Vector3.ZERO, booth + Vector3(0, 1.3, 0),
		Vector3(2.2, 2.6, 2.6), "white")
	_box("wheel_booth_roof", Vector3.ZERO, booth + Vector3(0, 2.75, 0),
		Vector3(2.8, 0.3, 3.2), "blue", 0.0, false)
	_box("wheel_booth_sign", Vector3.ZERO, booth + Vector3(-1.2, 3.5, 0),
		Vector3(0.2, 1.4, 2.6), "red", 0.0, false)
	# Six posts at 1.6m, laid north off the booth. The run ends at z -28.4,
	# which is inside the platform's own span (-29..-3), so the queue is beside
	# the machine for its whole length rather than trailing past the end of it.
	for i in 6:
		_box("wheel_queue_%d" % i, Vector3.ZERO,
			booth + Vector3(1.6, 0.5, -1.4 - i * 1.6), Vector3(0.08, 1.0, 0.08), "metal")


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
		if absf(z - PIER_ROOT.y) > PIER_MOUTH_CLEAR and not _over_the_jetty(z):
			_box("edge_post_%d" % n, Vector3.ZERO,
				Vector3(SHORE_EDGE + 0.4, SHORE_TOP + 0.6, z),
				Vector3(0.14, 1.3, 0.14), "wood")
			n += 1
		z += 2.4
	# Two runs of rail, north and south of the pier mouth. **These collide.** The
	# posts are 2.4m apart and the player is 0.8 across, so a decorative rail
	# between colliding posts is a gap the player walks through and off the edge
	# — which looks exactly like a rail right up until somebody tries it.
	# Three cuts, so four runs: the north end, the jetty, the pier's mouth, the
	# south end. Built as a list of gaps rather than as literals, because the
	# pier and the wheel have both moved this week and a hand-written run is a
	# run that is right until something does.
	var gaps := [
		[Plan.WHEEL_FROM_Z - 0.4, Plan.WHEEL_TO_Z + 0.4],
		[PIER_ROOT.y - PIER_MOUTH_CLEAR, PIER_ROOT.y + PIER_MOUTH_CLEAR],
	]
	gaps.sort_custom(func(a, b): return a[0] < b[0])
	var runs := []
	var from_z := WALK_FROM_Z
	for gap in gaps:
		if gap[0] > from_z:
			runs.append([from_z, gap[0]])
		from_z = maxf(from_z, gap[1])
	if from_z < WALK_TO_Z:
		runs.append([from_z, WALK_TO_Z])
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
		# **One skip now, and it is not the one that used to be here.**
		#
		# This line skipped the wheel's 26m and nothing else, because a lamp on
		# the centre line inside a ride is a lamp inside a ride. The wheel went
		# onto its own jetty on 2026-08-20 and the centre line there is open
		# deck, so that skip was protecting an object that had left — which
		# would have put a 54m stretch of unlit promenade directly in front of
		# the section's biggest thing. Removed with the reason that made it.
		#
		# What it never skipped is the pier's mouth, and it is the only one of
		# the three runs along this strip that did not: the edge posts and the
		# lamp masts have both stood off `PIER_ROOT.y` since they were written.
		# It cost nothing while the pier sat on `ALLEY_Z` and the 9m lamp
		# spacing happened to straddle it. The pier moved 8m south the same day
		# and `prom_lamp` at z 5 landed a metre off the deck's centre line —
		# 4.8m of steel standing in the only doorway on the strip.
		#
		# Three call sites skipping the same opening, two by rule and one by
		# luck, and the luck is invisible until the opening moves.
		# `PIER_MOUTH_CLEAR` is the rule and all three read it.
		if absf(z - PIER_ROOT.y) > PIER_MOUTH_CLEAR:
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
		if absf(z - PIER_ROOT.y) > PIER_MOUTH_CLEAR and not _over_the_jetty(z):
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
## **It carries the walls and nothing hung on them, and that is now the whole of
## its job.** This used to say the frontage was applied to inner faces only, so
## there was nothing of it to see from the west, and that the roof clutter was
## left off because a stand-in that reproduces detail has to be kept in step with
## detail. The second half is sound and is the reason none of it is copied here.
## The first half was simply not true, and one screenshot through the arch said
## so: the parapets, cornices and cupolas sit *on top* of the walls and read from
## either side, and the gate's own kit — jamb, course, valance, thirteen bulbs,
## two festoon runs — is inside the passage, which is where the player stands
## after crossing. All of it vanished at two metres.
##
## The answer was not to copy it. `plaza_frontage.tscn`, `plaza_fountain.tscn`,
## `plaza_paving.tscn`, `plaza_props.tscn` and `plaza_clock.tscn` are in this
## section's own scene list since 2026-08-19, so the dressing out here is the
## real thing and cannot drift from itself. The haze stops at the walls, which is
## the one part a stand-in has to own: the near run must collide and the far runs
## must not, and no mounted copy of the plaza can be two things at once.
## A far massing run, thinned to half its depth with its outer face left where it
## was.
##
## **The nudge cannot be made safe by choosing a better value, and this is what
## replaces trying.** `EAST_FAR_NUDGE` separates two massing copies from each
## other, and it was also carrying the separation between a massing copy and
## `plaza_frontage.tscn`, which is mounted alongside both. That second job is not
## one an offset can do: every frontage face sits at the wall's inner face plus
## some multiple of 5mm, and the seam ring's own swing is 5.25mm — wider than
## that pitch — so for *any* nudge there is a frontage plane the ring can walk
## onto. Three different pairs turned up in three consecutive runs, each in a
## different scene, each a genuine 2 to 15 m² fight and each one only there
## because a node count somewhere else had changed.
##
## Halving the depth moves the inner face five and a half metres back into the
## wall, which is a hundred times any offset the frontage uses, so the class is
## gone rather than dodged. It costs nothing: these runs are silhouette seen from
## sixty to ninety metres, they carry no collision, and the face that does the
## work — the one away from the fountain — does not move at all.
##
## Near-boundary runs are left alone. Their outer face is what the player stands
## against and their depth is what the gate passage is cut through.
func _mass_thinned(box: Dictionary) -> Dictionary:
	var at: Vector3 = box["at"]
	var size: Vector3 = box["size"]
	if not String(box["nm"]).begins_with("perim_"):
		return {"at": at, "size": size}
	var along_x := _run_along_x(size)
	var depth: float = size.z if along_x else size.x
	var keep := depth * 0.5
	if along_x:
		return {
			"at": at + Vector3(0.0, 0.0, signf(at.z) * depth * 0.25),
			"size": Vector3(size.x, size.y, keep),
		}
	return {
		"at": at + Vector3(signf(at.x) * depth * 0.25, 0.0, 0.0),
		"size": Vector3(keep, size.y, size.z),
	}


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
		var mat := _mass_material(box, "far")
		if near:
			mat = "accent" if nm.ends_with("_sign") else "building"
		# **The floor is not haze**, which `_plaza_from_the_east` worked out on its
		# own side and this one never inherited. `far` is the distance wash, and it
		# is the right answer for a silhouette ninety metres out across the lagoon;
		# applied to the plaza's own 104m of up-facing floor it came back as a
		# white sheet framed by the arch. From the overlook, six metres from the
		# reveal, the plaza did not read as hazy — it read as unbuilt.
		#
		# The plaza's own brick, which is world-space triplanar, so it lines up
		# with `terrace_floor` on this side of the wall without either of them
		# knowing about the other.
		if nm == "ground":
			mat = "brick"
		# Snapped to the centimetre, and that is not tidiness.
		#
		# The plaza's shapes carry hand displacement, and it runs *downward and
		# inward* — on the west side each successive node is a quarter-millimetre
		# further out in −X. `_add` displaces in +X by the same step in the same
		# order. Copied verbatim, the two cancel exactly: the arch's two piers and
		# the mass that used to span them came out sharing three planes over
		# ninety square metres, all of it hand displacement that had been carefully
		# arranged in the file they were read from. Snapping throws that away and
		# lets this scene's own ring do the separating, which is the only ring that
		# applies here.
		# Dropped a hand's width when it is only here to be seen down the tunnel.
		# The plaza's `ground` is one of these and it is 104m of up-facing floor
		# at exactly y=0, which is also `terrace_floor`'s — two floors on one
		# plane, five hundred square metres of it. Everything framed by the arch
		# is a silhouette between fifteen and a hundred metres off through a six
		# metre aperture, so a 12cm drop costs nothing and settles it for all of
		# them rather than special-casing the one that collides.
		var drop := 0.0 if (near or at.x < BELOW_WEST_X) else BELOW_FRAMED_DROP
		var thin := {"at": at, "size": size} if near else _mass_thinned(box)
		_box("far_%s" % nm, Vector3.ZERO,
			Vector3(thin["at"]).snapped(Vector3.ONE * 0.01)
				- Vector3(0.0, drop, 0.0), thin["size"],
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
	var mat := ""
	for raw in text.split("\n"):
		var line := raw.strip_edges()
		if line.begins_with("[node "):
			_keep_box(nm, origin, size, mat)
			nm = _quoted(line, "name=\"")
			origin = Vector3.ZERO
			size = Vector3.ZERO
			mat = ""
		elif line.begins_with("transform = Transform3D("):
			var n := _numbers(line)
			if n.size() >= 12:
				origin = Vector3(n[9], n[10], n[11])
		elif line.begins_with("size = Vector3("):
			var n := _numbers(line)
			if n.size() >= 3:
				size = Vector3(n[0], n[1], n[2])
		elif line.begins_with("material = SubResource("):
			mat = _quoted(line, "SubResource(\"")
	_keep_box(nm, origin, size, mat)
	return _plaza_boxes


func _keep_box(nm: String, origin: Vector3, size: Vector3, mat: String) -> void:
	if nm != "" and size.length() > 0.0:
		_plaza_boxes.append({"nm": nm, "at": origin, "size": size, "mat": mat})


## What a massing copy of a hand-authored plaza box should be painted.
##
## **A wash is for distance; it is not for identity.** Both stand-ins used to
## take a name prefix — `far_warm` for `tower_*`, `far` for everything else — and
## the clock tower is four boxes in two colours: a grey shaft and belfry with a
## terracotta cap and spire. Flattened to one tan, the one landmark that clears
## its own perimeter wall from either neighbour came back as a plain obelisk,
## which is most of what "the plaza looks oversimplified from out here" was
## about. It is the wheel's cars again — what *identifies* a thing has to be the
## same colour on both sides of a seam, and only what merely describes it gets
## hazed.
##
## So the accent reads its own accent and the rest takes the wash the caller
## asked for. Read off `plaza.tscn` rather than listed here, so repainting a box
## in the editor repaints both copies of it.
func _mass_material(box: Dictionary, wash: String) -> String:
	return "accent" if String(box.get("mat", "")) == "mat_accent" else wash


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
	_gate_house(GATE_WEST)
	for i in runs.size():
		_facade_wash(runs[i], i)
	# **The east gate is dressed last, after the washes, and it is not where it
	# reads best.** It belongs on the line above beside its twin. It cannot go
	# there: `_begin_scene` hands every shape a fraction of a millimetre of
	# displacement in build order and the ordinal wraps at 21, so eighty-odd nodes
	# inserted in the middle of this scene move every shape after them cyclically
	# and can put two untouched surfaces on one plane in a run nobody edited.
	# Appending shifts nothing. `_cascade(CASCADE_EAST)` sits at the end of
	# `_initialize` for the same reason and says so.
	_gate_house(GATE_EAST)

	# **The backs, appended for the reason the line above is appended.** Every
	# one of these is a surface a player stands against in the boardwalk or the
	# terraces and none of them had anything on it; they go last so that not one
	# shape already in this scene changes its seam displacement.
	for i in runs.size():
		_rear(runs[i], i)
	_gate_rear(GATE_WEST)
	_gate_rear(GATE_EAST)


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
	var along_x := _run_along_x(size)
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
## into a building rather than a hole in a wall.
##
## **Everything on this face is now broken at the opening**, where the plinth and
## the course were the only two that used to be. The other three ran straight
## across it because there was mass to run along: the lintel carried the wall
## over the gap. The top came off on 2026-08-16, the cutting is open to the sky,
## and a cornice crossing six metres of nothing at twelve metres up is a lintel
## drawn in trim — the one thing taking the top off was meant to be rid of.
##
## The two gates, as the facts that differ between them. Everything else about a
## gate — the plinth's 0.09 stand-off, the jamb's 0.36, the valance's drop, the
## thirteen bulbs — is shape, and shape is shared.
##
## `mass` is in the order the code reads it: north pier, south pier, beam. Named
## rather than found by shape, because there is no rule over a box that says
## "this one is a gate".
##
## The four `*_name` fields exist so the assertion can print the constant a
## reader has to go and open. An error that says a number is wrong and does not
## say where the other copy of it lives is an error somebody has to do the
## search for.
const GATE_WEST := {
	"prefix": "gate",
	"mass": ["arch_pier_north", "arch_pier_south", "arch_beam"],
	"inward": 1.0,
	"festoons": true,
	"axis_z": Plan.ARCH_AT.y,
	"width": Plan.ARCH_WIDTH,
	"height": Plan.ARCH_HEIGHT,
	"mouth_x": Plan.ARCH_MOUTH_X,
	"far_x": Plan.ARCH_FAR_X,
	"width_name": "ARCH_WIDTH",
	"height_name": "ARCH_HEIGHT",
	"mouth_name": "ARCH_MOUTH_X",
	"far_name": "ARCH_FAR_X",
}

## The east gate, and the only field of substance that differs is `inward`.
##
## The prefix is `east_gate` rather than `gate_east` so the two gates' nodes do
## not interleave when the scene is read as text, which is how everything in this
## file finds anything.
const GATE_EAST := {
	"prefix": "east_gate",
	"mass": ["east_pier_north", "east_pier_south", "east_beam"],
	"inward": -1.0,
	"festoons": true,
	"axis_z": Plan.EAST_GAP_AT.y,
	"width": Plan.EAST_GAP_WIDTH,
	"height": Plan.EAST_GAP_HEIGHT,
	"mouth_x": Plan.EAST_GAP_MOUTH_X,
	"far_x": Plan.EAST_GAP_FAR_X,
	"width_name": "EAST_GAP_WIDTH",
	"height_name": "EAST_GAP_HEIGHT",
	"mouth_name": "EAST_GAP_MOUTH_X",
	"far_name": "EAST_GAP_FAR_X",
}


## Read out of `plaza.tscn` like everything else here, so moving the arch in the
## editor moves its dressing. The three boxes are named rather than found by
## shape — an arch is the one thing in the perimeter with a hole in it, and there
## is no rule over a box that says "this one is a gate".
##
## **There are two gates and this dresses either.** The east gap was cut on
## 2026-08-17 on the fountain's own east-west line, and it is the west arch's
## arrangement rather than its coordinates: the plaza is not symmetric, so the
## piers are measured off the east wall's own faces and only their *relationship*
## to that wall is mirrored. What that leaves differing between the two is six
## facts, and they are in `GATE_WEST` and `GATE_EAST` below.
##
## `inward` is the one doing the real work. Every offset in this function and in
## `_gate_frontispiece` is a depth off the gate's plaza face, and the plaza is at
## +x from the west arch and −x from the east gate — so each is written once as
## `face + inward * d` rather than twice with a sign flipped. Get that wrong and
## the dressing builds itself inside the masonry, which is invisible rather than
## wrong-looking.
func _gate_house(gate: Dictionary) -> void:
	var names: Array = gate["mass"]
	var prefix: String = gate["prefix"]
	var inward: float = gate["inward"]
	var mass := {}
	for box in _plaza_scene_boxes():
		if String(box["nm"]) in names:
			mass[String(box["nm"])] = box
	if mass.size() < 3:
		push_error("the %s's three masses were not all found in %s — "
			% [prefix, PLAZA_SCENE_PATH] + "the gate would be dressed against nothing")
		return

	var north: Dictionary = mass[names[0]]
	var south: Dictionary = mass[names[1]]
	var beam: Dictionary = mass[names[2]]
	# The face you see from the plaza, the two outer edges, and the top.
	var face: float = north["at"].x + inward * north["size"].x * 0.5
	var from_z: float = north["at"].z - north["size"].z * 0.5
	var to_z: float = south["at"].z + south["size"].z * 0.5
	var top: float = north["at"].y + north["size"].y * 0.5
	# The opening, as the two pier faces that make it and the beam's underside.
	var open_n: float = north["at"].z + north["size"].z * 0.5
	var open_s: float = south["at"].z - south["size"].z * 0.5
	var head: float = beam["at"].y - beam["size"].y * 0.5
	# The numbers written down twice — here, where they are measured off the
	# scene, and in `ParkPlan`, where everything that reasons about the view
	# through the opening reads them. The clear height is the one that matters
	# most: the whole argument for taking the arch's top off was about clear
	# height, so it is exactly the number that must not drift quietly. A
	# centimetre of tolerance covers the hand displacement and nothing else.
	#
	# **The other three earn their place from the east.** `spoke_east` is laid
	# out of `EAST_GAP_MOUTH_X` and `EAST_GAP_FAR_X` while the piers that make
	# those faces are hand-typed in `plaza.tscn`, so a wall nudged in the editor
	# would leave the paving running through a pier — and paving is the one thing
	# in the park that draws itself over whatever it is standing in without
	# complaint. The west has the same pair of constants and had never checked
	# them either.
	for check in [
		[head, gate["height"], "clear height", gate["height_name"]],
		[face, gate["mouth_x"], "plaza face", gate["mouth_name"]],
		[north["at"].x - inward * north["size"].x * 0.5, gate["far_x"],
			"far face", gate["far_name"]],
		[open_s - open_n, gate["width"], "opening", gate["width_name"]],
	]:
		if absf(float(check[0]) - float(check[1])) > 0.01:
			push_error("the %s's %s is %.3f in %s but ParkPlan.%s says %.3f"
				% [prefix, check[2], check[0], PLAZA_SCENE_PATH, check[3], check[1]])

	# Plinth and ground-floor course, both broken at the opening because you walk
	# through it. The course sits at `FRONT_GROUND` so it runs on into the
	# shopfronts either side rather than starting a line of its own.
	# **Each run laps 2cm past the pier at both ends, which is the jambs' trick
	# and for the jambs' stated reason: so that no face of theirs lands on a face
	# of the piers'.** The plinth and the course had run exactly `from_z` to
	# `open_n`, which *is* the pier's own z extent — two pairs of coplanar faces
	# by construction, at the arch and at the gate both. The west got away with it
	# for as long as it did on nothing but luck of the draw: the seam displacement
	# is handed out in build order, the piers are hand-displaced in `plaza.tscn`,
	# and the two happened to differ there. At the east gate they landed on the
	# same plane and `coplanar_test` had four pairs. A coincidence that holds is
	# still a coincidence — the lap is what makes it a rule.
	for i in 2:
		var a: float = (from_z - 0.02) if i == 0 else (open_s - 0.02)
		var b: float = (open_n + 0.02) if i == 0 else (to_z + 0.02)
		_box("%s_plinth_%d" % [prefix, i], Vector3.ZERO,
			Vector3(face + inward * 0.09, 0.45, (a + b) * 0.5),
			Vector3(0.34, 0.9, b - a), "far_shade", 0.0, false)
		_box("%s_course_%d" % [prefix, i], Vector3.ZERO,
			Vector3(face + inward * 0.06, FRONT_GROUND, (a + b) * 0.5),
			Vector3(0.28, 0.34, b - a), "white", 0.0, false)

	# The surround. Two jambs and a head, each lapping 2cm into the opening so
	# that no face of theirs lands on a face of the piers'.
	for i in 2:
		var jz: float = (open_n - 0.33) if i == 0 else (open_s + 0.33)
		_box("%s_jamb_%d" % [prefix, i], Vector3.ZERO,
			Vector3(face + inward * 0.17, head * 0.5, jz),
			Vector3(0.36, head, 0.7), "white", 0.0, false)
	_box("%s_head" % prefix, Vector3.ZERO,
		Vector3(face + inward * 0.17, head + 0.36, gate["axis_z"]),
		Vector3(0.36, 0.72, float(gate["width"]) + 1.6), "white", 0.0, false)

	# Cornice and parapet, one run per pier. The parapet stands on the roof rather
	# than on the face, which is what stops a 12.5m mass ending in a raw edge
	# against the sky.
	#
	# Each run oversails its *outer* end and stops dead on the reveal at its inner
	# one, so the pair reads as two towers flanking a cut rather than as one
	# building with a gap punched in it. That is the silhouette the cutting wants:
	# the piers already stand 1.5–2m above the walls either side of them.
	for i in 2:
		# Lapped 3cm into the opening, which the plinth and the course above have
		# done since 2026-08-17 and this had not. `open_s` *is* the south pier's
		# own reveal face, so a run ending exactly there is a coplanar pair by
		# construction; it survived on the luck of the two displacements until a
		# change to this scene's node count reshuffled the ring. Three
		# centimetres at eleven metres up changes nothing about the two-towers
		# reading the paragraph above is protecting.
		var ca: float = (from_z - 0.26) if i == 0 else (open_s - 0.03)
		var cb: float = (open_n + 0.03) if i == 0 else (to_z + 0.26)
		_box("%s_cornice_%d" % [prefix, i], Vector3.ZERO,
			Vector3(face + inward * 0.14, top - FRONT_CORNICE * 0.5, (ca + cb) * 0.5),
			Vector3(0.5, FRONT_CORNICE, cb - ca), "white", 0.0, false)
	for i in 2:
		var pa: float = (from_z - 0.09) if i == 0 else open_s
		var pb: float = open_n if i == 0 else (to_z + 0.09)
		_box("%s_parapet_%d" % [prefix, i], Vector3.ZERO,
			Vector3(face - inward * 0.52, top + 0.56, (pa + pb) * 0.5),
			Vector3(1.24, 1.12, pb - pa), "building", 0.0, false)

	_gate_frontispiece(gate, face, head, top, from_z, to_z, open_n, open_s)


## The valance, the bulb run and the finials — the park's own entrance kit,
## applied to the entrance that did not have it.
##
## The west arch is the most important of the six ways out and until 2026-08-16
## it was the barest: a board on a wall, no valance, no bulbs, and **no night
## treatment of any kind** while all four scaffolded threshold mouths glow. It
## got away with that while it was a hole in a flat wall, because a hole in a
## wall is read by its surround. Taking the top off made it a gateway — two masses
## and something spanning — and a gateway with nothing on the span reads as
## unfinished. `_threshold_mouth` has said what an entrance looks like in this
## park since the thresholds were laid: piers with a finial, a beam, a valance
## hung on the plaza side, a row of bulbs, a tinted glow and a warm throat behind.
## This is that, at the scale of a 15m masonry gate house.
##
## **Everything here sits at or above the beam's soffit, and that is the whole
## constraint.** A valance hangs *below* the beam on the four mouths, because down
## there the sign is the point and nothing is looked at through the opening. Here
## the opening is the view west — it is why the top came off — so a canopy hung
## 30cm proud under the soffit would give back a third of what the day bought.
## The valance goes on the beam's face instead and the bulbs hang under the
## valance rather than under the beam, which lands them 47cm clear of the soffit.
## Anything added here later gets held to the same line.
func _gate_frontispiece(gate: Dictionary, face: float, head: float, top: float,
		from_z: float, to_z: float, open_n: float, open_s: float) -> void:
	var mid: float = gate["axis_z"]
	var prefix: String = gate["prefix"]
	var inward: float = gate["inward"]
	var width: float = gate["width"]

	# The canopy, in the blue against the board's terracotta. The four mouths
	# pair a warm board with a cool valance and a cool board with a warm one for
	# the same reason: the head of a gateway is three bands stacked within two
	# metres of each other, and three warm browns is one brown.
	_box("%s_valance" % prefix, Vector3.ZERO,
		Vector3(face + inward * 0.58, head + 0.92, mid),
		Vector3(0.6, 0.3, width + 3.6), "canvas_alt", 0.0, false)

	# A row of lights is what says a thing is open — the same sentence the alley
	# mouths and the threshold valances are built on. Spread across the opening
	# and a stride onto each pier, so the run reads as belonging to the gate
	# rather than to the hole.
	var bulbs := 13
	for i in bulbs:
		var t := (float(i) + 0.5) / float(bulbs)
		_sphere("%s_bulb_%d" % [prefix, i], Vector3.ZERO,
			Vector3(face + inward * 0.78, head + 0.62, lerpf(mid - 4.3, mid + 4.3, t)),
			0.15, "bulb")

	# Finials, one per pier, standing on the parapet. The caps are what carry a
	# gateway at distance — at sixty metres across the plaza the board is a smudge
	# and a silhouette is still a shape, which is the argument `_mouth_cap` makes
	# for the four mouths and it applies twice over here: this gate tops its own
	# wall, so its outline is against sky rather than against more building.
	for i in 2:
		var pz: float = (from_z + open_n) * 0.5 if i == 0 else (open_s + to_z) * 0.5
		_box("%s_finial_plinth_%d" % [prefix, i], Vector3.ZERO,
			Vector3(face - inward * 0.52, top + 1.40, pz),
			Vector3(1.5, 0.56, 1.5), "far_shade", 0.0, false)
		_sphere("%s_finial_%d" % [prefix, i], Vector3.ZERO,
			Vector3(face - inward * 0.52, top + 2.30, pz), 0.62, "white")

	# Three pools rather than one, and rather than one per bulb.
	#
	# The threshold valances use a single pool and give the reason: a row of omnis
	# produces one even wash at a fraction of the price, and the *reading* of a
	# bulb run comes from the emissive spheres, not from the light. That holds
	# there, because their pool hangs in open air over a passage floor. Here it
	# was 1.1m off a 9.6m board, and a point source that close to a big flat
	# surface does not wash it — it blooms on it, hot in the middle and dark at
	# both ends, which reads as one lamp behind the sign rather than thirteen
	# under it. Caught by the first night shot the arch has ever had.
	#
	# So: spread over six metres, further proud, and under half the energy each.
	# Three writes rather than thirteen, which keeps the argument above intact.
	# Warm rather than a colour of its own — the four mouths each get one so the
	# four stay distinguishable from the fountain, and this is not one of the
	# four. It is the gate to the section that is actually built.
	for i in 3:
		var gz: float = lerpf(mid - 3.0, mid + 3.0, (float(i) + 0.5) / 3.0)
		_omni("%s_valance_glow_%d" % [prefix, i],
			Vector3(face + inward * 1.35, head + 0.30, gz), "warm", 1.5, 11.0)

	# And the cutting behind it. A threshold unlit after dark is a black rectangle
	# and reads as closed — more so now than when it was a tunnel, because 13.5m
	# of open canyon at night is a slot of nothing where the tunnel at least had
	# a lit far end. Set well back so the source is not visible from the plaza.
	_omni("%s_throat" % prefix, Vector3(face - inward * 7.0, 5.4, mid),
		"warm", 2.6, 13.0)

	# **Both gates now, and the east's argument is different from the west's.**
	# The west's run rides a rising plane derived from the wheel — the plane the
	# beam already hides, because anything under it draws itself across the west's
	# biggest silhouette. The east has no such plane to borrow and this file said
	# so for a day: its beam crops the rim on purpose. What it has instead is a
	# monument, a forecourt and a hill, none of which a wire at a constant height
	# under the soffit crosses. So the east hangs level and the west hangs rising,
	# and `rise` is the one number that differs.
	if gate["festoons"]:
		_gate_festoons(gate, top, open_n, open_s)


## The two ends of the run, as x. Clear of the beam's west face at −31.4 and
## short of the wall's own west face at −44, so the whole thing is inside the
## cutting and nothing hangs out over the terrace.
const FESTOON_FROM_X := -31.7
const FESTOON_TO_X := -43.3

## Wires, not anchors — there is one more anchor than there are wires, and they
## alternate reveals, so six wires is four pins on the north pier and three on
## the south and a zigzag with a stride of 1.93m.
const FESTOON_SPANS := 6

## How far the wire drops at mid-span. Added to the anchor height along with the
## flag drop, so that the *lowest* point of the run rides the free line rather
## than the anchors doing so and everything else hanging through it.
const FESTOON_SAG := 0.5

## The flag, and the drop is **computed from it rather than typed**. A guessed
## 0.7 left the tightest flag corner 51mm clear of the free line, which is
## thinner than the beam's own 138mm against the wheel — so the decoration would
## have been the tighter of the two constraints, which is precisely backwards.
##
## The corner and not the edge: a box rotated by `LEAN` puts its lowest point at
## `h/2·cos + w/2·sin`, which is the rotated-box rule that cost three centimetres
## on a wheelchair footplate and three metres on a cascade wing. It is 27mm here.
## The rule does not care about the scale, and this is the third scale it has been
## applied at.
const FESTOON_FLAG_HANG := 0.34
const FESTOON_FLAG_H := 0.6
const FESTOON_FLAG_W := 0.5
const FESTOON_FLAG_LEAN := 0.11

## What the lowest thing on the run keeps off the plane the beam hides. Stated
## rather than absorbed, so that anybody who changes the flag or the lean can see
## what they are spending.
const FESTOON_CLEAR := 0.2

## Segments per wire. The flag runs are sampled finer because the flags hang at
## the interior points: seven steps is six flags at 0.86m on a 5.9m wire, which
## is bunting, and six steps is five bulbs at 1.03m, which is a light string.
const FESTOON_BULB_STEPS := 6
const FESTOON_FLAG_STEPS := 7

## How far the pin stands out of the reveal. The wire ends on its tip; the
## cylinder is drawn twice that long about the midpoint, so it laps the same
## distance back into the masonry rather than being stuck on the face.
const FESTOON_PIN := 0.42

## **Both observed, and marked observed because that is the thing this file keeps
## losing.** The camera is not at the player: the spring arm hangs it about 2.5m
## back, which is further from the mouth and so tighter than a standing eye. Its
## *height* moves with the shot's pitch — 1.10 to 1.47 measured in the running
## game across the west poses — and a lower eye needs more clearance, so the run
## is sized on 1.10 rather than on the middle of the range.
const FESTOON_EYE := 1.10
const FESTOON_ARM := 2.5

## Signal flags, in the four colours the park already owns. No two adjacent are
## alike and the cycle is nine against six flags a wire, so the pattern does not
## line up wire to wire. One box each: at greybox fidelity a code flag is a
## coloured rectangle in a row of coloured rectangles, and splitting each into
## bands would put two 0.15m² faces on the same plane eighteen times over for
## detail the rest of the park does not carry.
const FESTOON_HOIST := ["red", "white", "blue", "yellow", "red", "blue",
	"white", "yellow", "blue"]


## Festoons across the cutting: bulb strings and signal-flag bunting, zigzagged
## between the two pier reveals, alternating one and then the other.
##
## The cutting is 13.5m of open canyon with 12.5m walls and nothing spanning it
## between the beam at the mouth and the sky. That is what the top coming off
## bought and it is also what it cost — `_gate_frontispiece` makes the argument
## for the near plane, that a gateway with nothing on the span reads as
## unfinished, and past the beam the same sentence applies to the passage.
##
## **They hang above the beam's own sight-line and not where the tunnel's ceiling
## was, and that difference is the whole of what 2026-08-16 bought.** The old
## soffit ran flat at 5m. That plane is not "decoration slightly in the way of the
## view" — it *is* the view: the beam clears the wheel's rim by 0.138m at
## `ARCH_RIM_CLEAR_X`, 6.298 built against 6.16 required, so there is no band
## under the beam that costs only sky. A wire at 5m sits 1.4m below the free line
## at the mouth and 5.4m below it at the far end, and a run of bunting there would
## draw itself straight across the west's biggest silhouette from everywhere in
## the plaza. Which is the failure the lintel was removed for, rebuilt in cloth.
##
## So the run is hung on the plane the beam already hides. From the binding
## standpoint the ray grazing the soffit rises 0.306 per metre west, putting the
## free line at 6.30 at the mouth and 10.21 at the far end; anchors sit a sag and
## a flag's drop above that, so the lowest flag at mid-span rides it. Standing
## *closer* to the arch the beam subtends more and hides more, so the far
## standpoint is the binding one — the same argument and the same standpoint
## `ARCH_HEIGHT` is itself set at, which is what makes this safe by construction
## rather than by a second survey. Nothing here can be the thing that crops the
## wheel; the beam crops first, at every pose, or neither does.
##
## What that means for how it reads is worth saying out loud, because it is a
## real trade and not a free one: this is **not** an invitation seen from the
## fountain. From the plaza the run sits behind the beam and you get the sign and
## the bulb row under it, exactly as before. It appears the moment you walk under
## the beam, overhead — the strings lift away west and open the slot — and it is
## a thing you look up at rather than ahead at, 44° to 79° above level from the
## middle of the cutting. A passage dressed for the length of the passage rather
## than a shopfront for it.
##
## **And it is only ever seen from the plaza's side of the seam.** This scene is
## `plaza_frontage.tscn`, the seam is at `ARCH_SEAM_AT` in the middle of the
## cutting, and `ParkSections` frees the plaza on the way across — so from the
## terrace looking back there are no festoons, for the same reason there is no
## sign, no valance and no bulb row: everything behind the arch out there is
## `_plaza_from_below`'s massing copy, which carries shapes and deliberately not
## detail. The run therefore reads over about seven metres of walking, from the
## beam to the crossing. Putting it on the far side too would mean teaching the
## stand-in to reproduce detail, which is the one thing that comment argues
## against — it is a real limit, not an oversight, and it is the sign's limit
## already.
func _gate_festoons(gate: Dictionary, top: float, open_n: float, open_s: float) -> void:
	var inward: float = gate["inward"]
	var mouth: float = gate["mouth_x"]
	var far: float = gate["far_x"]
	var height: float = gate["height"]
	# The plane the beam hides, from the standpoint the beam is bound at — west
	# only. `ARCH_RIM_CLEAR_X` is a fact about looking at the wheel through the
	# west arch and means nothing on this side of the park, so the east takes a
	# level run and derives nothing.
	var rise := 0.0
	if inward > 0.0:
		var cam_x: float = Plan.ARCH_RIM_CLEAR_X + FESTOON_ARM
		rise = (Plan.ARCH_HEIGHT - FESTOON_EYE) / (cam_x - Plan.ARCH_MOUTH_X)
	# The bottom corner of the lowest flag, measured from its own wire.
	var drop: float = FESTOON_FLAG_HANG + FESTOON_CLEAR \
		+ FESTOON_FLAG_H * 0.5 * cos(FESTOON_FLAG_LEAN) \
		+ FESTOON_FLAG_W * 0.5 * sin(FESTOON_FLAG_LEAN)

	# The run's ends, off the gate's own mouth and far face rather than off two
	# constants that were the west's. Same insets: 1.2m in from the mouth so the
	# first span is clear of the beam, 0.7m short of the far face so nothing hangs
	# out past the wall.
	var from_x: float = mouth - inward * 1.2
	var to_x: float = far + inward * 0.7
	var anchors: Array[Vector3] = []
	for i in FESTOON_SPANS + 1:
		var x := lerpf(from_x, to_x, float(i) / float(FESTOON_SPANS))
		var z: float = (open_n + FESTOON_PIN) if i % 2 == 0 else (open_s - FESTOON_PIN)
		var free: float = height + (mouth - x) * inward * rise
		anchors.append(Vector3(x, free + FESTOON_SAG + drop, z))

	# Cheap and general: assert the run is where the run belongs. Everything is
	# inside the cutting in x, and the highest anchor is under the pier top —
	# which is the end the rising line runs at, and the one that would climb out
	# through the sky if the eye height or the span ever moved.
	for a in anchors:
		if (a.x - mouth) * inward > 0.0 or (a.x - far) * inward < 0.0:
			push_error("a festoon anchor at x %.2f is outside the cutting" % a.x)
			return
	if anchors[FESTOON_SPANS].y > top - 0.6:
		push_error("the west end of the festoon run stands at %.2f against a pier "
			% anchors[FESTOON_SPANS].y + "top of %.2f — it is over the wall" % top)
		return

	# A pin per anchor, standing out of the reveal and lapping the same distance
	# back into it, so the wire ends on something rather than in masonry.
	for i in anchors.size():
		var a: Vector3 = anchors[i]
		var wall: float = open_n if i % 2 == 0 else open_s
		_cyl("%s_festoon_pin_%d" % [gate["prefix"], i], Vector3(a.x, a.y, (wall + a.z) * 0.5),
			Vector3.ZERO, 0.06, absf(a.z - wall) * 2.0, "metal", 0.0, 8, false, PI * 0.5)

	for w in FESTOON_SPANS:
		var a: Vector3 = anchors[w]
		var b: Vector3 = anchors[w + 1]
		var flags: bool = w % 2 == 1
		var steps: int = FESTOON_FLAG_STEPS if flags else FESTOON_BULB_STEPS
		var pts: Array[Vector3] = []
		for s in steps + 1:
			var t := float(s) / float(steps)
			var p := a.lerp(b, t)
			p.y -= FESTOON_SAG * sin(PI * t)
			pts.append(p)
		for s in steps:
			_strut("%s_festoon_wire_%d_%d" % [gate["prefix"], w, s], pts[s], pts[s + 1], 0.045, "metal")
		if flags:
			for f in steps - 1:
				var p: Vector3 = pts[f + 1]
				# Yaw off the neighbours rather than off one segment, so a flag on
				# a sagging wire hangs along the curve instead of along the chord
				# it happens to sit at the end of.
				var d: Vector3 = pts[f + 2] - pts[f]
				# A little wind. Alternating rather than random, because two
				# adjacent flags leaning the same way read as a printing error and
				# two leaning apart read as a breeze.
				var lean: float = FESTOON_FLAG_LEAN * (1.0 if f % 2 == 0 else -1.0)
				var hoist: String = FESTOON_HOIST[(w / 2 * (FESTOON_FLAG_STEPS - 1)
					+ f) % FESTOON_HOIST.size()]
				_box("%s_festoon_flag_%d_%d" % [gate["prefix"], w, f],
					Vector3(p.x, p.y - FESTOON_FLAG_HANG, p.z), Vector3.ZERO,
					Vector3(0.03, FESTOON_FLAG_H, FESTOON_FLAG_W), hoist,
					atan2(d.x, d.z), false, lean)
		else:
			for bl in steps - 1:
				_sphere("%s_festoon_bulb_%d_%d" % [gate["prefix"], w, bl], pts[bl + 1],
					Vector3(0.0, -0.22, 0.0), 0.13, "bulb")

	# Two pools, hung at the strings rather than over the floor. `gate_throat`
	# already lights the floor from 5.4 and is the reason the cutting does not read
	# as closed after dark; these are for the wires and the flags themselves and
	# for the top of the reveals, which is 12.5m of masonry that nothing else in
	# the park reaches. The emissive bulbs carry the look of the run, as they do
	# on the street and on the promenade — this is so the bunting between them is
	# a colour at night and not a silhouette.
	for i in 2:
		var w: int = 1 if i == 0 else 4
		var mid: Vector3 = anchors[w].lerp(anchors[w + 1], 0.5)
		_omni("%s_festoon_glow_%d" % [gate["prefix"], i],
			Vector3(mid.x, mid.y - FESTOON_SAG - 0.3, mid.z), "warm", 1.5, 12.0)


## One run of perimeter, from the pavement to the skyline.
##
## Local space is the wall's: +X along it, +Z out of its inner face, so every
## number below is read the way you would read it standing in front of the
## building. Which face is the inner one is decided by which side of the run the
## fountain is on, so nothing here has to know which wall it is working on.
## The perimeter's own depth, worked out from the runs rather than written down.
##
## Every range of the perimeter is one wall of one thickness — that is what makes
## it a perimeter — so the depth is the horizontal dimension the fifteen runs
## agree on, and the *other* horizontal dimension of a run is its length. Which
## sounds like a long way round "the longer side is the length", and is not: the
## east wall is 11m deep and `perim_e_mid_n` is 10.4m long, because the gate ate
## most of it. **That one run was shorter than the wall was thick**, so the
## longer-side rule turned it ninety degrees and dressed its north end face
## instead of its elevation. Its whole frontage was built at z −9, which is
## buried inside `east_pier_north`, and the face beside the gate that both the
## belvedere and the forecourt look straight at had nothing on it at all. It read
## as the plaza being unfinished in the one direction somebody had just cut a
## gate through.
##
## A mode rather than a minimum, because the runs are not all the same length and
## `perim_s_west` is 11.7 by 11 — near enough to the depth that any tolerance
## wide enough to catch `perim_e_mid_n` would catch that as well and turn a
## corner block the wrong way instead.
var _perim_depth := 0.0


func _perimeter_depth() -> float:
	if _perim_depth > 0.0:
		return _perim_depth
	var tally := {}
	for run in _perimeter_runs():
		var s: Vector3 = run["size"]
		for d in [snappedf(s.x, 0.01), snappedf(s.z, 0.01)]:
			tally[d] = int(tally.get(d, 0)) + 1
	var best := 0.0
	var best_n := 0
	for d in tally:
		if int(tally[d]) > best_n:
			best_n = int(tally[d])
			best = float(d)
	_perim_depth = best
	return _perim_depth


## True when this run's length is measured along X — so its faces point along Z.
##
## Decided by which dimension is the wall's depth, never by which is longer. See
## `_perimeter_depth`. Falls back to the longer side for a run that is square in
## plan, where the question has no answer and either is as good.
func _run_along_x(size: Vector3) -> bool:
	var depth := _perimeter_depth()
	var dx := absf(size.x - depth) < 0.005
	var dz := absf(size.z - depth) < 0.005
	if dz and not dx:
		return true
	if dx and not dz:
		return false
	return size.x >= size.z


func _facade(run: Dictionary, idx: int) -> void:
	var c: Vector3 = run["at"]
	var s: Vector3 = run["size"]
	var along_x: bool = _run_along_x(s)
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
	var storeys := _storey_count(upper)
	var floors := _storey_heights(upper, storeys)
	var ground := FRONT_GROUND + jog

	# Floor lines, one per storey including the shopfront's own cornice at 4.3.
	# Run the whole length rather than per bay: a course that stops at every
	# joint reads as a row of sheds, and the point of these is that a run is one
	# building with several shops in it.
	#
	# They thin as they climb, by the same ratio the storey they sit under does.
	# Trim held at one size up a diminishing wall is the tell that gives the trick
	# away — it is the only thing in shot whose true size the eye already knows.
	var y := ground
	for st in storeys:
		var k: float = floors[st] / floors[0]
		_box("%s_course_%d" % [tag, st], base, Vector3(0.0, y, 0.14),
			Vector3(length - 0.5, 0.26 * k, 0.46 * k), "white", theta, false)
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

## Where the diminution stops. Main Street's ladder is 1, 5/8, 1/2 and then it
## *ends* — there is no fourth term, because a storey built at 0.39 of the ground
## floor is not a storey any more, it is a band of trim with windows in it.
##
## Compounding 0.78 without a floor is what broke the tall runs. The east wall is
## 19m, which `_storey_count` reads as five upper storeys, and the fifth came out
## at 0.37 — 1.55m, holding a window 0.80 wide and 0.50 high. From the fountain
## that is not a small distant floor, it is a squashed one, and the eye reads the
## squashing rather than the distance.
const FRONT_FALLOFF_MIN := 0.58

## Nothing thinner than this counts as a storey. The ladder's last rung is always
## its shortest, so this is only ever a reason to build one fewer.
const FRONT_STOREY_MIN := 1.9

## A window's height as a fraction of the storey it is in. **A fraction and not a
## margin**, which is the whole of the second half of the fix.
##
## It used to be `min(2.2, storey - 1.05)` — a constant subtracted for the sill
## and the head. A constant taken out of a shrinking storey is a growing *share*
## of it: 25% of the east wall's second floor and 68% of its fifth, so the
## openings collapsed far faster than the storeys did and the top row read as
## letterboxes. The `min` broke the same ladder from the other end, capping the
## two lowest storeys at the same 2.2 while the storeys themselves differed by a
## metre — so the diminution did not start until the third floor and then fell
## off a cliff.
const FRONT_WIN_H := 0.56


## The ladder of upper storeys, tallest first, filling `upper` exactly.
##
## Exactly, because the floor lines are laid on it and a course that lands past
## the cornice is worse than an approximate storey. So the weights below set the
## *proportions* and the normalisation sets the size.
func _storey_heights(upper: float, storeys: int) -> Array:
	var weights := _storey_weights(storeys)
	var total := 0.0
	for w in weights:
		total += w
	var out: Array = []
	for i in storeys:
		out.append(upper * weights[i] / total)
	return out


func _storey_weights(storeys: int) -> Array:
	var out: Array = []
	for i in storeys:
		out.append(maxf(pow(FRONT_FALLOFF, float(i)), FRONT_FALLOFF_MIN))
	return out


## How many upper storeys a wall of this much spare height carries.
##
## `round(upper / 3)` is the guess, and then two rules correct it, both of which
## exist because the heights are normalised to fill: the ladder's proportions are
## fixed but its *scale* is whatever the wall left over, so the same weights land
## differently on a 10m wall and a 19m one.
##
## The second rule is the one that matters and it was missing entirely. On the
## 19m east wall the first upper storey came out at 4.18m against a 4.3m
## shopfront — no diminution at all at the bottom, all of it crammed into the top
## two floors. Forced perspective that starts three storeys up is not forced
## perspective, it is a wall with some small windows near the roof, and that is
## what "some of the buildings" were doing.
func _storey_count(upper: float) -> int:
	var n: int = clampi(int(round(upper / 3.0)), 1, 5)
	while n > 1 and float(_storey_heights(upper, n)[n - 1]) < FRONT_STOREY_MIN:
		n -= 1
	while n < 5:
		if float(_storey_heights(upper, n)[0]) <= FRONT_GROUND:
			break
		if float(_storey_heights(upper, n + 1)[n]) < FRONT_STOREY_MIN:
			break
		n += 1
	return n


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
	# The windows shrink with their storey, in width as well as height, and every
	# opening on a run is therefore the same *shape* — which is what sells the
	# lie, and which this did not actually do until 2026-08-15. Width fell off at
	# `FALLOFF^(st*0.6)` and height at a constant subtraction, so three different
	# rates were diminishing one wall and the aspect ratio ran from 0.66 at the
	# shopfront to 1.61 at the roof: portrait windows at the bottom and slots at
	# the top, on the same building.
	#
	# **The scale is read off the storeys rather than recomputed from the ratio.**
	# That is the structural half of the fix: `floors` is already the ladder, the
	# normalisation is a common factor that cancels, and a window that takes its
	# size from the floor it stands on cannot drift away from it the way two
	# copies of the same arithmetic did.
	var wins := 2 if bw < 7.2 else 3
	var ww0 := minf(1.45, bw / (float(wins) * 2.15))
	var sill := ground
	for st in floors.size():
		var sh: float = floors[st]
		var k: float = sh / float(floors[0])
		var ww := ww0 * k
		var wh := sh * FRONT_WIN_H
		var y := sill + sh * 0.52
		for w in wins:
			var t := (float(w) + 0.5) / float(wins)
			# The margins stay at the ground storey's width so a column of
			# windows keeps one centre line all the way up. Shrinking those too
			# would pull the outer columns inward floor by floor and lean the
			# whole bay, which is a different building trick and not this one.
			var wx := lerpf(-bw * 0.5 + ww0, bw * 0.5 - ww0, t)
			_box("%s_win_%d_%d" % [nm, st, w], at, Vector3(wx, y, 0.07),
				Vector3(ww, wh, 0.14), "glass", theta, false)
			_box("%s_head_%d_%d" % [nm, st, w], at, Vector3(wx, y + wh * 0.5 + 0.13 * k, 0.11),
				Vector3(ww + 0.34 * k, 0.2 * k, 0.26), "white", theta, false)
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


## Where the dark band at the foot of a rear elevation stops.
##
## Knee height rather than the front's 0.9m plinth: out here it is a kerb-and-
## splash band under brickwork, not the base of a shopfront, and the two faces
## of one block should not agree about a line neither of them can see the other
## draw.
const REAR_PLINTH := 1.15

## How far the plinth and the downpipes go below the paving.
##
## Not a detail: at zero the plinth's underside is on the plaza box's own
## underside, which both massing copies stand a duplicate of, and on the foot of
## every pipe standing on it.
const REAR_BURY := 0.22

## How far the gate's own rear banding sits above the perimeter's. See the
## comment on `_gate_rear`'s plinth: 43mm, because `_rear` jogs by multiples of
## 31 and this must not land on one or come within the seam ring's 5.25mm of one.
const GATE_REAR_JOG := 0.043


## The outside of the perimeter, which is a **back** and not a second front.
##
## `_facade` is applied to inner faces only, and that was right for as long as
## the plaza was the only place anybody stood. It has not been right since the
## west seam moved to the arch: crossing it puts the player on the terrace two
## metres from the outer face of `perim_w_arch_n`, and the east gate delivers
## them into a fourteen-metre forecourt against `perim_e_mid_s`, which is
## nineteen metres of wall with nothing whatever on it. Shot from either, the
## park was a grey cliff — no opening, no course, no colour, and a roofline that
## is a raw edge, because the front's parapet stands eleven metres away on the
## far side of the block.
##
## **The runs are 11m deep, so these are two elevations of one building rather
## than two treatments of one wall.** That is the whole argument for what goes on
## here: a back has a smaller vocabulary than a front by nature, and the smaller
## vocabulary is also the cheap one. Brick to the first floor where the front is
## rendered and glazed, plain openings sitting on their own course with no heads
## and no awnings, service doors and roller shutters instead of display bays,
## pilasters and downpipes, and on about half the runs the painted sign that a
## front never carries because a front has a fascia to put its name on.
##
## The storey ladder and the bay count are `_facade`'s, read from the same `jog`,
## so the courses meet round the corner and the two faces agree about where the
## party walls are. Everything else disagrees on purpose.
##
## **Every run gets one, not only the two a player can reach today.** Which
## outer faces are stood against is exactly the kind of list that goes stale the
## day a section is built — the north and south backs are behind unbuilt ground
## now and will be somebody's approach later — and the cost of being general
## here is about forty nodes a run.
func _rear(run: Dictionary, idx: int) -> void:
	var c: Vector3 = run["at"]
	var s: Vector3 = run["size"]
	var along_x: bool = _run_along_x(s)
	var length: float = s.x if along_x else s.z
	var thick: float = s.z if along_x else s.x
	var h: float = s.y
	# `_facade`'s normal with the sign flipped: +Z now points *away* from the
	# fountain, so every offset below reads the way you would read it standing on
	# the terrace or in the forecourt.
	var normal := (Vector3(0.0, 0.0, signf(c.z)) if along_x
		else Vector3(signf(c.x), 0.0, 0.0))
	if normal.length_squared() < 0.5:
		normal = Vector3(0.0, 0.0, 1.0) if along_x else Vector3(1.0, 0.0, 0.0)
	var theta := atan2(normal.x, normal.z)
	var base := Vector3(c.x, 0.0, c.z) + normal * (thick * 0.5 - FRONT_SINK)
	var tag := "r%02d" % idx

	var usable := length - FRONT_INSET * 2.0
	var bays: int = maxi(1, int(ceil(usable / FRONT_BAY_MAX)))
	var bw := usable / float(bays)

	var jog := 0.031 * float((idx * 3) % 5)
	var upper := h - FRONT_GROUND - jog - FRONT_CORNICE
	var storeys := _storey_count(upper)
	var floors := _storey_heights(upper, storeys)
	var ground := FRONT_GROUND + jog
	var wall_top := h + jog - FRONT_CORNICE

	# The service storey: a dark band to knee height and brickwork above it to
	# the first floor line. **This is where the colour comes from**, and it is
	# put at the bottom rather than over the whole face on purpose — the plaza's
	# palette is grey with accents in it, and repainting a hundred and twenty
	# metres of perimeter terracotta would move the park to answer a complaint
	# about one elevation. At the bottom it is the part the player is standing in
	# front of, and the silhouette against the sky is untouched.
	#
	# `brick` rather than a flat tint because it is the one warm material the
	# park already has that is *textured*, and half of "featureless" is that a
	# CSG box has no surface at all. It is world-space triplanar, so it needs no
	# UVs on a vertical face and tiles continuously across the run's own joints.
	# Bottomed a hand *below* the paving rather than on it. At y=0 its underside
	# is on the plaza box's own underside — which the two massing copies stand a
	# duplicate of — and on every downpipe's foot: three coplanar pairs from one
	# number, and a plinth that stops exactly at the ground is the one that looks
	# wrong anyway.
	_box("%s_plinth" % tag, base,
		Vector3(0.0, (REAR_PLINTH - REAR_BURY) * 0.5, 0.09),
		Vector3(length - 0.4, REAR_PLINTH + REAR_BURY, 0.24),
		"far_shade", theta, false)
	# Bottomed *inside* the plinth rather than on top of it: two boxes that meet
	# exactly share a horizontal plane, and the house rule is that parts run into
	# each other rather than butting.
	_box("%s_base" % tag, base,
		Vector3(0.0, (ground + REAR_PLINTH - 0.3) * 0.5, 0.06),
		Vector3(length - 0.5, ground - REAR_PLINTH + 0.3, 0.18),
		"brick", theta, false)

	# Floor lines. Thinner and shallower than the front's, and they double as the
	# windows' sills — which is why there are no separate sills below. A back
	# gets one horizontal per storey and that is all it gets.
	var course_y: Array = []
	var y := ground
	for st in storeys:
		var k: float = floors[st] / floors[0]
		course_y.append(y)
		_box("%s_course_%d" % [tag, st], base, Vector3(0.0, y, 0.10),
			Vector3(length - 0.7, 0.20 * k, 0.34 * k), "white", theta, false)
		y += floors[st]

	# Pilasters on the bay joints, carried in the brick rather than in render.
	# They are the piece that stops the wall being a plane: four of them across a
	# twenty metre run put a vertical shadow every five metres, which is what the
	# eye reads as structure at the range the forecourt puts you at.
	for j in bays + 1:
		var px := -usable * 0.5 + bw * float(j)
		_box("%s_pil_%d" % [tag, j], base,
			Vector3(px, (REAR_PLINTH + wall_top) * 0.5, 0.07),
			Vector3(0.62, wall_top - REAR_PLINTH, 0.2), "brick", theta, false)

	# One run in two carries a painted wall sign, and it takes the top storey's
	# windows with it. A blank top floor with lettering across it is what a back
	# actually looks like, and it is the only place on this elevation with room
	# for something big enough to read from the far side of a forecourt.
	var sign: bool = storeys >= 2 and _hash01(idx, 11, 61) < 0.5
	var glazed: int = storeys - 1 if sign else storeys

	for b in bays:
		var bx := -usable * 0.5 + bw * (float(b) + 0.5)
		var at := _place(base, Vector3(bx, 0.0, 0.0), theta)
		var nm := "%s_b%d" % [tag, b]
		# Ground level is doors. Half of them are a loading shutter and half a
		# pair of leaves with a lintel over — the shutter is what says the far
		# side of this is a stockroom rather than a room.
		# **Proud of the plinth, and cut into the paving.** Both were wrong the
		# first time and neither showed in a screenshot taken from standing: at
		# 0.13 the leaf sat *behind* the plinth's own face, so its bottom metre
		# was buried in the band it is supposed to open through, and at y=0 its
		# underside shared a plane with the massing copy of the wall it is in.
		var dw := minf(bw * 0.42, 3.4)
		if _hash01(idx, b, 29) < 0.5:
			_box("%s_shutter" % nm, at, Vector3(0.0, 1.6, 0.26),
				Vector3(dw, 3.4, 0.14), "metal", theta, false)
			_box("%s_shutter_head" % nm, at, Vector3(0.0, 3.46, 0.3),
				Vector3(dw + 0.4, 0.32, 0.22), "far_shade", theta, false)
		else:
			var paints := ["blue", "red", "wood", "canvas_alt"]
			_box("%s_door" % nm, at, Vector3(0.0, 1.2, 0.26),
				Vector3(minf(dw, 1.9), 2.6, 0.14),
				paints[(idx * 2 + b) % paints.size()], theta, false)
			_box("%s_door_head" % nm, at, Vector3(0.0, 2.62, 0.3),
				Vector3(minf(dw, 1.9) + 0.36, 0.26, 0.22), "white", theta, false)

		# Openings. Nothing but a dark panel standing on the course — no head, no
		# reveal, no surround. The front's windows are an illusion of depth built
		# out of three shapes; a back window is a hole, and one shape is what a
		# hole looks like.
		var wins := 2 if bw < 7.6 else 3
		var ww0 := minf(1.15, bw / (float(wins) * 2.6))
		for st in glazed:
			var sh: float = floors[st]
			var k: float = sh / float(floors[0])
			var ww := ww0 * k
			var wh := sh * 0.44
			for w in wins:
				var t := (float(w) + 0.5) / float(wins)
				var wx := lerpf(-bw * 0.5 + ww0 * 1.4, bw * 0.5 - ww0 * 1.4, t)
				_box("%s_win_%d_%d" % [nm, st, w], at,
					Vector3(wx, float(course_y[st]) + 0.16 + wh * 0.5, 0.08),
					Vector3(ww, wh, 0.16), "glass", theta, false)

	if sign:
		var st: int = storeys - 1
		var sh: float = float(floors[st])
		var colours := ["red", "blue", "accent", "yellow"]
		_box("%s_sign" % tag, base,
			Vector3(0.0, float(course_y[st]) + sh * 0.52, 0.09),
			Vector3(minf(usable * 0.72, 13.0), sh * 0.62, 0.14),
			colours[(idx * 5) % colours.size()], theta, false)
		_box("%s_sign_rule" % tag, base,
			Vector3(0.0, float(course_y[st]) + sh * 0.52, 0.13),
			Vector3(minf(usable * 0.72, 13.0) - 0.9, sh * 0.20, 0.1),
			"white", theta, false)

	# Downpipes, which are the cheapest thing on this list and the one nobody
	# would put on a front. Offset off the pilasters rather than on them, so a
	# pipe reads as bolted to the wall beside a pier instead of as a moulding
	# down the middle of one.
	for j in bays + 1:
		var px := -usable * 0.5 + bw * float(j) + (0.55 if j == 0 else -0.55)
		# `metal`, and thin. At `far_shade` and 22cm across they came out as pale
		# columns standing beside the pilasters rather than as pipework on the
		# wall — the same value as the plinth and the parapet cap, in full sun,
		# on the one element here whose whole job is to be a dark vertical.
		_cyl("%s_pipe_%d" % [tag, j], base,
			Vector3(px, (wall_top - REAR_BURY * 2.0) * 0.5, 0.2), 0.075,
			wall_top + REAR_BURY * 2.0, "metal", theta, 8, false)
		_box("%s_hopper_%d" % [tag, j], base,
			Vector3(px, wall_top - 0.45, 0.22),
			Vector3(0.34, 0.5, 0.34), "metal", theta, false)

	# A cornice and a parapet of its own. Without them the block's outer edge is
	# the top of a raw box against the sky — the front's parapet is eleven metres
	# away on the other side of an 11m-deep roof and does nothing for this side.
	_box("%s_cornice" % tag, base,
		Vector3(0.0, wall_top + FRONT_CORNICE * 0.25, 0.16),
		Vector3(length - 0.3, FRONT_CORNICE * 0.5, 0.54), "white", theta, false)
	_box("%s_parapet" % tag, base, Vector3(0.0, h + jog + 0.40, 0.0),
		Vector3(length + 0.06, 1.0, 0.66), "building", theta, false)
	_box("%s_par_cap" % tag, base, Vector3(0.0, h + jog + 0.95, 0.03),
		Vector3(length + 0.18, 0.18, 0.86), "far_shade", theta, false)


## A gate from outside, and the passage through it.
##
## `_gate_house` dresses the plaza face and stops there, which left the two
## surfaces the player actually walks up to and along completely bare: the outer
## face, which is what the terrace and the forecourt look at head-on, and the two
## reveals of the throat, which are 13.5m long and 6m apart and fill most of the
## frame for the whole length of the crossing.
##
## **There is no head out here and there must not be.** The cutting is open to
## the sky and the beam is at the plaza face, so from outside the opening is a
## slot between two towers. A band across the top of it would be the lintel
## drawn in trim, which is the thing taking the arch's top off was meant to be
## rid of — `_gate_house` says so about its own cornice.
##
## It takes the gate dicts, so `inward` does the same work here it does there —
## with the sign flipped once, into `out`, because everything on this side is a
## depth off the *far* face.
func _gate_rear(gate: Dictionary) -> void:
	var names: Array = gate["mass"]
	var prefix: String = gate["prefix"]
	var inward: float = gate["inward"]
	var mass := {}
	for box in _plaza_scene_boxes():
		if String(box["nm"]) in names:
			mass[String(box["nm"])] = box
	if mass.size() < 3:
		push_error("the %s's three masses were not all found in %s — "
			% [prefix, PLAZA_SCENE_PATH] + "its outer face would be left bare")
		return

	var north: Dictionary = mass[names[0]]
	var south: Dictionary = mass[names[1]]
	var out: float = -inward
	var outer: float = north["at"].x + out * north["size"].x * 0.5
	var face: float = north["at"].x + inward * north["size"].x * 0.5
	var from_z: float = north["at"].z - north["size"].z * 0.5
	var to_z: float = south["at"].z + south["size"].z * 0.5
	var top: float = north["at"].y + north["size"].y * 0.5
	var open_n: float = north["at"].z + north["size"].z * 0.5
	var open_s: float = south["at"].z - south["size"].z * 0.5

	# Plinth, brick base and course, each in two runs broken at the opening,
	# lapping 2cm past the pier at both ends for the reason `_gate_house` gives:
	# a run that stops exactly on the pier's own z extent is a coplanar pair by
	# construction, and the west only got away with it on the luck of the draw.
	for i in 2:
		var a: float = (from_z - 0.02) if i == 0 else (open_s - 0.02)
		var b: float = (open_n + 0.02) if i == 0 else (to_z + 0.02)
		# **Lifted by a jog of its own**, which is `_facade`'s trick for the same
		# problem: this run and the perimeter run beside it lap past each other
		# inside the pier, and both put their plinth top at exactly `REAR_PLINTH`
		# and their base top at exactly `FRONT_GROUND`. Four pairs, and none of
		# them anything a seam ring can help with — a gate and a wall are sixty
		# nodes apart in build order. `_rear` jogs by multiples of 31mm, so this
		# is 43: never equal to one, and never within the ring's swing of one.
		_box("%s_rear_plinth_%d" % [prefix, i], Vector3.ZERO,
			Vector3(outer + out * 0.09,
				(REAR_PLINTH - REAR_BURY) * 0.5 + GATE_REAR_JOG, (a + b) * 0.5),
			Vector3(0.24, REAR_PLINTH + REAR_BURY, b - a), "far_shade", 0.0, false)
		_box("%s_rear_base_%d" % [prefix, i], Vector3.ZERO,
			Vector3(outer + out * 0.06,
				(FRONT_GROUND + REAR_PLINTH - 0.3) * 0.5 + GATE_REAR_JOG,
				(a + b) * 0.5),
			Vector3(0.18, FRONT_GROUND - REAR_PLINTH + 0.3, b - a),
			"brick", 0.0, false)
		_box("%s_rear_course_%d" % [prefix, i], Vector3.ZERO,
			Vector3(outer + out * 0.10, FRONT_GROUND + GATE_REAR_JOG,
				(a + b) * 0.5),
			Vector3(0.34, 0.28, b - a), "white", 0.0, false)

	# The quoin strips on the two outer corners of the opening, run the pier's
	# full height. This is what makes the slot read as cut through a building
	# rather than as the gap between two slabs, and it is the one piece of the
	# frontispiece's vocabulary that belongs on a back.
	for i in 2:
		var jz: float = (open_n - 0.33) if i == 0 else (open_s + 0.33)
		_box("%s_rear_jamb_%d" % [prefix, i], Vector3.ZERO,
			Vector3(outer + out * 0.15, top * 0.5, jz),
			Vector3(0.3, top, 0.7), "white", 0.0, false)

	for i in 2:
		# Lapped 3cm into the opening at its inner end rather than stopped on
		# the reveal, which is the plinth's rule two paragraphs up: `open_s` *is*
		# the pier's own face, so a run that ends there is a coplanar pair by
		# construction. `_gate_house`'s cornice stops dead and gets away with it
		# on the hand displacement in `plaza.tscn`; this one landed on it.
		var ca: float = (from_z - 0.26) if i == 0 else (open_s - 0.03)
		var cb: float = (open_n + 0.03) if i == 0 else (to_z + 0.26)
		# Topped 6cm under the pier's own roof rather than flush with it. Flush is
		# what `_gate_house`'s cornice does on the other face, and it is on that
		# plane too — it has simply never been caught, because the ring happened
		# to be separating it. A member that stops a hand short of a parapet is
		# what a cornice does anyway.
		_box("%s_rear_cornice_%d" % [prefix, i], Vector3.ZERO,
			Vector3(outer + out * 0.13, top - FRONT_CORNICE * 0.5 - 0.06,
				(ca + cb) * 0.5),
			Vector3(0.46, FRONT_CORNICE, cb - ca), "white", 0.0, false)

	# A lantern either side of the opening. The throat has six of its own and the
	# plaza face has thirteen bulbs and two festoon runs; this face had nothing,
	# and it is the one the player walks *up to* — from the terrace at the west
	# and out of the forecourt at the east, both of which are arrivals at a
	# doorway rather than passages through one. Set outboard of the quoin so the
	# pair frames the opening instead of standing in it.
	for i in 2:
		var lz: float = (open_n - 1.5) if i == 0 else (open_s + 1.5)
		var at := Vector3(outer + out * 0.44, 3.3, lz)
		_box("%s_rear_arm_%d" % [prefix, i], Vector3.ZERO,
			Vector3(outer + out * 0.24, 3.54, lz),
			Vector3(0.44, 0.09, 0.09), "metal", 0.0, false)
		_box("%s_rear_lamp_%d" % [prefix, i], Vector3.ZERO, at,
			Vector3(0.32, 0.46, 0.32), "lamp_glass", 0.0, false)
		_omni("%s_rear_glow_%d" % [prefix, i], at, "lamp", 1.8, 8.0, LIGHT_FIXTURE)

	_gate_throat(gate, outer, face, top, open_n, open_s)


## The two reveals of a gate passage.
##
## Thirteen and a half metres of blank wall on either side of a six metre gap, at
## arm's length, for the whole of a crossing that is meant to be the park's most
## composed piece of sequence. It gets the same three horizontals the outer face
## does so the dressing turns the corner, pilasters at the spacing of the piers'
## own depth, and lanterns — which are the first light of any kind inside either
## passage, the west having had one omni in the throat and nothing to look at.
##
## Local space is each reveal's: +X along the passage and +Z out of the wall into
## it. The south reveal is turned by pi, so its offsets mirror the north's about
## the axis, which is what a passage should do anyway.
func _gate_throat(gate: Dictionary, outer: float, face: float, top: float,
		open_n: float, open_s: float) -> void:
	var prefix: String = gate["prefix"]
	var mid_x: float = (outer + face) * 0.5
	var depth: float = absf(face - outer)
	var head: float = minf(top, float(gate["height"]))
	var piers: int = maxi(2, int(round(depth / 3.4)))

	for i in 2:
		var side := "n" if i == 0 else "s"
		var wz: float = (open_n - FRONT_SINK) if i == 0 else (open_s + FRONT_SINK)
		var theta: float = 0.0 if i == 0 else PI
		var base := Vector3(mid_x, 0.0, wz)

		_box("%s_throat_%s_plinth" % [prefix, side], base,
			Vector3(0.0, (REAR_PLINTH - REAR_BURY) * 0.5, 0.09),
			Vector3(depth - 0.3, REAR_PLINTH + REAR_BURY, 0.24),
			"far_shade", theta, false)
		_box("%s_throat_%s_base" % [prefix, side], base,
			Vector3(0.0, (FRONT_GROUND + REAR_PLINTH - 0.3) * 0.5, 0.06),
			Vector3(depth - 0.4, FRONT_GROUND - REAR_PLINTH + 0.3, 0.18),
			"brick", theta, false)
		_box("%s_throat_%s_course" % [prefix, side], base,
			Vector3(0.0, FRONT_GROUND, 0.10),
			Vector3(depth - 0.5, 0.26, 0.32), "white", theta, false)

		# Pilasters run from the plinth to the clear height rather than to the
		# pier top: above the beam's soffit the cutting is open to the sky and
		# the reveal is a cliff edge, not a room.
		for j in piers:
			var px := lerpf(-depth * 0.5 + 0.9, depth * 0.5 - 0.9,
				float(j) / float(piers - 1))
			_box("%s_throat_%s_pil_%d" % [prefix, side, j], base,
				Vector3(px, (REAR_PLINTH + head) * 0.5, 0.07),
				Vector3(0.54, head - REAR_PLINTH, 0.22), "brick", theta, false)

		# Lanterns between the pilasters. Bracket, glass, and an omni at the
		# glass's own centre — the fitting is its own source here, which is the
		# cascade's rule for a globe and the opposite of the facade wash's.
		for j in piers - 1:
			var lx := lerpf(-depth * 0.5 + 0.9, depth * 0.5 - 0.9,
				(float(j) + 0.5) / float(piers - 1))
			_box("%s_throat_%s_arm_%d" % [prefix, side, j], base,
				Vector3(lx, 3.6, 0.28), Vector3(0.09, 0.09, 0.44),
				"metal", theta, false)
			_box("%s_throat_%s_lamp_%d" % [prefix, side, j], base,
				Vector3(lx, 3.36, 0.5), Vector3(0.32, 0.46, 0.32),
				"lamp_glass", theta, false)
			_omni("%s_throat_%s_glow_%d" % [prefix, side, j],
				_place(base, Vector3(lx, 3.36, 0.5), theta),
				"lamp", 1.6, 7.0, LIGHT_FIXTURE)


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

## The east seam, and it is `_arch_seam` at the other gate. **Sited on the wall's
## own centre line and nothing else** — the cascade, the belvedere and the
## staircase are what the section carries, not what the load point is measured
## against.
##
## `eastward` is the outbound direction here, so the signs are the arch's flipped
## and the two hold poses swap roles: leaving the plaza looks east through the
## gate, coming back looks west through it.
func _east_seam(belongs: StringName, leads: StringName) -> void:
	var eastward := belongs == &"plaza"
	var hold: Dictionary = Plan.EAST_HOLD_OUT if eastward else Plan.EAST_HOLD_IN
	var walk := Vector3(1.0, 0.0, 0.0) if eastward else Vector3(-1.0, 0.0, 0.0)

	if eastward:
		_gate_area("preload_%s" % leads, Plan.EAST_PRELOAD_AT,
			Plan.EAST_PRELOAD_SIZE, 0, leads, belongs)
	else:
		_gate_area("preload_%s" % leads,
			Vector3(56.0, 1.5, Plan.ARCH_AT.y), Vector3(9.0, 3.0, 7.0),
			0, leads, belongs)

	_gate_area("cross_%s" % leads, Plan.EAST_SEAM_AT, Plan.EAST_SEAM_SIZE,
		1, leads, belongs, hold["from"], hold["look"], walk, Plan.ARCH_HOLD_SECONDS)

	# **Named for where the player has come *from*, which inverts against the
	# branch.** The plaza's copy is `arrival_from_terraces` and puts you down
	# *inside the plaza*; the terraces' copy is `arrival_from_plaza` and puts you
	# in the forecourt. Written the other way round it reads plausibly and drops
	# the player onto the section that has just been freed — `section_test` caught
	# it as an 11m fall through the world one frame after the swap.
	if eastward:
		_marker("arrival_from_%s" % leads, Plan.EAST_ARRIVE_IN,
			Plan.EAST_ARRIVE_IN_YAW)
	else:
		_marker("arrival_from_%s" % leads, Plan.EAST_ARRIVE_OUT,
			Plan.EAST_ARRIVE_OUT_YAW)


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



## The basin chain's own line, which is **not** the floor's. Constant at the
## climb's own mean grade from the head to the mouth; see `BASIN_COUNT` for why
## it runs straight through a stair that steps.
##
## Anchored at `CLIMB_HEAD_Y`, and the day that constant was born this said
## `TERRACE_TWO_Y` — which *was* the head's level right up until the climb
## doubled, and was six metres low from that hour on. The whole median hung
## 6m below its own flights behind kerbs that rode the floor line, and it was
## reported from play as "why is the center sunk down?" before any tool said a
## word: the walk test walks the flights, the coplanar test has no opinion on
## a chute that is consistently elsewhere, and every screenshot of a sunken
## garden looks like a sunken garden on purpose.
func _climb_channel_y(x: float) -> float:
	return Plan.CLIMB_HEAD_Y - (Plan.CLIMB_TO_X - x) * (Plan.CLIMB_RISE / Plan.CLIMB_RUN)


## Half the ravine's opening at a station: the floor's own half-width plus
## whatever the bank has laid back over the depth still to be retained.
func _climb_open_half(x: float) -> float:
	return Plan.CLIMB_HALF_Z + _climb_bank_d(x) * Plan.CLIMB_BANK_BATTER


## How much of the cut's depth the planted bank takes at a station, and how much
## is left for the retaining wall under it. Capped by `CLIMB_BANK_MAX_D`, which
## is what keeps the mouth from eating the belvedere's east wall.
func _climb_bank_d(x: float) -> float:
	return minf(Plan.east_ground_base(x) - Plan.climb_floor_y(x),
		Plan.CLIMB_BANK_MAX_D)


## The ravine, and the park climbing into the hill.
##
## **Nothing here subtracts.** These are sibling `CSGBox3D`s under a plain
## `Node3D`, not a combiner, so a cutting cannot be cut — the hill has to be
## *built around* the void, which is why `hill_back` is gone and this lays the
## mass either side itself. The tell that it matters: the faces taper, so there
## was never a single box that could have been notched anyway.
func _east_climb() -> void:
	var axis: float = Plan.ARCH_AT.y
	var x0: float = Plan.CLIMB_FROM_X
	var x1: float = Plan.CLIMB_TO_X
	var base := -HILL_EMBED
	var sz0: float = Plan.SHELF_FROM_Z
	var sz1: float = Plan.SHELF_TO_Z
	var segs := 10
	var half: float = Plan.CLIMB_HALF_Z

	# --- the earthwork -----------------------------------------------------
	#
	# **The sides alternate bank, bay, bank.** Along a flight the hill lays back
	# as planting over a retaining wall; at a terrace it opens into a bay cut in
	# at that terrace's own level, so each landing is a path running left and
	# right into a shelf rather than a place the stair merely pauses. That is what
	# makes this circulation for a hillside district instead of a monument with
	# steps on it.
	#
	# Iterated by reach and not by even segments, because a bay's edges are a
	# reach's edges — spacing them independently put the opening's corner
	# somewhere the stair had no feature.
	var reaches := Plan.climb_reaches()
	var si := 0
	var bay := 0
	for ri in reaches.size():
		var r: Array = reaches[ri]
		var rx0: float = r[0]
		var rx1: float = r[1]
		# A narrow landing takes the flight branch below: its sides are banked
		# hillside like the flight's own, and `climb_floor_y` is flat across it,
		# which is all the difference there is. Only a terrace deep enough for
		# a room gets cut — see `CLIMB_BAY_MIN_T`.
		if not bool(r[4]) and rx1 - rx0 >= Plan.CLIMB_BAY_MIN_T:
			# A bay. Its floor is the landing's own level carried out to the
			# hillside; its ends are the cut faces of the banks either side and
			# its back is the hill. Nothing needs a parapet — it is a bite out of
			# a slope, walled by what it was cut from on three sides.
			var by: float = r[2]
			var bd: float = Plan.CLIMB_BAY_D
			# The local ground, not `TERRACE_TWO_Y`: the hill behind an upper
			# bay stands at the ramp's height, and a back mass topped at the
			# bench constant ends two metres below its own bay's floor — the
			# probe walked out over it and fell onto the buried block. The
			# datum-fork bug, at its third site.
			#
			# **At the reach's west end, not its middle.** The ground base
			# rises ~0.35/m through the ramp, so a flat top set to the middle
			# station stood most of half a metre proud of the skin at the west
			# end of a 3.6m bay — one grey tooth per bay along the brow, in
			# the 2026-08-23 play reports. A flat top under rising ground is
			# set by the low end or it is not under the ground.
			var btop: float = Plan.east_ground_base(rx0) - 0.03
			for s in 2:
				var side := -1.0 if s == 0 else 1.0
				var tag := "n" if s == 0 else "s"
				# Started inboard of the wall's inner face rather than on it.
				var iz: float = axis + side * (half - 0.3)
				var oz: float = axis + side * (half + bd)
				# Past the notch line rather than to it, buried in the hill
				# blocks: ending exactly at `SHELF_FROM_Z` put this face on the
				# same plane as the shelf buttresses standing on that line.
				var ez: float = sz0 - 0.35 if s == 0 else sz1 + 0.35
				_box("climb_bay_%s_%d" % [tag, bay], Vector3.ZERO,
					Vector3((rx0 + rx1) * 0.5, (base - 0.2 + by - 0.14) * 0.5,
						(iz + oz) * 0.5),
					Vector3(rx1 - rx0 + 0.12, by + 0.06 - base, absf(oz - iz)),
					"building")
				# Brick, like the belvedere and the court and the plaza past it.
				# The east is one floor that happens to climb.
				#
				# **Laid `BAY_DECK_DROP` under the landing beside it, and that is the
				# whole of what stops it sharing a plane with it.** A bay's floor and
				# the landing it opens off are the same terrace level by construction —
				# `by` and the reach's `ya` are both `r[2]` — and the two overlap by
				# 0.3m in z, because the deck starts inboard of the wall's inner face
				# and `climb_land_top` reaches out to `CLIMB_HALF_Z`. Topped level that
				# is 1.8m² of brick and `accent` on one plane, in the middle of a floor
				# the player walks over.
				#
				# **It reported before the landform pass and did not after**, which is
				# the reason it is worth a paragraph: nothing about it changed except
				# which way the build-order ordinal fell. A green coplanar report can be
				# luck, and adding nodes anywhere re-rolls it.
				#
				# The route yields nothing and the side space does: a landing is on the
				# way up and a bay is somewhere you step aside into, so the landing's
				# surface stays unbroken and the brick laps under its edge. A dozen
				# millimetres is a construction tolerance rather than a step — a real
				# one here would be a riser wanting a nosing, which is a different
				# decision — and it is 240 times `coplanar_test`'s floor, where the
				# quarter-millimetre the ordinal was giving it is four.
				_box("climb_bay_deck_%s_%d" % [tag, bay], Vector3.ZERO,
					Vector3((rx0 + rx1) * 0.5, by - 0.07 - BAY_DECK_DROP,
						(iz + oz) * 0.5),
					Vector3(rx1 - rx0 + 0.12, 0.14, absf(oz - iz)), "brick")
				# The hill behind it, and the face that is the bay's back wall.
				# Footed and topped a hair inside the hill blocks' own levels,
				# because its end is buried in those blocks since 2026-08-22 and
				# a shared volume with shared top and bottom planes is two
				# coplanar pairs. The top hides under the skin either way.
				if absf(ez - oz) > 0.2:
					_box("climb_bayhill_%s_%d" % [tag, bay], Vector3.ZERO,
						Vector3((rx0 + rx1) * 0.5, (base + 0.28 + btop) * 0.5,
							(oz + ez) * 0.5),
						Vector3(rx1 - rx0, btop - base - 0.28, absf(ez - oz)),
						"building")
					# A course on the back wall, `accent`. The belvedere settled
					# this: relief on a west-facing face draws nothing and value
					# draws everything, and these faces look the same way.
					_box("climb_bay_course_%s_%d" % [tag, bay], Vector3.ZERO,
						Vector3((rx0 + rx1) * 0.5, by + (btop - by) * 0.62,
							oz - side * 0.13),
						Vector3(rx1 - rx0 + 0.12, 0.3, 0.26), "accent", 0.0, false)
					# And the brick to head height, which is `_hill_brick`'s rule
					# reaching the one retaining face that is neither on the scarp
					# nor in the notch. A bay is a room you stand in with its back
					# wall an arm's length away, so it is the last place the cut
					# should be wearing the plaza perimeter's grey.
					# Full width less a hair, not `- 0.3`: the back facing used
					# to stop 15cm short of each side facing, and the strip
					# between them was the bay's one un-dressed vertical — a
					# pale grey slit of bare mass at both back corners, in the
					# 2026-08-23 play reports. It laps into the side facings'
					# ends now; a corner overlap is the house rule, a gap is
					# the fault.
					_box("climb_bay_brick_%s_%d" % [tag, bay], Vector3.ZERO,
						Vector3((rx0 + rx1) * 0.5,
							by + (HILL_BRICK_H - 0.3) * 0.5,
							oz - side * (HILL_FACE_T * 0.5 - HILL_FACE_OUT)),
						Vector3(rx1 - rx0 - 0.02, HILL_BRICK_H + 0.3, HILL_FACE_T),
						"brick", 0.0, false)
					# Its coping, because from the flights the top of this wall is a
					# raw brick edge against green and a wall with an unfinished top
					# reads as scenery rather than masonry.
					_box("climb_bay_brickcap_%s_%d" % [tag, bay], Vector3.ZERO,
						Vector3((rx0 + rx1) * 0.5, by + HILL_BRICK_H + 0.06,
							oz - side * (HILL_FACE_T * 0.5 - HILL_FACE_OUT)),
						Vector3(rx1 - rx0 - 0.18, 0.13, HILL_FACE_T + 0.12),
						"accent", 0.0, false)
					# The side walls too, which the back-wall pass of 2026-08-21
					# missed: a bay has three cut faces and only one got dressed, so
					# standing in one you had brick behind you and the perimeter's
					# bare grey an arm's length away on both sides.
					#
					# **Stepped down toward the mouth, with a coping on every step,
					# and both of those are the difference between a retaining wall
					# and a blade.** The first version was one flat panel at head
					# height for its whole depth: the bank beside a bay falls toward
					# the mouth while the panel's top stayed level, so from the
					# flights each bay read as a row of thin brick teeth standing
					# proud of the hillside — freestanding walls on a slope rather
					# than the lining of a cut. Two steps per side, tall at the back
					# corner where the cut is deep and dropping to garden-wall height
					# at the mouth, is the return walls' own vocabulary one size
					# down, and the coping is what says the exposed top is a top.
					for e in 2:
						var ex: float = rx0 if e == 0 else rx1
						var edir: float = -1.0 if e == 0 else 1.0
						var wx: float = ex + edir * (HILL_FACE_T * 0.5 - HILL_FACE_OUT)
						for st_i in 2:
							# Step 0 is the mouth half, low; step 1 the back half,
							# full brick height. The mouth end starts 0.35 in so the
							# wall never reaches past the cut it lines.
							var za: float = iz + side * 0.35 if st_i == 0 \
								else (iz + oz) * 0.5
							var zb: float = (iz + oz) * 0.5 + side * 0.14 if st_i == 0 \
								else oz - side * 0.12
							var st_top: float = by + 1.5 if st_i == 0 \
								else by + HILL_BRICK_H
							_box("climb_bay_sidebrick_%s_%d_%d_%d" % [tag, bay, e, st_i],
								Vector3.ZERO,
								Vector3(wx, (by - 0.3 + st_top) * 0.5,
									(za + zb) * 0.5),
								Vector3(HILL_FACE_T, st_top - by + 0.3,
									absf(zb - za)),
								"brick", 0.0, false)
							_box("climb_bay_sidecap_%s_%d_%d_%d" % [tag, bay, e, st_i],
								Vector3.ZERO,
								Vector3(wx, st_top + 0.06, (za + zb) * 0.5),
								Vector3(HILL_FACE_T + 0.12, 0.13,
									absf(zb - za) - 0.1),
								"accent", 0.0, false)
			bay += 1
			continue
		# A flight — or a narrow landing, which is banked exactly the same way
		# and differs only in `climb_floor_y` being flat across it. Three
		# segments so the taper reads rather than stepping once per reach.
		for k in 3:
			var xa: float = lerpf(rx0, rx1, float(k) / 3.0)
			var xb: float = lerpf(rx0, rx1, float(k + 1) / 3.0)
			var xm := (xa + xb) * 0.5
			var fy := Plan.climb_floor_y(xm)
			var w := _climb_open_half(xm)
			# Local ground, not `TERRACE_TWO_Y`: the bench constant would
			# understate the cut everywhere the ramp has risen.
			var ltop: float = Plan.east_ground_base(xm)
			var depth := ltop - fy
			var bank_d := _climb_bank_d(xm)
			var wall_h: float = depth - bank_d
			for s in 2:
				var side := -1.0 if s == 0 else 1.0
				var tag := "n" if s == 0 else "s"
				# The fill's inner edge takes the opening at the segment's
				# *west* end, not its middle: the cut narrows as it climbs, so
				# at `xa` the ravine is wider than at `xm`, and a box set to
				# the middle stands its inner-west corner inside the cut —
				# through the descending bank, as a grey tetrahedron among the
				# blooms. Named by bisection (`_dart2_probe`), 2026-08-23:
				# `climb_hill_s_24`. The height fix above does not cover it,
				# because this poke is lateral.
				var oz: float = axis + side * (_climb_open_half(xa) + 0.05)
				# Past the notch line and buried in the hill blocks, for the
				# reason the bay branch's `ez` is: ending exactly at
				# `SHELF_FROM_Z` shares a plane with the shelf buttresses.
				var ez: float = sz0 - 0.35 if s == 0 else sz1 + 0.35
				if wall_h > 0.05:
					# **Brick, not `building`.** It is the same cut face as the scarp
					# and the notch, and it is shorter than `HILL_BRICK_H` everywhere —
					# `wall_h` tops out near 1.5m at the mouth and runs to nothing by
					# the head — so it takes the colour outright rather than a facing
					# standing proud of a wall barely thicker than the facing.
					_box("climb_wall_%s_%d" % [tag, si], Vector3.ZERO,
						Vector3(xm, (base + fy + wall_h) * 0.5,
							axis + side * (half + 0.3)),
						Vector3(xb - xa + 0.06, fy + wall_h - base, 0.6),
						"brick")
					_box("climb_wall_course_%s_%d" % [tag, si], Vector3.ZERO,
						Vector3(xm, fy + wall_h + 0.07,
							axis + side * (half + 0.3)),
						Vector3(xb - xa + 0.06, 0.14, 0.78), "accent", 0.0, false)
				# **The mass, and nothing on top of it.** This block used to
				# carry a `planting` cap, and the bank beside it was four more
				# plates stepping down to the wall — twelve to a flight, each
				# one flat on top with a vertical riser, so a slope battered at
				# 1.4 came out as a green staircase standing beside a real one.
				# `_east_earth` lays the ground now. What is left here is
				# buried: it stops a cap's thickness under the plateau and the
				# skin covers it everywhere.
				# Footed and topped a hair inside the hill blocks' own levels,
				# because its end is buried in them now and shared volumes with
				# shared top and bottom planes are coplanar pairs — the bay
				# branch's lesson, at the flight branch.
				# Topped at the segment's *west* end, not `ltop` — the bay
				# branch's lesson at the flight branch: `ltop` is the middle
				# station and the ground rises through the segment, so a flat
				# top at the middle stands ~15cm through the skin at the west
				# end of every third-of-a-reach on the ramp. A row of grey
				# teeth along both brows, from play, 2026-08-23.
				var htop: float = Plan.east_ground_base(xa) - 0.03
				if absf(ez - oz) > 0.2:
					_box("climb_hill_%s_%d" % [tag, si], Vector3.ZERO,
						Vector3(xm, (base + 0.26 + htop) * 0.5,
							(oz + ez) * 0.5),
						Vector3(xb - xa, htop - base - 0.26, absf(ez - oz)),
						"building")
				# The core under the bank. Topped a hand below the retaining
				# wall's own level, which is the lowest the skin gets over this
				# span — so it sits under the batter everywhere rather than only
				# at its foot. The skin is a single surface: with nothing solid
				# under it you see its back faces from the mouth, which is to say
				# you see through the hill.
				#
				# **It does not seal the wedge and this comment used to say it
				# did.** Topping at the skin's *lowest* point is exactly what
				# leaves the batter above it hollow, and the hollow was open at
				# both ends of every bank — see `_earth_cap`, which is what
				# closes it. A block under a slope is a floor, not a fill.
				#
				# **It clears the wall on all three shared faces, and it took a run
				# of the coplanar test to find the two that were not the obvious
				# one.** Dropping the top a hand was reasoned about in advance; the
				# core and the wall also began on the same z line and were footed at
				# the same `base`, which put 0.87m² of side face and a strip of
				# underside on one plane apiece — eight pairs over the four flights.
				# A buried shape fights exactly as hard as a visible one and is the
				# harder of the two to be told about.
				#
				# So it starts outboard of the wall rather than under it, and the
				# strip it gives up is the one the wall is standing in anyway.
				# Skipped where the bank has run out near the head, or the span goes
				# negative and the box turns itself inside out.
				# Topped at the segment's *west* end, like `climb_hill` above and
				# for the same arithmetic: the skin's foot line is the floor
				# where there is no wall, the floor climbs a third of a metre
				# across a segment, and a flat top set to the middle station
				# put every core's west corners through the batter — grey
				# tetrahedra among the blooms along the last flight, where no
				# proud retaining wall stood in front of the seam to hide it.
				var fy0 := Plan.climb_floor_y(xa)
				var wall_h0 := maxf(Plan.east_ground_base(xa) - fy0
					- _climb_bank_d(xa), 0.0)
				var core_z: float = half + 0.5
				if w > core_z + 0.1:
					_box("climb_bankcore_%s_%d" % [tag, si], Vector3.ZERO,
						Vector3(xm, (base + 0.4 + fy0 + wall_h0 - 0.02) * 0.5,
							axis + side * (core_z + w) * 0.5),
						Vector3(xb - xa + 0.11, fy0 + wall_h0 - 0.42 - base,
							absf(w - core_z)), "building", 0.0, false)
				# The planting on the bank, sat on the skin rather than on a
				# plate's flat top. `_east_bank_y` is the one description of
				# where that surface is and `_east_earth` builds off the same
				# two endpoints, so a bloom cannot drift off the slope it is
				# supposed to be growing out of.
				for c in 4:
					var jit: float = (_hash01(si * 41 + c, 17, 71) - 0.5) * 0.22
					var t0: float = clampf(float(c) / 4.0 + (0.0 if c == 0 else jit), 0.0, 1.0)
					var t1: float = clampf(float(c + 1) / 4.0 + (0.0 if c == 3 else jit), 0.0, 1.0)
					var iz: float = axis + side * lerpf(half, w, t0)
					var jz: float = axis + side * lerpf(half, w, t1)
					# **Clumps of three rather than singles, and smaller with it.**
					# At 9-19cm a bloom is about the size of a real flower head, and
					# the size was never the problem: scattered one at a time over a
					# bare green plane, an opaque sphere with no foliage under it
					# reads as an egg lying on a lawn. The identical spheres in the
					# planters at the foot of the monument read as flowers, because
					# there are half a dozen of them in a box together. The grouping
					# is what does the work, not the diameter.
					#
					# So each placement becomes a clump and the radius comes down to
					# pay for the count. A third of a metre of spread is one plant
					# rather than three standing near each other.
					for b in 2:
						var hx: float = lerpf(xa + 0.3, xb - 0.3, _hash01(si * 31 + c * 7 + b, 5, 41))
						var hz: float = lerpf(minf(iz, jz) + 0.25, maxf(iz, jz) - 0.25,
							_hash01(si * 31 + c * 7 + b, 13, 61))
						var bloom: String = ["bloom_pale", "bloom_warm", "bloom_pink"][(si + c + b) % 3]
						for q in 3:
							var qx: float = hx + (_hash01(si * 7 + c * 3 + b * 11 + q, 19, 53) - 0.5) * 0.34
							var qz: float = hz + (_hash01(si * 7 + c * 3 + b * 11 + q, 23, 59) - 0.5) * 0.34
							_sphere("climb_bloom_%s_%d_%d_%d_%d" % [tag, si, c, b, q],
								Vector3(qx, _east_bank_y(qx, qz) + 0.03, qz),
								Vector3.ZERO,
								0.055 + _hash01(q * 5 + b, 3, 29) * 0.055, bloom)
			si += 1

	# --- the two flights ---------------------------------------------------
	#
	# One strip either side of the garden, running the whole 24m: ramped where
	# the reach is a flight and level where it is a terrace. The mass under a
	# flight is **one box per riser**, not one box tilted to the slope — the rule
	# the west's wings cost three rebuilds to learn, and it applies here at a
	# tenth of the size for the same reason.
	var fz: float = Plan.climb_flight_z()
	for ri in reaches.size():
		var r: Array = reaches[ri]
		var ra: float = r[0]
		var rb: float = r[1]
		var ya: float = r[2]
		var yb: float = r[3]
		for s in 2:
			var side := -1.0 if s == 0 else 1.0
			var tag := "n" if s == 0 else "s"
			var zc: float = axis + side * fz
			# **North is a ramp and south a garden stair**, which is the wings of
			# the monument below carried up the hill. The whole climb is then one
			# pair of routes rather than two features that happen to meet: the
			# smooth way and the stepped way, unbroken from the forecourt to
			# terrace two. `_cascade_wing` records what happens if this is
			# forgotten — treads built unconditionally made every leg a stair and
			# the two wings stopped differing at all.
			#
			# The landings stay on both, because a landing is where the route
			# rests rather than part of how it climbs.
			var smooth := s == 0
			if bool(r[4]):
				# **The ramp's top face *is* the nosing line**, and everything
				# else hangs off it — the construction `_wing_treads` proves and
				# the one this got wrong first time by topping each mass step at
				# its own lower edge and then putting the upper edge's height at
				# the lower edge's station. That builds a stair whose treads
				# stand a full riser through the surface you walk on.
				#
				# So: treads a hair under the line and wider than the ramp, so
				# they show past it; nosings a hair over it and narrower, so the
				# strip reads without becoming a kerb across the walk.
				var fa := Vector3(ra, ya, zc)
				var fb := Vector3(rb, yb, zc)
				for j in Plan.CLIMB_FLIGHT_RISERS:
					var tm: Vector3 = fa.lerp(fb,
						(float(j) + 0.5) / float(Plan.CLIMB_FLIGHT_RISERS))
					# **The segment's lower end, not its upper one**, and that is
					# the whole difference between this and `_wing_treads`. A
					# tread topped at its upper end stands `riser - 1cm` proud of
					# the ramp across its whole going; the wing survives that at
					# `WING_RISE`, and at `FLIGHT_RISE` it is a 24cm wall that
					# blocked all four ascending flights on both strips. Topped at
					# the lower end the tread is at the ramp where they meet and
					# under it everywhere else, so it shows past the ramp's sides
					# and never in its path.
					var tn: Vector3 = fa.lerp(fb,
						float(j) / float(Plan.CLIMB_FLIGHT_RISERS))
					# The mass, stopping under the tread. Padded past its span so
					# neighbours overlap rather than share an end face; safe to
					# pad here precisely because its top is half a metre below
					# the walking surface and cannot stand proud of it.
					# **Footed above `base`, not on it.** The hill's own blocks are
					# bottomed at `-HILL_EMBED` and so was this, so every flight step
					# shared its underside with `hill_back` and with every other mass
					# in the east — hundreds of nodes apart, which is exactly the
					# distance the build-order ordinal cannot reach across. It went
					# unreported for as long as the ordinal happened to separate them.
					# 0.22 rather than a rounder number because `climb_land` already
					# owns `base - 0.35` and `climb_bankcore` owns `base + 0.4`.
					_box("climb_step_%s_%d_%d" % [tag, ri, j], Vector3.ZERO,
						Vector3(tm.x, (base + 0.22 + tn.y - 0.5) * 0.5, zc),
						Vector3(Plan.FLIGHT_GOING + 0.08, tn.y - 0.72 - base,
							Plan.CLIMB_FLIGHT_W - (0.14 if smooth else 0.0)),
						"building")
					if smooth:
						continue
					_box("climb_tread_%s_%d_%d" % [tag, ri, j], Vector3.ZERO,
						Vector3(tm.x, tn.y - 0.26, zc),
						Vector3(Plan.FLIGHT_GOING, 0.5,
							Plan.CLIMB_FLIGHT_W + 0.5), "accent")
					_box("climb_nose_%s_%d_%d" % [tag, ri, j], Vector3.ZERO,
						Vector3(tn.x, tn.y + 0.015, zc),
						Vector3(0.16, 0.03, Plan.CLIMB_FLIGHT_W - 0.2),
						"far_shade", 0.0, false)
				_flight_ramp("climb_ramp_%s_%d" % [tag, ri], fa, fb, PI * 0.5,
					Plan.CLIMB_FLIGHT_W, "accent")
			else:
				# Wider and deeper than the flight mass it butts, on purpose.
				# At matching width off a matching base the landing and the next
				# flight's first step shared both side faces *and* their
				# undersides — three coplanar pairs per junction, and only on the
				# south strip, because the seam ordinal happened to save the
				# north one. Overlapping is the rule here; lining up is the fault.
				# **The mass stops `LAND_MASS_DROP` under its own paving, and the
				# paving laps past it.** Both of these topped out at `ya`, and the
				# only thing keeping them apart was the build-order ordinal — a
				# quarter of a millimetre, five times out of six. The sixth is
				# what gave it away: `_add`'s displacement wraps at `SEAM_STEPS`,
				# so once every 21 nodes the separation it lends changes *sign*,
				# and on `climb_land_n_5` the grey mass came out five millimetres
				# **above** the accent plate. The plate is narrower, so it was not
				# merely fighting — it was buried, and that landing rendered as
				# `building` while its five siblings rendered as `accent`.
				#
				# `walk_test` had been reporting it for as long as it existed and
				# nobody had read it that way: "bay 2 n out" lands on
				# `climb_land_n_5` where its opposite number lands on
				# `climb_land_top_s_5`. A leg naming the mass instead of the
				# paving is the tell.
				#
				# **The paving laps rather than the mass narrowing**, because the
				# mass's width is doing a job already: it is deliberately wider
				# than the flight mass it butts, and at a matching width the
				# landing and the next flight's first step shared both side faces
				# and their undersides. Narrowing it to fit under the plate would
				# have walked it back towards `climb_step`'s own dimensions to fix
				# a problem at the other end of the box. Lapping the plate leaves
				# every one of those clearances alone and leaves no mass top
				# exposed, so there is no border and no lip — the accent is the
				# whole walking surface.
				#
				# The lap is only needed in z. In x the mass overhangs by 4cm at
				# each end and both ends are buried under the neighbouring flight's
				# ramp, which arrives at `ya` exactly where the landing stops.
				_box("climb_land_%s_%d" % [tag, ri], Vector3.ZERO,
					Vector3((ra + rb) * 0.5,
						(base - 0.35 + ya - LAND_MASS_DROP) * 0.5, zc),
					Vector3(rb - ra + 0.08, ya - base + 0.35 - LAND_MASS_DROP,
						Plan.CLIMB_FLIGHT_W + 0.12), "building")
				_box("climb_land_top_%s_%d" % [tag, ri], Vector3.ZERO,
					Vector3((ra + rb) * 0.5, ya - 0.05, zc),
					Vector3(rb - ra, 0.1,
						Plan.CLIMB_FLIGHT_W + LAND_TOP_LAP), "accent")

	# --- the garden between them -------------------------------------------
	#
	# **The beds step with the stair since the climb doubled, and the chute's
	# reveal is what absorbs the difference now.** They used to ride the
	# channel's straight line — deliberate, and the mechanism that made the
	# middle read as a garden at the old scale — but the floor climbs 2m up a
	# 3.2m flight where the channel climbs 1.5, so at the head of every flight
	# the planting sat most of a metre down behind its own kerb, and over twelve
	# near-continuous metres of rise the centre read as a sunken median trench
	# between two raised stairs. The reference plate reads the other way round:
	# the borders hug the stairs, and it is the *bowls* that sit deeper or
	# shallower in the planting as the constant chute crosses the stepping
	# ground. So the beds hold a hand below the adjacent flight's own line, the
	# chain keeps its constant grade, and the basins stand 0.1 to 0.7 proud of
	# the beds depending on where the two lines are in their cycle — which is
	# the plate's own look, relocated to the one element built to carry it.
	#
	# One slab per reach rather than one per side: the bed's line is the
	# floor's now, and the floor bends at every reach boundary.
	for s in 2:
		var side := -1.0 if s == 0 else 1.0
		var tag := "n" if s == 0 else "s"
		var iz: float = axis + side * (Plan.CLIMB_CHANNEL_HALF + 0.1)
		# **Stopped `BED_KERB_TUCK` short of `CLIMB_BED_TO`, so the kerb is the
		# outermost thing and the planting dies inside it.** Run to the same line
		# the kerb's outer face is on, the bed shares a plane with it — which was
		# always true and was reported by nothing, because the two used to be built
		# one after the other and the seam ordinal lends consecutive nodes a quarter
		# of a millimetre. Splitting this block into a slab pass, a mass pass and a
		# kerb pass moved them hundreds of nodes apart and the cover came off: 14
		# pairs, brick-on-planting, down both sides of the garden.
		var oz: float = axis + side * (Plan.CLIMB_BED_TO - BED_KERB_TUCK)
		var bri := 0
		for r in reaches:
			_flight_ramp("climb_bedramp_%s_%d" % [tag, bri],
				Vector3(float(r[0]), float(r[2]) - 0.15, (iz + oz) * 0.5),
				Vector3(float(r[1]), float(r[3]) - 0.15, (iz + oz) * 0.5),
				PI * 0.5, absf(oz - iz), "planting")
			bri += 1

	# The mass under it, still one box a basin because nothing about it is seen —
	# it is what stops you looking under the garden, and the slab is the surface.
	# Topped `BED_MASS_DROP` below the channel so it clears the slab's underside
	# at the *high* end of its own span, where a flat top comes closest to a
	# falling one: half a basin's fall plus the slab's thickness is what that
	# number is.
	#
	# **The footings alternate**, and that is not decoration. Twenty-four boxes in
	# a row all bottomed at one depth, each overlapping its neighbour by the 6cm
	# of padding that keeps them from butting, is twenty-three shared underside
	# planes — reported by nothing today only because consecutive nodes are a
	# quarter-millimetre apart in the seam ordinal, which is the arrangement that
	# put a landing's grey mass five millimetres over its own paving.
	for i in Plan.BASIN_COUNT:
		var ba: float = x0 + Plan.BASIN_STEP * float(i)
		var bb: float = ba + Plan.BASIN_STEP
		var bm := (ba + bb) * 0.5
		var cy := _climb_channel_y(bm)
		var foot: float = base - 0.2 - (0.12 if i % 2 == 1 else 0.0)
		for s in 2:
			var side := -1.0 if s == 0 else 1.0
			var tag := "n" if s == 0 else "s"
			var iz: float = axis + side * (Plan.CLIMB_CHANNEL_HALF + 0.1)
			var oz: float = axis + side * (Plan.CLIMB_BED_TO - BED_KERB_TUCK)
			# Below the floor line now that the slabs ride it — at the span's low
			# end, which is where a flat top comes closest to a climbing one.
			var mtop := Plan.climb_floor_y(ba) - 0.45
			_box("climb_bed_%s_%d" % [tag, i], Vector3.ZERO,
				Vector3(bm, (foot + mtop) * 0.5, (iz + oz) * 0.5),
				Vector3(bb - ba + 0.06, mtop - foot, absf(oz - iz)), "planting")
			# The planting on it, clumped and small for the reason the banks' are —
			# a single opaque sphere on a bare green plane is an egg on a lawn, and
			# these were the last ones left scattered. Sat on the slab rather than
			# on the channel line, which is where they used to be: 12cm over the
			# bed's own top, so every one of them was floating.
			for b in 2:
				var hx: float = lerpf(ba + 0.3, bb - 0.3, _hash01(i * 17 + b, 7, 43))
				var hz: float = lerpf(minf(iz, oz) + 0.3, maxf(iz, oz) - 0.3,
					_hash01(i * 17 + b, 19, 67))
				var bloom: String = ["bloom_pale", "bloom_warm", "bloom_pink"][(i + b) % 3]
				for q in 3:
					var qx: float = hx + (_hash01(i * 5 + b * 13 + q, 29, 47) - 0.5) * 0.34
					var qz: float = hz + (_hash01(i * 5 + b * 13 + q, 31, 59) - 0.5) * 0.34
					_sphere("climb_bedbloom_%s_%d_%d_%d" % [tag, i, b, q],
						Vector3(qx, Plan.climb_floor_y(qx) - 0.12, qz),
						Vector3.ZERO,
						0.055 + _hash01(q * 7 + b, 5, 31) * 0.055, bloom)

	# **The kerb steps with the stair, and it is sampled at the stair's own
	# pitch.** It guards the flight's edge against a bed that can sit most of a
	# metre lower — the floor runs 1.5m up a 2.4m flight where the channel runs
	# 0.6, so at the head of every flight the planting is 0.9m down — which is
	# why its top is a max of the two rather than either. That max changes at
	# every riser and it was being sampled every `BASIN_STEP`, five risers apart,
	# so the guard was a twelve-step staircase agreeing with neither the stair it
	# edges nor the bed it retains. At `FLIGHT_GOING` it lands on the risers
	# exactly and crosses each terrace in six.
	#
	# Taken at the segment's *upper* end rather than its middle: both terms rise
	# with x, so that is the max over the span, and a guard sampled at its middle
	# is half a riser short for half its length.
	var kn := int(round((x1 - x0) / Plan.FLIGHT_GOING))
	for i in kn:
		var ka: float = x0 + Plan.FLIGHT_GOING * float(i)
		var kb: float = ka + Plan.FLIGHT_GOING
		var kc := _climb_channel_y(kb) - 0.12
		# A low garden edge rather than a retaining guard: the bed holds a hand
		# below the floor now, so the kerb has nothing deep to hold back and a
		# tall one is what made the old sunken beds read as a moat.
		var ktop: float = Plan.climb_floor_y(kb) + 0.14
		for s in 2:
			var side := -1.0 if s == 0 else 1.0
			var tag := "n" if s == 0 else "s"
			var oz: float = axis + side * Plan.CLIMB_BED_TO
			# Padded 4cm and not 6, which is the bed mass's figure. The first and
			# last of each run start and finish on the same station, so a shared
			# padding puts their end faces on one plane — the same four pairs, at
			# the ends instead of down the sides.
			_box("climb_bedkerb_%s_%d" % [tag, i], Vector3.ZERO,
				Vector3((ka + kb) * 0.5, (kc - 1.4 + ktop) * 0.5, oz - side * 0.11),
				Vector3(kb - ka + 0.04, ktop - kc + 1.4, 0.22), "accent")

	# --- the chain ----------------------------------------------------------
	#
	# Twelve bowls, each spilling half a metre into the one below. Terracotta and
	# not the facade's blue, because it is the niche fountain's own stone — this
	# is the same water feature and the niche is the bottom of it.
	for i in Plan.BASIN_COUNT:
		var bx: float = x0 + Plan.BASIN_STEP * (float(i) + 0.5)
		var by := _climb_channel_y(bx)
		var o := Vector3(bx, 0.0, axis)
		# The bed the bowl stands on, carried down to the mass so no bowl floats.
		_box("basin_%d_plinth" % i, o,
			Vector3(0.0, (base - 0.15 + by - 0.42) * 0.5, 0.0),
			Vector3(Plan.BASIN_STEP + 0.06, by - 0.27 - base,
				Plan.BASIN_R * 2.0 + 0.5), "niche_stone")
		_cyl("basin_%d_bowl" % i, o, Vector3(0.0, by - 0.2, 0.0),
			Plan.BASIN_R, 0.44, "niche_stone", 0.0, 16)
		_water_cyl("basin_%d_water" % i, o, Vector3(0.0, by, 0.0),
			Plan.BASIN_R - 0.07, 0.12, "basin_pool_%d" % i)
		# The spill arriving off the lip above — **a sloped sheet, not a
		# standing tube.** The bowls are 1.5m across on a 2.5m spacing, so a
		# metre of dry plinth stands between each pair, and the old fall
		# cylinder was drawn on *this* bowl's upstream lip — 1.1m downstream
		# of the lip the water actually leaves, connected to nothing at
		# either end. From play it read as a row of striped tubes hovering
		# over the garden, which is exactly what it was. The reference plate
		# settles the shape: between basins the Cleveland Cascade runs sloped
		# chutes, so the water leaves the upper lip and slides as one ribbon
		# into this bowl over its own rim. The material's fade band already
		# spans exactly this drop. Downhill is -x, so the ribbon climbs +x
		# from just inside this bowl's water to the upstream bowl's lip.
		# **Two segments, because the plinth has a shelf in it.** The upper
		# bowl stands on its own plinth, whose top runs half a metre past the
		# lip before stepping down — so one straight ribbon from lip to bowl
		# lies tangent along that shelf corner, and its translucent bands
		# zebra against the terracotta a millimetre beneath. The water's real
		# path is a short fall off the lip *onto* the shelf, then a chute off
		# the shelf corner over the lower rim — which is also the plate's own
		# stacked-lips reading, one lip more per basin.
		if i < Plan.BASIN_COUNT - 1:
			_water_ramp("basin_%d_spill_a" % i,
				o + Vector3(1.42, by + 0.63, 0.0),
				o + Vector3(Plan.BASIN_STEP - Plan.BASIN_R + 0.03,
					by + Plan.BASIN_FALL + 0.04, 0.0),
				0.44, "basin_fall_%d" % i)
			_water_ramp("basin_%d_spill_b" % i,
				o + Vector3(0.58, by + 0.06, 0.0),
				o + Vector3(1.46, by + 0.64, 0.0),
				0.44, "basin_fall_%d" % i)
	# The discharge into the collecting pool, off the lowest bowl.
	var b0x: float = x0 + Plan.BASIN_STEP * 0.5
	var b0y := _climb_channel_y(b0x)
	_water_box("basin_spill", Vector3(b0x - Plan.BASIN_R - 0.35, 0.0, axis),
		Vector3(0.0, (b0y + Plan.POOL_TOP_Y) * 0.5, 0.0),
		Vector3(0.7, b0y - Plan.POOL_TOP_Y, 0.9), "basin_fall_head")

	# --- the collecting pool ------------------------------------------------
	#
	# On the belvedere, at the mouth of the ravine, and the reason the shelf was
	# never going to stay a bare deck. It is what the chain is aimed at and what
	# the whole climb is read across from the parapet.
	var pz: float = Plan.POOL_HALF_Z
	var px0: float = Plan.POOL_FROM_X
	var px1: float = Plan.CLIMB_FROM_X
	var prim: float = Plan.HILL_TOP + 0.18
	# **Three sides, not four.** The east is where the chain arrives, and a coping
	# across it is a dam at the one place the water is supposed to come in. It
	# also shared its west face with the first tread of the south flight, which is
	# how it got noticed — the pair was the symptom and the dam was the fault.
	for s in 3:
		var hx := s < 2
		# **The west bar overhangs the water rather than stopping level with it.**
		# At `px0 - 0.3` its east face landed on `POOL_FROM_X` — which is where
		# `shelf_deck_w` also ends, so 3.6m² of coping and deck shared one plane.
		# The ordinal had been saving it and a run that added six boxes upstream
		# stopped saving it, which is the case `_begin_scene` warns about: fix the
		# shape, never the order. The shape was wrong anyway — a coping that stops
		# dead on the water line is a kerb, and this one now laps it by a hand,
		# which is what a coping is for.
		var cx: float = (px0 + px1) * 0.5 if hx else (px0 - 0.2 if s == 2 else px1 + 0.3)
		var cz: float = (axis - pz - 0.3 if s == 0 else axis + pz + 0.3) if hx else axis
		var sx: float = px1 - px0 + 1.2 if hx else 0.6
		var sz: float = 0.6 if hx else pz * 2.0 + 1.2
		_box("pool_coping_%d" % s, Vector3.ZERO,
			Vector3(cx, prim - 0.28, cz), Vector3(sx, 0.56, sz), "niche_stone")
	# Carried past the scarp line rather than stopped on it: `shelf_fill` ends at
	# `SHELF_TO_X` too, and two slabs ending on one plane is the seam a capsule
	# catches and a z-fight both.
	_box("pool_floor", Vector3.ZERO,
		Vector3((px0 + px1 + 0.35) * 0.5, Plan.HILL_TOP - 0.62, axis),
		Vector3(px1 - px0 + 0.35, 0.5, pz * 2.0), "niche_stone")
	_water_box("pool_water", Vector3.ZERO,
		Vector3((px0 + px1) * 0.5, Plan.POOL_TOP_Y, axis),
		Vector3(px1 - px0, 0.16, pz * 2.0), "basin_pool_head")

	# --- the chain after dark ----------------------------------------------
	#
	# **The historic photograph is a night photograph**, and lighting the chain is
	# not a finishing pass on it — it is half of what the feature is. Each bowl
	# gets a lens at its own bed and a short omni just above the water.
	#
	# Two fittings and not one, for the reason the niche fountain records: the
	# shader brightens *itself* over `lamp_a`, which needs the surface to have
	# something to be pale in after dark, and a lens with no light is a sticker
	# while a light with no lens is a glow from nowhere. `_uplight` carries
	# `shadow := false`, so what contains one of these is its range, never the
	# masonry it looks like it sits inside.
	for i in Plan.BASIN_COUNT:
		var lx: float = x0 + Plan.BASIN_STEP * (float(i) + 0.5)
		var ly := _climb_channel_y(lx)
		_sphere("basin_%d_lens" % i, Vector3(lx, ly - 0.14, axis), Vector3.ZERO,
			0.10, "lamp_glass")
		# **Cyan, not amber, and the frame said so before any argument did.** The
		# shader was already putting turquoise in the water and these were washing
		# the terracotta bowls warm from above, so the chain read as a line of
		# orange lamps with blue-green puddles lost inside it. The fitting has to
		# agree with the water or the brighter of the two wins — here that was a
		# 2.4m omni beating a 1.4m disc.
		#
		# This is the niche's rule inverted rather than broken: down there a warm
		# pocket in a cold monument is the point, and cool light up through water
		# is a swimming pool. Up here the water *is* the subject and there is no
		# masonry pocket to keep warm.
		_omni("basin_%d_lamp" % i, Vector3(lx, ly + 0.10, axis), "cyan",
			2.1, 2.6)
	# The pool at the foot takes two, matching the pair its own shader carries.
	for k in 2:
		var lz: float = axis + (-1.9 if k == 0 else 1.9)
		var lx: float = (Plan.POOL_FROM_X + Plan.CLIMB_FROM_X) * 0.5 - 1.6
		_sphere("pool_lens_%d" % k, Vector3(lx, Plan.POOL_TOP_Y - 0.16, lz),
			Vector3.ZERO, 0.12, "lamp_glass")
		_omni("pool_lamp_%d" % k, Vector3(lx, Plan.POOL_TOP_Y + 0.12, lz),
			"cyan", 2.4, 4.0)


## Rails on the climb, and **the monument's own rail rather than one like it**.
##
## `_wing_rail` is the whole construction — post spacing by `ceili` so the bays
## do not grow with the run, a 9cm top rail rather than a slab, and the
## `POST_MERGE` that stops two rails meeting at a corner from putting two lamps
## 30cm apart. One call per reach on each edge, so the guard steps and ramps with
## the floor it guards instead of cutting the corner of every landing.
##
## **Globes on the outer run only.** Both edges get a rail because a public stair
## has handrails on both sides and the reference plainly does; but a globe on
## every post of every edge is sixty omnis on one hillside, and the outer line is
## the one that draws the shape of the climb from the belvedere and from the
## court below it.
func _climb_rails() -> void:
	var axis: float = Plan.ARCH_AT.y
	var fz: float = Plan.climb_flight_z()
	var hw: float = Plan.CLIMB_FLIGHT_W * 0.5 - 0.12
	# Where the monument's own rails stop, so the globe pass below can tell the
	# climb's posts from the wings' without knowing anything about either.
	var first := _cascade_rails.size()
	for s in 2:
		var side := -1.0 if s == 0 else 1.0
		var tag := "n" if s == 0 else "s"
		for e in 2:
			var outer := e == 1
			var ez: float = axis + side * (fz + (hw if outer else -hw))
			var en := "o" if outer else "i"
			var reaches := Plan.climb_reaches()
			for ri in reaches.size():
				var r: Array = reaches[ri]
				# **No outer rail across a terrace**, because that is where the
				# landing turns into the bay and the thing being guarded is a
				# doorway. It ran continuously at first and the walk test was
				# blunt about it: all six ways into the shelves stopped on
				# `climb_rail_*_o_*_rail`. A guard belongs beside a drop, and
				# along a terrace the outer side is floor.
				if outer and not bool(r[4]):
					continue
				_wing_rail("climb_rail_%s_%s_%d" % [tag, en, ri],
					Vector2(float(r[0]), ez), float(r[2]),
					Vector2(float(r[1]), ez), float(r[3]), outer)
	for i in range(first, _cascade_rails.size()):
		var at: Vector3 = _cascade_rails[i] + Vector3(0.0, 0.16, 0.0)
		_sphere("climb_globe_%d" % i, at, Vector3.ZERO, 0.13, "lamp_glass")
		_omni("climb_globe_%d_pool" % i, at, "lamp", 1.5, 7.0, LIGHT_FIXTURE)


## The plaza seen from the terraces, and **the answer to standing on the
## belvedere and finding the park gone.**
##
## `ParkSections` frees everything the outgoing section owned, so crossing the
## east gate deletes the plaza, its walls, its tower and its skyline all at once —
## and the terraces look straight back down their own axis at all four. It is
## `_plaza_from_below`'s problem at the other gate, and it takes the same answer:
## read the hand-authored plaza as text and stand a massing copy of it up in the
## section that can see it.
##
## Two differences from the west's version, both because of where the seam is.
## **The east perimeter is the *near* boundary here** — the forecourt runs to
## x 33 now, so the player stands against the outer face of a wall the plaza used
## to own. Those runs get the plaza's own material and collide, or you walk
## through the back of the gate you just came out of. Everything else is a
## silhouette at sixty metres and stays washed and passable.
##
## Snapped to the centimetre for `_plaza_from_below`'s reason, which is the one
## piece of this that is genuinely subtle: the plaza's own hand displacement runs
## opposite to the generator's ring, so a verbatim copy cancels it exactly and
## lands shapes on shared planes. Snapping throws it away and lets this scene's
## ring do the separating.
func _plaza_from_the_east() -> void:
	var n := 0
	for box in _plaza_scene_boxes():
		var nm: String = box["nm"]
		var at: Vector3 = box["at"]
		var size: Vector3 = box["size"]
		if size.y < BELOW_MIN_H:
			continue
		# The near boundary: the east wall's runs and the gate that is cut through
		# them. Named rather than found by position, because "the wall you are
		# standing against" is not a thing a bounding box says about itself.
		var near := nm.begins_with("perim_e") or nm.begins_with("east_pier") \
			or nm.begins_with("east_beam")
		# Everything else has to be worth drawing from sixty metres east: the
		# tower because it is the one thing that clears its own wall and the view
		# back down the axis at it is what the belvedere is *for*, and the far
		# perimeter because a plaza with no far side reads as a wall with sky
		# behind it.
		if not (near or nm.begins_with("tower_") or nm.begins_with("perim_")
				or nm == "ground"):
			continue
		var mat := _mass_material(box, "far")
		if near:
			mat = "building"
		# **The floor is not haze.** `far` is the west's distance wash and it is
		# right there — ninety metres of lagoon between the promenade and the
		# plaza's silhouette. From the belvedere the same floor is forty metres
		# away through a six metre gap, and washed out it read as a white sheet
		# between the crest's two piers: the park stopped at the wall and became
		# fog. It gets the plaza's own brick, which is world-space triplanar and
		# so lines up with the forecourt this section is standing on.
		if nm == "ground":
			mat = "brick"
		# The plaza's `ground` is 104m of up-facing floor at exactly y = 0, and so
		# is the forecourt this scene stands on. Two floors on one plane is five
		# hundred square metres of fight; a hand's width settles it, and at sixty
		# metres through a six metre gap it costs nothing.
		var drop: float = 0.0 if near else BELOW_FRAMED_DROP
		var thin := {"at": at, "size": size} if near else _mass_thinned(box)
		# **Six millimetres east of where `_plaza_from_below` puts its copy**, and
		# it is about the test rather than about the render. Both functions stand
		# a massing copy of the same hand-authored boxes and both snap to the same
		# centimetre grid, so identical sources land on identical planes — and
		# `coplanar_test.py` compares every scene against every other with no
		# notion of which of them are ever mounted together. `boardwalk` and
		# `terraces` are mutually exclusive sections and a player cannot see both
		# copies at once, so the pair it reports is real arithmetic about an
		# impossible frame. A permanently-red test is worse than the pair, because
		# the next real one hides behind it.
		_box("efar_%s" % nm, Vector3.ZERO,
			Vector3(thin["at"]).snapped(Vector3.ONE * 0.01)
				+ Vector3(EAST_FAR_NUDGE, -drop, 0.0), thin["size"],
			mat, 0.0, near)
		n += 1
	if n < 6:
		push_error("only %d plaza masses read for the view from the east — "
			% n + "the parse found nothing, or the perimeter has been renamed")
