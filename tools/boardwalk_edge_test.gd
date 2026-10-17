extends Node

## Test: the boardwalk's pier and its open edges, walked by the real player.
##
## `footprint_walk_test` walks the waterfront spine centre and both edges, but
## the pier is not a route body and an edge test asks a different question:
## not "can I walk along it" but "does it stop me". Pushed square at the water,
## the wheel's jetty, the bluff, the shop backs, the yard and the coaster
## fence; none of those may arrive. The pier is walked out to the pavilion and
## back, the editor-owned T-head loop is walked in both directions, every new
## water edge is pushed, and the Grand Circuit platform in the back lane is
## walked with its lane-side guard probed. The editor-owned north Boardwalk
## extension is walked centre and both edges, both ways, with its outer
## guardrail pushed. S2's staff yard by the station, solid and gated since
## 2026-10-16 (Christina: "Make it solid and gate it"), is pushed at each of the
## five ways it was open, and B and C are walked beside it and across the holes
## filled inside B's loop. The rails on its other edges (the bluff crest, the B/C
## junction and C south of it) and S2's south gate are pushed, and the walks
## beside them walked. The four closed after them (NT-1's crest gap, the pit by
## the junction, B's north return through the bluff and S2's ledge) are pushed
## and walked too.
##
## Split out of the retired `walk_test.gd` on 2026-09-05, minus its strip-end
## probes, which named the pre-expansion boundary: the coast now tapers into
## planted ground past both ends of the promenade rather than stopping.

const ARRIVE := 1.6
const STALL_FRAMES := 90
const MAX_SECONDS := 22.0
const FALL_BELOW := 3.0

var _player: CharacterBody3D
var _legs: Array = []
var _leg := 0
var _from := Vector3.ZERO
var _to := Vector3.ZERO
var _t := 0.0
var _still := 0
var _min_y := 1e9
var _last := Vector3.ZERO
var _fails: Array = []


func _clear_crowds() -> void:
	for crowd in get_tree().get_nodes_in_group("crowd"):
		crowd.set_physics_process(false)
	for g in get_tree().get_nodes_in_group("guest"):
		g.queue_free()


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	for i in 4:
		await get_tree().physics_frame
	_player = get_tree().get_first_node_in_group("player") as CharacterBody3D
	if _player == null:
		print("FAIL: no player")
		get_tree().quit(1)
		return
	_clear_crowds()
	await get_tree().physics_frame
	_legs = _legs_list()
	print("--- boardwalk edges: %d legs ---" % _legs.size())
	_start_leg()


## Eye height is the shore plus the same 1.2 the plaza legs use.
func _legs_list() -> Array:
	var y := ParkPlan.SHORE_TOP + 1.2
	var alley_in := Vector3(ParkPlan.BACK_LANE_X, y, ParkPlan.ALLEY_Z)
	var alley_out := Vector3(ParkPlan.PROMENADE_X + 5.0, y, ParkPlan.ALLEY_Z)
	var prom := alley_out
	# The Grand Circuit stop is a side destination off the back lane. Until
	# boarding can open a gate, the platform must not be a pedestrian crossing
	# into a moving service.
	var tram_lane := Vector3(ParkPlan.BACK_LANE_X, y, 5.0)
	var tram_apron := Vector3(-76.85, y, 5.0)
	var tram_north := Vector3(-76.85, y, 11.0)
	var tram_south := Vector3(-76.85, y, 25.0)
	# Onto the pier is two legs, out of the alley then south along the promenade
	# to the mouth: a shallow diagonal is the waypoint trap.
	var pz := ParkPlan.PIER_ROOT.y
	var mouth := Vector3(ParkPlan.PROMENADE_X + 5.0, y, pz)
	# These points are the centre of the clear ring around the fixed pavilion.
	# They follow the directly editable markers in boardwalk_pier_head.tscn; the
	# test measures the emitted scene's approved route rather than the old apron.
	var head_front := Vector3(-150.5, y, pz)
	var head_n_e := Vector3(-150.5, y, -2.0)
	var head_n_w := Vector3(-166.0, y, -2.0)
	var head_s_w := Vector3(-166.0, y, 14.5)
	var head_s_e := Vector3(-150.5, y, 14.5)
	var legs := [
		["bw lane -> tram", alley_in, tram_lane, true],
		["bw tram apron", tram_lane, tram_apron, true],
		["bw tram platform in", tram_apron, tram_north, true],
		["bw tram platform length", tram_north, tram_south, true],
		["bw tram platform back", tram_south, tram_north, true],
		["bw tram platform out", tram_north, tram_apron, true],
		["bw tram -> lane", tram_apron, tram_lane, true],
		["bw tram lane guard holds", Vector3(-76.85, y, 18.0), Vector3(-70.0, y, 18.0), false],
		["bw tram -> alley", tram_lane, alley_in, true],
		["bw lane -> alley", alley_in, alley_out, true],
		["bw alley -> pier mouth", prom, mouth, true],
		["bw onto the pier", mouth, Vector3(-106, y, pz), true],
		["bw out the pier", Vector3(-106, y, pz), Vector3(-149, y, pz), true],
		["bw pavilion holds", Vector3(-149, y, pz), Vector3(-162, y, pz), false],
		["bw head enter front", Vector3(-147, y, pz), head_front, true],
		["bw head enter north", head_front, head_n_e, true],
		["bw head north out", head_n_e, head_n_w, true],
		["bw head outer south", head_n_w, head_s_w, true],
		["bw head south return", head_s_w, head_s_e, true],
		["bw head leave south", head_s_e, head_front, true],
		["bw head leave front", head_front, Vector3(-147, y, pz), true],
		["bw head enter front 2", Vector3(-147, y, pz), head_front, true],
		["bw head enter south", head_front, head_s_e, true],
		["bw head south out", head_s_e, head_s_w, true],
		["bw head outer north", head_s_w, head_n_w, true],
		["bw head north return", head_n_w, head_n_e, true],
		["bw head leave north", head_n_e, head_front, true],
		["bw head leave front 2", head_front, Vector3(-147, y, pz), true],
		["bw head north rail", Vector3(-159, y, -2.0), Vector3(-159, y, -7.0), false],
		["bw head outer rail", Vector3(-166, y, 6.5), Vector3(-172, y, 6.5), false],
		["bw head south rail", Vector3(-159, y, 14.5), Vector3(-159, y, 20.0), false],
		["bw head entry rail n", head_n_e, Vector3(-140, y, -2.0), false],
		["bw head entry rail s", head_s_e, Vector3(-140, y, 14.5), false],
		["bw back down pier", Vector3(-149, y, pz), Vector3(-102, y, pz), true],
		["bw mouth -> alley", mouth, prom, true],
		# The jetty: the promenade rail breaks across the wheel's platform, and
		# what stops the player there is the platform's own face, half a metre
		# proud. Start west of the lamp standards at `PROMENADE_X`, or the leg
		# stops on a lamp and passes for the wrong reason.
		["bw jetty holds", Vector3(-103, y, ParkPlan.WHEEL_AT.y),
			Vector3(-120, y, ParkPlan.WHEEL_AT.y), false],
		["bw jetty holds n", Vector3(-103, y, ParkPlan.WHEEL_FROM_Z + 1.0),
			Vector3(-120, y, ParkPlan.WHEEL_FROM_Z + 1.0), false],
		["bw jetty holds s", Vector3(-103, y, ParkPlan.WHEEL_TO_Z - 1.0),
			Vector3(-120, y, ParkPlan.WHEEL_TO_Z - 1.0), false],
		["bw water holds", Vector3(-98, y, 30.0), Vector3(-120, y, 30.0), false],
		["bw water holds n", Vector3(-98, y, -50.0), Vector3(-120, y, -50.0), false],
		["bw shops hold", Vector3(-96, y, 26.0), Vector3(-60.0, y, 26.0), false],
		["bw yard holds", Vector3(-98, y, 70.0), Vector3(-62.0, y, 70.0), false],
		["bw coaster fence holds", Vector3(-96, y, -60.0), Vector3(-60.0, y, -60.0), false],
		["bw bluff holds", Vector3(-70.0, y, 20.0), Vector3(-50.0, y, 20.0), false],
		["bw bluff holds n", Vector3(-70.0, y, -50.0), Vector3(-50.0, y, -50.0), false],
	]
	var north_extension := [
		Vector3(-99, y, -78), Vector3(-107, y, -92),
		Vector3(-108, y, -112), Vector3(-108, y, -136),
		Vector3(-106, y, -158), Vector3(-102, y, -176),
		Vector3(-98, y, -188), Vector3(-96, y, -198),
		Vector3(-92, y, -205), Vector3(-80, y, -205),
	]
	for i in north_extension.size() - 1:
		var a: Vector3 = north_extension[i]
		var b: Vector3 = north_extension[i + 1]
		var direction := Vector3(b.x - a.x, 0.0, b.z - a.z).normalized()
		var side := Vector3(-direction.z, 0.0, direction.x) * 3.1
		for lane in [["c", Vector3.ZERO], ["l", side], ["r", -side]]:
			var suffix: String = lane[0]
			var offset: Vector3 = lane[1]
			# Segment-edge probes stop one metre short of the mitered corner. The
			# corner itself belongs to both legs and carries the outer rail post;
			# aiming a straight offset at that post tests the waypoint, not the lane.
			var edge_a := a + direction * 1.0 + offset
			var edge_b := b - direction * 1.0 + offset
			legs.append(["bw north %02d%s out" % [i, suffix], edge_a, edge_b, true])
			legs.append(["bw north %02d%s back" % [i, suffix], edge_b, edge_a, true])
	legs.append_array([
		["bw north west rail", Vector3(-104, y, -118), Vector3(-116, y, -118), false],
		["bw north arc rail", Vector3(-97, y, -193), Vector3(-109, y, -195.4), false],
	])
	legs.append_array(_yard_legs(y))
	legs.append_array(_yard_rail_legs())
	legs.append_array(_holes_legs())
	legs.append_array(_r4_rail_legs())
	return legs


## R4's queue railed where its bed stands over the B/C junction (Christina,
## 2026-10-17: "Rail it, this batch"): pushed square from the queue's centre
## toward the floor on each of its railed legs, which must hold; the queue walked
## up and down its centre and along its railed side, 0.7 m off its centre; and
## the floor walked along the rail both ways.
func _r4_rail_legs() -> Array:
	var on := func(label: String, a: Vector2, b: Vector2, arrive: bool) -> Array:
		var from := _stand(a.x, a.y)
		return [label, from, _stand(b.x, b.y) if arrive else Vector3(b.x, from.y, b.y), arrive]
	return [
		on.call("bw R4 rail 0", Vector2(-67.20, 94.47), Vector2(-70.26, 98.42), false),
		on.call("bw R4 rail 1", Vector2(-67.50, 97.72), Vector2(-71.70, 95.01), false),
		on.call("bw R4 rail 2", Vector2(-67.50, 101.60), Vector2(-71.09, 105.08), false),
		on.call("bw R4 rail 3", Vector2(-67.00, 104.70), Vector2(-71.20, 101.99), false),
		on.call("bw R4 rail 4", Vector2(-66.40, 107.49), Vector2(-69.46, 111.44), false),
		on.call("bw R4 rail 4 north", Vector2(-65.00, 108.57), Vector2(-68.06, 112.53), false),
		on.call("bw R4 queue up 1", Vector2(-66.0, 95.4), Vector2(-69.0, 100.05), true),
		on.call("bw R4 queue up 2", Vector2(-69.0, 100.05), Vector2(-66.0, 103.15), true),
		on.call("bw R4 queue up 3", Vector2(-66.0, 103.15), Vector2(-68.0, 106.25), true),
		on.call("bw R4 queue up 4", Vector2(-68.0, 106.25), Vector2(-64.0, 109.35), true),
		on.call("bw R4 queue down 4", Vector2(-64.0, 109.35), Vector2(-68.0, 106.25), true),
		on.call("bw R4 queue down 1", Vector2(-69.0, 100.05), Vector2(-66.0, 95.4), true),
		on.call("bw R4 queue side 1", Vector2(-66.59, 95.02), Vector2(-69.59, 99.67), true),
		on.call("bw R4 queue side 2", Vector2(-69.50, 100.54), Vector2(-66.50, 103.64), true),
		on.call("bw R4 queue side 3", Vector2(-66.59, 102.77), Vector2(-68.59, 105.87), true),
		on.call("bw R4 queue side 4", Vector2(-68.43, 106.80), Vector2(-64.43, 109.90), true),
		on.call("bw R4 queue side 4 down", Vector2(-64.43, 109.90), Vector2(-68.43, 106.80), true),
		on.call("bw R4 queue side 1 down", Vector2(-69.59, 99.67), Vector2(-66.59, 95.02), true),
		on.call("bw R4 rail floor north", Vector2(-72.2, 98.8), Vector2(-72.2, 108.2), true),
		on.call("bw R4 rail floor south", Vector2(-72.2, 108.2), Vector2(-72.2, 98.8), true),
	]


## A point on the top surface under (x, z), at the legs' eye height over it.
func _stand(x: float, z: float) -> Vector3:
	var space := get_tree().root.get_world_3d().direct_space_state
	var hit := space.intersect_ray(PhysicsRayQueryParameters3D.create(
		Vector3(x, 60.0, z), Vector3(x, -40.0, z)))
	var top: float = ParkPlan.SHORE_TOP if hit.is_empty() else float(hit["position"].y)
	return Vector3(x, top + 1.2, z)


## S2's staff yard (2026-10-16), the shore floor between the garden fence, the
## bluff face, B's south return and C's west lobe: each way it was open is
## pushed and must hold, a leg into the yard ending in it if it does not. Legs on
## a route start on its surface and keep that level, so a drop into the yard
## counts as a fall. Then the routes beside it are walked, and the holes filled
## inside B's loop crossed.
func _yard_legs(y: float) -> Array:
	var floor_at := func(x: float, z: float) -> Vector3: return Vector3(x, y, z)
	var on := func(label: String, a: Vector2, b: Vector2, arrive: bool) -> Array:
		var from := _stand(a.x, a.y)
		return [label, from, _stand(b.x, b.y) if arrive else Vector3(b.x, from.y, b.y), arrive]
	# S2's gate stands between its posts where S2 leaves C: pushed square at
	# it from C, at a quarter, the middle and three quarters of its span.
	var gate: Dictionary = ParkPlan.coastal_creek_placements()["yard"]["S2_gate"]
	var pa := ParkPlan.rebuild_expand_point(gate["posts"][0])
	var pb := ParkPlan.rebuild_expand_point(gate["posts"][1])
	var square := Vector2(-(pb - pa).y, (pb - pa).x).normalized()
	if square.dot(Vector2(-75.0, 98.0) - pa) < 0.0:
		square = -square
	var legs := [
		# The north fence and its staff gate, from the back lane and from the yard.
		["bw yard gate holds", floor_at.call(-62.3, 42.0), floor_at.call(-62.3, 60.0), false],
		["bw yard fence holds by drop", floor_at.call(-65.5, 42.0), floor_at.call(-65.5, 60.0), false],
		["bw yard fence holds by bluff", floor_at.call(-59.2, 42.0), floor_at.call(-59.2, 60.0), false],
		["bw yard gate holds out", floor_at.call(-62.3, 58.0), floor_at.call(-62.3, 40.0), false],
		["bw yard fence holds out", floor_at.call(-59.2, 58.0), floor_at.call(-59.2, 40.0), false],
		# Off B's east edge, its guard.
		on.call("bw yard B guard z72", Vector2(-86.5, 72.0), Vector2(-72.0, 72.0), false),
		on.call("bw yard B guard z78", Vector2(-84.5, 78.0), Vector2(-70.0, 78.0), false),
		on.call("bw yard B guard z82", Vector2(-82.4, 82.0), Vector2(-71.6, 76.8), false),
		# Off C's west lobe, its rail.
		on.call("bw yard C rail x-62", Vector2(-62.0, 80.6), Vector2(-62.0, 70.0), false),
		on.call("bw yard C rail NW", Vector2(-69.0, 85.5), Vector2(-77.0, 77.5), false),
		on.call("bw yard C rail W", Vector2(-72.0, 89.2), Vector2(-80.0, 83.5), false),
		# Round the garden fence's end, both ways, and under B, C and S2 through
		# their banks.
		["bw yard fence end holds", floor_at.call(-77.0, 79.0), floor_at.call(-82.0, 71.0), false],
		["bw yard fence end holds in", floor_at.call(-79.0, 71.0), floor_at.call(-76.0, 80.0), false],
		["bw yard B bank holds", floor_at.call(-90.5, 80.0), floor_at.call(-72.0, 80.0), false],
		["bw yard C bank holds", floor_at.call(-62.0, 70.0), floor_at.call(-62.0, 92.0), false],
		["bw yard S2 bank holds", floor_at.call(-65.0, 66.0), floor_at.call(-68.5, 86.0), false],
	]
	for k in 3:
		var at := pa.lerp(pb, 0.25 + 0.25 * float(k))
		legs.append(on.call("bw yard S2 gate holds %d" % k, at + square * 3.0, at - square * 6.0, false))
	legs.append_array([
		# B and C beside the yard, and B and C at their junction.
		on.call("bw yard B walks", Vector2(-92.6, 67.0), Vector2(-82.0, 83.0), true),
		on.call("bw yard B walks on", Vector2(-82.0, 83.0), Vector2(-80.0, 101.6), true),
		on.call("bw yard C walks", Vector2(-58.0, 79.9), Vector2(-69.0, 85.5), true),
		on.call("bw yard C walks on", Vector2(-69.0, 85.5), Vector2(-76.4, 98.9), true),
		on.call("bw yard C walks its rail", Vector2(-58.5, 77.0), Vector2(-67.5, 80.0), true),
		on.call("bw yard C crosses S2", Vector2(-65.5, 80.5), Vector2(-73.0, 87.0), true),
		# C's west edge over B, north of where C comes down to the junction's surface,
		# is railed (2026-10-17, Christina: "Rail it, rebuild flush"): pushed both ways.
		on.call("bw C rail over B z92", Vector2(-73.5, 92.0), Vector2(-84.0, 92.0), false),
		on.call("bw C rail over B z94", Vector2(-73.5, 94.0), Vector2(-84.0, 94.0), false),
		on.call("bw C rail over B z96", Vector2(-73.5, 96.0), Vector2(-84.0, 96.0), false),
		on.call("bw B to C rail z94", Vector2(-84.0, 94.0), Vector2(-73.5, 94.0), false),
		on.call("bw B to C rail z96", Vector2(-84.0, 96.0), Vector2(-73.5, 96.0), false),
		on.call("bw yard B to C", Vector2(-84.0, 100.0), Vector2(-72.0, 100.0), true),
		# Where C has come down onto it the junction is one surface: crossed both
		# ways, and walked along C onto it and back at its centre and both sides.
		on.call("bw junction B to C z98.5", Vector2(-84.0, 98.5), Vector2(-72.5, 98.5), true),
		on.call("bw junction C to B z98.5", Vector2(-72.5, 98.5), Vector2(-84.0, 98.5), true),
		on.call("bw junction C to B z100", Vector2(-72.0, 100.0), Vector2(-84.0, 100.0), true),
		on.call("bw junction B to C z104", Vector2(-84.0, 104.0), Vector2(-71.0, 104.0), true),
		on.call("bw junction C to B z104", Vector2(-71.0, 104.0), Vector2(-84.0, 104.0), true),
		on.call("bw junction C onto floor", Vector2(-74.4, 93.6), Vector2(-77.9, 108.8), true),
		on.call("bw junction floor onto C", Vector2(-77.9, 108.8), Vector2(-74.4, 93.6), true),
		on.call("bw junction C east onto floor", Vector2(-71.5, 94.3), Vector2(-75.0, 109.5), true),
		on.call("bw junction floor onto C east", Vector2(-75.0, 109.5), Vector2(-71.5, 94.3), true),
		on.call("bw junction C west onto floor", Vector2(-77.3, 92.9), Vector2(-80.8, 108.1), true),
		on.call("bw junction floor onto C west", Vector2(-80.8, 108.1), Vector2(-77.3, 92.9), true),
		on.call("bw yard garden stem", Vector2(-88.5, 64.1), Vector2(-80.8, 63.7), true),
		# The holes filled inside B's loop, walked off the paving beside each and
		# over it to the land, or down from the land to the paving.
		on.call("bw loop hole -61,104", Vector2(-61.0, 106.5), Vector2(-61.0, 100.0), true),
		# From the land beside R4's queue bed: the bed's own side is railed since
		# 2026-10-17 (`_r4_rail_legs`).
		on.call("bw loop hole -68,110", Vector2(-66.5, 111.0), Vector2(-74.0, 110.0), true),
		on.call("bw loop hole -70.5,96", Vector2(-75.0, 96.5), Vector2(-69.5, 96.5), true),
		on.call("bw loop slot z90", Vector2(-70.0, 90.0), Vector2(-59.0, 90.0), true),
		on.call("bw loop slot z112", Vector2(-70.5, 112.0), Vector2(-60.0, 112.0), true),
		on.call("bw loop slot z116", Vector2(-67.6, 116.5), Vector2(-60.0, 116.5), true),
	])
	return legs


## The yard's other edges railed and S2's south arm gated (2026-10-16, Christina:
## "rail these four in one batch"). Each rail is pushed square along its length
## from the walk it guards and must hold: the bluff crest from the bluff top, the
## B/C junction's north end and west side from its floor, and C south of the
## junction from C. S2's south gate is pushed from the junction at a quarter, the
## middle and three quarters of its span, and from S2's south arm back toward the
## junction, square at it where S2's paving reaches it and up S2's east half to
## its far post. Then the walks the rails
## stand beside are walked: the bluff top along the crest and in from C, the
## junction's west strip, C south of the junction to the bluff, S2 inside the
## junction up to its south gate, and B under the Grand Circuit's overpass.
func _yard_rail_legs() -> Array:
	var on := func(label: String, a: Vector2, b: Vector2, arrive: bool) -> Array:
		var from := _stand(a.x, a.y)
		return [label, from, _stand(b.x, b.y) if arrive else Vector3(b.x, from.y, b.y), arrive]
	var legs := []
	for z in [12.5, 16.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0,
			74.0, 75.3]:
		legs.append(on.call("bw crest rail z%s" % str(z), Vector2(-55.0, z), Vector2(-63.0, z), false))
	legs.append_array([
		on.call("bw rail BC north end", Vector2(-86.8, 100.2), Vector2(-86.7, 92.7), false),
		on.call("bw rail BC north corner", Vector2(-87.8, 100.5), Vector2(-87.8, 92.7), false),
		on.call("bw rail BC z99", Vector2(-85.9, 99.0), Vector2(-93.4, 99.0), false),
		on.call("bw rail BC z103", Vector2(-85.9, 103.0), Vector2(-93.4, 103.0), false),
		on.call("bw rail BC z106", Vector2(-85.9, 105.3), Vector2(-93.4, 106.1), false),
		on.call("bw rail BC z110", Vector2(-85.5, 109.3), Vector2(-92.9, 110.1), false),
		on.call("bw rail BC z112", Vector2(-85.2, 111.9), Vector2(-92.5, 113.3), false),
		on.call("bw rail BC z116", Vector2(-84.4, 115.8), Vector2(-91.7, 117.3), false),
		on.call("bw rail BC z120", Vector2(-83.6, 119.7), Vector2(-91.0, 121.2), false),
		on.call("bw rail BC z124", Vector2(-82.1, 123.3), Vector2(-88.9, 126.3), false),
		on.call("bw rail BC z128", Vector2(-80.4, 126.9), Vector2(-87.3, 130.0), false),
		on.call("bw rail BC z132", Vector2(-78.3, 130.2), Vector2(-84.6, 134.2), false),
		on.call("bw rail C south -74,141", Vector2(-71.3, 139.3), Vector2(-77.5, 144.3), false),
		on.call("bw rail C south -72,144", Vector2(-69.4, 141.7), Vector2(-75.6, 146.7), false),
		on.call("bw rail C south -69,146", Vector2(-67.4, 144.2), Vector2(-72.5, 150.3), false),
		on.call("bw rail C south -66,149", Vector2(-64.3, 146.7), Vector2(-69.4, 152.9), false),
		on.call("bw rail C south -64,151", Vector2(-62.7, 148.1), Vector2(-66.6, 155.1), false),
		on.call("bw rail C south -61,153", Vector2(-59.2, 150.0), Vector2(-63.0, 157.0), false),
		on.call("bw rail C south -59,154", Vector2(-57.7, 150.9), Vector2(-59.9, 158.6), false),
	])
	# S2's south gate, square at it from the junction (inside, toward the floor's
	# middle) and along S2 from its south arm.
	var gate: Dictionary = ParkPlan.coastal_creek_placements()["yard"]["S2_south_gate"]
	var pa := ParkPlan.rebuild_expand_point(gate["posts"][0])
	var pb := ParkPlan.rebuild_expand_point(gate["posts"][1])
	var square := Vector2(-(pb - pa).y, (pb - pa).x).normalized()
	if square.dot(Vector2(-70.0, 125.0) - pa) < 0.0:
		square = -square
	for k in 3:
		var at := pa.lerp(pb, 0.25 + 0.25 * float(k))
		legs.append(on.call("bw S2 south gate holds %d" % k, at + square * 3.0, at - square * 6.0, false))
	# From S2's south arm the gate stands askew across the paving, so each push
	# starts on S2 just outside it, at the part of the span S2's paving reaches.
	for spec in [[0.4, 1.0], [0.5, 1.2], [0.75, 2.0]]:
		var at := pa.lerp(pb, float(spec[0]))
		legs.append(on.call("bw S2 south gate holds out %.2f" % float(spec[0]),
			at - square * float(spec[1]), at + square * 5.0, false))
	legs.append_array([
		on.call("bw S2 south gate out e", Vector2(-75.9, 141.2), Vector2(-75.3, 136.5), false),
		# The walks beside the rails.
		on.call("bw crest walks", Vector2(-56.0, 14.0), Vector2(-56.0, 72.0), true),
		on.call("bw crest walks back", Vector2(-56.0, 72.0), Vector2(-56.0, 14.0), true),
		on.call("bw crest from C", Vector2(-55.0, 82.0), Vector2(-56.0, 60.0), true),
		on.call("bw BC strip walks", Vector2(-86.5, 101.0), Vector2(-84.8, 117.0), true),
		on.call("bw C south walks", Vector2(-71.0, 135.5), Vector2(-63.5, 147.5), true),
		on.call("bw C south walks on", Vector2(-63.5, 147.5), Vector2(-54.0, 151.5), true),
		on.call("bw S2 to its south gate", Vector2(-74.8, 105.1), Vector2(-77.6, 129.0), true),
		on.call("bw B under overpass", Vector2(-60.3, -192.3), Vector2(-74.5, -201.5), true),
		on.call("bw B under overpass back", Vector2(-74.5, -201.5), Vector2(-60.3, -192.3), true),
	])
	return legs


## The four closed on 2026-10-16 (Christina: "do these four in one batch"):
## - NT-1's crest, where the crest rail now runs on inside the monument's zone
##   line to the end of its south bank, pushed west between the two;
## - the pit between C, the junction floor's south end, B's south return and
##   the bluff, filled (grid edit G26), crossed from C and from the junction;
## - B's north return where it leaves the headland through the bluff, walked
##   centre and both edges both ways and pushed square at both sides, its trench
##   walls pushed from the paving, and the cut's rim walked along the line where
##   a slot between the grid's edge and the wall dropped out of the world;
## - S2's ledge, pushed from S2's south arm along the rail's outside at the
##   gate's first post, where a guest slid round it onto the junction's shoulder.
func _holes_legs() -> Array:
	var on := func(label: String, a: Vector2, b: Vector2, arrive: bool) -> Array:
		var from := _stand(a.x, a.y)
		return [label, from, _stand(b.x, b.y) if arrive else Vector3(b.x, from.y, b.y), arrive]
	var legs := []
	for z in [10.65, 10.9, 11.2, 11.5, 11.8]:
		legs.append(on.call("bw NT-1 crest z%s" % str(z), Vector2(-55.0, z), Vector2(-63.0, z), false))
	legs.append_array([
		on.call("bw pit from C", Vector2(-66.5, 143.0), Vector2(-57.0, 136.0), true),
		on.call("bw pit from C on", Vector2(-62.5, 146.5), Vector2(-60.5, 137.5), true),
		on.call("bw pit from J", Vector2(-68.5, 134.5), Vector2(-58.5, 137.0), true),
		on.call("bw pit to C", Vector2(-59.0, 134.0), Vector2(-66.0, 142.0), true),
	])
	# B's north return: the leg that crosses the bluff face, centre and 3.1 m either
	# side (0.9 m inside the paving's edge), stopping a metre short of each end.
	var b_points: Array = []
	for run in ParkPlan.rebuild_build_runs():
		if StringName(run["id"]) == &"b_north_return":
			b_points = run["points"]
	for i in b_points.size() - 1:
		var a3 := Vector3(b_points[i])
		var b3 := Vector3(b_points[i + 1])
		if (a3.x > ParkPlan.BLUFF_FACE_X) == (b3.x > ParkPlan.BLUFF_FACE_X):
			continue
		# B is at its own level here, under the headland's ground where it leaves it:
		# the legs start on the paving, not on the top surface.
		var at := func(p: Vector2) -> Vector3:
			var t := clampf((p - Vector2(a3.x, a3.z)).dot(Vector2(b3.x - a3.x, b3.z - a3.z))
				/ Vector2(b3.x - a3.x, b3.z - a3.z).length_squared(), 0.0, 1.0)
			return Vector3(p.x, lerpf(a3.y, b3.y, t) + 1.2, p.y)
		var a := Vector2(a3.x, a3.z)
		var b := Vector2(b3.x, b3.z)
		var d := (b - a).normalized()
		var side := Vector2(-d.y, d.x)
		for lane in [["c", 0.0], ["l", 3.1], ["r", -3.1]]:
			var p0: Vector2 = a + d + side * float(lane[1])
			var p1: Vector2 = b - d + side * float(lane[1])
			legs.append(["bw B bluff %s out" % lane[0], at.call(p0), at.call(p1), true])
			legs.append(["bw B bluff %s back" % lane[0], at.call(p1), at.call(p0), true])
		# Square at both sides east of the face, where the cut's walls stand.
		for k in 5:
			var m := a.lerp(b, 0.1 + 0.15 * float(k))
			var from: Vector3 = at.call(m)
			var l := m + side * 8.0
			var r := m - side * 8.0
			legs.append(["bw B bluff push l%d" % k, from, Vector3(l.x, from.y, l.y), false])
			legs.append(["bw B bluff push r%d" % k, from, Vector3(r.x, from.y, r.y), false])
		break
	# Its trench, pushed square at both walls from the paving, and walked along both
	# rims where the slots were, both ways.
	for z in [-105.0, -115.0, -125.0, -135.0, -145.0]:
		var c := _stand(-44.0, z)
		legs.append(["bw B trench w z%d" % int(z), c, Vector3(-56.0, c.y, z), false])
		legs.append(["bw B trench e z%d" % int(z), c, Vector3(-32.0, c.y, z), false])
	legs.append_array([
		on.call("bw B rim w", Vector2(-49.5, -104.0), Vector2(-49.5, -136.0), true),
		on.call("bw B rim w back", Vector2(-49.5, -136.0), Vector2(-49.5, -104.0), true),
		on.call("bw B rim e", Vector2(-38.5, -104.0), Vector2(-38.5, -136.0), true),
		on.call("bw B rim e back", Vector2(-38.5, -136.0), Vector2(-38.5, -104.0), true),
	])
	# S2's ledge: from S2's south arm along the outside of the junction's north run
	# at the gate's first post, on S2's shoulder and from its paving.
	var gate: Dictionary = ParkPlan.coastal_creek_placements()["yard"]["S2_south_gate"]
	var pa := ParkPlan.rebuild_expand_point(gate["posts"][0])
	var pb := ParkPlan.rebuild_expand_point(gate["posts"][1])
	var run := (pb - pa).normalized()
	var out := Vector2(-run.y, run.x)
	if out.dot(Vector2(-70.0, 125.0) - pa) > 0.0:
		out = -out
	# Along the rail's outside, parallel to the gate, from S2's paving to 6 m past the
	# post. Offsets start at 0.35 m: a body's centre cannot stand nearer the gate's leaf
	# than its 0.35 m radius, and a leg started nearer (0.20 m, dropped 1.2 m from the
	# start's height as every leg is) landed on the leaf's top rail and walked the rails'
	# tops onto the shoulder, a path no guest can take with no step-up.
	for off in [0.35, 0.55]:
		legs.append(on.call("bw S2 ledge at post a %.2f" % off, pa + run * 1.2 + out * off,
			pa - run * 6.0 + out * off, false))
	# From S2's paving 0.6 m outside the gate's line, slanting past the post to the
	# shoulder's middle beyond it: on S2's paving until the post, so it asks whether the
	# shoulder can be reached. Started on S2's west shoulder instead (1.2 m out), it
	# slid along the return and stepped off the shoulder's outer edge, S2's own
	# unguarded west edge, which a guest can walk off anywhere along S2's south arm;
	# that edge is not this leg's question (2026-10-17, reported, not railed).
	legs.append(on.call("bw S2 ledge in from S2", pa + run * 1.0 + out * 0.6,
		pa - run * 6.0 + out * 0.19, false))
	return legs


func _start_leg() -> void:
	if _leg >= _legs.size():
		_report()
		return
	var leg: Array = _legs[_leg]
	_from = leg[1]
	_to = leg[2]
	_player.global_position = _from
	_player.velocity = Vector3.ZERO
	var d := _to - _from
	_player.rotation.y = atan2(-d.x, -d.z)
	_t = 0.0
	_still = 0
	_min_y = _from.y
	_last = _from
	Input.action_press("move_forward")


func _physics_process(delta: float) -> void:
	if _player == null or _leg >= _legs.size():
		return
	_t += delta
	var p := _player.global_position
	_min_y = minf(_min_y, p.y)
	if p.distance_to(_last) < 0.004:
		_still += 1
	else:
		_still = 0
	_last = p
	var flat_to := Vector3(_to.x, p.y, _to.z)
	var arrived := p.distance_to(flat_to) < ARRIVE
	var stalled := _still >= STALL_FRAMES
	var fell := p.y < minf(_from.y, _to.y) - FALL_BELOW
	if arrived or stalled or fell or _t > MAX_SECONDS:
		Input.action_release("move_forward")
		_finish_leg(arrived, stalled, fell, p)


func _blockers() -> String:
	var seen := {}
	for i in _player.get_slide_collision_count():
		var c := _player.get_slide_collision(i)
		var o := c.get_collider()
		if o != null:
			seen[String(o.name)] = true
	var names := seen.keys()
	names.sort()
	return ", ".join(names) if names.size() else "nothing"


func _finish_leg(arrived: bool, stalled: bool, fell: bool, at: Vector3) -> void:
	var leg: Array = _legs[_leg]
	var label: String = leg[0]
	var must_arrive: bool = leg[3]
	var verdict := "ok"
	if fell:
		verdict = "FELL"
	elif must_arrive and not arrived:
		verdict = "BLOCKED" if stalled else "TIMEOUT"
	elif not must_arrive and arrived:
		verdict = "LEAKED"
	if verdict != "ok":
		_fails.append("%s (%s)" % [label, verdict])
	print("%-26s %-8s  end=(%6.1f,%5.2f,%6.1f)  min_y=%5.2f  t=%4.1f  hit: %s" % [
		label, verdict, at.x, at.y, at.z, _min_y, _t, _blockers()])
	_leg += 1
	_start_leg()


func _report() -> void:
	print("---")
	if _fails.is_empty():
		print("PASS: the pier walks both ways and every boardwalk edge holds")
	else:
		print("FAIL: %d" % _fails.size())
		for f in _fails:
			print("  - %s" % f)
	get_tree().quit(1 if _fails.size() else 0)
