#!/usr/bin/env node
// A dry run of Photoshop's save hook outside Photoshop (2026-10-14): runs on_save.jsx in node
// against a fake Photoshop for one fake save of <saved path>, and prints what the hook would do:
// each duplicate, the layers it shows, every file it would save and the shell command it would
// start. Nothing is written, saved or run. A script save fires no event, so this is how the hook's
// dispatch is checked without her Photoshop.
//
//   node tools/photoshop/hook_dry_run.js <saved path> [<hook.jsx>]
//   node tools/photoshop/hook_dry_run.js --compare <old hook.jsx> <new hook.jsx> <saved path>
//
// --compare runs both hooks as if each were installed where the new one is (so `$.fileName`,
// the includes and the tools folder are the same) and says whether they act the same; e.g. the
// committed hook (`git show HEAD:tools/photoshop/on_save.jsx`) against the working one, on a
// prop canvas. The fake document's layers follow the path: a prop canvas has its paint and UV
// guide (and its cut-out, if the prop has one); a ground painting has its two groups, the colour
// hidden at 40% and a stray top-level layer, to show the export forcing her view.
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');
const vm = require('vm');

function expand(p) {
  p = String(p && p.fsName ? p.fsName : p);
  return p.startsWith('~') ? path.join(os.homedir(), p.slice(1)) : p;
}

function source(file, dir) {
  return fs.readFileSync(file, 'utf8').replace(/^#include "([^"]+)"\s*$/mg,
    (_, inc) => source(path.join(dir, inc), dir));
}

function run(hookFile, installedAs, saved) {
  const calls = [];
  const say = (s) => calls.push(s);
  class Folder {
    constructor(p) { this.fsName = path.resolve(expand(p)); }
    get exists() { return fs.existsSync(this.fsName); }
    get parent() { return new Folder(path.dirname(this.fsName)); }
    get name() { return path.basename(this.fsName); }
    create() { say('make folder ' + this.fsName); return true; }
  }
  class File extends Folder {
    open() { return true; }
    writeln(s) { say('log to ' + path.basename(this.fsName) + ': ' + s); }
    close() {}
  }
  const layer = (name, typename, extra) => Object.assign(
    { name, typename, visible: true, opacity: 100, allLocked: false, blendMode: 'NORMAL', isBackgroundLayer: false }, extra || {});
  const describe = (o) => Object.keys(o).filter((k) => k !== 'kind').sort().map((k) => k + '=' + o[k]).join(' ');
  function makeDoc(p, layers) {
    let bits = 16;
    return {
      name: p ? path.basename(p) : 'untitled', layers, saved: true,
      get fullName() { if (!p) throw new Error('no path'); return { fsName: p }; },
      get bitsPerChannel() { return bits; },
      set bitsPerChannel(v) { say('  bits per channel -> ' + v); bits = v; },
      duplicate(n) {
        say('duplicate ' + this.name + ' as ' + n);
        const d = makeDoc(null, layers.map((l) => Object.assign({}, l)));
        d.name = n;
        return d;
      },
      flatten() { say('  flatten'); },
      saveAs(file, o, asCopy) {
        say('  save ' + o.kind + ' (' + describe(o) + ')' + (asCopy ? ' as a copy' : '') + ' -> ' + file.fsName
            + '; showing [' + this.layers.filter((l) => l.visible).map((l) => l.name + (l.opacity !== 100 ? ' ' + l.opacity + '%' : '')).join(', ') + ']');
      },
      close(how) { say('  close ' + this.name + ' (' + how + ')'); },
    };
  }
  let layers;
  const prop = saved.match(/\/assets\/source\/textures\/([^/]+)\/\1_colour\.psd$/);
  if (/\/assets\/source\/world_ground\/paint\/([^/]+)\/\1\.psd$/.test(saved)) {
    layers = [layer('colour', 'LayerSet', { visible: false, opacity: 40 }), layer('height', 'LayerSet'),
              layer('reference photo', 'ArtLayer')];
  } else if (prop) {
    layers = [layer('UV guide (hide before export)', 'ArtLayer', { allLocked: true }), layer('paint', 'ArtLayer')];
    if (fs.existsSync(saved.replace(/_colour\.psd$/, '_cutout.png'))) {
      layers.splice(1, 0, layer('cut-out (black cuts, white keeps)', 'ArtLayer', { blendMode: 'MULTIPLY', visible: false }));
    }
  } else {
    layers = [layer('Layer 1', 'ArtLayer')];
  }
  const doc = makeDoc(saved, layers);
  const ctx = {
    app: { displayDialogs: 'ALL', activeDocument: doc, system: (cmd) => { say('run: ' + cmd); return 0; } },
    File, Folder,
    DialogModes: { NO: 'NO' }, SaveOptions: { DONOTSAVECHANGES: 'DONOTSAVECHANGES' },
    BitsPerChannelType: { EIGHT: 8, SIXTEEN: 16 }, BlendMode: { NORMAL: 'NORMAL' },
    Extension: { LOWERCASE: 'LOWERCASE' }, TIFFEncoding: { NONE: 'NONE' }, ByteOrder: { IBM: 'IBM', MACOS: 'MACOS' },
    PNGSaveOptions: function () { this.kind = 'PNG'; },
    TiffSaveOptions: function () { this.kind = 'TIFF'; },
  };
  const dir = path.dirname(installedAs);
  ctx.$ = {
    fileName: installedAs,
    evalFile: (f) => { const p = expand(f); say('load ' + p); vm.runInContext(source(p, path.dirname(p)), ctx, { filename: p }); },
  };
  vm.createContext(ctx);
  vm.runInContext(source(hookFile, dir), ctx, { filename: hookFile });
  return calls;
}

function main(argv) {
  if (argv[0] === '--compare') {
    const [oldHook, newHook, saved] = argv.slice(1).map((p) => path.resolve(expand(p)));
    const live = newHook;
    const a = run(oldHook, live, saved);
    const b = run(newHook, live, saved);
    console.log('save of ' + saved);
    console.log('-- old hook (' + path.basename(oldHook) + '):\n' + (a.length ? a.join('\n') : '(nothing)'));
    console.log('-- new hook (' + path.basename(newHook) + '):\n' + (b.length ? b.join('\n') : '(nothing)'));
    const same = JSON.stringify(a) === JSON.stringify(b);
    console.log(same ? 'SAME: the two hooks do exactly the same for this save' : 'DIFFERENT');
    return same ? 0 : 1;
  }
  const saved = path.resolve(expand(argv[0]));
  const hook = path.resolve(argv[1] || path.join(__dirname, 'on_save.jsx'));
  const calls = run(hook, hook, saved);
  console.log('save of ' + saved + '\n' + (calls.length ? calls.join('\n') : '(the hook does nothing)'));
  return 0;
}

if (process.argv.length < 3) {
  console.error('usage: node hook_dry_run.js <saved path> [<hook.jsx>] | --compare <old.jsx> <new.jsx> <saved path>');
  process.exit(2);
}
process.exit(main(process.argv.slice(2)));
