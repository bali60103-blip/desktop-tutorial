import bpy,json,os,pathlib,re
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;sc.view_layers[0].update();deepest={}
for o in sc.objects:
 match=re.fullmatch(r'COMP_(.+)_B(\d+)_FLOOR',o.name)
 if match:
  section,level=match.groups();level=int(level)
  if section not in deepest or level>deepest[section][0]:deepest[section]=(level,o)
paths=json.load(open(out.parent/'Calibration/checked_paths.json'));rows=[]
for section,(level,o) in deepest.items():
 rows.append({'section':section,'level':level,'object':o.name,'vertices':[list(o.matrix_world@v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'paths':[p for p in paths if p['id'].startswith('CORE_'+section+'_') and ('_B'+str(level)+'_') in p['id']]})
(out/'bottom_floor_opening_inventory.json').write_text(json.dumps(rows,ensure_ascii=False));result={'bottom_floors':[{'section':r['section'],'level':r['level'],'paths':len(r['paths'])} for r in rows]}
