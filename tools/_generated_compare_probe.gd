extends Node

## Dev probe: is every generated scene the same scene as a snapshot of it, by
## content rather than by text? Written on 2026-09-19 for the change that moved
## heavy meshes and shapes out of the `.tscn` into binary `.res`: the text
## filter in AGENTS.md cannot compare a sub_resource with an ext_resource, so
## this instantiates both and compares every node's class, stored properties
## and the full contents of every resource they hold, meshes and collision
## included. Headless.
##
## `GENERATED_SNAPSHOT=/absolute/dir` names the copies: a mirror of
## `scenes/world/generated/`, its `<scene>_data/` directories included. Fill it
## from HEAD before regenerating, outside the project:
##
##     git archive HEAD scenes/world/generated | tar -x -C /absolute/dir --strip-components 3
##
## Copying only the `.tscn` files is not enough. A scene names its `_data`
## files by `res://` path, so until 2026-10-08 the snapshot side loaded the
## working tree's binaries and a changed one read as "same": that day it hid
## 401 moved vertices in the road corridor while `git status` showed the file
## modified. Now each reference into `generated/` is pointed at the snapshot's
## own copy before the snapshot scene loads, a scene whose copy is missing is
## reported and not compared, and each `_data` file that differs is named under
## its scene.

const SKIP := ["resource_path", "resource_name", "resource_local_to_scene",
	"resource_scene_unique_id", "script"]
const GENERATED := "res://scenes/world/generated/"

var _memo := {}
## The snapshot directory as given and as Godot localizes it: its copies are
## generator output and are compared by content, like `generated/` itself.
var _roots: Array[String] = []
## A scene's reference into `generated/`, the whole line and the file relative
## to `generated/`.
var _ref := RegEx.create_from_string(
	'(?m)^\\[ext_resource [^\\n]*path="res://scenes/world/generated/([^"]+)"[^\\n]*$')
## A uid that resolves wins over the path, so a redirected line loses it.
var _uid := RegEx.create_from_string(' uid="[^"]*"')


func _ready() -> void:
	var snapshot := OS.get_environment("GENERATED_SNAPSHOT")
	if snapshot == "" or not DirAccess.dir_exists_absolute(snapshot):
		print("FAIL: GENERATED_SNAPSHOT names no directory; the header says how to fill one")
		get_tree().quit(1)
		return
	_roots = [snapshot, ProjectSettings.localize_path(snapshot)]
	# Per process, because user:// is shared by every session's runs.
	var scratch := "user://generated_compare_%d" % OS.get_process_id()
	DirAccess.make_dir_recursive_absolute(scratch)
	var compared := 0
	var differing := 0
	var unchecked := 0
	for file in DirAccess.get_files_at("res://scenes/world/generated"):
		if not file.ends_with(".tscn") or not FileAccess.file_exists(snapshot.path_join(file)):
			continue
		compared += 1
		var source := snapshot.path_join(file)
		var text := FileAccess.get_file_as_string(source)
		var data: Array[String] = []
		var missing: Array[String] = []
		for found: RegExMatch in _ref.search_all(text):
			var rel := found.get_string(1)
			data.append(rel)
			if not FileAccess.file_exists(snapshot.path_join(rel)):
				missing.append(rel)
			text = text.replace(found.get_string(), _uid.sub(
				found.get_string().replace(GENERATED + rel, snapshot.path_join(rel)), ""))
		if not missing.is_empty():
			unchecked += 1
			print("%-28s %12s  NOT COMPARED: the snapshot has no %s"
				% [file, "", ", ".join(missing)])
			continue
		if not data.is_empty():
			source = scratch.path_join(file)
			var out := FileAccess.open(source, FileAccess.WRITE)
			out.store_string(text)
			out.close()
		var now := (ResourceLoader.load(GENERATED + file, "",
			ResourceLoader.CACHE_MODE_IGNORE) as PackedScene).instantiate()
		var then := (ResourceLoader.load(source, "",
			ResourceLoader.CACHE_MODE_IGNORE) as PackedScene).instantiate()
		if source.begins_with(scratch):
			DirAccess.remove_absolute(source)
		var a := _dump(now)
		var b := _dump(then)
		var verdict := "same"
		if a.size() != b.size():
			verdict = "DIFFERENT: %d nodes against %d" % [a.size(), b.size()]
		else:
			for i in a.size():
				if a[i] != b[i]:
					verdict = "DIFFERENT at %s" % a[i][0]
					for k in mini(a[i].size(), b[i].size()):
						if a[i][k] != b[i][k]:
							verdict += "  %s" % str(a[i][k]).left(90)
							break
					break
		# The verdict names a node; name the file under it too.
		var files: Array[String] = []
		for found: RegExMatch in _ref.search_all(FileAccess.get_file_as_string(GENERATED + file)):
			if not (found.get_string(1) in data):
				data.append(found.get_string(1))
		for rel in data:
			if not FileAccess.file_exists(GENERATED + rel):
				files.append("    %s  only in the snapshot" % rel)
			elif not FileAccess.file_exists(snapshot.path_join(rel)):
				files.append("    %s  only in the working tree" % rel)
			elif _h(ResourceLoader.load(GENERATED + rel)) \
					!= _h(ResourceLoader.load(snapshot.path_join(rel))):
				files.append("    %s  DIFFERENT" % rel)
		if verdict == "same" and not files.is_empty():
			verdict = "DIFFERENT in its _data files"
		if verdict != "same":
			differing += 1
		print("%-28s %6d nodes  %s" % [file, a.size(), verdict])
		for line in files:
			print(line)
		now.free()
		then.free()
	DirAccess.remove_absolute(scratch)
	if compared == 0:
		print("FAIL: no generated scene has a copy in %s" % snapshot)
		get_tree().quit(1)
		return
	if differing + unchecked == 0:
		print("PASS: every generated scene matches its snapshot by content")
	else:
		print("FAIL: %d scenes differ, %d not compared" % [differing, unchecked])
	get_tree().quit(0 if differing + unchecked == 0 else 1)


func _dump(root: Node) -> Array:
	var rows: Array = []
	for n in [root] + root.find_children("*", "", true, false):
		var row: Array = [String(root.get_path_to(n)), n.get_class()]
		for p in n.get_property_list():
			if p.usage & PROPERTY_USAGE_STORAGE and not (p.name in SKIP):
				row.append([p.name, _h(n.get(p.name))])
		rows.append(row)
	return rows


func _h(value: Variant) -> int:
	match typeof(value):
		TYPE_OBJECT:
			var resource := value as Resource
			if resource == null:
				return 0 if value == null else 1
			var id := resource.get_instance_id()
			if _memo.has(id):
				return _memo[id]
			var parts: Array = [resource.get_class()]
			# A file that stands on its own outside `generated/` is compared by
			# name; anything the generator wrote, or the snapshot's copy of it,
			# is compared by what is in it.
			var path := resource.resource_path
			if path != "" and not path.contains("::") and not path.contains("/generated/") \
					and not _roots.any(func(root: String) -> bool: return path.begins_with(root)):
				parts.append(path)
			else:
				for p in resource.get_property_list():
					if p.usage & PROPERTY_USAGE_STORAGE and not (p.name in SKIP):
						parts.append([p.name, _h(resource.get(p.name))])
			_memo[id] = hash(parts)
			return _memo[id]
		TYPE_ARRAY:
			var items: Array = []
			for item in value:
				items.append(_h(item))
			return hash(items)
		TYPE_DICTIONARY:
			var pairs: Array = []
			for key in value:
				pairs.append([str(key), _h(value[key])])
			pairs.sort()
			return hash(pairs)
	return hash(value)
