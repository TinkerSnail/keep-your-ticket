// Exports a ground painting's "height" and "colour" groups for tools/ground_paint.py save when
// the save hook did not (it was off): the hook's own export (ground_save.jsx), from the saved
// document. Run by ground_paint.py save through AppleScript:
//   do javascript file "ground_export.jsx" with arguments {psd}
// If the painting is open, the open document is used and refused if it has unsaved changes, so
// the export matches the saved PSD; if not, it is opened and closed again. Returns a one-line
// report, "EXPORTED <stamp>" when done.
#include "ground_save.jsx"
app.displayDialogs = DialogModes.NO;
var target = new File(arguments[0]), doc = null, opened = false;
for (var i = 0; i < app.documents.length; i++) {
    try { if (app.documents[i].fullName.fsName == target.fsName) doc = app.documents[i]; } catch (e) {}
}
if (doc == null) { doc = app.open(target); opened = true; }
var result;
if (!doc.saved) {
    result = "REFUSED: " + doc.name + " has unsaved changes; save it in Photoshop first";
} else {
    try { result = "EXPORTED " + kytGroundExport(doc, target.fsName); }
    catch (e) { result = "FAILED " + e; }
}
if (opened) doc.close(SaveOptions.DONOTSAVECHANGES);
result;
