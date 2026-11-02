"""Reversible assumed stair sidewalls and handrails; not a surveyed/code-certified design."""
import bpy,bmesh,json,pathlib,datetime,math
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'YStairDetail';out.mkdir(exist_ok=True)
main=bpy.data.scenes['Scene'];sc=bpy.data.scenes['Y_MALL_ENTRANCE_COMPARISON'];src=root/'YMallEntrances/source/y_entrance_payload.json';p=json.load(open(src));stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_stair_detail_'+stamp+'.blend')),copy=True)
assert not bpy.data.collections.get('Y_STAIR_DETAIL_ESTIMATED')
col=bpy.data.collections.new('Y_STAIR_DETAIL_ESTIMATED');main.collection.children.link(col);sc.collection.children.link(col);main.view_layers[0].layer_collection.children[col.name].exclude=True
wallmat=bpy.data.materials.new('Y_STAIR_CONCRETE_EST');wallmat.diffuse_color=(.5,.58,.6,1);railmat=bpy.data.materials.new('Y_STAIR_RAIL_EST');railmat.diffuse_color=(.13,.15,.17,1);qa=[]
def solid(name,verts,faces,mat):
 assert all(len(f)==len(set(f)) for f in faces)
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);assert all(len(set(v.index for v in f.verts))==len(f.verts) for f in bm.faces);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);assert bad==0;bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);col.objects.link(o);me.materials.append(mat);o['status']='ASSUMED: stair direction, width, sidewalls and rails not surveyed';qa.append({'name':name,'nonmanifold_edges':bad});return o
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def prism(name,a,b,halfwidth,z0,ta,tb,mat):
 d=(Vector(b)-Vector(a)).normalized();n=Vector((-d.y,d.x))*halfwidth;xy=[Vector(a)+n,Vector(b)+n,Vector(b)-n,Vector(a)-n];v=[(q.x,q.y,z0) for q in xy]+[(q.x,q.y,z) for q,z in zip(xy,[ta,tb,tb,ta])];return solid(name,v,faces,mat)
def rod(name,a,b,r=.035):
 a=Vector(a);b=Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,0,1)))
 if u.length<.001:u=d.cross(Vector((0,1,0)))
 u.normalize();v=d.cross(u);pts=[tuple(c+r*(math.cos(i*math.tau/8)*u+math.sin(i*math.tau/8)*v)) for c in [a,b] for i in range(8)];fs=[tuple(range(7,-1,-1)),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)];return solid(name,pts,fs,railmat)
entries=[]
for e in p['entries']:
 if not e['built']:continue
 a=Vector(e['live_xy']);end=Vector(e['lower_landing_xy']);d=(end-a).normalized();n=Vector((-d.y,d.x));ref=e['ref'];length=(end-a).length
 def xy(s,offset):return a+d*s+n*offset
 for side in [-1,1]:
  # 0.15m walls outside original 2.4m stair width; avoid closing either stair mouth.
  for i in range(12):
   s0=i*.6;s1=(i+1)*.6;prism(ref+'_SIDE_'+str(side)+'_'+str(i),xy(s0,side*1.275),xy(s1,side*1.275),.075,-3.9,max(.9-s0*.5,-.8),max(.9-s1*.5,-.8),wallmat)
  rod(ref+'_HANDRAIL_'+str(side),(*xy(0,side*1.08),.9),(*xy(7.2,side*1.08),-2.7))
  for j in range(7):
   s0=j*1.2;z=-s0*.5;rod(ref+'_POST_'+str(side)+'_'+str(j),(*xy(s0,side*1.08),z),(*xy(s0,side*1.08),z+.9),.025)
  # Enclose only external branch, ending at original shell edge so mall circulation remains open.
  branch_end=e['distance_to_boundary_m'] if not e['inside'] else 0
  if branch_end>7.21:prism(ref+'_BRANCH_WALL_'+str(side),xy(7.2,side*1.275),xy(branch_end,side*1.275),.075,-3.9,-.8,-.8,wallmat)
 entries.append({'ref':ref,'flight_sidewalls':24,'handrails':2,'posts':14,'clear_between_handrails_m':2.09,'branch_wall_length_m':max(0,(e['distance_to_boundary_m'] if not e['inside'] else 0)-7.2)})
# Check additions alone for obstructions on walking centerlines, at 1.6m above steps.
from mathutils.bvhtree import BVHTree
verts=[];polys=[]
for o in col.objects:
 off=len(verts);verts.extend(o.matrix_world@v.co for v in o.data.vertices);polys.extend([[off+i for i in f.vertices] for f in o.data.polygons])
tree=BVHTree.FromPolygons(verts,polys);hits=[]
for e in p['entries']:
 if not e['built']:continue
 a=Vector(e['live_xy']);d=(Vector(e['lower_landing_xy'])-a).normalized()
 for j in range(24):
  s0=j*.3+.05;s1=min(s0+.25,7.19);q=a+d*s0;z=1.6-.5*s0;loc,_,_,dist=tree.ray_cast(Vector((q.x,q.y,z)),Vector((d.x,d.y,-.5)).normalized(),.28)
  if loc is not None:hits.append({'ref':e['ref'],'step':j,'distance':dist})
assert not hits,hits
cam=sc.camera
for ref in ['Y13','Y27','Y12']:
 e=next(e for e in p['entries'] if e['ref']==ref);center=Vector((*e['live_xy'],-2));cam.location=center+Vector((25,-30,30));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=48;sc.render.filepath=str(out/(ref+'_detail.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
file=out/('CIVIC_Y_STAIR_DETAIL_'+stamp+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));r={'file':str(file),'entrances':len(entries),'mesh_count':len(qa),'nonmanifold_edges':sum(x['nonmanifold_edges'] for x in qa),'centerline_ray_hits_against_new_parts':hits,'centerline_ray_samples':len(entries)*24,'details':entries,'limits':'Checks against new parts only; no compliance or as-built accuracy claim. Ground excavation, actual elevator/escalator types, shop layout and entrance directions unresolved.'};(out/'stair_detail_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result={k:v for k,v in r.items() if k!='details'}
