extends Node

## Drives the sun, the sky and the ambient from `ParkClock`.
##
## The park's axis is fixed: you come in from the south, the boardwalk is west.
## So the sun's arc is a constraint the sections get laid out against, not a
## lighting setting to tune per scene, and it is worth computing rather than
## keyframing. Real solar geometry for the park's latitude gives sunrise in the
## north-east, solar noon to the south, and sunset just north of due west —
## which is the claim `design.md` makes about the boardwalk, arrived at from the
## sky rather than asserted.
##
## World compass: north is -Z, east is +X, south is +Z, west is -X.

## Arlington, Texas — the park the entrance and parking-lot layout was checked
## against. The game's park is nowhere in particular, but it is somewhere with
## this sun.
const LATITUDE_DEG := 32.75

## Solar declination. +20 is mid-August: long day, high sun, the crowded and hot
## season `design.md` describes. Seasons move this between roughly -23 and +23.
const DECLINATION_DEG := 20.0

## Clock time minus solar time. Daylight saving plus the park's offset within
## its time zone. Without it solar noon lands at 12:00 and the evening light
## arrives two hours too early.
const SOLAR_OFFSET_HOURS := 1.75

## Below this the sun is off and the sky is night. Civil twilight.
const NIGHT_ALTITUDE := -6.0

## Paths rather than node references, because a scene file lists its nodes in
## order and this one has to come before the sun it drives.
@export var sun_path: NodePath = ^"../sun"
@export var world_environment_path: NodePath = ^"../world_environment"

var sun: DirectionalLight3D
var world_environment: WorldEnvironment

## Sun colour and energy against altitude in degrees. The 40-degree row is the
## pair that made the greybox concrete stop reading as water, kept as the
## anchor the rest of the day was built around.
const SUN_COLOR := [
	[NIGHT_ALTITUDE, Color(0.35, 0.30, 0.42)],
	[0.0, Color(1.0, 0.55, 0.32)],
	[6.0, Color(1.0, 0.74, 0.50)],
	[15.0, Color(1.0, 0.88, 0.70)],
	[40.0, Color(1.0, 0.95, 0.86)],
	[75.0, Color(1.0, 0.97, 0.92)],
]

## Energy comes back down over the top of the arc, which the sun does not do.
## Nothing here has an aperture — auto-exposure is exactly what the Instamatic
## is not allowed to have, since the night stays shut until the camera opens it
## — so peak sun is where the greybox albedo clips, and the curve is what stops
## an August noon from turning the concrete into white paper.
const SUN_ENERGY := [
	[NIGHT_ALTITUDE, 0.0],
	[0.0, 0.35],
	[6.0, 1.1],
	[15.0, 1.6],
	[40.0, 1.8],
	[75.0, 1.55],
]

const AMBIENT_COLOR := [
	[-18.0, Color(0.16, 0.19, 0.28)],
	[NIGHT_ALTITUDE, Color(0.32, 0.36, 0.48)],
	[0.0, Color(0.62, 0.55, 0.55)],
	[15.0, Color(0.76, 0.74, 0.72)],
	[40.0, Color(0.78, 0.76, 0.72)],
]

const AMBIENT_ENERGY := [
	[-18.0, 0.06],
	[NIGHT_ALTITUDE, 0.25],
	[0.0, 0.45],
	[15.0, 0.75],
	[40.0, 0.86],
	[75.0, 0.78],
]

const SKY_TOP := [
	[-18.0, Color(0.03, 0.04, 0.08)],
	[NIGHT_ALTITUDE, Color(0.12, 0.15, 0.30)],
	[0.0, Color(0.28, 0.36, 0.58)],
	[10.0, Color(0.33, 0.50, 0.74)],
	[40.0, Color(0.35, 0.55, 0.78)],
]

const SKY_HORIZON := [
	[-18.0, Color(0.07, 0.08, 0.13)],
	[NIGHT_ALTITUDE, Color(0.42, 0.28, 0.30)],
	[0.0, Color(0.92, 0.62, 0.42)],
	[10.0, Color(0.82, 0.80, 0.74)],
	[40.0, Color(0.72, 0.78, 0.80)],
]

const SKY_ENERGY := [
	[-18.0, 0.15],
	[NIGHT_ALTITUDE, 0.5],
	[0.0, 0.9],
	[10.0, 1.0],
]

var _sky_material: ProceduralSkyMaterial
var _environment: Environment


func _ready() -> void:
	sun = get_node_or_null(sun_path) as DirectionalLight3D
	world_environment = get_node_or_null(world_environment_path) as WorldEnvironment
	if sun == null or world_environment == null:
		push_error("daylight needs both a sun and a world_environment")
		set_process(false)
		return
	_environment = world_environment.environment
	_sky_material = _environment.sky.sky_material as ProceduralSkyMaterial
	_apply(ParkClock.hours())


func _process(_delta: float) -> void:
	_apply(ParkClock.hours())


func _apply(clock_hours: float) -> void:
	var solar := solar_position(clock_hours)
	var altitude: float = solar.x
	var azimuth: float = solar.y

	sun.visible = altitude > NIGHT_ALTITUDE
	if sun.visible:
		# Never quite vertical at this latitude, but `look_at` has no answer for
		# a direction parallel to its up vector, so don't let a changed
		# declination be the thing that finds that out.
		var to_sun := direction_to_sun(minf(altitude, 88.0), azimuth)
		sun.look_at(sun.global_position - to_sun, Vector3.UP)
		sun.light_color = _color_at(SUN_COLOR, altitude)
		sun.light_energy = _value_at(SUN_ENERGY, altitude)

	_environment.ambient_light_color = _color_at(AMBIENT_COLOR, altitude)
	_environment.ambient_light_energy = _value_at(AMBIENT_ENERGY, altitude)

	if _sky_material != null:
		var horizon := _color_at(SKY_HORIZON, altitude)
		_sky_material.sky_top_color = _color_at(SKY_TOP, altitude)
		_sky_material.sky_horizon_color = horizon
		_sky_material.ground_horizon_color = horizon.darkened(0.15)
		_sky_material.sky_energy_multiplier = _value_at(SKY_ENERGY, altitude)


## Solar altitude and azimuth in degrees for a clock time, as a Vector2 of
## (altitude, azimuth). Azimuth is measured from north and increases clockwise,
## so 90 is east and 270 is west.
static func solar_position(clock_hours: float) -> Vector2:
	var lat := deg_to_rad(LATITUDE_DEG)
	var dec := deg_to_rad(DECLINATION_DEG)
	# Hour angle: zero at solar noon, negative in the morning.
	var hour_angle := deg_to_rad(15.0 * (clock_hours - SOLAR_OFFSET_HOURS - 12.0))

	var sin_altitude := sin(dec) * sin(lat) + cos(dec) * cos(lat) * cos(hour_angle)
	var altitude := asin(clampf(sin_altitude, -1.0, 1.0))

	var azimuth := atan2(
		sin(hour_angle),
		cos(hour_angle) * sin(lat) - tan(dec) * cos(lat)
	) + PI

	return Vector2(rad_to_deg(altitude), rad_to_deg(azimuth))


## Unit vector pointing from the park toward the sun.
static func direction_to_sun(altitude_deg: float, azimuth_deg: float) -> Vector3:
	var alt := deg_to_rad(altitude_deg)
	var az := deg_to_rad(azimuth_deg)
	var horizontal := cos(alt)
	return Vector3(horizontal * sin(az), sin(alt), -horizontal * cos(az))


static func _color_at(stops: Array, altitude: float) -> Color:
	var i := _span(stops, altitude)
	if i < 0:
		return stops[0][1] as Color
	if i >= stops.size() - 1:
		return stops[stops.size() - 1][1] as Color
	var a: Array = stops[i]
	var b: Array = stops[i + 1]
	return (a[1] as Color).lerp(b[1] as Color, _weight(float(a[0]), float(b[0]), altitude))


static func _value_at(stops: Array, altitude: float) -> float:
	var i := _span(stops, altitude)
	if i < 0:
		return float(stops[0][1])
	if i >= stops.size() - 1:
		return float(stops[stops.size() - 1][1])
	var a: Array = stops[i]
	var b: Array = stops[i + 1]
	return lerpf(float(a[1]), float(b[1]), _weight(float(a[0]), float(b[0]), altitude))


## Index of the stop at or below `altitude`, or -1 if it sits below them all.
static func _span(stops: Array, altitude: float) -> int:
	if altitude < float(stops[0][0]):
		return -1
	var i := stops.size() - 1
	while i > 0 and altitude < float(stops[i][0]):
		i -= 1
	return i


static func _weight(low: float, high: float, at: float) -> float:
	if is_equal_approx(low, high):
		return 0.0
	return clampf((at - low) / (high - low), 0.0, 1.0)
