import bpy,json,os,pathlib,datetime,math
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';s=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=s
name='ZHONGLUN_STATION_PHOTO_0912_EST';assert not bpy.data.collections.get(name)
bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_ZHONGLUN_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True)
ids=['w270524575','w270524576'];old=[o for o in s.objects if any(i in o.name for i in ids) and o.visible_get()]
assert len(old)==4
for c in list(s.collection.children):
 rem=[o for o in old if o.name in c.objects]
 if not rem:continue
 state=s.view_layers[0].layer_collection.children[c.name].exclude;clone=c.copy();clone.name='ZHONGLUN12_'+c.name;s.collection.children.unlink(c);s.collection.children.link(clone)
 for o in rem:clone.objects.unlink(o)
 s.view_layers[0].layer_collection.children[clone.name].exclude=state
col=bpy.data.collections.new(name);s.collection.children.link(col);materials={}
for k,v in {'STONE':(.68,.68,.65,1),'FRAME':(.86,.87,.85,1),'GLASS':(.12,.25,.28,1),'METAL':(.2,.23,.25,1),'RED':(.72,.07,.045,1),'BLUE':(.025,.15,.48,1)}.items():
 m=bpy.data.materials.new('ZHONGLUN_'+k);m.diffuse_color=v;materials[k]=m
source='https://www.google.com/maps/@25.0461347,121.5398856,3a,90y,270h,90t/data=!3m4!1e1!3m2!1sD1Rot5xfxAoFnFVJWYeqwQ!2e0'
objects=[];report=[]
def box(label,a,b,mat='STONE'):
 verts=[(a[0],a[1],a[2]),(b[0],a[1],a[2]),(b[0],b[1],a[2]),(a[0],b[1],a[2]),(a[0],a[1],b[2]),(b[0],a[1],b[2]),(b[0],b[1],b[2]),(a[0],b[1],b[2])]
 m=bpy.data.meshes.new('ZHONGLUN_'+id+'_'+label);m.from_pydata([u*x+v*y+Vector((0,0,z)) for x,y,z in verts],[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);m.materials.append(materials[mat]);m.update();o=bpy.data.objects.new(m.name,m);col.objects.link(o);o.location=origin;o['osm_id']=id;o['status']='2025 street-view informed estimate; roof identity, dimensions, pump count and column positions unmeasured';o['source_url']=source;objects.append(o.name)
for id,xy,w,d,h in [('w270524576',(2930.95,512.71),41.893,18.614,5.6),('w270524575',(2932.38,497.57),33.35,12.907,4.4)]:
 start=len(objects);origin=Vector((*xy,0));u=Vector((.98537,.17033,0)).normalized();v=Vector((-u.y,u.x,0))
 box('ROOF',(0,0,h-.5),(w,d,h),'FRAME')
 for z0,z1,mat in [(h-.65,h-.3,'BLUE'),(h-.3,h-.18,'FRAME'),(h-.18,h,'RED')]:
  box('FASCIA_S_'+mat,(0,-.08,z0),(w,.12,z1),mat);box('FASCIA_N_'+mat,(0,d-.12,z0),(w,d+.08,z1),mat)
 if id=='w270524576':
  for x in [w*.2,w*.5,w*.8]:
   for y in [d*.3,d*.7]:
    box('COLUMN',(x-.22,y-.22,0),(x+.22,y+.22,h-.5),'FRAME');box('ISLAND',(x-2,y-.65,0),(x+2,y+.65,.16),'STONE')
    box('PUMP',(x+.65,y-.35,.16),(x+1.35,y+.35,1.6),'FRAME');box('DISPLAY',(x+.66,y-.37,1.05),(x+1.34,y-.35,1.4),'METAL')
 else:
  # Low service/wash shelter; open end and estimated glazed service frontage.
  box('BACK_WALL',(0,d-.2,0),(w,d,h-.5),'FRAME');box('SIDE_WALL',(0,0,0),(.2,d,h-.5),'FRAME')
  for j in range(7):
   x=j*w/7;box('FRONT_POST',(x,0,0),(x+.18,.22,h-.5),'FRAME')
   if j<5:
    box('FRONT_PLINTH',(x+.18,0,0),(x+w/7,.2,.7),'FRAME');box('FRONT_GLASS',(x+.18,.08,.7),(x+w/7,.12,3.5),'GLASS')
  box('END_POST',(w-.2,d-.25,0),(w,d,h-.5),'FRAME')
 report.append({'osm_id':id,'objects':objects[start:],'prior_height_m':26.4,'height_estimate_m':h,'uncertainty_m':1.2,'source_url':source,'pending':'Column and pump placement estimated; source footprints retained; service/wash identity and exact opening layout pending closer registration'})
s.view_layers[0].update();assert all(not o.visible_get() for o in old)
(out/'zhonglun_station_photo_report.json').write_text(json.dumps({'items':report,'parts':len(objects),'retained_objects':[o.name for o in old],'source_date':'2025-04','main_scene_replacement':True},ensure_ascii=False,indent=2))
review=bpy.data.scenes.new('ZHONGLUN_STATION_REVIEW_0912');review.use_fake_user=True;review.collection.children.link(col);review.render.engine='BLENDER_WORKBENCH';review.render.resolution_x=1000;review.render.resolution_y=700;review.render.resolution_percentage=100;review.display.shading.light='STUDIO';review.display.shading.color_type='MATERIAL';review.display.shading.show_shadows=False;review.display.shading.show_cavity=True
cd=bpy.data.cameras.new('ZHONGLUN_REVIEW_CAMERA');cam=bpy.data.objects.new(cd.name,cd);review.collection.objects.link(cam);review.camera=cam;cd.type='ORTHO';cd.ortho_scale=65;cd.clip_end=500
cam.location=(3000,465,35);cam.rotation_euler=(Vector((2950,518,2))-cam.location).to_track_quat('-Z','Y').to_euler();review.render.filepath=str(out/'ZHONGLUN_STATION_PHOTO.png');bpy.ops.render.render(write_still=True,scene=review.name)
bpy.context.window.scene=s;bpy.ops.wm.save_as_mainfile(filepath=str(out/'CIVIC_FULL_CORRIDOR_WORKING_20260912.blend'));result={'parts':len(objects),'assets':2,'rendered':1}
