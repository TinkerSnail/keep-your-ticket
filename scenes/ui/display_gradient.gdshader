shader_type canvas_item;

// The vertical fill on the display face: gold at the cap line, orange-red at the
// baseline. Every cartoon logo this game is aimed at does this, and it is the
// one thing a flat `font_color` cannot express.
//
// Two things make this trickier than a gradient normally is.
//
// The first is that a Label draws its outline and its glyphs through the same
// material, so a shader that simply tints everything would take the black line
// with it and the letters would lose the thing holding them together. They are
// separate draws with separate vertex colours, though, so the fill can be told
// apart from the outline by brightness — the outline is INK and the fill is set
// light on purpose. `step(0.5, ...)` is the whole test.
//
// The second is that UV on a glyph quad addresses the *font atlas*, not the
// label, so it is useless for asking how far down a letter a pixel is. VERTEX in
// the vertex stage is in the control's own space, which is the coordinate the
// gradient actually wants, so it gets carried across as a varying.

uniform vec4 top_colour : source_color = vec4(1.0, 0.851, 0.290, 1.0);
uniform vec4 bottom_colour : source_color = vec4(0.878, 0.263, 0.110, 1.0);

// Distance from the top of the label down to the baseline, in pixels. The span
// is the ascent rather than the label's height so the ramp lands on the capitals
// and finishes exactly at the baseline; anything below it is a descender and
// clamps to the bottom colour, which is what the reference logos do.
uniform float ascent = 26.0;

// 1.0 to fill, 0.0 to leave the label alone. Unselected tabs want their flat
// colour, so the gradient is per-label rather than a property of the face.
uniform float enabled = 0.0;

varying float local_y;

void vertex() {
	local_y = VERTEX.y;
}

void fragment() {
	float fill = step(0.5, max(COLOR.r, max(COLOR.g, COLOR.b))) * enabled;
	float t = clamp(local_y / max(ascent, 1.0), 0.0, 1.0);
	COLOR.rgb = mix(COLOR.rgb, mix(top_colour.rgb, bottom_colour.rgb, t), fill);
}
