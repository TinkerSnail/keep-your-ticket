// Photoshop's "Save Document" script event for Keep Your Ticket, turned on and
// off by tools/photoshop/live_update.sh. When the document just saved is a
// prop's canvas, assets/source/textures/<prop>/<prop>_colour.psd, this writes
// its PNG beside it (the hand-back's own export) and sends the prop to the
// game in the background: a headless Blender runs Send to game on
// assets/source/props/<prop>.blend as saved, so Godot shows the painting the
// next time its window is focused. Christina's open Blender is not touched;
// its Keep Your Ticket panel reloads the texture by itself. Any other save,
// and the export's own save of its duplicate (which has no path), does nothing.
//
// The send's output goes to ~/Library/Logs/Keep Your Ticket/live_send.log.
#include "canvas_export.jsxinc"

(function () {
    app.displayDialogs = DialogModes.NO;
    var doc, path;
    try { doc = app.activeDocument; path = doc.fullName.fsName; } catch (e) { return; }
    var m = path.match(/^(.*)\/assets\/source\/textures\/([^\/]+)\/\2_colour\.psd$/);
    if (!m) return;
    var root = m[1], prop = m[2];
    kytExportCanvas(doc, path.replace(/\.psd$/, ".png"));

    var blend = root + "/assets/source/props/" + prop + ".blend";
    if (!new File(blend).exists) return;
    var tools = new File($.fileName).parent.parent.fsName;
    var logs = new Folder("~/Library/Logs/Keep Your Ticket");
    if (!logs.exists) logs.create();
    var q = function (s) { return "'" + s.replace(/'/g, "'\\''") + "'"; };
    app.system("(echo \"== $(date '+%Y-%m-%d %H:%M:%S') " + prop + "\"; "
               + q("/Applications/Blender.app/Contents/MacOS/Blender") + " --background " + q(blend)
               + " --python " + q(tools + "/blender/prop_handback_blender.py") + " -- send)"
               + " >> " + q(logs.fsName + "/live_send.log") + " 2>&1 &");
})();
