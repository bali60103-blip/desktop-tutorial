import bpy,json,os,pathlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['GONGZHONG_INTEGRATED_OPENINGS_0912_EST'];bpy.context.window.scene=sc;sc.view_layers[0].update();o=next(o for o in sc.objects if o.get('source_object')=='COMP_公中_B2_FLOOR');tree=BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons]);paths=[p for p in json.load(open(out/'gongzhong_integrated_paths.json')) if p['id'].startswith('CORE_公中_0_B2_')];miss=[];samples=0
for p in paths:
 for j in range(1,10):
  q=Vector(p['a']).lerp(Vector(p['b']),j/10);q.z=-7.1;hit,_,_,_=tree.ray_cast(q,Vector((0,0,-1)),.2);samples+=1
  if hit is None or abs(hit.z+7.2)>.001:miss.append({'path':p['id'],'sample':j})
markers=[m for m in sc.timeline_markers if m.name.startswith('EW_1SEC_')];assert len(markers)==106;assert sc.use_fake_user
bpy.context.window.scene=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
import tempfile,shutil
with tempfile.TemporaryDirectory(prefix='civic-persistence-') as folder:
 probe=str(pathlib.Path(folder)/'probe.blend');shutil.copyfile(bpy.data.filepath,probe)
 with bpy.data.libraries.load(probe,link=True) as (available,requested):persisted=sc.name in available.scenes
r={'floor_support_samples':samples,'floor_support_misses':miss,'scene_present_in_saved_file':persisted,'scene_fake_user':sc.use_fake_user,'comparison_camera_markers':len(markers),'adopted':False};(out/'gongzhong_floor_persistence_check.json').write_text(json.dumps(r,indent=2));result=r
