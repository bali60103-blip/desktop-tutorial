"""Inside Blender: replace previous working ground with full-corridor ground version.
Snapshots and visibility preservation prevent overwriting original geometry.
"""
import bpy,json,pathlib,datetime,bmesh
from mathutils import Vector
p=json.loads(pathlib.Path(PAYLOAD).read_text());root=pathlib.Path(ROOT);root.mkdir(parents=True,exist_ok=True);s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');sc=bpy.context.scene
bpy.ops.wm.save_as_mainfile(filepath=str(root/('before_ground_'+s+'.blend')),copy=True)
name='GROUND_FULL_01_OFFICIAL_AND_ESTIMATED';old=bpy.data.collections.get(name)
if old:
 for o in list(old.objects):bpy.data.objects.remove(o,do_unlink=True)
 bpy.data.collections.remove(old)
c=bpy.data.collections.new(name);sc.collection.children.link(c);hidden={}
for oldname in ['01_Sidewalks_official_XY','02_Roads_official_extent']:
 old=bpy.data.collections.get(oldname)
 if old:
  hidden[oldname]={'hide_viewport':old.hide_viewport,'hide_render':old.hide_render};old.hide_viewport=True;old.hide_render=True
checks=[]
colors=[(.18,.21,.23,1),(.32,.25,.2,1),(.55,.52,.47,1),(.76,.75,.71,1)]
for (key,d),color in zip(p['meshes'].items(),colors):
 if not d['vertices']:continue
 me=bpy.data.meshes.new(key);me.from_pydata(d['vertices'],[],d['faces']);me.update();o=bpy.data.objects.new(key,me);c.objects.link(o)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.dissolve_degenerate(bm,dist=.00001,edges=list(bm.edges));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));nonmanifold=sum(not e.is_manifold for e in bm.edges);bm.to_mesh(me);bm.free();me.update()
 mat=bpy.data.materials.new(key+'_MAT');mat.diffuse_color=color;me.materials.append(mat)
 o['geometry_status']='Estimated footprint' if 'GAPS' in key else ('Estimated road-facing curb strips' if 'CURBS' in key else 'Official source XY, clipped to study extent')
 o['vertical_status']='Model local datum and thickness are estimated';o['source_era']='Road footprints historic 2014-2016; sidewalk GIS metadata 2026';o['nonmanifold_edges']=nonmanifold
 checks.append({'object':key,'vertices':len(me.vertices),'faces':len(me.polygons),'nonmanifold_edges':nonmanifold,'area_m2':d['area_m2'],'triangulation_area_loss_m2':d['triangulation_area_loss_m2']})
c['scope']='Civic Boulevard ground sections 1-8 with 70m study clipping; not as-built certified';c['visibility_before']=json.dumps(hidden);c['assumptions']=json.dumps(p['assumptions']);c['remaining']='Crosswalks, junction accessibility and parking mouth details are separate work items'
cam=bpy.data.objects.get('GROUND_FULL_CAMERA')
if not cam:
 ca=bpy.data.cameras.new('GROUND_FULL_CAMERA');cam=bpy.data.objects.new(ca.name,ca);sc.collection.objects.link(cam)
b=p['summary']['bounds'];cx=(b[0]+b[2])/2;cy=(b[1]+b[3])/2;cam.location=(cx,cy,12000);cam.rotation_euler=(Vector((cx,cy,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=(b[2]-b[0])*1.06;cam.data.clip_end=30000;sc.camera=cam
sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=2200;sc.render.resolution_y=850;sc.render.resolution_percentage=100;sc.display.shading.color_type='MATERIAL';sc.render.image_settings.file_format='PNG';sc.render.filepath=str(root/'ground_all_overview.png')
file=root/('GROUND_FULL_'+s+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));result={'file':str(file),'checks':checks,'summary':p['summary'],'previous_ground_visibility':hidden,'status':'Ground surfaces rebuilt; remaining surface features not yet complete'};(root/'build_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
