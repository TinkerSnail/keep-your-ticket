extends Control

## The bright-line finder.
##
## The Instamatic's finder is not its lens. It is a separate plastic window an
## inch above and to the side, and everything worth having here follows from
## that: you see outside the picture, the picture is square where the screen is
## not, and what the lens got is not quite what was composed.
##
## So this is not a crop overlay. There is no mask outside the lines — the
## surround stays visible, because the propped service door just outside the
## frame is the thing the whole park design is built to put there. The player
## sees it sitting outside the picture and decides whether to abandon the
## assignment for it. The tunnel sibling is what takes the periphery away; these
## lines only say where the photograph ends.
##
## No reticle and no centre dot. Aiming is look-based and the player composes the
## whole frame.

## 126 film is square, so the photograph is square. This is the number to change
## if the camera ever stops being an Instamatic; `hud.gd` crops to whatever it
## says, so the lines are never decoration.
@export var frame_aspect := 1.0
## Fraction of screen height taken by the picture. The tunnel window is larger,
## which is what leaves a surround to see into.
@export var frame_scale := 0.60
@export var thickness := 2.0
## Bright-lines are bright. A dark line under a light one is how a real finder
## stays readable against sky, and it costs one extra draw.
@export var line_color := Color(1, 1, 1, 0.92)
@export var line_shadow := Color(0, 0, 0, 0.45)
## The parallax mark: where the top of the picture really is at closest focus.
@export var mark_color := Color(1, 1, 1, 0.5)
@export var mark_length := 26.0

## Shutter kick. The finder does not black out — no mirror — so the clack and a
## twitch in the frame are the only evidence anything happened.
var jolt := 0.0:
	set(value):
		jolt = value
		queue_redraw()

var _specks: Array[Vector3] = []


func _ready() -> void:
	resized.connect(queue_redraw)
	_seed_specks()


func _draw() -> void:
	var frame := picture_rect()

	_draw_frame(frame)
	_draw_parallax_mark(frame)
	_draw_specks()


## The picture, in this control's coordinates. `hud.gd` reads this to cut the
## photograph out of the viewport, which is what keeps the lines honest.
func picture_rect() -> Rect2:
	var available := size * frame_scale
	var height := minf(size.y * frame_scale, available.y)
	var width := height * frame_aspect
	if width > size.x * 0.94:
		width = size.x * 0.94
		height = width / frame_aspect
	var frame_size := Vector2(width, height)
	return Rect2(((size - frame_size) * 0.5).round(), frame_size)


func _draw_frame(frame: Rect2) -> void:
	var rect := Rect2(frame.position + Vector2(0.0, jolt), frame.size)
	draw_rect(rect.grow(1.0), line_shadow, false, thickness + 2.0)
	draw_rect(rect, line_color, false, thickness)


## Drawn once at the closest distance the camera pretends to focus, and never
## updated. A finder that tracked the real offset would be telling the player
## what they were about to get, which is the one thing this camera must not do.
## It says an error exists and roughly how big. The print says what it was.
func _draw_parallax_mark(frame: Rect2) -> void:
	var drop := _close_range_drop()
	if drop <= 1.0:
		return
	var y := frame.position.y + drop + jolt
	if y > frame.end.y:
		return
	var span := minf(mark_length, frame.size.x * 0.28)
	draw_line(Vector2(frame.position.x, y), Vector2(frame.position.x + span, y), mark_color, thickness)
	draw_line(Vector2(frame.end.x - span, y), Vector2(frame.end.x, y), mark_color, thickness)


func _close_range_drop() -> float:
	var camera_tool := get_tree().get_first_node_in_group("camera_tool")
	if camera_tool == null or not camera_tool.has_method("close_range_parallax_fraction"):
		return 0.0
	return camera_tool.close_range_parallax_fraction() * size.y


## Dust on the finder glass, not on the film. It is in the way of looking and
## never in the way of the photograph, which is the distinction the whole
## overlay rests on.
func _draw_specks() -> void:
	for speck in _specks:
		var at := Vector2(speck.x * size.x, speck.y * size.y)
		draw_circle(at, speck.z, Color(0.85, 0.84, 0.8, 0.13))


func _seed_specks() -> void:
	var rng := RandomNumberGenerator.new()
	# Fixed, because the same camera has the same dirt on it every day.
	rng.seed = 19970614
	_specks.clear()
	for i in 16:
		_specks.append(Vector3(
			rng.randf_range(0.18, 0.82),
			rng.randf_range(0.14, 0.86),
			rng.randf_range(0.6, 1.9)
		))
