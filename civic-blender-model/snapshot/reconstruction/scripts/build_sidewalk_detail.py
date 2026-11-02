"""Blender: physical pilot paving and curbs. Preserve originals and save versioned result."""
import bpy,json,pathlib,datetime,bmesh
from mathutils import Vector
p=json.loads(pathlib.Path(PAYLOAD).read_text());root=pathlib.Path(ROOT);root.mkdir(parents=True,exist_ok=True);s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');sc=bpy.context.scene
bpy.ops.wm.save_as_mainfile(filepath=str(root/('before_detail_'+s+'.blend')),copy=True)
name='DETAIL_01_ZHONGLIN_PAVING__ESTIMATED_DIMENSIONS';old=bpy.data.collections.get(name)
if old:
 for o in list(old.objects):bpy.data.objects.remove(o,do_unlink=True)
 bpy.data.collections.remove(old)
c=bpy.data.collections.new(name);sc.collection.children.link(c)
for key,data in p['meshes'].items():
 me=bpy.data.meshes.new(key);me.from_pydata(data['vertices'],[],data['faces']);me.update();o=bpy.data.objects.new(key,me);c.objects.link(o)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0.000001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));boundary=[e for e in bm.edges if e.is_boundary];assert all(abs(e.verts[0].co.z-e.verts[1].co.z)<1e-6 for e in boundary),'Non-planar hole requires inspection';bmesh.ops.holes_fill(bm,edges=boundary,sides=0) if boundary else None;bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));o['nonmanifold_edges']=sum(not e.is_manifold for e in bm.edges);assert o['nonmanifold_edges']==0,'Detail mesh not closed';bm.to_mesh(me);bm.free();me.update()
 mat=bpy.data.materials.new(key+'_MATERIAL');mat.diffuse_color=(.58,.54,.46,1) if key.startswith('PAVING') else (.78,.78,.74,1);o.data.materials.append(mat);o['source']='Taipei sidewalk GIS XY; road-facing curb classification from OSM';o['parameters']=json.dumps(p['parameters']);o['source_ids']=json.dumps(p['source_ids']);o['physical_piece_count']=p['summary']['paving_tiles' if key.startswith('PAVING') else 'curb_stones']
c['status']='Physical detailed pilot started; dimensions estimated, not verified as-built';c['known_missing']='Kerb ramps, tactile routes, drains and underground entrances need position evidence'
cam=bpy.data.objects.get('DETAIL_CAMERA')
if not cam:
 ca=bpy.data.cameras.new('DETAIL_CAMERA');cam=bpy.data.objects.new(ca.name,ca);sc.collection.objects.link(cam)
cam.location=(1225,735,100);cam.rotation_euler=(Vector((1225,708,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=65;cam.data.clip_end=20000;sc.camera=cam
sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=1600;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.render.image_settings.file_format='PNG';sc.render.filepath=str(root/'detail_closeup.png')
file=root/('DETAIL_01_'+s+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file))
result={'file':str(file),'objects':len(c.objects),'summary':p['summary'],'render':sc.render.filepath,'status':'Detailed physical paving pilot started; gates not automatically passed'}
(root/'build_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
