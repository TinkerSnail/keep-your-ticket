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

// And a **ring** of them, because the plaza's pool has twelve and writing twelve
// scalars would be writing the jets' own arithmetic out a second time in a
// second language. `x` is the ring radius, `y` the count, `z` each lamp's
// radius, `w` the strength; the ring is concentric with `centre`, which it
// genuinely is — the same uniform the waves already radiate from.
//
// **The sign of the count carries the phase.** Positive puts spokes at
// `(i + 0.5)` steps, which is `_fountain_jets`' convention; negative puts them at
// `i` steps, which is `_veil`'s. The plaza's pool wears one of each — its lamps
// under the jets and its froth under the falls — and getting the sign wrong
// lands every patch exactly halfway between two of the things it belongs to,
// which looks deliberate and is not. Packed into the sign rather
// than given a uniform of its own because it is one bit.
uniform vec4 lamp_ring = vec4(0.0);

// **Froth, by the same argument.** It was 28 discs laid on the plaza's pool and
// it read exactly as the niche's lamps did — "the lights still sit on top of the
// water" turned out to be about these. Froth is not an object floating on water;
// it is a patch of water that is white and broken instead of dark and glassy, so
// it is the same term with the gloss going the other way.
//
// `foam_a`/`foam_b` are single patches, `foam_ring` a ring of them — one patch
// per fall, at the radius the falls hang from. The plaza's pool takes the ring,
// for the sixteen falls off the lower lip; the niche's trough and bowl take the
// singles, for the two off its basin and the one off its spout.
uniform vec4 foam_a = vec4(0.0);
uniform vec4 foam_b = vec4(0.0);
uniform vec4 foam_ring = vec4(0.0);
uniform vec3 foam_tint : source_color = vec3(0.62, 0.74, 0.76);
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

// The nearest spoke of a ring, then the same falloff as a single lamp. Only the
// nearest one can matter: the lamps are 0.55m across on a 13m circle, so no two
// of their halos reach each other.
//
// **`round` about the spoke, not `floor` into the cell, and the two are only the
// same thing for half the rings this draws.** At `i + 0.5` a spoke sits at the
// middle of its cell, so `floor` lands on the cell containing the fragment and
// the spoke it names is the nearest one — which is why the jets' lamp ring came
// out right. At `i` a spoke sits on the *boundary* between two cells, and `floor`
// always names the one below: every fragment in the anticlockwise half of a
// patch is measured against the spoke a whole step away and comes back with no
// froth at all. Sixteen landings would have drawn as sixteen half-moons, each
// cut dead straight through its own centre, and nothing had ever seen it because
// every `vec4` on this shader was arriving null (see `_shader_material`).
//
// Rounding asks the question the comment above claims to be asking — which spoke
// is nearest — instead of asking which cell this is in and hoping they agree.
float ring_lamps(vec2 p, vec4 ring) {
	// **`abs`, and it was not.** The count carries the phase in its sign — which
	// is what `half_step` four lines down reads it for — and this guard tested the
	// signed count, so the froth ring, whose count is −16, was rejected before it
	// drew a single patch. Every froth patch in the plaza's fountain vanished the
	// moment this shader took the job over, the generator reported success, the
	// coplanar test passed, and it took somebody looking at the pool to say the
	// foam was gone. A convention introduced in one hunk and a guard left assuming
	// the old one, written in the same edit, minutes apart.
	if (ring.w <= 0.0 || abs(ring.y) < 1.0) {
		return 0.0;
	}
	vec2 d = p - centre.xz;
	float n = abs(ring.y);
	float step_a = 6.28318530718 / n;
	float a = atan(d.y, d.x);
	float half_step = ring.y > 0.0 ? 0.5 : 0.0;
	float sa = (round(a / step_a - half_step) + half_step) * step_a;
	vec2 lp = centre.xz + vec2(cos(sa), sin(sa)) * ring.x;
	return one_lamp(p, vec4(lp, ring.z, ring.w));
}


float foam_at(vec2 p) {
	return one_lamp(p, foam_a) + one_lamp(p, foam_b) + ring_lamps(p, foam_ring);
}

float lamp_glow(vec2 p) {
	return one_lamp(p, lamp_a) + one_lamp(p, lamp_b) + ring_lamps(p, lamp_ring);
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
	// Froth goes on **after** the lamps and pulls the opposite way on gloss:
	// broken water scatters, so it is pale and matt where a lit patch is pale and
	// glassy. Applied second so a lamp under froth reads as froth lit from below,
	// which is what it would be.
	float froth = clamp(foam_at(w_pos.xz), 0.0, 1.0);
	vec3 col = mix(tint, lamp_tint, clamp(lit * 0.75, 0.0, 0.92));
	float rg = mix(rough, rough * 0.45, clamp(lit, 0.0, 1.0));
	float sp = mix(spec, 1.0, clamp(lit * 0.6, 0.0, 1.0));

	ALBEDO = mix(col, foam_tint, froth * 0.85);
	ROUGHNESS = mix(rg, 0.55, froth);
	METALLIC = 0.0;
	SPECULAR = mix(sp, 0.35, froth);
	// Deliberately opaque. A 25cm pool over a dark floor shows nothing through
	// it worth the sorting, and the one thing transparency would definitely do
	// is put a translucent disc in front of eleven translucent jets.
}
