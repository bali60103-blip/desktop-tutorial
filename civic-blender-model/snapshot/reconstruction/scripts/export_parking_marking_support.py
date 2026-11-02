import bpy,json,os,pathlib
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;sc.view_layers[0].update()
rows=[]
for o in sc.objects:
 if o.type!='MESH' or not o.visible_get() or '_BAYLINE_' not in o.name:continue
 floorname=o.name.split('_BAYLINE_')[0]+'_FLOOR';floor=sc.objects.get(floorname)
 if floor is None:continue
 def geo(x):return {'name':x.name,'vertices':[list(x.matrix_world@v.co) for v in x.data.vertices],'faces':[list(p.vertices) for p in x.data.polygons]}
 rows.append({'marking':geo(o),'floor':floor.name})
floors={r['floor']:geo(sc.objects[r['floor']]) for r in rows}
(out/'parking_marking_support_inventory.json').write_text(json.dumps({'markings':rows,'floors':floors},ensure_ascii=False));result={'markings':len(rows),'floors':len(floors)}
