"""Detail a retained photo-informed ramp alternative. Added dimensions/drains are explicitly estimated."""
import bpy,json,pathlib,os,math,datetime
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';working=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];scene=bpy.data.scenes['YANJI_PHOTO_COMPARISON_ESTIMATED'];col=bpy.data.collections['CAL3_YANJI_PHOTO_COMPARISON'];assert not bpy.data.objects.get('YANJI_DETAIL_HANGER_0'),'Already detailed';bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_YANJI_DETAIL_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True)
anchor=Vector((4215.1324,348.2492,0));angle=math.atan2(-5.75,55);d=Vector((math.cos(angle),math.sin(angle),0));n=Vector((-d.y,d.x,0));mats={k:bpy.data.materials['YANJI_PHOTO_'+k] for k in ['wall','paving','orange','yellow','white','dark']};created=[];faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def world(v):return anchor+d*v[0]+n*v[1]+Vector((0,0,v[2]))
def mesh(name,vs,fs,mat):
 m=bpy.data.meshes.new(name);m.from_pydata([tuple(world(v)-anchor) for v in vs],[],fs);m.materials.append(mats[mat]);m.update();o=bpy.data.objects.new(name,m);o.location=anchor;col.objects.link(o);o['status']='Estimated detail on unadopted Yanji comparison; no measured positions or drainage survey';created.append(o);return o
def box(name,x0,x1,y0,y1,z0,z1,mat):return mesh(name,[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],faces,mat)
def cyl(name,x,y,z0,z1,r,mat):
 N=16;vs=[(x+r*math.cos(i*math.tau/N),y+r*math.sin(i*math.tau/N),z) for z in [z0,z1] for i in range(N)];return mesh(name,vs,[tuple(reversed(range(N))),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)],mat)
xs=[-8,0,12,30,55];ys=[0,0,.5,.8,0];zs=[0,0,-.4,-1.8,-3.6]
def surface(x):
 for j in range(4):
  if xs[j]<=x<=xs[j+1]:
   t=(x-xs[j])/(xs[j+1]-xs[j]);return ys[j]*(1-t)+ys[j+1]*t,zs[j]*(1-t)+zs[j+1]*t
 raise ValueError(x)
# Archive the old square posts; preserve all source data in an excluded collection.
keep=bpy.data.collections.new('CAL3_RETAINED_YANJI_SQUARE_POSTS');working.collection.children.link(keep);archived=[]
for o in list(col.objects):
 if o.name.startswith('YANJI_PHOTO_CENTER_POST_'):keep.objects.link(o);col.objects.unlink(o);archived.append(o.name)
working.view_layers[0].layer_collection.children[keep.name].exclude=True
for i in range(15):
 x=1+i*.85;y,z=surface(x);cyl('YANJI_DETAIL_DIVIDER_BASE_'+str(i),x,y,z,z+.035,.10,'dark');cyl('YANJI_DETAIL_DIVIDER_'+str(i),x,y,z+.035,z+.75,.04,'yellow');cyl('YANJI_DETAIL_REFLECTOR_'+str(i),x,y,z+.49,z+.57,.041,'white')
for i,y in enumerate([-2.4,2.4]):
 box('YANJI_DETAIL_CANTILEVER_'+str(i),-.08,.76,y-.045,y+.045,2.76,2.84,'dark');cyl('YANJI_DETAIL_HANGER_'+str(i),.71,y,1.88,2.8,.012,'dark')
# Drains are alternative detail assumptions. Recessed channel pan is represented under the flush grate.
drains=[]
for tag,x in [('UPPER',-.8),('LOWER',53.5)]:
 y,z=surface(x);width=5.6;verts=[];ff=[]
 def part(x0,x1,y0,y1,z0,z1):
  off=len(verts);verts.extend([(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]);ff.extend([tuple(off+i for i in f) for f in faces])
 # Match ramp slope at each end so the long thin detail does not float.
 y0,z0=surface(x-.15);y1,z1=surface(x+.15)
 pan=mesh('YANJI_DETAIL_DRAIN_PAN_'+tag,[(x-.15,y0-width/2,z0-.15),(x+.15,y1-width/2,z1-.15),(x+.15,y1+width/2,z1-.15),(x-.15,y0+width/2,z0-.15),(x-.15,y0-width/2,z0+.001),(x+.15,y1-width/2,z1+.001),(x+.15,y1+width/2,z1+.001),(x-.15,y0+width/2,z0+.001)],faces,'dark')
 for j in range(57):
  yy=-width/2+j*width/56;off=len(verts);verts.extend([(x-.15,y0+yy-.012,z0+.002),(x+.15,y1+yy-.012,z1+.002),(x+.15,y1+yy+.012,z1+.002),(x-.15,y0+yy+.012,z0+.002),(x-.15,y0+yy-.012,z0+.012),(x+.15,y1+yy-.012,z1+.012),(x+.15,y1+yy+.012,z1+.012),(x-.15,y0+yy+.012,z0+.012)]);ff.extend([tuple(off+i for i in f) for f in faces])
 mesh('YANJI_DETAIL_DRAIN_GRATE_'+tag,verts,ff,'wall');drains.append({'name':tag,'local_x':x,'width_m':width,'length_m':.3,'status':'Estimated covered drain; invert/outfall and actual existence unverified; no hydraulic claim'})
issues=[]
for o in created:
 edges={}
 for f in o.data.polygons:
  for e in f.edge_keys:edges[e]=edges.get(e,0)+1
 if any(c!=2 for c in edges.values()):issues.append(o.name)
scene.display.shading.show_shadows=False;bpy.ops.render.render(write_still=True,scene=scene.name);bpy.context.window.scene=working;working.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
r={'created_objects':len(created),'retained_square_posts':archived,'new_cylindrical_dividers':15,'hanger_rods':2,'drains':drains,'mesh_issues':issues,'adopted':False,'posted_height_limit_m':1.8,'limit_note':'Observed sign value; not a measured vertical clearance','limits':'Drain pans are detail proxies embedded in the existing ramp slab; excavation, outfall, thickness and structural support require future validation.'};(out/'yanji_detail_report.json').write_text(json.dumps(r,indent=2));result={k:v for k,v in r.items() if k!='retained_square_posts'}
