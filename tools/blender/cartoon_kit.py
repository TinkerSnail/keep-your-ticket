"""The cartoon kit: the pieces of the cartoony building standard, shared by
every house builder in `tools/blender/` (2026-10-04).

The standard is `documentation/prop-pipeline.md`, Standards applied,
"Buildings are cartoony": few, big pieces, the folksy features enlarged,
a top-heavy roof, a seeded hand of a few centimetres. These pieces came out
of the Victorian study (`victorian_cottage.py`, approved 2026-10-04)
unchanged, so the Victorian builds the same from here. A second set followed
the same day, when the Victorian's purple and b variants took the standard
and needed them too, generalized and still drawing in the blue's order (the
blue stayed hash-identical): the bell-cast roof (`bell_roof`, its
`BellRoof` with the profile the bargeboards read and the slopes the
shingles lie on), the cluster and vent scatter (`roof_clusters`,
`roof_vents`), the shaped brackets, the timber posts and the stoop parapets;
`turned` was added for the purple's posts and spindles. The house itself
(its sizes, its sunburst's composition, its order of work) stays in its
own builder.

Used from a house builder run in Blender, as `family_bolt` is:

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import cartoon_kit as ck  # noqa: E402

**Two kinds of maker.** A `*_bm` function builds into a bmesh in world
coordinates, a new one or the `bm` it is given, and hands it back; nothing
is named, tagged or linked. Every other maker takes a `finish` first: the
builder's own `finish(part, bm, mats, collide=...)`, which names, tags,
colours and links a part; the maker returns what it returns. Nothing here
reaches into a builder's kit, so each passes what it has:

- `victorian_cottage.py`, `carriage_house.py`: `kit.finish`
- `cottage_kit.py`: its module `finish`
- `stucco_row.py`: `lambda part, bm, mats, collide=True:
  finish(part, bm, coll, mats, variant=v, collide=collide)`

A finish that moves the vertices before handing them on (the Victorian's
lean, `Chunky.finish`) moves everything made through it, so a wall's
casings follow the wall.

**The hand.** The irregularities come from an `rng`, a `random.Random` the
builder seeds and passes in; `jit(rng, a)` is a nudge in -a..a. The draws
happen in the order the code below makes them, so the same makers called in
the same order on the same seed rebuild the same house. The roof's shingle
clusters draw from a seed of their own, so a change to the trim's hand does
not reshuffle the roof.

**Sizes.** The standard's sizes are the constants under "the standard's
sizes"; each maker takes them as keyword defaults, so a house departs from
one only where it means to. What belongs to the house (its rail height, its
risers and grade, how far a foot goes under the ground) is an argument.

**Shingles.** The roof's shingles are painted on a grid (`SHINGLE_E` courses
down each slope, `SHINGLE_W` tabs across, each course slid by `STAGGER` of a
tab), and the raised clusters are tabs of that same grid lifting, so the
roof's UVs and painting must follow it. `cartoon_preview.py` paints its
stand-in from these constants, so the two cannot drift apart. A slope is a
dict:

    s       +1 for the slope falling toward +X, -1 toward -X
    xc      the ridge line's x
    theta   the pitch, radians
    surf    surf(r, y): the slab's top face z at r across from the ridge, y along
    r, y    (lo, hi) ranges a tab must stay inside
    avoid   optional [(r0, r1, y0, y1)] boxes a tab must not touch (a chimney)
    placed  filled in by `shingle_tab`, (r, y, w, L) per tab, for vents to keep clear of

Every maker keeps the build rules in `AGENTS.md`: planar faces only (a lean
is a shear of level rings, never a tilted box), nothing sharing a plane with
what it meets (each laps in or stands proud), and scenery that must not be
walked on built `collide=False`.
"""

import math

import bmesh
from mathutils import Vector

# --- the standard's sizes ------------------------------------------------------
CASING, CASING_HEAD = 0.16, 0.20       # casing bars across, the head a little deeper
CASING_PROUD, CASING_SUNK = 0.06, 0.07  # a casing's face out of the wall, and its back into it
MULLION = 0.12
NEWEL = 0.24               # newels and piers: posts at least the cottage kit's chunky 0.22
BALUSTER, BALUSTER_PITCH = 0.10, 0.30   # square balusters, about this far apart
RAIL_H = 0.90              # a railing's top over its deck, unless the house says otherwise
RAIL_BOTTOM = 0.10         # the bottom rail's top over the deck
CAP_W, CAP_H = 0.14, 0.10  # the fat top rail
STRINGER = (0.22, 0.10)    # a stair rail's stringer under and over the nosing line
BARGE_PROUD = 0.10         # a bargeboard out of the rake's end

# --- the shingle grid ------------------------------------------------------------
# The grid the painting follows and the raised tabs snap to (her "make them
# the same size as the cluster shingles", then "lets address the funky
# shingles clusters", 2026-10-04): courses SHINGLE_E apart along each slope,
# measured as the world position's distance down the slope (so every roof
# plane keeps one phase), tabs SHINGLE_W across, each course slid by the
# golden fraction of a tab so no two courses' keyways line up. A raised tab is
# one painted shingle lifting: its butt on its course's butt line, its keyways
# on the painted ones, its head just long enough to pass under the course
# above and come out of the slab at that course's butt.
SHINGLE_E, SHINGLE_W, SHINGLE_KEY = 0.50, 0.62, 0.02
STAGGER = 0.618034         # a course's slide per course, in tabs
# a raised tab's wedge: its underside sunk, its butt proud, its head's thin edge under the face
TAB_SINK, TAB_TOP, TAB_EDGE = 0.014, 0.045, 0.004
# the tab's length, so its head leaves the slab exactly one course up
SHINGLE_L = SHINGLE_E / (1.0 - TAB_EDGE / (TAB_EDGE + TAB_TOP))


def jit(rng, amount):
    """A seeded nudge in -amount..amount."""
    return rng.uniform(-amount, amount)


# --- plates and prisms -----------------------------------------------------------

def prism_bm(poly, axis, lo, hi, bm=None):
    """A 2D polygon extruded along `axis` ('x' gives (y, z) pairs, 'y' gives
    (x, z), 'z' gives (x, y))."""
    if bm is None:
        bm = bmesh.new()

    def at(a, b, t):
        return {"x": (t, a, b), "y": (a, t, b), "z": (a, b, t)}[axis]

    near = [bm.verts.new(at(a, b, lo)) for a, b in poly]
    far = [bm.verts.new(at(a, b, hi)) for a, b in poly]
    bm.faces.new(near)
    bm.faces.new(list(reversed(far)))
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((near[i], near[j], far[j], far[i]))
    return bm


def prism(finish, part, mat, poly, axis, lo, hi, collide=True):
    return finish(part, prism_bm(poly, axis, lo, hi), [mat], collide=collide)


def plate_bm(polys, axis, lo, hi, bm=None):
    """One closed piece from convex polygons (points, material index) in a
    plane, welded where they share points, extruded along `axis` from lo
    to hi (prism_bm's convention): front and back faces per polygon and a
    side face on every edge only one polygon uses. A polygon meeting
    another must carry every point of their shared edge."""
    if bm is None:
        bm = bmesh.new()

    def key(p):
        return (round(p[0], 5), round(p[1], 5))
    verts = {}

    def vert(p, side):
        k = key(p) + (side,)
        if k not in verts:
            t = hi if side else lo
            verts[k] = bm.verts.new({"x": (t, p[0], p[1]), "y": (p[0], t, p[1]), "z": (p[0], p[1], t)}[axis])
        return verts[k]
    edges = {}

    def area(a, b, c):
        return abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) / 2

    for pts, mi in polys:
        if len(pts) <= 4:
            faces = [pts]
        else:
            # a long polygon (a rail or a band whose edge carries the
            # balusters' or drops' points in a row) as a fan from the corner
            # that makes the fattest triangles, never a sliver along the row
            n = len(pts)

            def fan(i):
                return [(pts[i], pts[(i + k) % n], pts[(i + k + 1) % n]) for k in range(1, n - 1)]
            best = max(range(n), key=lambda i: min(area(*t) for t in fan(i)))
            faces = fan(best)
        for f in faces:
            bm.faces.new([vert(p, 0) for p in f]).material_index = mi
            bm.faces.new([vert(p, 1) for p in reversed(f)]).material_index = mi
        for k in range(len(pts)):
            p, q = pts[k], pts[(k + 1) % len(pts)]
            edges.setdefault(frozenset((key(p), key(q))), []).append((p, q, mi))
    for uses in edges.values():
        if len(uses) == 1:
            p, q, mi = uses[0]
            bm.faces.new((vert(p, 0), vert(q, 0), vert(q, 1), vert(p, 1))).material_index = mi
    return bm


def plate(finish, part, mats, polys, axis, lo, hi, collide=True):
    return finish(part, plate_bm(polys, axis, lo, hi), mats, collide=collide)


def half_disc(finish, part, mat, xc, zc, r, y_lo, y_hi, segments=12, collide=False):
    """A half-disc standing on its diameter in an X-Z plane (a fan light, a
    sunburst's ground), from y_lo to y_hi."""
    pts = [(xc + r * math.cos(math.pi * k / segments), zc + r * math.sin(math.pi * k / segments)) for k in range(segments + 1)]
    return prism(finish, part, mat, pts, "y", y_lo, y_hi, collide=collide)


# --- posts, sweeps, sagging slabs ------------------------------------------------

def lathe_bm(cx, cy, rings, lean=(0.0, 0.0), bm=None):
    """A post as stacked rectangles (half x, half y, z) from the bottom up,
    each joined to the next by four faces. `lean` shears it (dx, dy per
    metre up): every ring stays level, so it is a sheared prism, never a
    tilted box."""
    if bm is None:
        bm = bmesh.new()
    z0 = rings[0][2]
    loops = []
    for hx, hy, z in rings:
        ox, oy = cx + lean[0] * (z - z0), cy + lean[1] * (z - z0)
        loops.append([bm.verts.new((ox + sx * hx, oy + sy * hy, z)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    bm.faces.new(list(reversed(loops[0])))
    for a, b in zip(loops, loops[1:]):
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bm.faces.new(loops[-1])
    return bm


def lathe(finish, part, mat, cx, cy, rings, lean=(0.0, 0.0), collide=True):
    return finish(part, lathe_bm(cx, cy, rings, lean=lean), [mat], collide=collide)


def turned_bm(cx, cy, rings, sides=8, bm=None):
    """A turned post or spindle as stacked level `sides`-gons (radius, z) from
    the bottom up, flats facing the axes, each joined to the next by `sides`
    faces: a lathe's beads, bellies and necks in a few rings, never a tilted
    solid. A radius of 0 ends it in a point."""
    if bm is None:
        bm = bmesh.new()
    loops = []
    for r, z in rings:
        if r <= 0.0:
            loops.append([bm.verts.new((cx, cy, z))])
            continue
        loops.append([bm.verts.new((cx + r * math.cos(math.tau * (k + 0.5) / sides),
                                    cy + r * math.sin(math.tau * (k + 0.5) / sides), z)) for k in range(sides)])
    if len(loops[0]) > 1:
        bm.faces.new(list(reversed(loops[0])))
    for a, b in zip(loops, loops[1:]):
        if len(b) == 1:
            for k in range(sides):
                bm.faces.new((a[k], a[(k + 1) % sides], b[0]))
        elif len(a) == 1:
            for k in range(sides):
                bm.faces.new((a[0], b[(k + 1) % sides], b[k]))
        else:
            for k in range(sides):
                bm.faces.new((a[k], a[(k + 1) % sides], b[(k + 1) % sides], b[k]))
    if len(loops[-1]) > 1:
        bm.faces.new(loops[-1])
    return bm


def turned(finish, part, mat, cx, cy, rings, sides=8, collide=True):
    return finish(part, turned_bm(cx, cy, rings, sides=sides), [mat], collide=collide)


def swept_bm(section, stations, bm=None):
    """A prism along Y whose (x, z) `section` drops by d at each station
    (y, d): every face is a parallelogram, so it stays planar while the
    whole section sags."""
    if bm is None:
        bm = bmesh.new()
    rings = [[bm.verts.new((x, y, z - d)) for x, z in section] for y, d in stations]
    n = len(section)
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    for a, b in zip(rings, rings[1:]):
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    return bm


def swept(finish, part, mat, section, stations, collide=True):
    return finish(part, swept_bm(section, stations), [mat], collide=collide)


def sag_at(stations, y):
    """How far a swept section has dropped at y, between its stations."""
    for (ya, da), (yb, db) in zip(stations, stations[1:]):
        if ya <= y <= yb:
            return da + (db - da) * (y - ya) / (yb - ya)
    return 0.0


def sweep_bm(path, section, closed=True, bm=None):
    """A (out, z) `section` swept along a plan `path` that runs
    counter-clockwise (outward is on its right), mitred at the corners:
    one piece round the house (closed) or round three sides of a porch."""
    if bm is None:
        bm = bmesh.new()
    n = len(path)

    def normal(i, j):
        (ax, ay), (bx, by) = path[i], path[j]
        length = math.hypot(bx - ax, by - ay)
        return ((by - ay) / length, -(bx - ax) / length)
    rings = []
    for i in range(n):
        ns = []
        if closed or i > 0:
            ns.append(normal((i - 1) % n, i))
        if closed or i < n - 1:
            ns.append(normal(i, (i + 1) % n))
        if len(ns) == 2:
            (ax, ay), (bx, by) = ns
            s = 1.0 + ax * bx + ay * by
            ox, oy = (ax + bx) / s, (ay + by) / s
        else:
            ox, oy = ns[0]
        px, py = path[i]
        rings.append([bm.verts.new((px + ox * o, py + oy * o, z)) for o, z in section])
    m = len(section)
    for i in (range(n) if closed else range(n - 1)):
        a, b = rings[i], rings[(i + 1) % n]
        for k in range(m):
            bm.faces.new((a[k], a[(k + 1) % m], b[(k + 1) % m], b[k]))
    if not closed:
        bm.faces.new(rings[0])
        bm.faces.new(list(reversed(rings[-1])))
    return bm


def sweep(finish, part, mat, path, section, closed=True, collide=True):
    return finish(part, sweep_bm(path, section, closed=closed), [mat], collide=collide)


# --- openings --------------------------------------------------------------------

def casing(finish, rng, part, mat, axis, face_at, outward, a0, a1, z0, z1, lights=1, sill=True,
           width=CASING, head=CASING_HEAD, mullion=MULLION, proud=CASING_PROUD, sunk=CASING_SUNK):
    """A window's or door's casing as one piece: jambs, head, sill and
    mullions round `lights` holes, `width` across (the head `head`), `proud`
    out of the wall's face and its back `sunk` into the wall, where the
    mullions lap 1 cm into the pane. The holes' edges lap 2 cm over the
    opening's; the outer corners are each nudged up to 1.2 cm, a touch
    off-square, and a door's feet stay on its sill line. The opening is
    (a0..a1, z0..z1) on a wall whose outer face is at `face_at` and faces
    `outward` (+1 or -1); `axis` is 'x' when its width runs along X."""
    def j(amount):
        return jit(rng, amount)
    h0, h1 = a0 + 0.02, a1 - 0.02
    zb = z0 + 0.02 if sill else z0 - 0.025     # a door's feet half a centimetre under its leaf's
    zt = z1 - 0.02
    A0, A1 = h0 - width, h1 + width
    Zt, Zb = zt + head, (zb - width if sill else zb)
    bl = (A0 + j(0.012), Zb + (j(0.012) if sill else 0.0))
    br = (A1 + j(0.012), Zb + (j(0.012) if sill else 0.0))
    tr, tl = (A1 + j(0.012), Zt + j(0.012)), (A0 + j(0.012), Zt + j(0.012))
    lw = (h1 - h0 - (lights - 1) * mullion) / lights
    holes = [(h0 + i * (lw + mullion), h0 + i * (lw + mullion) + lw) for i in range(lights)]
    polys = [([bl, (h0, zb), (h0, zt), tl], 0), ([(h1, zb), br, tr, (h1, zt)], 0),
             ([p for u0, u1 in holes for p in ((u0, zt), (u1, zt))] + [tr, tl], 0)]
    if sill:
        polys.append(([bl, br] + [p for u0, u1 in reversed(holes) for p in ((u1, zb), (u0, zb))], 0))
    for i in range(lights - 1):
        u1, u2 = holes[i][1], holes[i + 1][0]
        polys.append(([(u1, zb), (u2, zb), (u2, zt), (u1, zt)], 0))
    lo, hi = sorted((face_at - sunk * outward, face_at + proud * outward))
    return plate(finish, part, [mat], polys, "y" if axis == "x" else "x", lo, hi, collide=False)


# --- newels and railings ---------------------------------------------------------

def newel_post(finish, rng, part, mat, cx, cy, z_floor, rail_h=RAIL_H, size=NEWEL):
    """A fat newel, `size` square, centred on (cx, cy): the post 2 cm into
    what it stands on, a fat cap flaring out over it, a neck and a squared
    diamond knob (cap and knob sized for the standard 0.24). Each one's cap,
    knob and lean differ by a centimetre or two."""
    def j(amount):
        return jit(rng, amount)
    h = size / 2
    zc = z_floor + rail_h + 0.06 + j(0.015)       # where the post flares into its cap, over the rail
    ct = zc + 0.11 + j(0.012)
    cap = 0.17 + j(0.012)
    knob = 0.115 + j(0.012)
    rings = [(h, h, z_floor - 0.02), (h, h, zc), (cap, cap, zc + 0.03), (cap, cap, ct),
             (0.07, 0.07, ct + 0.04), (knob, knob, ct + 0.12 + j(0.015)), (0.03, 0.03, ct + 0.27 + j(0.02))]
    return lathe(finish, part, mat, cx, cy, rings, lean=(j(0.01), j(0.01)))


def spaced(p0, p1, pitch=BALUSTER_PITCH):
    """Baluster centres evenly between two faces p0 < p1, about `pitch` apart."""
    n = max(0, round((p1 - p0) / pitch) - 1)
    return [p0 + (p1 - p0) * (k + 1) / (n + 1) for k in range(n)]


def comb(finish, part, mat, axis, at, bottom, zb1, zt, centres, baluster=BALUSTER):
    """A railing's bottom rail and its square balusters as one piece:
    `bottom` is the rail's underside from its low end to its high end
    along the run (a for `axis` 'x' is x), zb1(a) the rail's top, zt(a)
    the balusters' tops (inside the top rail), `baluster` square, centred
    on the line `at` across the run."""
    w = baluster
    a0, a1 = bottom[0][0], bottom[-1][0]
    top = [(a1, zb1(a1))]
    for c in sorted(centres, reverse=True):
        top += [(c + w / 2, zb1(c + w / 2)), (c - w / 2, zb1(c - w / 2))]
    top.append((a0, zb1(a0)))
    polys = [(list(bottom) + top, 0)]
    for c in centres:
        l, r = c - w / 2, c + w / 2
        polys.append(([(l, zb1(l)), (r, zb1(r)), (r, zt(r)), (l, zt(l))], 0))
    return plate(finish, part, [mat], polys, "y" if axis == "x" else "x", at - w / 2, at + w / 2)


def top_rail(finish, part, mat, axis, at, a0, a1, under, cap_w=CAP_W, cap_h=CAP_H):
    """The fat top rail, `cap_w` wide and `cap_h` tall over under(a), which
    sags at the middle: two pieces of one plate."""
    am = (a0 + a1) / 2
    polys = [([(a0, under(a0)), (am, under(am)), (am, under(am) + cap_h), (a0, under(a0) + cap_h)], 0),
             ([(am, under(am)), (a1, under(a1)), (a1, under(a1) + cap_h), (am, under(am) + cap_h)], 0)]
    return plate(finish, part, [mat], polys, "y" if axis == "x" else "x", at - cap_w / 2, at + cap_w / 2)


def straight_rail(finish, rng, name, mat, axis, at, a0, a1, open0, open1, z_floor, rail_h=RAIL_H):
    """A level railing between two newels (or a newel and a wall): the comb
    of bottom rail and square balusters at BALUSTER_PITCH, its ends inside
    the newels (a0..a1), and the fat top rail over it, sagging 1-2 cm at the
    middle as a hand-set rail does. `open0..open1` is the clear span."""
    sag = rng.uniform(0.01, 0.02)
    am, half = (a0 + a1) / 2, (a1 - a0) / 2
    base = z_floor + rail_h + 0.02 - CAP_H

    def under(a):
        return base - sag * (1 - abs(a - am) / half)
    comb(finish, name, mat, axis, at, [(a0, z_floor - 0.015), (a1, z_floor - 0.015)],
         lambda a: z_floor + RAIL_BOTTOM, lambda a: under(a) + 0.02, spaced(open0, open1))
    top_rail(finish, f"{name}_top", mat, axis, at, a0 + 0.013, a1 - 0.013, under)


# --- stairs ------------------------------------------------------------------------

def flight(finish, prefix, mat, x0, x1, y_edge, out, z_top, risers, grade, below):
    """A straight flight of `risers` chunky risers at `grade` (riser over
    going) down from a deck's edge at `y_edge`, outward in `out` (-1 toward
    the street), x0..x1 wide, by the park's stair rule: the treads one
    stepped block of scenery 2 cm into the deck, the narrow colliding ramp
    on the nosing line, no nosing strips (a stringer rail covers the treads'
    ends). Feet go `below` under the ground. Returns (n, riser, going)."""
    n = risers
    riser = z_top / n
    going = riser / grade

    def y(s):
        return y_edge + out * s
    profile = [(y(n * going), -below)]
    for k in range(1, n):
        profile += [(y(n * going - (k - 1) * going), k * riser), (y(n * going - k * going), k * riser)]
    profile += [(y(-0.02), (n - 1) * riser), (y(-0.02), -below)]
    prism(finish, f"{prefix}_treads", mat, profile, "x", x0, x1, collide=False)
    ramp = [(y(n * going + 0.05), -below - 0.02), (y(n * going), 0.0), (y(0.0), z_top), (y(-0.06), -below - 0.02)]
    prism(finish, f"{prefix}_ramp", mat, ramp, "x", x0 + 0.10, x1 - 0.10)
    return n, riser, going


def stair_rails(finish, rng, prefix, mat, x_ats, y_edge, out, z_top, n, riser, going, rail_h=RAIL_H):
    """A flight's railings, one per (tag, x) in `x_ats`: a fat newel on the
    deck and one on the ground, and between them a fat stringer over the
    treads' ends (it rises STRINGER[1] over the nosing line and hangs
    STRINGER[0] under it, down to the ground line) carrying the square
    balusters, under the sagging top rail. n, riser and going are the
    flight's, as `flight` returns them."""
    slope = riser / going

    def nose(y):
        return z_top - (y - y_edge) * out * slope
    s_top = -(0.03 + NEWEL / 2)
    s_foot = n * going + 0.03 + NEWEL / 2
    drop, rise = STRINGER
    yk = y_edge + out * (z_top - drop + 0.06) / slope     # the stringer's underside meets the ground line
    for tag, x_at in x_ats:
        newel_post(finish, rng, f"{prefix}_{tag}_newel_top", mat, x_at, y_edge + out * s_top, z_top, rail_h=rail_h)
        newel_post(finish, rng, f"{prefix}_{tag}_newel_foot", mat, x_at, y_edge + out * s_foot, 0.0, rail_h=rail_h)
        ya, yb = sorted((y_edge + out * (s_top + 0.055), y_edge + out * (s_foot - 0.055)))
        bottom = [(ya, max(nose(ya) - drop, -0.06))]
        if ya < yk < yb:
            bottom.append((yk, -0.06))
        bottom.append((yb, max(nose(yb) - drop, -0.06)))
        sag = rng.uniform(0.01, 0.02)
        ym, half = (ya + yb) / 2, (yb - ya) / 2

        def cap_under(y, sag=sag, ym=ym, half=half):
            return nose(y) + rail_h + 0.02 - CAP_H - sag * (1 - abs(y - ym) / half)
        o0, o1 = sorted((y_edge + out * (s_top + NEWEL / 2), y_edge + out * (s_foot - NEWEL / 2)))
        comb(finish, f"{prefix}_{tag}", mat, "y", x_at, bottom, lambda y: nose(y) + rise,
             lambda y, cu=cap_under: cu(y) + 0.02, spaced(o0, o1))
        top_rail(finish, f"{prefix}_{tag}_top", mat, "y", x_at, ya + 0.013, yb - 0.013, cap_under)


# --- bargeboards -----------------------------------------------------------------------

def barge(finish, rng, part, mats, profile, knees, r_end, xc, y_rake, out, board, band, pendants, proud=BARGE_PROUD):
    """A bargeboard as one piece, a board over a sawn band (`mats`: the
    board's and the band's), on a rake whose top is profile(r) at r from
    the ridge line xc, both sides of it: its top 2 cm under the roof's top,
    its back lapped 2 cm into the rake's end at `y_rake`, `proud` out of it
    (`out` is -1 at the front, +1 at the back), bending at the profile's
    `knees` (a bell-cast kick). `board` and `band` are their depths under
    the top. A few big pointed drops hang from the band at `pendants`
    (fractions of the first knee, or of r_end without one), as the
    Victorian photo's do, each a little different in width and depth, as
    sawn by hand."""
    def j(amount):
        return jit(rng, amount)
    reach = knees[0] if knees else r_end
    polys = []

    def T(r):
        return profile(r) - 0.02

    def M(r):
        return T(r) - board

    def B(r):
        return M(r) - band
    stops = [0.0] + list(knees) + [r_end]
    for s in (1, -1):
        def X(p):
            return (xc + s * p[0], p[1])
        for ra, rb in zip(stops, stops[1:]):
            polys.append(([X(p) for p in ((ra, M(ra)), (rb, M(rb)), (rb, T(rb)), (ra, T(ra)))], 0))
            drops = []
            for f in pendants:
                c = f * reach + j(0.08)
                half, d = 0.17 + j(0.025), 0.40 + j(0.05)
                if ra + 0.10 <= c - half and c + half <= rb - 0.10:
                    drops.append((c - half, c, c + half, d))
            edge = [(ra, B(ra))]
            for t0, tc, t1, d in drops:
                edge += [(t0, B(t0)), (t1, B(t1))]
                # a pointed drop: shoulders, a waist, the point
                polys.append(([X(p) for p in ((t0, B(t0)), (t0 + 0.04, B(t0 + 0.04) - 0.40 * d),
                                              (tc - 0.06, B(tc - 0.06) - 0.66 * d), (tc, B(tc) - d),
                                              (tc + 0.06, B(tc + 0.06) - 0.66 * d), (t1 - 0.04, B(t1 - 0.04) - 0.40 * d),
                                              (t1, B(t1)))], 1))
            edge += [(rb, B(rb)), (rb, M(rb)), (ra, M(ra))]
            polys.append(([X(p) for p in edge], 1))
    lo, hi = sorted((y_rake - out * 0.02, y_rake + out * proud))
    return plate(finish, part, mats, polys, "y", lo, hi, collide=False)


# --- the bell-cast roof ------------------------------------------------------------------

def sag_stations(y0, y1, sag):
    """A roof's ridge and eaves dipping between its rakes at y0 and y1: none
    at the rakes, `sag` at the middle, three quarters of it halfway out, a
    hand-built roof and not a ruled one. The whole section drops, so every
    face of a swept slab stays planar."""
    ym = (y0 + y1) / 2
    return [(y0, 0.0), ((y0 + ym) / 2, 0.75 * sag), (ym, sag), ((ym + y1) / 2, 0.75 * sag), (y1, 0.0)]


class BellRoof:
    """A gable roof the standard's way, the heavy part of the house (World of
    Warcraft's lesson): a thick main slab, a shallower bell-cast kick at each
    eave lapped under it, a ridge roll, all sagging between the rakes. Built
    by `bell_roof`; what it keeps is what the bargeboards, the shingle grid
    and the vents read. Distances across are r, from the ridge line xc.

        tan, vt     the main pitch's tangent, the slab's vertical thickness
        rt          the ridge's top (before the sag)
        r_k         where the kick leaves the main slab's top, past the wall
        r_in, r_out the kick's inner end (under the main slab) and its eave
        stations    the sag, as swept() takes it"""

    def __init__(self, xc, half, eave, pitch, slab, y0, y1, sag, kick_at, kick_deg, kick_t, kick_in, eave_over):
        self.xc, self.half, self.eave, self.pitch = xc, half, eave, pitch
        self.y0, self.y1 = y0, y1
        self.tan = math.tan(pitch)
        self.vt = slab / math.cos(pitch)
        self.rt = eave + half * self.tan + self.vt
        self.r_k = half + kick_at
        self.kick_pitch = math.radians(kick_deg)
        self.t_k = math.tan(self.kick_pitch)
        self.k_z = eave + self.vt - kick_at * self.tan    # the kick's top where it leaves the main slab's
        self.kick_t = kick_t
        self.r_in, self.r_out = half - kick_in, half + eave_over
        self.stations = sag_stations(y0, y1, sag)

    def under(self, x):
        """The main slab's underside over x."""
        return self.eave + (self.half - abs(x - self.xc)) * self.tan

    def top(self, x):
        """The main slab's top over x (before the sag)."""
        return self.rt - abs(x - self.xc) * self.tan

    def kick_top(self, r):
        return self.k_z - (r - self.r_k) * self.t_k

    def profile(self, r):
        """The roof's top at r across from the ridge, the bend at r_k included:
        what a bargeboard follows."""
        return self.rt - r * self.tan if r <= self.r_k else self.kick_top(r)

    def slope(self, s, avoid=()):
        """The main slab's face on the side `s` as a shingle-grid slope (see
        the module docstring), `avoid` the boxes a tab keeps off (a chimney)."""
        rt, tan, stations = self.rt, self.tan, self.stations
        return dict(s=s, xc=self.xc, theta=self.pitch, surf=lambda r, y: rt - r * tan - sag_at(stations, y),
                    r=(0.32, self.r_k - 0.03), y=(self.y0 + 0.03, self.y1 - 0.03), avoid=list(avoid))

    def kick_slope(self, s):
        """The kick's face on the side `s`, as a shingle-grid slope."""
        stations = self.stations
        return dict(s=s, xc=self.xc, theta=self.kick_pitch, surf=lambda r, y: self.kick_top(r) - sag_at(stations, y),
                    r=(self.r_k + 0.03, self.r_out + 0.04), y=(self.y0 + 0.03, self.y1 - 0.03))


def bell_roof(finish, mat, xc, half, eave, pitch, slab, y0, y1, sag=0.05, kick_at=0.10, kick_deg=27.0, kick_t=0.24,
              kick_in=0.35, eave_over=0.75, ridge=0.24, part="roof", ridge_part="ridge_cap"):
    """The bell-cast gable roof over walls `half` either side of the ridge
    line xc with their eave at `eave`, from rake to rake (y0..y1): the main
    slab `slab` thick at `pitch` (radians), ending 2 cm past where the kick
    leaves its top, `kick_at` past the wall, out of sight under the kick; the
    kick, a second slab at `kick_deg` and `kick_t` deep (vertical), from
    `kick_in` inside the wall line, lapped under the main one, to a
    `eave_over` eave, 3 cm past each rake; and a ridge roll `ridge` either
    side, sitting on the slopes, not a plank floating over them. All of it
    sags `sag` at mid-length. Parts `part`, `part`_kick_e and _w, and
    `ridge_part`; returns the BellRoof."""
    roof = BellRoof(xc, half, eave, pitch, slab, y0, y1, sag, kick_at, kick_deg, kick_t, kick_in, eave_over)
    stations, vt, under = roof.stations, roof.vt, roof.under
    x_end = roof.r_k + 0.02          # the main slab ends 2 cm under the kick's top, out of sight
    section = [(xc - x_end, under(xc - x_end)), (xc, under(xc)), (xc + x_end, under(xc + x_end)),
               (xc + x_end, under(xc + x_end) + vt), (xc, under(xc) + vt), (xc - x_end, under(xc - x_end) + vt)]
    swept(finish, part, mat, section, stations)
    # the kick: a second, shallower slab from inside the wall line, lapped
    # under the main one, whose top it leaves kick_at past the wall
    r_in, r_out, kick_top = roof.r_in, roof.r_out, roof.kick_top
    k_stations = [(y0 - 0.03, 0.0)] + stations[1:-1] + [(y1 + 0.03, 0.0)]
    for tag, s in (("e", 1), ("w", -1)):
        swept(finish, f"{part}_kick_{tag}", mat, [(xc + s * r_in, kick_top(r_in)), (xc + s * r_out, kick_top(r_out)),
                                                 (xc + s * r_out, kick_top(r_out) - kick_t),
                                                 (xc + s * r_in, kick_top(r_in) - kick_t)], k_stations)
    rt, top, h = roof.rt, roof.top, ridge
    swept(finish, ridge_part, mat, [(xc - h, top(xc - h) - 0.03), (xc, rt - 0.03), (xc + h, top(xc + h) - 0.03),
                                    (xc + h, top(xc + h) + 0.07), (xc, rt + 0.08), (xc - h, top(xc - h) + 0.07)],
          [(y0 - 0.02, 0.0)] + stations[1:-1] + [(y1 + 0.02, 0.0)], collide=False)
    return roof


# --- shaped brackets, timber posts, stoop parapets ---------------------------------------

def shaped_bracket(finish, rng, part, mat, axis, at, face, out, z_top, reach, drop, width=0.18, foot=0.12, band=0.14):
    """A knee bracket with a cove sawn out of its face and a short drop at its
    foot, each one a little different (the Victorian's balcony brackets): its
    back 4 cm into the wall whose face is at `face`, reaching `reach` out
    along `axis` ('y' or 'x') in the direction `out` (+1 or -1), its top at
    z_top lapped into what it carries, `drop` deep, `width` thick, centred on
    `at` across. Its top band is `band` deep and its foot `foot` wide; the cove
    is a quarter ellipse between them."""
    def j(amount):
        return jit(rng, amount)
    reach = reach + j(0.03)
    drop = drop + j(0.05)
    ft = foot + j(0.015)
    rx, rz = reach - ft, drop - foot - band + j(0.03)
    cz = -band - rz
    pts = [(-0.04, 0.0), (reach, 0.0), (reach, -band)]
    pts += [(reach + rx * math.cos(math.radians(a)), cz + rz * math.sin(math.radians(a))) for a in (112.5, 135.0, 157.5)]
    pts += [(ft, cz), (ft, -drop + 0.05), (ft - 0.06, -drop), (-0.04, -drop)]
    half = width / 2 + j(0.01)
    at += j(0.012)
    return prism(finish, part, mat, [(face + out * s, z_top + dz) for s, dz in pts], "x" if axis == "y" else "y",
                 at - half, at + half, collide=False)


def timber_post(finish, rng, part, mat, cx, cy, z_foot, base, z_eave, z_top, size=0.26, block=0.17, collar=0.165):
    """A chunky timber post, `size` square, centred on (cx, cy): a base block
    (`block` its half-size) from z_foot to base[0], stepping in to the shaft
    by base[1], a collar (`collar` its half-size) from 0.28 to 0.13 under
    z_eave, the shaft on up to z_top, into what it carries. The block, collar
    and steps differ by a centimetre or two."""
    def j(amount):
        return jit(rng, amount)
    sh, blk, col = size / 2, block + j(0.01), collar + j(0.008)
    return lathe(finish, part, mat, cx, cy,
                 [(blk, blk, z_foot), (blk, blk, base[0] + j(0.03)), (sh, sh, base[1] + j(0.02)), (sh, sh, z_eave - 0.32),
                  (col, col, z_eave - 0.28), (col, col, z_eave - 0.13), (sh, sh, z_eave - 0.10), (sh, sh, z_top)])


def stoop_parapets(finish, rng, prefix, mat, x_ats, y_edge, out, z_floor, n, riser, going, s_wall, rail_h=RAIL_H,
                   width=0.14, cap_w=0.20):
    """Solid parapets beside a flight `flight` built (its n, riser and going),
    down from a deck's edge at y_edge outward in `out`, one per (tag, x) in
    `x_ats`: each one plain piece from `s_wall` (behind the edge, inside the
    wall) along the deck and down the flight, its underside on the
    stringer's line to the ground, `width` thick, under a fat cap `cap_w`
    wide that sags a centimetre or so down the flight, and a fat pier (a
    newel) at its foot. Rail heights over the deck and the nosing line are
    `rail_h`. An `s_wall` short of where the stringer's underside rises to
    the deck (a parapet beginning just behind the edge, beside a door)
    starts on the stringer's line, inside the deck."""
    slope = riser / going
    drop = STRINGER[0]
    s2 = -(drop - 0.02) / slope              # the underside rises to the deck's top here
    s3 = (z_floor - drop + 0.06) / slope     # and meets the ground line here
    s_end = n * going + 0.03 + NEWEL / 2     # the pier's centre

    def Y(s):
        return y_edge + out * s

    def rail(s):
        return z_floor + rail_h if s <= 0 else z_floor - s * slope + rail_h
    for tag, x_at in x_ats:
        pt = rail(0.0) - CAP_H + 0.04          # the parapet's top, 2 cm into its cap
        if s_wall < s2:
            polys = [([(Y(s_wall), z_floor - 0.02), (Y(s2), z_floor - 0.02), (Y(s2), pt), (Y(s_wall), pt)], 0),
                     ([(Y(s2), z_floor - 0.02), (Y(s3), -0.06), (Y(s_end), -0.06), (Y(s_end), rail(s_end) - CAP_H + 0.04),
                       (Y(0.0), pt), (Y(s2), pt)], 0)]
        else:
            zu = z_floor - s_wall * slope - drop    # the stringer's line carried back, inside the deck
            polys = [([(Y(s_wall), zu), (Y(s3), -0.06), (Y(s_end), -0.06), (Y(s_end), rail(s_end) - CAP_H + 0.04),
                       (Y(0.0), pt), (Y(s_wall), pt)], 0)]
        plate(finish, f"{prefix}_parapet_{tag}", [mat], polys, "x", x_at - width / 2, x_at + width / 2)
        sag = rng.uniform(0.01, 0.015)
        sm = s_end / 2

        def cu(s, sag=sag):
            return rail(s) + 0.02 - CAP_H - (sag * (1 - abs(s - sm) / sm) if s > 0 else 0.0)
        sa, se = s_wall + 0.01, s_end - 0.013     # the cap's ends off the parapet's, inside the wall and the pier
        cap = [([(Y(sa), cu(sa)), (Y(0.0), cu(0.0)), (Y(0.0), cu(0.0) + CAP_H), (Y(sa), cu(sa) + CAP_H)], 0),
               ([(Y(0.0), cu(0.0)), (Y(sm), cu(sm)), (Y(sm), cu(sm) + CAP_H), (Y(0.0), cu(0.0) + CAP_H)], 0),
               ([(Y(sm), cu(sm)), (Y(se), cu(se)), (Y(se), cu(se) + CAP_H), (Y(sm), cu(sm) + CAP_H)], 0)]
        plate(finish, f"{prefix}_parapet_{tag}_cap", [mat], cap, "x", x_at - cap_w / 2, x_at + cap_w / 2)
        newel_post(finish, rng, f"{prefix}_pier_{tag}", mat, x_at, Y(s_end), 0.0, rail_h=rail_h)


# --- shingles ------------------------------------------------------------------------

def shingle_stagger(k):
    """Course k's slide, in tabs: the golden fraction, never repeating."""
    return (k * STAGGER) % 1.0


def slope_s(slope, r, y):
    """The distance down the slope of the slab's face at (r, y): the world
    position on the face dotted with the slope's downhill direction."""
    sg, th = slope["s"], slope["theta"]
    return (slope["xc"] + sg * r) * sg * math.cos(th) - slope["surf"](r, y) * math.sin(th)


def r_at_s(slope, target, y):
    """The r whose face point lies `target` down the slope (a plane, so the
    distance is linear in r)."""
    f0, f1 = slope_s(slope, 0.0, y), slope_s(slope, 1.0, y)
    return (target - f0) / (f1 - f0)


def shingle_tab(bm, slope, r, y, w, L, turn_deg, lift_deg):
    """One chunky shingle tab lying on a slope, wedged like an axe head (her
    "they need to be thin at the top", "like an ax head", 2026-10-04): thin
    at its head (up the slope), just under the slab's face so it grows out of
    the roof, thickening evenly down to its butt (parallel to the eave, turned
    a hair at most), which stands TAB_TOP proud plus its lift of a degree or
    two; its underside sunk all along. Returns False, building nothing, if
    any corner would leave the slope's region or touch what it must avoid."""
    s, th = slope["s"], slope["theta"]
    ct, st = math.cos(th), math.sin(th)
    c, sn = math.cos(math.radians(turn_deg)), math.sin(math.radians(turn_deg))

    def rot(u, v):
        return u * c - v * sn, u * sn + v * c
    for u, v in ((-w / 2, -L / 2), (w / 2, -L / 2), (-w / 2, L / 2), (w / 2, L / 2)):
        du, dv = rot(u, v)
        rr, yy = r + dv * ct, y + du
        if not (slope["r"][0] <= rr <= slope["r"][1] and slope["y"][0] <= yy <= slope["y"][1]):
            return False
        if any(r0 <= rr <= r1 and y0 <= yy <= y1 for r0, r1, y0, y1 in slope.get("avoid", ())):
            return False
    U = Vector((0.0, 1.0, 0.0))
    Dn = Vector((s * ct, 0.0, -st))
    N = Vector((s * st, 0.0, ct))
    O = Vector((slope["xc"] + s * r, y, slope["surf"](r, y)))
    rise = L * math.tan(math.radians(lift_deg))
    sink, top, edge = TAB_SINK, TAB_TOP, TAB_EDGE   # the butt grown with the tab (0.034 at the old size)
    # the section from the head down to the butt: (v, n); the head's thin
    # edge sits 4 mm under the slab's face, so the wedge never shares its plane
    section = [(-L / 2, -sink), (-L / 2, -edge), (L / 2, top + rise), (L / 2, -sink - 0.004)]

    def at(u, v, n):
        du, dv = rot(u, v)
        return O + U * du + Dn * dv + N * n
    a = [bm.verts.new(at(-w / 2, v, n)) for v, n in section]
    b = [bm.verts.new(at(w / 2, v, n)) for v, n in section]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    for k in range(4):
        bm.faces.new((a[k], b[k], b[(k + 1) % 4], a[(k + 1) % 4]))
    slope.setdefault("placed", []).append((r, y, w, L))    # for the vents to keep clear of
    return True


def shingle_cluster(rng, bm, slope, r_c, y_c, max_courses=3):
    """A little patch of lifted shingles, as the hedges' leaf clusters: around
    (r_c, y_c), the course there and one or two above it, a run of one to
    three whole grid shingles in the lowest, fewer in each course up, so the
    patch mounds; 3 to 7 tabs, any that would leave the region dropped. Each
    tab is the painted shingle under it, lifted a degree or two at its butt
    and turned no more than half a degree. Built into `bm`; returns how many
    tabs it placed."""
    e, w, sg = SHINGLE_E, SHINGLE_W, slope["s"]
    k0 = math.floor(slope_s(slope, r_c, y_c) / e)       # the lowest course
    t_mid = -sg * y_c                                   # across, as the painting runs it
    half = rng.uniform(0.55, 0.95)
    cells = []
    for i in range(rng.randint(2, max_courses)):
        k = k0 - i                                      # up the slope, course by course
        f = shingle_stagger(k)
        mid = t_mid + rng.uniform(-0.15, 0.15)
        h = half * (1.0 - 0.35 * i)
        for j in range(math.floor((mid - h) / w + f), math.floor((mid + h) / w + f) + 1):
            tc = (j + 0.5 - f) * w
            if abs(tc - mid) <= h:
                cells.append((k, tc))
    placed = 0
    for k, tc in cells[:7]:
        y = -sg * tc
        r = r_at_s(slope, (k + 1) * e - SHINGLE_L / 2, y)
        placed += shingle_tab(bm, slope, r, y, w - SHINGLE_KEY, SHINGLE_L,
                              rng.uniform(-0.5, 0.5), rng.uniform(0.8, 2.5))
    return placed


def vent_pipe(finish, part, mats, slope, r, y, height, lean):
    """A little plumbing vent through a slope, cartoon-fat (about twice a real
    one): an octagonal boot sunk under the slope's low side and standing 6 cm
    over its high side, a 0.15 m pipe rising `height` over the face at its
    axis, and a fat rim at its top with the dark hole showing in it (`mats`:
    the pipe's and the hole's). Every ring level and sheared by `lean` (per
    metre up), never tilted."""
    sg, xc = slope["s"], slope["xc"]
    x = xc + sg * r
    surf = slope["surf"]

    def ring(bm, rad, z, z0):
        ox, oy = lean[0] * (z - z0), lean[1] * (z - z0)
        return [bm.verts.new((x + ox + rad * math.cos(math.radians(22.5 + 45 * k)),
                              y + oy + rad * math.sin(math.radians(22.5 + 45 * k)), z)) for k in range(8)]

    def solid(bm, rings, mat_top=0):
        loops = [ring(bm, rad, z, rings[0][1]) for rad, z in rings]
        bm.faces.new(list(reversed(loops[0])))
        for a, b in zip(loops, loops[1:]):
            for k in range(8):
                bm.faces.new((a[k], a[(k + 1) % 8], b[(k + 1) % 8], b[k]))
        bm.faces.new(loops[-1]).material_index = mat_top
    bm = bmesh.new()
    low = surf(r + 0.14, y) - 0.05                    # under the face at the boot's low side
    top = surf(r, y) + height
    solid(bm, [(0.14, low), (0.10, surf(r - 0.10, y) + 0.06)])           # the boot
    solid(bm, [(0.075, low + 0.01), (0.075, top - 0.025)], mat_top=1)    # the pipe, its top the dark hole
    # the rim: a fat collar round the pipe's top, open in the middle
    zr0, zr1 = top - 0.05, top
    outer0, outer1 = ring(bm, 0.095, zr0, low + 0.01), ring(bm, 0.095, zr1, low + 0.01)
    inner0, inner1 = ring(bm, 0.055, zr0, low + 0.01), ring(bm, 0.055, zr1, low + 0.01)
    for k in range(8):
        n = (k + 1) % 8
        bm.faces.new((outer0[k], outer0[n], outer1[n], outer1[k]))
        bm.faces.new((inner0[n], inner0[k], inner1[k], inner1[n]))
        bm.faces.new((outer1[k], outer1[n], inner1[n], inner1[k]))
        bm.faces.new((inner0[k], inner0[n], outer0[n], outer0[k]))
    return finish(part, bm, mats, collide=False)


# --- scattering clusters and vents over a bell-cast roof ---------------------------------

def roof_clusters(rng, bm, roof, avoid=None, scattered=3, gap=2.6):
    """Shingle clusters over a BellRoof's two main slopes and their kicks, as
    the hedges' leaf clusters lie: a few small patches, scattered, never
    banded, different on each slope, the slab between them the painted
    surface. On each slope, east then west: one at a rake (the front on the
    east slope, the back on the west), where its tabs stand up on the roof's
    edge; one on the kick, its lowest butts just over the eave's edge; then
    `scattered` more, `gap` apart and clear of `avoid` (per side s, boxes in
    r and y: a chimney). Built into `bm` from `rng` (a seed of their own, so
    the trim's hand never reshuffles the roof); returns (tabs, mains), the
    main slopes by side with the tabs they hold, for vents to keep clear of."""
    avoid = avoid or {}
    y0, y1, r_k = roof.y0, roof.y1, roof.r_k
    tabs = 0
    mains = {}
    for s in (1, -1):
        main = mains[s] = roof.slope(s, avoid.get(s, ()))
        kick = roof.kick_slope(s)
        ct = math.cos(roof.pitch)
        centres = []

        def free(r, y):
            return all(math.hypot((r - r2) / ct, y - y2) >= gap for r2, y2 in centres)
        r_c = rng.uniform(1.2, r_k - 0.7)
        y_c = (y0 + 0.62) if s > 0 else (y1 - 0.62)
        tabs += shingle_cluster(rng, bm, main, r_c, y_c)
        centres.append((r_c, y_c))
        y_c = rng.uniform(y0 + 1.2, y1 - 1.2)
        tabs += shingle_cluster(rng, bm, kick, r_k + 0.40, y_c, max_courses=2)
        centres.append((r_k + 0.40, y_c))
        placed, tries = 0, 0
        while placed < scattered and tries < 200:
            tries += 1
            r_c, y_c = rng.uniform(0.9, r_k - 0.5), rng.uniform(y0 + 0.8, y1 - 0.8)
            if not free(r_c, y_c) or any(r0 - 0.3 <= r_c <= r1 + 0.3 and q0 - 0.3 <= y_c <= q1 + 0.3 for r0, r1, q0, q1 in main["avoid"]):
                continue
            tabs += shingle_cluster(rng, bm, main, r_c, y_c)
            centres.append((r_c, y_c))
            placed += 1
    return tabs, mains


def roof_vents(finish, rng, mats, roof, mains, counts=((-1, 2), (1, 1)), part="roof_vent"):
    """A few little vent pipes on the back half of a BellRoof (`counts`: how
    many on each side s), each clear of the slope's `avoid` boxes and of every
    lifted shingle, 1.6 m apart; drawn after the clusters, so they never move
    them. `mats`: the pipe's and its hole's. Returns how many."""
    vents = 0
    ym = (roof.y0 + roof.y1) / 2
    for s, count in counts:
        main = mains[s]
        tries = 0
        spots = []
        while len(spots) < count and tries < 400:
            tries += 1
            r_v, y_v = rng.uniform(1.0, roof.r_k - 0.9), rng.uniform(ym + 0.6, roof.y1 - 1.0)
            if any(r0 - 0.35 <= r_v <= r1 + 0.35 and q0 - 0.35 <= y_v <= q1 + 0.35 for r0, r1, q0, q1 in main["avoid"]):
                continue
            if any(abs(r_v - r) <= L * math.cos(roof.pitch) / 2 + 0.30 and abs(y_v - y) <= w / 2 + 0.30
                   for r, y, w, L in main.get("placed", ())):
                continue
            if any(math.hypot(r_v - r2, y_v - y2) < 1.6 for r2, y2 in spots):
                continue
            spots.append((r_v, y_v))
        for r_v, y_v in spots:
            vent_pipe(finish, f"{part}_{vents}", mats, main, r_v, y_v, rng.uniform(0.40, 0.58),
                      (rng.uniform(-0.01, 0.01), rng.uniform(-0.01, 0.01)))
            vents += 1
    return vents
