import bpy,json,pathlib,os
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];rows=[]
# Remove only the empty collections created by the aborted solid-block precondition check.
for name in ['CAL3_MACHINE_ROOM_SHELLS','CAL3_MACHINE_ROOM_ROOFS','CAL3_RETAINED_MACHINE_ROOM_BLOCKS']:
 c=bpy.data.collections.get(name)
 if c and not c.objects and not c.children:bpy.data.collections.remove(c)
for o in sc.objects:
 if o.type=='MESH' and o.name.startswith('COMP_') and '_MACHINE_ROOM_' in o.name:rows.append({'name':o.name,'vertices':[list(o.matrix_world@v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons]})
(out/'machine_room_existing_walls.json').write_text(json.dumps(rows));result={'existing_wall_shells':len(rows),'note':'Existing geometry already has full-height door gaps; preserve walls.'}
