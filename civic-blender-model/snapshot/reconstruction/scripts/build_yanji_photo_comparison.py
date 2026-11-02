import os
import bpy,pathlib,json,math
from mathutils import Vector
out=(pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3');working=bpy.context.scene
col=bpy.data.collections.new('CAL3_YANJI_PHOTO_COMPARISON');working.collection.children.link(col)
scene=bpy.data.scenes.new('YANJI_PHOTO_COMPARISON_ESTIMATED');scene.collection.children.link(col);scene.world=working.world
mats={}
for name,c in [('wall',(.43,.44,.42,1)),('paving',(.15,.16,.16,1)),('orange',(.78,.28,.09,1)),('yellow',(.92,.65,.08,1)),('white',(.9,.91,.89,1)),('dark',(.055,.07,.08,1))]:
 m=bpy.data.materials.new('YANJI_PHOTO_'+name);m.diffuse_color=c;mats[name]=m
anchor=Vector((4215.1324,348.2492,0));angle=math.atan2(-5.75,55);d=Vector((math.cos(angle),math.sin(angle),0));n=Vector((-d.y,d.x,0))
def local(x,y,z):return anchor+d*x+n*y+Vector((0,0,z))
def obj(name,vs,fs,material):
 origin=local(0,0,0);m=bpy.data.meshes.new(name);m.from_pydata([tuple(local(*v)-origin) for v in vs],[],fs);m.materials.append(mats[material]);m.update();o=bpy.data.objects.new(name,m);o.location=origin;col.objects.link(o);o['verification_status']='PHOTO-INFORMED COMPARISON. Dimensions and map-photo anchor estimated, not surveyed. Not adopted in assembly.';return o
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def box(name,x0,x1,y0,y1,z0,z1,mat):return obj(name,[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],faces,mat)
# Two lanes and bend-in descent inferred from entrance photo and schematic, not a swept-path design.
xs=[-8,0,12,30,55];ys=[0,0,.5,.8,0];zs=[0,0,-.4,-1.8,-3.6];half=2.9
for j in range(len(xs)-1):
 x0,x1=xs[j:j+2];y0,y1=ys[j:j+2];z0,z1=zs[j:j+2]
 obj('YANJI_PHOTO_RAMP_'+str(j),[(x0,y0-half,z0-.2),(x1,y1-half,z1-.2),(x1,y1+half,z1-.2),(x0,y0+half,z0-.2),(x0,y0-half,z0),(x1,y1-half,z1),(x1,y1+half,z1),(x0,y0+half,z0)],faces,'paving')
 for side in [-1,1]:
  a0=side*half;a1=side*(half+.25);lo,hi=sorted([a0,a1]);obj('YANJI_PHOTO_RETAINING_'+str(j)+'_'+str(side),[(x0,y0+lo,z0-.2),(x1,y1+lo,z1-.2),(x1,y1+hi,z1-.2),(x0,y0+hi,z0-.2),(x0,y0+lo,.9),(x1,y1+lo,.9),(x1,y1+hi,.9),(x0,y0+hi,.9)],faces,'wall')
for side in [-1,1]:box('YANJI_PHOTO_PORTAL_POST_'+str(side),-.2,.2,side*3.25-.22,side*3.25+.22,0,3.5,'wall')
box('YANJI_PHOTO_PORTAL_SIGN',-.18,.18,-3.45,3.45,2.8,3.5,'orange')
# 1.8m is observed posted restriction, not a claim of measured structural clearance.
box('YANJI_PHOTO_LIMITER',.65,.77,-2.75,2.75,1.80,1.88,'yellow')
for i in range(15):
 x=1+i*.85;z=-max(0,x)*.4/12;box('YANJI_PHOTO_CENTER_POST_'+str(i),x-.035,x+.035,-.05,.05,z,z+.75,'yellow')
box('YANJI_PHOTO_DISPLAY_PYLON',-.45,.25,-4.2,-3.55,0,4.2,'dark');box('YANJI_PHOTO_DISPLAY_FACE',-.47,-.44,-4.1,-3.65,.5,4.0,'orange')
text=bpy.data.curves.new('YANJI_LIMIT_LABEL','FONT');text.body='YANJI  |  1.8 m';text.size=.33;text.align_x='CENTER';o=bpy.data.objects.new('YANJI_PHOTO_LABEL',text);col.objects.link(o);o.location=local(-.21,0,3.0);o.rotation_euler=(math.pi/2,0,angle-math.pi/2);text.materials.append(mats['white'])
camdata=bpy.data.cameras.new('YANJI_PHOTO_COMPARISON_CAMERA');cam=bpy.data.objects.new('YANJI_PHOTO_COMPARISON_CAMERA',camdata);col.objects.link(cam);cam.location=local(-10,-2,1.7);target=local(5,0,1.3);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camdata.lens=25;scene.camera=cam;scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.display.shading.color_type='MATERIAL';scene.display.shading.light='STUDIO';scene.display.shading.show_cavity=True;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(out/'YANJI_PHOTO_COMPARISON.png')
working.view_layers[0].layer_collection.children[col.name].exclude=True;bpy.ops.render.render(write_still=True,scene=scene.name);bpy.context.window.scene=working;bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
r={'scene':scene.name,'anchor_live_xy':list(anchor)[:2],'anchor_status':'Google contributor-photo map center; ±unknown position error; official schematic supports west-of-Yanji-Street entrance only','assumed_ramp_width_m':5.8,'assumed_ramp_run_m':55,'assumed_bottom_z_m':-3.6,'posted_maxheight_observed_m':1.8,'adopted':False,'reason':'Current parking envelope conflicts with photo-supported west entrance; do not excavate existing model using unmeasured photo coordinates','objects':len(col.objects)};(out/'yanji_photo_comparison.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result=r
