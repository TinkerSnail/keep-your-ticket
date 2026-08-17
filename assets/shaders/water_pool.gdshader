shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

// Standing water: the fountain's pool and the two basins above it.
//
// Hand-written rather than generated, and it is the only shader in the park.
// Everything else here is a `StandardMaterial3D` with a procedural texture on
// it, and that stops working the moment a surface has to *move*: a material
// cannot animate itself and a script scrolling `uv1_offset` every frame would
// be the park's only per-frame CPU cost that is not a guest. `TIME` in a
// fragment shader costs nothing and needs nobody to drive it.
//
// The park has almost no motion in it — the crowd, and the clock's hands. Water
// is the third thing, and it is the only one that never stops, which is most of
// why the fountain is worth the trouble: it puts something alive at the centre
// of the room at every hour, including the ones with nobody in it.

// A pool this size is not a texture, it is a wake. Two families of wave, and
// they are doing different jobs:
//
//   - rings travelling *outward from the centre*, because the thing disturbing
//     this water is in the middle of it. That is what makes it read as a
//     fountain's pool rather than as a pond that happens to have a statue in.
//   - two flat ripples crossing at an angle, so the rings are not a dartboard.
//
// Analytic, so the slope is the exact derivative rather than a difference of
// two texture samples, and there is no tile to line up and no normal map to
// need tangents CSG may or may not have generated.
uniform vec3 tint : source_color = vec3(0.10, 0.24, 0.28);
uniform vec3 centre = vec3(0.0, 0.0, 0.0);

// Metres per ring, roughly. The upper basins take a much smaller number,
// because a 4m dish with the pool's wavelength on it has one wave in it.
uniform float ring_scale = 1.0;
uniform float chop = 1.0;
uniform float rough : hint_range(0.0, 1.0) = 0.06;

// Low roughness is the whole point and it is the same argument the boardwalk's
// water makes: it is what turns a low sun into a glitter path. At noon this
// reads as a dark mirror of the sky, at seven it reads as gold, and neither
// needs anything drawn on it.
uniform float spec : hint_range(0.0, 1.0) = 0.9;

// Submerged lamps, drawn **by the water** rather than laid on top of it.
//
// Three builds of the cascade's niche put the glow on separate geometry — a
// 4cm disc, then a thinner one, then a small lens inside a rippling halo — and
// every one of them got the same note back: they sit on top of the water. They
// did, and they always would have. A patch laid on a surface is a second
// surface: it has its own height, its own rim, its own shading and, once it
// wore this very shader, its own ring pattern radiating from its own centre
// while the water's radiated from the fountain's. Two rippling things instead
// of one rippling thing with a bright part.
//
// So the water draws it. There is nothing to float, because there is nothing
// there — the pool is one surface and the lit part of it is one term in its own
// fragment shader, carrying the same waves and the same normal as the water a
// centimetre away, because it *is* that water.
//
// `xy` is the lamp in world x/z, `z` its radius, `w` its strength. Zero by
// default, so every other water material in the park is untouched.
//
// **Two scalars rather than an array, and that is Godot rather than taste:**
// "Setting default values to uniform arrays is not supported". An array would
// therefore have to be initialised by every material that wears this shader —
// eight of them, six of which have no lamps — or carry a separate count uniform
// to be skipped by. Two `vec4`s default cleanly to nothing and cover both
// basins: the trough has two lamps and the niche's bowl has one.
uniform vec4 lamp_a = vec4(0.0);
uniform vec4 lamp_b = vec4(0.0);
uniform vec3 lamp_tint : source_color = vec3(1.0, 0.90, 0.72);

varying vec3 w_pos;

void vertex() {
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

// The surface gradient in world x/z. Height is never needed — only its slope,
// which is what the shading normal is made of.
vec2 slope(vec2 p) {
	vec2 d = p - centre.xz;
	float r = max(length(d), 0.001);
	vec2 rn = d / r;
	vec2 g = vec2(0.0);

	float k1 = 5.5 * ring_scale;
	float k2 = 11.0 * ring_scale;
	g += rn * (0.017 * k1) * cos(r * k1 - TIME * 2.9);
	g += rn * (0.008 * k2) * cos(r * k2 - TIME * 4.6 + 1.3);

	vec2 a = normalize(vec2(0.83, 0.56));
	vec2 b = normalize(vec2(-0.42, 0.91));
	float k3 = 9.0 * chop;
	float k4 = 15.0 * chop;
	g += a * (0.006 * k3) * cos(dot(p, a) * k3 + TIME * 2.1);
	g += b * (0.004 * k4) * cos(dot(p, b) * k4 - TIME * 3.3);
	return g;
}

// How lit this bit of water is, summed over the lamps under it. Two terms per
// lamp and they are doing different jobs: a wide soft halo, which is the light
// spreading through the water, and a tight core, which is the lens itself seen
// through it. One term alone gives either a flat disc or a point with no reach.
float one_lamp(vec2 p, vec4 l) {
	if (l.w <= 0.0) {
		return 0.0;
	}
	float d = length(p - l.xy);
	float halo = 1.0 - smoothstep(0.0, l.z, d);
	float core = 1.0 - smoothstep(0.0, l.z * 0.30, d);
	return l.w * (halo * halo * 0.6 + core * core);
}

float lamp_glow(vec2 p) {
	return one_lamp(p, lamp_a) + one_lamp(p, lamp_b);
}

void fragment() {
	vec2 g = slope(w_pos.xz);
	// Straight to `NORMAL` in view space rather than through `NORMAL_MAP`.
	// A normal map is in tangent space and would need tangents on a CSG cap
	// face; this needs nothing but the model matrix.
	vec3 n = normalize(vec3(-g.x, 1.0, -g.y));
	NORMAL = normalize((VIEW_MATRIX * vec4(n, 0.0)).xyz);

	// **Albedo and gloss, not emission.** An emissive term would need driving off
	// the clock the way `_lit_material` is, or it would glow flat at noon — which
	// is the fault that doc block warns about. Brightening the water instead
	// costs nothing and is closer to true: a lamp under water does not make the
	// surface a light source, it makes that patch of it pale and glassy. It reads
	// by day as the lens showing through and by night under `niche_glow`, which
	// is the omni already standing in the recess.
	float lit = lamp_glow(w_pos.xz);
	ALBEDO = mix(tint, lamp_tint, clamp(lit * 0.75, 0.0, 0.92));
	ROUGHNESS = mix(rough, rough * 0.45, clamp(lit, 0.0, 1.0));
	METALLIC = 0.0;
	SPECULAR = mix(spec, 1.0, clamp(lit * 0.6, 0.0, 1.0));
	// Deliberately opaque. A 25cm pool over a dark floor shows nothing through
	// it worth the sorting, and the one thing transparency would definitely do
	// is put a translucent disc in front of eleven translucent jets.
}
