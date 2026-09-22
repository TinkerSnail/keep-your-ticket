#!/usr/bin/env python3
"""Build and validate the live visual catalogs embedded in the park rosters.

The Markdown tables remain the inventory. This tool reads those tables, derives
camera targets from the synchronized park-section map, and owns only the
generated blocks between the visual-catalog markers.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import sys
import textwrap
import uuid
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "documentation"
CATALOG_DIR = DOCS / "visual-catalog"
IMAGE_DIR = CATALOG_DIR / "images"
CARD_DIR = CATALOG_DIR / "cards"
SHEET_DIR = CATALOG_DIR / "sheets"
PLAN_PATH = CATALOG_DIR / "capture-plan.json"
REQUEST_PATH = CATALOG_DIR / "capture-request.json"
STATE_PATH = CATALOG_DIR / "catalog-state.json"
COMPLETE_PATH = CATALOG_DIR / "capture-complete.json"
MAP_PATH = DOCS / "maps" / "park-sections.html"
BEGIN = "[visual-catalog-generated-begin]: # (generated catalog begins)"
END = "[visual-catalog-generated-end]: # (generated catalog ends)"
LEGACY_BEGIN = "<!-- BEGIN GENERATED VISUAL CATALOG -->"
LEGACY_END = "<!-- END GENERATED VISUAL CATALOG -->"

CARD_SIZE = (560, 438)
PREVIEW_HEIGHT = 316
SHEET_COLUMNS = 4

ROSTERS = {
    "buildings": DOCS / "buildings-and-facilities-roster.md",
    "attractions": DOCS / "rides-and-attractions-roster.md",
}

# Rows without a map ID still get a repeatable, named view rather than an
# arbitrary screenshot. Values are [x, ground_y, z, extent, target_y_offset].
FALLBACKS = {
    "arrival parking": [0, 0, 145, 80, 2],
    "main gate": [0, 0, 78, 24, 5],
    "entrance frontage": [0, 0, 105, 46, 5],
    "plaza perimeter": [0, 0, 0, 92, 8],
    "plaza café": [21, 0, 16, 24, 3],
    "family support lodge": [27, 5, 107, 24, 4],
    "false-front street": [80, 11, -92, 54, 8],
    "picnic pavilion": [-13, 3, -98, 30, 5],
    "grand circuit": [15, 4, 20, 210, 12],
    "five grand circuit": [15, 4, 20, 210, 12],
    "service spines": [20, 5, -15, 235, 10],
    "pier, pier house": [-145, -1, -8, 76, 5],
    "pond, garden loop": [-10, 3, -104, 55, 4],
    "western street show": [80, 11, -92, 54, 8],
    "frontier street show": [80, 11, -92, 54, 8],
    "big top performances": [-32, 2, 92, 32, 5],
    "bandstand program": [-42, 0, -32, 28, 5],
    "parades": [0, 0, 25, 105, 7],
    "mascot appearances": [103, 5, 74, 30, 4],
    "seasonal tentpoles": [0, 0, 0, 150, 10],
}

# The map supplies horizontal placement. These overrides make tall subjects and
# protected compositions fit the frame without changing their geometry.
SHOT_OVERRIDES = {
    "R1": {"extent": 48, "target_y": 14},
    "R2": {"extent": 82, "target_y": 10},
    "R5": {"direction": [-0.8, 1.0], "extent": 48, "height_scale": 1.0},
    "R6": {"direction": [-0.8, 1.0], "extent": 26, "height_scale": 1.0},
    "R7": {"direction": [-0.8, 1.0], "extent": 26, "height_scale": 1.0},
    "R11": {"extent": 55, "target_y": 34},
    "R12": {"extent": 165, "target_y": 22},
    "R13": {"extent": 75, "target_y": 32},
    "R14": {"extent": 52, "target_y": 14, "direction": [-0.8, 1.0], "height_scale": 0.9},
    "P1": {"extent": 30, "target_y": 43},
    "P4": {"direction": [-0.8, 1.0]},
    "KS1": {"direction": [-0.8, 1.0]},
    "KG1": {"direction": [-0.8, 1.0]},
    "KC1": {"direction": [-0.8, 1.0]},
    "KC2": {"direction": [-0.8, 1.0]},
    "KC3": {"direction": [-0.8, 1.0]},
    "KP1": {"direction": [-0.8, 1.0]},
    "CLOCK": {"extent": 36, "target_y": 22},
    "NT-1": {"extent": 28, "target_y": 1, "position": [-108, 12, -2]},
    "NT-2": {"extent": 55, "target_y": 10, "position": [62, 22, 0]},
    "PLAZA": {"extent": 32, "target_y": 3},
}

PROGRAM_TARGETS = {
    "mascot appearances": "KC1",
    "parades": "PLAZA",
    "big top performances": "P3",
    "bandstand program": "P5",
    "pier, pier house": "BW-H",
}

FALLBACK_OVERRIDES = {
    "plaza café": {"position": [-2, 12, 35]},
}

HOME_Y = {
    "entrance": 0,
    "plaza": 0,
    "boardwalk": -1,
    "fairground": 2,
    "kiddieland": 5,
    "high terrace": 19,
    "frontier": 11,
    "grove": 3,
    "headland": 31,
    "parkwide": 4,
}


def clean_cell(value: str) -> str:
    value = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", value)
    value = value.replace("**", "").replace("*", "").replace("`", "")
    return html.unescape(value).strip()


def slug(value: str) -> str:
    value = clean_cell(value).lower().replace("↔", " to ")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:72] or "entry"


def parse_tables(kind: str, path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    text = strip_generated(text)
    entries: list[dict] = []
    section = ""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].startswith("## "):
            section = lines[i][3:].strip()
        if lines[i].startswith("|") and i + 1 < len(lines) and re.match(r"^\|[-:| ]+\|$", lines[i + 1]):
            headers = [clean_cell(c) for c in lines[i].strip("|").split("|")]
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                cells = [clean_cell(c) for c in lines[i].strip("|").split("|")]
                if len(cells) == len(headers):
                    row = dict(zip(headers, cells))
                    entry = entry_from_row(kind, section, row)
                    if entry:
                        entries.append(entry)
                i += 1
            continue
        i += 1
    return entries


def entry_from_row(kind: str, section: str, row: dict[str, str]) -> dict | None:
    if kind == "buildings":
        if section == "Park buildings and facilities":
            name = row["Building or facility"]
            plan_id, home, state = row["Plan ID"], row["Home"], row["Current state"]
        elif section == "Unmapped facilities and coverage checks":
            name = row["Facility"]
            plan_id, home, state = "—", "Unmapped", row["Current gap"]
        else:
            return None
    else:
        if section == "Rides":
            name, plan_id, home, state = row["Current label"], row["ID"], row["Home"], row["Current state"]
        elif section == "Programmed and landscape attractions":
            name, plan_id, home, state = row["Attraction"], row["ID"], row["Home"], row["Current state"]
        elif section == "Midway games and participatory attractions":
            name, plan_id, home, state = row["Attraction"], row["ID"], row["Home"], row["Current state"]
        elif section == "Scheduled park entertainment":
            name, plan_id, home, state = row["Program"], "—", row["Primary route or home"], row["What remains open"]
        else:
            return None
    key = f"{kind}-{slug(section)}-{slug(plan_id)}-{slug(name)}"
    return {
        "key": key,
        "kind": kind,
        "section": section,
        "id": plan_id,
        "home": home,
        "name": name,
        "state": state,
    }


def strip_generated(text: str) -> str:
    candidates = []
    for opening, closing in ((BEGIN, END), (LEGACY_BEGIN, LEGACY_END)):
        start = text.find(opening)
        if start >= 0:
            candidates.append((start, opening, closing))
    if not candidates:
        return text
    start, _opening, closing = min(candidates, key=lambda candidate: candidate[0])
    finish = text.find(closing, start)
    if finish < 0:
        raise RuntimeError("Visual catalog has an opening marker but no closing marker")
    finish += len(closing)
    return text[:start].rstrip() + "\n\n" + text[finish:].lstrip()


def canonical_roster(text: str) -> str:
    """Remove generated output and normalize only its surrounding blank space."""
    return strip_generated(text).rstrip() + "\n"


def map_objects() -> dict[str, dict]:
    source = MAP_PATH.read_text(encoding="utf-8")
    objects: dict[str, dict] = {}
    for match in re.finditer(r"\{id:'([^']+)'", source):
        start = match.start()
        depth = 0
        end = start
        for pos in range(start, len(source)):
            ch = source[pos]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = pos + 1
                    break
        block = source[start:end]
        item_id = match.group(1)
        points: list[tuple[float, float]] = []
        at = re.search(r"\bat:\[(-?[\d.]+),(-?[\d.]+)\]", block)
        terminals = re.search(r"\bterminals:\[(\[[^;]+?\])\](?:,|\})", block)
        shape = re.search(r"\b(?:footprint|points|track):\[(\[[^;]+?\])\](?:,|\})", block)
        rect = re.search(r"\bx0:(-?[\d.]+),x1:(-?[\d.]+),z0:(-?[\d.]+),z1:(-?[\d.]+)", block)
        if terminals:
            points = number_pairs(terminals.group(1))
        elif shape:
            points = number_pairs(shape.group(1))
        elif at:
            points = [(float(at.group(1)), float(at.group(2)))]
        elif rect:
            x0, x1, z0, z1 = map(float, rect.groups())
            points = [(x0, z0), (x1, z1)]
        if not points:
            continue
        if not (item_id.startswith("BW-") or item_id.startswith("HL-")):
            points = [rebuild_expand_point(point) for point in points]
        xs, zs = [p[0] for p in points], [p[1] for p in points]
        cx, cz = sum(xs) / len(xs), sum(zs) / len(zs)
        extent = max(max(xs) - min(xs), max(zs) - min(zs), 12.0)
        size = re.search(r"\bsize:\[([\d.]+),([\d.]+)\]", block)
        radius = re.search(r"\br:([\d.]+)", block)
        radii = re.search(r"\brx:([\d.]+),rz:([\d.]+)", block)
        if size:
            extent = max(extent, float(size.group(1)), float(size.group(2)))
        if radius:
            extent = max(extent, float(radius.group(1)) * 2)
        if radii:
            extent = max(extent, float(radii.group(1)) * 2, float(radii.group(2)) * 2)
        objects.setdefault(item_id, {"x": cx, "z": cz, "extent": extent})
    return objects


def number_pairs(value: str) -> list[tuple[float, float]]:
    return [(float(a), float(b)) for a, b in re.findall(r"\[(-?[\d.]+),(-?[\d.]+)\]", value)]


def rebuild_expand_point(point: tuple[float, float]) -> tuple[float, float]:
    """Mirror ParkPlan.rebuild_expand_point for map-to-live-world targeting."""
    x, z = point
    expanded_x, expanded_z = x, z
    if z > 52.0:
        expanded_z = 52.0 + (z - 52.0) * 1.55
        if x > 49.0:
            expanded_x = 49.0 + (x - 49.0) * 1.45
    elif z < -52.0:
        expanded_z = -52.0 + (z + 52.0) * (178.0 / 108.0)
        if x > 20.0:
            expanded_x = 20.0 + (x - 20.0) * 1.35
    elif x > 128.0:
        expanded_x = 128.0 + (x - 128.0) * 2.5
    if x < -112.0:
        expanded_x = -112.0 + (x + 112.0) * 1.5
    return expanded_x, expanded_z


def first_map_id(value: str, objects: dict[str, dict]) -> str | None:
    for token in re.findall(r"NT-\d|[A-Z]+(?:-[A-Z]+)?\d*", value):
        if token in objects:
            return token
    return None


def ground_y(home: str) -> float:
    low = home.lower()
    for key, value in HOME_Y.items():
        if key in low:
            return value
    return 3


def placeholder_status(entry: dict) -> str | None:
    state = entry["state"].lower()
    if state.startswith("source only"):
        return "SOURCE ONLY"
    if state.startswith("unmounted"):
        return "UNMOUNTED"
    if "mentioned only" in state:
        return "MENTIONED ONLY"
    if state.startswith("not specified") or state.startswith("unassigned"):
        return "UNASSIGNED"
    if entry["name"].lower() == "security / gate-control room":
        return "UNASSIGNED"
    if "physical boxes" in state and "not yet" in state:
        return "NOT BUILT"
    return None


def fallback_for(name: str) -> tuple[str, list[float]] | None:
    low = name.lower()
    for phrase, values in FALLBACKS.items():
        if phrase in low:
            return phrase, values
    return None


def build_catalog() -> tuple[list[dict], list[dict]]:
    objects = map_objects()
    entries = [entry for kind, path in ROSTERS.items() for entry in parse_tables(kind, path)]
    shots: dict[str, dict] = {}
    missing: list[str] = []
    for entry in entries:
        placeholder = placeholder_status(entry)
        if placeholder:
            entry["visual_status"] = placeholder
            entry["image"] = f"visual-catalog/images/{entry['key']}.svg"
            continue

        object_id = first_map_id(entry["id"], objects)
        if object_id is None:
            low_name = entry["name"].lower()
            object_id = next((target for phrase, target in PROGRAM_TARGETS.items() if phrase in low_name), None)
        fallback = fallback_for(entry["name"])
        if object_id:
            obj = objects[object_id]
            y = ground_y(entry["home"])
            extent = max(18.0, obj["extent"] * 1.7)
            target_y = y + max(3.0, extent * 0.08)
            override = SHOT_OVERRIDES.get(object_id, {})
            extent = override.get("extent", extent)
            target_y = override.get("target_y", target_y)
            capture_key = slug(object_id)
            shot = {"key": capture_key, "target": [obj["x"], target_y, obj["z"]], "extent": extent}
            if "direction" in override:
                shot["direction"] = override["direction"]
            if "position" in override:
                shot["position"] = override["position"]
            if "height_scale" in override:
                shot["height_scale"] = override["height_scale"]
        elif fallback:
            phrase, values = fallback
            x, y, z, extent, target_offset = values
            x, z = rebuild_expand_point((x, z))
            capture_key = "place-" + slug(phrase)
            shot = {"key": capture_key, "target": [x, y + target_offset, z], "extent": extent}
            shot.update(FALLBACK_OVERRIDES.get(phrase, {}))
        else:
            missing.append(f"{entry['kind']}: {entry['name']} ({entry['id']})")
            entry["visual_status"] = "NEEDS CAPTURE PROFILE"
            entry["image"] = f"visual-catalog/images/{entry['key']}.svg"
            continue
        shots[capture_key] = shot
        entry["capture_key"] = capture_key
        entry["visual_status"] = "LIVE PARK VIEW"
        entry["image"] = f"visual-catalog/images/{capture_key}.png"

    if missing:
        print("Entries without a map target or explicit profile:", file=sys.stderr)
        for item in missing:
            print(f"  - {item}", file=sys.stderr)
    return entries, sorted(shots.values(), key=lambda shot: shot["key"])


def fingerprint() -> str:
    digest = hashlib.sha256()
    roots = [ROOT / "scenes", ROOT / "scripts", ROOT / "assets"]
    files: list[Path] = []
    for base in roots:
        files.extend(path for path in base.rglob("*") if path.is_file() and ".godot" not in path.parts)
    files.extend([
        ROOT / "project.godot",
        MAP_PATH,
        ROOT / "planning" / "park-sections.html",
        DOCS / "park-scenery-fidelity-ledger.md",
        Path(__file__),
        ROOT / "tools" / "visual_catalog_capture.gd",
    ])
    files.extend(ROSTERS.values())
    for path in sorted(set(files)):
        if not path.exists():
            continue
        data = path.read_bytes()
        if path in ROSTERS.values():
            data = canonical_roster(data.decode("utf-8")).encode("utf-8")
        digest.update(str(path.relative_to(ROOT)).encode("utf-8") + b"\0")
        digest.update(data + b"\0")
    return digest.hexdigest()


def entry_signature(entries: list[dict]) -> str:
    payload = [{k: e.get(k) for k in ("key", "section", "id", "home", "name", "state", "image", "visual_status")} for e in entries]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def prepare() -> int:
    entries, shots = build_catalog()
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    current = fingerprint()
    request_id = uuid.uuid4().hex
    if COMPLETE_PATH.exists():
        COMPLETE_PATH.unlink()
    PLAN_PATH.write_text(json.dumps({"version": 1, "request_id": request_id, "shots": shots}, indent=2) + "\n", encoding="utf-8")
    REQUEST_PATH.write_text(json.dumps({
        "version": 1,
        "request_id": request_id,
        "source_fingerprint": current,
        "entry_signature": entry_signature(entries),
        "shot_count": len(shots),
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(entries)} cards and {len(shots)} live views.")
    return 0


def write_placeholder(path: Path, entry: dict) -> None:
    title = html.escape(entry["name"][:62])
    status = html.escape(entry["visual_status"])
    detail_lines = textwrap.wrap(entry["state"], width=68)[:2]
    detail_svg = "".join(
        f'<text x="320" y="{215 + index * 24}" text-anchor="middle" font-family="sans-serif" font-size="15" fill="#c8d2dc">{html.escape(line)}</text>'
        for index, line in enumerate(detail_lines)
    )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">
<rect width="640" height="360" fill="#222831"/><rect x="18" y="18" width="604" height="324" rx="12" fill="#303946" stroke="#8fa3b8" stroke-width="2"/>
<text x="320" y="122" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="700" fill="#f4d58d">{status}</text>
<text x="320" y="169" text-anchor="middle" font-family="sans-serif" font-size="22" fill="#ffffff">{title}</text>
{detail_svg}
</svg>'''
    path.write_text(svg, encoding="utf-8")


def catalog_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


FONT_LABEL = catalog_font(24, bold=True)
FONT_NAME = catalog_font(22)
FONT_STATUS = catalog_font(16, bold=True)
FONT_HOME = catalog_font(16)
FONT_PLACEHOLDER = catalog_font(30, bold=True)
FONT_SHEET = catalog_font(42, bold=True)


def catalog_groups(kind: str, entries: list[dict]) -> list[tuple[str, list[dict]]]:
    groups: dict[str, list[dict]] = {}
    for entry in entries:
        if entry["kind"] != kind:
            continue
        if kind == "buildings" and entry["section"] == "Park buildings and facilities":
            group = entry["home"]
        elif kind == "buildings":
            group = "Unmapped and coverage checks"
        else:
            group = entry["section"]
        groups.setdefault(group, []).append(entry)
    return list(groups.items())


def placeholder_preview(entry: dict) -> Image.Image:
    colors = {
        "SOURCE ONLY": (199, 158, 111),
        "UNMOUNTED": (172, 170, 166),
        "MENTIONED ONLY": (211, 202, 184),
        "UNASSIGNED": (172, 170, 166),
        "NOT BUILT": (211, 202, 184),
        "NEEDS CAPTURE PROFILE": (207, 186, 125),
    }
    image = Image.new("RGB", (CARD_SIZE[0], PREVIEW_HEIGHT), colors.get(entry["visual_status"], (172, 170, 166)))
    draw = ImageDraw.Draw(image)
    draw.rectangle((28, 28, CARD_SIZE[0] - 28, PREVIEW_HEIGHT - 28), outline=(55, 58, 55), width=3)
    message = entry["visual_status"]
    box = draw.textbbox((0, 0), message, font=FONT_PLACEHOLDER)
    draw.text(((CARD_SIZE[0] - (box[2] - box[0])) // 2, 118), message, fill=(45, 48, 45), font=FONT_PLACEHOLDER)
    return image


def make_catalog_card(entry: dict) -> Image.Image:
    if entry["visual_status"] == "LIVE PARK VIEW":
        preview = ImageOps.fit(
            Image.open(DOCS / entry["image"]).convert("RGB"),
            (CARD_SIZE[0], PREVIEW_HEIGHT),
            method=Image.Resampling.LANCZOS,
        )
    else:
        preview = placeholder_preview(entry)
    card = Image.new("RGB", CARD_SIZE, (32, 37, 37))
    card.paste(preview, (0, 0))
    draw = ImageDraw.Draw(card)
    label = entry["id"] if entry["id"] != "—" else (
        "COVERAGE" if entry["kind"] == "buildings" and entry["section"].startswith("Unmapped") else
        "PROGRAM" if entry["section"] == "Scheduled park entertainment" else
        "FACILITY" if entry["kind"] == "buildings" else "ATTRACTION"
    )
    draw.text((20, PREVIEW_HEIGHT + 12), label, fill=(247, 194, 67), font=FONT_LABEL)
    status_box = draw.textbbox((0, 0), entry["visual_status"], font=FONT_STATUS)
    draw.text(
        (CARD_SIZE[0] - 20 - (status_box[2] - status_box[0]), PREVIEW_HEIGHT + 17),
        entry["visual_status"], fill=(174, 194, 185), font=FONT_STATUS,
    )
    name_lines = textwrap.wrap(entry["name"], width=43)[:2]
    for index, line in enumerate(name_lines):
        draw.text((20, PREVIEW_HEIGHT + 51 + index * 25), line, fill=(244, 239, 226), font=FONT_NAME)
    draw.text((20, CARD_SIZE[1] - 23), entry["home"], fill=(174, 194, 185), font=FONT_HOME)
    return card


def build_sheets(entries: list[dict]) -> dict[str, list[dict]]:
    CARD_DIR.mkdir(parents=True, exist_ok=True)
    SHEET_DIR.mkdir(parents=True, exist_ok=True)
    expected_cards: set[str] = set()
    sheets: dict[str, list[dict]] = {"buildings": [], "attractions": []}
    for entry in entries:
        card_name = f"{entry['key']}.png"
        expected_cards.add(card_name)
        make_catalog_card(entry).save(CARD_DIR / card_name, optimize=True)
    for kind in sheets:
        for group, members in catalog_groups(kind, entries):
            rows = math.ceil(len(members) / SHEET_COLUMNS)
            sheet_name = f"{kind}-{slug(group)}.png"
            sheet = Image.new("RGB", (CARD_SIZE[0] * SHEET_COLUMNS, 82 + CARD_SIZE[1] * rows), (22, 27, 27))
            draw = ImageDraw.Draw(sheet)
            draw.text((24, 17), f"{kind.upper()} · {group.upper()}", fill=(247, 194, 67), font=FONT_SHEET)
            for index, entry in enumerate(members):
                card = Image.open(CARD_DIR / f"{entry['key']}.png")
                sheet.paste(card, ((index % SHEET_COLUMNS) * CARD_SIZE[0], 82 + (index // SHEET_COLUMNS) * CARD_SIZE[1]))
            sheet.save(SHEET_DIR / sheet_name, optimize=True)
            sheets[kind].append({"group": group, "count": len(members), "file": sheet_name})
    expected_sheets = {sheet["file"] for values in sheets.values() for sheet in values}
    for directory, expected in ((CARD_DIR, expected_cards), (SHEET_DIR, expected_sheets)):
        for old_file in directory.glob("*.png"):
            if old_file.name not in expected:
                old_file.unlink()
    return sheets


def generated_block(kind: str, entries: list[dict], sheets: dict[str, list[dict]], source_fingerprint: str, generated_at: str | None = None) -> str:
    if generated_at:
        try:
            stamp = datetime.fromisoformat(generated_at).astimezone().strftime("%Y-%m-%d %H:%M %Z")
        except ValueError:
            stamp = generated_at
    else:
        stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    lines = [
        BEGIN,
        "## Visual catalog",
        "",
        f"Generated from the roster above and the live persistent park on **{stamp}**. "
        "Each card is either a current game view or an explicit status card; no planning image is presented as built work.",
        "",
        "Refresh after park, map or roster edits with `tools/update_visual_catalog.sh`. "
        "Run `python3 tools/visual_catalog.py check` to verify that this catalog still matches its sources. "
        f"Catalog fingerprint: `{source_fingerprint[:12]}`.",
        "",
    ]
    for sheet in sheets[kind]:
        group = sheet["group"]
        count = sheet["count"]
        lines.extend([
            f"### {group}",
            "",
            f"![{group} visual catalog, {count} entries](visual-catalog/sheets/{sheet['file']})",
            "",
        ])
    live_entries = sum(1 for entry in entries if entry["kind"] == kind and entry["visual_status"] == "LIVE PARK VIEW")
    status_entries = sum(1 for entry in entries if entry["kind"] == kind and entry["visual_status"] != "LIVE PARK VIEW")
    distinct_live = len({entry.get("capture_key") for entry in entries if entry["kind"] == kind and entry.get("capture_key")})
    lines.extend([
        f"Current coverage: {live_entries} entries shown from {distinct_live} distinct live park views,",
        f"plus {status_entries} explicit source-only, unmounted, unbuilt or unmapped status cards.",
        "",
    ])
    lines.append(END)
    return "\n".join(lines)


def inject(path: Path, block: str) -> None:
    text = canonical_roster(path.read_text(encoding="utf-8"))
    marker = "## Sources and maintenance\n"
    head, separator, tail = text.partition(marker)
    if not separator:
        raise RuntimeError(f"Cannot locate Sources and maintenance in {path}")
    path.write_text(head.rstrip() + "\n\n" + block + "\n\n" + marker + tail, encoding="utf-8")


def format_docs() -> int:
    """Rewrite only the generated Markdown shell around the recorded visuals."""
    if not STATE_PATH.exists():
        print("Visual catalog has not been finalized.", file=sys.stderr)
        return 2
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    entries, _shots = build_catalog()
    if entry_signature(entries) != state.get("entry_signature"):
        print("Roster entries changed; a full catalog refresh is required.", file=sys.stderr)
        return 2
    sheets = build_sheets(entries)
    for kind, path in ROSTERS.items():
        inject(path, generated_block(kind, entries, sheets, state["source_fingerprint"], state.get("generated_at")))
    print("Reformatted both visual catalogs as ordinary Markdown.")
    return 0


def finalize() -> int:
    if not REQUEST_PATH.exists():
        print("No capture request. Run prepare first.", file=sys.stderr)
        return 2
    request = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
    if not COMPLETE_PATH.exists():
        print("No completed render for this request; run visual_catalog_capture first.", file=sys.stderr)
        return 2
    completion = json.loads(COMPLETE_PATH.read_text(encoding="utf-8"))
    if completion.get("request_id") != request.get("request_id"):
        print("The completed render belongs to an older request; recapture the catalog.", file=sys.stderr)
        return 2
    current = fingerprint()
    if current != request["source_fingerprint"]:
        print("Park or roster sources changed during capture; restart the refresh.", file=sys.stderr)
        return 2
    entries, shots = build_catalog()
    if completion.get("shot_count") != len(shots):
        print("The completed render has the wrong number of shots; recapture the catalog.", file=sys.stderr)
        return 2
    if entry_signature(entries) != request["entry_signature"]:
        print("Catalog entries changed during capture; restart the refresh.", file=sys.stderr)
        return 2
    missing = []
    for shot in shots:
        path = IMAGE_DIR / f"{shot['key']}.png"
        if not path.exists() or path.stat().st_size < 5000:
            missing.append(path.name)
    if missing:
        print("Missing or implausibly small live captures: " + ", ".join(missing), file=sys.stderr)
        return 2
    expected_images = {Path(entry["image"]).name for entry in entries}
    for old_image in IMAGE_DIR.iterdir():
        if old_image.suffix.lower() in {".png", ".svg"} and old_image.name not in expected_images:
            old_image.unlink()
    for entry in entries:
        if entry["image"].endswith(".svg"):
            write_placeholder(DOCS / entry["image"], entry)
    sheets = build_sheets(entries)
    for kind, path in ROSTERS.items():
        inject(path, generated_block(kind, entries, sheets, current))
    STATE_PATH.write_text(json.dumps({
        "version": 1,
        "request_id": request.get("request_id"),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_fingerprint": current,
        "entry_signature": entry_signature(entries),
        "entry_count": len(entries),
        "shot_count": len(shots),
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Updated both roster documents with {len(entries)} visual cards.")
    return 0


def check() -> int:
    if not STATE_PATH.exists():
        print("Visual catalog has not been finalized. Run tools/update_visual_catalog.sh.", file=sys.stderr)
        return 2
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    entries, shots = build_catalog()
    errors: list[str] = []
    current = fingerprint()
    if REQUEST_PATH.exists():
        request = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
        if request.get("request_id") != state.get("request_id"):
            if not COMPLETE_PATH.exists():
                errors.append("the latest refresh did not complete its render")
            else:
                completion = json.loads(COMPLETE_PATH.read_text(encoding="utf-8"))
                if completion.get("request_id") != request.get("request_id"):
                    errors.append("the latest refresh has no matching completed render")
                else:
                    errors.append("the latest completed render has not been finalized")
    if current != state.get("source_fingerprint"):
        errors.append("park, map, tool or roster sources changed")
    if entry_signature(entries) != state.get("entry_signature"):
        errors.append("the roster inventory no longer matches the recorded cards")
    for path in ROSTERS.values():
        text = path.read_text(encoding="utf-8")
        if text.count(BEGIN) != 1 or text.count(END) != 1:
            errors.append(f"generated block missing or duplicated in {path.name}")
        elif any(tag in text.split(BEGIN, 1)[1].split(END, 1)[0] for tag in ("<table", "<td", "<tr", "<img", "<!--")):
            errors.append(f"raw HTML remains in the visual catalog in {path.name}")
    for kind in ROSTERS:
        for group, _members in catalog_groups(kind, entries):
            sheet = SHEET_DIR / f"{kind}-{slug(group)}.png"
            if not sheet.exists() or sheet.stat().st_size < 5000:
                errors.append(f"missing catalog sheet: {sheet.relative_to(ROOT)}")
    for entry in entries:
        image = DOCS / entry["image"]
        if not image.exists() or image.stat().st_size < (5000 if image.suffix == ".png" else 200):
            errors.append(f"missing visual: {image.relative_to(ROOT)}")
        if entry["visual_status"] == "NEEDS CAPTURE PROFILE":
            errors.append(f"capture profile needed: {entry['name']}")
    if errors:
        print("Visual catalog is stale:", file=sys.stderr)
        for error in sorted(set(errors)):
            print(f"  - {error}", file=sys.stderr)
        print("Refresh with tools/update_visual_catalog.sh", file=sys.stderr)
        return 1
    print(f"Visual catalog is current: {len(entries)} cards, {len(shots)} live views.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "finalize", "format", "check"))
    args = parser.parse_args()
    return {"prepare": prepare, "finalize": finalize, "format": format_docs, "check": check}[args.command]()


if __name__ == "__main__":
    raise SystemExit(main())
