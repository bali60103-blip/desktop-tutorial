"""Audit added underbridge masses. A closed mesh is not real-world completeness."""
import bpy,json,os
from collections import Counter
root=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922')
s=bpy.data.scenes['CIVIC_UNDERBRIDGE_MASSING_20260916'];rows=[]
for c in s.collection.children:
 if not c.name.startswith('UB_'):continue
 objs=[o for o in c.all_objects if o.type=='MESH'];bad=[]
 for o in objs:
  ec=Counter(tuple(sorted(e)) for f in o.data.polygons for e in f.edge_keys)
  if any(n!=2 for n in ec.values()):bad.append(o.name)
 rows.append({'collection':c.name,'mesh_count':len(objs),'non_closed_meshes':bad,'source_tagged':sum(bool(o.get('source_url') or o.get('source_pano')) for o in objs),'dimensions_verified':False})
r={'active_scene':s.name,'collections':rows,'total_meshes':sum(x['mesh_count'] for x in rows),'full_corridor_complete':False,'limits':['Geometry checks do not establish measured dimensions, real-world coverage or occluded inventory.','Comparison scene objects are not automatically adopted into working scene.']}
json.dump(r,open(os.path.join(root,'mass_topology_checkpoint.json'),'w'),ensure_ascii=False,indent=2)
result=r
