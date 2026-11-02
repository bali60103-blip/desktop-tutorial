import bpy,json,os,pathlib,datetime
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';paths={p['id']:p for p in json.load(open(out.parent/'Calibration/checked_paths.json'))};bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_GUARD_WIDTH_FIX_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True);rows=[]
for o in bpy.data.collections['CAL3_PARKING_LANDING_GUARDS'].objects:
 if o.get('guard_outer_edge_clearance_m')==.08:continue
 key=o['source_path'];_,section,core,level,_=key.split('_');p=paths[key.removesuffix('_LANDING')+'_A'];a,b=Vector(p['a']),Vector(p['b']);h=b-a;h.z=0;h.normalize();landing=bpy.data.objects['COMP_'+section+'_CORE'+core+'_L'+level[1:]+'_LANDING'];extent=max((landing.matrix_world@v.co-b).dot(h) for v in landing.data.vertices);desired=extent-.08;delta=desired-.99
 for i,v in enumerate(o.data.vertices):
  if 10<=i<50 or i>=60:v.co+=h*delta
 o.data.update();o['guard_outer_edge_clearance_m']=.08;rows.append({'object':o.name,'translation_m':delta,'new_offset_from_flight_end_m':desired})
r={'guards_fixed':len(rows),'method':'Set outer rail/post centerline 0.08m inside actual modeled landing edge; retain connection to flight handrails. Mesh is shared by comparison copies.','changes':rows};(out/'landing_guard_width_fix.json').write_text(json.dumps(r,indent=2));bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result={'guards_fixed':len(rows),'max_shift_m':max(abs(x['translation_m']) for x in rows)}
