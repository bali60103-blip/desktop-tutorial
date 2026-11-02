"""Reversible photo-informed hotel shell. All dimensions and bay counts are estimates."""
import bpy,json,os,pathlib,datetime,math
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3'
s=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=s
name='MIRAMAR_PHOTO_SHELL_0912_EST';assert not bpy.data.collections.get(name)
bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_MIRAMAR_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True)
old=[o for o in s.objects if 'w238513441' in o.name and o.visible_get()]
assert len(old)==2
for c in list(s.collection.children):
 remove=[o for o in old if o.name in c.objects]
 if not remove:continue
 state=s.view_layers[0].layer_collection.children[c.name].exclude
 clone=c.copy();clone.name='MIRAMAR12_'+c.name;s.collection.children.unlink(c);s.collection.children.link(clone)
 for o in remove:clone.objects.unlink(o)
 s.view_layers[0].layer_collection.children[clone.name].exclude=state
col=bpy.data.collections.new(name);s.collection.children.link(col)
source='https://www.yaifu.com.tw/%E7%BE%8E%E9%BA%97%E4%BF%A1%E8%8A%B1%E5%9C%92%E9%85%92%E5%BA%97'
materials={}
for k,v in {'STONE':(.64,.59,.46,1),'FRAME':(.79,.75,.64,1),'GLASS':(.13,.26,.31,1),'METAL':(.18,.15,.12,1),'JOINT':(.38,.35,.29,1)}.items():
 m=bpy.data.materials.new('MIRAMAR_'+k);m.diffuse_color=v;materials[k]=m
origin=Vector((2690.18,409.76,0));u=Vector((59.24,-1.63,0)).normalized();v=Vector((-u.y,u.x,0));W=59.2624;D=24.22;H=51.2;objects=[]
def box(label,a,b,mat='STONE'):
 if min(b[i]-a[i] for i in range(3))<.0001:return
 verts=[(a[0],a[1],a[2]),(b[0],a[1],a[2]),(b[0],b[1],a[2]),(a[0],b[1],a[2]),(a[0],a[1],b[2]),(b[0],a[1],b[2]),(b[0],b[1],b[2]),(a[0],b[1],b[2])]
 m=bpy.data.meshes.new('MIRAMAR_'+label);m.from_pydata([u*x+v*y+Vector((0,0,z)) for x,y,z in verts],[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);m.materials.append(materials[mat]);m.update();o=bpy.data.objects.new(m.name,m);col.objects.link(o);o.location=origin;o['osm_id']='w238513441';o['status']='Photo-informed estimate; dimensions, bay counts, rear facade and entry orientation unmeasured';o['source_url']=source;objects.append(o.name)
box('BASE',(0,0,0),(W,D,.2));box('ROOF',(0,0,H-.25),(W,D,H))
# Floors and shell maintain real recesses, rather than a solid core behind windows.
for z in [8+3.6*i for i in range(12)]:box('FLOOR_'+str(z),(.35,.35,z-.22),(W-.35,D-.35,z),'STONE')
# Local wall mapping: front and rear photo-derived repeat, rear explicitly inferred.
for side in ['S','N','E','W']:
 length=W if side in ['S','N'] else D
 bays=14 if side in ['S','N'] else 1
 pitch=length/bays
 def wall(label,x0,x1,z0,z1,d0=0,d1=.35,mat='STONE'):
  if side=='S':a=(x0,d0,z0);b=(x1,d1,z1)
  elif side=='N':a=(x0,D-d1,z0);b=(x1,D-d0,z1)
  elif side=='W':a=(d0,x0,z0);b=(d1,x1,z1)
  else:a=(W-d1,x0,z0);b=(W-d0,x1,z1)
  box(side+'_'+label,a,b,mat)
 # Tall ground storey with opaque arch panels above glazed bays.
 for j in range(bays):
  x=j*pitch;ww=min(2.75,pitch-.8);l=x+(pitch-ww)/2;r=l+ww
  wall('GROUND_PIER_'+str(j),x,l,0,8);wall('GROUND_PIER_R_'+str(j),r,x+pitch,0,8)
  wall('GROUND_HEAD_'+str(j),l,r,5.1,8)
  wall('GROUND_GLASS_'+str(j),l,r,.2,5.1,.2,.23,'GLASS')
  wall('GROUND_MULLION_'+str(j),(l+r)/2-.04,(l+r)/2+.04,.2,5.1,.05,.22,'METAL')
  # Simplified arched relief, not a copy of the sculptural medallions.
  if side=='S':
   for q in range(32):
    t=(q+.5)*math.pi/32;cx=(l+r)/2+ww*.44*math.cos(t);cz=6.15+ww*.44*math.sin(t)
    wall('ARCH_%d_%d'%(j,q),cx-.085,cx+.085,cz-.085,cz+.085,-.16,.02,'FRAME')
 for i in range(12):
  z=8+i*3.6
  for j in range(bays):
   x=j*pitch;ww=2.35 if side in ['S','N'] else 2.4;l=x+(pitch-ww)/2;r=l+ww;lo=z+.65;hi=z+2.95
   wall('PIER_%d_%d'%(i,j),x,l,z,z+3.6);wall('PIER_R_%d_%d'%(i,j),r,x+pitch,z,z+3.6)
   wall('SILL_%d_%d'%(i,j),l,r,z,lo);wall('HEAD_%d_%d'%(i,j),l,r,hi,z+3.6)
   wall('GLASS_%d_%d'%(i,j),l,r,lo,hi,.24,.27,'GLASS')
   for a,b,c,d in [(l-.12,l,lo-.12,hi+.12),(r,r+.12,lo-.12,hi+.12),(l,r,lo-.12,lo),(l,r,hi,hi+.12)]:wall('FRAME_%d_%d'%(i,j),a,b,c,d,-.13,.03,'FRAME')
 for z in [7.8,36.6,50.7]:wall('CORNICE_'+str(z),-.25,length+.25,z,z+.4,-.5,.35,'FRAME')
# Estimated entrance canopy, supported by front columns; actual central position pending imagery registration.
box('CANOPY',(W*.37,-4.2,4.9),(W*.63,.3,5.2),'METAL')
for x in [W*.38,W*.62]:box('CANOPY_POST',(x-.18,-3.9,0),(x+.18,-3.54,4.9),'FRAME')
for j in range(5):
 x=W*.37+(W*.26)*j/4;box('CANOPY_BEAM',(x-.05,-4.2,4.7),(x+.05,.3,4.9),'METAL')
s.view_layers[0].update();assert all(not o.visible_get() for o in old)
report={'osm_id':'w238513441','parts':len(objects),'objects':objects,'retained_objects':[o.name for o in old],'prior_height_m':6.6,'height_estimate_m':H,'height_uncertainty_m':6,'working_levels':14,'source_url':source,'additional_source':'https://www.miramargarden.com.tw/zh-tw/台北美麗信/Room/精薈客房','evidence':'Contractor photographs show projecting window surrounds, cornices, tall ground glazing and canopy. Hotel page gives one room type clear height 3.7m; this is NOT building floor-to-floor height. 14-level envelope and 51.2m total are working assumptions, not a surveyed height.','pending':['Exact floor levels and height','Bay count and footprint registration','Rear facade','Canopy position and depth'],'main_scene_replacement':True}
(out/'miramar_photo_shell_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
review=bpy.data.scenes.new('MIRAMAR_PHOTO_REVIEW_0912');review.use_fake_user=True;review.collection.children.link(col);review.render.engine='BLENDER_WORKBENCH';review.render.resolution_x=1000;review.render.resolution_y=850;review.render.resolution_percentage=100;review.display.shading.light='STUDIO';review.display.shading.color_type='MATERIAL';review.display.shading.show_shadows=False;review.display.shading.show_cavity=True
cd=bpy.data.cameras.new('MIRAMAR_REVIEW_CAMERA');cam=bpy.data.objects.new(cd.name,cd);review.collection.objects.link(cam);review.camera=cam;cd.type='ORTHO';cd.clip_end=1000
for label,eye,target,scale in [('FULL',(-65,-90,65),(W/2,D/2,25),95),('ENTRY',(W/2-12,-30,12),(W/2,0,5),30)]:
 cam.location=origin+u*eye[0]+v*eye[1]+Vector((0,0,eye[2]));look=origin+u*target[0]+v*target[1]+Vector((0,0,target[2]));cam.rotation_euler=(look-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=scale;review.render.filepath=str(out/('MIRAMAR_'+label+'.png'));bpy.ops.render.render(write_still=True,scene=review.name)
bpy.context.window.scene=s;bpy.ops.wm.save_as_mainfile(filepath=str(out/'CIVIC_FULL_CORRIDOR_WORKING_20260912.blend'));result={'parts':len(objects),'height_estimate_m':H,'renders':2}
