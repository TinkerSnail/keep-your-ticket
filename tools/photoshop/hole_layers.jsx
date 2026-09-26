// Gives a perforated prop's PSD the two layers that keep its painting
// independent of where the holes fall:
//   "metal under the holes (Claude)", at the bottom, locked: the canvas colour,
//     opaque, so a see-through spot in the paint exports as metal, not white;
//   "UV guide: holes (Claude)", at the top, locked: the holes, translucent, to
//     paint by; hidden on export like every "UV guide" layer.
// Layers of those names already there are replaced, so the guide follows the
// holes when they are cut again (paint_canvas.py --holes-only). Layers are
// copied between documents, which keeps their position (Place does not). The
// paint layer is selected again after. Run by tools/prop_handback.py
// (--open, --holes) through AppleScript:
//   do javascript file "hole_layers.jsx" with arguments {psd, underlay_png, guide_png, "save"|"nosave"}
// Returns a one-line report.
app.displayDialogs = DialogModes.NO;
var UNDER = "metal under the holes (Claude)", GUIDE = "UV guide: holes (Claude)";
var target = new File(arguments[0]), doc = null;
for (var i = 0; i < app.documents.length; i++) {
    try { if (app.documents[i].fullName.fsName == target.fsName) doc = app.documents[i]; } catch (e) {}
}
if (doc == null) doc = app.open(target);
app.activeDocument = doc;
var paint = null;
for (var k = doc.layers.length - 1; k >= 0; k--) {
    var layer = doc.layers[k];
    if (layer.name == UNDER || layer.name == GUIDE) {
        if (layer.allLocked) layer.allLocked = false;
        layer.remove();
    } else if (layer.name == "paint") {
        paint = layer;
    }
}

function bring(path, name) {
    var src = app.open(new File(path));
    var copy = src.layers[0].duplicate(doc, ElementPlacement.PLACEATBEGINNING);
    src.close(SaveOptions.DONOTSAVECHANGES);
    app.activeDocument = doc;
    copy.name = name;
    return copy;
}
var under = bring(arguments[1], UNDER);
under.move(doc.layers[doc.layers.length - 1], ElementPlacement.PLACEAFTER);
under.allLocked = true;
var guide = bring(arguments[2], GUIDE);
guide.allLocked = true;
if (paint) doc.activeLayer = paint;
if (arguments[3] == "save") doc.save();
var names = [];
for (var n = 0; n < doc.layers.length; n++) names.push(doc.layers[n].name);
"LAYERS " + names.join(" / ") + (arguments[3] == "save" ? "; saved" : "; not saved");
