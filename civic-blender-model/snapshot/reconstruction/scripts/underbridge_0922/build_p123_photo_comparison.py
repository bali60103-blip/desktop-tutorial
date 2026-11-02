"""P123 photo-proportion study. Isolated comparison; legacy piers untouched.
Visible forms are observed. All numerical dimensions and XY are working estimates.
"""
import bpy,math,os,json
from mathutils import Vector
from collections import Counter
assert bpy.context.scene.name=='CIVIC_UNDERBRIDGE_MASSING_20260916'
NAME='UB_TAIYUAN_P123_PHOTO_COMPARISON'
assert not bpy.data.scenes.get(NAME),'Study already exists'
s=bpy.data.scenes.new(NAME);c=bpy.data.collections.new(NAME);s.collection.children.link(c)
base=Vector((466,851,0));angle=math.radians(-14)
source='https://www.google.com/maps/@25.0491877,121.5149281,3a,45y,160h,90t/data=!3m4!1e1!3m2!1s7jxY9aXs4Z8BllYteOtqlw!2e0'
mats={}
for n,color in [('concrete',(.6,.6,.56,1)),('steel',(.2,.24,.22,1)),('guard',(.44,.4,.28,1)),('white_pipe',(.74,.76,.72,1)),('green_pipe',(.06,.22,.12,1)),('stone',(.48,.43,.33,1))]:
 m=bpy.data.materials.new('P123_'+n);m.use_nodes=True;m.diffuse_color=color;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=color;mats[n]=m
made=[]
def pt(v):
 x,y,z=v;return (base.x+x*math.cos(angle)-y*math.sin(angle),base.y+x*math.sin(angle)+y*math.cos(angle),z)
def mesh(n,vs,fs,mat):
 me=bpy.data.meshes.new('P123_'+n);me.from_pydata([pt(v) for v in vs],[],fs);me.update()
 ob=bpy.data.objects.new('P123_'+n,me);c.objects.link(ob);me.materials.append(mats[mat])
 for k,val in {'source_url':source,'imagery_date':'2025-05','observed_label':'P123','dimensions_status':'estimated, not measured','xy_status':'approximate panorama-relative placement; untriangulated','height_status':'estimated Z, column top outside detail view','adoption_status':'comparison only; legacy pier correspondence unresolved','review_required':True}.items():ob[k]=val
 made.append(ob);return ob
def box(n,center,size,mat):
 x,y,z=center;w,d,h=size
 return mesh(n,[(x+i*w/2,y+j*d/2,z+k*h/2) for k in [-1,1] for i,j in [(-1,-1),(1,-1),(1,1),(-1,1)]],[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
def rod(n,start,end,r,mat):
 a,b=Vector(start),Vector(end);d=(b-a).normalized();u=d.cross(Vector((0,0,1)))
 if u.length<.01:u=d.cross(Vector((0,1,0)))
 u.normalize();v=d.cross(u);count=12
 vs=[list(p+r*(math.cos(i*2*math.pi/count)*u+math.sin(i*2*math.pi/count)*v)) for p in [a,b] for i in range(count)]
 fs=[tuple(reversed(range(count))),tuple(range(count,count*2))]+[(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
 return mesh(n,vs,fs,mat)
box('COLUMN_EST',(0,0,3.75),(2.6,2.4,7.5),'concrete')
box('PLINTH_EST',(0,0,.15),(3,2.8,.3),'concrete')
# The full shaft height is hypothetical; no support pad is inferred from this photo.
box('EQUIPMENT_ENCLOSURE_EST',(-5.5,0,1.15),(3.2,2.7,2.3),'stone')
box('WALL_VISIBLE_PATCH_EST',(-4,-1.55,.7),(5.1,.3,1.4),'concrete')
for mat,z,r in [('white_pipe',.55,.18),('green_pipe',1.05,.085)]:
 y=1.55 if mat=='white_pipe' else 1.9
 rod(mat+'_HORIZONTAL_EST',(-3.9,y,z),(-1.65,y,z),r,mat)
 rod(mat+'_RISER_EST',(-1.65,y,z),(-1.65,y,7.5),r,mat)
for x in [1.55,2.2]:rod('LADDER_RAIL_'+str(x),(x,1.4,.35),(x,1.4,7.2),.035,'steel')
for i in range(23):rod('LADDER_RUNG_'+str(i),(1.55,1.4,.5+i*.29),(2.2,1.4,.5+i*.29),.018,'steel')
box('PLATFORM_EST',(1.85,1.65,4),(1.15,1.3,.12),'steel')
for x in [1.275,2.425]:
 for y in [1,2.3]:rod('PLATFORM_POST_'+str((x,y)),(x,y,4),(x,y,5.05),.025,'steel')
 rod('PLATFORM_SIDE_RAIL_'+str(x),(x,1,5.05),(x,2.3,5.05),.025,'steel')
rod('PLATFORM_FRONT_RAIL',(1.275,2.3,5.05),(2.425,2.3,5.05),.025,'steel')
rod('PLATFORM_BRACE',(1.35,1.2,3),(2.35,2.2,3.95),.045,'steel')
# Visible pickets modeled as simple pointed masses; counts are not measured.
for i in range(15):
 x=-1.5+i*3/14
 box('FRONT_PICKET_'+str(i),(x,1.5,1),( .07,.07,1.4),'guard')
for side in [-1,1]:
 for i in range(8):box('SIDE_PICKET_'+str(side)+'_'+str(i),(side*1.5,-1.1+i*.32,1),(.07,.07,1.4),'guard')
rod('GUARD_FRONT_TIE',(-1.5,1.5,.85),(1.5,1.5,.85),.022,'guard')
for side in [-1,1]:rod('GUARD_SIDE_TIE_'+str(side),(side*1.5,-1.1,.85),(side*1.5,1.5,.85),.022,'guard')
bad=[]
for ob in made:
 e=Counter(tuple(sorted(k)) for p in ob.data.polygons for k in p.edge_keys)
 if any(v!=2 for v in e.values()):bad.append(ob.name)
cam=bpy.data.objects.new('P123_REVIEW_CAMERA',bpy.data.cameras.new('P123_REVIEW_CAMERA'));s.collection.objects.link(cam)
cam.location=pt((12,20,12));target=Vector(pt((-1,0,3)))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=14;s.camera=cam
sun=bpy.data.objects.new('P123_REVIEW_SUN',bpy.data.lights.new('P123_REVIEW_SUN','SUN'));s.collection.objects.link(sun);sun.data.energy=3;sun.rotation_euler=(.4,-.5,.2)
s.world=bpy.data.worlds.get('UB_ZZ_REVIEW_WORLD');s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1000;s.render.resolution_y=900;s.render.resolution_percentage=100
root=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922');s.render.filepath=os.path.join(root,'P123_PHOTO_COMPARISON.png')
bpy.ops.render.render(write_still=True,scene=s.name)
report={'scene':NAME,'objects':len(made),'non_closed_meshes':bad,'source_url':source,'adopted_in_working_scene':False,'dimensions_verified':False,'open_issues':['P123 identity observed but legacy pier match unresolved','column top and full height not verified','pipe back-side routes unknown','guard dimensions/count estimated','comparison only; do not duplicate into main without resolving legacy pier placement']}
json.dump(report,open(os.path.join(root,'p123_photo_comparison_report.json'),'w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result=report
