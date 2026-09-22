shader_type spatial;
render_mode cull_disabled;

// Local leaf UVs run edge-to-edge on X and crown-to-tip on Y. The broad base
// colour stays visible between an adjustable margin and a slim centre stripe.
uniform vec4 base_color : source_color = vec4(0.22, 0.38, 0.10, 1.0);
uniform vec4 edge_color : source_color = vec4(0.92, 0.78, 0.30, 1.0);
uniform vec4 centre_color : source_color = vec4(0.58, 0.66, 0.18, 1.0);
uniform float edge_width : hint_range(0.02, 0.32) = 0.16;
uniform float centre_width : hint_range(0.0, 0.28) = 0.08;
uniform float softness : hint_range(0.005, 0.12) = 0.035;

void fragment() {
	float nearest_edge = min(UV.x, 1.0 - UV.x);
	float edge_mask = 1.0 - smoothstep(edge_width - softness, edge_width + softness, nearest_edge);
	float centre_distance = abs(UV.x - 0.5);
	float centre_mask = 1.0 - smoothstep(centre_width - softness, centre_width + softness, centre_distance);
	vec3 colour = mix(base_color.rgb, edge_color.rgb, edge_mask);
	colour = mix(colour, centre_color.rgb, centre_mask);
	ALBEDO = colour;
	ROUGHNESS = 0.9;
}
