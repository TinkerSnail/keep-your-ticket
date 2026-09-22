shader_type spatial;
render_mode cull_disabled;

uniform vec4 color_a : source_color = vec4(0.83, 0.035, 0.055, 1.0);
uniform vec4 color_b : source_color = vec4(0.94, 0.86, 0.68, 1.0);
uniform float panel_count : hint_range(4.0, 24.0, 2.0) = 12.0;

varying vec3 local_position;

void vertex() {
	local_position = VERTEX;
}

void fragment() {
	float angle = atan(local_position.z, local_position.x);
	float around = (angle + 3.14159265) / 6.28318530;
	float panel = mod(floor(around * panel_count), 2.0);
	ALBEDO = mix(color_a.rgb, color_b.rgb, panel);
	METALLIC = 0.0;
	ROUGHNESS = 0.66;
}
