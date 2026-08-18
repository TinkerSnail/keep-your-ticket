#!/usr/bin/env bash
# Run a driver scene against the game under a virtual display.
#
#   drive.sh path/to/driver.gd [width height]
#
# Takes the .gd, writes the one-node .tscn that wraps it, runs it, and removes
# both afterwards so nothing throwaway is left in the repo. Screenshots land in
# ~/.local/share/godot/app_userdata/Keep Your Ticket/ -- go and look at them.
set -euo pipefail

DRIVER="${1:?usage: drive.sh path/to/driver.gd [width height]}"
W="${2:-1280}"
H="${3:-720}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"

eval "$("$(dirname "${BASH_SOURCE[0]}")/setup_headless.sh")"

# A killed run leaves an X lock behind, and the next launch then dies with a
# bare `exit 144` and no message. Clear them rather than debugging that twice.
pkill -9 -f Xvfb >/dev/null 2>&1 || true
rm -f /tmp/.X*-lock 2>/dev/null || true
rm -rf /tmp/.X11-unix 2>/dev/null || true

# Godot can only run a scene, not a bare script, so wrap the .gd in one node.
STEM="_drive_$$"
cp "$DRIVER" "$REPO/$STEM.gd"
cat > "$REPO/$STEM.tscn" <<TSCN
[gd_scene load_steps=2 format=3]
[ext_resource type="Script" path="res://$STEM.gd" id="1_d"]
[node name="drive" type="Node"]
script = ExtResource("1_d")
TSCN
trap 'rm -f "$REPO/$STEM.gd" "$REPO/$STEM.tscn" "$REPO/$STEM.gd.uid"' EXIT

# `--audio-driver Dummy` only quiets the console: a container has no sound
# server, so ALSA and PulseAudio each fail loudly at startup and bury the
# driver's own prints under a screenful of errors that mean nothing.
xvfb-run -a -s "-screen 0 ${W}x${H}x24" \
	"$GODOT" --path "$REPO" --rendering-driver vulkan --audio-driver Dummy \
	--resolution "${W}x${H}" "$STEM.tscn" \
	2>&1 | grep -vE "Leaked instance|RID allocation|ObjectDB instances|resources still in use|PagedAllocator|ALSA lib|snd_" || true

echo
echo "output: $HOME/.local/share/godot/app_userdata/Keep Your Ticket/"
