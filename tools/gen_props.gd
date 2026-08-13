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
const SKYLINE_PATH := "res://scenes/world/plaza_skyline.tscn"
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
	_build_materials()

	_root = Node3D.new()
	_root.name = "props"
	_begin_scene()
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
	_west_stair()
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


func _build_materials() -> void:
	var defs := {
		"wood": [Color(0.55, 0.42, 0.3), 0.9, 0.0],
		"metal": [Color(0.3, 0.31, 0.33), 0.55, 0.2],
		"white": [Color(0.87, 0.86, 0.82), 0.8, 0.0],
		"red": [Color(0.84, 0.27, 0.24), 0.7, 0.0],
		"yellow": [Color(0.93, 0.76, 0.24), 0.7, 0.0],
		"blue": [Color(0.27, 0.5, 0.72), 0.7, 0.0],
		"accent": [Color(0.78, 0.54, 0.42), 0.85, 0.0],
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
		# Deck boards. Greyer and cooler than `wood`, which is furniture — planking
		# that has had weather on it is not the same colour as a bench slat, and
		# the promenade is 17m wide, so getting it wrong is 2,700m² of wrong.
		"plank": [Color(0.62, 0.56, 0.48), 0.95, 0.0],
		# Awnings and the stripes on things. Saturated on purpose: the boardwalk is
		# the one section allowed to be loud, and it is what the late sun hits.
		"canvas": [Color(0.86, 0.4, 0.33), 0.85, 0.0],
		"canvas_alt": [Color(0.35, 0.55, 0.66), 0.85, 0.0],
	}
	for key in defs:
		var m := StandardMaterial3D.new()
		m.albedo_color = defs[key][0]
		m.roughness = defs[key][1]
		m.metallic = defs[key][2]
		mats[key] = m


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
func _place(base: Vector3, local: Vector3, theta: float) -> Vector3:
	return base + Basis(Vector3.UP, theta) * local


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
		leads: StringName, belongs := &"plaza") -> void:
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


func _sphere(nm: String, origin: Vector3, radius: float, mat: String, squash := 1.0) -> void:
	var s := CSGSphere3D.new()
	s.radius = radius
	s.radial_segments = 10
	s.rings = 6
	s.material = mats[mat]
	s.use_collision = false
	s.transform = Transform3D(Basis.IDENTITY.scaled(Vector3(1.0, squash, 1.0)), origin)
	_add(s, nm)


func _bench(nm: String, base: Vector3, theta: float) -> void:
	_box(nm + "_seat", base, Vector3(0, 0.45, 0), Vector3(1.8, 0.12, 0.55), "wood", theta)
	_box(nm + "_leg_l", base, Vector3(-0.78, 0.225, 0), Vector3(0.14, 0.45, 0.5), "metal", theta)
	_box(nm + "_leg_r", base, Vector3(0.78, 0.225, 0), Vector3(0.14, 0.45, 0.5), "metal", theta)
	_box(nm + "_back", base, Vector3(0, 0.72, -0.22), Vector3(1.8, 0.52, 0.11), "wood", theta)


## Turn so the assembly's local +Z faces `target`.
func _facing(from: Vector3, target: Vector3) -> float:
	var d := target - from
	return atan2(d.x, d.z)


func _benches() -> void:
	var r := 7.5
	var degs := [25.0, 95.0, 165.0, 235.0, 305.0]
	for i in degs.size():
		var a := deg_to_rad(degs[i])
		var p := Vector3(r * cos(a), 0.0, r * sin(a))
		_bench("bench_%d" % i, p, _facing(p, Vector3.ZERO))
	_bench("bench_hut", Vector3(4.5, 0, 11.5), deg_to_rad(8))
	_bench("bench_south", Vector3(-5, 0, 19), deg_to_rad(186))

	var band := Vector3(-12, 0, -12)
	var bdegs := [20.0, 140.0, 260.0]
	for i in bdegs.size():
		var a := deg_to_rad(bdegs[i])
		var p := band + Vector3(7.4 * cos(a), 0.0, 7.4 * sin(a))
		_bench("bench_band_%d" % i, p, _facing(p, band))
	_bench("bench_sw", Vector3(-11, 0, 20), deg_to_rad(120))
	_bench("bench_se", Vector3(2, 0, 22), deg_to_rad(200))


func _lamps() -> void:
	var spots := [
		Vector2(13, -2), Vector2(9, -11), Vector2(-2, -13), Vector2(-13, -3),
		Vector2(-11, 6), Vector2(-3, 13), Vector2(7, 14), Vector2(14, 9),
		Vector2(-19, 2), Vector2(-19, 12), Vector2(-18, -14), Vector2(-16, 20),
	]
	for i in spots.size():
		var b := Vector3(spots[i].x, 0, spots[i].y)
		_cyl("lamp_%d_pole" % i, b, Vector3(0, 2.1, 0), 0.09, 4.2, "metal", 0.0, 8)
		_box("lamp_%d_head" % i, b, Vector3(0, 4.13, 0), Vector3(0.5, 0.24, 0.5), "white")


func _bins() -> void:
	var spots := [
		Vector2(5.5, 6), Vector2(-6, 5.5), Vector2(-6.5, -6), Vector2(6, -6.5),
		Vector2(12, 12), Vector2(-14, 14), Vector2(3, -14),
		Vector2(-19, 7), Vector2(-17, 18), Vector2(-6.5, 24), Vector2(8, 20),
	]
	for i in spots.size():
		var b := Vector3(spots[i].x, 0, spots[i].y)
		_cyl("bin_%d_body" % i, b, Vector3(0, 0.42, 0), 0.32, 0.85, "metal")
		_cyl("bin_%d_lid" % i, b, Vector3(0, 0.865, 0), 0.36, 0.1, "blue")


func _cafe() -> void:
	var spots := [Vector2(14, 3), Vector2(17, 8), Vector2(13, 12)]
	var turns := [15.0, -25.0, 40.0]
	var shades := ["red", "yellow", "blue"]
	for i in spots.size():
		var b := Vector3(spots[i].x, 0, spots[i].y)
		var th := deg_to_rad(turns[i])
		_cyl("table_%d_top" % i, b, Vector3(0, 0.74, 0), 0.6, 0.08, "white", th, 16)
		_cyl("table_%d_post" % i, b, Vector3(0, 0.37, 0), 0.07, 0.74, "metal", th, 8)
		_cyl("table_%d_umb_pole" % i, b, Vector3(0, 1.15, 0), 0.05, 2.3, "metal", th, 8)
		_cyl("table_%d_umb_top" % i, b, Vector3(0, 2.3, 0), 1.5, 0.12, shades[i], th, 12)
		var offs := [Vector3(0.95, 0, 0.2), Vector3(-0.9, 0, -0.35)]
		for j in offs.size():
			var cb: Vector3 = b + offs[j]
			var cth: float = th + deg_to_rad(30.0 * (j + 1))
			_cyl("chair_%d%d_post" % [i, j], cb, Vector3(0, 0.235, 0), 0.05, 0.47, "metal", cth, 8)
			_box("chair_%d%d_seat" % [i, j], cb, Vector3(0, 0.44, 0), Vector3(0.42, 0.07, 0.42), "white", cth)
			_box("chair_%d%d_back" % [i, j], cb, Vector3(0, 0.66, -0.16), Vector3(0.42, 0.48, 0.07), "white", cth)


func _queue() -> void:
	var xs := [5.5, 7.0, 8.5, 10.0, 11.5]
	var z := 12.0
	for i in xs.size():
		_cyl("stanchion_%d" % i, Vector3(xs[i], 0, z), Vector3(0, 0.5, 0), 0.06, 1.0, "metal", 0.0, 8)
	for i in xs.size() - 1:
		var mid: float = (xs[i] + xs[i + 1]) * 0.5
		_box("rope_%d" % i, Vector3(mid, 0, z), Vector3(0, 0.8, 0), Vector3(1.5, 0.05, 0.05), "red", 0.0, false)


func _bollards() -> void:
	for i in 5:
		_cyl("bollard_n_%d" % i, Vector3(-4 + i * 3.0, 0, -20), Vector3(0, 0.45, 0), 0.13, 0.9, "metal", 0.0, 8)
	for i in 5:
		_cyl("bollard_s_%d" % i, Vector3(-6 + i * 3.0, 0, 30), Vector3(0, 0.45, 0), 0.13, 0.9, "metal", 0.0, 8)
	var pl := [Vector2(-7, 26), Vector2(4, 26)]
	for i in pl.size():
		_box("planter_s_%d" % i, Vector3(pl[i].x, 0, pl[i].y), Vector3(0, 0.45, 0), Vector3(2.6, 0.9, 2.6), "accent")


## Two panels leaning together at the top. The tilt is about each panel's own
## X axis, and the offset is rotated by the same transform, so the tops meet.
func _aframes() -> void:
	var spots := [Vector2(3, 10), Vector2(-9, -2), Vector2(12, -8)]
	var turns := [22.0, -40.0, 115.0]
	var lean := deg_to_rad(11.0)
	for i in spots.size():
		var b := Vector3(spots[i].x, 0, spots[i].y)
		var th := deg_to_rad(turns[i])
		_box("aframe_%d_a" % i, b, Vector3(0, 0.54, -0.16), Vector3(0.9, 1.1, 0.05), "wood", th, true, lean)
		_box("aframe_%d_b" % i, b, Vector3(0, 0.54, 0.16), Vector3(0.9, 1.1, 0.05), "yellow", th, true, -lean)


func _newsboxes() -> void:
	var spots := [Vector2(3.4, 7.6), Vector2(2.5, 7.4)]
	for i in spots.size():
		var b := Vector3(spots[i].x, 0, spots[i].y)
		var th := deg_to_rad(12.0 + i * 20.0)
		_box("newsbox_%d_body" % i, b, Vector3(0, 0.45, 0), Vector3(0.45, 0.9, 0.4), "red", th)
		_box("newsbox_%d_top" % i, b, Vector3(0, 0.9, 0), Vector3(0.5, 0.08, 0.45), "metal", th)


func _flagpoles() -> void:
	var xs := [15.5, 20.5]
	var shades := ["red", "yellow"]
	for i in xs.size():
		var b := Vector3(xs[i], 0, -16)
		_cyl("flagpole_%d_pole" % i, b, Vector3(0, 3.0, 0), 0.07, 6.0, "white", 0.0, 8)
		_box("flagpole_%d_banner" % i, b, Vector3(0, 4.6, 0.35), Vector3(0.08, 2.2, 0.7), shades[i], 0.0, false)


func _cart() -> void:
	var c := Vector3(-6, 0, -10)
	var th := deg_to_rad(-18.0)
	_box("cart_body", c, Vector3(0, 0.6, 0), Vector3(2.0, 1.2, 1.1), "white", th)
	_box("cart_roof", c, Vector3(0, 1.55, 0), Vector3(2.4, 0.1, 1.5), "red", th)
	_cyl("cart_wheel_l", c, Vector3(-0.8, 0.22, 0.6), 0.22, 0.1, "metal", th + PI / 2, 10)
	_cyl("cart_wheel_r", c, Vector3(0.8, 0.22, 0.6), 0.22, 0.1, "metal", th + PI / 2, 10)


func _stroller() -> void:
	var s := Vector3(-3.2, 0, 8.4)
	var th := deg_to_rad(34.0)
	_box("stroller_basket", s, Vector3(0, 0.62, 0), Vector3(0.55, 0.5, 0.8), "blue", th)
	_box("stroller_handle", s, Vector3(0, 0.86, -0.28), Vector3(0.5, 0.06, 0.06), "metal", th)
	_cyl("stroller_leg", s, Vector3(0, 0.19, 0), 0.04, 0.38, "metal", th, 6)
	_cyl("stroller_wheel", s, Vector3(0, 0.1, 0.34), 0.1, 0.06, "metal", th + PI / 2, 8)


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


func _balloons() -> void:
	# Two tied to the bench by the hut, floating on their strings.
	# Kept clear of the photo hut, which occupies x 6.5..11.5, z 6..10.
	var tied := [
		{"at": Vector2(5.6, 4.9), "y": 1.5, "mat": "red"},
		{"at": Vector2(5.95, 5.25), "y": 1.7, "mat": "yellow"},
	]
	for i in tied.size():
		var d: Dictionary = tied[i]
		var x: float = d["at"].x
		var z: float = d["at"].y
		var y: float = d["y"]
		_sphere("balloon_%d" % i, Vector3(x, y, z), 0.26, d["mat"])
		_box("balloon_%d_string" % i, Vector3(x, 0, z), Vector3(0, y * 0.5, 0),
			Vector3(0.02, y, 0.02), "white", 0.0, false)

	# One that came down, caught against a bollard at the south entrance with its
	# string trailing on the ground. Sitting loose on open concrete it read as
	# half-buried no matter where it was in Y — a ball resting on a plane and a
	# ball sunk into one have the same silhouette. Leaning it on something and
	# giving it a string is what makes it legible as a balloon.
	var r := 0.22
	var bollard := Vector3(0, 0, 30)
	var at := bollard + Vector3(0.13 + r, r, 0.06)
	_sphere("balloon_2", at, r, "blue")
	_box("balloon_2_string", Vector3(at.x, 0, at.z), Vector3(0.55, 0.012, 0.0),
		Vector3(0.9, 0.018, 0.018), "white", deg_to_rad(28.0), false)


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
func _wooden_coaster(origin: Vector3, heading: float, mat: String) -> void:
	var profile := [3.0, 9.0, 15.0, 21.0, 26.0, 27.0, 9.0, 19.0, 8.0, 15.5, 7.0, 12.0, 6.5, 9.0, 5.0]
	var step := 7.0
	var dir := Basis(Vector3.UP, heading) * Vector3.FORWARD
	var prev := Vector3.ZERO
	for i in profile.size():
		var foot: Vector3 = origin + dir * (i * step)
		var h: float = profile[i]
		_far_cyl("coaster_col_%d" % i, foot + Vector3(0, h * 0.5, 0), 0.55, h, mat, 6)
		# cross-bracing, which is most of what reads as "wooden" at distance
		if h > 8.0:
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
	_box("water", Vector3.ZERO, Vector3(-186, WATER_TOP - 4.0, 0),
		Vector3(240, 8.0, 400), "water", 0.0, false)
	# The face the plaza stands on. Everything west of the parapet drops away
	# here, which is what turns the parapet into an overlook rather than a fence.
	# Cut in two so the stair has a slot to descend through — a stair cut into a
	# seawall, which is also what puts a corner between the terrace and the
	# bottom of the flight.
	# These four are also the walls and floor of the stair well, and without them
	# a player walking sideways off a flight goes straight through the scenery
	# and out of the world.
	_box("bluff_north", Vector3.ZERO, Vector3(-42.5, -6.0 + GROUND_SEAM, -91.0),
		Vector3(7.0, 12.0, 158.0), "far_warm")
	_box("bluff_south", Vector3.ZERO, Vector3(-42.5, -6.0 + GROUND_SEAM, 89.0),
		Vector3(7.0, 12.0, 162.0), "far_warm")
	# Its west face is inset 3cm from the other bluff pieces, because the stair's
	# treads are exactly one stair-width at the turn axis and land on -46 too.
	# Two faces the same way at the same depth is the vibration in the ground, and
	# the build-order seam cannot separate these two: they are in different
	# scenes. Giving way inward is the hand-authored rule.
	_box("bluff_base", Vector3.ZERO, Vector3(-42.485, -9.0, -2.0),
		Vector3(6.97, 6.0, 20.0), "far_warm")
	# The rest of the bluff fills back in around the well, in three pieces,
	# because the upper flight runs east through it and a solid fill walls in the
	# stair it is supposed to be holding up.
	_box("bluff_slot_north", Vector3.ZERO, Vector3(-41.2, -6.0 + GROUND_SEAM, -11.5),
		Vector3(4.4, 12.0, 1.0), "far_warm")
	_box("bluff_slot_south", Vector3.ZERO, Vector3(-41.2, -6.0 + GROUND_SEAM, -0.2),
		Vector3(4.4, 12.0, 16.4), "far_warm")
	_box("bluff_slot_under", Vector3.ZERO, Vector3(-41.2, -6.75, -9.7),
		Vector3(4.4, 10.5, 2.6), "far_warm")
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
	# The north end of the strip, closed by the coaster rather than trailing off.
	# Same origin the section builds it at, or the silhouette shifts eight metres
	# when the player walks through the gate.
	_wooden_coaster(Vector3(FRONT_X, SHORE_TOP, COASTER_STATION.y - 2.0),
		0.0, "far_warm")

	# Masts along the promenade. At this distance they are the thing that says
	# somebody strung lights here, without a single light being modelled.
	var z := -46.0
	var n := 0
	while z <= 46.0:
		if z < GAP_FROM - 3.0 or z > GAP_TO + 3.0:
			_cyl("mast_%d" % n, Vector3.ZERO, Vector3(PROMENADE_X + 4.0, SHORE_TOP + 4.0, z),
				0.22, 8.0, "far_shade", 0.0, 6, false)
			n += 1
		z += 11.0


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


## The way down. Two flights with a corner between them, cut into the bluff:
## west out of a gap in the parapet, a landing, then south along the face to the
## boardwalk.
##
## The corner is the point. The arch is a straight tube you can see through,
## which makes it a weak threshold; a flight that turns puts a wall between the
## terrace and wherever it comes out, which is where a section load can hide and
## why the reveal gets walked into rather than faded into.
const STAIR_W := Plan.STAIR_W
const STAIR_RISE := Plan.STAIR_RISE
const STAIR_TOP_Z := Plan.STAIR_TOP_Z
const STAIR_TURN_X := Plan.STAIR_TURN_X


## The treads are scenery and the ramps under them are the floor.
##
## CharacterBody3D has no step-up: a quarter-metre riser is a ninety-degree wall,
## so a stair built out of boxes is walkable down and impassable coming back.
## Verified by driving the player at it rather than by looking at it, which a
## screenshot could not have told us. A ramp at the slope of the nosings is
## flush with every one of them and under forty-five degrees, so it is floor.
func _flight_ramp(nm: String, top_a: Vector3, top_b: Vector3, theta: float) -> void:
	var span := top_b - top_a
	var horizontal := Vector2(span.x, span.z).length()
	var phi := atan2(-span.y, horizontal)
	var mid := (top_a + top_b) * 0.5
	var thickness := 0.4
	# Back the slab off along its own up-axis so its top face lands on the line
	# the nosings sit on.
	var up := (Basis(Vector3.UP, theta) * Basis(Vector3.RIGHT, phi)).y
	_box(nm, mid - up * (thickness * 0.5), Vector3.ZERO,
		Vector3(STAIR_W, thickness, span.length()), "accent", theta, true, phi)


func _west_stair() -> void:
	# Flight A: west off the terrace, out of the parapet gap. Short and shallow,
	# because it has to reach the landing's near edge rather than cross it — a
	# ramp that overhangs its own landing presents the landing with a wall.
	var treads_a := 4
	var run_a := 0.85
	for i in treads_a:
		var top := -STAIR_RISE * (i + 1)
		var x := -40.0 - run_a * (i + 0.5)
		_box("flight_a_%d" % i, Vector3.ZERO, Vector3(x, top - 0.25, STAIR_TOP_Z),
			Vector3(run_a, 0.5, STAIR_W), "accent", 0.0, false)
	_flight_ramp("ramp_a", Vector3(-40.0, 0.0, STAIR_TOP_Z),
		Vector3(-40.0 - run_a * treads_a, -STAIR_RISE * treads_a, STAIR_TOP_Z),
		-PI * 0.5)

	# The landing is a plinth rather than a slab: the slot it sits in is open to
	# the boardwalk below, and a floating step reads as a mistake from down there.
	var landing_y := -STAIR_RISE * treads_a
	# Run the landing all the way back to the bluff wall. One stair-width leaves a
	# metre of gap behind it, and a metre of gap five metres up is a hole a player
	# falls into and cannot climb out of.
	# A centimetre proud of the stair width rather than equal to it. The landing
	# and the ramp that comes off it are both STAIR_W at the same x, so built
	# flush they share both side faces — the one pair the build-order seam cannot
	# separate, because these two are exactly SEAM_STEPS apart. The plinth is the
	# thing the ramp lands on, so the plinth is the one that owns the edge.
	_box("stair_landing", Vector3.ZERO,
		Vector3(STAIR_TURN_X, (landing_y - 6.0) * 0.5, STAIR_TOP_Z - 0.5),
		Vector3(STAIR_W + 0.01, landing_y + 6.0, STAIR_W + 1.0), "accent")

	# Flight B: turn south and run down the bluff face to the boardwalk.
	var treads_b := 20
	var run_b := 0.63
	var start_z := STAIR_TOP_Z + STAIR_W * 0.5
	for i in treads_b:
		var top := landing_y - STAIR_RISE * (i + 1)
		var z := start_z + run_b * (i + 0.5)
		_box("flight_b_%d" % i, Vector3.ZERO, Vector3(STAIR_TURN_X, top - 0.25, z),
			Vector3(STAIR_W, 0.5, run_b), "accent", 0.0, false)
	_flight_ramp("ramp_b", Vector3(STAIR_TURN_X, landing_y, start_z),
		Vector3(STAIR_TURN_X, landing_y - STAIR_RISE * treads_b, start_z + run_b * treads_b),
		0.0)

	# A rail down the open west side of flight B, and a return across the head of
	# flight A so the gap in the parapet reads as a stair rather than a hole.
	var horizontal := run_b * treads_b
	var vertical := STAIR_RISE * treads_b
	var slope := atan2(vertical, horizontal)
	_box("stair_rail", Vector3.ZERO,
		Vector3(STAIR_TURN_X - STAIR_W * 0.5 - 0.1, landing_y - vertical * 0.5 + 0.55,
			start_z + horizontal * 0.5),
		Vector3(0.2, 1.0, sqrt(horizontal * horizontal + vertical * vertical)),
		"metal", 0.0, true, slope)
	_box("stair_head_rail", Vector3.ZERO,
		Vector3(-40.6, 0.55, STAIR_TOP_Z - STAIR_W * 0.5 - 0.1),
		Vector3(1.4, 1.1, 0.2), "metal")

	# The foot, and the gate across it. Everything past this point is a tableau
	# with no collision on it, so the stair has to end somewhere the player can
	# stand and look and not walk through the scenery.
	#
	# This is the section boundary, and it is deliberately at the bottom of a
	# flight that turned: out of sight of the terrace, one room deep, with the
	# boardwalk at eye level through the bars. When there is a boardwalk to load,
	# the gate is what opens and this is where it loads.
	var foot_z := start_z + horizontal + STAIR_W * 0.5
	var foot_y := landing_y - vertical
	_box("stair_foot", Vector3.ZERO, Vector3(STAIR_TURN_X, foot_y - 0.25, foot_z),
		Vector3(STAIR_W, 0.5, STAIR_W), "accent")
	# The gate is on the *west* face, because that is the only face the well has.
	# It ran across the south face until 2026-08-12, which put twelve metres of
	# bluff behind a door — a mistake that could not be seen from either side
	# while the bluff belonged to the plaza and stopped existing at the crossing.
	# The back wall of the well takes the rail instead.
	_box("foot_rail_south", Vector3.ZERO,
		Vector3(STAIR_TURN_X, foot_y + 0.55, foot_z + STAIR_W * 0.5 + 0.1),
		Vector3(STAIR_W, 1.1, 0.2), "metal")
	_box("foot_gate", Vector3.ZERO,
		Vector3(Plan.FOOT_GATE_X, foot_y + 1.1, foot_z),
		Vector3(0.2, 2.2, STAIR_W), "metal")

	# The well's west face, closed except at the gate — which turns flight B from
	# a ledge into a shaft. It was open for its whole twenty metres, and a player
	# who reached the foot could walk north under their own stair and straight out
	# onto the shore, six metres below a section that was not mounted.
	#
	# Closing it also makes good on something the comment above has been claiming
	# since the seam was built: "the boardwalk at eye level through the bars" is
	# only true if the bars are the *only* way to see it.
	for run in [[-12.0, foot_z - STAIR_W * 0.5], [foot_z + STAIR_W * 0.5, 8.0]]:
		var from: float = run[0]
		var to: float = run[1]
		_box("well_wall_%.0f" % from, Vector3.ZERO,
			Vector3(Plan.FOOT_GATE_X, -3.0, (from + to) * 0.5),
			Vector3(0.3, 6.0, to - from), "far_warm")

	# The section boundary, as three nodes rather than as geometry.
	#
	# The preload sits at the head of flight A, so stepping off the terrace onto
	# the stair is what starts the load. The crossing sits just short of the shut
	# gate at the bottom. Between them is the whole stair — about twenty-two
	# metres, most of a minute at a walk — and it turns halfway down, so the
	# thing being loaded is never in shot while it loads. That corridor is the
	# budget; the fade over the swap is only there to hide the cut.
	#
	# The crossing is deliberately in front of the gate rather than past it. The
	# gate is a solid box and stays shut: the player walks up to it and the park
	# takes over, which is a threshold opening rather than a wall vanishing.
	_gate_area("preload_boardwalk", Vector3(-40.0, 0.9, STAIR_TOP_Z),
		Vector3(4.0, 3.0, 2.4), 0, &"boardwalk")
	_gate_area("cross_boardwalk",
		Vector3(Plan.FOOT_GATE_X + 0.5, foot_y + 1.4, foot_z),
		Vector3(1.0, 3.0, STAIR_W), 1, &"boardwalk")
	# East of the crossing volume, or arriving from the boardwalk lands the player
	# inside the trigger that sent them and bounces them straight back. Facing
	# north is facing back up the flight they would have come down.
	_marker("arrival_from_boardwalk", Plan.STAIR_FOOT_STAND, 0.0)


func _skyline() -> void:
	# North, straight down the spawn sightline, cropped by building_north.
	_wooden_coaster(Vector3(-22, 0, -58), deg_to_rad(72.0), "far_warm")
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
	_box("entrance_ground", Vector3.ZERO, Vector3(ST_X, -0.5 + GROUND_SEAM, 75.5),
		Vector3(41, 1, 75), "accent", 0.0, true)

	_street_frontage()
	_street_booths()
	_gate()
	_apron()


## Both sides of the street, one building deep, fronting the walk. This is the
## midway treatment the design calls for: the corridor between the gate and the
## plaza is where the small commerce lives, not a section of its own.
##
## Depths and heights vary per building so the run reads as a street of separate
## businesses. A constant depth gives two long walls, which is what the boardwalk
## frontage got wrong at close range.
func _street_frontage() -> void:
	# Kinds alternate across the street rather than down it, so neither side is a
	# run of the same thing and the arcades face something other than each other.
	var west := [
		[44.0, 10.0, 9.0, 6.5, "far_warm", "store"],
		[55.0, 11.0, 10.0, 5.0, "accent", "cafe"],
		[66.0, 10.0, 8.0, 7.0, "far_warm", "arcade"],
		[76.0, 9.0, 9.5, 5.5, "white", "store"],
		[87.0, 12.0, 8.5, 6.0, "accent", "cafe"],
	]
	var east := [
		[45.0, 11.0, 9.0, 5.5, "accent", "cafe"],
		[57.0, 12.0, 10.0, 7.0, "far_warm", "store"],
		[69.0, 11.0, 8.0, 5.0, "white", "arcade"],
		[80.0, 10.0, 9.0, 6.5, "accent", "store"],
		[90.0, 9.0, 8.5, 5.5, "far_warm", "cafe"],
	]
	_shopfronts(west, -1.0, 0)
	_shopfronts(east, 1.0, 10)


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
	_box("apron_wall_west", Vector3.ZERO, Vector3(ST_X - 20.3, 1.5, 104.0),
		Vector3(0.4, 3.0, 15.0), "far_shade")
	_box("apron_wall_east", Vector3.ZERO, Vector3(ST_X + 17.3, 1.5, 104.0),
		Vector3(0.4, 3.0, 15.0), "far_shade")

	# The parking lot, which is a backdrop. No collision, never reached.
	_box("lot_ground", Vector3.ZERO, Vector3(ST_X, -0.6, 145.0),
		Vector3(150.0, 1.0, 68.0), "far_shade", 0.0, false)
	var n := 0
	for row in range(4):
		for col in range(14):
			var x := ST_X - 45.0 + float(col) * 7.0
			var z := 120.0 + float(row) * 12.0
			_box("car_%d" % n, Vector3.ZERO, Vector3(x, 0.7, z),
				Vector3(1.9, 1.4, 4.4), "far" if (n % 3) else "far_warm",
				0.0, false)
			n += 1
	for i in range(9):
		_cyl("lot_tree_%d" % i, Vector3.ZERO,
			Vector3(ST_X - 48.0 + float(i) * 12.0, 3.5, 116.0),
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


func _thresholds() -> void:
	for t in THRESHOLDS:
		_passage(t["name"], t["at"], t["theta"], t["width"], t["turn"])


## Local +Z is out of the plaza, local +X is the direction of the turn, and
## `turn` flips which way that is. Built in local space and rotated once, so the
## four of them are the same shape rather than four hand-placed near-misses.
func _passage(nm: String, base: Vector3, theta: float, w: float, turn: float) -> void:
	var n := w * 0.5
	var t := turn

	# Floors. Tops at y=0 to match the plaza, and the first one overlaps back
	# under the wall line so there is no seam at the threshold.
	_box("way_%s_floor_a" % nm, base, Vector3(0, -0.5 + PASSAGE_SEAM, REACH * 0.5 - 0.5),
		Vector3(w, 1, REACH + 1.0), "accent", theta)
	_box("way_%s_floor_b" % nm, base,
		Vector3(t * (n + BEND * 0.5), -0.5 + PASSAGE_SEAM, REACH - w * 0.5),
		Vector3(BEND, 1, w), "accent", theta)

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

	_box("%s_pier_l" % nm, at, Vector3(-n + 0.15, 1.7, 0.15), Vector3(0.3, 3.4, 0.3),
		"white", theta, false)
	_box("%s_pier_r" % nm, at, Vector3(n - 0.15, 1.7, 0.15), Vector3(0.3, 3.4, 0.3),
		"white", theta, false)

	if open_front:
		# A faked mouth only where there is nothing behind the wall. Where the
		# room is real the doorway is a real hole, and a hole is darker than any
		# panel imitating one.
		if solid:
			_box("%s_mouth" % nm, at, Vector3(0, 1.35, 0.02), Vector3(width - 0.7, 2.7, 0.06),
				"glass", theta, false)
		_box("%s_soffit" % nm, at, Vector3(0, 2.85, 0.24), Vector3(width - 0.7, 0.3, 0.5),
			"far_shade", theta, false)
		# Cabinets just inside, in a row facing out. Silhouettes at this size, but
		# they are the difference between a dark rectangle and somewhere to go.
		var cabs := 0 if not solid else maxi(2, int((width - 1.6) / 1.1))
		for i in range(cabs):
			var x := -n + 1.0 + float(i) * ((width - 2.0) / maxf(1.0, float(cabs - 1)))
			_box("%s_cab_%d" % [nm, i], at, Vector3(x, 0.8, 0.42),
				Vector3(0.72, 1.6, 0.6), "far_shade", theta, false)
			_box("%s_cab_%d_screen" % [nm, i], at, Vector3(x, 1.25, 0.73),
				Vector3(0.5, 0.42, 0.06), "blue", theta, false)
	else:
		# Glass, bulkhead and door are three layers of relief on one wall, and
		# all three had their back face at exactly 0 — the wall's plane and each
		# other's. Their fronts are what reads, so the backs sink into the wall
		# by differing amounts and nothing shares a plane with anything.
		_box("%s_glass" % nm, at, Vector3(0, 1.7, 0.04), Vector3(width - 0.7, 2.1, 0.12),
			"glass", theta, false)
		_box("%s_bulkhead" % nm, at, Vector3(0, 0.45, 0.1), Vector3(width - 0.7, 0.9, 0.28),
			"accent", theta, false)
		# Off to one side. Centred, a door makes the unit read as a symmetrical
		# shed; off-centre it reads as a building somebody laid out.
		_box("%s_door" % nm, at, Vector3(n - 1.1, 1.055, 0.055), Vector3(1.0, 2.1, 0.17),
			"wood", theta, false)

	# Marquee for an arcade, plain fascia for the rest.
	var band := 0.9 if open_front else 0.55
	var y := 3.7 if open_front else 3.55
	var sign_mat := "red"
	if kind == "cafe":
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
func _street_booths() -> void:
	_booth("booth_ring", Vector3(ST_X - 4.2, 0.0, 52.0), PI * 0.5, 4.5, "far_warm")
	_booth("booth_darts", Vector3(ST_X + 4.2, 0.0, 63.0), -PI * 0.5, 4.5, "accent")
	_booth("booth_hoops", Vector3(ST_X - 4.2, 0.0, 79.0), PI * 0.5, 4.0, "accent")


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

## Where the player is put down having come through the gate, and which way they
## are looking. South of the gate because the stair descends southward and comes
## out below it; turned north-west because that is where the alley mouth is, and
## arriving already looking at the way on is the difference between a threshold
## and a loading screen.
const ARRIVAL_AT := Plan.BOARDWALK_ARRIVAL
const ARRIVAL_YAW := Plan.BOARDWALK_ARRIVAL_YAW


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
	_boardwalk_wheel()
	_boardwalk_coaster()
	_boardwalk_pier()
	_boardwalk_edges()
	_boardwalk_props()
	_plaza_from_below()

	_boardwalk_seam()


## The gate at the foot of the stair, from below, and the bluff it is set into.
##
## The well the stair descends is a slot open on its west face for twenty metres
## of its length, which is correct from the plaza — you walk down inside it and
## the boardwalk is at eye level through the opening. From the boardwalk it is a
## twenty-metre notch with nothing in it, because the stair is in the plaza's
## scenes and the plaza is not mounted down here.
##
## So this side fills the notch and leaves one door. Same gate, same plane, same
## 2.6m of opening as `_west_stair` builds from the other side — and the two
## agree because both read `FOOT_GATE_X` and `STAIR_FOOT` rather than each
## measuring the bluff themselves.
##
## The crossing volume is west of the gate and the arrival is west of that, out
## on the lane. Which means the walk north to the alley never touches either: the
## lane's centre line is nearly four metres clear of both, so heading for the
## promenade cannot be mistaken for heading back up the stair.
func _boardwalk_seam() -> void:
	var foot_z := Plan.STAIR_FOOT.z
	var w := Plan.STAIR_W
	var gate_x := Plan.FOOT_GATE_X
	# The notch, filled north of the gate and above it.
	# Inset on **every** axis, so the fill is strictly inside the piece it fills.
	# `west_shell` is mounted underneath this, so these two are in the tree
	# together and the build-order seam cannot reach across scenes to separate
	# them — the inset is the only thing keeping them apart.
	#
	# It was inset on three faces and not the fourth: the height came down but the
	# centre did not move with it, so the bottom stayed on the bluff's own −12 and
	# 41m² of it z-fought the moment an unrelated edit shifted the ordinals. Both
	# ends of every axis, or it is not an inset.
	_box("bluff_infill_north", Vector3.ZERO,
		Vector3(-44.67, SHORE_TOP, (-11.94 + foot_z - w * 0.5) * 0.5),
		Vector3(2.54, 11.88, foot_z - w * 0.5 + 11.94), "far_warm")
	_box("bluff_infill_south", Vector3.ZERO,
		Vector3(-44.67, SHORE_TOP, (foot_z + w * 0.5 + 7.94) * 0.5),
		Vector3(2.54, 11.88, 7.94 - foot_z - w * 0.5), "far_warm")
	_box("bluff_infill_over", Vector3.ZERO,
		Vector3(-44.7, SHORE_TOP + 4.1, foot_z),
		Vector3(2.6, 3.8, w), "far_warm")
	# Something to see through the bars: the slab the last tread lands on.
	_box("gate_sill", Vector3.ZERO, Vector3(-44.7, SHORE_TOP - 0.25, foot_z),
		Vector3(2.6, 0.5, w), "accent")
	_box("foot_gate", Vector3.ZERO, Vector3(gate_x, SHORE_TOP + 1.1, foot_z),
		Vector3(0.2, 2.2, w), "metal")
	# A sign on the bluff beside it, because a door in a wall with no writing on
	# it is a door nobody tries.
	_box("gate_sign", Vector3.ZERO, Vector3(gate_x - 0.2, SHORE_TOP + 2.6, foot_z),
		Vector3(0.12, 0.7, 2.0), "white", 0.0, false)

	# The lane is the corridor: it goes to the gate and to the alley and nowhere
	# else, so entering it at all is enough to start the plaza loading.
	_gate_area("preload_plaza", Vector3(BACK_LANE_X, SHORE_TOP + 1.5, 4.0),
		Vector3(8.0, 3.0, 24.0), 0, &"plaza", &"boardwalk")
	_gate_area("cross_plaza", Vector3(gate_x - 0.7, SHORE_TOP + 1.4, foot_z),
		Vector3(1.2, 3.0, w), 1, &"plaza", &"boardwalk")
	_marker("arrival_from_plaza", ARRIVAL_AT, ARRIVAL_YAW)


## Everything the player can stand on, as three slabs: the promenade, the alley
## through the frontage, and the back lane behind it.
func _boardwalk_paving() -> void:
	var prom_w := (FRONT_X - FRONT_DEPTH * 0.5) - SHORE_EDGE
	var prom_x := (SHORE_EDGE + FRONT_X - FRONT_DEPTH * 0.5) * 0.5
	_box("deck_promenade", Vector3.ZERO,
		Vector3(prom_x, DECK_TOP - DECK_THICK * 0.5, (WALK_FROM_Z + WALK_TO_Z) * 0.5),
		Vector3(prom_w, DECK_THICK, WALK_TO_Z - WALK_FROM_Z), "plank")

	_box("deck_alley", Vector3.ZERO,
		Vector3(FRONT_X, DECK_TOP - DECK_THICK * 0.5, (GAP_FROM + GAP_TO) * 0.5),
		Vector3(FRONT_DEPTH, DECK_THICK, GAP_TO - GAP_FROM), "plank")

	# The lane runs from the backs of the shops to the foot of the bluff. Not
	# planked: it is a service road, and the material change is what says so.
	# The lane runs from the backs of the shops to the foot of the bluff — 7.5m
	# of it, laid 8 wide so it tucks under both rather than butting against
	# either. Not planked: it is a service road, and the material says so.
	_box("deck_lane", Vector3.ZERO,
		Vector3(BACK_LANE_X, DECK_TOP - DECK_THICK * 0.5, 3.0),
		Vector3(8.0, DECK_THICK, 74.0), "far_warm")


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
	_box("pier_deck", Vector3.ZERO,
		Vector3(mid.x, DECK_TOP - DECK_THICK * 0.5, mid.z),
		Vector3(PIER_LENGTH, DECK_THICK, PIER_HALF_W * 2.0), "plank")

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
	_box("pavilion_apron", Vector3.ZERO,
		Vector3(head.x, DECK_TOP - DECK_THICK * 0.5, head.z),
		Vector3(16.0, DECK_THICK, 17.0), "plank")
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
				Vector3(PROMENADE_X, SHORE_TOP + 5.0, z), 0.34, "white")
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
		_cyl("table_%d_shade" % i, base, Vector3(0, 2.26, 0), 1.5, 0.1,
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
		_sphere("bulb_%d_%d" % [index, b], points[b + 1], 0.11, "yellow")


## The plaza, seen from below, as massing with nothing behind it.
##
## This exists because the plaza is *gone* down here. `ParkSections` frees the
## outgoing section, so the bluff the player just walked down, the parapet they
## looked over and the arch they walked through all cease to exist the moment
## they step through the gate — and the bluff top would be a clean horizon line
## with sky above it, which is the one thing that would say "this is a different
## level" out loud.
##
## Six boxes. They are the plaza's own west wall at the plaza's own coordinates,
## which is duplication, and it is the kind a test can hold: anything that moves
## the plaza's west face and not these will show up as the skyline sliding.
func _plaza_from_below() -> void:
	_box("far_parapet", Vector3.ZERO, Vector3(-38.5, 0.5, -0.2),
		Vector3(1.0, 1.0, 16.4), "far_warm", 0.0, false)
	_box("far_overlook_n", Vector3.ZERO, Vector3(-35.0, 1.6, -11.5),
		Vector3(8.0, 3.2, 1.0), "far", 0.0, false)
	_box("far_overlook_s", Vector3.ZERO, Vector3(-35.0, 1.6, 7.5),
		Vector3(8.0, 3.2, 1.0), "far", 0.0, false)
	_box("far_west_n", Vector3.ZERO, Vector3(-26.0, 3.5, -11.5),
		Vector3(10.0, 7.0, 9.0), "far", 0.0, false)
	_box("far_west_s", Vector3.ZERO, Vector3(-26.0, 3.5, 5.5),
		Vector3(10.0, 7.0, 5.0), "far", 0.0, false)
	# The one thing on the plaza tall enough to clear the bluff from down here,
	# and the only way of telling the time that survives the crossing.
	_box("far_sign_tower", Vector3.ZERO, Vector3(18.0, 7.0, -16.0),
		Vector3(1.6, 14.0, 1.6), "far", 0.0, false)
