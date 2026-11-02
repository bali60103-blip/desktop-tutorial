"""Use local mesh coordinates to avoid float32 collapse in long world-coordinate walls."""
import bpy,json,pathlib
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'CompletionPass';p=json.load(open(out/'payload.json'));fixed=[]
for part in p['parts']:
 if part['name'] not in ['COMP_敦延_B1_PERIMETER','COMP_敦延_B2_PERIMETER']:continue
 o=bpy.data.objects[part['name']];vs=part['mesh']['vertices'];origin=[sum(v[i] for v in vs)/len(vs) for i in range(3)];local=[tuple(v[i]-origin[i] for i in range(3)) for v in vs];old=o.data;me=bpy.data.meshes.new(o.name+'_LOCAL_COORDINATES');me.from_pydata(local,[],part['mesh']['faces']);me.update();assert all(p.area>1e-10 for p in me.polygons)
 for m in old.materials:me.materials.append(m)
 old.use_fake_user=True;o.data=me;o.location=origin;o['numerical_repair']='Local coordinates preserve thin triangulation faces; same source footprint and elevations';fixed.append(o.name)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);(out/'numeric_repair.json').write_text(json.dumps({'fixed':fixed,'method':'Local mesh origin; source shape and height unchanged'},ensure_ascii=False,indent=2));exec(pathlib.Path('/tmp/civic-stage00/reconstruction/scripts/check_completion_checkpoint.py').read_text())
