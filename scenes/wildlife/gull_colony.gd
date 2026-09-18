class_name GullColony
extends Node3D

## Connects explicitly placed gulls to explicitly placed roost and feeding
## markers. The marker nodes in wildlife.tscn own every artistic location; this
## script only staggers departures and gives each bird a repeatable home.

@export_range(0, 32, 1) var resident_count := 9

@onready var roosts: Node3D = $roosts
@onready var foraging_sites: Node3D = $foraging_sites
@onready var birds: Node3D = $birds


func _ready() -> void:
	var roost_positions: Array[Vector3] = []
	for child in roosts.get_children():
		if child is Marker3D:
			child.add_to_group("gull_roost")
			roost_positions.append((child as Marker3D).global_position)
	var feeding_positions: Array[Vector3] = []
	for child in foraging_sites.get_children():
		if child is Marker3D:
			child.add_to_group("gull_foraging_site")
			feeding_positions.append((child as Marker3D).global_position)
	if roost_positions.is_empty() or feeding_positions.is_empty():
		push_error("gull_colony: roost and foraging markers are both required")
		return
	var gulls: Array[ParkBird] = []
	for child in birds.get_children():
		if child is ParkBird and (child as ParkBird).species == "gull":
			gulls.append(child as ParkBird)
	var resident_total := mini(resident_count, gulls.size())
	for index in range(gulls.size()):
		var resident := index < resident_total
		var roost_index := index if resident else index - resident_total
		gulls[index].configure_colony(
			roost_positions[roost_index % roost_positions.size()],
			feeding_positions,
			resident,
			maxi(0, index - resident_total) % feeding_positions.size())
