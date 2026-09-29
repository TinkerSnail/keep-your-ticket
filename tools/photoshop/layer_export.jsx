// Saves one layer of a prop's canvas PSD alone, as a PNG with its
// transparency, from the document as it is open (unsaved changes included),
// or from the file if it isn't open. The work is done on a duplicate, closed
// after, so the document is not touched.
//
// Used by tools/prop_handback.py for a perforated prop's "metal under the
// holes (Claude)" layer: her paint layer's own colours are spread into its
// see-through spots, so holes cut again after she has painted leave no mark
// of the old ones (the street bin, 2026-09-27: the old, smaller quatrefoils
// showed through her paint as grey plus signs).
//
// Run through AppleScript:
//   do javascript file "layer_export.jsx" with arguments {psd, png, layer name}
// Returns a one-line report.
app.displayDialogs = DialogModes.NO;
var target = new File(arguments[0]), pngPath = arguments[1], wanted = arguments[2];
var doc = null, opened = false;
for (var i = 0; i < app.documents.length; i++) {
    try { if (app.documents[i].fullName.fsName == target.fsName) doc = app.documents[i]; } catch (e) {}
}
if (doc == null) { doc = app.open(target); opened = true; }
var result;
var found = false;
for (var k = 0; k < doc.layers.length; k++) if (doc.layers[k].name == wanted) found = true;
if (!found) {
    result = "FAIL " + doc.name + " has no '" + wanted + "' layer";
} else {
    var dup = doc.duplicate("layer_export", false);
    try {
        for (var n = dup.layers.length - 1; n >= 0; n--) {
            var layer = dup.layers[n];
            if (layer.name == wanted) {
                if (!layer.visible) layer.visible = true;
                continue;
            }
            if (layer.allLocked) layer.allLocked = false;
            if (layer.isBackgroundLayer) layer.isBackgroundLayer = false;
            layer.remove();
        }
        if (dup.bitsPerChannel != BitsPerChannelType.EIGHT) dup.bitsPerChannel = BitsPerChannelType.EIGHT;
        var png = new PNGSaveOptions(); png.compression = 9; png.interlaced = false;
        dup.saveAs(new File(pngPath), png, true, Extension.LOWERCASE);
        result = "LAYER " + wanted + " of " + doc.name + (doc.saved ? "" : " (with unsaved changes)");
    } finally {
        dup.close(SaveOptions.DONOTSAVECHANGES);
    }
}
if (opened) doc.close(SaveOptions.DONOTSAVECHANGES);
result;
