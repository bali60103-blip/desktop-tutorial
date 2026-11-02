"""Create selectable model-only span measurement markers and a review table."""
import bpy,os,json,html,math
from mathutils import Vector
ROOT=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922')
d=json.load(open(os.path.join(ROOT,'span_height_audit.json')))
s=bpy.data.scenes['CIVIC_UNDERBRIDGE_MASSING_20260916']
name='UB_SPAN_HEIGHT_MODEL_AUDIT'
assert bpy.data.collections.get(name) is None,'Audit markers already exist'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(bpy.data.filepath),'BEFORE_SPAN_HEIGHT_MARKERS_20260922.blend'),copy=True)
c=bpy.data.collections.new(name);s.collection.children.link(c)
lines=0
for r in d['spans']:
 mid=r['samples'][5];o=bpy.data.objects.new(r['span_id'],None);c.objects.link(o)
 o.empty_display_type='PLAIN_AXES';o.empty_display_size=1.;o.location=(*mid['xy'],9.)
 o['measurement_basis']='MODEL ONLY; not surveyed or verified from imagery'
 o['start_piers']='|'.join(r['start_piers']);o['end_piers']='|'.join(r['end_piers']);o['decks']='|'.join(r['decks']);o['plan_length_m']=r['plan_length_m'];o['review_flags']='|'.join(r['flags']);o['real_world_verified']=False
 if r['sampled_min_clearance_m'] is not None:o['sampled_min_clearance_m']=r['sampled_min_clearance_m']
 if r['deck_top_z_min'] is not None:o['deck_top_z_min']=r['deck_top_z_min'];o['deck_top_z_max']=r['deck_top_z_max']
 valid=[v for v in mid['cross_samples'] if v['clearance_m'] is not None]
 if valid:
  v=min(valid,key=lambda v:v['clearance_m']);cu=bpy.data.curves.new(r['span_id']+'_MEASURE','CURVE');cu.dimensions='3D';cu.bevel_depth=.035
  sp=cu.splines.new('POLY');sp.points.add(1)
  for p,z in zip(sp.points,[v['ground_z'],v['soffit_z']]):p.co=(*v['xy'],z,1.)
  ob=bpy.data.objects.new(r['span_id']+'_MODEL_MIDSPAN_LINE',cu);c.objects.link(ob);ob.hide_render=True;ob['measurement_basis']='MODEL ONLY at sampled midspan point; not whole-span minimum';ob['height_m']=v['clearance_m'];lines+=1
def fmt(x):return '—' if x is None else f'{x:.2f}'
rows=[]
for r in d['spans']:
 rows.append('<tr><td>'+r['span_id']+'</td><td>'+html.escape(' / '.join(r['start_piers']))+'</td><td>'+html.escape(' / '.join(r['end_piers']))+'</td><td>'+fmt(r['plan_length_m'])+'</td><td>'+fmt(r['sampled_min_clearance_m'])+'</td><td>'+fmt(r['deck_top_z_min'])+'–'+fmt(r['deck_top_z_max'])+'</td><td>'+html.escape(', '.join(r['flags']) or '僅完成模型取樣，實景待核')+'</td></tr>')
page='''<!doctype html><meta charset="utf-8"><title>市民高架逐跨高度檢查</title><style>body{font:15px system-ui;margin:32px;background:#f5f3ee;color:#222}h1{font-size:26px}aside{background:#fff0d7;padding:18px;line-height:1.7}table{border-collapse:collapse;background:white;width:100%;margin-top:20px}th,td{text-align:left;border-bottom:1px solid #ddd;padding:10px;font-size:12px}th{position:sticky;top:0;background:#172a34;color:white}input{padding:12px;width:420px;margin-top:18px}a{color:#086577}</style><h1>市民高架：柱間跨段高度檢查</h1><aside><b>目前是模型量測，不是現地實測。</b><br>241 個既有估算柱位，產生 116 組候選跨段；19 個柱位歸屬有歧義。部分跨距過長，不能視為真實橋跨。另有柱位 598、621 未組成跨段，13 條橋面路徑無柱間量測；見 span_height_coverage_gaps.json。<br>每跨沿長度取 11 站、橫向取 9 點。淨高是取樣最小值，不保證連續最小值；未取到地面顯示「—」，不以 0 補值。<br>橋面取樣均約 Z=8 m，表示原有統一估算尚未完成高程校準。Z 不是已知海拔基準。<br>量測只涵蓋 DECK/GIRDER 幾何；橫梁、支承墊與管線等可能再降低淨高，尚待納入。<br>官方主橋資料記載 160 孔；與此模型的候選跨段範圍及柱位配對不同，不可直接當成對應表。</aside><p><a href="span_height_audit.csv">下載逐跨表 CSV</a> · <a href="span_station_heights.csv">分站高度 CSV</a> · <a href="span_height_summary.json">摘要 JSON</a> · <a href="https://bridge.nco.taipei/bms2/guest/bridge/inventory.aspx?vid=28846">官方橋梁資料</a></p><input id="q" placeholder="搜尋柱號、跨段、缺失旗標" oninput="for(const r of document.querySelectorAll('tbody tr'))r.hidden=!r.textContent.toLowerCase().includes(this.value.toLowerCase())"><table><thead><tr><th>候選跨段</th><th>起端柱位</th><th>終端柱位</th><th>平面長度 m</th><th>取樣淨高 m</th><th>橋面模型 Z m</th><th>疑慮</th></tr></thead><tbody>'''+''.join(rows)+'</tbody></table>'
open(os.path.join(ROOT,'span_height_review.html'),'w').write(page)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result={'span_markers':len(d['spans']),'midspan_measurement_lines':lines,'html':'span_height_review.html'}
