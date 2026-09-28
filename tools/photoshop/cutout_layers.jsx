// Gives a crown's new PSD (paint_canvas.py --leaflets) the two layers of its
// cut-out:
//   "leaf under the paint (Claude)", at the bottom, locked: the canvas colour,
//     opaque, so a see-through spot in the paint exports as leaf, not white;
//   "cut-out (black cuts, white keeps)", directly above "paint", at Multiply,
//     so the gaps show black over the painting: the leaflets themselves, which
//     Christina paints. Every export writes it to <prop>_cutout.png at Normal
//     (canvas_export.jsxinc) and apply_holes.py makes it the alpha.
// A PSD that already has a "cut-out" layer is left alone: it may be painted.
// Layers are copied between documents, which keeps their position (Place does
// not). The paint layer is selected again after, and the PSD saved. Run by
// tools/prop_handback.py --open through AppleScript:
//   do javascript file "cutout_layers.jsx" with arguments {psd, underlay_png, cutout_png}
// With a fourth argument "replace" (prop_handback.py --cutout-layer, after
// paint_canvas.py --leaflets --cutout-only), the existing cut-out layer's
// pixels are replaced by cutout_png instead, keeping its name, place, blend
// mode, opacity and visibility, and the PSD is not saved: she looks first.
// Photoshop's history can take it back.
// Returns a one-line report.
app.displayDialogs = DialogModes.NO;
var UNDER = "leaf under the paint (Claude)", CUT = "cut-out (black cuts, white keeps)";
var target = new File(arguments[0]), doc = null;
for (var i = 0; i < app.documents.length; i++) {
    try { if (app.documents[i].fullName.fsName == target.fsName) doc = app.documents[i]; } catch (e) {}
}
if (doc == null) doc = app.open(target);
app.activeDocument = doc;
var paint = null, kept = null;
for (var k = 0; k < doc.layers.length; k++) {
    if (doc.layers[k].name == "paint") paint = doc.layers[k];
    if (doc.layers[k].name.indexOf("cut-out") == 0) kept = doc.layers[k];
}

function bring(path, name) {
    var src = app.open(new File(path));
    var copy = src.layers[0].duplicate(doc, ElementPlacement.PLACEATBEGINNING);
    src.close(SaveOptions.DONOTSAVECHANGES);
    app.activeDocument = doc;
    copy.name = name;
    return copy;
}

var result;
if (arguments[3] == "replace") {
    if (kept == null) {
        result = "FAIL " + doc.name + " has no cut-out layer to replace";
    } else {
        var wasSaved = doc.saved, old = kept, fresh = bring(arguments[2], old.name);
        fresh.move(old, ElementPlacement.PLACEBEFORE);
        fresh.blendMode = old.blendMode;
        fresh.opacity = old.opacity;
        fresh.visible = old.visible;
        if (old.allLocked) old.allLocked = false;
        old.remove();
        if (paint != null) doc.activeLayer = paint;
        result = "REPLACED '" + fresh.name + "' in " + doc.name + "; not saved"
            + (wasSaved ? "" : " (it had other unsaved changes)");
    }
} else if (kept != null) {
    result = "KEPT " + doc.name + " already has '" + kept.name + "'";
} else if (paint == null) {
    result = "FAIL " + doc.name + " has no 'paint' layer";
} else {
    var under = bring(arguments[1], UNDER);
    under.move(doc.layers[doc.layers.length - 1], ElementPlacement.PLACEAFTER);
    under.allLocked = true;
    var cut = bring(arguments[2], CUT);
    cut.move(paint, ElementPlacement.PLACEBEFORE);
    cut.blendMode = BlendMode.MULTIPLY;
    doc.activeLayer = paint;
    doc.save();
    var names = [];
    for (var n = 0; n < doc.layers.length; n++) names.push(doc.layers[n].name);
    result = "LAYERS " + names.join(" / ") + "; saved";
}
result;
