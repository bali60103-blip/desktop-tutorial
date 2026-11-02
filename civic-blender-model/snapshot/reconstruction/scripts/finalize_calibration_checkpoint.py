import bpy,json,pathlib,collections,math,time
from mathutils import Vector
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/Calibration');sc=bpy.data.scenes['CIVIC_COMPLETE_WORKING_ASSEMBLY'];sc.view_layers[0].update();bad=[];count=0
for o in sc.objects:
 if o.type!='MESH' or not o.visible_get(view_layer=sc.view_layers[0]) or not o.name.startswith(('CAL_','COMP_')):continue
 count+=1;m=o.data;ec=collections.Counter(tuple(sorted(e)) for p in m.polygons for e in p.edge_keys);z=sum(p.area<1e-10 for p in m.polygons);nf=sum(not all(math.isfinite(x) for x in v.co) for v in m.vertices);edge=sum(n!=2 for n in ec.values())
 if z or nf or edge:bad.append({'object':o.name,'zero_area_faces':z,'nonfinite_vertices':nf,'nonmanifold_edges':edge})
head=json.load(open(out/'headroom_check.json'));col=bpy.data.collections.get('CALIBRATION_UNRESOLVED_POSITIONS') or bpy.data.collections.new('CALIBRATION_UNRESOLVED_POSITIONS')
if col.name not in sc.collection.children:sc.collection.children.link(col)
for r in head['issues']:
 name='CAL_ISSUE_'+r['path'];o=bpy.data.objects.get(name) or bpy.data.objects.new(name,None)
 if o.name not in col.objects:col.objects.link(o)
 h=r['hits'][0];o.location=(*h['xy'],-1);o.empty_display_type='SPHERE';o.empty_display_size=1;o['status']='UNRESOLVED source/layout overlap; not corrected by arbitrary excavation';o['conflicting_objects']=json.dumps(sorted({h['object'] for h in r['hits']}),ensure_ascii=False)
report={'file':bpy.data.filepath,'checked_active_meshes':count,'mesh_issues':bad,'road_cameras':sum(o.type=='CAMERA' and o.name.startswith('CIVIC200_') for o in sc.objects),'all_cameras':sum(o.type=='CAMERA' for o in sc.objects),'headroom_sample_paths':head['sampled_paths'],'headroom_samples':head['samples'],'headroom_unresolved_paths':head['paths_with_obstructions'],'status':'PARTIAL_SITE_CALIBRATION; geometry fixes applied, streetview images unavailable; absolute elevations, occluded equipment and conflicting source envelopes unresolved'}
text=bpy.data.texts.get('CIVIC_CALIBRATION_STATUS.json') or bpy.data.texts.new('CIVIC_CALIBRATION_STATUS.json');text.clear();text.write(json.dumps(report,ensure_ascii=False,indent=2));sc['calibration_status']=report['status'];sc['calibration_report']=str(out/'校準報告.md');bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);(out/'final_checkpoint.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));result=report
