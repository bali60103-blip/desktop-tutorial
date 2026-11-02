"""Convert mapped references to existing Blender coordinates; no survey accuracy claim."""
import argparse,json,pathlib,re,math,collections,html
from pyproj import Transformer

def run(src,regpath,out):
    out.mkdir(parents=True,exist_ok=True);reg=json.loads(regpath.read_text());a=math.radians(reg['live_to_twd97']['rotation_degrees']);c,s=math.cos(a),math.sin(a);scale=reg['live_to_twd97']['scale'];origin=[reg['origin_epsg3826'][i]+reg['live_to_twd97']['translation'][i] for i in range(2)];tr=Transformer.from_crs(4326,3826,always_xy=True)
    def local(ll):
        x,y=tr.transform(*ll[:2]);x-=origin[0];y-=origin[1];return [(c*x+s*y)/scale,(-s*x+c*y)/scale]
    ways=json.loads((src/'civic_all_named_ways.geojson').read_text())['features'];routes=[]
    for f in ways:
        p=f['properties'];name=p.get('name','')
        if re.fullmatch('市民大道[一二三四五六七八]段',name) and p.get('highway'):group='ground'
        elif name=='市民大道高架道路' and p.get('highway')=='trunk':group='elevated'
        else:continue
        routes.append({'id':p['osm_id'],'name':name,'group':group,'xy':[local(x) for x in f['geometry']['coordinates']],'status':'Mapped plan reference only; no elevation or road width inferred'})
    entrances=json.loads((src/'entrance_candidates.geojson').read_text())['features'];controls=[]
    for f in entrances:
        ll=f['geometry']['coordinates'];p=f['properties'];ref=p.get('ref') or p.get('name','')
        if not (121.508<ll[0]<121.524 and 25.044<ll[1]<25.059):continue
        if re.fullmatch('[MRY][0-9]+',ref):
            matched=ref in ['M1','M2','M3','M4','M5','M6','M7','M8','R1','R2','R4','R5','R7','R9','R10']
            controls.append({'id':p['osm_id'],'ref':ref,'wgs84':ll,'twd97':list(tr.transform(*ll)),'xy':local(ll),'z_m':None,'osm_level_tag':p.get('level'),'plan_label_seen':matched,'confidence':'OSM XY; matching map label is NOT an independently surveyed ground control point','public_access':'not verified; emergency exits must be classified separately'})
    outpayload={'routes':routes,'controls':controls,'registration':reg,'presentation_z_only':0,'note':'Plan-reference lines and entrance markers only. No new underground structural geometry.'}
    (out/'control_payload.json').write_text(json.dumps(outpayload,ensure_ascii=False))
    (out/'controls.json').write_text(json.dumps(controls,ensure_ascii=False,indent=2))
    refs=collections.Counter(p['ref'] for p in controls);bounds=[min(p['xy'][0] for p in controls),min(p['xy'][1] for p in controls),max(p['xy'][0] for p in controls),max(p['xy'][1] for p in controls)]
    errors=[]
    for p in controls:
        x,y=p['xy'];rx=scale*(c*x-s*y)+origin[0];ry=scale*(s*x+c*y)+origin[1];errors.append(math.hypot(rx-p['twd97'][0],ry-p['twd97'][1]))
    check={'route_way_count':len(routes),'groups':dict(collections.Counter(p['group'] for p in routes)),'ground_sections':sorted(set(p['name'] for p in routes if p['group']=='ground')),'control_candidates':len(controls),'map_label_seen':sum(p['plan_label_seen'] for p in controls),'duplicate_refs':{k:v for k,v in refs.items() if v>1},'roundtrip_max_m':max(errors),'independent_survey_accuracy_m':None,'underground_elevation_verified':False,'gate_B_status':'Not passed: mapped references prepared; source-plan registration and elevation control incomplete'}
    (out/'control_check.json').write_text(json.dumps(check,ensure_ascii=False,indent=2))
    x0,y0,x1,y1=bounds;fac=min(1000/(x1-x0),480/(y1-y0))
    def screen(p):return (80+(p[0]-x0)*fac,590-(p[1]-y0)*fac)
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760"><rect width="1200" height="760" fill="#f7f4ec"/><g font-family="sans-serif" fill="#24383b"><text x="60" y="48" font-size="26">Gate B · 地下出入口平面參考</text><text x="60" y="80" font-size="16">OSM 位置＋既有模型座標轉換；不是實測控制點，地下高程尚未取得</text>']
    svg.append('<defs><clipPath id="map"><rect x="60" y="95" width="1070" height="520"/></clipPath></defs><g clip-path="url(#map)">')
    for r in routes:
        coords=' '.join('%.2f,%.2f'%screen(p) for p in r['xy']);svg.append(f'<polyline points="{coords}" fill="none" stroke="#b4bbac" stroke-width="2"/>')
    for p in controls:
        x,y=screen(p['xy']);color={'M':'#176aac','R':'#b93936','Y':'#a68112'}[p['ref'][0]];svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}"/>')
        if p['plan_label_seen']:svg.append(f'<text x="{x+6:.2f}" y="{y-5:.2f}" font-size="12" fill="{color}">{html.escape(p["ref"])}</text>')
    svg.append('</g><text x="60" y="654" font-size="17">M：台北車站出入口　R：中山地下街　Y：台北地下街</text><text x="60" y="688" font-size="16">灰線：市民大道圖上路線。點位不代表各地下街已配準或已連通。</text><text x="60" y="720" font-size="16">下一步：確認入口實體、切分示意圖、求圖面比例與高程控制，再做剖面。</text></g></svg>')
    (out/'gate_B_controls.svg').write_text(''.join(svg));print(json.dumps(check,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--sources',type=pathlib.Path,required=True);p.add_argument('--registration',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();run(a.sources,a.registration,a.output)
