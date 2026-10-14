shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

// The land of the ground grid (2026-10-13, Stage 2 of
// documentation/terrain-height-grid-plan-2026-10-12.md). Its colour is Christina's painted
// image, assets/source/world_ground/colour/x{tx}_z{tz}.png, one per 1 km tile, which
// tools/ground_mount.gd gives each tile's own material. The image holds the albedo itself as
// sRGB: the palette's tint was baked into it (her choice, 2026-10-13), so there is no tint and
// no depth term here, and what she paints is what the game shows.
//
// The lighting response is landscape_depth_palette.gdshader's, so the land looks as it did:
// Burley diffuse, Schlick-GGX specular, roughness 0.97, specular and metallic left at Godot's
// defaults (0.5 and 0), and the colour linearised by the same sRGB step after it is filtered,
// as the palette does after the GPU interpolates a vertex colour.

// No source_color: the texture is filtered in its stored sRGB values, as vertex colours were.
uniform sampler2D colour : filter_linear_mipmap_anisotropic, repeat_disable;
// Nodes along a tile's side (grid.json's tile_samples). The tile's UV runs 0..1 from node 0
// to node 500; node n is texel n, whose centre is (n + 0.5) / 501.
uniform float tile_samples = 501.0;
// Where the image has no ground (alpha 0) and the mesh still reaches: the plain green.
const vec3 FALLBACK_SRGB = vec3(0.36, 0.47, 0.31);


vec3 srgb_to_linear(vec3 color_srgb) {
	vec3 low = color_srgb / 12.92;
	vec3 high = pow((color_srgb + vec3(0.055)) / 1.055, vec3(2.4));
	return mix(low, high, step(vec3(0.04045), color_srgb));
}


void fragment() {
	vec2 texel = (UV * (tile_samples - 1.0) + vec2(0.5)) / tile_samples;
	vec4 painted = texture(colour, texel);
	// The texture is premultiplied (tools/ground_mount.gd makes it so from the PNG), so
	// dividing by alpha averages only the nodes that have ground, at every mip level: a coast
	// never darkens towards the empty texels beside it.
	vec3 albedo_srgb = painted.a > 0.002 ? painted.rgb / painted.a : FALLBACK_SRGB;
	ALBEDO = srgb_to_linear(clamp(albedo_srgb, vec3(0.0), vec3(1.0)));
	ROUGHNESS = 0.97;
}
