import bpy,json,pathlib,collections,math
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Calibration';sc=bpy.data.scenes['CIVIC_COMPLETE_WORKING_ASSEMBLY'];r=json.load(open(out/'topology_repair.json'));col=bpy.data.collections['COMPLETION_GROUND_HIGHWAY'];old=bpy.data.objects[r['replaces']]
for p in r['parts']:
 org=Vector(p['mesh']['vertices'][0]);m=bpy.data.meshes.new(p['name']);m.from_pydata([tuple(Vector(v)-org) for v in p['mesh']['vertices']],[],p['mesh']['faces']);m.update();o=bpy.data.objects.new(p['name'],m);o.location=org;col.objects.link(o)
 for mat in old.data.materials:m.materials.append(mat)
 o['calibration_status']=r['method'];o['changed_area_m2']=r['changed_area_m2']
col.objects.unlink(old)
# An architect-published height applies to this single named exhibition building.
o=bpy.data.objects['COMP_FRONT_558011740_0'];before=[(o.matrix_world@v.co).z for v in o.data.vertices];low=min(before);high=max(before);o.data=o.data.copy()
for v in o.data.vertices:
 w=o.matrix_world@v.co;w.z=low+(w.z-low)*(46.05/(high-low));v.co=o.matrix_world.inverted()@w
o.data.update();o['height_m']=46.05;o['height_source']='https://www.twarchitect.org.tw/works/國家會展中心南港展覽館二館/';o['calibration_status']='Published overall height46.05m; footprint remains OSM; uniform massing omits stepped roof and rooftop details';o['previous_estimated_height_m']=high-low
report={'landmark':{'name':o.name,'before_height_m':high-low,'after_height_m':46.05,'status':o['calibration_status']},'topology_cleanup':{k:v for k,v in r.items() if k!='parts'}}
# Explicit source constraints, kept separate from unsupported absolute elevations.
constraints=[{'id':'Y_VERTICAL_SOURCE','source':'https://www.ceci.org.tw/Upload/Download/BE9F1DB3-1378-4492-BE0A-F183E2BE3798.pdf','page':88,'B1_floor_to_floor_m':5.7,'B2_floor_to_floor_m':5.4,'status':'Published structural floor heights; ground cover/datum unknown; current -3.6/-7.2 assumptions are not calibrated. Do not equate these with clear height.'},{'id':'QSQUARE_HEIGHT','source':'https://www.onenessarchitects.com/project/Redium-Parcel-9-Taipei-Main-Station-BOT-Joint-Development?lang=tw','complex_max_height_m':69.95,'status':'Mixed podium/tower complex. Existing3.3m podium is unverified; applying69.95m to whole footprint would be incorrect.'},{'id':'SONGSHAN_HEIGHT','source':'https://www.twarchitect.org.tw/works/潤泰松山車站共構bot/','station_tower_height_m':81,'other_tower_height_m':84.8,'status':'A podium footprint is not the81m tower footprint; tower-part geometry must be identified before height change.'}]
(out/'source_constraints.json').write_text(json.dumps(constraints,ensure_ascii=False,indent=2));text=bpy.data.texts.get('CIVIC_CALIBRATION_CONSTRAINTS.json') or bpy.data.texts.new('CIVIC_CALIBRATION_CONSTRAINTS.json');text.clear();text.write(json.dumps(constraints,ensure_ascii=False,indent=2))
sc.view_layers[0].update();bb=[]
for o in sc.objects:
 if o.type!='MESH':continue
 v=[o.matrix_world@Vector(v) for v in o.bound_box];bb.append({'name':o.name,'min':[min(p[i] for p in v) for i in range(3)],'max':[max(p[i] for p in v) for i in range(3)],'collections':[c.name for c in o.users_collection]})
(out/'assembly_bounds.json').write_text(json.dumps(bb,ensure_ascii=False));bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);(out/'geometry_finish.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));result=report
