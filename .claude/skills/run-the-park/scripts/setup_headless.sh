#!/usr/bin/env bash
# Put a working Godot + software renderer on this container, and import the
# project so `class_name` resolves. Idempotent: safe and cheap to re-run.
#
# Prints the binary's path as GODOT=... on the last line, so callers can do:
#   eval "$(.claude/skills/run-the-park/scripts/setup_headless.sh | tail -1)"
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
DEST="${GODOT_DIR:-${SCRATCHPAD:-/tmp}/godot}"
mkdir -p "$DEST"

# The version the project expects. Reading it rather than hardcoding it means a
# project.godot bump does not silently leave this pinned to the old binary --
# and a mismatched minor version reshuffles every unique_id the generators
# write, turning a small change into a whole-file diff.
FEATURE="$(sed -n 's/^config\/features=PackedStringArray(\(.*\))$/\1/p' "$REPO/project.godot" \
	| tr -d '" ' | tr ',' '\n' | grep -E '^4\.[0-9]+$' | head -1)"
VERSION="${GODOT_VERSION:-${FEATURE:-4.7}.1-stable}"
BIN="$DEST/Godot_v${VERSION}_linux.x86_64"

if [ ! -x "$BIN" ]; then
	echo "fetching Godot $VERSION" >&2
	URL="https://github.com/godotengine/godot/releases/download/${VERSION}/Godot_v${VERSION}_linux.x86_64.zip"
	curl -sSL -o "$DEST/godot.zip" "$URL"
	unzip -oq "$DEST/godot.zip" -d "$DEST"
	rm -f "$DEST/godot.zip"
	chmod +x "$BIN"
fi

# lavapipe (a software Vulkan driver) and a virtual display. libvulkan alone is
# not enough -- with no ICD installed there is no driver behind it, and Godot
# falls back or fails rather than rendering.
need=()
[ -e /usr/share/vulkan/icd.d/lvp_icd.json ] || need+=(mesa-vulkan-drivers)
command -v xvfb-run >/dev/null || need+=(xvfb)
if [ ${#need[@]} -gt 0 ]; then
	echo "installing: ${need[*]}" >&2
	apt-get update -qq >/dev/null 2>&1 || true
	apt-get install -y -qq "${need[@]}" >/dev/null 2>&1 || true
fi

# The import pass. Without .godot/global_script_class_cache.cfg the class_name
# registry is empty, and main.tscn fails to load on an "Identifier not declared"
# parse error in a file nobody touched.
if [ ! -f "$REPO/.godot/global_script_class_cache.cfg" ]; then
	echo "importing project (first run only)" >&2
	xvfb-run -a -s "-screen 0 1280x720x24" \
		"$BIN" --path "$REPO" --editor --quit --rendering-driver vulkan >/dev/null 2>&1 || true
fi

echo "GODOT=$BIN"
