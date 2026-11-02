import bpy,json,pathlib,os,math
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;sc.view_layers[0].update();report=json.load(open(out/'mapped_vent_shell_report.json'));issues=[];rows=[]
for item in report['items']:
 o=bpy.data.objects[item['new_object']];points=[o.matrix_world@v.co for v in o.data.vertices];z0=min(p.z for p in points);z1=max(p.z for p in points)
 if abs(z0-item['base_z_m'])>.001 or abs(z1-item['height_m'])>.001:issues.append({'object':o.name,'issue':'elevation_changed'})
 if any(not math.isfinite(c) for p in points for c in p):issues.append({'object':o.name,'issue':'nonfinite'})
 for name in item['archived']:
  if bpy.data.objects[name].visible_get(view_layer=sc.view_layers[0]):issues.append({'object':name,'issue':'retained_proxy_visible'})
 rows.append({'object':o.name,'z0':z0,'z1':z1,'vertices':len(o.data.vertices),'faces':len(o.data.polygons)})
markers=[m for m in sc.timeline_markers if m.name.startswith('EW_1SEC_')];assert len(markers)==106 and all(m.camera and m.camera.get('direction')=='TOWARD_BOULEVARD_AXIS' for m in markers)
r={'checked':len(rows),'issues':issues,'animation_markers':len(markers),'items':rows,'limits':'Geometry/elevation and hidden-original checks only; not real-world height validation'};(out/'mapped_vent_shell_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result={k:v for k,v in r.items() if k!='items'}
