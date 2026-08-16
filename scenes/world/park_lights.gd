extends Node

## Turns the park's own lights on, and turns most of them off again at ten.
##
## The complement of `daylight.gd`: that one drives the sun, the sky and the
## ambient, and this one drives everything the park plugs in. They read the same
## number — the sun's altitude, from the same solar geometry — so the lamps come
## up as the sky goes down rather than at a clock time somebody typed. Which is
## also what makes the crossfade work at all: the ambient floor is falling on
## exactly the curve the lamps are rising on.
##
## Two things get driven, and they are not the same thing:
##
##   **The fittings**, which are 196 pieces of geometry sharing three emissive
##   materials. A bulb reads as *on* because its own surface is bright, and that
##   is what carries at distance — the festoon runs on the masts, the wheel's rim
##   and the cascade's two eyes are all read from 100m or more, where the light
##   they cast has fallen off to nothing. Driven by writing
##   `emission_energy_multiplier` on three materials, which is three assignments
##   for the whole park because those materials are external resources rather
##   than per-scene copies. See `_lit_material` in `tools/gen_props.gd`.
##
##   **The lights**, ~110 `OmniLight3D` and `SpotLight3D` in the `park_light`
##   group, which put light on the ground and on the walls. These are what make
##   the plaza a room after dark instead of an unlit field with glowing dots in
##   it, and they are the part that costs anything.
##
## Both are needed and neither substitutes. Emission with no lights is a park of
## floating beads; lights with no emission is a park where everything is lit and
## nothing is a lamp.

const Daylight := preload("res://scenes/world/daylight.gd")
const Plan := preload("res://scripts/park_plan.gd")

## Sun altitude in degrees against how lit the park is, 0 to 1.
##
## Starts before sunset on purpose. Real parks switch their lighting on while
## there is still plenty of sky — a photocell trips at dusk, not at dark — and
## the half hour where the lamps are on and the light is still golden is the best
## looking part of the evening. It is also the hour the boardwalk crowd peaks at,
## so it is the one the game spends the most time in.
##
## Fully on by −6°, which is `daylight.gd`'s own `NIGHT_ALTITUDE` and the point
## its sun switches off. Past there nothing more happens; the park is as lit as
## it gets and the sky keeps darkening around it.
const LEVEL := [
	[8.0, 0.0],
	[3.0, 0.35],
	[0.0, 0.75],
	[-6.0, 1.0],
]

## What survives the park closing, by light kind.
##
## `night.md`: "The lights are mostly off and nothing is silent." Mostly, not
## all — the point of the shut park is that it reads as recently vacated and
## still powered, and a park at zero reads as a power cut. So the fixtures thin
## rather than switch: a quarter of them stay on, dim, which leaves pools with
## dark between them instead of an even wash. The uplighting goes completely,
## because floodlighting is the park performing and there is nobody to perform
## to. The service lights do not change at all — they were never for the guests.
##
## This is the state the Instamatic cannot expose, and that is deliberate:
## `night.md` makes the dark park visible long before it is photographable, and
## camera capability is the progression gate. Do not brighten these to make the
## night shootable. The night is meant to be shut.
const CLOSED_FIXTURE := 0.30
const CLOSED_FEATURE := 0.0
const CLOSED_SERVICE := 1.0

## How much of the fixture set stays on after close. One in four, chosen by a
## hash of the node's name so it is the same four every night and stable across
## a section unloading and coming back — a random subset re-rolled on each mount
## would have the plaza's lamps flickering on and off as the player crossed the
## seam.
const CLOSED_KEEP := 4

## How long the park takes to shut its lights down, in clock minutes. A hard
## switch at 22:00:00 is a light-switch sound effect with no sound effect. Six
## minutes is long enough to read as the place closing and short enough that the
## player who is watching for it sees it happen.
const CLOSING_FADE_MINUTES := 6.0

## Emission multiplier at full darkness, per material. Not one number, because
## these are three different kinds of fitting: a clear festoon bulb is the
## brightest thing per square centimetre, a frosted lamp globe is larger and
## softer, and the cascade's eyes have to hold up at 130m across open water.
## `LAMP` is well below `BULB` and that is a size argument rather than a taste
## one. A festoon bulb is 11cm across and a promenade globe is 68cm, so at equal
## emission the globe puts about forty times the light into the frame and clips
## to a white disc — which is what the first capture showed, two blown-out balls
## dominating the overlook and reading as bugs rather than as lamps. Emission is
## per unit area; the big fittings have to be dimmer to look the same brightness.
##
## `TRIM` is the lowest of the four and has to be. It is not a fitting — it is
## 40m of coping down each of the cascade's wings, so its *area* is enormous
## compared to a bulb, and at bulb brightness the monument stops being a lit edge
## and becomes two glowing girders. Low enough to read as stone with light in it.
const BULB_EMISSION := 2.6
const LAMP_EMISSION := 1.3
const EYE_EMISSION := 3.4
const TRIM_EMISSION := 0.42

var _bulb: StandardMaterial3D
var _lamp: StandardMaterial3D
var _eye: StandardMaterial3D
var _trim: StandardMaterial3D

## The group is re-read when a section mounts rather than every frame. A section
## swap is the only thing that changes which lights exist, and the plaza's own
## are 60-odd nodes — scanning them 60 times a second to discover nothing has
## changed is the kind of cost that does not show up until the crowd is on top
## of it.
var _lights: Array[Light3D] = []
var _stale := true

## What was applied last, so a frame where nothing changed does nothing. The
## clock runs at twelve times real, so the level still moves visibly; this only
## skips the long flat stretches, which is most of the day.
var _last_level := -1.0
var _last_open := true


func _ready() -> void:
	_bulb = load(Plan.BULB_MATERIAL) as StandardMaterial3D
	_lamp = load(Plan.LAMP_MATERIAL) as StandardMaterial3D
	_eye = load(Plan.EYE_MATERIAL) as StandardMaterial3D
	_trim = load(Plan.TRIM_MATERIAL) as StandardMaterial3D
	if _bulb == null or _lamp == null or _eye == null or _trim == null:
		# Loud, because the failure is otherwise invisible: the lights still come
		# on and light the ground, and only the fittings stay dark. Which reads
		# as an art problem rather than as a missing file.
		push_error("park_lights: the emissive materials did not load — "
			+ "run tools/gen_props.gd to write them")
		set_process(false)
		return

	ParkSections.section_entered.connect(_on_section_changed)
	ParkClock.clock_jumped.connect(_on_clock_jumped)
	_apply(true)


func _process(_delta: float) -> void:
	_apply(false)


func _on_section_changed(_id: StringName) -> void:
	# The new section's lights are generated dark and invisible, so they have to
	# be brought up to whatever the current level is on the frame they arrive.
	# Without the forced re-apply the boardwalk mounts at nine in the evening
	# with every fitting off, and stays that way until the level happens to move.
	_stale = true
	_apply(true)


func _on_clock_jumped() -> void:
	_apply(true)


func _apply(force: bool) -> void:
	var altitude := Daylight.solar_position(ParkClock.hours()).x
	var level := _level_at(altitude)
	var open := _closing_level()

	if not force and is_equal_approx(level, _last_level) \
			and is_equal_approx(open, _last_open):
		return
	_last_level = level
	_last_open = open

	# The fittings. Four writes, ~190 objects.
	#
	# These follow the park closing too, and the first version did not — every
	# bulb in the park went on glowing at full brightness after ten while three
	# quarters of the lights under them were switched off, so the festoons were
	# lit strings casting nothing. The materials are shared, so this cannot thin
	# one fitting in four the way `_closing_factor` does for the lights; what it
	# can do is dim the lot to the same fraction, which at a distance reads as a
	# park with its lights mostly out rather than as one still fully dressed.
	#
	# The trim takes the *feature* fraction instead, and goes fully dark. It is
	# floodlighting by another means — the cascade presenting itself — and the
	# rule for that after close is the same whether the light comes from a
	# spotlight or from the stone.
	var fixture_on := lerpf(CLOSED_FIXTURE, 1.0, open)
	var feature_on := lerpf(CLOSED_FEATURE, 1.0, open)
	_bulb.emission_energy_multiplier = BULB_EMISSION * level * fixture_on
	_lamp.emission_energy_multiplier = LAMP_EMISSION * level * fixture_on
	_eye.emission_energy_multiplier = EYE_EMISSION * level * fixture_on
	_trim.emission_energy_multiplier = TRIM_EMISSION * level * feature_on

	if _stale:
		_rescan()

	for l in _lights:
		if not is_instance_valid(l):
			_stale = true
			continue
		var kind: int = l.get_meta("light_kind", Plan.LIGHT_FIXTURE)
		var base: float = l.get_meta("base_energy", 1.0)
		var energy := base * level * _closing_factor(kind, l, open)
		# Hidden rather than left at zero energy. A light with no energy is still
		# a light the renderer clusters, culls and considers; invisible, it is
		# not there at all. Since the park is fully lit for about two hours in
		# twelve, this is what keeps the whole system free for the other ten.
		l.visible = energy > 0.001
		if l.visible:
			l.light_energy = energy


## Per-kind survival after close, blended over the closing fade.
##
## `open` is 1 while the park is open and 0 once it has shut, with the fade in
## between, so each kind interpolates from full to its own closed fraction.
func _closing_factor(kind: int, l: Light3D, open: float) -> float:
	match kind:
		Plan.LIGHT_SERVICE:
			return lerpf(CLOSED_SERVICE, 1.0, open)
		Plan.LIGHT_FEATURE:
			return lerpf(CLOSED_FEATURE, 1.0, open)
		_:
			var keep := _kept_after_close(l)
			return lerpf(CLOSED_FIXTURE if keep else 0.0, 1.0, open)


## Whether a fixture is one of the ones left on. Hashed from the name so it is
## stable across runs and across a section unloading and remounting.
func _kept_after_close(l: Light3D) -> bool:
	return absi(hash(l.name)) % CLOSED_KEEP == 0


## 1 while the park is open, 0 once it is shut, fading between over the last few
## minutes. Not `ParkClock.is_open()`, which is a bool and would step.
func _closing_level() -> float:
	var h := ParkClock.hours()
	if h < ParkClock.OPEN_HOUR:
		# The small hours, before the park opens again — still shut.
		return 0.0
	var fade := CLOSING_FADE_MINUTES / 60.0
	return clampf((ParkClock.CLOSE_HOUR - h) / fade, 0.0, 1.0)


func _rescan() -> void:
	_lights.clear()
	for n in get_tree().get_nodes_in_group(Plan.LIGHT_GROUP):
		if n is Light3D:
			_lights.append(n)
	_stale = false


static func _level_at(altitude: float) -> float:
	# The table runs downward in altitude, unlike `daylight.gd`'s, because this
	# is a curve about the sun setting rather than about it being up.
	if altitude >= float(LEVEL[0][0]):
		return float(LEVEL[0][1])
	for i in LEVEL.size() - 1:
		var a: Array = LEVEL[i]
		var b: Array = LEVEL[i + 1]
		if altitude >= float(b[0]):
			var t := (float(a[0]) - altitude) / (float(a[0]) - float(b[0]))
			return lerpf(float(a[1]), float(b[1]), t)
	return float(LEVEL[LEVEL.size() - 1][1])
