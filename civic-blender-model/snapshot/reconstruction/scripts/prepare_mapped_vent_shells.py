"""Replace generic building modules on explicitly mapped ventilation shafts; sizes remain estimates."""
import json,pathlib,os,math
from shapely.geometry import shape
from shapely.geometry.polygon import orient
from shapely import constrained_delaunay_triangles
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';rows=json.load(open(out/'corrected_rows_context.json'));payload=[]
for r in rows:
 t=r['tags']
 if t.get('man_made')!='ventilation_shaft':continue
 base=float(r['base_z_m']);height=float(r['height_m'])-base
 g=shape(r['geometry']);parts=list(g.geoms) if hasattr(g,'geoms') else [g];vs=[];fs=[];mi=[]
 def box(co,z0,z1,material):
  k=len(vs);vs.extend([[x,y,z] for z in [z0,z1] for x,y in co]);N=len(co);fs.extend([list(reversed(range(k,k+N))),list(range(k+N,k+2*N))]);fs.extend([[k+i,k+(i+1)%N,k+(i+1)%N+N,k+i+N] for i in range(N)]);mi.extend([material]*(N+2))
 def slab(p,z0,z1):
  # Triangular prisms avoid unsupported nonplanar n-gons and keep each shell closed.
  for tri in constrained_delaunay_triangles(p).geoms:box(list(orient(tri,1).exterior.coords)[:-1],z0,z1,0)
 blades=0
 for p in parts:
  p=orient(p,1);slab(p,0,.15);slab(p,height-.12,height)
  co=list(p.exterior.coords)
  for a,b in zip(co,co[1:]):
   dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy)
   if L<.4:continue
   ux,uy=dx/L,dy/L;nx,ny=-uy,ux
   def rect(s0,s1,d0,d1):return [(a[0]+ux*s+nx*d,a[1]+uy*s+ny*d) for s,d in [(s0,d0),(s1,d0),(s1,d1),(s0,d1)]]
   for s in [.09,L-.09]:box(rect(s-.03,s+.03,.02,.09),.15,height-.12,1)
   count=max(2,int((height-.4)/.15))
   for j in range(count):
    z=.25+j*(height-.5)/(count-1);box(rect(.12,L-.12,.015,.105),z-.016,z+.016,1);blades+=1
 vs=[[x,y,z+base] for x,y,z in vs]
 payload.append({'osm_id':r['osm_id'],'vertices':vs,'faces':fs,'materials':mi,'old_height_m':r['height_m'],'height_m':r['height_m'],'base_z_m':base,'height_status':r['height_status'],'height_policy':'Preserve existing elevation and estimated height; do not infer a lower shaft from function alone','source_tags':t,'louver_blades':blades,'scope':'Mapped ventilation-shaft function and footprint; surface elevation, housing and louver configuration unverified'})
(out/'mapped_vent_shell_payload.json').write_text(json.dumps(payload,ensure_ascii=False));print(json.dumps([{k:v for k,v in r.items() if k not in ['vertices','faces','materials']} for r in payload],ensure_ascii=False,indent=2))
