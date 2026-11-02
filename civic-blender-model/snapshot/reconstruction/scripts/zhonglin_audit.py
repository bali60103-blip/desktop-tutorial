"""Audit Zhonglin OSM plan candidates; unknown elevations remain null.
Run with --osm, --registration, --out. Uses pyproj and matplotlib.
"""
import argparse,json,math,pathlib
from pyproj import Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('--osm',required=True);p.add_argument('--registration',required=True);p.add_argument('--out',required=True);a=p.parse_args()
out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
d=json.loads(pathlib.Path(a.osm).read_text());reg=json.loads(pathlib.Path(a.registration).read_text())
f=reg['live_to_twd97'];ang=math.radians(f['rotation_degrees']);origin=[reg['origin_epsg3826'][i]+f['translation'][i] for i in (0,1)]
def live(xy):
 x,y=[xy[i]-origin[i] for i in (0,1)];return [(math.cos(ang)*x+math.sin(ang)*y)/f['scale'],(-math.sin(ang)*x+math.cos(ang)*y)/f['scale']]
t=Transformer.from_crs(4326,3826,always_xy=True)
ids={313684462,313684460,1454572596,1454572597,1454572598,1454572599}
ways=[w for w in d['ways'] if int(w['id']) in ids]
assert len(ways)==6,'Missing expected OSM access ways'
entrances=[]
for label,nid,ll in [('West',3196999081,[121.5215419,25.0479554]),('East',3196999076,[121.5231221,25.0478653])]:
 xy=t.transform(*ll);entrances.append(dict(label=label,osm_id=str(nid),lonlat=ll,twd97=list(xy),live_xy=live(xy),elevation_m=None,status='OSM candidate, not surveyed',vehicle_height_limit_m=1.8))
routes=[dict(osm_id=str(w['id']),live_xy=[live(x) for x in w['xy']],lonlat=w['ll'],status='OSM access centerline; width and Z unknown') for w in ways]
sep=math.dist(entrances[0]['twd97'],entrances[1]['twd97'])
stairs=[dict(number=i,location_description=s,coordinates=None,elevation_m=None) for i,s in enumerate(['North side, Zhongshan N Rd / health insurance office','South side, Zhongshan N Rd / Executive Yuan','South side, Tianjin St / police agency','South side, Linsen N Rd / Shandao Temple'],1)]
report=dict(crs='EPSG:3826',entrances=entrances,routes=routes,stairs=stairs,entrance_candidate_separation_m=sep,levels={'B1':{'floor_elevation_m':None,'floor_to_floor_m':None},'B2':{'floor_elevation_m':None,'floor_to_floor_m':None}},plan_scale={'status':'UNREGISTERED','reason':'No dimensioned control pairs established on plan. OSM entry nodes are not proven homologous plan points; do not stretch plan to fit.'},gate='B NOT PASSED')
(out/'zhonglin_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
fig,ax=plt.subplots(figsize=(13,5))
for w in d['ways']:
 if not w.get('xy') or not any(121.5198<x<121.5247 and 25.0473<y<25.0486 for x,y in w['ll']):continue
 if not ('highway' in w['tags'] or 'building' in w['tags']):continue
 q=[live(x) for x in w['xy']];ax.plot(*zip(*q),color='#b7c0cc',lw=.65)
for r in routes:ax.plot(*zip(*r['live_xy']),color='#e18524',lw=3)
for e in entrances:
 x,y=e['live_xy'];ax.scatter(x,y,s=70,color='#b54a00');ax.annotate(e['label']+' candidate\nOSM '+e['osm_id'],(x,y),xytext=(0,25),textcoords='offset points',ha='center',fontsize=9)
q0=live(t.transform(121.5198,25.0473));q1=live(t.transform(121.5247,25.0486));ax.set_xlim(q0[0],q1[0]);ax.set_ylim(q0[1],q1[1]);ax.set_aspect('equal');ax.set_title('ZHONGLIN | vehicle access alignment candidates (not surveyed)');ax.set_xlabel('Blender local X (m), registered to TWD97');ax.set_ylabel('Local Y (m)');ax.grid(alpha=.2)
fig.text(.08,.02,f'Orange: 6 OSM access lines. Candidate separation: {sep:.1f} m. Four pedestrian stairs: coordinates unresolved. B1/B2 Z: unknown.',fontsize=9)
fig.savefig(out/'zhonglin_alignment.png',dpi=180,bbox_inches='tight');plt.close(fig)
print(json.dumps({'candidate_separation_m':sep,'routes':len(routes),'stairs_unlocated':len(stairs),'gate':report['gate']}))
