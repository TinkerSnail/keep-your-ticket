extends Node

## Dev probe: is every generated scene the same scene as a snapshot of it, by
## content rather than by text? Written on 2026-09-19 for the change that moved
## heavy meshes and shapes out of the `.tscn` into binary `.res`: the text
## filter in AGENTS.md cannot compare a sub_resource with an ext_resource, so
## this instantiates both and compares every node's class, stored properties
## and the full contents of every resource they hold, meshes and collision
## included. `GENERATED_SNAPSHOT=/absolute/dir` names the copies. Headless.

const SKIP := ["resource_path", "resource_name", "resource_local_to_scene",
	"resource_scene_unique_id", "script"]

var _memo := {}


func _ready() -> void:
	var snapshot := OS.get_environment("GENERATED_SNAPSHOT")
	var differing := 0
	for file in DirAccess.get_files_at("res://scenes/world/generated"):
		if not file.ends_with(".tscn") or not FileAccess.file_exists(snapshot.path_join(file)):
			continue
		var now := (ResourceLoader.load("res://scenes/world/generated/" + file, "",
			ResourceLoader.CACHE_MODE_IGNORE) as PackedScene).instantiate()
		var then := (ResourceLoader.load(snapshot.path_join(file), "",
			ResourceLoader.CACHE_MODE_IGNORE) as PackedScene).instantiate()
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
		if verdict != "same":
			differing += 1
		print("%-28s %6d nodes  %s" % [file, a.size(), verdict])
		now.free()
		then.free()
	print("PASS: every generated scene matches its snapshot by content" if differing == 0
		else "FAIL: %d scenes differ" % differing)
	get_tree().quit(0 if differing == 0 else 1)


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
			# name; anything the generator wrote is compared by what is in it.
			if resource.resource_path != "" and not resource.resource_path.contains("::") \
					and not resource.resource_path.contains("/generated/"):
				parts.append(resource.resource_path)
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
