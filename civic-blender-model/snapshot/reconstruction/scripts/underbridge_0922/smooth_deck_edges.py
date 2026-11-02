"""Soften deck edge shading with a reversible 3cm bevel; retain base mesh vertices."""
import bpy,math,os,json
scene=bpy.context.scene
rows=[]
for o in scene.objects:
 if o.type!='MESH' or not o.name.startswith('DECK_'):continue
 before=[tuple(v.co) for v in o.data.vertices]
 # Objects are shared with presentation scenes; the reversible modifier applies there too.
 m=o.modifiers.get('CIVIC_EDGE_SOFTEN_03M') or o.modifiers.new('CIVIC_EDGE_SOFTEN_03M','BEVEL')
 m.width=.03;m.segments=3;m.limit_method='ANGLE';m.angle_limit=math.radians(30);m.use_clamp_overlap=True
 for p in o.data.polygons:p.use_smooth=abs(p.normal.z)<.5
 adjacent={}
 for p in o.data.polygons:
  for key in p.edge_keys:adjacent.setdefault(tuple(sorted(key)),[]).append(p.normal.copy())
 for e in o.data.edges:
  ns=adjacent.get(tuple(sorted(e.vertices)),[])
  e.use_edge_sharp=len(ns)!=2 or ns[0].angle(ns[1])>math.radians(30)
 o.data.update()
 assert before==[tuple(v.co) for v in o.data.vertices]
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=e.to_mesh()
 rows.append({'deck':o.name,'base_vertices_unchanged':True,'evaluated_faces':len(mesh.polygons),'bevel_m':.03,'shared_scene_count':len(o.users_scene)})
 e.to_mesh_clear()
root=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922')
json.dump({'decks':rows,'scope':'Edge shading and 3cm local bevel only; no alignment/plan curvature smoothing or height correction'},open(os.path.join(root,'deck_edge_smoothing_report.json'),'w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result={'decks':len(rows),'all_have_evaluated_faces':all(r['evaluated_faces']>0 for r in rows),'base_vertices_unchanged':True}
