shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

// Paint distance into the land itself: the park-edge landscape stays a warm,
// sunlit olive while the world beyond settles into a darker coastal blue-green.
// The park rectangle, not the origin, is the reference so every district gets
// the same foreground band around its own edge.
uniform bool use_vertex_color = true;
uniform vec4 base_color = vec4(0.36, 0.47, 0.31, 1.0);
uniform vec3 near_gain = vec3(1.08, 1.06, 0.92);
uniform vec3 far_gain = vec3(0.72, 0.82, 1.06);
uniform vec2 park_min = vec2(-212.0, -230.0);
uniform vec2 park_max = vec2(222.0, 220.0);
uniform float warm_band = 20.0;
uniform float cool_band = 360.0;

varying vec3 landscape_world_position;


vec3 srgb_to_linear(vec3 color_srgb) {
	vec3 low = color_srgb / 12.92;
	vec3 high = pow((color_srgb + vec3(0.055)) / 1.055, vec3(2.4));
	return mix(low, high, step(vec3(0.04045), color_srgb));
}


void vertex() {
	landscape_world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}


void fragment() {
	vec2 outside = max(max(park_min - landscape_world_position.xz,
		landscape_world_position.xz - park_max), vec2(0.0));
	float depth = smoothstep(warm_band, cool_band, length(outside));
	vec3 source_srgb = use_vertex_color ? COLOR.rgb : base_color.rgb;

	// Rock and beach colors share these meshes with the greenery. Restrict the
	// depth treatment to colors whose green channel is genuinely dominant.
	float green_mask = smoothstep(0.025, 0.09,
		source_srgb.g - max(source_srgb.r, source_srgb.b));
	vec3 depth_gain = mix(near_gain, far_gain, depth);
	vec3 tinted_srgb = source_srgb * mix(vec3(1.0), depth_gain, green_mask);

	ALBEDO = srgb_to_linear(clamp(tinted_srgb, vec3(0.0), vec3(1.0)));
	ROUGHNESS = 0.97;
}
