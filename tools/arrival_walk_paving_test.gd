extends Node

## Focused acceptance for the editor-owned arrival paving: one uninterrupted
## flat field whose actual brick bond forms waves over the original support.


func _ready() -> void:
	add_child(load("res://scenes/main/main.tscn").instantiate())
	_run.call_deferred()


func _run() -> void:
	for _i in 12:
		await get_tree().process_frame
	var entrance := get_tree().root.find_child("entrance", true, false) as Node3D
	var approach := get_tree().root.find_child("park_approach", true, false) as Node3D
	if entrance == null or approach == null:
		_fail("entrance or park approach is not mounted")
		return
	var legacy_path := entrance.get_node_or_null("parking_arrival_path") as GeometryInstance3D
	var legacy_extension := approach.get_node_or_null("arrival_walk_extension") as Node3D
	if legacy_path == null or legacy_path.visible:
		_fail("generated arrival asphalt is missing or still visible")
		return
	if legacy_extension == null or legacy_extension.visible:
		_fail("generated drop-off extension is missing or still visible")
		return
	if entrance.get_node_or_null("parking_arrival_bed") == null \
			or legacy_extension.get_child_count() < 2:
		_fail("original support or collision was removed")
		return
	var paving := entrance.get_node_or_null(
		"authored_additions/arrival_walk_paving") as Node3D
	if paving == null:
		_fail("editor-owned arrival paving is not mounted")
		return
	var field := paving.get_node_or_null("brick_field") as MeshInstance3D
	if field == null or not field.mesh is BoxMesh:
		_fail("brick field is missing")
		return
	var box := field.mesh as BoxMesh
	if not is_equal_approx(box.size.x, 13.4) or not is_equal_approx(box.size.z, 67.95):
		_fail("brick field no longer spans the continuous 13.4m arrival walk")
		return
	var material := box.material as ShaderMaterial
	if material == null or material.shader == null:
		_fail("brick field is not using the wavy-bond material")
		return
	var amplitude := float(material.get_shader_parameter("wave_amplitude_m"))
	var wavelength := float(material.get_shader_parameter("wave_length_m"))
	var courses_per_tint := float(material.get_shader_parameter("courses_per_tint"))
	var tint_strength := float(material.get_shader_parameter("tint_strength"))
	if amplitude < 0.65 or amplitude > 1.0 or wavelength < 4.5 or wavelength > 7.0:
		_fail("brick wave is no longer a tight cartoon-ocean sine")
		return
	if courses_per_tint < 3.0 or courses_per_tint > 5.0 \
			or tint_strength < 0.55 or tint_strength > 0.75:
		_fail("grouped brick-row tints are missing or too weak")
		return
	if paving.has_node("motif_courses") or paving.has_node("derived_motif"):
		_fail("the retired colored ribbon motif is still present")
		return
	for i in 7:
		var old_bar := entrance.get_node_or_null("parking_crosswalk_%02d" % i) \
				as GeometryInstance3D
		if old_bar == null or old_bar.visible:
			_fail("generated zebra bar %02d is missing or still visible" % i)
			return
	var crossing_table := paving.get_node_or_null("crossing_table") as MeshInstance3D
	if crossing_table == null or not crossing_table.mesh is BoxMesh:
		_fail("continuous brick crossing table is missing")
		return
	var table_box := crossing_table.mesh as BoxMesh
	if table_box.size.x < 13.39 or table_box.size.z < 5.59 \
			or crossing_table.position.y <= field.position.y + box.size.y * 0.5:
		_fail("brick crossing table does not cover the asphalt lane above the main field")
		return
	var south_edge := paving.get_node_or_null("tram_edge_south") as MeshInstance3D
	var north_edge := paving.get_node_or_null("tram_edge_north") as MeshInstance3D
	if south_edge == null or north_edge == null:
		_fail("quiet Grand Circuit lane-edge inlays are missing")
		return
	for edge in [south_edge, north_edge]:
		if not edge.mesh is BoxMesh:
			_fail("a Grand Circuit lane-edge inlay is not a flat box")
			return
		var edge_box := edge.mesh as BoxMesh
		if edge_box.size.y > 0.01 or edge_box.size.z > 0.25 \
				or edge_box.size.x < 13.4:
			_fail("a Grand Circuit lane-edge inlay is no longer a quiet flush band")
			return
	if absf((north_edge.position - south_edge.position).length() - 5.4) > 0.01:
		_fail("Grand Circuit lane-edge inlays no longer hold its 5.4m right-of-way")
		return
	print("PASS: the continuous wavy-brick promenade forms a raised table across the Grand Circuit, the generated zebra bars are retired, and two flush inlays hold the 5.4m vehicle lane")
	get_tree().quit()


func _fail(message: String) -> void:
	push_error("arrival_walk_paving_test: %s" % message)
	get_tree().quit(1)
