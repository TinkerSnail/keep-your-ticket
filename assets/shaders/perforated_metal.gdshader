shader_type spatial;
render_mode cull_disabled, depth_prepass_alpha;

uniform vec4 paint : source_color = vec4(0.035, 0.25, 0.16, 1.0);
uniform vec2 cells = vec2(24.0, 6.0);
uniform float strand_width : hint_range(0.02, 0.16) = 0.065;

void fragment() {
	vec2 cell = fract(UV * cells) - vec2(0.5);
	float diamond = abs(cell.x) + abs(cell.y);
	if (abs(diamond - 0.46) > strand_width) {
		discard;
	}
	ALBEDO = paint.rgb;
	METALLIC = 0.34;
	ROUGHNESS = 0.58;
}
