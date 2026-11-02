import json,pathlib,math,collections
from shapely.geometry import shape,Polygon,LineString,box,Point
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely import set_precision,make_valid,constrained_delaunay_triangles
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'BlockFacades';blocks=json.load(open(out/'blocks.json'));region=unary_union([shape(r['geometry']) for r in blocks]);streets=json.load(open(out/'source/streets_plan_boundaries.json'));roadparts=[];widths=[]
for r in streets:
 t=r['tags']
 if t.get('bridge','no')!='no' or t.get('layer','0') not in ['0','']:continue
 line=LineString(r['xy'])
 if not line.intersects(region):continue
 defaults={'primary':14,'secondary':10,'tertiary':8,'residential':6,'service':4,'pedestrian':4,'living_street':5,'trunk':18}
 try:w=float(t['width']);status='OSM width'
 except:w=defaults.get(t['highway'],6);status='Estimated width by road class'
 w=max(2,min(30,w));roadparts.append(line.buffer(w/2,cap_style=2,join_style=2));widths.append({'osm_id':r['osm_id'],'width_m':w,'status':status})
roadspace=set_precision(unary_union(roadparts).intersection(region.buffer(8)),.005);existing=[]
for r in json.load(open(root/'Calibration/flow_meshes.json')):
 if not r['name'].startswith('CAL_GROUND_'):continue
 vs=r['vertices'];z=max(v[2] for v in vs)
 for f in r['faces']:
  if all(abs(vs[i][2]-z)<1e-5 for i in f):
   p=Polygon([vs[i][:2] for i in f])
   if p.is_valid and p.area>1e-8:existing.append(p)
existing=set_precision(unary_union(existing),.005);openings=unary_union([shape(r['geometry']) for r in json.load(open(root/'Calibration/openings_payload.json'))['openings']]);buildings=unary_union([shape(r['geometry']) for r in json.load(open(out/'buildings_selected.json'))]);land=set_precision(region.difference(roadspace).difference(existing).difference(openings),.005);roads=set_precision(roadspace.difference(existing).difference(openings),.005);walk=set_precision(land.intersection(roadspace.buffer(1.8)).difference(buildings).difference(openings),.005)
def mesh(p,z0,z1):
 p=orient(p);v=[];f=[];ids={}
 def idx(x,y,z):
  k=(round(x,6),round(y,6),z)
  if k not in ids:ids[k]=len(v);v.append(k)
  return ids[k]
 for tri in constrained_delaunay_triangles(p).geoms:
  cc=list(orient(tri).exterior.coords)[:3];f.append([idx(x,y,z1) for x,y in cc]);f.append([idx(x,y,z0) for x,y in cc[::-1]])
 for ring in [p.exterior,*p.interiors]:
  cc=list(ring.coords)
  for a,b in zip(cc,cc[1:]):f.append([idx(*a,z0),idx(*b,z0),idx(*b,z1),idx(*a,z1)])
 return {'vertices':v,'faces':f}
parts=[];fixes=[]
for kind,g,z0,z1 in [('LAND',land,-.12,0),('ROAD',roads,-.12,0),('SIDEWALK',walk,0,.12)]:
 xmin,ymin,xmax,ymax=g.bounds
 for ix in range(math.floor(xmin/200),math.floor(xmax/200)+1):
  for iy in range(math.floor(ymin/200),math.floor(ymax/200)+1):
   q=set_precision(make_valid(g.intersection(box(ix*200,iy*200,(ix+1)*200,(iy+1)*200))),.005)
   if q.is_empty:continue
   pp=[q] if q.geom_type=='Polygon' else [p for p in getattr(q,'geoms',[]) if p.geom_type=='Polygon'];chunks=[]
   for p in pp:
    if p.area<.001:continue
    m=mesh(p,z0,z1);ec=collections.Counter(tuple(sorted((f[j],f[(j+1)%len(f)]))) for f in m['faces'] for j in range(len(f)));bad=[k for k,n in ec.items() if n!=2]
    if bad:
     disks=unary_union([Point(m['vertices'][k[0]][:2]).buffer(.015) for k in bad]);p=set_precision(p.difference(disks),.005);fixes.append({'kind':kind,'cell':[ix,iy],'contacts':len(bad)});p2=[p] if p.geom_type=='Polygon' else [r for r in p.geoms if r.geom_type=='Polygon'];chunks.extend(mesh(r,z0,z1) for r in p2 if r.area>.001)
    else:chunks.append(m)
   if not chunks:continue
   v=[];f=[]
   for m in chunks:
    off=len(v);v.extend(m['vertices']);f.extend([[i+off for i in ff] for ff in m['faces']])
   ec=collections.Counter(tuple(sorted((ff[j],ff[(j+1)%len(ff)]))) for ff in f for j in range(len(ff)))
   if any(n!=2 for n in ec.values()):raise RuntimeError('Nonmanifold context cell')
   parts.append({'name':'BLOCK_CONTEXT_'+kind+'_'+str(ix)+'_'+str(iy),'kind':kind,'mesh':{'vertices':v,'faces':f}})
r={'parts':parts,'widths':widths,'cleanup_contacts':fixes,'status':'Mapped street/block plan context; side-road widths, sidewalks and flat Z0 are estimated. Existing calibrated ground and provisional access openings excluded to avoid resealing.'};(out/'context_payload.json').write_text(json.dumps(r,ensure_ascii=False));print({'parts':len(parts),'street_widths':len(widths),'cleanup_cells':len(fixes)})
