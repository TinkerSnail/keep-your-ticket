"""The summary table: D1 and D2 (the regrade) first, then A, B and C (benches cut into today's hill)."""

import os

import ht_pil as G
from ht_site import PREFIX, RENDERS

ORDER = ("D1", "D2", "A", "B", "C")
HEAD = {"D1": "D1  regrade, all three legs streets", "D2": "D2  regrade, two streets, steps down",
        "A": "A  cut: her lines, all streets", "B": "B  cut: two streets, steps down", "C": "C  cut: streets, stepped lanes"}


def short(name):
    return (name.replace(" (street)", " street").replace(" (stepped lane)", " lane").replace("leg down (steps, switching back)", "steps down")
            .replace("leg down street", "leg down to J3"))


def is_d(r):
    return r["variant"].startswith("D")


def rows(V):
    def col(fd, fc):
        return tuple(fd(V[v]) if is_d(V[v]) else fc(V[v]) for v in ORDER)
    km = lambda m3: f"{m3 / 1000:.0f}k m³"
    on = lambda r: ", ".join([f"{short(k)} {p[-1]['s']:.0f} m" for k, p in r["profiles"].items() if "line" in k or "leg" in k]
                             + [f"{short(l['name'])} {l['run_m']:.0f} m" for l in r["lanes"]])
    grade = lambda r: ", ".join(f"{short(k).replace('street to the underpass', 'to underpass')} {x['pct']:.0f} %"
                                for k, x in r["max_grades"].items() if "steps" not in k)
    vk = lambda r: r["volumes"] if is_d(r) else r["volumes_1:1"]
    return [
        ("", *(HEAD[v] for v in ORDER)),
        ("meeting point (ground 72.7)", *col(lambda r: f"{r['meet_h']:.1f} m: ground lowered {r['lowered']['meeting_point_m']:.0f} m",
                                              lambda r: f"{r['meet_h']:.1f} m" + (", in a cut" if r["variant"] != "C" else ", on the hill"))),
        ("on her lines", *col(on, on)),
        ("steepest street grade", *col(grade, grade)),
        ("ground lowered, max/mean m", *col(lambda r: ", ".join(f"{short(k).replace(' to J3', '')} {x['max_m']:.0f}/{x['mean_m']:.0f}"
                                                               for k, x in r["lowered"].items() if k != "meeting_point_m"),
                                                lambda r: "the streets sit in cuts (see deepest cut)")),
        ("hill's top, 87.4 at (160, 630)", *col(lambda r: f"{r['summit']['there_after_m']:.0f} m there (down {r['summit']['drop_m']:.0f}); "
                                                          f"highest left {r['summit']['highest_in_box_after_m']:.0f} m",
                                                 lambda r: f"{r['summit']['there_after_m']:.0f} m there (down {r['summit']['drop_m']:.0f})")),
        ("cut / fill", *col(lambda r: f"{km(r['volumes']['cut_m3'])} / {km(r['volumes']['fill_m3'])} (fill only smooths)",
                            lambda r: f"{km(r['volumes_1:1']['cut_m3'])} / {km(r['volumes_1:1']['fill_m3'])}")),
        ("deepest cut", *col(lambda r: f"{vk(r)['deepest_cut_m']:.0f} m at ({vk(r)['deepest_cut_at'][0]:.0f}, {vk(r)['deepest_cut_at'][1]:.0f})",
                             lambda r: f"{vk(r)['deepest_cut_m']:.0f} m at ({vk(r)['deepest_cut_at'][0]:.0f}, {vk(r)['deepest_cut_at'][1]:.0f})")),
        ("footprint", *col(lambda r: f"{vk(r)['disturbed_m2'] / 1e4:.2f} ha", lambda r: f"{vk(r)['disturbed_m2'] / 1e4:.2f} ha")),
        ("ground steeper than 1:3", *col(lambda r: f"{r['slopes']['over_1_3_m2'] / 1e4:.2f} ha of {r['slopes']['regraded_m2'] / 1e4:.1f} "
                                                   f"({r['slopes']['over_1_3_at_rim_m2'] / 1e4:.2f} at the rim); steepest bank "
                                                   f"{100 * r['slopes']['steepest_inside']:.0f} %",
                                         lambda r: "cut faces planted at 1:1 above 4 m walls")),
        ("walls", *col(lambda r: f"lot terraces ≤ {r['lot_terrace_wall_max_m']:.1f} m; other steps ≤ {r['walls']['other']:.0f} m",
                       lambda r: f"{r['walls']['highest_wall_m']:.0f} m highest; {r['walls']['wall_over_4m_length_m']:.0f} m of it over 4 m")),
        ("cutting to the underpass", *col(lambda r: f"face beside it ≤ {r['cutting']['face_last_40m_m']:.0f} m (walls of {r['cutting']['before_walls_m']:.0f} m in {r['cutting']['before_on']})",
                                          lambda r: f"walls up to {r['walls']['portal_wall_highest_m']:.0f} m")),
        ("portal and verge walls", *col(lambda r: f"up to {r['walls']['verge']:.0f} m", lambda r: f"up to {r['walls']['verge_wall_highest_m']:.0f} m")),
        ("lots (8 x 7 m)", *col(lambda r: f"{r['lots']['total']} on low terraces, garages at the street",
                                lambda r: f"{r['lots']['total']}: {r['lots']['cut_pad']} cut pads, {r['lots']['lane']} on lanes (no car)")),
        ("skyline, Beach Road at the row", *col(*(2 * (lambda r: f"down {r['views']['beach_road_row']['skyline_max_drop_deg']:.1f}° over "
                                                                f"{r['views']['beach_road_row']['skyline_changed_over_deg']:.0f}° of bearing",)))),
        ("skyline, Second Street / V4", *col(*(2 * (lambda r: f"down {r['views']['second_street']['skyline_max_drop_deg']:.1f}° / "
                                                             f"{r['views']['V4']['skyline_max_drop_deg']:.1f}°",)))),
        ("new ground in view, Beach Road", *col(*(2 * (lambda r: f"{r['views']['beach_road_row']['visible_disturbed_m2'] / 1000:.1f}k m²",)))),
    ]


def table(R):
    rs = rows(R["variants"])
    widths = [250, 400, 400, 340, 340, 500]
    W, RH = sum(widths) + 40, 30
    img, dr = G.new(W, 60 + RH * len(rs) + 100)
    f, fb = G.font(13), G.font(14)
    dr.text((20, 14), "Hillside along her lines: regrade (D1, D2) against benches cut into today's hill (A, B, C). Heights over the sea; "
            "volumes on a 1 m grid of the master", fill=(10, 10, 10), font=G.font(17))
    for i, r in enumerate(rs):
        y = 50 + i * RH
        if i % 2 == 1:
            dr.rectangle([20, y - 4, W - 20, y + RH - 6], fill=(242, 242, 236))
        x = 20
        for c, w in zip(r, widths):
            dr.text((x + 6, y), str(c), fill=(10, 10, 10), font=fb if i == 0 or x == 20 else f)
            x += w
    y = 50 + RH * len(rs) + 8
    for k, line in enumerate((
            "D: her lines are ordinary streets; the hill round them is reshaped to one slope of at most 1:3, planted, blended into "
            "today's ground over 15 m; lots on low terraces; pass 10's terrace streets held on grade.",
            "A-C: 4 m walls at the back of lots, then planted 1:1; the street to the underpass a walled cutting. The underpass itself "
            "is not cut here (pass 13 measured it).",
            "The highway's strip keeps today's ground (hash-checked). Skylines are terrain only, from 1.6 m over the ground.")):
        dr.text((20, y + 22 * k), line, fill=(70, 70, 70), font=f)
    img.save(os.path.join(RENDERS, PREFIX + "table.png"))
    print("hillside_terraces: wrote table")
