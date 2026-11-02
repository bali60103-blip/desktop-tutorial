import bpy,bmesh,json,pathlib,datetime,math
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Y26PhotoVariant';out.mkdir(exist_ok=True);stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_y26_'+stamp+'.blend')),copy=True)
p=json.load(open(root/'YMallEntrances/source/y_entrance_payload.json'));e=next(e for e in p['entries'] if e['ref']=='Y26');a=Vector(e['live_xy']);d=(Vector(e['lower_landing_xy'])-a).normalized();n=Vector((-d.y,d.x));main=bpy.data.scenes['Scene'];col=bpy.data.collections.new('Y26_PHOTO_CONFIGURATION_ESTIMATED');main.collection.children.link(col);main.view_layers[0].layer_collection.children[col.name].exclude=True;sc=bpy.data.scenes.new('Y26_PHOTO_COMPARISON');sc.collection.children.link(col);sc.world=main.world;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=False;sc.display.shading.show_cavity=True
mats={}
for key,c in [('frame',(.85,.87,.83,1)),('glass',(.35,.62,.65,.3)),('stone',(.34,.35,.36,1)),('metal',(.12,.14,.15,1))]:
 m=bpy.data.materials.new('Y26_'+key);m.diffuse_color=c;mats[key]=m
qa=[]
def xyz(x,y,z):q=a+d*x+n*y;return(q.x,q.y,z)
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def box(name,x0,x1,y0,y1,z0,z1,key):
 vs=[xyz(x,y,z) for z in [z0,z1] for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]];me=bpy.data.meshes.new(name);me.from_pydata(vs,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not ed.is_manifold for ed in bm.edges);assert bad==0;bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);col.objects.link(o);me.materials.append(mats[key]);o['status']='PHOTO-CONFIGURATION ALTERNATIVE: all dimensions and orientation estimated; not surveyed';qa.append(name)
# Four outside risers to raised landing, inferred from photos; tread .3 and rise .15 assumed.
for i in range(4):box('Y26_OUTSIDE_STEP_'+str(i),-2.4+i*.3,-2.1+i*.3,-2.5,2.5,-.15,(i+1)*.15,'stone')
box('Y26_RAISED_LANDING',-1.2,0,-2.5,2.5,-.15,.6,'stone')
# Parallel stair and escalator alternative. 28 assumed rises from +.6 to -3.6.
for i in range(28):
 z=.6-i*.15;box('Y26_STAIR_'+str(i),i*.3,(i+1)*.3,-2.2,.2,-3.9,z,'stone');box('Y26_ESC_STEP_'+str(i),i*.3,(i+1)*.3,.8,1.8,-3.9,z,'metal')
for side in [.68,1.92]:
 for i in range(14):box('Y26_ESC_BALUSTRADE_'+str(side)+'_'+str(i),i*.6,(i+1)*.6,side-.06,side+.06,.6-i*.3,.6-i*.3+.9,'metal')
# Portal dimensions are working guesses; published design area is NOT used as canopy footprint.
for side in [-2.65,2.65]:
 box('Y26_PLINTH_'+str(side),-1.2,8.8,side-.12,side+.12,0,.85,'stone')
 for i in range(7):
  x=-1.2+i*(10/6);box('Y26_FRAME_'+str(side)+'_'+str(i),x-.065,x+.065,side-.065,side+.065,.85,3.75,'frame')
  if i<6:box('Y26_GLASS_'+str(side)+'_'+str(i),x+.065,x+10/6-.065,side-.018,side+.018,.9,3.65,'glass')
box('Y26_REMOVABLE_ROOF',-1.4,9,-2.9,2.9,3.75,3.9,'frame')
# Keep roof visible for exterior review, glazing shown as wire in workbench for inspection.
for o in col.objects:
 if 'GLASS' in o.name:o.hide_render=True;o.display_type='WIRE';o['render_note']='Glass hidden in solid workbench preview; modeled panel retained'
cd=bpy.data.cameras.new('Y26_PHOTO_REVIEW');cam=bpy.data.objects.new(cd.name,cd);sc.collection.objects.link(cam);sc.camera=cam;center=Vector(xyz(3,0,.4));cam.location=Vector(xyz(-12,-15,11));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=23;sc.render.resolution_x=1400;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.render.filepath=str(out/'Y26_exterior.png');bpy.ops.render.render(write_still=True,scene=sc.name)
bpy.data.objects['Y26_REMOVABLE_ROOF'].hide_render=True;sc.render.filepath=str(out/'Y26_cutaway.png');bpy.ops.render.render(write_still=True,scene=sc.name);bpy.data.objects['Y26_REMOVABLE_ROOF'].hide_render=False
file=out/('CIVIC_Y26_PHOTO_VARIANT_'+stamp+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));r={'file':str(file),'meshes':len(qa),'nonmanifold_edges':0,'source':'https://www.studiox4.com/works/y26/','photo_observed':['white-framed glazed pavilion','raised exterior entrance landing','parallel stairs and escalator'],'assumed':{'platform_z':.6,'B1_z':-3.6,'roof_z':3.75,'roof_plan_m':[10.4,5.8],'stair_width':2.4,'escalator_tread_width':1.0},'limitations':'Footprint, roof simplification, stair orientation, escalator direction, dimensions, tread counts all estimated. Roof hanging mesh art omitted. Project design area115.5m2 not treated as canopy footprint. Separate scene, original Y26 retained; no certified connection or obstruction check.'};(out/'photo_variant_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result=r
