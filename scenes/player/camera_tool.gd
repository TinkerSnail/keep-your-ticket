extends Node

## The Instamatic.
##
## Fixed focus, fixed exposure, no zoom — raising the camera changes what the
## player sees framed, not what the lens does. This node only tracks whether the
## camera is up and announces shutter presses; the HUD owns the actual capture
## because it owns overlay visibility.

signal raised_changed(raised: bool)
signal shutter_requested

## Raising the camera is tap-or-hold. A quick tap leaves it up until tapped
## again; holding keeps it up only while held. A trackpad cannot hold one
## button and click another, so nothing here requires two hands or two fingers.
const TAP_SECONDS := 0.25

## The finder window sits about 25mm above the taking lens and looks parallel to
## it, so the two are not aimed at the same thing. At any distance the lens sees
## 25mm lower than the finder does; far away that is nothing, close up it is the
## difference between a head and a chin. The picture comes back shifted down
## from the one that was composed, and this camera can only be solved by
## standing closer — so its one lie is loudest exactly when the player is doing
## what it asks.
const FINDER_RISE := 0.025

## Fixed focus gives up before this, so there is no point modelling parallax
## nearer than it. It is also where the printed correction mark is drawn.
const NEAR_LIMIT := 0.6

## Past this the offset is well under a pixel and a ray this long is wasted.
const SUBJECT_MAX := 25.0

var raised := false

var _pressed_at := 0.0
var _latched := false
var _swallow_release := false


func _ready() -> void:
	add_to_group("camera_tool")


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("camera_raise"):
		_on_raise_pressed()
	elif event.is_action_released("camera_raise"):
		_on_raise_released()
	elif raised and event.is_action_pressed("shutter"):
		shutter_requested.emit()


func raise() -> void:
	_latched = true
	_set_raised(true)


func lower() -> void:
	_latched = false
	_set_raised(false)


## Whatever is under the middle of the frame, in metres. `INF` when the frame is
## pointed at sky or at nothing within range, which is the case where parallax
## does not apply at all.
func subject_distance() -> float:
	var cam := _lens()
	if cam == null:
		return INF
	var from := cam.global_position
	var to := from - cam.global_transform.basis.z * SUBJECT_MAX
	var query := PhysicsRayQueryParameters3D.create(from, to)
	var body := get_parent()
	if body is CollisionObject3D:
		query.exclude = [body.get_rid()]
	var hit := cam.get_world_3d().direct_space_state.intersect_ray(query)
	if hit.is_empty():
		return INF
	return from.distance_to(hit["position"])


## How far below the composed frame the lens actually looked, as a fraction of
## screen height. Live, so it moves as the player closes on a subject.
func parallax_screen_fraction() -> float:
	return parallax_fraction_at(subject_distance())


## What the finder's printed mark is drawn at: the worst offset the camera
## admits to.
func close_range_parallax_fraction() -> float:
	return parallax_fraction_at(NEAR_LIMIT)


## The same offset for a stated distance. The finder's printed mark is this at
## `NEAR_LIMIT` — the worst case the camera admits to, drawn once and never
## updated, because a finder that corrected itself would be telling the player
## what they were about to get.
func parallax_fraction_at(distance: float) -> float:
	var cam := _lens()
	if cam == null or not is_finite(distance):
		return 0.0
	var angle := atan(FINDER_RISE / maxf(distance, NEAR_LIMIT))
	return 0.5 * tan(angle) / tan(deg_to_rad(cam.fov) * 0.5)


## The eye camera, not whatever is currently rendering — raising the Instamatic
## forces first person, so by the time any of this is asked for they are the
## same, but the optics belong to the lens either way.
func _lens() -> Camera3D:
	return get_node_or_null("../head/camera") as Camera3D


func _on_raise_pressed() -> void:
	_pressed_at = Time.get_ticks_msec() / 1000.0
	if _latched:
		# Already held up by a previous tap — this press puts it away, and the
		# matching release must not be read as another tap.
		_latched = false
		_swallow_release = true
		_set_raised(false)
	else:
		_set_raised(true)


func _on_raise_released() -> void:
	if _swallow_release:
		_swallow_release = false
		return
	if Time.get_ticks_msec() / 1000.0 - _pressed_at <= TAP_SECONDS:
		_latched = true
	else:
		_set_raised(false)


func _set_raised(value: bool) -> void:
	if raised == value:
		return
	raised = value
	raised_changed.emit(raised)
