extends AnimatableBody3D

## A guest walking a fixed loop.
##
## Waypoints are offsets from wherever the instance is placed, so a loop can be
## copied around the plaza without re-authoring it. This is deliberately dumb:
## the real park runs subjects on a schedule, and this is the placeholder that
## proves the plaza feels inhabited enough to photograph.

@export var waypoints: PackedVector3Array = PackedVector3Array()
@export var speed := 1.3
@export var turn_speed := 6.0
@export var pause_at_waypoint := 1.2
@export var start_delay := 0.0

var _origin := Vector3.ZERO
var _index := 0
var _wait := 0.0


func _ready() -> void:
	add_to_group("npc")
	_origin = global_position
	_wait = start_delay


func _physics_process(delta: float) -> void:
	if waypoints.size() < 2:
		return

	if _wait > 0.0:
		_wait -= delta
		return

	var target := _origin + waypoints[_index]
	var to_target := target - global_position
	to_target.y = 0.0
	var distance := to_target.length()

	if distance < 0.15:
		_index = (_index + 1) % waypoints.size()
		_wait = pause_at_waypoint
		return

	var direction := to_target / distance
	global_position += direction * minf(speed * delta, distance)
	rotation.y = lerp_angle(rotation.y, atan2(-direction.x, -direction.z), turn_speed * delta)
