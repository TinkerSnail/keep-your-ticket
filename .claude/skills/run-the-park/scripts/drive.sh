#!/usr/bin/env bash
# Run a driver scene against the game under a virtual display.
#
#   drive.sh path/to/driver.gd  [width height]   # wraps it in a scene, runs, cleans up
#   drive.sh tools/capture.tscn  [width height]   # already a scene, runs as-is
#
# Godot can only run a scene, so a bare .gd needs a one-node wrapper. The tools
# that are here to stay carry their own (tools/capture.tscn, west_capture.tscn);
# a throwaway driver does not, and should not leave one behind. Screenshots land
# in ~/.local/share/godot/app_userdata/Keep Your Ticket/ -- go and look at them.
set -euo pipefail

DRIVER="${1:?usage: drive.sh path/to/driver.gd or .tscn [width height]}"
W="${2:-1280}"
H="${3:-720}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"

eval "$("$(dirname "${BASH_SOURCE[0]}")/setup_headless.sh")"

# A killed run leaves an X lock behind, and the next launch then dies with a
# bare `exit 144` and no message. Clear them rather than debugging that twice.
#
# This is safe *here* and is not safe typed at a prompt: `pkill -f` matches
# whole command lines, and an interactive shell running a command that mentions
# Xvfb has "Xvfb" in its own argv, so the pkill kills the shell it is running
# in. The symptom is a command that stops dead halfway with no error at all.
# Inside a script the argv is the script's path, so there is nothing to match.
pkill -9 -f Xvfb >/dev/null 2>&1 || true
rm -f /tmp/.X*-lock 2>/dev/null || true
rm -rf /tmp/.X11-unix 2>/dev/null || true

if [ "${DRIVER##*.}" = "tscn" ]; then
	# Already a scene. Pass it through as a res:// path and touch nothing.
	SCENE="res://$(realpath --relative-to="$REPO" "$DRIVER")"
else
	# A bare script, so build the one-node scene Godot needs to run it, and
	# take both away again on the way out -- including the .uid Godot writes
	# beside any script it imports, which is pure noise for a throwaway.
	STEM="_drive_$$"
	cp "$DRIVER" "$REPO/$STEM.gd"
	cat > "$REPO/$STEM.tscn" <<TSCN
[gd_scene load_steps=2 format=3]
[ext_resource type="Script" path="res://$STEM.gd" id="1_d"]
[node name="drive" type="Node"]
script = ExtResource("1_d")
TSCN
	trap 'rm -f "$REPO/$STEM.gd" "$REPO/$STEM.tscn" "$REPO/$STEM.gd.uid"' EXIT
	SCENE="$STEM.tscn"
fi

# `--audio-driver Dummy` only quiets the console: a container has no sound
# server, so ALSA and PulseAudio each fail loudly at startup and bury the
# driver's own prints under a screenful of errors that mean nothing.
xvfb-run -a -s "-screen 0 ${W}x${H}x24" \
	"$GODOT" --path "$REPO" --rendering-driver vulkan --audio-driver Dummy \
	--resolution "${W}x${H}" "$SCENE" \
	2>&1 | grep --line-buffered -vE "Leaked instance|RID allocation|ObjectDB instances|resources still in use|PagedAllocator|ALSA lib|snd_" || true

echo
echo "output: $HOME/.local/share/godot/app_userdata/Keep Your Ticket/"
