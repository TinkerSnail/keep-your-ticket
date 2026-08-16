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

void fragment() {
	vec2 g = slope(w_pos.xz);
	// Straight to `NORMAL` in view space rather than through `NORMAL_MAP`.
	// A normal map is in tangent space and would need tangents on a CSG cap
	// face; this needs nothing but the model matrix.
	vec3 n = normalize(vec3(-g.x, 1.0, -g.y));
	NORMAL = normalize((VIEW_MATRIX * vec4(n, 0.0)).xyz);

	ALBEDO = tint;
	ROUGHNESS = rough;
	METALLIC = 0.0;
	SPECULAR = spec;
	// Deliberately opaque. A 25cm pool over a dark floor shows nothing through
	// it worth the sorting, and the one thing transparency would definitely do
	// is put a translucent disc in front of eleven translucent jets.
}
