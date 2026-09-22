#!/usr/bin/env python3
"""Render the mounted range-geography audit as a self-contained review map."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mirror", type=Path)
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    html = TEMPLATE.replace("__AUDIT_DATA__", payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    if args.mirror:
        args.mirror.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.output, args.mirror)


TEMPLATE = r'''<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Range geography recovery audit · 2026-09-12</title>
<body>
<main>
  <header>
    <p class="eyebrow">Mounted-coordinate recovery gate · 2026-09-12</p>
    <div class="title-row">
      <div><h1>Range geography recovery audit</h1><p class="lede">The current world contains parallel terrain owners in the same geographic volume. This is a source model failure, not a camera or palette problem.</p></div>
      <div class="verdict"><b>FAIL</b><span>construction remains frozen</span></div>
    </div>
  </header>

  <section class="metrics" aria-label="Audit summary">
    <article><b id="object-count"></b><span>measured objects</span></article>
    <article><b id="overlap-count"></b><span>sampled plan intersections</span></article>
    <article><b id="cross-owner-count"></b><span>cross-source intersections</span></article>
    <article><b>5</b><span>owner-volume sections</span></article>
  </section>

  <section class="finding">
    <div>
      <p class="eyebrow">Primary finding</p>
      <h2>The Blender range is not behind the generated range</h2>
      <p>The north and middle Blender bodies occupy the generated mainland, northern coast and road-corridor footprints. The old green midground and transition sit in that same mounted volume. Southward, one long Blender lowland crosses the generated mainland and then overlaps the separately authored city foothills and connector chain.</p>
    </div>
    <ul id="critical-list"></ul>
  </section>

  <section class="plan-section">
    <div class="section-head"><div><p class="eyebrow">Plan view</p><h2>Ownership footprints · north up</h2><p>Every filled cell is touched by a projected source triangle. Cell size is <span id="cell-size"></span>m; overlaps are conservative at that resolution.</p></div><div class="filters" id="filters"></div></div>
    <div class="plan-grid">
      <div class="canvas-wrap"><canvas id="plan" width="920" height="1280" aria-label="Plan view of mounted geography colored by source owner"></canvas><div class="axis x-axis">world x (m)</div><div class="axis z-axis">world z (m) · north</div></div>
      <aside id="selection"><p class="eyebrow">Selected owner</p><h3>Click an inventory row</h3><p>The plan will isolate that source and list every sampled footprint intersection.</p></aside>
    </div>
    <div class="legend"><span><i class="generated"></i>generated geography</span><span><i class="range"></i>range Blender source</span><span><i class="city"></i>city Blender source</span><span><i class="infra"></i>roads / protected bridge</span><span><i class="reference"></i>park and town references</span></div>
  </section>

  <section>
    <p class="eyebrow">Cross-sections</p><h2>Owner volumes along the five required transects</h2>
    <p class="section-note">Bands show the minimum-to-maximum source volume touched in each plan cell. They expose ownership stacking; they are not smoothed terrain profiles.</p>
    <div id="sections" class="sections"></div>
  </section>

  <section>
    <div class="section-head"><div><p class="eyebrow">Mounted inventory</p><h2>Every terrain owner implicated in the range composition</h2></div><label class="search">Filter <input id="search" type="search" placeholder="north, road, foothill…"></label></div>
    <div class="table-wrap"><table><thead><tr><th>Owner / object</th><th>Role</th><th>World footprint x / z</th><th>Height</th><th>Material</th><th>Collision</th><th>Intersects</th></tr></thead><tbody id="inventory"></tbody></table></div>
  </section>

  <section class="decision">
    <div><p class="eyebrow">Decision required before geometry moves</p><h2>Choose one canonical mountain owner</h2><p class="recommendation">Recommended: migrate the complete artistic range shape to an editor-owned source.</p></div>
    <article><h3>A · Editor-owned full range <span>recommended</span></h3><p><b>Easier:</b> Christina can sculpt the real silhouette, sections and connections directly; redundant bodies can be removed in one coherent source.</p><p><b>Harder:</b> road cuts, town-valley cuts, collision and support must be re-derived from that source, and the legacy height-function range must be retired carefully.</p></article>
    <article><h3>B · Generated crescent remains canonical</h3><p><b>Easier:</b> existing road/town grading formulas and structural tests survive; recovery is smaller.</p><p><b>Harder:</b> the primary mountain stays code-owned and difficult to reshape; all overlapping Blender bodies must be removed or moved wholly outside the generated land.</p></article>
  </section>

  <section class="protected"><b>Frozen in both options</b><span>NT-1 Cascading Staircases · NT-2 Terraced Fountain · Christina’s cameras and saved views · relocated city, bridge, ferries and peninsula source · clean pre-geographic-repair checkpoint</span></section>
  <footer>Source: <code>range_geography_audit.gd</code> measuring the three singular mounts and road source in Godot 4.7.1. No scene, Blender file, camera or geometry was saved by the audit.</footer>
</main>
<script>
const DATA=__AUDIT_DATA__;
const COLORS={generated:'#9a7042',range:'#2d7562',city:'#865b86',infra:'#405f79',reference:'#bb3f3a'};
const state={visible:{generated:true,range:true,city:true,infra:true},selected:null};
const inventory=new Map(DATA.inventory.map(r=>[r.id,r]));
const sourceGroup=r=>r.id.startsWith('range__')?'range':r.id.startsWith('city__')?(r.category==='terrain'?'city':'infra'):r.id.startsWith('road__')?'infra':'generated';
const short=id=>id.replace(/^generated_/,'generated · ').replace(/^range__/,'range · ').replace(/^city__/,'city · ').replace(/^road__/,'road · ').replaceAll('_',' ');
const fmt=n=>Math.round(n).toLocaleString();
const ownerName=g=>({generated:'generated geography',range:'range Blender',city:'city Blender',infra:'infrastructure'})[g];

document.querySelector('#object-count').textContent=DATA.inventory.length;
document.querySelector('#overlap-count').textContent=DATA.sampled_plan_overlaps.length;
const cross=DATA.sampled_plan_overlaps.filter(o=>sourceGroup(inventory.get(o.a))!==sourceGroup(inventory.get(o.b)));
document.querySelector('#cross-owner-count').textContent=cross.length;
document.querySelector('#cell-size').textContent=DATA.plan_cell_metres;

const critical=cross.sort((a,b)=>b.sampled_area_m2-a.sampled_area_m2).slice(0,6);
document.querySelector('#critical-list').innerHTML=critical.map(o=>`<li><b>${short(o.a)}</b><span>with ${short(o.b)} · ${(o.sampled_area_m2/1e6).toFixed(2)} km² sampled cells</span></li>`).join('');

const filters=document.querySelector('#filters');
for(const group of ['generated','range','city','infra']){
  const label=document.createElement('label');
  label.innerHTML=`<input type="checkbox" checked data-group="${group}"><i style="background:${COLORS[group]}"></i>${ownerName(group)}`;
  filters.append(label);
}
filters.addEventListener('change',e=>{if(e.target.dataset.group){state.visible[e.target.dataset.group]=e.target.checked;drawPlan();}});

const canvas=document.querySelector('#plan'),ctx=canvas.getContext('2d');
const allBounds=DATA.inventory.map(r=>r.bounds);
const minX=Math.floor(Math.min(...allBounds.map(b=>b.min_x))/200)*200;
const maxX=Math.ceil(Math.max(...allBounds.map(b=>b.max_x))/200)*200;
const minZ=Math.floor(Math.min(...allBounds.map(b=>b.min_z))/200)*200;
const maxZ=Math.ceil(Math.max(...allBounds.map(b=>b.max_z))/200)*200;
const pad=42,scale=Math.min((canvas.width-pad*2)/(maxX-minX),(canvas.height-pad*2)/(maxZ-minZ));
const tx=x=>pad+(x-minX)*scale, tz=z=>pad+(z-minZ)*scale;
function drawPlan(){
  ctx.clearRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#f3f0e7';ctx.fillRect(0,0,canvas.width,canvas.height);
  ctx.strokeStyle='#d0cbc0';ctx.lineWidth=1;ctx.font='11px system-ui';ctx.fillStyle='#6e716b';
  for(let x=Math.ceil(minX/500)*500;x<=maxX;x+=500){ctx.beginPath();ctx.moveTo(tx(x),tz(minZ));ctx.lineTo(tx(x),tz(maxZ));ctx.stroke();ctx.fillText(x,tx(x)+3,tz(minZ)+12);}
  for(let z=Math.ceil(minZ/500)*500;z<=maxZ;z+=500){ctx.beginPath();ctx.moveTo(tx(minX),tz(z));ctx.lineTo(tx(maxX),tz(z));ctx.stroke();ctx.fillText(z,tx(minX)+3,tz(z)-3);}
  for(const record of DATA.inventory){const group=sourceGroup(record);if(!state.visible[group])continue;ctx.globalAlpha=group==='generated'?.22:group==='infra'?.78:.36;ctx.fillStyle=COLORS[group];for(const [iz,x0,x1] of record.footprint_rle){ctx.fillRect(tx(x0*DATA.plan_cell_metres),tz(iz*DATA.plan_cell_metres),(x1-x0+1)*DATA.plan_cell_metres*scale,DATA.plan_cell_metres*scale);}}
  ctx.globalAlpha=1;ctx.strokeStyle=COLORS.reference;ctx.lineWidth=2;ctx.setLineDash([7,5]);
  for(const ref of DATA.reference_regions){ctx.beginPath();ref.points.forEach((p,i)=>i?ctx.lineTo(tx(p[0]),tz(p[1])):ctx.moveTo(tx(p[0]),tz(p[1])));ctx.closePath();ctx.stroke();const p=ref.points[0];ctx.fillStyle=COLORS.reference;ctx.fillText(ref.label,tx(p[0])+4,tz(p[1])-5);}
  ctx.setLineDash([3,4]);ctx.strokeStyle='#20231f';ctx.globalAlpha=.65;
  for(const sec of DATA.cross_sections){ctx.beginPath();sec.path.forEach((p,i)=>i?ctx.lineTo(tx(p[0]),tz(p[1])):ctx.moveTo(tx(p[0]),tz(p[1])));ctx.stroke();}
  ctx.globalAlpha=1;ctx.setLineDash([]);
  if(state.selected){const b=inventory.get(state.selected).bounds;ctx.strokeStyle='#111';ctx.lineWidth=3;ctx.strokeRect(tx(b.min_x),tz(b.min_z),(b.max_x-b.min_x)*scale,(b.max_z-b.min_z)*scale);}
}

function renderSelection(record){
  const group=sourceGroup(record),b=record.bounds;
  document.querySelector('#selection').innerHTML=`<p class="eyebrow">Selected owner</p><h3>${short(record.id)}</h3><p><span class="owner-dot" style="background:${COLORS[group]}"></span>${ownerName(group)} · ${record.category}</p><p>${record.role}</p><dl><dt>World footprint</dt><dd>x ${fmt(b.min_x)}…${fmt(b.max_x)}<br>z ${fmt(b.min_z)}…${fmt(b.max_z)}</dd><dt>Height</dt><dd>${b.min_y.toFixed(1)}…${b.max_y.toFixed(1)}m</dd><dt>Source</dt><dd><code>${record.editable_source.replace('res://','')}</code></dd><dt>Sampled intersections</dt><dd>${record.intersects.length}</dd></dl><ol>${record.intersects.map(id=>`<li>${short(id)}</li>`).join('')}</ol>`;
}

const tbody=document.querySelector('#inventory');
function renderTable(query=''){
  const q=query.trim().toLowerCase();
  tbody.innerHTML='';
  for(const r of DATA.inventory){const hay=[r.id,r.role,r.editable_source,r.materials.join(' ')].join(' ').toLowerCase();if(q&&!hay.includes(q))continue;const b=r.bounds,g=sourceGroup(r);const tr=document.createElement('tr');tr.dataset.id=r.id;tr.innerHTML=`<td><i class="row-dot" style="background:${COLORS[g]}"></i><b>${short(r.id)}</b><small>${ownerName(g)} · ${r.category}</small></td><td>${r.role}</td><td>x ${fmt(b.min_x)}…${fmt(b.max_x)}<br>z ${fmt(b.min_z)}…${fmt(b.max_z)}</td><td>${b.min_y.toFixed(1)}…${b.max_y.toFixed(1)}m</td><td>${r.materials.join('<br>')}</td><td>${r.collision_owner==='none'?'<em>none</em>':'yes'}</td><td><b>${r.intersects.length}</b><small>${r.intersects.slice(0,3).map(short).join('<br>')}${r.intersects.length>3?'<br>…':''}</small></td>`;tr.onclick=()=>{state.selected=r.id;renderSelection(r);drawPlan();document.querySelectorAll('tbody tr').forEach(row=>row.classList.toggle('selected',row===tr));};tbody.append(tr);}
}
document.querySelector('#search').addEventListener('input',e=>renderTable(e.target.value));

const sectionHost=document.querySelector('#sections');
for(const sec of DATA.cross_sections){
  const width=860,height=245,plot={l:52,r:18,t:22,b:40};
  const yMin=Math.min(-15,...sec.series.flatMap(s=>s.points.map(p=>p[1]))),yMax=Math.max(50,...sec.series.flatMap(s=>s.points.map(p=>p[2])));
  const px=d=>plot.l+d/sec.length_metres*(width-plot.l-plot.r),py=y=>plot.t+(yMax-y)/(yMax-yMin)*(height-plot.t-plot.b);
  let marks='';
  for(let y=Math.ceil(yMin/100)*100;y<=yMax;y+=100){marks+=`<line x1="${plot.l}" y1="${py(y)}" x2="${width-plot.r}" y2="${py(y)}" class="gridline"/><text x="${plot.l-7}" y="${py(y)+4}" text-anchor="end">${y}</text>`;}
  for(const s of sec.series){const r=inventory.get(s.id),g=sourceGroup(r);marks+=s.points.map(p=>`<line x1="${px(p[0])}" y1="${py(p[1])}" x2="${px(p[0])}" y2="${py(p[2])}" stroke="${COLORS[g]}" class="volume"><title>${short(s.id)} · ${p[1]}…${p[2]}m at ${p[0]}m</title></line>`).join('');}
  const legend=[...new Set(sec.series.map(s=>sourceGroup(inventory.get(s.id))))].map(g=>`<span><i style="background:${COLORS[g]}"></i>${ownerName(g)}</span>`).join('');
  const el=document.createElement('article');el.className='section-chart';el.innerHTML=`<div><h3>${sec.label}</h3><p>${fmt(sec.length_metres)}m transect · ${sec.series.length} owners</p></div><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${sec.label} source volume cross-section"><line x1="${plot.l}" y1="${py(0)}" x2="${width-plot.r}" y2="${py(0)}" class="datum"/>${marks}<text x="${(plot.l+width-plot.r)/2}" y="${height-7}" text-anchor="middle">distance along transect (m)</text><text transform="translate(13 ${(plot.t+height-plot.b)/2}) rotate(-90)" text-anchor="middle">world height (m)</text></svg><div class="mini-legend">${legend}</div><small>Source: mounted triangle-cell audit · 2026-09-12 · 40m plan cells</small>`;sectionHost.append(el);
}

renderTable();drawPlan();
</script>
<style>
:root{--paper:#f3f0e7;--ink:#22251f;--muted:#6e716b;--line:#cbc5b9;--panel:#e9e5da;--red:#bb3f3a}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:14px/1.45 ui-sans-serif,system-ui,-apple-system,sans-serif}main{width:min(1240px,100%);margin:auto;padding:30px}h1{font-size:34px;line-height:1.05;margin:.15em 0}h2{font-size:24px;margin:.2em 0}h3{margin:.2em 0;font-size:16px}.eyebrow{text-transform:uppercase;letter-spacing:.09em;font-size:11px;font-weight:800;color:var(--red);margin:0}.lede,.section-note{max-width:76ch;color:var(--muted)}.title-row,.section-head{display:flex;justify-content:space-between;gap:28px;align-items:flex-start}.verdict{background:var(--red);color:white;padding:14px 18px;min-width:190px}.verdict b{display:block;font-size:26px}.verdict span{font-size:12px}.metrics{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--line);margin:24px 0}.metrics article{padding:14px 18px;border-right:1px solid var(--line)}.metrics article:last-child{border:0}.metrics b{display:block;font-size:22px}.metrics span{color:var(--muted);font-size:12px}.finding{display:grid;grid-template-columns:1.15fr .85fr;gap:36px;padding:24px 0 30px;border-bottom:1px solid var(--line)}.finding ul{margin:0;padding:0;list-style:none}.finding li{padding:9px 0;border-bottom:1px solid var(--line)}.finding li b,.finding li span{display:block}.finding li span{color:var(--muted);font-size:12px}.plan-section,section{margin:32px 0}.filters{display:flex;gap:10px;flex-wrap:wrap;justify-content:flex-end}.filters label{display:flex;align-items:center;gap:6px;border:1px solid var(--line);padding:6px 9px}.filters i,.legend i,.mini-legend i{width:18px;height:7px;display:inline-block}.plan-grid{display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:18px;margin-top:14px}.canvas-wrap{position:relative;border:1px solid var(--line);background:var(--paper)}canvas{display:block;width:100%;height:auto}.axis{position:absolute;color:var(--muted);font-size:11px}.x-axis{bottom:6px;left:50%;transform:translateX(-50%)}.z-axis{left:4px;top:50%;transform:translateY(-50%) rotate(-90deg)}#selection{border-left:4px solid var(--ink);padding:14px;background:var(--panel);overflow-wrap:anywhere}#selection dl{display:grid;grid-template-columns:86px 1fr;gap:6px;margin:15px 0}#selection dt{color:var(--muted)}#selection dd{margin:0}.owner-dot{display:inline-block;width:10px;height:10px;margin-right:6px}.legend,.mini-legend{display:flex;gap:14px;flex-wrap:wrap;margin-top:9px;color:var(--muted);font-size:12px}.legend span,.mini-legend span{display:flex;align-items:center;gap:5px}.generated{background:#9a7042}.range{background:#2d7562}.city{background:#865b86}.infra{background:#405f79}.reference{background:#bb3f3a}.sections{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.section-chart{border:1px solid var(--line);padding:14px}.section-chart:first-child{grid-column:1/-1}.section-chart p,.section-chart small{color:var(--muted);margin:.1em 0}.section-chart svg{width:100%;height:auto}.section-chart svg text{font:10px system-ui;fill:var(--muted)}.gridline{stroke:var(--line);stroke-width:1}.datum{stroke:var(--ink);stroke-width:1.5}.volume{stroke-width:3;opacity:.42}.search{display:flex;align-items:center;gap:8px;color:var(--muted)}input[type=search]{border:1px solid var(--line);background:transparent;padding:8px 10px}.table-wrap{overflow:auto;border:1px solid var(--line);max-height:760px}table{width:100%;border-collapse:collapse;min-width:1120px}th{position:sticky;top:0;background:var(--ink);color:var(--paper);text-align:left;font-size:11px;letter-spacing:.04em;padding:9px}td{vertical-align:top;padding:10px 9px;border-bottom:1px solid var(--line)}tbody tr{cursor:pointer}tbody tr:hover,tbody tr.selected{background:var(--panel)}td:first-child b,td small{display:block}td small{color:var(--muted);font-size:11px}.row-dot{display:inline-block;width:8px;height:8px;margin-right:6px}.decision{display:grid;grid-template-columns:1fr 1fr 1fr;gap:22px;padding:25px 0;border-top:3px solid var(--ink)}.decision article{border-left:1px solid var(--line);padding-left:18px}.decision h3 span{color:var(--red);font-size:10px;text-transform:uppercase}.recommendation{font-weight:700}.protected{display:flex;gap:18px;padding:14px 18px;background:var(--panel);border-left:4px solid var(--red)}footer{border-top:1px solid var(--line);padding-top:14px;color:var(--muted);font-size:12px}code{font-size:11px;overflow-wrap:anywhere}@media(max-width:850px){main{padding:18px}.title-row,.section-head{display:block}.metrics{grid-template-columns:repeat(2,1fr)}.finding,.plan-grid,.decision,.sections{grid-template-columns:1fr}.section-chart:first-child{grid-column:auto}.filters{justify-content:flex-start;margin-top:10px}.protected{display:block}.verdict{margin-top:14px;width:max-content}}
</style>
</body>
</html>'''


if __name__ == "__main__":
    main()
