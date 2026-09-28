shader_type spatial;
render_mode cull_disabled;

// The palm crown's leaves (PRP-COAST-006), in place of the material its GLB
// brings, through the GLB's import settings (`materials` > `palm_crown` > use
// external: assets/materials/palm_crown_leaf.tres). The same as that material,
// the colour painted in her PSD with the cut-out in its alpha and roughness and
// metalness from the ORM, with one thing it cannot do: a leaf's underside
// looks unlike its top. Both faces share one painted texture, so the
// underside is taken darker, cooler and flatter here (Christina, 2026-09-27:
// "can the undersides of the fronds be more differentiated").
//
// Which face is the underside: the blades' normals point down (measured on
// assets/source/props/palm_crown.blend, 2026-09-27), so the glTF front face,
// the side the normals face, is the underside. Mirrored fronds keep it
// (palm_crown.gd reflects their normals and reverses their winding). Flip
// `underside_is_front` if the blades' normals are ever turned over.

uniform sampler2D colour_texture : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D orm_texture : hint_default_white, filter_linear_mipmap, repeat_disable;
uniform float alpha_cut : hint_range(0.0, 1.0) = 0.5;
uniform bool underside_is_front = true;
// The underside's colour: the painted colour taken toward this tint...
uniform vec4 underside_tint : source_color = vec4(0.46, 0.62, 0.58, 1.0);
// ...this far (0 the top's colour, 1 the tint times the paint's brightness)...
uniform float underside_mix : hint_range(0.0, 1.0) = 0.6;
// ...and this much darker, and this rough.
uniform float underside_darken : hint_range(0.0, 1.0) = 0.25;
uniform float underside_roughness : hint_range(0.0, 1.0) = 0.9;
// Frond to frond, each frond's green leans a little yellow or a little
// blue-green, this far at most, and is a little lighter or darker (Christina,
// 2026-09-27: "vary the yellow-green slightly frond to frond"). The frond's own
// tone is its vertex colour's red (palm_crown.gd, `_tone`); where the crown
// stands offsets it, so the same frond on two palms differs. Merged or not, a
// crown's fronds share its position, so the look is the same either way.
uniform float frond_hue : hint_range(0.0, 0.6) = 0.25;
uniform float frond_brightness : hint_range(0.0, 0.3) = 0.08;

float crown_offset(vec3 at) {
	return fract(sin(dot(at.xz, vec2(12.9898, 78.233))) * 43758.5453);
}

void fragment() {
	vec4 colour = texture(colour_texture, UV);
	vec4 orm = texture(orm_texture, UV);
	bool underside = FRONT_FACING == underside_is_front;
	vec3 albedo = colour.rgb;
	float roughness = orm.g;
	// Only green paint takes the frond's lean and the underside's cool: stubs
	// and brown dead fronds keep their colour.
	float green = smoothstep(0.0, 0.12, albedo.g - max(albedo.r, albedo.b));
	vec3 crown = MODEL_MATRIX[3].xyz;
	float lean = fract(COLOR.r + crown_offset(crown)) * 2.0 - 1.0;
	// A vivid green has almost no red or blue to scale, so the lean adds them
	// in proportion to the green: red toward yellow, blue toward teal.
	float amount = frond_hue * abs(lean) * green;
	if (lean > 0.0) {
		albedo.r += amount * albedo.g;
		albedo.b *= 1.0 - 0.5 * amount;
	} else {
		albedo.b += 0.6 * amount * albedo.g;
		albedo.r *= 1.0 - 0.5 * amount;
	}
	float lift = fract(COLOR.r * 7.31 + crown_offset(crown + vec3(3.7))) * 2.0 - 1.0;
	albedo *= 1.0 + frond_brightness * lift * green;
	if (underside) {
		float brightness = dot(albedo, vec3(0.2126, 0.7152, 0.0722));
		vec3 cool = underside_tint.rgb * brightness * 1.8;
		albedo = mix(albedo, cool, underside_mix * green) * (1.0 - underside_darken);
		roughness = underside_roughness;
	}
	ALBEDO = albedo;
	ROUGHNESS = roughness;
	METALLIC = orm.b;
	ALPHA = colour.a;
	ALPHA_SCISSOR_THRESHOLD = alpha_cut;
}
