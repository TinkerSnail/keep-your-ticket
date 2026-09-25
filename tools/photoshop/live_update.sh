#!/bin/sh
# Keep Your Ticket's Photoshop save hook: on, off or status (the default).
#
#   tools/photoshop/live_update.sh on
#
# While on, every save of a prop canvas PSD
# (assets/source/textures/<prop>/<prop>_colour.psd) writes its PNG and sends the
# prop to the game in the background (tools/photoshop/on_save.jsx); Blender's
# Keep Your Ticket panel reloads the texture, and Godot re-imports the prop
# the next time its window is focused. The tests still wait for a hand-back.
# Photoshop keeps the setting across restarts: it is the "Save Document" event
# in File > Scripts > Script Events Manager.
here=$(cd "$(dirname "$0")" && pwd -P)
mode=${1:-status}
case "$mode" in on|off|status) ;; *) echo "usage: $0 [on|off|status]" >&2; exit 2 ;; esac
osascript -e "tell application id \"com.adobe.Photoshop\" to do javascript file (POSIX file \"$here/install_on_save.jsx\") with arguments {\"$mode\", \"$here/on_save.jsx\"}"
