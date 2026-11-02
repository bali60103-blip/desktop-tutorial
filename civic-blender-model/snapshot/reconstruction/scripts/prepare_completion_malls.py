import pathlib,json,math,runpy
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union,nearest_points
from shapely import set_precision
from pyproj import Transformer
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'CompletionPass';mesh=runpy.run_path('/tmp/civic-stage00/reconstruction/scripts/prepare_mall_shells.py')['mesh'];parts=[];issues=[]
def add(name,p,z0,z1,status):
 p=set_precision(p,.0001)
 for i,g in enumerate([p] if p.geom_type=='Polygon' else getattr(p,'geoms',[])):
  if g.geom_type=='Polygon' and g.area>.001:parts.append({'name':name+'_'+str(i),'mesh':mesh(g,z0,z1),'status':status})
def rect(a,d,x0,x1,y0,y1):
 n=(-d[1],d[0]);return Polygon([(a[0]+d[0]*x+n[0]*y,a[1]+d[1]*x+n[1]*y) for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]])
shells=[]
for r in json.load(open(root/'UndergroundShells/source/legacy.json')):
 polys=[]
 for f in r['faces']:
  vs=[r['vertices'][i] for i in f]
  if max(v[2] for v in vs)-min(v[2] for v in vs)<.001:
   g=Polygon([v[:2] for v in vs])
   if g.is_valid and g.area>.001:polys.append(g)
 g=unary_union(polys);shells.append((r['name'],g));box=list(g.minimum_rotated_rectangle.exterior.coords);a,b=max(zip(box,box[1:]),key=lambda ab:Point(ab[0]).distance(Point(ab[1])));le=Point(a).distance(Point(b));d=((b[0]-a[0])/le,(b[1]-a[1])/le);c=g.centroid;aa=(c.x-d[0]*le/2,c.y-d[1]*le/2);short=min(Point(x).distance(Point(y)) for x,y in zip(box,box[1:]));offset=min(5,max(2,short/3));status='ESTIMATED modular interior; no actual shop identity, aisle width, structural grid or MEP layout claimed'
 for j,s in enumerate(range(8,int(le-8),8)):
  for side in [-1,1]:
   col=rect(aa,d,s-.25,s+.25,side*offset-.25,side*offset+.25)
   if g.buffer(-1).covers(col):add('COMP_MALL_'+r['name']+'_COLUMN_'+str(j)+'_'+str(side),col,-3.6,-.8,status)
  light=rect(aa,d,s-1,s+1,-.12,.12)
  if g.buffer(-1).covers(light):add('COMP_MALL_'+r['name']+'_LIGHT_'+str(j),light,-1.0,-.9,status)
  # Short side partitions leave central aisle and a broad front opening.
  for side in [-1,1]:
   pp=rect(aa,d,s,s+.12,offset+1,offset+4) if side==1 else rect(aa,d,s,s+.12,-offset-4,-offset-1)
   if g.buffer(-.5).covers(pp):add('COMP_MALL_'+r['name']+'_PARTITION_'+str(j)+'_'+str(side),pp,-3.6,-1,status)
 issues.append({'id':'MALL_INTERIOR_'+r['name'],'xy':[c.x,c.y],'type':'generic_interiors_and_shell_identity_pending'})
# Mapped R1: use closest shell to choose provisional heading, label association unverified.
f=next(f for f in json.load(open(root/'Stage01_Sources/entrance_candidates.geojson'))['features'] if f['properties'].get('ref')=='R1');tf=Transformer.from_crs(4326,3826,always_xy=True);x,y=tf.transform(*f['geometry']['coordinates']);a=(x-301495.6087493267,y-2770459.509396812);name,g=min(shells,key=lambda ng:ng[1].distance(Point(a)));c=g.representative_point();dist=Point(a).distance(c);d=((c.x-a[0])/dist,(c.y-a[1])/dist);status='R1 OSM XY; straight stair, heading, shell association and elevations estimated'
for j in range(24):add('COMP_R1_STEP_'+str(j),rect(a,d,j*.3,(j+1)*.3,-1.2,1.2),-3.9,-j*.15,status)
landing=rect(a,d,7.2,9,-1.2,1.2);add('COMP_R1_LANDING',landing,-3.9,-3.6,status)
for side in [-1,1]:
 for j in range(12):
  poly=rect(a,d,j*.6,(j+1)*.6,side*1.3-.075,side*1.3+.075);add('COMP_R1_WALL_'+str(side)+'_'+str(j),poly,-3.9,max(-.8,.9-j*.3),status)
issues.append({'id':'R1_ENTRANCE','xy':a,'type':'heading_and_shell_association_unverified','provisional_shell':name,'ground_and_roof_opening':'pending'})
(out/'malls_payload.json').write_text(json.dumps({'parts':parts,'issues':issues},ensure_ascii=False));print({'meshes':len(parts),'issues':len(issues)})
