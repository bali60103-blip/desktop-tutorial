"""Estimate B1 ramp-opening guards on supported slab edges in five non-pilot sections."""
import json,os,pathlib,math
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';r=json.load(open(out/'parking_marking_support_inventory.json'));sections=json.load(open(out.parent/'ParkingSections/source/payload.json'))['sections'];items=[]
for s in sections:
 if s['levels']!=2 or s['name']=='中林':continue
 floor=r['floors']['COMP_'+s['name']+'_B1_FLOOR'];v=floor['vertices'];z=max(p[2] for p in v);g=unary_union([Polygon([v[i][:2] for i in f]) for f in floor['faces'] if all(abs(v[i][2]-z)<.0001 for i in f)])
 hole=Polygon(s['interlevel_hole'][0]);c=hole.centroid;coords=list(hole.exterior.coords)
 for j,(a,b) in enumerate(zip(coords,coords[1:])):
  dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy)
  if L<10:continue
  nx,ny=-dy/L,dx/L;mx,my=(a[0]+b[0])/2,(a[1]+b[1])/2
  if nx*(mx-c.x)+ny*(my-c.y)<0:nx,ny=-nx,-ny
  line=LineString([(a[0]+nx*.14,a[1]+ny*.14),(b[0]+nx*.14,b[1]+ny*.14)]);supported=line.intersection(g.buffer(-.055));parts=list(supported.geoms) if hasattr(supported,'geoms') else [supported]
  for k,p in enumerate(parts):
   if p.geom_type!='LineString' or p.length<.5:continue
   a,b=list(p.coords)[0],list(p.coords)[-1];items.append({'section':s['name'],'edge':j,'part':k,'a':[*a,z],'b':[*b,z],'height':1.1,'post_spacing_max':2.,'post_width':.06,'rail_width':.05,'floor':floor['name']})
(out/'parking_opening_guards_payload.json').write_text(json.dumps({'items':items,'scope':'Five non-pilot B1 ramp openings; longitudinal guards only; short approach/departure ends remain open. Dimensions and appearance estimated, not a vehicle crash barrier design.'},ensure_ascii=False));print({'guard_runs':len(items),'sections':sorted(set(x['section'] for x in items))})
