extends Control

## The quit subscreen, and the one place the game admits it cannot be saved.
##
## Saving is a slot with its reason on it rather than a working button or an
## absent one. There is no save system: the only thing that survives closing the
## game is the photographs, which `PhotoAlbum` writes to `user://photos` as they
## are taken and reloads at start. A real save would have to hold the hour, the
## standing section and eventually which guests are owed a claim ticket, and
## none of that is written yet.
##
## Leaving the row visible and disabled is the honest version. A player who
## quits out of a photography game wants to know whether they are about to lose
## an afternoon of pictures, and the answer — they are already on disk — is
## worth more than a tidy menu with one fewer row in it.

signal note_changed(note: String)

var _list: MenuList
var _confirming := false


func _ready() -> void:
	# Carded and centred, same as options. The confirm swaps four rows for two and
	# the card shrinks around them, which is the right behaviour here — the screen
	# visibly becomes a question rather than growing two extra rows at the top.
	_list = MenuList.carded(self)

	_list.activated.connect(_on_activated)
	_list.note_changed.connect(func(note: String) -> void: note_changed.emit(note))
	_rebuild()


func _rebuild() -> void:
	if _confirming:
		_list.set_rows([
			{
				"id": &"confirm_no",
				"label": "No, keep playing",
				"kind": MenuList.Kind.ACTION,
				"note": "",
			},
			{
				"id": &"confirm_yes",
				"label": "Yes, quit",
				"kind": MenuList.Kind.ACTION,
				"note": "Photographs already taken are kept.",
			},
		])
		return

	_list.set_rows([
		{
			"id": &"save",
			"label": "Save",
			"kind": MenuList.Kind.DISABLED,
			"note": "No save yet. Photographs are written to disk as you take them.",
		},
		{
			"id": &"photos",
			"label": "Show photo folder",
			"kind": MenuList.Kind.ACTION,
			"note": PhotoAlbum.photo_directory(),
		},
		{
			"id": &"resume",
			"label": "Back to the park",
			"kind": MenuList.Kind.ACTION,
			"note": "",
		},
		{
			"id": &"quit",
			"label": "Quit",
			"kind": MenuList.Kind.ACTION,
			"note": "",
		},
	])


func _on_activated(id: StringName) -> void:
	match id:
		&"photos":
			# The album shows the pictures; this is for the files. A photography
			# game whose output the player cannot find on their own machine has
			# taken the pictures hostage.
			OS.shell_open(ProjectSettings.globalize_path(PhotoAlbum.photo_directory()))
		&"resume":
			_close()
		&"quit":
			_confirming = true
			_rebuild()
		&"confirm_no":
			_confirming = false
			_rebuild()
		&"confirm_yes":
			# Not `get_tree().quit()` from a paused tree without unpausing: the
			# quit is processed on the next frame and a paused tree still gets
			# one, but leaving the pause set makes the shutdown order depend on
			# process modes, which is not a thing to be clever about.
			get_tree().paused = false
			get_tree().quit()


func _close() -> void:
	var menu := get_tree().get_first_node_in_group("park_menu")
	if menu != null and menu.has_method("close"):
		menu.call("close")


## Rebuilt on the way in, unconditionally, which options has always done and this
## screen did not. The menu clears the footer note as it opens a screen and then
## asks the screen to speak; a `_on_shown` that only acts when confirming never
## spoke, so the save row's reason — the one line on this screen that is actually
## load-bearing — was blank every time the tab was opened.
func _on_shown() -> void:
	_rebuild()


## Backing out of the confirm when the screen is left, so that reopening the
## menu never lands on "Yes, quit" already selected.
func _on_hidden() -> void:
	if _confirming:
		_confirming = false
		_rebuild()
