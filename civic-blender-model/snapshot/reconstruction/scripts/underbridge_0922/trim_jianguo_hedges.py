"""Cut local estimated hedge strips around existing estimated piers. Originals stay intact."""
import bpy,json,os
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from collections import Counter
s=bpy.context.scene;c=bpy.data.collections['UB_JIANGUO_WEST_023_025_EST']
hedges=[o for o in c.objects if '_HEDGE_' in o.name]
piers=[o for o in s.objects if o.type=='MESH' and o.name.startswith('UNVERIFIED_Pier_') and 'CAP' not in o.name]
def bounds(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]
cuts=[]
for ob in hedges:
 lo,hi=bounds(ob)
 for p in piers:
  a,b=bounds(p)
  if not all(min(hi[i],b[i]+.35)>max(lo[i],a[i]-.35) for i in [0,1]):continue
  x0,y0=a[0]-.35,a[1]-.35;x1,y1=b[0]+.35,b[1]+.35
  verts=[(x,y,z) for z in [-1,2] for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]]
  me=bpy.data.meshes.new('UB_TEMP_HEDGE_CUT');me.from_pydata(verts,[],[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);me.update()
  cut=bpy.data.objects.new('UB_TEMP_HEDGE_CUT',me);s.collection.objects.link(cut)
  m=ob.modifiers.new('Pier_clearance_estimate','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cut;bpy.context.view_layer.update()
  with bpy.context.temp_override(object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):bpy.ops.object.modifier_apply(modifier=m.name)
  bpy.data.objects.remove(cut,do_unlink=True);cuts.append([ob.name,p.name])
 ob['clearance_status']='cut around existing estimated pier bounds with .35m margin; not verified actual clearance'
 if 'surface_intersection' in ob:del ob['surface_intersection']
def tree(o):return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons])
left=[]
for h in hedges:
 t=tree(h)
 for p in piers:
  a,b=bounds(p);lo,hi=bounds(h)
  if all(min(hi[i],b[i])>max(lo[i],a[i]) for i in range(3)) and t.overlap(tree(p)):left.append([h.name,p.name])
closed=[]
for o in hedges:
 ec=Counter(tuple(sorted(e)) for p in o.data.polygons for e in p.edge_keys)
 closed.append({'name':o.name,'nonmanifold_edges':sum(v!=2 for v in ec.values())})
report={'cuts':cuts,'remaining_hedge_pier_intersections':left,'mesh_checks':closed,'median_base_pier_contact':'Expected model ground contact, not removed','dimensions_verified':False}
root=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922')
json.dump(report,open(os.path.join(root,'jianguo_hedge_clearance_report.json'),'w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result=report
