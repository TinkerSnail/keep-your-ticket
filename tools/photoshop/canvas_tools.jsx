// The Blender panel's buttons for a prop's canvas that is open in Photoshop.
// Run through AppleScript by the Keep Your Ticket extension (photoshop.py):
//   do javascript file "canvas_tools.jsx" with arguments {"guide", <psd>, "show"|"hide"}
//   do javascript file "canvas_tools.jsx" with arguments {"patch", <psd>, <name>}
// "guide" shows or hides every "UV guide" layer with Photoshop's own Show and
// Hide, by layer id, which a locked layer allows; the selected layer stays
// selected. "patch" adds an empty layer "<name> patch" ("<name> patch 2", ...)
// directly under the guide and selects it, for dressing: the clean surface
// painted over a spot that becomes a decal (prop-pipeline.md stage 7).
// Neither saves the PSD. Returns a one-line report, NOTOPEN when the canvas
// isn't open in Photoshop.
app.displayDialogs = DialogModes.NO;
var action = arguments[0], target = new File(arguments[1]), arg = arguments[2];
var doc = null;
for (var i = 0; i < app.documents.length; i++) {
    try { if (app.documents[i].fullName.fsName == target.fsName) doc = app.documents[i]; } catch (e) {}
}

function guides(d) {
    var found = [];
    for (var k = 0; k < d.layers.length; k++) {
        if (d.layers[k].name.indexOf("UV guide") == 0) found.push(d.layers[k]);
    }
    return found;
}

function showGuides(d, show) {
    var layers = guides(d);
    if (!layers.length) return "NOGUIDE " + d.name + " has no UV guide layer";
    app.activeDocument = d;
    var list = new ActionList();
    for (var k = 0; k < layers.length; k++) {
        var ref = new ActionReference();
        ref.putIdentifier(charIDToTypeID("Lyr "), layers[k].id);
        list.putReference(ref);
    }
    var desc = new ActionDescriptor();
    desc.putList(charIDToTypeID("null"), list);
    executeAction(charIDToTypeID(show ? "Shw " : "Hd  "), desc, DialogModes.NO);
    return "GUIDE " + (show ? "shown" : "hidden");
}

function addPatch(d, base) {
    app.activeDocument = d;
    var taken = {};
    for (var k = 0; k < d.layers.length; k++) taken[d.layers[k].name] = true;
    var name = base + " patch";
    for (var n = 2; taken[name]; n++) name = base + " patch " + n;
    var layer = d.artLayers.add();
    layer.name = name;
    var layers = guides(d);
    if (layers.length) layer.move(layers[0], ElementPlacement.PLACEAFTER);
    d.activeLayer = layer;
    return "PATCH " + name;
}

var result;
if (doc == null) result = "NOTOPEN " + target.name;
else if (action == "guide") result = showGuides(doc, arg == "show");
else if (action == "patch") result = addPatch(doc, arg);
else result = "REFUSED unknown action " + action;
result;
