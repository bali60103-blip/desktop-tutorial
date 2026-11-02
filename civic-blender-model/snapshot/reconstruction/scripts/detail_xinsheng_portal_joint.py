"""Model visible south-column joint details; no hidden bearing specification inferred."""
import bpy,os,json,pathlib,datetime,math,collections
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'PriorityNodes_20260914';sc=bpy.data.scenes['P1_PORTAL_PHOTO_PROPORTION_REVIEW'];prev=bpy.context.window.scene
assert not bpy.data.collections.get('P1_PORTAL_SOUTH_JOINT_PHOTO_EST')
bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_PORTAL_JOINT_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True)
r=json.load(open(out/'xinsheng_observed_portal_report.json'));a,b=[Vector(p) for p in r['pillar_xy']];across=(b-a).normalized();along=Vector((across.y,-across.x,0));up=Vector((0,0,1));col=bpy.data.collections.new('P1_PORTAL_SOUTH_JOINT_PHOTO_EST');sc.collection.children.link(col)
mat=bpy.data.materials.new('P1_JOINT_PLATE_WHITE');mat.diffuse_color=(.61,.63,.61,1);bolt=bpy.data.materials.new('P1_JOINT_BOLT_GREY');bolt.diffuse_color=(.33,.35,.33,1)
def mesh(name,vs,fs,m):
 me=bpy.data.meshes.new(name);me.from_pydata([v-a for v in vs],[],fs);me.materials.append(m);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);o.location=a;o['evidence']='Street View 2025-02 LyDE7zKTZ6cDVJfCjJg6jg yaw220 pitch150 FOV45';o['confidence']='Visible morphology; metric dimensions and bolt layout estimated';return o
v=[a+along*x+across*y+up*z for z in (10.1,10.7) for x,y in [(1,-.88),(1.025,-.88),(1.025,.88),(1,.88)]]
mesh('P1_SOUTH_JOINT_PLATE_EST',v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
def tube(name,start,end,radius,sides,m):
 direction=(end-start).normalized();u=across if abs(direction.dot(across))<.9 else along;u=(u-direction*direction.dot(u)).normalized();v=direction.cross(u)
 vs=[p+radius*(u*math.cos(2*math.pi*i/sides)+v*math.sin(2*math.pi*i/sides)) for p in (start,end) for i in range(sides)];fs=[list(reversed(range(sides))),list(range(sides,2*sides))]+[[i,(i+1)%sides,(i+1)%sides+sides,i+sides] for i in range(sides)];mesh(name,vs,fs,m)
for row in range(4):
 for j in range(12):
  p=a+along*1.025+across*(-.77+j*1.54/11)+up*(10.17+row*.15);tube('P1_SOUTH_BOLT_%02d_%02d_EST'%(row,j),p,p+along*.022,.025,6,bolt)
p=a+along*1.13-across*1.02;tube('P1_SOUTH_DRAINPIPE_EST',p+up*.15,p+up*10.8,.075,16,mat)
for i,z in enumerate([1,3,5,7,9]):tube('P1_SOUTH_DRAIN_COLLAR_%d_EST'%i,p+up*z,p+up*(z+.07),.09,16,mat)
bpy.context.window.scene=sc;sc.view_layers[0].update();bad=[]
for o in col.objects:
 ec=collections.Counter(tuple(sorted(e)) for f in o.data.polygons for e in f.edge_keys)
 if any(v!=2 for v in ec.values()):bad.append(o.name)
assert not bad
cd=bpy.data.cameras.new('P1_JOINT_CLOSEUP');cam=bpy.data.objects.new(cd.name,cd);sc.collection.objects.link(cam);target=a+up*10.15;cam.location=target+along*6-across*2+up*1;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=3.8;sc.camera=cam;sc.display.shading.show_cavity=True;sc.render.filepath=str(out/'P1_SOUTH_JOINT_DETAIL.png');bpy.ops.render.render(write_still=True,scene=sc.name)
report={'meshes':len(col.objects),'closed_mesh_errors':bad,'observed':['Rectangular bolted joint plate and repeated bolt heads','External round drainpipe and collars'],'estimated':{'plate_m':[.025,1.76,.6],'bolt_grid':[4,12],'bolt_radius_m':.025,'pipe_diameter_m':.15,'collar_spacing_m':2},'bearing_pad_status':'No separate pad distinguishable in this view. Bolted exterior does not prove absence of hidden bearings.','source_url':'https://www.google.com/maps/@25.0461762,121.5302139,3a,45y,220h,150t/data=!3m4!1e1!3m2!1sLyDE7zKTZ6cDVJfCjJg6jg!2e0','placement_status':'South column photo-proportion study only; north side not copied without observation. Prior XY depends on uncalibrated panorama projection; remain provisional.'}
(out/'xinsheng_joint_detail_report.json').write_text(json.dumps(report,indent=2));bpy.context.window.scene=prev;bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result=report
