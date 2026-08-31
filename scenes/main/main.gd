extends Node3D

## The game's root. It holds the complete park, the sun, the player and the HUD.
## The world is one continuously standing composition; area names are logical
## context for the map, interactions and crowds, not ownership boundaries.
##
## The sun is up here rather than in the plaza because it belongs to the park
## and not to any part of it. `scenes/world/daylight.gd` drives it off
## `ParkClock` using the latitude's real solar geometry, and a section swap must
## not be able to interrupt that: a sun parented to the plaza is freed with the
## world, and no route through the park can interrupt it.
##
## Same argument for the environment and the sky. There is one sky over the
## park.


## Establish the initial logical area. `ParkSections` then follows the player's
## position without loading, freeing or teleporting any world scene.
func _ready() -> void:
	ParkSections.adopt(&"plaza")
