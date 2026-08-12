extends Node3D

## The game's root. It holds the things that outlive a section — the sun, the
## player, the HUD — and a host node for the section that happens to be
## standing.
##
## The sun is up here rather than in the plaza because it belongs to the park
## and not to any part of it. `scenes/world/daylight.gd` drives it off
## `ParkClock` using the latitude's real solar geometry, and a section swap must
## not be able to interrupt that: a sun parented to the plaza is freed with the
## plaza, and the player walks out of the arch into a lit world and down the
## stair into a black one.
##
## Same argument for the environment and the sky. There is one sky over the
## park.


## The plaza is placed by hand in this scene rather than mounted by
## `ParkSections`, because something has to be standing on frame one and the
## alternative is a launch that loads the hub through the same machinery it uses
## for a threshold nobody has crossed. `adopt` tells the loader that what it
## finds under the host is the plaza, so the first crossing has something to
## take down.
func _ready() -> void:
	ParkSections.adopt(&"plaza")
