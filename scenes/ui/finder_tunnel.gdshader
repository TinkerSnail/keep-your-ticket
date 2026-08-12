shader_type canvas_item;

// The inside of a plastic camera body with an eye pressed to the back of it.
//
// Not a letterbox and not a crop. The window is a small rounded hole and
// everything outside it is gone, which is the whole cost of raising the camera:
// a few more degrees where you are pointing, and no park at all beside you.
//
// The window is deliberately bigger than the picture. A bright-line finder shows
// more than it takes, so the thing about to walk into frame is visible before it
// arrives — and so is the thing that will never be in the photograph at all.

// Half-extents in screen heights, so the window keeps its shape at any aspect.
uniform float window_half_height = 0.40;
uniform float window_aspect = 1.18;
uniform float corner_radius = 0.10;
// Cheap plastic optics do not have an edge. Neither does an eye socket.
uniform float softness = 0.085;
uniform vec4 body_color : source_color = vec4(0.015, 0.014, 0.018, 1.0);
uniform float body_alpha = 0.985;

void fragment() {
	float aspect = SCREEN_PIXEL_SIZE.y / SCREEN_PIXEL_SIZE.x;

	// Work in screen heights on both axes so the rounded corners stay round.
	vec2 p = UV - vec2(0.5);
	p.x *= aspect;

	vec2 half_ext = vec2(window_half_height * window_aspect, window_half_height);
	vec2 inner = max(half_ext - vec2(corner_radius), vec2(0.0));
	vec2 d = abs(p) - inner;
	float dist = length(max(d, vec2(0.0))) + min(max(d.x, d.y), 0.0) - corner_radius;

	COLOR = vec4(body_color.rgb, smoothstep(0.0, softness, dist) * body_alpha);
}
