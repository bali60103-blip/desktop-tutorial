import bpy,json,os,pathlib,datetime,math
from mathutils import Vector
root=pathlib.Path(os.environ['CIVIC_MODEL_ROOT']);out=root/'PriorityNodes_20260914';r=json.load(open(out/'priority_a_registration.json'));s=bpy.context.scene
assert s.name=='CIVIC_BLOCKS_FACADES_WORKING';assert not bpy.data.scenes.get('PRIORITY_A_REVIEW_20260914')
snapshot=out/('BEFORE_PRIORITY_A_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(snapshot),copy=True)
col=bpy.data.collections.new('PRIORITY_A_SCHEMATIC_EXTENTS_EST');s.collection.children.link(col);mat=bpy.data.materials.new('PRIORITY_A_RED');mat.diffuse_color=(1,.06,.02,1)
review=s.copy();review.name='PRIORITY_A_REVIEW_20260914';review.use_fake_user=True;review.timeline_markers.clear();bpy.context.window.scene=review
cams=bpy.data.collections.new('PRIORITY_A_REVIEW_CAMERAS');review.collection.children.link(cams);records=[]
for n in r['nodes']:
 ring=n['working_focus_polygon']['coordinates'][0];cu=bpy.data.curves.new('P1_'+n['id']+'_ESTIMATED_BOUNDARY','CURVE');cu.dimensions='3D';cu.bevel_depth=.12;cu.bevel_resolution=0;sp=cu.splines.new('POLY');sp.points.add(len(ring)-1)
 for p,(x,y) in zip(sp.points,ring):p.co=(x,y,.35,1)
 cu.materials.append(mat);o=bpy.data.objects.new(cu.name,cu);col.objects.link(o);o.hide_render=True;o.show_in_front=True;o['status']=n['status'];o['priority']='P1';o['node']=n['id']
 pts=n['axis']['coordinates'];p=Vector((pts[0][0],pts[0][1],0));q=Vector((pts[-1][0],pts[-1][1],0));center=(p+q)/2;d=(q-p).normalized();normal=Vector((-d.y,d.x,0))
 for side,sign in [('N',1),('S',-1)]:
  cd=bpy.data.cameras.new('P1_'+n['id']+'_'+side);cam=bpy.data.objects.new(cd.name,cd);cams.objects.link(cam);cam.location=center+normal*sign*50+Vector((0,0,16));target=center+Vector((0,0,5));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=max(155,(q-p).length+35);cd.clip_end=1500;cam['purpose']='Dedicated priority-node model review; not road animation camera';records.append({'node':n['id'],'camera':cam.name,'side':side})
cd=bpy.data.cameras.new('P1_A_OVERVIEW');cam=bpy.data.objects.new(cd.name,cd);cams.objects.link(cam);cam.location=(1690,430,470);cam.rotation_euler=(Vector((1680,655,0))-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=820;cd.clip_end=2000;records.append({'node':'A','camera':cam.name,'side':'overview'})
review.render.engine='BLENDER_WORKBENCH';review.render.resolution_x=1100;review.render.resolution_y=650;review.render.resolution_percentage=100;review.display.shading.light='STUDIO';review.display.shading.color_type='MATERIAL';review.display.shading.show_shadows=False;review.display.shading.show_cavity=True;review.render.image_settings.file_format='PNG'
for rec in records:
 review.camera=bpy.data.objects[rec['camera']];review.render.filepath=str(out/(rec['camera']+'.png'));bpy.ops.render.render(write_still=True,scene=review.name)
# Keep original animation and current user view unchanged; boundaries are viewport-only guides.
bpy.context.window.scene=s;assert len([m for m in s.timeline_markers if m.camera])==106
s['priority_nodes_20260914']='A1-A3, B1-B2, C1-C4; all P1; west to east. A boundaries currently schematic estimates.'
file=out/'CIVIC_PRIORITY_A_WORKING_20260914.blend';bpy.ops.wm.save_as_mainfile(filepath=str(file));report={'review_scene':review.name,'renders':records,'node_count':3,'road_animation_cameras':106,'boundary_status':'Working schematic registration, not exact site boundaries','saved_model':file.name,'snapshot':snapshot.name};(out/'priority_a_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));result=report
