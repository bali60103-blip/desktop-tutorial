"""Zhonglin frontage candidates by first polygon intersected by street-normal rays.
Not parcel frontage certification. Heights only from explicit OSM height tags.
"""
import argparse,json,math,pathlib,re,collections
from shapely.geometry import Polygon,LineString,Point
from shapely.strtree import STRtree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser()
for n in ['osm','controls','registration','out']:p.add_argument('--'+n,required=True)
a=p.parse_args();out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
d=json.load(open(a.osm));controls=json.load(open(a.controls));reg=json.load(open(a.registration));axis=LineString([c['twd97'] for c in controls['crossings']]);f=reg['live_to_twd97'];ang=math.radians(f['rotation_degrees']);org=[reg['origin_epsg3826'][i]+f['translation'][i] for i in (0,1)]
def local(q):
 x,y=q[0]-org[0],q[1]-org[1];return [(math.cos(ang)*x+math.sin(ang)*y)/f['scale'],(-math.sin(ang)*x+math.cos(ang)*y)/f['scale']]
bs=[];gs=[]
for w in d['ways']:
 if 'building' not in w['tags'] or len(w['xy'])<4 or w['xy'][0]!=w['xy'][-1]:continue
 g=Polygon(w['xy'],w.get('holes_xy',[]))
 if not g.is_valid:g=g.buffer(0)
 if g.is_empty or g.distance(axis)>200:continue
 bs.append(w);gs.append(g)
tree=STRtree(gs)
def select(step,depth):
 hits=collections.defaultdict(list)
 for k in range(int(axis.length/step)+1):
  station=min(k*step,axis.length);q=axis.interpolate(station);l=axis.interpolate(max(0,station-.5));r=axis.interpolate(min(axis.length,station+.5));dx,dy=r.x-l.x,r.y-l.y;norm=math.hypot(dx,dy)
  for sign,label in [(1,'north'),(-1,'south')]:
   ray=LineString([(q.x,q.y),(q.x-sign*dy/norm*depth,q.y+sign*dx/norm*depth)]);candidates=[]
   for i in tree.query(ray):
    inter=gs[i].intersection(ray)
    if not inter.is_empty:candidates.append((q.distance(inter),int(i)))
   if candidates:
    dist,i=min(candidates);hits[i].append({'side':label,'station_m':round(station,2),'gap_from_axis_m':round(dist,2)})
 return hits
hits=select(2,200);coarse=select(5,200);short=select(2,100)
def height(tags):
 raw=tags.get('height');m=re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*(m)?\s*',raw or '')
 return float(m.group(1)) if m and float(m.group(1))>0 else None
records=[]
for i,hh in sorted(hits.items(),key=lambda z:min(x['station_m'] for x in z[1])):
 w=bs[i];g=gs[i];tags=w['tags'];h=height(tags);parts=list(g.geoms) if hasattr(g,'geoms') else [g]
 records.append(dict(osm_id=(('relation/'+tags['_source_relation_id']+'/part/'+tags['_part_index']) if tags.get('_source_type')=='relation' else str(w['id'])),name=tags.get('name',''),tags=tags,height_m=h,height_status='OSM explicit height; unverified' if h else 'UNKNOWN; levels not converted',levels=tags.get('building:levels'),area_m2=round(g.area,2),side=sorted(set(x['side'] for x in hh)),rays_hit=len(hh),min_axis_gap_m=min(x['gap_from_axis_m'] for x in hh),stable_at_5m=i in coarse,stable_at_100m=i in short,rings=[{'outer':[local(q) for q in part.exterior.coords],'holes':[[local(q) for q in ring.coords] for ring in part.interiors]} for part in parts],status='First-hit frontage candidate, not verified building frontage'))
summary={'candidate_buildings':len(records),'explicit_height':sum(r['height_m'] is not None for r in records),'levels_only':sum(r['height_m'] is None and r['levels'] is not None for r in records),'no_height_or_levels':sum(r['height_m'] is None and r['levels'] is None for r in records),'sampling_sensitive':sum(not r['stable_at_5m'] for r in records),'search_depth_sensitive':sum(not r['stable_at_100m'] for r in records),'axis_length_m':axis.length,'scope':'Zhonglin only, Zhongshan eastern carriageway to Linsen; full corridor pending'}
result={'summary':summary,'method':{'ray_spacing_m':2,'max_search_m':200,'sensitivity_spacing_m':5,'sensitivity_search_m':100,'note':'Search reach is not a fixed-buffer selection. Only first polygon intersections are candidates; open spaces may expose setback buildings. OSM missing or merged buildings remain a limitation.'},'buildings':records}
(out/'first_row.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
fig,ax=plt.subplots(figsize=(13,6))
for g in gs:
 parts=list(g.geoms) if hasattr(g,'geoms') else [g]
 for part in parts:ax.plot(*zip(*map(local,part.exterior.coords)),color='#d5d8df',lw=.6)
for r in records:
 color='#17816d' if r['height_m'] is not None else ('#dd9b23' if r['levels'] else '#c55767')
 for poly in r['rings']:
  ax.fill(*zip(*poly['outer']),color=color,alpha=.65);ax.plot(*zip(*poly['outer']),color=color,lw=1)
ax.plot(*zip(*map(local,axis.coords)),color='#283a80',lw=2)
xx,yy=zip(*map(local,axis.coords));ax.set_xlim(min(xx)-25,max(xx)+25);ax.set_ylim(min(yy)-150,max(yy)+150);ax.set_aspect('equal');ax.grid(alpha=.15);ax.set_title('ZHONGLIN | first-row building candidates and height evidence');ax.set_xlabel('Blender local X (m)');ax.set_ylabel('Blender local Y (m)')
fig.text(.07,.02,'Green: explicit OSM height. Amber: levels only. Red: neither. All footprints and heights require independent verification.',fontsize=9);fig.savefig(out/'first_row.png',dpi=180,bbox_inches='tight');plt.close(fig)
print(json.dumps(summary))
