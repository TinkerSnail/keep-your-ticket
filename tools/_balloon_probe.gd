extends Node

## Dev tool: is every balloon in the park standing over the person holding it?
##
## This exists because the answer was no, twice over and for two unrelated
## reasons, and neither showed up in anything the project already runs.
##
## The three *prop* balloons in `plaza_props.tscn` were separated from their own
## strings by 5.4m, 5.6m and 13.2m, because `_sphere` was the one generator
## primitive that did not go through `_place` and so ignored the plaza dilation
## while `_box` obeyed it. The five *carried* balloons were rigidly parented to
## `arm_r`, which swings 25 degrees each way and parks at a fixed 20 when its
## owner sits down, so a 1.6m string leaned by up to two thirds of a metre.
##
## Nothing catches either. `coplanar_test.py` has no opinion about shapes that
## have drifted apart, the walk test does not walk into balloons, and a still of
## a plaza with a balloon in the wrong half of it looks like a plaza with a
## balloon in it. Both were found by somebody looking at a screenshot and asking
## why the balloons had no strings — which is not a repeatable process, hence
## this.
##
## Run it at three clocks, because the seated fault only exists while somebody
## is sitting down, and at eleven in the morning almost nobody is.

## **Two questions, and only one of them is about verticality.**
##
## The first pass asked every balloon to hang within nine degrees of vertical,
## and it failed three things that were right and would have passed three that
## were wrong. Worth writing down, because the fix was to ask better rather than
## to widen the number:
##
##   - The balloon lying against a bollard came out at 65 degrees. Of course it
##     did — its string is *trailing on the ground*, which is the whole picture.
##     Verticality is only a meaningful question for a balloon that is floating.
##   - Walking guests came out at 11 to 14. Also right: `guest.gd` lets a tenth
##     of the arm's swing through on purpose and chases the rest, so a towed
##     balloon sways at the walk cadence. A balloon that stayed rigidly vertical
##     over a running child would be its own artefact.
##
## So: *every* balloon must be near its string, which is the question that
## catches metres of drift and does not care what the string is doing. Only a
## floating one is additionally asked to hang.
##
## The lean is split by whether the guest is **seated**, because the two
## failures are different in kind. A swing while walking is water off a duck; a
## *steady* lean is the bug, and seated is the only genuine steady state a guest
## has — the old pose held every balloon out at twenty degrees for as long as
## somebody stayed on the bench.
##
## Splitting on *speed* instead was tried first and flagged a guest who had
## simply come to a stop: the damping takes about a third of a second to settle,
## so "not moving this frame" and "at rest" are not the same question. Both of
## the states that carried the bug are still caught — seated at 20 degrees fails
## the tight limit, and an undamped walk at 25 fails the loose one.
const MAX_GAP := 1.2
const FLOATS_ABOVE := 1.0
const MAX_LEAN_SEATED_DEG := 6.0
const MAX_LEAN_LOOSE_DEG := 18.0

const CLOCKS := [11, 16, 19]
const SETTLE := 6.0

var _main: Node
var _fails: Array = []
var _checked := 0


func _ready() -> void:
	_main = load("res://scenes/main/main.tscn").instantiate()
	add_child(_main)
	_run()


func _run() -> void:
	ParkClock.running = false
	for hour in CLOCKS:
		ParkClock.set_clock(hour, 0)
		await get_tree().create_timer(SETTLE).timeout
		_check(hour)
	_report()


func _check(hour: int) -> void:
	for b in _find(_main, "balloon"):
		var s := _sibling_string(b)
		if s == null:
			_fails.append("%02d:00 %s has no string" % [hour, b.get_path()])
			continue
		_checked += 1
		# Both in world space, so this asks the question the eye asks and does
		# not care how either of them got there — which is the point, given that
		# the prop bug was a generator composing two positions two ways and the
		# carried one was a runtime transform inherited from an arm.
		var d: Vector3 = b.global_position - s.global_position
		var flat := Vector2(d.x, d.z).length()
		if d.length() > MAX_GAP:
			_fails.append("%02d:00 %s is %.2fm from its string"
				% [hour, _who(b), d.length()])
			continue
		if b.global_position.y < FLOATS_ABOVE:
			continue
		var seated := _is_seated(b)
		var limit := MAX_LEAN_SEATED_DEG if seated else MAX_LEAN_LOOSE_DEG
		var lean := rad_to_deg(atan2(flat, maxf(d.y, 0.001)))
		if lean > limit:
			_fails.append("%02d:00 %s leans %.1f deg %s (limit %.0f)"
				% [hour, _who(b), lean, "seated" if seated else "afoot", limit])


## The prop balloons are `balloon_N` / `balloon_N_string` siblings; the carried
## ones are `balloon` / `balloon_string` under the same knot or chair. Both
## resolve by looking for a sibling whose name starts with this one's.
func _sibling_string(b: Node3D) -> Node3D:
	var parent := b.get_parent()
	if parent == null:
		return null
	for c in parent.get_children():
		if c is Node3D and String(c.name).begins_with(String(b.name)) \
				and String(c.name).ends_with("_string"):
			return c as Node3D
	return null


## Whether the guest holding this is sitting down. A prop balloon has no guest
## over it at all and is tied to a bench that never moves, so it takes the tight
## limit too — which is right, and is what caught the 5.4m drift.
func _is_seated(n: Node) -> bool:
	var p: Node = n
	while p != null and not ("group_kind" in p):
		p = p.get_parent()
	if p == null:
		return true
	var v = p.get("_seated")
	return v != null and bool(v)


func _who(n: Node) -> String:
	var p: Node = n
	while p != null and not ("group_kind" in p):
		p = p.get_parent()
	return String(p.name) if p != null else String(n.get_parent().name)


func _find(root: Node, prefix: String) -> Array:
	var out: Array = []
	var stack: Array = [root]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		if n is Node3D and String(n.name).begins_with(prefix) \
				and not String(n.name).ends_with("_string") \
				and not String(n.name).ends_with("_knot"):
			out.append(n)
		for c in n.get_children():
			stack.append(c)
	return out


func _report() -> void:
	print("=== balloon probe ===")
	print("%d balloon/string pairs checked across %d clocks" % [_checked, CLOCKS.size()])
	for f in _fails:
		print("FAIL ", f)
	if _fails.is_empty():
		print("PASS every balloon stands over its string")
	else:
		print("FAIL %d" % _fails.size())
	get_tree().quit(0 if _fails.is_empty() else 1)
