// Puts on_save.jsx on Photoshop's "Save Document" event, or takes it off
// (File > Scripts > Script Events Manager shows the same list). Run by
// tools/photoshop/live_update.sh:
//   do javascript file "install_on_save.jsx" with arguments {"on"|"off"|"status", <on_save.jsx path>}
// Photoshop keeps its script events across restarts. "off" removes only this
// hook, leaving any other script event as it was. Returns a one-line report.
var mode = arguments[0], hook = new File(arguments[1]);
if (mode == "on" || mode == "off") {
    for (var i = app.notifiers.length - 1; i >= 0; i--) {
        if (app.notifiers[i].eventFile.fsName == hook.fsName) app.notifiers[i].remove();
    }
}
if (mode == "on") {
    app.notifiersEnabled = true;
    app.notifiers.add("save", hook);
}
var ours = false, others = 0;
for (var j = 0; j < app.notifiers.length; j++) {
    if (app.notifiers[j].eventFile.fsName == hook.fsName && app.notifiers[j].event == "save") ours = true;
    else others++;
}
(ours && app.notifiersEnabled ? "ON: saving a prop canvas PSD updates the prop" : "OFF")
    + (others ? "; " + others + " other script event" + (others > 1 ? "s" : "") + " left as they were" : "");
