// The ground's half of Photoshop's save hook (2026-10-14, height-grid Stage 3). on_save.jsx
// loads this file afresh at every save of a ground painting,
// assets/source/world_ground/paint/<name>/<name>.psd (made by tools/ground_paint.py open), and
// calls kytGroundSaved, so a change here takes effect at the next save with nothing to restart
// or register again. ground_export.jsx includes it for the same export run by hand.
//
// The export: each of the painting's two top-level groups, "height" and "colour", alone, whatever
// her view of it (shown, at 100%), every other top-level layer or group hidden, from a duplicate
// closed after, so her document is not touched. Written as Photoshop writes it: 16 bits,
// uncompressed TIFF with its transparency, <name>/exports/height-<stamp>.tif and
// colour-<stamp>.tif. Then tools/ground_paint.py save runs in the background and makes the grid
// edit. Both log to ~/Library/Logs/Keep Your Ticket/ground_paint.log.
//
// ExtendScript is ES3: no String trim, no Array indexOf, no JSON. A lock or visibility is set only
// when it has to change (canvas_export.jsxinc, 2026-09-25).

function kytGroundLogPath() {
    var logs = new Folder("~/Library/Logs/Keep Your Ticket");
    if (!logs.exists) logs.create();
    return logs.fsName + "/ground_paint.log";
}

function kytGroundLog(line) {
    try {
        var f = new File(kytGroundLogPath());
        f.encoding = "UTF-8";
        if (f.open("a")) { f.writeln(line); f.close(); }
    } catch (e) {}
}

function kytGroundName(layer) {
    return layer.name.replace(/^\s+|\s+$/g, "").toLowerCase();
}

function kytGroundIs(layer, name) {
    return layer.typename == "LayerSet" && kytGroundName(layer) == name;
}

// Throws unless the document has exactly one top-level group called `name`.
function kytGroundCheck(doc, name) {
    var count = 0;
    for (var i = 0; i < doc.layers.length; i++) if (kytGroundIs(doc.layers[i], name)) count++;
    if (count != 1) throw new Error(doc.name + " has " + count + " top-level groups called '" + name + "', not one");
}

function kytGroundSaveGroup(doc, name, path) {
    kytGroundCheck(doc, name);
    var dup = doc.duplicate("ground_export", false);
    try {
        for (var k = 0; k < dup.layers.length; k++) {
            var layer = dup.layers[k], show = kytGroundIs(layer, name);
            if (layer.visible == show && (!show || layer.opacity == 100)) continue;
            if (layer.allLocked) layer.allLocked = false;
            if (layer.visible != show) layer.visible = show;
            if (show && layer.opacity != 100) layer.opacity = 100;
        }
        var tiff = new TiffSaveOptions();
        tiff.imageCompression = TIFFEncoding.NONE;
        tiff.byteOrder = ByteOrder.IBM;
        tiff.layers = false;
        tiff.transparency = true;
        tiff.alphaChannels = false;
        tiff.annotations = false;
        tiff.spotColors = false;
        tiff.embedColorProfile = true;
        tiff.interleaveChannels = true;
        tiff.saveImagePyramid = false;
        dup.saveAs(new File(path), tiff, true, Extension.LOWERCASE);
    } finally {
        dup.close(SaveOptions.DONOTSAVECHANGES);
    }
}

// Both groups, under one stamp (milliseconds); returns the stamp.
function kytGroundExport(doc, psdPath) {
    var out = new Folder(new File(psdPath).parent.fsName + "/exports");
    if (!out.exists) out.create();
    var stamp = String(new Date().getTime());
    kytGroundSaveGroup(doc, "height", out.fsName + "/height-" + stamp + ".tif");
    kytGroundSaveGroup(doc, "colour", out.fsName + "/colour-" + stamp + ".tif");
    return stamp;
}

// The hook's ground case: export, then the grid edit in the background.
function kytGroundSaved(doc, psdPath, photoshopDir) {
    var name = psdPath.replace(/^.*\//, "").replace(/\.psd$/i, "");
    var stamp;
    try {
        stamp = kytGroundExport(doc, psdPath);
    } catch (e) {
        kytGroundLog("== " + name + ": the export failed, so nothing went to the grid: " + e);
        return;
    }
    var q = function (s) { return "'" + s.replace(/'/g, "'\\''") + "'"; };
    var tools = new Folder(photoshopDir).parent.fsName;
    var py = "/opt/homebrew/bin/python3";
    if (!new File(py).exists) py = "/usr/local/bin/python3";
    if (!new File(py).exists) py = "python3";
    app.system("(echo \"== $(date '+%Y-%m-%d %H:%M:%S') " + name + " (export " + stamp + ")\"; "
               + q(py) + " -u " + q(tools + "/ground_paint.py") + " save " + q(psdPath) + " --no-photoshop)"
               + " >> " + q(kytGroundLogPath()) + " 2>&1 &");
}
