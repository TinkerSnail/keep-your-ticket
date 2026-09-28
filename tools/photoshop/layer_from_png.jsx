// Puts a PNG into a prop's open canvas PSD as a named layer, directly above
// another layer (by name), replacing a layer of the same name if there is one,
// and doesn't save: she looks first, and Photoshop's history can take it back.
// For a starting look she may keep, hide or paint over, e.g. a crown's
// "shading (Claude)" (paint_canvas.py --leaflets --shading-only). The layer is
// copied between documents, which keeps its position (Place does not).
// Run by tools/prop_handback.py (--shading-layer) through AppleScript:
//   do javascript file "layer_from_png.jsx" with arguments {psd, png, name, above[, blend]}
// `blend` is a Photoshop blend mode by its name in BlendMode ("COLORBLEND" for
// Color), Normal when left out.
// Returns a one-line report.
app.displayDialogs = DialogModes.NO;
// Not `name`: at the top level of a Photoshop script that is the app's own name.
var target = new File(arguments[0]), layerName = arguments[2], aboveName = arguments[3], doc = null;
for (var i = 0; i < app.documents.length; i++) {
    try { if (app.documents[i].fullName.fsName == target.fsName) doc = app.documents[i]; } catch (e) {}
}
if (doc == null) doc = app.open(target);
app.activeDocument = doc;
var wasSaved = doc.saved, above = null, old = null;
for (var k = 0; k < doc.layers.length; k++) {
    if (doc.layers[k].name == aboveName) above = doc.layers[k];
    if (doc.layers[k].name == layerName) old = doc.layers[k];
}
var result;
if (above == null) {
    result = "FAIL " + doc.name + " has no '" + aboveName + "' layer";
} else {
    var src = app.open(new File(arguments[1]));
    var layer = src.layers[0].duplicate(doc, ElementPlacement.PLACEATBEGINNING);
    src.close(SaveOptions.DONOTSAVECHANGES);
    app.activeDocument = doc;
    layer.name = layerName;
    if (arguments.length > 4 && arguments[4] != "") layer.blendMode = BlendMode[arguments[4]];
    // Whether there was one, kept before it is removed: a removed layer is an
    // invalid object and even comparing it throws.
    var replaced = old != null;
    layer.move(replaced ? old : above, ElementPlacement.PLACEBEFORE);
    if (replaced) {
        if (old.allLocked) old.allLocked = false;
        old.remove();
    }
    doc.activeLayer = above;
    result = (replaced ? "REPLACED '" : "ADDED '") + layerName + "' above '" + aboveName + "' in " + doc.name
        + "; not saved" + (wasSaved ? "" : " (it had other unsaved changes)");
}
result;
