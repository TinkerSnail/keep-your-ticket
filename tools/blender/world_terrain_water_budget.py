"""Water budget for the park's water network with Christina's two rulings (2026-10-01):
the big hill lakes K1 and L0 are MANAGED RESERVOIRS releasing wet-season water to the park
ponds through controlled outlets (no dry-season pumps), and the creeks are fed by rain on the
visible catchments PLUS snowmelt from far-away mountains OFF THE MAP (an assumption she made;
shown and parameterised here, LOW / MEDIUM / HIGH, to be confirmed, not a fact).

System Python only, proposal only, nothing touches the master.

    python3 tools/blender/world_terrain_water_budget.py --out <renders>
      writes network2_budget.json, network2_assumptions.png, network2_year_of_water.png,
      network2_reaches_table.png, network2_schematic.png
"""
import json
import math
import os
import sys

HYDRO = None
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
SEC = [d * 86400 for d in DAYS]

# ---------------------------------------------------------------- assumptions (to confirm)
# Southern California coast-range setting at latitude 32.75: the mapped range crest is 294 m; the
# snow source is a higher range beyond the mapped land (as the Lagunas / Palomar / San Jacinto
# carry winter snow at 1,500-2,500 m and melt out by May-June). Yields are water reaching the
# creek heads per year per unit of off-map catchment (snow water + rain at elevation, after
# losses), split 60 % to the north valley K and 40 % to the south valley L.
CASES = {  # Christina: "here in CA snow melt is a big deal": LOW is the coast-range-like case; MEDIUM and HIGH (deep snowpack, Sierra-like) are the likelier ones
    "LOW": {"area_km2": 2.0, "band_m": "1,200-1,800", "yield_mm": 150, "melt_mm_day": 15, "spring_factor": 0.4, "note": "coast-range snowfall only: thin pack, melt out by May, little summer baseflow"},
    "MEDIUM": {"area_km2": 15.0, "band_m": "2,000-3,000", "yield_mm": 400, "melt_mm_day": 25, "spring_factor": 1.0, "note": "a high range with a deep pack: late-spring peak, recession into August, real summer baseflow (likely)"},
    "HIGH": {"area_km2": 40.0, "band_m": "2,200-3,400", "yield_mm": 600, "melt_mm_day": 35, "spring_factor": 2.0, "note": "Sierra-like: a large snow catchment, melt through July, strong year-round baseflow"},
    "CHOSEN": {"area_km2": 34.0, "band_m": "2,000-3,200", "yield_mm": 570, "melt_mm_day": 30, "spring_factor": 1.0, "note": "Christina 2026-10-01: K the beefy river (24 km2 at 600 mm, melt 35 mm/day), L a strong medium-high creek (10 km2 at 500 mm, melt 30 mm/day); springs MEDIUM",
               "per_system": {"K": {"area_km2": 24.0, "yield_mm": 600, "melt_mm_day": 35}, "L": {"area_km2": 10.0, "yield_mm": 500, "melt_mm_day": 30}}},
}
# groundwater: rain on the hills recharges an aquifer in the wet season; springs lag the rain by 2-3 months and keep flowing into summer
RECHARGE_AREA_HA = 300.0        # the range ring around the park plus the two valleys (assumed)
RECHARGE_FRACTION = 0.25        # of the 300 mm rain reaching the aquifer (MEDIUM; LOW 0.1, HIGH 0.5 via spring_factor)
SPRING_FRAC = [0.09, 0.11, 0.13, 0.13, 0.11, 0.09, 0.07, 0.06, 0.05, 0.05, 0.05, 0.06]   # springs: lagged, damped rain
SPRINGS = [  # name, (x, z), MEDIUM flow L/s, system it feeds, what it feeds, plan language
    ("S1 north-ridge toe", (150, -262), 1.5, "K", "the shelf channel K-5 and P3", "a seep line at the foot of the +17 ridge, the shelf's own spring"),
    ("S2 corner-spur foot", (192, -234), 1.0, "K", "the corner cascade K-4", "the take-off's pop-out reads as a spring bursting from the spur"),
    ("S3 Grove-mound foot", (-30, -132), 1.0, "K", "P2 directly", "the Grove duct's pop-up reads as a spring at the mound's foot: a spring-fed Grove pond"),
    ("S4 bluff-notch seeps", (-50, -148), 0.5, "K", "the notch cascade K-7", "weeping bluff face at the notch, ferns and moss"),
    ("S5 shore-band bluff foot", (-58, 40), 1.0, "CC", "Coastal Creek and the rain pond", "coastal bluff seeps along the Boardwalk's bluff foot (real in California)"),
    ("S6 Kiddieland spur foot", (190, 152), 1.0, "L", "P1a directly", "the fork culvert's pop-out reads as a spring at the spur's foot"),
    ("S7 slough floor", (120, 206), 1.0, "lobe", "the NE lobe", "marsh springs on the slough floor"),
    ("S8 approach-valley floor", (175, 305), 1.0, "lobe", "the east body", "seeps on the valley floor under the arrival bridge"),
    ("S9 D3 saucer", (-18, 176), 0.3, "L", "D3 directly", "a small spring in the entrance garden's low: the pop-up pond explained"),
    ("S10 D4/D5 saucers", (140, 160), 0.6, "L", "P1a / P1b", "seeps in the Kiddieland lows"),
    ("S11 beach-front bluff seeps", (300, 1000), 2.0, "coast", "the beach front (outside the network)", "coastal bluff seeps between z 600 and 2,200"),
    ("S12 Headland cove toe", (-150, -300), 0.5, "cove", "the north cove", "a seep at the knoll's foot"),
]
SPLIT_K, SPLIT_L = 0.6, 0.4
# monthly fractions of the yearly snow-fed flow: spring peak, recession, small perennial baseflow
SNOW_FRAC = [0.04, 0.05, 0.08, 0.14, 0.20, 0.17, 0.11, 0.07, 0.045, 0.035, 0.03, 0.03]   # deep-pack hydrograph: late-spring peak, long recession, perennial baseflow
# rain on the visible catchments: 300 mm/yr, runoff coefficient 0.3 (hills) / 0.5 (park); winter fractions
RAIN_MM, C_HILLS, C_PARK = 300.0, 0.3, 0.5
RAIN_FRAC = [0.22, 0.22, 0.15, 0.06, 0.02, 0.005, 0.005, 0.005, 0.01, 0.03, 0.095, 0.18]
EVAP_MM = 1400.0
EVAP_FRAC = [0.04, 0.05, 0.07, 0.09, 0.11, 0.12, 0.13, 0.13, 0.10, 0.08, 0.05, 0.03]
VISIBLE = {"K": {"total_ha": 70.0, "above_lake_ha": 25.0}, "L": {"total_ha": 47.0, "above_lake_ha": 21.0}}
# stage - volume - area of the two reservoirs from the master's mesh (world_terrain_hydrology.py basins)
STAGE = {
    "K1": {"brim": 79.7, "table": [(57.3, 0, 0.0), (59.3, 1851, 0.20), (62.3, 12317, 0.52), (67.3, 53599, 1.18), (78.1, 278070, 3.14), (79.7, 330000, 3.45)]},
    "L0": {"brim": 92.0, "table": [(61.6, 0, 0.0), (63.6, 2314, 0.21), (66.6, 12240, 0.46), (71.6, 46989, 0.95), (90.2, 499068, 4.02), (92.0, 570000, 4.28)]},
}
OUTLET = {"K1": {"invert": 74.0, "device": "0.6 m sluice valve in a tower at the spill saddle (520,-410), outfall into the north creek"},
          "L0": {"invert": 86.0, "device": "0.6 m sluice valve in a tower at the spill (660,110), outfall into the south creek"}}
# the park ponds served by each reservoir (area ha) and the circulation flow wanted through each chain
PONDS = {"K": {"P3": 0.165, "P2": 0.12}, "L": {"P1a": 0.09, "P1b": 0.141, "D3": 0.076}}
CIRC_L_S = {"K": 3.0, "L": 2.0}       # continuous flow through each chain, May-Nov, for freshness (design choice)
SEEP_MM_DAY = 2.0                     # pond seepage assumption (lined ponds would be 0)
# regulated take-offs (sluice settings) and structures
STRUCT = [  # id, name, kind, capacity_m3s, regulated_m3s, verdict text
    ("K-3", "K take-off box culvert 1.5 x 1.5 m at 1.26 %", "culvert", 10.0, 0.30, "takes the sluice's regulated flow only (gate 0.6 x 0.6 m, max 0.3 m3/s); the creek's peaks pass the side weir down the main stem"),
    ("K-5", "shelf channel 4 m wide, 1 m deep", "channel", 3.0, 0.30, "regulated flow; local runoff joins (shelf 4 ha, peak 0.14)"),
    ("P3", "P3 spillway: weir -0.1, 8 m long, west along the shelf to the Boardwalk's north end", "spill", 1.5, 0.30, "takes any surplus of the chain plus storm runoff; the flood path is the shelf's natural exit"),
    ("K-6", "Grove duct 1.2 m pipe at 0.38 %", "duct", 2.4, 0.30, "regulated flow only; surplus leaves by P3's spillway before the duct"),
    ("P2", "P2 weir -0.6 and the notch cascade; culvert under route B 1.0 m, under the Grand Circuit 1.0 m", "spill", 3.0, 0.61, "regulated 0.3 + the park's 9 ha storm peak 0.31 = 0.61 m3/s; passes"),
    ("L-3", "L fork box culvert 1.2 x 1.2 m at 2.5 %", "culvert", 6.0, 0.20, "sluice 0.5 x 0.5 m at the fork weir, max 0.2 m3/s; the creek's peaks go on down the main stem to the east body"),
    ("P1a", "P1a weir +3.9 to the P1a-P1b channel; culverts under S3 and the Grand Circuit 0.8 m", "spill", 1.0, 0.20, "regulated; passes"),
    ("P1b", "P1b slough spillway: weir +2.9, 6 m long, cascade to the NE lobe", "spill", 1.5, 0.20, "every surplus of the Kiddieland chain leaves here to the lobe; the rides R6/R14 stand above +5 and north of the ponds"),
    ("L-7", "entrance siphon 1.0 m pipe, 3.2 m head", "duct", 2.8, 0.10, "intake sluice at P1b set to 0.1 m3/s: REGULATED BASEFLOW ONLY beneath the entrance; peaks never enter it"),
    ("D3", "D3 pond: emergency overflow weir -0.1 into a 0.6 m pipe west to the shore band at (-88,170)", "spill", 0.5, 0.10, "so a blocked Fairground duct cannot flood the entrance precinct"),
    ("L-8", "Fairground duct 1.0 m pipe at 0.81 %", "duct", 2.2, 0.10, "regulated baseflow only; outfall into Coastal Creek at CX1"),
    ("CC", "Coastal Creek 05A channel 3.2 m ribbon, rain pond, CB1, CB2, outfall", "channel", 1.5, 0.10, "its own 05A design flow plus 0.1; unchanged"),
    ("K-2", "K main stem to the north cove", "creek", 99.0, None, "carries the full flood: no structure in the park"),
    ("L-2", "L main stem and the arrival bridge (61 m span) into the east body", "creek", 99.0, None, "carries the full flood under the plan's bridge"),
]


def interp_stage(name, level):
    t = STAGE[name]["table"]
    if level <= t[0][0]:
        return 0.0, 0.0
    for (l0, v0, a0), (l1, v1, a1) in zip(t, t[1:]):
        if l0 <= level <= l1:
            f = (level - l0) / (l1 - l0)
            return v0 + f * (v1 - v0), a0 + f * (a1 - a0)
    return t[-1][1], t[-1][2]


def level_for_volume(name, vol):
    t = STAGE[name]["table"]
    if vol <= 0:
        return t[0][0]
    for (l0, v0, a0), (l1, v1, a1) in zip(t, t[1:]):
        if v0 <= vol <= v1:
            return l0 + (vol - v0) / (v1 - v0) * (l1 - l0)
    return t[-1][0]


def simulate(case):
    c = CASES[case]
    yearly_off = c["area_km2"] * 1e6 * c["yield_mm"] / 1000.0
    out = {"case": case, "off_map_m3_per_yr": yearly_off, "systems": {}}
    for sysname, split, lake in (("K", SPLIT_K, "K1"), ("L", SPLIT_L, "L0")):
        if "per_system" in c:
            ps = c["per_system"][sysname]
            yearly_off_sys = ps["area_km2"] * 1e6 * ps["yield_mm"] / 1000.0
            split = yearly_off_sys / yearly_off
        vis = VISIBLE[sysname]
        rain_year_above = vis["above_lake_ha"] * 1e4 * RAIN_MM / 1000 * C_HILLS
        rain_year_below = (vis["total_ha"] - vis["above_lake_ha"]) * 1e4 * RAIN_MM / 1000 * C_HILLS
        snow = [yearly_off * split * SNOW_FRAC[m] for m in range(12)]
        rain = [rain_year_above * RAIN_FRAC[m] for m in range(12)]
        inflow = [snow[m] + rain[m] for m in range(12)]
        below = [rain_year_below * RAIN_FRAC[m] for m in range(12)]
        spring_year = RECHARGE_AREA_HA * 1e4 * RAIN_MM / 1000 * RECHARGE_FRACTION * c["spring_factor"]
        chain_springs_ls = sum(q for _, _, q, sys_, _, _ in SPRINGS if sys_ == sysname) * c["spring_factor"]
        spring_total_ls = sum(q for _, _, q, *_ in SPRINGS) * c["spring_factor"]
        springs = [spring_year * SPRING_FRAC[m] * (chain_springs_ls / spring_total_ls) for m in range(12)]   # the share emerging in this chain
        pond_ha = sum(PONDS[sysname].values())
        circ = CIRC_L_S[sysname]
        # demand from the park chain: pond evaporation + seepage + circulation (May..Nov)
        demand = []
        for m in range(12):
            ev = pond_ha * 1e4 * EVAP_MM / 1000 * EVAP_FRAC[m]
            seep = pond_ha * 1e4 * SEEP_MM_DAY / 1000 * DAYS[m]
            circ_m = circ / 1000 * SEC[m] if 4 <= m <= 10 else 0.0
            demand.append(max(0.0, ev + seep + circ_m - springs[m]))   # the chain's own springs top the ponds up first
        brim = STAGE[lake]["brim"]
        vol_brim, _ = interp_stage(lake, brim)
        vol_outlet, _ = interp_stage(lake, OUTLET[lake]["invert"])
        # two passes so the year closes
        vol = vol_brim
        levels, spills, releases, evaps, vols = [], [], [], [], []
        for _ in range(2):
            levels, spills, releases, evaps, vols = [], [], [], [], []
            for m in range(12):
                lvl = level_for_volume(lake, vol)
                _, area_ha = interp_stage(lake, lvl)
                ev = area_ha * 1e4 * EVAP_MM / 1000 * EVAP_FRAC[m]
                rel = demand[m] if vol - ev + inflow[m] > vol_outlet + demand[m] else max(0.0, vol - ev + inflow[m] - vol_outlet)
                vol = vol + inflow[m] - ev - rel
                sp = max(0.0, vol - vol_brim)
                vol -= sp
                levels.append(level_for_volume(lake, vol))
                spills.append(sp)
                releases.append(rel)
                evaps.append(ev)
                vols.append(vol)
        met = all(r >= d - 1e-6 for r, d in zip(releases, demand))
        creek_at_takeoff = [spills[m] + releases[m] + below[m] for m in range(12)]  # what flows past the take-off (lake spill + release + rain below the lake)
        runs_all_year = min(creek_at_takeoff[m] / SEC[m] * 1000 for m in range(12)) > 0.5
        out["systems"][sysname] = {
            "lake": lake, "brim": brim, "vol_brim_m3": vol_brim, "outlet_invert": OUTLET[lake]["invert"], "usable_storage_m3": vol_brim - vol_outlet,
            "inflow_m3_month": [round(v) for v in inflow], "inflow_L_s": [round(v / s * 1000, 1) for v, s in zip(inflow, SEC)],
            "snow_m3_month": [round(v) for v in snow], "rain_m3_month": [round(v) for v in rain], "springs_to_chain_m3_month": [round(v) for v in springs],
            "springs_to_chain_L_s": [round(v / s * 1000, 2) for v, s in zip(springs, SEC)], "creek_runs_all_year": runs_all_year,
            "summer_baseflow_at_head_L_s": round(min(inflow[m] / SEC[m] * 1000 for m in (6, 7, 8)), 1),
            "rain_below_lake_m3_month": [round(v) for v in below],
            "demand_m3_month": [round(v) for v in demand], "release_m3_month": [round(v) for v in releases], "release_L_s": [round(v / s * 1000, 1) for v, s in zip(releases, SEC)],
            "evaporation_m3_month": [round(v) for v in evaps], "spill_m3_month": [round(v) for v in spills],
            "level_end_of_month": [round(v, 2) for v in levels], "drawdown_m": round(brim - min(levels), 2), "demand_met_all_year": met,
            "creek_past_takeoff_L_s": [round(v / s * 1000, 1) for v, s in zip(creek_at_takeoff, SEC)],
            "mean_creek_L_s": round(sum(creek_at_takeoff) / 31.536e6 * 1000, 1), "pond_ha": pond_ha, "circulation_L_s": circ,
        }
    return out


def peaks(case):
    c = CASES[case]
    res = {}
    for sysname, split in (("K", SPLIT_K), ("L", SPLIT_L)):
        A_ha = VISIBLE[sysname]["total_ha"]
        storm_vis = 0.35 * 25.0 * A_ha / 360.0                      # rational method, 10-yr 1-h intensity 25 mm/h, C 0.35
        melt_day_mm = c["melt_mm_day"]
        area_sys = c["area_km2"] * split
        if "per_system" in c:
            area_sys, melt_day_mm = c["per_system"][sysname]["area_km2"], c["per_system"][sysname]["melt_mm_day"]
        melt_peak = area_sys * 1e6 * melt_day_mm / 1000 * 0.7 / 86400.0   # daily melt, 70 % reaching the creek
        rain_on_snow = 2.0 * melt_peak
        res[sysname] = {"winter_storm_visible_m3s": round(storm_vis, 2), "spring_melt_peak_m3s": round(melt_peak, 2), "rain_on_snow_m3s": round(rain_on_snow, 2),
                        "design_peak_m3s": round(max(storm_vis + melt_peak, rain_on_snow), 2),
                        "method": "rational method on the visible area (C 0.35, i 25 mm/h, A ha) + daily snowmelt (mm/day x off-map area x 0.7 x split) / 86400; rain-on-snow = 2 x melt; the lake attenuates nothing in this estimate (conservative)"}
    return res


def run(out, prefix="network2_", check_case="HIGH"):
    os.makedirs(out, exist_ok=True)
    budget = {"assumptions": {"cases": CASES, "split_K_L": [SPLIT_K, SPLIT_L], "snow_month_fractions": SNOW_FRAC, "rain_mm": RAIN_MM, "runoff_hills": C_HILLS, "runoff_park": C_PARK,
                              "rain_month_fractions": RAIN_FRAC, "evap_mm": EVAP_MM, "evap_month_fractions": EVAP_FRAC, "seepage_mm_day": SEEP_MM_DAY, "circulation_L_s": CIRC_L_S,
                              "outlets": OUTLET, "stage_tables": STAGE,
                              "why": "SoCal coast ranges at this latitude (Lagunas, Palomar, San Jacinto) carry winter snow at 1,500-2,600 m and melt out by May-June; mountain runoff yields of 100-400 mm/yr are typical; all of this is Christina's assumption to confirm"},
              "cases": {k: simulate(k) for k in CASES}, "peaks": {k: peaks(k) for k in CASES}}
    # structure check against the HIGH design peaks and the regulated flows
    hp = budget["peaks"][check_case]
    budget["check_case"] = check_case
    checks = []
    for sid, name, kind, cap, reg, verdict in STRUCT:
        if reg is None:
            flow = hp["K" if sid.startswith("K") else "L"]["design_peak_m3s"]
            ok = True
        else:
            flow = reg
            ok = cap >= reg
        checks.append({"id": sid, "name": name, "kind": kind, "capacity_m3s": cap, "design_flow_m3s": flow, "passes": ok, "verdict": verdict})
    budget["structures"] = checks
    budget["_hydro_folder"] = HYDRO
    budget["springs"] = {"recharge_area_ha": RECHARGE_AREA_HA, "recharge_fraction_MEDIUM": RECHARGE_FRACTION, "lag_months": "2-3", "month_fractions": SPRING_FRAC,
                         "recharge_m3_per_yr_MEDIUM": RECHARGE_AREA_HA * 1e4 * RAIN_MM / 1000 * RECHARGE_FRACTION,
                         "sites": [{"name": n, "at": xy, "flow_L_s_LOW_MED_HIGH": [round(q * 0.4, 2), q, q * 2], "system": sy, "feeds": f, "plan": pl} for n, xy, q, sy, f, pl in SPRINGS],
                         "total_L_s_MEDIUM": sum(q for _, _, q, *_ in SPRINGS), "dry_season_share": "July-September springs run at about 55-70 % of their mean (fractions 0.07/0.06/0.05 of the year per month)",
                         "outlets": "every spring-fed low has an outlet: P3 (weir west), P2 (notch weir), P1a/P1b (weirs), D3 (emergency overflow pipe), the slough and valley springs drain to the lagoon; the saucers D4/D5 would pond and overflow Kiddieland's lawns without their new spillways",
                         "pops_up_as_springs": "K-4 (corner), K-6 outlet at P2 (Grove-mound foot), L-4 (Kiddieland spur foot), D3: each underground link ends where a spring line would plausibly emerge, so in plan language the water 'goes under and comes up as a spring'"}
    budget["flood_path"] = {
        "K": "creek floods stay in the main stem to the north cove; the take-off sluice limits the park chain to 0.3 m3/s; surplus at P3 goes west along the shelf (the natural exit), surplus at P2 down the notch cascade to the sea; nothing reaches the Plaza, NT-1 or the Grove's flume",
        "L": "creek floods stay in the main stem through the arrival bridge into the east body; the fork sluice limits the Kiddieland chain to 0.2 m3/s; surplus at P1b leaves by the slough spillway to the lobe; the siphon under the entrance carries 0.1 m3/s regulated and nothing else; D3 has its own emergency overflow to the shore band; the rides R5, R6, R7, R14 stand above the ponds' levels and off the spillway lines",
        "pumps": "none: the reservoirs' gravity release supplies evaporation, seepage and a 3 + 2 L/s circulation through the chains May-Nov; no pump is needed for circulation either",
    }
    budget["changes"] = ["a groundwater layer: 12 spring/seep sites (network2_springs.png), 10 L/s in total in the MEDIUM case, topping up P2, P3, P1a/P1b, D3, Coastal Creek, the slough and the lobe","K1 and L0 are managed reservoirs: sluice towers at their spills with inverts +74 and +86 (drawdown up to 5.7 / 6 m), usable storage 137 k and 173 k m3",
                         "the K-3 and L-3 take-offs get sluice gates (0.6 and 0.5 m) limiting the park chains to 0.3 / 0.2 m3/s; the fork weirs return the rest to the main stems",
                         "the entrance siphon gets an intake sluice (0.1 m3/s) and D3 an emergency overflow to the shore band",
                         "P1a shrinks to z 136..160 (0.09 ha) to clear R14's footprint", "culvert sizes unchanged: all pass their regulated flows with margin; the two dry-season pumps are dropped"]
    budget["prefix"] = prefix
    with open(os.path.join(out, prefix + "budget.json"), "w") as f:
        json.dump(budget, f, indent=1)
    draw(budget, out)
    for k, cs in budget["cases"].items():
        for s_, v in cs["systems"].items():
            print(f"budget {k} {s_}: inflow {sum(v['inflow_m3_month']) / 1e3:.0f} k m3/yr, creek mean {v['mean_creek_L_s']} L/s, drawdown {v['drawdown_m']} m, demand met {v['demand_met_all_year']}, levels {v['level_end_of_month']}")
    print("budget: peaks HIGH", budget["peaks"]["HIGH"])
    return budget


def draw(b, out):
    from PIL import Image, ImageDraw
    AZ = (0, 115, 255)
    P = b.get("prefix", "network2_")
    # 1. assumptions table
    rows = [["case", "off-map area", "elevation band", "yield", "water/yr", "K head mean L/s", "L head mean L/s", "spring peak K / L (melt) m3/s", "winter storm K / L m3/s", "note"]]
    for k, c in CASES.items():
        cs = b["cases"][k]["systems"]
        pk = b["peaks"][k]
        rows.append([k, f"{c['area_km2']} km2", c["band_m"] + " m", f"{c['yield_mm']} mm", f"{b['cases'][k]['off_map_m3_per_yr'] / 1e6:.2f} M m3",
                     f"{sum(cs['K']['inflow_m3_month']) / 31.536e6 * 1000:.1f}", f"{sum(cs['L']['inflow_m3_month']) / 31.536e6 * 1000:.1f}",
                     f"{pk['K']['spring_melt_peak_m3s']} / {pk['L']['spring_melt_peak_m3s']}", f"{pk['K']['winter_storm_visible_m3s']} / {pk['L']['winter_storm_visible_m3s']}", c["note"]])
    rows.append(["visible rain", "70 ha K / 47 ha L", "0-294 m", "300 mm x 0.3", "63 k / 42 k m3", "2.0", "1.3", "-", "1.7 / 1.1", "rain on the mapped catchments, winter-seasonal"])
    widths = [90, 120, 140, 90, 110, 120, 120, 200, 170, 420]
    img = Image.new("RGB", (sum(widths) + 40, 26 * len(rows) + 140), (250, 250, 248))
    dr = ImageDraw.Draw(img)
    dr.text((20, 10), "network2_assumptions: the off-map snowmelt catchment as Christina's assumption, parameterised LOW / MEDIUM / HIGH (to confirm)", fill=(0, 0, 0))
    for r_, row in enumerate(rows):
        x = 20
        y = 40 + r_ * 26
        dr.line([20, y - 5, sum(widths) + 20, y - 5], fill=(225, 225, 225))
        for v, w in zip(row, widths):
            dr.text((x, y), str(v)[:int(w / 5.6)], fill=(20, 20, 20))
            x += w
    y = 40 + len(rows) * 26 + 10
    dr.text((20, y), "Monthly snow-fed fractions (Jan..Dec): " + ", ".join(f"{int(f * 100)}" for f in SNOW_FRAC) + " %; rain fractions: " + ", ".join(f"{int(f * 100)}" for f in RAIN_FRAC) + " %; evaporation 1,400 mm/yr, fractions " + ", ".join(f"{int(f * 100)}" for f in EVAP_FRAC) + " %", fill=(60, 60, 60))
    dr.text((20, y + 18), "Split 60 % K / 40 % L. Peaks: rational method on the visible area (C 0.35, i 25 mm/h) + daily melt (15 / 20 / 30 mm/day over the off-map area, 70 % reaching the creek); rain-on-snow = 2 x melt. Seepage 2 mm/day on unlined ponds.", fill=(60, 60, 60))
    dr.text((20, y + 36), "Why: coast ranges at this latitude (Lagunas, Palomar, San Jacinto) carry winter snow at 1,500-2,600 m and melt out by May-June; mountain runoff yields of 100-400 mm/yr are typical. All of it is an assumption to be confirmed by Christina.", fill=(60, 60, 60))
    img.save(os.path.join(out, P + "assumptions.png"))

    # 2. year of water: three cases, two systems
    W, Hh = 30 + len(CASES) * 600, 1150
    img = Image.new("RGB", (W, Hh), (250, 250, 248))
    dr = ImageDraw.Draw(img)
    dr.text((20, 10), P + "year_of_water: monthly inflow to each reservoir (bars), reservoir level (line, right scale), release to the park chain (azure bars) and the park ponds (held full) for the three cases", fill=(0, 0, 0))
    panel_w, panel_h = 560, 300
    for ci, case in enumerate(CASES):
        for si, sysname in enumerate(("K", "L")):
            v = b["cases"][case]["systems"][sysname]
            x0 = 30 + ci * (panel_w + 40)
            y0 = 50 + si * (panel_h + 220)
            dr.rectangle([x0, y0, x0 + panel_w, y0 + panel_h], outline=(150, 150, 150))
            dr.text((x0 + 4, y0 + 4), f"{case}: {sysname} / {v['lake']} (brim {v['brim']}, outlet {v['outlet_invert']}, usable {v['usable_storage_m3'] / 1e3:.0f} k m3)", fill=(20, 20, 20))
            mx = max(max(v["inflow_m3_month"][m] + v["springs_to_chain_m3_month"][m] for m in range(12)), 1)
            for m in range(12):
                bx = x0 + 10 + m * 45
                base_y = y0 + panel_h - 20
                hs = v["snow_m3_month"][m] / mx * (panel_h - 80)
                hr_ = v["rain_m3_month"][m] / mx * (panel_h - 80)
                hg = v["springs_to_chain_m3_month"][m] / mx * (panel_h - 80)
                dr.rectangle([bx, base_y - hs, bx + 18, base_y], fill=(170, 200, 240))
                dr.rectangle([bx, base_y - hs - hr_, bx + 18, base_y - hs], fill=(120, 150, 200))
                dr.rectangle([bx, base_y - hs - hr_ - hg, bx + 18, base_y - hs - hr_], fill=(90, 190, 150))
                hr = v["release_m3_month"][m] / mx * (panel_h - 80)
                dr.rectangle([bx + 20, y0 + panel_h - 20 - hr, bx + 32, y0 + panel_h - 20], fill=AZ)
                dr.text((bx, y0 + panel_h - 16), MONTHS[m], fill=(80, 80, 80))
            dr.text((x0 + 4, y0 + 20), f"max inflow {mx / 1e3:.0f} k m3/month ({max(v['inflow_L_s'])} L/s); release May-Nov {v['release_L_s'][6]} L/s (Jul)", fill=(80, 80, 80))
            lo, hi = v["outlet_invert"] - 1, v["brim"] + 0.5
            pts = [(x0 + 19 + m * 45, y0 + panel_h - 20 - (v["level_end_of_month"][m] - lo) / (hi - lo) * (panel_h - 80)) for m in range(12)]
            dr.line(pts, fill=(200, 60, 60), width=3)
            dr.text((x0 + panel_w - 150, y0 + 20), f"level {min(v['level_end_of_month'])}..{max(v['level_end_of_month'])} (drawdown {v['drawdown_m']} m)", fill=(200, 60, 60))
            dr.text((x0 + 4, y0 + panel_h + 6), f"park ponds {sysname}: {v['pond_ha']:.2f} ha held full all year: {'YES' if v['demand_met_all_year'] else 'NO'}; creek past the take-off: mean {v['mean_creek_L_s']} L/s, Jul {v['creek_past_takeoff_L_s'][6]} L/s", fill=(0, 60, 150))
            dr.text((x0 + 4, y0 + panel_h + 22), "inflow L/s: " + " ".join(str(x) for x in v["inflow_L_s"]), fill=(80, 80, 80))
            dr.text((x0 + 4, y0 + panel_h + 38), "release L/s: " + " ".join(str(x) for x in v["release_L_s"]), fill=(80, 80, 80))
            dr.text((x0 + 4, y0 + panel_h + 54), "level: " + " ".join(str(x) for x in v["level_end_of_month"]), fill=(80, 80, 80))
    dr.text((20, Hh - 58), "Bands: pale blue = snowmelt (off map), blue = rain above the lake, green = springs emerging in the park chain (shown with the inflow for scale; they top the ponds up directly). Cases: LOW = coast-range snow + weak springs; MEDIUM / HIGH = deep pack, likelier.", fill=(60, 60, 60))
    dr.text((20, Hh - 40), "Reading: bars = inflow (snowmelt + rain above the lake, springs), azure bars = controlled release to the park chain (evaporation + seepage + 3/2 L/s circulation May-Nov), red line = reservoir level (outlet invert at the bottom of the scale, brim at the top). Peaks and storms are in network2_reaches_table.png.", fill=(60, 60, 60))
    img.save(os.path.join(out, P + "year_of_water.png"))

    # 3. reaches / structures table
    rows = [["id", "structure", "kind", "capacity m3/s", "design flow m3/s", "passes", "verdict"]]
    for c in b["structures"]:
        rows.append([c["id"], c["name"], c["kind"], c["capacity_m3s"], c["design_flow_m3s"], "yes" if c["passes"] else "NO", c["verdict"]])
    hp = b["peaks"][b.get("check_case", "HIGH")]
    rows.append(["", "", "", "", "", "", ""])
    rows.append(["peaks", f"{b.get('check_case', 'HIGH')} case: K design peak {hp['K']['design_peak_m3s']} m3/s (storm {hp['K']['winter_storm_visible_m3s']} + melt {hp['K']['spring_melt_peak_m3s']}, rain-on-snow {hp['K']['rain_on_snow_m3s']}); L {hp['L']['design_peak_m3s']} m3/s", "", "", "", "", "main stems only"])
    widths = [60, 520, 70, 110, 120, 60, 820]
    img = Image.new("RGB", (sum(widths) + 40, 26 * len(rows) + 80), (250, 250, 248))
    dr = ImageDraw.Draw(img)
    dr.text((20, 10), "network2_reaches_table: every structure against its regulated flow and the HIGH-case peaks; ducts under the entrance and the Plaza edge carry regulated baseflow only, peaks leave by the surface spillways", fill=(0, 0, 0))
    for r_, row in enumerate(rows):
        x = 20
        y = 40 + r_ * 26
        dr.line([20, y - 5, sum(widths) + 20, y - 5], fill=(225, 225, 225))
        for v, w in zip(row, widths):
            dr.text((x, y), str(v)[:int(w / 5.6)], fill=(20, 20, 20))
            x += w
    img.save(os.path.join(out, P + "reaches_table.png"))

    # 4. schematic with flows (MEDIUM case)
    cs = b["cases"][b.get("check_case", "MEDIUM") if b.get("check_case", "MEDIUM") in b["cases"] else "MEDIUM"]["systems"]
    W, Hh = 1600, 760
    img = Image.new("RGB", (W, Hh), (250, 250, 248))
    dr = ImageDraw.Draw(img)
    for yb, lab in [(60, "FAR MOUNTAINS (off map, snow)"), (150, "HILLS (mapped, rain)"), (400, "PARK (shelf at 0)"), (660, "SEA / LAGOON (-7.5)")]:
        dr.line([20, yb, W - 20, yb], fill=(200, 200, 200))
        dr.text((24, yb - 14), lab, fill=(120, 120, 120))
    nodes = {"snowK": (330, 30), "snowL": (1150, 30), "K1": (330, 120), "takeoff": (400, 250), "cove": (120, 690), "P3": (470, 420), "P2": (360, 480), "notch": (260, 580), "sea1": (260, 690),
             "L0": (1150, 120), "fork": (1050, 250), "P1a": (1000, 380), "P1b": (880, 420), "lobe": (980, 620), "eastbody": (1200, 660), "D3": (720, 450), "CC": (560, 500), "sea2": (480, 690), "E": (1080, 720)}
    def lab_flow(s, m):
        return f"{cs[s]['release_L_s'][m]} L/s"
    edges = [("snowK", "K1", "creek", f"snow+rain {sum(cs['K']['inflow_m3_month']) / 31.536e6 * 1000:.0f} L/s mean, {max(cs['K']['inflow_L_s'])} L/s Apr"), ("snowL", "L0", "creek", f"{sum(cs['L']['inflow_m3_month']) / 31.536e6 * 1000:.0f} L/s mean, {max(cs['L']['inflow_L_s'])} L/s Apr"),
             ("K1", "takeoff", "creek", f"spill + release; Jul {cs['K']['creek_past_takeoff_L_s'][6]} L/s"), ("takeoff", "cove", "creek", "main stem: the flood path"), ("takeoff", "P3", "duct", "sluice: 3 L/s summer, max 300 L/s"),
             ("P3", "P2", "duct", "regulated"), ("P2", "notch", "cascade", "+ park runoff"), ("notch", "sea1", "cascade", ""),
             ("L0", "fork", "creek", f"Jul {cs['L']['creek_past_takeoff_L_s'][6]} L/s"), ("fork", "eastbody", "creek", "main stem: the flood path"), ("fork", "P1a", "duct", "sluice: 2 L/s summer, max 200 L/s"),
             ("P1a", "P1b", "channel", ""), ("P1b", "lobe", "cascade", "spillway: all surplus"), ("P1b", "D3", "duct", "siphon: 0.1 m3/s max, baseflow only"), ("D3", "CC", "duct", "duct"), ("CC", "sea2", "creek", "Coastal Creek"), ("eastbody", "E", "boat", "")]
    for a, b_, k, t in edges:
        pa, pb = nodes[a], nodes[b_]
        if k == "duct":
            for i in range(10):
                t0, t1 = i / 10, (i + 0.5) / 10
                dr.line([(pa[0] + (pb[0] - pa[0]) * t0, pa[1] + (pb[1] - pa[1]) * t0), (pa[0] + (pb[0] - pa[0]) * t1, pa[1] + (pb[1] - pa[1]) * t1)], fill=AZ, width=4)
        elif k == "boat":
            dr.line([pa, pb], fill=(150, 60, 200), width=2)
        else:
            dr.line([pa, pb], fill=AZ if k != "cascade" else (0, 60, 200), width=4 if k != "creek" else 3)
        if t:
            dr.text(((pa[0] + pb[0]) / 2 + 6, (pa[1] + pb[1]) / 2 - 6), t, fill=(0, 70, 170))
    labels = {"snowK": "off-map snow catchment (60 %)", "snowL": "off-map snow catchment (40 %)", "K1": f"K1 reservoir {min(cs['K']['level_end_of_month'])}..{cs['K']['brim']}", "takeoff": "take-off +8.9, side weir + sluice", "cove": "north cove", "P3": "P3 -0.2 (spillway west)", "P2": "P2 -0.6", "notch": "notch weir, falls", "sea1": "sea",
              "L0": f"L0 reservoir {min(cs['L']['level_end_of_month'])}..{cs['L']['brim']}", "fork": "fork +9.3, side weir + sluice", "P1a": "P1a +3.9", "P1b": "P1b +2.9 (spillway to the lobe)", "lobe": "NE lobe", "eastbody": "east body (arrival bridge)", "D3": "D3 -0.3 (emergency overflow)", "CC": "Coastal Creek CX1 -1.5", "sea2": "shore band / sea", "E": "E landing"}
    for k, (x, y) in nodes.items():
        dr.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(120, 170, 255), outline=AZ, width=2)
        dr.text((x + 10, y + 4), labels[k], fill=(0, 40, 120))
    dr.text((20, Hh - 30), "network2_schematic (MEDIUM case): reservoirs K1/L0 with sluice outlets; regulated park chains; peaks on the main stems; no pumps", fill=(20, 20, 20))
    img.save(os.path.join(out, P + "schematic.png"))
    # 5. springs map on the master's terrain
    try:
        import numpy as np
        hydro = b.get("_hydro_folder")
        d = np.load(os.path.join(hydro, "hydro_grid10.npz"))
        H, xs, zs = d["H"], d["xs"], d["zs"]
        X0, X1, Z0, Z1, sc = -300.0, 400.0, -450.0, 450.0, 1.3
        W, Hh = int((X1 - X0) * sc), int((Z1 - Z0) * sc)
        img = Image.new("RGB", (W, Hh + 200), (250, 250, 248))
        arr = np.zeros((Hh, W, 3), dtype=np.uint8)
        jj = np.clip(((np.arange(Hh) / sc + Z0 - zs[0]) / 10).astype(int), 0, len(zs) - 1)
        ii = np.clip(((np.arange(W) / sc + X0 - xs[0]) / 10).astype(int), 0, len(xs) - 1)
        Hs = H[jj][:, ii]
        sea = Hs <= -7.45
        t = np.clip((Hs + 8) / 60.0, 0, 1)
        arr[..., 0] = (235 - 90 * t).astype(np.uint8)
        arr[..., 1] = (232 - 110 * t).astype(np.uint8)
        arr[..., 2] = (215 - 130 * t).astype(np.uint8)
        band = (np.floor(Hs / 5) != np.floor(np.roll(Hs, 1, axis=0) / 5)) | (np.floor(Hs / 5) != np.floor(np.roll(Hs, 1, axis=1) / 5))
        arr[band & ~sea] = (190, 180, 160)
        arr[sea] = (150, 185, 215)
        img.paste(Image.fromarray(arr), (0, 0))
        dr = ImageDraw.Draw(img)
        px = lambda x: (x - X0) * sc
        pz = lambda z: (z - Z0) * sc
        for name, (x0r, x1r, z0r, z1r) in {"Boardwalk": (-200, -44, -215, 88), "Fairground": (-88, 8, 18, 185), "Kiddieland": (-5, 181, 42, 185), "Frontier": (48, 196, -194, -45), "Grove": (-55, 81, -214, -45), "Headland": (-229, 18, -337, -148), "Entrance": (-48, 48, 83, 196), "Plaza": (-52, 52, -52, 52)}.items():
            dr.rectangle([px(x0r), pz(z0r), px(x1r), pz(z1r)], outline=(130, 130, 130))
            dr.text((px(x0r) + 3, pz(z0r) + 2), name, fill=(90, 90, 90))
        # contact lines where springs plausibly emerge: the ridge toe (+2 contour north of the shelf), the shore-band bluff foot, the coast bluff
        for pts, lab in [([(0, -262), (150, -262), (190, -240)], "north-ridge toe seep line"), ([(-56, -230), (-56, 220)], "shore-band bluff foot seeps"), ([(-110, 330), (-70, 365), (0, 370), (100, 370), (170, 320)], "approach-valley floor seeps"), ([(195, 140), (215, 100), (230, 60)], "east spur toe")]:
            dr.line([(px(x), pz(z)) for x, z in pts], fill=(90, 190, 150), width=3)
            dr.text((px(pts[0][0]) + 4, pz(pts[0][1]) - 14), lab, fill=(30, 130, 90))
        for n, (x, z), q, sy, f, pl in SPRINGS:
            if not (X0 <= x <= X1 and Z0 <= z <= Z1):
                continue
            r = 4 + q * 6
            dr.ellipse([px(x) - r, pz(z) - r, px(x) + r, pz(z) + r], fill=(90, 190, 150), outline=(20, 110, 70), width=2)
            dr.text((px(x) + r + 3, pz(z) - 6), f"{n}: {q * 0.4:.1f} / {q} / {q * 2:.1f} L/s -> {f}", fill=(20, 90, 60))
        y = Hh + 10
        dr.text((10, y), "network2_springs: plausible spring and seep sites (green; flows LOW / MEDIUM / HIGH in L/s) on the master's terrain; green lines = contact lines (ridge toe, bluff foot, valley floor) where seeps emerge", fill=(10, 10, 10))
        sp = b["springs"]
        dr.text((10, y + 20), f"Recharge: {sp['recharge_area_ha']:.0f} ha of hills x 300 mm x {sp['recharge_fraction_MEDIUM']} = {sp['recharge_m3_per_yr_MEDIUM'] / 1e3:.0f} k m3/yr (MEDIUM; LOW x0.4, HIGH x2); springs lag the rain 2-3 months; July-September they run at 55-70 % of their mean. Total {sp['total_L_s_MEDIUM']} L/s MEDIUM.", fill=(60, 60, 60))
        dr.text((10, y + 40), sp["pops_up_as_springs"][:200], fill=(60, 60, 60))
        dr.text((10, y + 60), sp["outlets"][:220], fill=(60, 60, 60))
        dr.text((10, y + 80), "Off the map south: S11 beach-front bluff seeps 0.8 / 2 / 4 L/s to the beach. All of this is a conceptual groundwater layer: Christina's assumption plus plausible siting, no hydrogeology claimed.", fill=(60, 60, 60))
        img.save(os.path.join(out, P + "springs.png"))
    except Exception as e:  # the map needs the hydrology samples; the budget does not
        print(f"budget: springs map skipped: {e}")
    print("budget: wrote network2_assumptions.png, network2_year_of_water.png, network2_reaches_table.png, network2_schematic.png")


if __name__ == "__main__":
    argv = sys.argv[1:]
    HYDRO = argv[argv.index("--hydro") + 1] if "--hydro" in argv else None
    prefix = argv[argv.index("--prefix") + 1] if "--prefix" in argv else "network2_"
    case = argv[argv.index("--case") + 1] if "--case" in argv else "HIGH"
    if prefix == "network2_":
        CASES.pop("CHOSEN", None)   # the network2_ set stays as issued: three cases
    run(argv[argv.index("--out") + 1], prefix, case)
