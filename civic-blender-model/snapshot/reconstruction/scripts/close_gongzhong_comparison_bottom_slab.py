import bpy,json,pathlib,os
from mathutils import Vector,Matrix
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['GONGZHONG_INTEGRATED_OPENINGS_0912_EST'];row=next(r for r in json.load(open(out/'gongzhong_integrated_openings_payload.json'))['items'] if r['source']=='COMP_公中_B2_FLOOR');o=next(o for o in sc.objects if o.get('source_object')=='COMP_公中_B2_FLOOR');origin=Vector(row['vertices'][0]);m=bpy.data.meshes.new('GZ12_BOTTOM_SLAB_CLOSED');m.from_pydata([tuple(Vector(v)-origin) for v in row['vertices']],[],row['faces']);m.update()
for mat in o.data.materials:m.materials.append(mat)
o.data=m;o.matrix_world=Matrix.Translation(origin);o['bottom_slab_closed_under_stair']=True;o['verification_status']='Estimated bottom slab closes old stair void. No floor below B2 modeled. Structural thickness and real foundation unverified.';sc.use_fake_user=True
r={'object':o.name,'area_added_m2':row['new_area_m2']-row['old_area_m2'],'bottom_slab_closed':True,'main_scene_changed':False};(out/'gongzhong_bottom_slab_closure.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result=r
