extends Control

## The viewfinder overlay.
##
## Corner brackets and a soft mask outside the frame. No reticle and no centre
## dot — aiming is look-based and the player composes the whole frame, so the
## overlay only says where the edges are.

@export var frame_aspect := 1.5
@export var frame_scale := 0.74
@export var bracket_length := 46.0
@export var thickness := 3.0
@export var line_color := Color(1, 1, 1, 0.9)
@export var mask_color := Color(0, 0, 0, 0.4)


func _ready() -> void:
	resized.connect(queue_redraw)


func _draw() -> void:
	var frame := _frame_rect()

	draw_rect(Rect2(0.0, 0.0, size.x, frame.position.y), mask_color)
	draw_rect(Rect2(0.0, frame.end.y, size.x, size.y - frame.end.y), mask_color)
	draw_rect(Rect2(0.0, frame.position.y, frame.position.x, frame.size.y), mask_color)
	draw_rect(
		Rect2(frame.end.x, frame.position.y, size.x - frame.end.x, frame.size.y),
		mask_color
	)

	var length := minf(bracket_length, minf(frame.size.x, frame.size.y) * 0.25)
	var corners := [
		[frame.position, Vector2(1, 0), Vector2(0, 1)],
		[Vector2(frame.end.x, frame.position.y), Vector2(-1, 0), Vector2(0, 1)],
		[Vector2(frame.position.x, frame.end.y), Vector2(1, 0), Vector2(0, -1)],
		[frame.end, Vector2(-1, 0), Vector2(0, -1)],
	]
	for corner in corners:
		var point: Vector2 = corner[0]
		draw_line(point, point + corner[1] * length, line_color, thickness)
		draw_line(point, point + corner[2] * length, line_color, thickness)


func _frame_rect() -> Rect2:
	var available := size * frame_scale
	var width := available.x
	var height := width / frame_aspect
	if height > available.y:
		height = available.y
		width = height * frame_aspect
	var frame_size := Vector2(width, height)
	return Rect2((size - frame_size) * 0.5, frame_size)
