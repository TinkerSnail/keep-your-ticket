extends SceneTree

## Renderer-independent acceptance for the passing coastal shower. Loading the
## scripts late also keeps this test independent of autoload registration, so
## it can run through `--script` with Godot's dummy renderer.


func _initialize() -> void:
	var weather_script := load("res://scenes/world/weather.gd")
	var daylight_script := load("res://scenes/world/daylight.gd")
	if weather_script == null or daylight_script == null:
		_fail("weather scripts did not load")
		return

	var weather: Node = weather_script.new() as Node
	var daylight: Node = daylight_script.new() as Node
	var before: Vector4 = weather.sample(9.5)
	var peak: Vector4 = weather.sample(10.35)
	var aftermath: Vector4 = weather.sample(11.75)
	var sunset: Vector4 = weather.sample(19.5)
	var dry: Dictionary = weather.wet_surface_values(
		Color(0.68, 0.62, 0.54), 0.95, 0.0, 0.0)
	var wet: Dictionary = weather.wet_surface_values(
		Color(0.68, 0.62, 0.54), 0.95, 0.0, 1.0)
	daylight.set_weather(2.0, -1.0)

	var failures: Array[String] = []
	_expect(before.is_equal_approx(Vector4.ZERO),
		"weather begins before its authored arrival", failures)
	_expect(peak.y > 0.99 and peak.x > 0.9,
		"the shower never reaches a readable peak", failures)
	_expect(aftermath.y < 0.01 and aftermath.z > 0.99,
		"the wet aftermath does not outlast the visible rain", failures)
	_expect(Vector3(sunset.x, sunset.y, sunset.z).is_equal_approx(Vector3.ZERO),
		"the shower does not clear for the protected western sunset", failures)
	_expect(float(wet["roughness"]) < 0.3 and float(dry["roughness"]) > 0.9,
		"wet decking does not gain a distinct reflective response", failures)
	_expect((wet["albedo"] as Color).get_luminance()
		< (dry["albedo"] as Color).get_luminance(),
		"wet decking does not darken", failures)
	_expect(is_equal_approx(daylight.weather_cloudiness, 1.0)
		and is_equal_approx(daylight.weather_rain, 0.0),
		"daylight does not clamp weather input", failures)

	weather.free()
	daylight.free()
	if failures.is_empty():
		print("PASS: shower timing, wet response and daylight input")
		quit()
		return
	for failure in failures:
		printerr("FAIL: ", failure)
	quit(1)


func _expect(condition: bool, message: String, failures: Array[String]) -> void:
	if not condition:
		failures.append(message)


func _fail(message: String) -> void:
	printerr("FAIL: ", message)
	quit(1)
