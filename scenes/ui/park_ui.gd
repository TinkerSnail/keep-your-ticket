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

## What the display face has to be set to to look the same size as the body face
## set to something else.
##
## A nominal size is not a rendered size and these two faces disagree about it
## badly — the same measurement `SIZE_TAB` is built on. Luckiest Guy at 30 draws
## the same width as Silkscreen at 24 and sits three pixels shorter, so anything
## putting the two faces on one line has to scale one of them or the display face
## reads as the smaller of the pair, which is the opposite of what it is for.
const DISPLAY_RATIO := 1.25
## 52 rather than 40 for the same reason, one step up. A title and a tab are both
## the display face, so a four-point gap between them is not a hierarchy — it is
## two headings that happen to differ. Nothing draws this yet; it is set now so
## the first screen that wants a title does not inherit the crowding.
const SIZE_TITLE := 52

## Ink and paper. The map is a printed object and stays paper — white-on-black
## is the one thing that has never been true of any park map ever handed out.
##
## The ink is a warm near-black rather than a neutral one. Cartoon outlines are
## never grey and never blue-black; they are the colour of a brush loaded with
## black ink over warm paper, and a neutral #111 next to a saturated fill reads
## as a UI border instead of a drawn line.
const INK := Color("17100a")
const PAPER := Color("f7e7bd")
const PAPER_LINE := Color("8a7040")

## The chrome. A saturated blue plaque you can still see the park through, which
## is the Squaresoft half — their boxes are dark but they read as glass rather
## than as a hole in the screen, and the difference is entirely that you can
## make out what is behind them.
## It stays blue, and blue is the right canvas precisely because none of the
## three references is blue — Looney Tunes, DKC and Banjo-Kazooie are all warm,
## gold-forward and green. A warm panel under a gold accent is gold on gold, and
## the accent stops being an accent. The blue is what makes the gold read.
##
## But it is a far more saturated blue than it was. The old value was a cool
## desaturated navy, which is a Squaresoft colour rather than a cartoon one, and
## it made every tab tint sitting on it look muted by association.
const PANEL := Color(0.098, 0.161, 0.541, 0.84)
const PANEL_HI := Color("6fa8ff")
const PANEL_LO := Color("070d2e")

## Gold, and the one colour all three references share — DKC's banana, Banjo's
## jiggy, the WB shield. This is the value the HUD prompts have been colouring
## key names with since they were written, so `hud.gd` reads it from here rather
## than keeping its own copy.
##
## The old `eec84a` was a pale, slightly greyed gold that read as brass. A jiggy
## is not brass. This is hotter and fully saturated, which is what lets it carry
## the selection bar on its own without an outline.
const ACCENT := Color("ffc82e")
const TEXT := Color("fffaf0")
const DIM := Color("93a7d4")

## The frame around the body of the menu, and the one warm surface on the
## screen. It is a *material* rather than a colour — the thing the subscreen is
## mounted in, the way a DKC signboard or a Banjo plaque is a wooden object with
## something painted on it, and that is why it does not compete with `ACCENT`
## the way a warm panel fill would. A frame is not a fill.
##
## It is deliberately a darker, browner gold than `ACCENT`. Two golds on one
## screen only works if one of them is clearly the older, dimmer, more wooden of
## the pair; matched they just look like a mistake in one of them.
const FRAME := Color("b5822a")

## And the frame's own line, which is the same black the letters get. This is
## what stops the gold reading as a beige rectangle: the entire look is flat
## saturated fills with a hard dark line around them, and the largest shape on
## the screen is not an exception to that.
const FRAME_EDGE := INK

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
## Every one of these was a tint of its hue rather than the hue itself — a sage
## green, a dusty blue, a lilac, a brick. Cartoon colour is not tinted. Looney
## Tunes title cards and Banjo's worlds both work in colours at or near full
## chroma, and the darkness that keeps them from glaring comes from the black
## line around them, not from muting the fill.
const TAB_COLOURS := {
	&"map": Color("46b23d"),
	&"album": Color("2b8ee8"),
	&"options": Color("9b4fd6"),
	&"quit": Color("e33d28"),
}

## The unchosen tab. It lived in `park_menu.gd` as a private constant, which made
## it the one colour in the game defined outside this file — and it is not an
## incidental one, it is three quarters of what the tab strip looks like.
const TAB_IDLE := Color(0.075, 0.114, 0.271, 0.92)

## How far an unchosen tab's border is knocked back from its true hue. It was
## 0.45, which took every tint most of the way to black and left a strip of
## near-identical navy buttons — the per-subscreen colour was doing no work at
## all until the tab was already selected, which is the one moment you no longer
## need telling. At 0.22 the green, violet and red are legible cold.
const TAB_IDLE_FADE := 0.22

## The hard shadow under everything. No blur, no spread curve. This is the
## single detail that does the most period work and the easiest one to lose to a
## default.
const SHADOW_SIZE := 0
const SHADOW_OFFSET := Vector2i(3, 3)
const SHADOW_COLOUR := Color(0, 0, 0, 0.85)

## Text shadow, which is the same idea one layer down. Two pixels, black, hard.
const TEXT_SHADOW := Vector2i(2, 2)

## The black line around the display face, and the thing that actually makes the
## reference set look like itself.
##
## This file used to argue the opposite — that an outlined face over a hard
## shadow was two period looks fighting and the shadow was the right one. That
## was written when the display face was Bungee, which is signwriting and does
## carry itself unoutlined. It does not survive contact with the references it
## was claiming to serve: Donkey Kong Country, Banjo-Kazooie and Looney Tunes
## all use outline *and* drop shadow together, on the same letters, and the
## outline is the more definitional of the two. A cartoon letterform without a
## black line around it is a font; with one it is a drawing.
##
## Body keeps `outline_size` at zero. A pixel face at 16 or 24 has strokes only
## two or three pixels wide, and a six-pixel line around those closes the
## counters and turns a word into a blob.
##
## It is a ratio of the font size rather than a flat pixel count, which is the
## opposite of how `BORDER` works and for the opposite reason. A border belongs
## to a box, and a box has no natural size to be a fraction of. A line around a
## letter belongs to the letter, and letters do have one — a drawn `O` keeps the
## same ratio of line to counter whether it is on a poster or a badge, and a
## fixed six pixels would go spindly at `SIZE_TITLE` and gummy at anything small.
const OUTLINE_RATIO := 0.17
const OUTLINE_COLOUR := INK

## The fill inside that line: bright yellow at the cap line falling to red-orange
## at the baseline. Mario Kart's logo, Looney Tunes' cards, DKC's title — they
## are all this ramp, and it is why those letters read as hot metal rather than
## as coloured text.
##
## The stops are hard. A yellow-to-orange ramp is a subtle thing and looks like a
## rendering artefact; yellow all the way to a genuine red is the effect. The
## bottom is a red-orange rather than a red, because a true red against this gold
## turns muddy where they meet in the middle of the letter.
const DISPLAY_TOP := Color("ffe23f")
const DISPLAY_BOTTOM := Color("e2400f")

## Loaded once. Every display label shares the shader and owns its own material,
## because the ramp is common and the on/off is not.
const DISPLAY_SHADER_PATH := "res://scenes/ui/display_gradient.gdshader"
static var _display_shader: Shader = null

## What goes between two prompts. One copy, because a separator that differs
## between the HUD and the pause screen is a separator nobody chose twice.
const HINT_SEPARATOR := "   ·   "

## Border weight, everywhere. Two pixels at every size, because a border that
## scales with its box is a vector-era idea.
const BORDER := 2

## Except on the one box that is holding all the others. The body of the menu is
## the largest single shape on the screen and a two-pixel line around something
## that size does not read as an edge at all — it reads as the field simply
## stopping. Five is not that border scaled up; it is the difference between a
## sheet and a frame with something mounted in it.
const BORDER_FRAME := 5

## The cut corner, and the thing this file was missing.
##
## Star Fox 64 and Smash Bros are the reference for it and they are the same
## reference: a console menu of that generation does not draw a rectangle. It
## draws a plate with its corners taken off at 45°, which is a *hardware* look —
## a chamfer is four extra vertices and a rounded corner is a curve nobody was
## going to tessellate. That is why the shape says late nineties and why a
## rounded one says phone.
##
## It is emphatically not a rounded corner with fewer steps. The cut is a
## straight line, it is aliased on purpose, and it is large enough to read as a
## deliberate bevel rather than as the renderer having missed the corner.
##
## Three sizes, and they are proportional to what they are cutting. A 14px cut on
## a 40px row would eat the row; a 6px cut on a panel the size of the screen
## disappears.
const CUT := 16.0
const CUT_TAB := 10.0
const CUT_ROW := 7.0

## How much further out the selected thing sits than the ones around it.
##
## This is the other half of the same reference and the more important half.
## Melee's main menu does not mark the current item by recolouring it — the plate
## physically slides out of the stack and grows. Smash 64 does it, Star Fox's
## mission select does it, and every one of them survives a photograph of the
## screen at a size where you cannot read the words: the thing sticking out is
## the thing you are on.
##
## The old menu marked selection by colour alone, on both the tab strip and the
## rows. Colour is the weaker of the two signals and it is the one that fails
## first when a screen is busy.
const JUT := 28
const TAB_RISE := 14

## How the plate gets there.
##
## Instant was wrong and it was wrong in a specific way: a plate that is simply
## *drawn* further out is a plate that has been redrawn, and a plate that slides
## out is a plate that moved. The references all ease it over a handful of frames
## and the reason is not polish — it is that the movement is the signal, and a
## thing which is only ever seen in its start and end positions never moved.
##
## Short. This is a tab press and a cursor step, not a transition; anything past
## about a fifth of a second and the menu is answering slower than the key was
## pressed, which is the one thing a menu of this generation never did.
const MOVE_SECONDS := 0.15

## Arriving overshoots and settles; leaving just retreats.
##
## The asymmetry is the whole character of it. `TRANS_BACK` on the way out gives
## the plate a small carry past its mark and a settle back, which is what makes
## it read as having been thrown rather than moved — and on 28 pixels it is about
## three, so it is felt rather than seen. The same curve on the way *back* would
## dip the leaving plate below its resting width first, which reads as a flinch.
const ARRIVE_TRANS := Tween.TRANS_BACK
const LEAVE_TRANS := Tween.TRANS_CUBIC


## A plate with its corners cut off.
##
## `StyleBoxFlat` cannot do this. It has a corner radius and no chamfer, and the
## radius is the one setting in the engine that would take the whole menu
## straight to the wrong decade — so the shape has to be drawn.
##
## Drawn as three flat polygons rather than as a border stroke: the shadow, the
## fill, and a ring of triangles between the outer and inner outlines. A stroked
## polyline was the obvious version and it notches at every 45° corner, which is
## the one place this shape has to be clean. Filling the ring mitres for free.
##
## Nothing here is antialiased and that is not an oversight. A hard stair-stepped
## diagonal is what the reference looks like; a smoothed one reads as a vector
## shape at the wrong resolution.
class Plate extends StyleBox:
	var fill := Color.BLACK
	var edge := Color.WHITE
	var border := 2.0
	var cut := ParkUI.CUT
	var shadow_offset := Vector2.ZERO
	var shadow_colour := Color(0, 0, 0, 0)

	## Which corners are cut, clockwise from top-left. A tab that runs into the
	## panel below it keeps its bottom corners square, so the two shapes meet as
	## one object rather than as a plate resting on a box.
	var corners := [true, true, true, true]

	## Content clears the border and nothing else. The chamfer is not counted,
	## because everything in this menu is centred or padded well inside it, and
	## charging every plate a corner's worth of margin on all four sides would
	## quietly shrink every screen.
	func _get_style_margin(_side: Side) -> float:
		return border

	func _get_draw_rect(rect: Rect2) -> Rect2:
		return rect.grow_individual(
			maxf(-shadow_offset.x, 0.0), maxf(-shadow_offset.y, 0.0),
			maxf(shadow_offset.x, 0.0), maxf(shadow_offset.y, 0.0))

	func _draw(to_canvas_item: RID, rect: Rect2) -> void:
		if rect.size.x <= 0.0 or rect.size.y <= 0.0:
			return

		var outer := _outline(rect, cut)

		if shadow_colour.a > 0.0 and shadow_offset != Vector2.ZERO:
			var cast := PackedVector2Array()
			for point in outer:
				cast.append(point + shadow_offset)
			RenderingServer.canvas_item_add_polygon(
				to_canvas_item, cast, PackedColorArray([shadow_colour]))

		var thickness := minf(border, minf(rect.size.x, rect.size.y) * 0.5)
		# Offsetting a 45° chamfer inward by `b` shortens the cut by `b(2 - √2)`,
		# which is what keeps the border an even width all the way round the
		# corner instead of pinching at it.
		var inner := _outline(rect.grow(-thickness),
			maxf(cut - thickness * (2.0 - sqrt(2.0)), 0.0))

		if fill.a > 0.0:
			RenderingServer.canvas_item_add_polygon(
				to_canvas_item, inner, PackedColorArray([fill]))

		if thickness > 0.0 and edge.a > 0.0:
			_ring(to_canvas_item, outer, inner, edge)

	## Always eight points, even where a corner is square — the two points there
	## land on top of each other and the triangles between them come out with no
	## area. Keeping the count fixed is what lets the ring be indexed rather than
	## rebuilt per shape.
	func _outline(rect: Rect2, size: float) -> PackedVector2Array:
		var left := rect.position.x
		var top := rect.position.y
		var right := left + rect.size.x
		var bottom := top + rect.size.y
		var at := clampf(size, 0.0, minf(rect.size.x, rect.size.y) * 0.5)

		var tl := at if corners[0] else 0.0
		var tr := at if corners[1] else 0.0
		var br := at if corners[2] else 0.0
		var bl := at if corners[3] else 0.0

		return PackedVector2Array([
			Vector2(left + tl, top), Vector2(right - tr, top),
			Vector2(right, top + tr), Vector2(right, bottom - br),
			Vector2(right - br, bottom), Vector2(left + bl, bottom),
			Vector2(left, bottom - bl), Vector2(left, top + tl),
		])

	func _ring(to_canvas_item: RID, outer: PackedVector2Array,
			inner: PackedVector2Array, colour: Color) -> void:
		var points := PackedVector2Array()
		points.append_array(outer)
		points.append_array(inner)

		var colours := PackedColorArray()
		colours.resize(points.size())
		colours.fill(colour)

		var indices := PackedInt32Array()
		for at in 8:
			var next := (at + 1) % 8
			for index in [at, next, 8 + next, at, 8 + next, 8 + at]:
				indices.append(index)

		RenderingServer.canvas_item_add_triangle_array(
			to_canvas_item, indices, points, colours)


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

	built.set_stylebox("panel", "PanelContainer", plate(PANEL, PANEL_HI))
	return built


## The plate, and what almost everything in the menu is now made of.
##
## `plaque`, `frame` and `inset` are still here and still square, because a
## photograph is a rectangle and the album's slots are photographs. The chamfer
## belongs to the *furniture* — the tabs, the frame, the field, the selection
## bar — and putting it on a picture would be cropping the picture.
static func plate(fill: Color, edge: Color, cut: float = CUT,
		border: int = BORDER, shadow: bool = true) -> Plate:
	var box := Plate.new()
	box.fill = fill
	box.edge = edge
	box.border = float(border)
	box.cut = cut
	if shadow:
		box.shadow_offset = Vector2(SHADOW_OFFSET)
		box.shadow_colour = SHADOW_COLOUR
	return box


## The field a subscreen sits on: the tab's own hue, taken down to near-black.
##
## This is the Pokémon Snap habit finally doing something. Colour-coding that
## only reaches a two-pixel border is colour-coding you have to go looking for —
## the tab strip already told you which tab is lit, so the border was repeating
## the one thing that was never in doubt. Recolouring the whole field means the
## screen has changed colour before you have focused on any part of it.
##
## The value is low enough that this stays a field rather than becoming a colour.
## `PANEL`'s note argues blue is the right canvas because none of the references
## is blue and a warm panel under gold is gold on gold, and that argument still
## holds — at 20% value the hue is a cast on a near-black, not a fill competing
## with the frame. Blue remains what the game is in; this is what a page is on.
## The saturation is high and the value is very low, which is the order that
## matters and the opposite of the obvious one. Taking a hue down by
## desaturating it gives four greys with a suggestion in them; taking it down by
## *value* while holding the chroma up keeps a dark green a green and a dark red
## a red. The red is what proves it — the first two attempts came out a rust
## brown and read as upholstery, and both of them lost by being too light rather
## than by being the wrong hue.
##
## The value looks impossibly low written down and is not, because a `Color` on
## the Forward+ canvas is not what lands on the screen: the 2D pipeline works in
## linear and converts on the way out, so 0.075 arrives at roughly a third of
## full. Anything picked by eye off a hex value in a colour picker will come out
## about twice as bright as intended here, which is exactly what happened twice.
static func field(tint: Color) -> Color:
	return Color.from_hsv(tint.h, 0.85, 0.075, 0.92)


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


## The heavy one, for the body of the menu. Same object, thicker edge — so what
## the subscreens sit in is a frame with a well in it rather than one flat field
## the size of the screen. The depth comes from there being two surfaces at all;
## a single translucent rectangle has no near and far to read.
static func frame(fill: Color, edge: Color) -> StyleBoxFlat:
	var box := plaque(fill, edge)
	box.set_border_width_all(BORDER_FRAME)
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


## Dress a label in the display face, outline and all.
##
## It is a function rather than four call sites setting four overrides, because
## the outline is not optional decoration on this face — a Luckiest Guy label
## without one is the odd one out on any screen that has the others. Anything
## reaching for `display_font()` directly should probably be calling this.
static func display_label(label: Label, size: int = SIZE_TAB) -> void:
	label.add_theme_font_override("font", display_font())
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_constant_override("outline_size", outline_for(size))
	label.add_theme_color_override("font_outline_color", OUTLINE_COLOUR)

	if _display_shader == null and ResourceLoader.exists(DISPLAY_SHADER_PATH):
		_display_shader = load(DISPLAY_SHADER_PATH)
	if _display_shader == null:
		return

	# The ramp is measured off the face rather than off the label, so it does not
	# depend on layout having happened. A label whose size is still zero the
	# first time it is styled would otherwise collapse the gradient to its bottom
	# colour and look like a bug in the shader rather than in the ordering.
	var mat := ShaderMaterial.new()
	mat.shader = _display_shader
	mat.set_shader_parameter("top_colour", DISPLAY_TOP)
	mat.set_shader_parameter("bottom_colour", DISPLAY_BOTTOM)
	mat.set_shader_parameter("ascent", display_font().get_ascent(size))
	mat.set_shader_parameter("enabled", 0.0)
	label.material = mat


## Turn the ramp on or off for one label. Off leaves whatever `font_color` says,
## which is how an unchosen tab keeps its flat dim grey.
static func display_gradient(label: Label, on: bool) -> void:
	var mat := label.material as ShaderMaterial
	if mat != null:
		mat.set_shader_parameter("enabled", 1.0 if on else 0.0)


## The line weight for a given font size. Floored at 2 because Godot rounds an
## outline to whole pixels and a 1px line reads as an artefact rather than as a
## drawn edge — below that it is better to have none.
static func outline_for(size: int) -> int:
	return maxi(2, roundi(size * OUTLINE_RATIO))


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


## A tween that runs while the game does not.
##
## Every one of these is driven by the pause screen, and the pause screen is the
## only thing in the tree still processing — a tween left on the default
## `TWEEN_PAUSE_BOUND` inherits its node's pause state, which is correct
## everywhere except here and would leave the menu frozen mid-slide the instant
## it did the thing it exists to do.
static func tween(on: Node) -> Tween:
	var made := on.create_tween()
	made.set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)
	made.set_parallel(true)
	return made


## The curve for one tweener. Untyped because `set_trans` lives on the concrete
## tweeners rather than on `Tweener`, and both kinds are passed through here —
## the jut is a property and the rise is a theme constant, which only
## `tween_method` can reach.
static func settle(tweener: Variant, arriving: bool) -> void:
	tweener.set_trans(ARRIVE_TRANS if arriving else LEAVE_TRANS)
	tweener.set_ease(Tween.EASE_OUT)


## A row of control prompts, in the one place that decides what one looks like.
##
## This lived twice — `hud.gd` built the string for the park and `park_menu.gd`
## built the same string for the footer — and the two had already drifted further
## than either copy admitted. The menu's row was Silkscreen; the HUD's was the
## engine's own face, because nothing had ever put a theme on the HUD, and this
## file has been asserting that "body appears on the HUD prompts" while that was
## quietly untrue.
##
## The key name is the display face and the action is the body face, which is a
## change to what this file used to say. The old rule sent anything short and
## shouty to the display face and everything else to body, and then made the key
## names an exception on the grounds that a prompt is a caption. But a key name
## is the shortest all-caps thing in the game — it is a tab label that happens to
## say ESC — and it was already being coloured to stand out from the word next to
## it. Giving it the face that does that job means the colour is no longer doing
## it alone.
##
## The word beside it stays body, which is the whole point: two faces on one line
## is the pairing this menu is built on, and it now happens at the smallest scale
## the interface has as well as the largest.
##
## `bold_font` rather than a second label, because `RichTextLabel` puts mixed
## faces on a common baseline and an `HBoxContainer` of two `Label`s does not —
## it centres each one in the row and leaves the two sitting at different heights
## by however much their ascents differ, which for these two faces is three
## pixels at tab size and visible at any size.
static func prompts(label: RichTextLabel, pairs: Array,
		centred: bool = true, size: int = SIZE_SMALL) -> void:
	var key_size := roundi(size * DISPLAY_RATIO)
	label.bbcode_enabled = true
	label.add_theme_font_override("normal_font", font())
	label.add_theme_font_size_override("normal_font_size", size)
	label.add_theme_font_override("bold_font", display_font())
	label.add_theme_font_size_override("bold_font_size", key_size)

	var parts := PackedStringArray()
	for pair in pairs:
		parts.append("[outline_size=%d][outline_color=#%s][color=#%s][b]%s[/b][/color][/outline_color][/outline_size]  %s" % [
			outline_for(key_size), OUTLINE_COLOUR.to_html(false),
			ACCENT.to_html(false), pair[0], pair[1],
		])

	var align := "center" if centred else "right"
	label.text = "[%s]%s[/%s]" % [align, HINT_SEPARATOR.join(parts), align]


## Capitals, and the one place that decides so. Every label in the menu goes
## through here — a menu that is capitals except for the two strings somebody
## added last is worse than one that never tried.
static func caps(text: String) -> String:
	return text.to_upper()
