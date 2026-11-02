"""Inside Blender: median surface, separate point-touching shells, ground-only renders.
ROOT and MEDIAN provided. Does not modify elevated geometry.
"""
import bpy,bmesh,json,pathlib,datetime
from mathutils import Vector
root=pathlib.Path(ROOT);root.mkdir(parents=True,exist_ok=True);s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');sc=bpy.context.scene
bpy.ops.wm.save_as_mainfile(filepath=str(root/('before_ground_finish_'+s+'.blend')),copy=True)
p=json.loads(pathlib.Path(MEDIAN).read_text());name='GROUND_MEDIAN_WORKING_ESTIMATED';old=bpy.data.objects.get(name)
if old:bpy.data.objects.remove(old,do_unlink=True)
me=bpy.data.meshes.new(name);me.from_pydata(p['mesh']['vertices'],[],p['mesh']['faces']);me.update();o=bpy.data.objects.new(name,me);bpy.data.collections['GROUND_FULL_01_OFFICIAL_AND_ESTIMATED'].objects.link(o);mat=bpy.data.materials.new(name+'_MAT');mat.diffuse_color=(.58,.58,.52,1);me.materials.append(mat);o['status']=json.dumps(p['assumptions']);o['summary']=json.dumps(p['summary'])
# Existing island guesses retained in archive but hidden in this consolidated working model.
c=bpy.data.collections.get('03_Islands_estimated_width')
if c:c.hide_render=True;c.hide_viewport=True
checks=[]
for col in [bpy.data.collections['GROUND_FULL_01_OFFICIAL_AND_ESTIMATED'],bpy.data.collections['GROUND_FULL_02_CROSSINGS_AND_RAMPS_ESTIMATED']]:
 for ob in col.objects:
  if ob.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.dissolve_degenerate(bm,dist=.00001,edges=list(bm.edges));bm.faces.ensure_lookup_table();bm.verts.ensure_lookup_table()
  before=sum(not e.is_manifold for e in bm.edges);labels={};component=0
  for face in bm.faces:
   if face in labels:continue
   stack=[face];labels[face]=component
   while stack:
    cur=stack.pop()
    for edge in cur.edges:
     if len(edge.link_faces)!=2:continue
     for other in edge.link_faces:
      if other not in labels:labels[other]=component;stack.append(other)
   component+=1
  verts=[];faces=[];indices={}
  for face in bm.faces:
   ids=[]
   for v in face.verts:
    key=(v.index,labels[face])
    if key not in indices:indices[key]=len(verts);verts.append(tuple(v.co))
    ids.append(indices[key])
   faces.append(ids)
  bm.free();new=bpy.data.meshes.new(ob.name+'_SHELLS');new.from_pydata(verts,[],faces);new.update()
  for m in ob.data.materials:new.materials.append(m)
  ob.data=new;bm=bmesh.new();bm.from_mesh(new);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));after=sum(not e.is_manifold for e in bm.edges);bm.to_mesh(new);bm.free();ob['nonmanifold_edges']=after
  checks.append({'object':ob.name,'before_nonmanifold_edges':before,'after_nonmanifold_edges':after,'surface_components':component})
cam=bpy.data.objects['GROUND_FULL_CAMERA'];sc.camera=cam;sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=2200;sc.render.resolution_y=850;sc.render.resolution_percentage=100;sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.render.image_settings.file_format='PNG'
sc['GROUND_WORKING_STATUS']='Ground surface working version: 8 sections, markings, estimated curb ramps and partial inferred medians. Not surveyed as-built.'
file=root/('GROUND_WORKING_'+s+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));result={'file':str(file),'mesh_checks':checks,'median_summary':p['summary'],'ground_status':sc['GROUND_WORKING_STATUS']};(root/'finish_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
