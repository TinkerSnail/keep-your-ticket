shader_type spatial;
render_mode blend_mix, cull_back, diffuse_burley, specular_schlick_ggx;

// Open water: the sea and the hill lakes (2026-10-07; Christina, 2026-10-06: "we dont want the
// ocean water to stay opaque").
//
// Clear where it is shallow and its own colour where it is deep, measured at every pixel from the
// ground behind the surface, read off the depth buffer. So it needs nothing laid under it: over
// the coast shelf, the beach front's shelf and a lake's bed, the ground shows through the first
// metres and fades out; where the sea has no ground under it at all, what lies behind is the far
// plane, and the water is wholly its colour, which is what the sea was before. A seabed, when one
// is built, shows through the same way without anything here changing.
//
// Depth is measured along the view, not straight down: at a low angle the light crosses more water
// before it reaches the bed, and the sea goes to colour sooner, as it does from a bluff.
//
// The colour is the bay's own (tools/gen_props.gd, `mats["water"]`), and so are its roughness and
// metalness, so from the promenade the far sea is what it was.
uniform vec3 colour : source_color = vec3(0.34, 0.44, 0.52);

// The water a metre or two deep over a pale bed, where the bed's colour and the sky's are both
// still in it.
uniform vec3 shallow : source_color = vec3(0.30, 0.50, 0.52);

// Metres of water, along the view, that hide nearly two thirds of what lies behind it.
uniform float clarity = 3.0;

// How much the surface itself covers at the waterline, where there is no water in front of the
// bed: enough that the edge reads as water and not as wet ground.
uniform float surface : hint_range(0.0, 1.0) = 0.25;

uniform float rough : hint_range(0.0, 1.0) = 0.08;
uniform float metal : hint_range(0.0, 1.0) = 0.1;

// Ripples: three swells crossing, in world metres, so the sea's four boxes and every lake ripple
// as one water. Metres per wave of the longest, and how far they tip the surface (its slope).
// Analytic, like the pool's, so there is no texture to tile and no tangent CSG has to supply.
uniform float wavelength = 7.0;
uniform float chop : hint_range(0.0, 0.5) = 0.08;

// Beyond this the ripples fade out, before they are finer than a pixel and sparkle.
uniform float ripple_reach = 120.0;

uniform sampler2D depth_texture : hint_depth_texture, filter_nearest;

varying vec3 world;

void vertex() {
	world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

vec2 slope(vec2 p, float t) {
	const vec2 dirs[3] = vec2[3](vec2(0.94, 0.34), vec2(-0.48, 0.88), vec2(0.17, -0.99));
	const float shorter[3] = float[3](1.0, 1.61, 2.47);
	const float speed[3] = float[3](0.7, 1.0, 1.3);
	vec2 g = vec2(0.0);
	for (int i = 0; i < 3; i++) {
		float k = TAU * shorter[i] / wavelength;
		g += dirs[i] * cos(dot(dirs[i], p) * k + t * speed[i]) * chop / 3.0;
	}
	return g;
}

void fragment() {
	// What lies behind this pixel, in view space (Forward+: the depth buffer is reversed and its
	// value is already the NDC depth).
	float raw = texture(depth_texture, SCREEN_UV).r;
	vec4 behind = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, raw, 1.0);
	behind.xyz /= behind.w;
	float through = max(0.0, length(behind.xyz) - length(VERTEX));
	float cover = 1.0 - exp(-through / clarity);
	ALPHA = mix(surface, 1.0, cover);
	ALBEDO = mix(shallow, colour, cover);

	vec2 g = slope(world.xz, TIME) * clamp(1.0 - length(VERTEX) / ripple_reach, 0.0, 1.0);
	NORMAL = normalize((VIEW_MATRIX * vec4(normalize(vec3(-g.x, 1.0, -g.y)), 0.0)).xyz);
	ROUGHNESS = rough;
	METALLIC = metal;
}
