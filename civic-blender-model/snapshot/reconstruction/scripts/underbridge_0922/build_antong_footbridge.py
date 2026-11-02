"""Antong pedestrian bridge comparison. OSM XY, all vertical dimensions estimated."""
import bpy,os,json,math,bmesh
from mathutils import Vector
from collections import Counter
s=bpy.context.scene;assert s.name=='CIVIC_UNDERBRIDGE_MASSING_20260916'
root=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922');d=json.load(open(os.path.join(root,'antong_footbridge_manifest.json')))
name='UB_ANTONG_FOOTBRIDGE_OSM_EST';assert bpy.data.collections.get(name) is None
c=bpy.data.collections.new(name);s.collection.children.link(c)
mat=bpy.data.materials.get('UB_BATCH_roof')
made=[]
def span(n,a,b,w,thick):
 dx=b[0]-a[0];dy=b[1]-a[1];le=math.hypot(dx,dy);nx=-dy/le*w/2;ny=dx/le*w/2
 vs=[(a[0]-nx,a[1]-ny,a[2]-thick),(b[0]-nx,b[1]-ny,b[2]-thick),(b[0]+nx,b[1]+ny,b[2]-thick),(a[0]+nx,a[1]+ny,a[2]-thick),(a[0]-nx,a[1]-ny,a[2]),(b[0]-nx,b[1]-ny,b[2]),(b[0]+nx,b[1]+ny,b[2]),(a[0]+nx,a[1]+ny,a[2])]
 fs=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.update()
 ob=bpy.data.objects.new(name+'_'+n,me);c.objects.link(ob)
 if mat:me.materials.append(mat)
 for k,v in {'source_url':d['source_url'],'source_date':d['source_date'],'osm_ids':str(d['osm_ids']),'xy_status':'OSM registered coordinates','height_status':'estimated 5.5m deck; 2.1m width; 1.1m guard','dimensions_verified':False,'review_required':True,'stairs_status':'sloped stair masses, treads and exact landing heights not verified'}.items():ob[k]=v
 made.append(ob)
def route(tag,pts,zs):
 for i,(a,b) in enumerate(zip(pts,pts[1:])):
  aa=(a[0],a[1],zs[i]);bb=(b[0],b[1],zs[i+1]);span(tag+'_'+str(i),aa,bb,d['width'],d['thickness'])
  dx=b[0]-a[0];dy=b[1]-a[1];le=math.hypot(dx,dy)
  for side in [-1,1]:
   nx=-dy/le*(d['width']/2-.05)*side;ny=dx/le*(d['width']/2-.05)*side
   span(tag+'_GUARD_'+str(i)+'_'+str(side),(aa[0]+nx,aa[1]+ny,aa[2]+1.1),(bb[0]+nx,bb[1]+ny,bb[2]+1.1),.10,1.1)
route('DECK',d['bridge'],[d['height'],d['height']])
for key,start,end in [('south',.18,d['height']),('north',d['height'],.18)]:
 pts=d[key];ls=[math.dist(a,b) for a,b in zip(pts,pts[1:])];total=sum(ls);zs=[start];run=0
 for le in ls:run+=le;zs.append(start+(end-start)*run/total)
 route(key.upper()+'_STAIR',pts,zs)
# The visible south landing column is a proportion estimate; other support positions remain unresolved.
x,y=d['bridge'][0];span('SOUTH_SUPPORT',(x-.3,y,.18+d['height']),(x+.3,y,.18+d['height']),.6,d['height'])
non=[]
for o in made:
 ec=Counter(tuple(sorted(e)) for p in o.data.polygons for e in p.edge_keys)
 if any(v!=2 for v in ec.values()):non.append(o.name)
report={'objects':len(made),'non_closed_meshes':non,'dimensions_verified':False,'full_corridor_complete':False,'limits':['Only south stair visibly checked','North stair follows OSM without opposite-side photo confirmation','Headroom and bridge supports remain estimates','Sloped stair mass is not a final tread model']}
json.dump(report,open(os.path.join(root,'antong_footbridge_report.json'),'w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result=report
