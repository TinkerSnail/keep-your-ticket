// Open a prop's paint canvas in Photoshop, ready to paint: its PSD if there is
// one; otherwise a new PSD made from the colour PNG, with the colour as a
// "paint" layer and the UV outlines on top as a locked "UV guide (hide before
// export)" layer, saved beside the PNG and left open. An existing PSD is never
// replaced: it may hold Christina's painting.
//
// Run through AppleScript:
//   do javascript file "open_canvas.jsx" with arguments {colour_png, guide_png, psd}
// Returns a one-line report.
app.displayDialogs = DialogModes.NO;
var pngPath = arguments[0], guidePath = arguments[1], psdPath = arguments[2];
var psd = new File(psdPath), result;
var already = null;
for (var i = 0; i < app.documents.length; i++) {
    try { if (app.documents[i].fullName.fsName == psd.fsName) already = app.documents[i]; } catch (e) {}
}
if (already != null) {
    app.activeDocument = already;
    result = "OPEN " + already.name + " (already open)";
} else if (psd.exists) {
    var doc = app.open(psd);
    result = "OPEN " + doc.name;
} else {
    var doc = app.open(new File(pngPath));
    doc.activeLayer.isBackgroundLayer = false;
    doc.activeLayer.name = "paint";
    var desc = new ActionDescriptor();
    desc.putPath(charIDToTypeID("null"), new File(guidePath));
    desc.putEnumerated(charIDToTypeID("FTcs"), charIDToTypeID("QCSt"), charIDToTypeID("Qcsa"));
    executeAction(charIDToTypeID("Plc "), desc, DialogModes.NO);
    var guide = doc.activeLayer;
    guide.name = "UV guide (hide before export)";
    guide.rasterize(RasterizeType.ENTIRELAYER);
    // Photoshop's Place can land off target; move the guide to where its
    // outlines sit in the PNG (their bounds are passed as arguments 3-4).
    var b = guide.bounds;
    guide.translate(new UnitValue(Number(arguments[3]) - b[0].as("px"), "px"),
                    new UnitValue(Number(arguments[4]) - b[1].as("px"), "px"));
    guide.allLocked = true;
    doc.activeLayer = doc.artLayers.getByName("paint");
    var opts = new PhotoshopSaveOptions(); opts.layers = true;
    doc.saveAs(psd, opts, false, Extension.LOWERCASE);
    b = guide.bounds;
    result = "CREATED " + doc.name + " guide at " + b[0].as("px") + "," + b[1].as("px");
}
result;
