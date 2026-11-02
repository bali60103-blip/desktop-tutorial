import bpy,bmesh,json,pathlib,datetime
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Y26Orientation';p=json.load(open(out/'integrated_payload.json'));stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_integrated_'+stamp+'.blend')),copy=True)
main=bpy.data.scenes['Scene'];assert not bpy.data.scenes.get('Y26_B_INTEGRATED_COMPARISON');sc=bpy.data.scenes.new('Y26_B_INTEGRATED_COMPARISON');sc.world=main.world;col=bpy.data.collections.new('Y26_B_INTEGRATED_COMPARISON');sc.collection.children.link(col);main.collection.children.link(col);main.view_layers[0].layer_collection.children[col.name].exclude=True
for o in bpy.data.collections['Y26_BUILDING_AXIS_ALTERNATIVE'].objects:
 if not o.name.startswith('Y26_B_'):col.objects.link(o)
mat=bpy.data.materials.new('Y26_INTEGRATED_FLOOR_EST');mat.diffuse_color=(.17,.52,.55,1);qa=[];wallobjects=[]
for m in p['parts']:
 me=bpy.data.meshes.new(m['name']);me.from_pydata(m['mesh']['vertices'],[],m['mesh']['faces']);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);assert bad==0;bm.to_mesh(me);bm.free();o=bpy.data.objects.new(me.name,me);col.objects.link(o);me.materials.append(mat);o['status']=p['status'];qa.append({'name':o.name,'nonmanifold_edges':bad})
 if 'WALL' in o.name:wallobjects.append(o)
vs=[];fs=[]
for o in wallobjects:
 off=len(vs);vs.extend(v.co for v in o.data.vertices);fs.extend([[i+off for i in f.vertices] for f in o.data.polygons])
tree=BVHTree.FromPolygons(vs,fs);hits=[]
for a,b in zip(p['walk_path_xy'],p['walk_path_xy'][1:]):
 a=Vector((*a,-2));b=Vector((*b,-2));v=b-a;hit,_,_,_=tree.ray_cast(a,v.normalized(),v.length)
 if hit is not None:hits.append(list(hit))
assert not hits
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=False;sc.display.shading.show_cavity=True;cam=bpy.data.objects['Y26_PHOTO_REVIEW'];sc.collection.objects.link(cam);sc.camera=cam;old=cam.matrix_world.copy();scale=cam.data.ortho_scale;center=Vector((113,932,-2));cam.location=center+Vector((12,-16,12));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=27;sc.render.resolution_x=1400;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;roof=bpy.data.objects['Y26_REMOVABLE_ROOF_AXIS_ALT'];roof.hide_render=True;sc.render.filepath=str(out/'Y26_B_integrated.png');bpy.ops.render.render(write_still=True,scene=sc.name);roof.hide_render=False;cam.matrix_world=old;cam.data.ortho_scale=scale
for w in bpy.context.window_manager.windows:
 for a in w.screen.areas:
  if a.type=='VIEW_3D':a.spaces.active.clip_end=30000
file=out/('CIVIC_Y26_INTEGRATED_'+stamp+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));r={'file':str(file),'parts':qa,'connected_floor_polygon':p['floor_connected'],'wall_hits_at_head_height_on_connector':hits,'viewport_clip_end_m':30000,'limitations':p['status'],'originals_retained':True};(out/'integrated_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result=r
