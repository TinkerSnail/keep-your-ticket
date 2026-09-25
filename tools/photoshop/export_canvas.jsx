// Export a prop's painted canvas from its PSD: a flattened copy with every
// "UV guide" layer hidden, 8 bits, saved as PNG. The PSD itself is not touched.
//
// Run from tools/prop_handback.py through AppleScript:
//   do javascript file "export_canvas.jsx" with arguments {psd, png, allow_unsaved}
// If the PSD is open, the open document is used (and refused if it has unsaved
// changes, unless allow_unsaved is "1", so the PNG always matches a saved PSD);
// if not, it is opened and closed again. Returns a one-line report.
#include "canvas_export.jsxinc"
app.displayDialogs = DialogModes.NO;
var psdPath = arguments[0], pngPath = arguments[1], allowUnsaved = arguments[2] == "1";
var target = new File(psdPath), doc = null, opened = false;
for (var i = 0; i < app.documents.length; i++) {
    try { if (app.documents[i].fullName.fsName == target.fsName) doc = app.documents[i]; } catch (e) {}
}
if (doc == null) { doc = app.open(target); opened = true; }
var result;
if (!doc.saved && !allowUnsaved) {
    result = "REFUSED: " + doc.name + " has unsaved changes; save it in Photoshop first";
} else {
    kytExportCanvas(doc, pngPath);
    result = "EXPORTED " + doc.name + " " + doc.width.as("px") + "x" + doc.height.as("px") + (doc.saved ? "" : " (with unsaved changes)");
}
if (opened) doc.close(SaveOptions.DONOTSAVECHANGES);
result;
