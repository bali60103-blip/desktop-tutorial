"""Compare operator-published station exit coordinates with old OSM references.
Official data are not automatically survey-grade, and same-label points may mark different doorway features.
"""
import csv,json,pathlib,math,argparse
from pyproj import Transformer
p=argparse.ArgumentParser()
for n in ['csv','old','registration','out']:p.add_argument('--'+n,required=True)
a=p.parse_args();rows=list(csv.DictReader(pathlib.Path(a.csv).read_bytes().decode('cp950').splitlines()));old=json.load(open(a.old));reg=json.load(open(a.registration));tr=Transformer.from_crs(4326,3826,always_xy=True);f=reg['live_to_twd97'];ang=math.radians(f['rotation_degrees']);origin=[reg['origin_epsg3826'][i]+f['translation'][i] for i in (0,1)]
def local(q):
 x,y=q[0]-origin[0],q[1]-origin[1];return [(math.cos(ang)*x+math.sin(ang)*y)/f['scale'],(-math.sin(ang)*x+math.cos(ang)*y)/f['scale']]
controls=[]
for r in rows:
 if not ('台北車站' in r['出入口名稱'] or '中山站' in r['出入口名稱']):continue
 ll=[float(r['經度']),float(r['緯度'])];xy=tr.transform(*ll);ref=r['出入口編號'];matches=[o for o in old if o['ref']==ref] if '台北車站' in r['出入口名稱'] else []
 comparisons=[{'osm_id':str(o['id']),'distance_m':math.dist(xy,o['twd97']),'osm_live_xy':o['xy']} for o in matches]
 controls.append({'name':r['出入口名稱'],'ref':ref,'wgs84':ll,'twd97':xy,'live_xy':local(xy),'elevation_m':None,'operator_accessibility_flag':r['是否為無障礙用'],'source':'Taipei Metro operator exit coordinate dataset, resource update 2026-08-04','status':'Operator-published XY, not survey-certified; ground elevation unknown','osm_comparisons':comparisons})
assert len(controls)==14
result={'source_url':'https://data.taipei/dataset/detail?id=cfa4778c-62c1-497b-b704-756231de348b','download_url':'https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=307a7f61-e302-4108-a817-877ccbfca7c1','controls':controls,'flag_threshold_m':10,'threshold_note':'Review triage only, not a declared source accuracy tolerance','flags':[{'name':c['name'],**m} for c in controls for m in c['osm_comparisons'] if m['distance_m']>10]}
pathlib.Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'controls':len(controls),'flags':result['flags'],'comparisons':[(c['name'],[round(m['distance_m'],2) for m in c['osm_comparisons']]) for c in controls]},ensure_ascii=False))
