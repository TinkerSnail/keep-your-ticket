#!/bin/bash
# Put a Godot on the box that can build the park and draw it.
#
# There is no package manifest in this repository and nothing to `npm install`.
# The dependency is the engine: `tools/gen_props.gd` generates every `.tscn` in
# `scenes/world/`, and the capture passes render them. Without Godot a session
# can read the project and change the generator, but it cannot regenerate the
# scenes the generator owns - which means it cannot honestly commit, because
# every commit here carries the generator and its output together.
#
# The container image does not ship Godot and never has, so this runs per
# session. The state is cached once the hook completes, so the 75MB download is
# paid on a cold container rather than every time.
set -euo pipefail

# Local machines have their own Godot and their own idea of where it lives.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

# The version the project actually asks for, rather than one written down twice.
# `config/features` is what Godot itself warns against on a mismatch.
VERSION="$(sed -n 's/^config\/features=PackedStringArray("\([0-9.]*\)".*/\1/p' \
  "$PROJECT_DIR/project.godot")"
VERSION="${VERSION:-4.7}"

BIN="/opt/godot/Godot_v${VERSION}-stable_linux.x86_64"

if [ ! -x "$BIN" ]; then
  echo "installing Godot ${VERSION}-stable"
  mkdir -p /opt/godot
  ZIP="/tmp/godot-${VERSION}.zip"
  curl -sSfL --retry 4 --retry-delay 2 --max-time 600 -o "$ZIP" \
    "https://github.com/godotengine/godot/releases/download/${VERSION}-stable/Godot_v${VERSION}-stable_linux.x86_64.zip"
  unzip -o -q "$ZIP" -d /opt/godot
  rm -f "$ZIP"
fi
ln -sfn "$BIN" /usr/local/bin/godot

# Rendering. `--headless` uses a dummy renderer that draws nothing, so the
# capture tools need a real one; lavapipe is Mesa's software Vulkan and is what
# lets Forward+ run on a box with no GPU. Xvfb is already in the image.
if [ ! -f /usr/share/vulkan/icd.d/lvp_icd.json ]; then
  echo "installing mesa-vulkan-drivers"
  apt-get update -qq || true
  apt-get install -y -qq --no-install-recommends mesa-vulkan-drivers
fi

# So a capture run does not have to name the driver every time.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json' >> "$CLAUDE_ENV_FILE"
fi

# Import once, so the first generator run is not also paying for the fonts and
# the generated `.res` textures. Idempotent: Godot skips what is already in
# `.godot/`.
godot --headless --path "$PROJECT_DIR" --import >/dev/null 2>&1 || true

echo "godot $(godot --headless --version 2>/dev/null | tail -1) ready"
