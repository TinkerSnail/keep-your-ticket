shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

// Flat paving whose brick courses form graphic sine-wave fronts washing north.
// Amplitude, wavelength and grouped-row tints are ordinary inspector
// controls; the walk geometry and collision never ripple.
uniform sampler2D brick_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D brick_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec4 brick_tint : source_color = vec4(0.69, 0.53, 0.43, 1.0);
uniform vec4 band_tint_a : source_color = vec4(0.74, 0.54, 0.42, 1.0);
uniform vec4 band_tint_b : source_color = vec4(0.58, 0.36, 0.29, 1.0);
uniform vec4 band_tint_c : source_color = vec4(0.78, 0.59, 0.35, 1.0);
uniform vec4 band_tint_d : source_color = vec4(0.65, 0.42, 0.47, 1.0);
uniform float tiles_per_metre : hint_range(0.1, 1.0, 0.01) = 0.3125;
uniform float wave_amplitude_m : hint_range(0.0, 1.5, 0.01) = 0.78;
uniform float wave_length_m : hint_range(3.0, 16.0, 0.1) = 5.6;
uniform float phase_drift : hint_range(0.0, 0.5, 0.01) = 0.06;
uniform float courses_per_tint : hint_range(1.0, 8.0, 1.0) = 4.0;
uniform float tint_strength : hint_range(0.0, 1.0, 0.01) = 0.65;
uniform float normal_depth : hint_range(0.0, 2.0, 0.01) = 0.60;
uniform vec2 pattern_origin = vec2(0.0, 194.025);

varying vec2 paving_metres;


void vertex() {
	vec3 world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	paving_metres = world_position.xz - pattern_origin;
}


void fragment() {
	vec2 metres = paving_metres;

	// A tighter, clean sine repeats several times across the walk like a drawn
	// ocean. The tiny phase drift keeps adjacent fronts from feeling stamped.
	float drift = phase_drift * sin(metres.y * TAU / 24.0);
	float front = wave_amplitude_m * sin(
		metres.x * TAU / wave_length_m + 0.55 + drift);
	vec2 brick_uv = vec2(metres.x, metres.y + front) * tiles_per_metre;

	vec3 brick_value = texture(brick_albedo, brick_uv).rgb;
	// The source texture contains 32 running-bond courses per repeat. Group a few
	// complete courses into each tint band, keeping every boundary on a mortar
	// joint and making the cartoon wave legible from standing height.
	float row_id = floor(brick_uv.y * 32.0);
	float band = mod(floor(row_id / courses_per_tint), 4.0);
	vec3 selected_tint = band_tint_a.rgb;
	if (band > 0.5 && band < 1.5) {
		selected_tint = band_tint_b.rgb;
	} else if (band >= 1.5 && band < 2.5) {
		selected_tint = band_tint_c.rgb;
	} else if (band >= 2.5) {
		selected_tint = band_tint_d.rgb;
	}
	// These are clay colours, not brightness multipliers. Blending the actual
	// row colour before applying the grayscale brick texture keeps the bond and
	// mortar intact while making the four-course striation visible in sunlight.
	vec3 brick = brick_value * mix(brick_tint.rgb, selected_tint, tint_strength);
	ALBEDO = brick;
	ROUGHNESS = 0.94;
	NORMAL_MAP = texture(brick_normal, brick_uv).rgb;
	NORMAL_MAP_DEPTH = normal_depth;
}
