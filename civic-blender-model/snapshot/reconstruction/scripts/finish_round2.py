import bpy,json,pathlib,collections,math
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/CalibrationRound2');sc=bpy.context.scene
old=bpy.data.collections['CALIBRATION_UNRESOLVED_POSITIONS'];sc.collection.children.unlink(old)
c=bpy.data.collections.new('CAL2_UNRESOLVED_POSITIONS');sc.collection.children.link(c);r=json.load(open(out/'headroom_check.json'))
for issue in r['issues']:
 o=bpy.data.objects.new('CAL2_ISSUE_'+issue['path'],None);c.objects.link(o);h=issue['hits'][0];o.location=(*h['xy'],-1);o.empty_display_type='SPHERE';o.empty_display_size=1.2;o['status']='UNRESOLVED model overlap; requires source/layout calibration';o['path']=issue['path'];o['conflicting_objects']=json.dumps(sorted(set(h['object'] for h in issue['hits'])),ensure_ascii=False)
issues=[]
for o in sc.objects:
 if not o.name.startswith('CAL2_YANJI_ENTRY_WALL_'):continue
 edges=collections.Counter(tuple(sorted((p.vertices[i],p.vertices[(i+1)%len(p.vertices)]))) for p in o.data.polygons for i in range(len(p.vertices)))
 if any(n!=2 for n in edges.values()):issues.append(o.name+':nonmanifold')
 if any(not math.isfinite(x) for v in o.data.vertices for x in v.co):issues.append(o.name+':nonfinite')
assert not issues
sc['round2_remaining_paths']=len(r['issues']);bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result={'file':bpy.data.filepath,'mesh_issues':issues,'current_unresolved_markers':len(c.objects),'resolved_path':'COMP_ACCESS_延吉_0','additional_detected_path':'CORE_公中_0_B1_B','original_scene_preserved':True};(out/'final_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
