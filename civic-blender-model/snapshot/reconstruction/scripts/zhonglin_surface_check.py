"""Ground QA: OSM intersections and official sidewalk outlines, no inferred stairs.
Dependencies: shapely, pyproj, matplotlib. Paths supplied as arguments.
"""
import argparse,json,math,pathlib
from shapely.geometry import LineString,shape,box,mapping
from shapely.ops import unary_union
from pyproj import Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser()
for n in ['osm','sidewalks','registration','out']:p.add_argument('--'+n,required=True)
a=p.parse_args();out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
d=json.load(open(a.osm));reg=json.load(open(a.registration));t=Transformer.from_crs(4326,3826,always_xy=True)
lo=t.transform(121.5198,25.0473);hi=t.transform(121.5247,25.0486);extent=box(*lo,*hi)
f=reg['live_to_twd97'];ang=math.radians(f['rotation_degrees']);org=[reg['origin_epsg3826'][i]+f['translation'][i] for i in (0,1)]
def local(q):
 x,y=q[0]-org[0],q[1]-org[1];return [(math.cos(ang)*x+math.sin(ang)*y)/f['scale'],(-math.sin(ang)*x+math.cos(ang)*y)/f['scale']]
def lines(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return [list(g.exterior.coords)]+[list(x.coords) for x in g.interiors]
 if hasattr(g,'geoms'):return sum([lines(x) for x in g.geoms],[])
 return []
civic=[w for w in d['ways'] if w['tags'].get('name')=='市民大道二段' and w['tags'].get('bridge')!='yes' and w['tags'].get('highway') in ['primary','secondary','tertiary','residential','unclassified']]
road=unary_union([LineString(w['xy']) for w in civic]);cross=[]
for label,ids in [('Zhongshan N',[264551743]),('Tianjin',[232106525]),('Linsen N',[1347363384])]:
 ws=[w for w in d['ways'] if w['id'] in ids];g=unary_union([LineString(w['xy']) for w in ws]).intersection(road)
 pts=list(g.geoms) if hasattr(g,'geoms') else [g];pts=[q for q in pts if q.geom_type=='Point' and not q.is_empty and extent.contains(q)]
 if not pts:raise RuntimeError('No surface intersection: '+label)
 xy=[sum(q.x for q in pts)/len(pts),sum(q.y for q in pts)/len(pts)]
 cross.append(dict(name=label,twd97=xy,live_xy=local(xy),intersection_points=[list(q.coords)[0] for q in pts],osm_way_ids=[str(i) for i in ids],status='Mean of OSM ground road intersections, not surveyed curb control'))
side=[]
for i,ft in enumerate(json.load(open(a.sidewalks))['features']):
 g=shape(ft['geometry'])
 if not g.is_valid:g=g.buffer(0)
 if g.intersects(extent):
  clipped=g.intersection(extent)
  if clipped.area>0:side.append(dict(source_index=i,properties=ft['properties'],area_clipped_m2=clipped.area,rings=[list(map(local,ring)) for ring in lines(clipped)]))
assert side,'No sidewalk coverage'
report=dict(crossings=cross,sidewalks=side,extent_lonlat=[121.5198,25.0473,121.5247,25.0486],stairs=[{'number':1,'side':'north','between':['Zhongshan N','Tianjin'],'xy':None},{'number':2,'side':'south','between':['Zhongshan N','Tianjin'],'xy':None},{'number':3,'side':'south','between':['Tianjin','Linsen N'],'xy':None},{'number':4,'side':'south','between':['Tianjin','Linsen N'],'xy':None}],sidewalk_height_m=None,source_plan_scale=None,gate='B remains open; do not infer stair coordinates from schematic proportions')
(out/'surface_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
fig,ax=plt.subplots(figsize=(13,5.5))
for w in d['ways']:
 if w.get('xy') and ('highway' in w['tags'] or 'building' in w['tags']) and LineString(w['xy']).intersects(extent):ax.plot(*zip(*map(local,w['xy'])),color='#ccd0d8',lw=.6)
for s in side:
 for ring in s['rings']:ax.plot(*zip(*ring),color='#008b8b',lw=1.3)
for c in cross:
 x,y=c['live_xy'];ax.scatter(x,y,color='#2948c5',s=45);ax.annotate(c['name'],(x,y),xytext=(0,-40),textcoords='offset points',ha='center',arrowprops={'arrowstyle':'-'})
ax.set_xlim(local(lo)[0],local(hi)[0]);ax.set_ylim(local(lo)[1],local(hi)[1]);ax.set_aspect('equal');ax.grid(alpha=.15);ax.set_title('ZHONGLIN | ground-level sidewalk and crossing QA');ax.set_xlabel('Blender local X (m)');ax.set_ylabel('Blender local Y (m)')
fig.text(.1,.02,'Teal: official sidewalk boundaries (clipped). Blue: OSM crossing references. Stair 1 north; stairs 2-4 south; exact positions unknown.',fontsize=9)
fig.savefig(out/'surface_check.png',dpi=180,bbox_inches='tight');plt.close(fig)
print(json.dumps({'sidewalk_features':len(side),'crossings':[(c['name'],len(c['intersection_points'])) for c in cross]}))
