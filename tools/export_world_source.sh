#!/bin/sh
# Re-export a mounted world GLB from its editable Blender master.
#
#   tools/export_world_source.sh                                  # the range master
#   tools/export_world_source.sh assets/source/far_shore_city_relocation.blend
#   tools/export_world_source.sh <master.blend> --output /tmp/x.glb
#
# The master is opened read-only by tools/export_world_source.py, which builds
# any batched rock cells and the derived-collision copies beside the authored
# objects, writes assets/<master>.glb and discards what it built; the .blend is
# never saved. Godot re-imports the GLB the next time it starts or scans, or at
# once with `Godot --headless --path . --import`.
set -e
cd "$(dirname "$0")/.."
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
MASTER="assets/source/range_forest_distinct_background.blend"
case "$1" in
	*.blend) MASTER="$1"; shift ;;
esac
LOG="${TMPDIR:-/tmp}/export_world_source.log"
"$BLENDER" --background "$MASTER" --python tools/export_world_source.py -- "$@" > "$LOG" 2>&1 || {
	echo "export failed; log at $LOG" >&2
	tail -40 "$LOG" >&2
	exit 1
}
sed -n '/^export_world_source/,$p' "$LOG" | grep -v '^Blender quit'
