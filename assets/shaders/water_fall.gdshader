shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

// `cull_back`, and it is not a performance choice — it is the difference
// between water and frosted glass.
//
// Everything wearing this material is a closed ring or a cylinder, so with
// culling off each surface is drawn *four* times over: the near face and its
// own backface, then the far side of the ring and its backface. Four coats of
// 40% alpha is 87%, which is opaque, and the first build of the fountain came
// out with two white drums where its basins should have been. Culled, the far
// half of a ring faces away and is dropped, a slab shows one face, and the
// number in `base_alpha` is the number you actually get.

// Moving water: the jets, the plume, the sheets under each basin's lip, and the
// froth where they land.
//
// The geometry underneath this is dumb on purpose — a jet is a thin cylinder
// and a sheet is a ring of thin slabs. What makes either read as water is that
// the *pattern on it travels*, and travels downward on the sheets and upward on
// the jets. Written off world position rather than UVs for the same reason
// `water_pool` is: nothing here promised a sensible UV, and world space means a
// sheet and the jet beside it are streaked at the same rate.

uniform vec3 tint : source_color = vec3(0.80, 0.89, 0.93);

// Positive falls, negative rises. A jet is the same material run backwards,
// which is worth more than a second shader: the two then break up at the same
// scale, and a plume that separates differently from the sheet it feeds reads
// as two effects rather than as one substance.
uniform float flow = 2.6;

// How many streaks across the sheet, and how fast the streaks themselves break.
uniform float streaks = 22.0;
uniform float grain = 2.4;

uniform float base_alpha : hint_range(0.0, 1.0) = 0.42;

// Water is not a light source, but falling water in sun is far brighter than
// anything's diffuse response, and the sheets hang in the shadow of the basin
// above them. A little self-lift is what stops a veil under a lip going grey
// exactly where it is supposed to be at its whitest.
uniform float glow : hint_range(0.0, 2.0) = 0.35;

// Fades the last of the fall out rather than ending it on a hard edge, which is
// what a sheet actually does — it does not stop, it stops being a sheet.
uniform float fade_from = 0.0;
uniform float fade_to = 0.0;

varying vec3 w_pos;

void vertex() {
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	// Streaks run down the sheet, so they are keyed off horizontal position and
	// the travel is keyed off height. A ring of slabs is then striped all the
	// way round without any of them knowing where on the ring it is.
	float across = (w_pos.x + w_pos.z * 0.7) * streaks;
	// Raised to a power, and that exponent is doing more work than anything
	// else in this file. A plain sine gives every fragment of a slab roughly the
	// same alpha, and a slab of near-uniform translucency with a specular
	// highlight on it is a pane of glass — which is what the first two builds of
	// the fountain looked like. Powered, the same sine becomes narrow bright
	// ropes with nearly-clear water between them, so one slab reads as several
	// falls and the stone behind shows through the gaps.
	float s = pow(sin(across) * 0.5 + 0.5, 2.2);

	// **Plus, not minus, and the sign was wrong until somebody watched it.**
	//
	// A band sits where `y * grain + TIME * flow` is constant, so it travels at
	// `dy/dTIME = -flow / grain`: positive `flow` carries it *down*, which is
	// what the uniform says it means. Written with a minus the whole thing ran
	// backwards — the sheets under each basin climbed their own lip at 1.1 m/s
	// and the jets rained into their own nozzles.
	//
	// Nothing could have caught it but an eye. Both directions animate, both
	// break up at the same rate, and every still frame of the two is identical;
	// the only difference is which way the pattern goes, and a screenshot has no
	// opinion about that. It is the same blind spot the coplanar rule has, and
	// the fix is the same one: capture consecutive frames and measure the shift
	// between them, which is what `tools/_flow_probe.gd` now does.
	float t = fract(w_pos.y * grain + TIME * flow);

	// Coherent where the water leaves, breaking up as it goes — so the thinning
	// end has to follow the *direction of travel* rather than always being the
	// bottom. A sheet is solid at the lip and ragged by the time it lands; a jet
	// is solid at the nozzle and ragged at the top of its throw. Same expression,
	// read the other way round.
	float along = flow >= 0.0 ? t : 1.0 - t;
	float body = mix(0.10, 1.0, s) * mix(0.35, 1.0, smoothstep(0.0, 0.55, along));

	float f = 1.0;
	if (fade_to != fade_from) {
		f = clamp((w_pos.y - fade_to) / (fade_from - fade_to), 0.0, 1.0);
	}

	ALBEDO = tint;
	EMISSION = tint * glow * body;
	// Deliberately *not* the pool's 0.06/0.9. Standing water is a mirror and
	// broken water is not: a sheet coming apart as it falls scatters, so a tight
	// specular highlight across a whole slab is the single strongest glass cue
	// there is. Rough and dull, with the brightness carried by `EMISSION`
	// instead, which varies rope by rope.
	ROUGHNESS = 0.32;
	METALLIC = 0.0;
	SPECULAR = 0.5;
	ALPHA = clamp(base_alpha * body * 1.5 * f, 0.0, 0.96);
}
