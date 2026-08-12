class_name ParkUI
extends RefCounted

## The look of every flat interface in the game, in one place.
##
## The references are Donkey Kong Country, Pokémon Snap and Squaresoft's PS1
## menus, and between them they settle the argument the HUD prompts had already
## half-decided. What all three have in common is that a panel is an *object* —
## a plaque, a card, a pane of coloured glass — with a raised edge and a hard
## shadow under it. None of them is a flat rectangle with text on it. Flat is a
## much later look and it is the one thing that would date this wrongly.
##
## Pokémon Snap is the closest relative and worth naming: a first-person
## photography game whose album screen is the same screen this one needs. Bright
## saturated panels, big type, colour-coding per subscreen, nothing subtle.
## Squaresoft supplies the translucency — a menu you can still see the world
## through, which matters here because the world behind it is the park.
## Donkey Kong Country supplies the bevel and the gold.
##
## Everything is square. Rounded corners, gradients and soft shadows are all
## later conventions, and each of them is one setting away from making this look
## like a phone app wearing a pixel font. Hard edges, flat saturated fills,
## two-pixel borders, a black shadow with no blur in it.
##
## Nothing here is a widget library. It builds one `Theme` and hands out the
## palette; the menu draws itself.

## Two faces, not one, and the references are what settle it. Donkey Kong
## Country, Banjo-Kazooie and Hey Arnold are chunky, rounded and hand-drawn;
## RollerCoaster Tycoon and Squaresoft's menus are small crisp sans. Those are
## not the same font and were never meant to be — DKC's *logo* is chunky and
## DKC's *menu text* is plain, and every one of these games works that way.
## Trying to serve both briefs with one face gets a menu that is either shouty
## and unreadable or legible and characterless.
##
## So: display carries the character and appears on tabs, titles and the map's
## printed lettering. Body carries the reading and appears on rows, notes,
## captions and the HUD prompts. Anything long is body.
##
## The paths are deliberately generic. The face behind `display.ttf` has already
## changed once — Bungee first, Luckiest Guy now — and naming the constant after
## the font would have meant touching every reference to swap it. A missing file
## falls back to the engine's own face, so the game runs and looks plain rather
## than breaking.
const FONT_DISPLAY_PATH := "res://scenes/ui/fonts/display.ttf"
const FONT_BODY_PATH := "res://scenes/ui/fonts/body.ttf"

## Whether each face is pixel art, which decides how it is rendered — and this
## matters more than the file choice does. A bitmap face with antialiasing and
## subpixel positioning on is a *blurry* bitmap face, which reads as a modern UI
## in costume. But a smooth rounded display face with those turned off is just
## jagged. So the smoothing is a property of the face rather than a house rule,
## which is the mistake the first version of this file made by turning it off
## for everything.
const FONT_DISPLAY_PIXEL := false
const FONT_BODY_PIXEL := true

## Loaded faces, kept so that a redraw calling `body_font()` seven times does not
## build seven `FontVariation`s.
static var _faces := {}

## Body sizes are multiples of eight, and that is a hard constraint rather than
## a tidy habit: Silkscreen is drawn on an eight-pixel grid, so it is sharp at
## 16, 24 and 32 and mush at anything between. The old `SIZE_BODY := 20` was
## exactly the sort of value that looks harmless and renders blurry.
##
## `SIZE_TAB` is the exception because it is the only one used with the display
## face, which is an outline font and lands wherever it likes.
##
## It is 36 rather than 30 because a nominal size is not a rendered size and the
## two faces disagree about it badly. Luckiest Guy at 30 draws "ALBUM" 93px wide
## with a 22px ascent; Silkscreen at `SIZE_BODY` draws it 90px wide with a 25px
## ascent. The tab was the same width as the rows underneath it and shorter, so
## the heading was reading as body text. 36 puts it at 111px and an ascent of 26,
## which is the first size that reads as a heading at all.
const SIZE_SMALL := 16
const SIZE_BODY := 24
const SIZE_TAB := 36
## 52 rather than 40 for the same reason, one step up. A title and a tab are both
## the display face, so a four-point gap between them is not a hierarchy — it is
## two headings that happen to differ. Nothing draws this yet; it is set now so
## the first screen that wants a title does not inherit the crowding.
const SIZE_TITLE := 52

## Ink and paper. The map is a printed object and stays paper — white-on-black
## is the one thing that has never been true of any park map ever handed out.
const INK := Color("14110c")
const PAPER := Color("f2e6c4")
const PAPER_LINE := Color("7a6a49")

## The chrome. A saturated blue plaque you can still see the park through, which
## is the Squaresoft half — their boxes are dark but they read as glass rather
## than as a hole in the screen, and the difference is entirely that you can
## make out what is behind them.
const PANEL := Color(0.106, 0.184, 0.451, 0.82)
const PANEL_HI := Color("7aa6e8")
const PANEL_LO := Color("0a1230")

## Gold. Donkey Kong Country's, and already the game's — this is the value the
## HUD prompts have been colouring key names with since they were written, so
## `hud.gd` reads it from here rather than keeping its own copy.
const ACCENT := Color("eec84a")
const TEXT := Color("fbf6e6")
const DIM := Color("8fa2c4")

## Selection is an inverted bar: a solid accent block with the label knocked out
## of it in ink. Glows and outlines are both later. This is what a menu looked
## like when a menu was drawn in tiles, and it survives being read at a glance
## from across a room, which a tinted outline does not.
const SELECT_FILL := ACCENT
const SELECT_TEXT := INK

## Per-subscreen colour, which is the Snap and DKC habit and does real work
## rather than being decoration: the tab you are on recolours its own panel
## edge, so the screen tells you where you are before you have read a word of
## it. Keyed by tab id.
const TAB_COLOURS := {
	&"map": Color("58b26a"),
	&"album": Color("4a90d9"),
	&"options": Color("9b6fd0"),
	&"quit": Color("d4604a"),
}

## The hard shadow under everything. No blur, no spread curve. This is the
## single detail that does the most period work and the easiest one to lose to a
## default.
const SHADOW_SIZE := 0
const SHADOW_OFFSET := Vector2i(3, 3)
const SHADOW_COLOUR := Color(0, 0, 0, 0.85)

## Text shadow, which is the same idea one layer down. Two pixels, black, hard.
const TEXT_SHADOW := Vector2i(2, 2)

## Border weight, everywhere. Two pixels at every size, because a border that
## scales with its box is a vector-era idea.
const BORDER := 2


## The theme. Built rather than stored as a `.tres` so that the palette above is
## the only definition of any of these values — a resource file would be a
## second copy that drifts, and the drawing code reads the constants anyway.
static func theme() -> Theme:
	var built := Theme.new()
	var face := font()

	built.default_font = face
	built.default_font_size = SIZE_BODY

	for type in ["Label", "RichTextLabel", "Button"]:
		built.set_font("font", type, face)
		built.set_font_size("font_size", type, SIZE_BODY)
		built.set_color("font_color", type, TEXT)
		built.set_color("font_shadow_color", type, SHADOW_COLOUR)
		built.set_constant("shadow_offset_x", type, TEXT_SHADOW.x)
		built.set_constant("shadow_offset_y", type, TEXT_SHADOW.y)
		# Zero explicitly: an outlined face over a hard shadow is two period
		# looks fighting, and the shadow is the right one.
		built.set_constant("outline_size", type, 0)

	built.set_stylebox("panel", "PanelContainer", plaque(PANEL, PANEL_HI))
	return built


## A raised plaque: saturated fill, a bright square border, and a hard black
## shadow thrown down and right. This is the DKC signboard reduced to the three
## properties that actually carry it.
##
## The bevel is one border colour rather than a true two-tone light/dark bevel,
## which would need a second nested box. A single bright edge over a black
## shadow reads as raised on its own, and it survives being tinted per subscreen
## — a two-tone bevel would need both of its tints recomputed for every tab.
static func plaque(fill: Color, edge: Color) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = fill
	box.border_color = edge
	box.set_border_width_all(BORDER)
	box.set_corner_radius_all(0)
	box.shadow_size = SHADOW_SIZE
	box.shadow_offset = Vector2(SHADOW_OFFSET)
	box.shadow_color = SHADOW_COLOUR
	# Or the engine rounds off the two-pixel border it was just told to draw.
	box.anti_aliasing = false
	return box


## The same plaque with no shadow, for boxes sitting inside another one. A
## shadow inside a panel is a shadow cast on a surface that is already lit,
## which is the tell that a UI was assembled rather than drawn.
static func inset(fill: Color, edge: Color) -> StyleBoxFlat:
	var box := plaque(fill, edge)
	box.shadow_size = 0
	box.shadow_offset = Vector2.ZERO
	return box


## The reading face. Everything that is a sentence goes through here.
static func font() -> Font:
	return face(FONT_BODY_PATH, FONT_BODY_PIXEL)


## The face with the character in it: tabs, titles, the map's lettering.
static func display_font() -> Font:
	return face(FONT_DISPLAY_PATH, FONT_DISPLAY_PIXEL)


## Load a face and set its rendering to match what it is.
##
## `FontFile` carries these as runtime properties, so they apply whether or not
## the import settings were ever touched — which matters because swapping a face
## is meant to be dropping a file in, and whoever does it should not also have to
## know to set three import flags before it looks right.
static func face(path: String, pixel: bool) -> Font:
	if _faces.has(path):
		return _faces[path]

	var loaded: Font = null
	if ResourceLoader.exists(path):
		var file := load(path) as FontFile
		if file == null:
			push_warning("park_ui: %s is not a FontFile" % path)
		else:
			if pixel:
				file.antialiasing = TextServer.FONT_ANTIALIASING_NONE
				file.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
				file.hinting = TextServer.HINTING_NONE
				file.force_autohinter = false
			else:
				# A rounded display face wants the smoothing it was drawn with.
				file.antialiasing = TextServer.FONT_ANTIALIASING_GRAY
				file.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_AUTO
			loaded = file

	if loaded == null:
		# The engine's own face. A `FontVariation` is the only way to stand in
		# for a missing file without mutating the fallback for the whole
		# project, which would take the editor's own UI with it.
		var fallback := FontVariation.new()
		fallback.base_font = ThemeDB.fallback_font
		loaded = fallback

	_faces[path] = loaded
	return loaded


## The colour a subscreen owns. Unknown ids get the gold, so a tab added
## without a colour looks deliberate rather than looking broken.
static func tab_colour(id: StringName) -> Color:
	return TAB_COLOURS.get(id, ACCENT)


## Capitals, and the one place that decides so. Every label in the menu goes
## through here — a menu that is capitals except for the two strings somebody
## added last is worse than one that never tried.
static func caps(text: String) -> String:
	return text.to_upper()
