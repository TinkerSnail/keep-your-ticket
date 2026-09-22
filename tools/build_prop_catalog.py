#!/usr/bin/env python3
"""Build the visual prop catalog and Godot label constants from the Markdown registry.

The human-authored source of identity is documentation/prop-library.md. The JSON
manifest only says how a label can be pictured; it is deliberately not a second
name or status registry.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "documentation/prop-library.md"
MANIFEST = ROOT / "documentation/prop-catalog.json"
IMAGE_ROOT = ROOT / "documentation/images/prop-library"
RAW_DIR = IMAGE_ROOT / "raw"
CARD_DIR = IMAGE_ROOT / "cards"
SHEET_DIR = IMAGE_ROOT / "sheets"
DONE = IMAGE_ROOT / "capture-result.json"
GODOT_IDS = ROOT / "scripts/prop_catalog_ids.gd"
VIS_START = "<!-- PROP-CATALOG:START -->"
VIS_END = "<!-- PROP-CATALOG:END -->"

ENTRY_RE = re.compile(
    r"^- \*\*(?P<label>(?P<kind>PRP|GRP)-(?P<domain>[A-Z]+)-\d{3})"
    r" — (?P<name>.+?)\.\*\* (?P<tail>.*)$"
)

KIND_ORDER = ("PRP", "GRP")
DOMAIN_ORDER = {
    "PRP": (
        "PARK", "LITE", "COAST", "WILD", "GAME", "FOOD", "PHOTO", "OPS",
        "PLANT", "FENCE", "TRANSIT", "ROAD", "TOWN", "STORY", "SEASON",
    ),
    "GRP": ("PLAZA", "PARK", "BW", "PHOTO", "STORY", "SEASON"),
}

CARD_SIZE = (560, 420)
PREVIEW_HEIGHT = 316
SHEET_COLUMNS = 4


@dataclass(frozen=True)
class Entry:
    label: str
    kind: str
    domain: str
    name: str
    status: str


def parse_entries(markdown: str) -> list[Entry]:
    entries: list[Entry] = []
    seen: set[str] = set()
    for line in markdown.splitlines():
        match = ENTRY_RE.match(line)
        if not match:
            continue
        label = match.group("label")
        if label in seen:
            raise ValueError(f"duplicate catalog label: {label}")
        seen.add(label)
        tail = match.group("tail").lower()
        if tail.startswith("built"):
            status = "BUILT"
        elif tail.startswith("in review"):
            status = "IN REVIEW"
        elif tail.startswith("retired"):
            status = "RETIRED"
        elif tail.startswith("planned"):
            status = "PLANNED"
        else:
            raise ValueError(f"{label}: status must begin Built, In review, Retired or Planned")
        entries.append(Entry(
            label=label,
            kind=match.group("kind"),
            domain=match.group("domain"),
            name=match.group("name"),
            status=status,
        ))
    if not entries:
        raise ValueError("no PRP/GRP entries found in prop-library.md")
    return entries


def load_manifest() -> dict:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("recipes"), dict):
        raise ValueError("prop-catalog.json must contain version 1 and a recipes object")
    return data


def validate(entries: list[Entry], manifest: dict) -> None:
    labels = {entry.label for entry in entries}
    extras = sorted(set(manifest["recipes"]) - labels)
    if extras:
        raise ValueError("visual recipes have no Markdown entry: " + ", ".join(extras))
    for label, recipe in manifest["recipes"].items():
        if "source" in recipe:
            source = ROOT / recipe["source"].removeprefix("res://")
            if not source.exists():
                raise ValueError(f"{label}: missing scene source {recipe['source']}")
        if "context" in recipe:
            context = ROOT / recipe["context"]
            if not context.exists():
                raise ValueError(f"{label}: missing context image {recipe['context']}")


def run_capture(timeout_seconds: float) -> None:
    IMAGE_ROOT.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    DONE.unlink(missing_ok=True)
    manifest = load_manifest()
    for label, recipe in manifest["recipes"].items():
        if "source" in recipe:
            (RAW_DIR / f"{label.lower()}.png").unlink(missing_ok=True)

    launch_services = [
        "open", "-n", "-a", "/Applications/Godot.app", "--args",
        "--path", str(ROOT), "tools/run.tscn", "--", "prop_catalog_capture",
    ]
    process: subprocess.Popen | None = None
    try:
        subprocess.run(launch_services, check=True)
    except subprocess.CalledProcessError:
        configured = os.environ.get("GODOT_BIN", "")
        candidates = [
            configured,
            shutil.which("godot") or "",
            "/Applications/Godot.app/Contents/MacOS/Godot",
        ]
        executable = next((candidate for candidate in candidates
                           if candidate and Path(candidate).is_file()), "")
        if not executable:
            raise RuntimeError("LaunchServices failed and no Godot executable was found")
        log_path = IMAGE_ROOT / "capture.log"
        log = log_path.open("w", encoding="utf-8")
        process = subprocess.Popen(
            [executable, "--path", str(ROOT), "tools/run.tscn", "--", "prop_catalog_capture"],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if DONE.exists():
            result = json.loads(DONE.read_text(encoding="utf-8"))
            errors = result.get("errors", [])
            if errors:
                raise RuntimeError("Godot catalog capture failed:\n" + "\n".join(errors))
            print(f"captured {result.get('captured', 0)} source recipes")
            return
        if process is not None and process.poll() is not None:
            log_path = IMAGE_ROOT / "capture.log"
            detail = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
            raise RuntimeError("Godot exited before writing capture-result.json:\n" + detail[-5000:])
        time.sleep(0.5)
    raise TimeoutError(
        "catalog capture did not finish; inspect the newest Godot log under "
        "Library/Application Support/Godot/app_userdata/Keep Your Ticket/logs"
    )


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else
             "/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/Helvetica.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


FONT_LABEL = font(24, bold=True)
FONT_NAME = font(25)
FONT_STATUS = font(18, bold=True)
FONT_PLACEHOLDER = font(34, bold=True)
FONT_SHEET = font(42, bold=True)


def fit_preview(source: Image.Image) -> Image.Image:
    source = source.convert("RGB")
    return ImageOps.fit(source, (CARD_SIZE[0], PREVIEW_HEIGHT), method=Image.Resampling.LANCZOS)


def placeholder(entry: Entry, message: str) -> Image.Image:
    colors = {
        "PLANNED": (211, 202, 184),
        "RETIRED": (172, 170, 166),
        "IN REVIEW": (207, 186, 125),
        "BUILT": (199, 158, 111),
    }
    image = Image.new("RGB", (CARD_SIZE[0], PREVIEW_HEIGHT), colors[entry.status])
    draw = ImageDraw.Draw(image)
    draw.rectangle((28, 28, CARD_SIZE[0] - 28, PREVIEW_HEIGHT - 28), outline=(55, 58, 55), width=3)
    wrapped = textwrap.wrap(message, width=19)
    line_height = 42
    top = (PREVIEW_HEIGHT - line_height * len(wrapped)) // 2
    for index, line in enumerate(wrapped):
        box = draw.textbbox((0, 0), line, font=FONT_PLACEHOLDER)
        x = (CARD_SIZE[0] - (box[2] - box[0])) // 2
        draw.text((x, top + index * line_height), line, fill=(45, 48, 45), font=FONT_PLACEHOLDER)
    return image


def preview_for(entry: Entry, recipe: dict) -> tuple[Image.Image, str]:
    raw = RAW_DIR / f"{entry.label.lower()}.png"
    # A stale render from an earlier recipe must never outrank the current
    # manifest. This matters when an item is deliberately changed from an
    # isolated source render to a context card.
    if "source" in recipe and raw.exists():
        return fit_preview(Image.open(raw)), "SOURCE RENDER"
    context = recipe.get("context")
    if context:
        image = Image.open(ROOT / context)
        crop = recipe.get("crop")
        if crop:
            image = image.crop(tuple(crop))
        return fit_preview(image), "IN-WORLD CONTEXT"
    if entry.status == "PLANNED":
        return placeholder(entry, "PLANNED\nNO ASSET YET"), "PLANNED"
    if entry.status == "RETIRED":
        return placeholder(entry, "RETIRED\nREFERENCE ONLY"), "RETIRED"
    if entry.status == "IN REVIEW":
        return placeholder(entry, "IN REVIEW\nCAPTURE PENDING"), "IN REVIEW"
    return placeholder(entry, "BUILT\nRECIPE NEEDED"), "RECIPE NEEDED"


def make_card(entry: Entry, recipe: dict) -> tuple[Image.Image, str]:
    preview, visual_status = preview_for(entry, recipe)
    card = Image.new("RGB", CARD_SIZE, (34, 38, 38))
    card.paste(preview, (0, 0))
    draw = ImageDraw.Draw(card)
    draw.rectangle((0, PREVIEW_HEIGHT, CARD_SIZE[0], CARD_SIZE[1]), fill=(32, 37, 37))
    draw.text((20, PREVIEW_HEIGHT + 12), entry.label, fill=(247, 194, 67), font=FONT_LABEL)
    status_box = draw.textbbox((0, 0), visual_status, font=FONT_STATUS)
    draw.text(
        (CARD_SIZE[0] - 20 - (status_box[2] - status_box[0]), PREVIEW_HEIGHT + 16),
        visual_status,
        fill=(174, 194, 185),
        font=FONT_STATUS,
    )
    name_lines = textwrap.wrap(entry.name, width=37)[:2]
    for index, line in enumerate(name_lines):
        draw.text((20, PREVIEW_HEIGHT + 50 + index * 28), line, fill=(244, 239, 226), font=FONT_NAME)
    return card, visual_status


def ordered_domains(entries: list[Entry], kind: str) -> list[str]:
    present = {entry.domain for entry in entries if entry.kind == kind}
    preferred = [domain for domain in DOMAIN_ORDER.get(kind, ()) if domain in present]
    return preferred + sorted(present - set(preferred))


def build_images(entries: list[Entry], manifest: dict) -> dict[str, dict[str, int]]:
    CARD_DIR.mkdir(parents=True, exist_ok=True)
    SHEET_DIR.mkdir(parents=True, exist_ok=True)
    stats: dict[str, dict[str, int]] = {}
    recipes = manifest["recipes"]
    for entry in entries:
        card, visual_status = make_card(entry, recipes.get(entry.label, {}))
        card.save(CARD_DIR / f"{entry.label.lower()}.png", optimize=True)
        stats.setdefault(entry.kind, {}).setdefault(visual_status, 0)
        stats[entry.kind][visual_status] += 1

    for kind in KIND_ORDER:
        for domain in ordered_domains(entries, kind):
            members = [entry for entry in entries if entry.kind == kind and entry.domain == domain]
            rows = math.ceil(len(members) / SHEET_COLUMNS)
            width = CARD_SIZE[0] * SHEET_COLUMNS
            height = 82 + CARD_SIZE[1] * rows
            sheet = Image.new("RGB", (width, height), (22, 27, 27))
            draw = ImageDraw.Draw(sheet)
            draw.text((24, 17), f"{kind} · {domain}", fill=(247, 194, 67), font=FONT_SHEET)
            for index, entry in enumerate(members):
                card = Image.open(CARD_DIR / f"{entry.label.lower()}.png")
                x = (index % SHEET_COLUMNS) * CARD_SIZE[0]
                y = 82 + (index // SHEET_COLUMNS) * CARD_SIZE[1]
                sheet.paste(card, (x, y))
            sheet.save(SHEET_DIR / f"{kind.lower()}_{domain.lower()}.png", optimize=True)
    return stats


def gd_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def generated_gd(entries: list[Entry]) -> str:
    lines = [
        "class_name PropCatalogIds",
        "extends RefCounted",
        "",
        "## Generated by tools/build_prop_catalog.py from documentation/prop-library.md.",
        "## Edit the Markdown registry, then rebuild; do not hand-edit this file.",
        "",
    ]
    for entry in entries:
        constant = entry.label.replace("-", "_")
        lines.append(f'const {constant}: StringName = &{gd_string(entry.label)}')
    lines.extend(["", "const DISPLAY_NAMES: Dictionary = {"])
    for entry in entries:
        constant = entry.label.replace("-", "_")
        lines.append(f"\t{constant}: {gd_string(entry.name)},")
    lines.extend(["}", "", "const STATUSES: Dictionary = {"])
    for entry in entries:
        constant = entry.label.replace("-", "_")
        lines.append(f"\t{constant}: &{gd_string(entry.status.lower().replace(' ', '_'))},")
    lines.extend([
        "}",
        "",
        "static func is_known(label: StringName) -> bool:",
        "\treturn DISPLAY_NAMES.has(label)",
        "",
        "static func display_name(label: StringName) -> String:",
        "\treturn String(DISPLAY_NAMES.get(label, \"\"))",
        "",
        "static func status(label: StringName) -> StringName:",
        "\treturn StringName(STATUSES.get(label, &\"\"))",
        "",
    ])
    return "\n".join(lines)


def visual_markdown(entries: list[Entry], stats: dict[str, dict[str, int]]) -> str:
    lines = [
        VIS_START,
        "",
        "This block is rebuilt from the labeled entries below. **Source render** means",
        "the tool isolated current Godot geometry; **in-world context** means the prop or",
        "composition is shown in a current proof frame. Planned and retired cards are",
        "deliberately unmistakable placeholders rather than invented concept art.",
        "",
    ]
    for kind, heading in (("PRP", "Prop families"), ("GRP", "Prop groupings")):
        lines.extend([f"### {heading}", ""])
        for domain in ordered_domains(entries, kind):
            count = sum(1 for entry in entries if entry.kind == kind and entry.domain == domain)
            rel = f"images/prop-library/sheets/{kind.lower()}_{domain.lower()}.png"
            lines.extend([
                f"#### {domain}",
                "",
                f"![{domain} {heading.lower()}, {count} entries]({rel})",
                "",
            ])
    rendered = stats.get("PRP", {}).get("SOURCE RENDER", 0)
    context = stats.get("PRP", {}).get("IN-WORLD CONTEXT", 0)
    lines.extend([
        f"Current prop coverage: {rendered} isolated source renders and {context} in-world",
        "context cards. A built card marked **recipe needed** is a pipeline backlog item,",
        "not evidence that the prop is absent from the game.",
        "",
        VIS_END,
    ])
    return "\n".join(lines)


def replace_visual_block(markdown: str, block: str) -> str:
    if VIS_START not in markdown or VIS_END not in markdown:
        raise ValueError("prop-library.md is missing the generated visual-catalog markers")
    before, rest = markdown.split(VIS_START, 1)
    _, after = rest.split(VIS_END, 1)
    return before.rstrip() + "\n\n" + block + "\n" + after.lstrip("\n")


def check_outputs(entries: list[Entry], markdown: str, manifest: dict) -> None:
    expected_gd = generated_gd(entries)
    if not GODOT_IDS.exists() or GODOT_IDS.read_text(encoding="utf-8") != expected_gd:
        raise ValueError("scripts/prop_catalog_ids.gd is stale; rebuild the catalog")
    missing_cards = [entry.label for entry in entries
                     if not (CARD_DIR / f"{entry.label.lower()}.png").exists()]
    if missing_cards:
        raise ValueError("missing catalog cards: " + ", ".join(missing_cards))
    stale_cards: list[str] = []
    for entry in entries:
        expected, _ = make_card(entry, manifest["recipes"].get(entry.label, {}))
        actual = Image.open(CARD_DIR / f"{entry.label.lower()}.png").convert("RGB")
        if actual.size != expected.size or actual.tobytes() != expected.tobytes():
            stale_cards.append(entry.label)
    if stale_cards:
        raise ValueError("stale catalog cards: " + ", ".join(stale_cards))
    stale_sheets: list[str] = []
    for kind in KIND_ORDER:
        for domain in ordered_domains(entries, kind):
            members = [entry for entry in entries
                       if entry.kind == kind and entry.domain == domain]
            rows = math.ceil(len(members) / SHEET_COLUMNS)
            expected = Image.new(
                "RGB", (CARD_SIZE[0] * SHEET_COLUMNS, 82 + CARD_SIZE[1] * rows),
                (22, 27, 27),
            )
            draw = ImageDraw.Draw(expected)
            draw.text((24, 17), f"{kind} · {domain}", fill=(247, 194, 67), font=FONT_SHEET)
            for index, entry in enumerate(members):
                card = Image.open(CARD_DIR / f"{entry.label.lower()}.png").convert("RGB")
                expected.paste(card, (
                    (index % SHEET_COLUMNS) * CARD_SIZE[0],
                    82 + (index // SHEET_COLUMNS) * CARD_SIZE[1],
                ))
            path = SHEET_DIR / f"{kind.lower()}_{domain.lower()}.png"
            if not path.exists():
                stale_sheets.append(f"{kind}-{domain} (missing)")
                continue
            actual = Image.open(path).convert("RGB")
            if actual.size != expected.size or actual.tobytes() != expected.tobytes():
                stale_sheets.append(f"{kind}-{domain}")
    if stale_sheets:
        raise ValueError("stale catalog sheets: " + ", ".join(stale_sheets))
    stats: dict[str, dict[str, int]] = {}
    for entry in entries:
        _, status = preview_for(entry, manifest["recipes"].get(entry.label, {}))
        stats.setdefault(entry.kind, {}).setdefault(status, 0)
        stats[entry.kind][status] += 1
    expected_doc = replace_visual_block(markdown, visual_markdown(entries, stats))
    if expected_doc != markdown:
        raise ValueError("visual catalog block is stale; rebuild the catalog")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="render all source recipes in Godot first")
    parser.add_argument("--check", action="store_true", help="validate without writing")
    parser.add_argument("--timeout", type=float, default=300.0, help="capture timeout in seconds")
    args = parser.parse_args()

    markdown = DOC.read_text(encoding="utf-8")
    entries = parse_entries(markdown)
    manifest = load_manifest()
    validate(entries, manifest)
    if args.capture:
        run_capture(args.timeout)
    if args.check:
        check_outputs(entries, markdown, manifest)
        print(f"prop catalog OK: {sum(e.kind == 'PRP' for e in entries)} props, "
              f"{sum(e.kind == 'GRP' for e in entries)} groupings")
        return 0

    stats = build_images(entries, manifest)
    GODOT_IDS.write_text(generated_gd(entries), encoding="utf-8")
    new_markdown = replace_visual_block(markdown, visual_markdown(entries, stats))
    DOC.write_text(new_markdown, encoding="utf-8")
    print(json.dumps(stats, indent=2, sort_keys=True))
    print(f"wrote {GODOT_IDS.relative_to(ROOT)} and visual catalog sheets")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, TimeoutError) as exc:
        print(f"prop catalog: {exc}", file=sys.stderr)
        raise SystemExit(1)
