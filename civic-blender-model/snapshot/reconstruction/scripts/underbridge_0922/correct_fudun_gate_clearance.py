import bpy,math,json,os
from mathutils.bvhtree import BVHTree
root=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922')
o=bpy.data.objects['UB_FUDUN_CANOPY_LANDSCAPE_EST_GATE_UNIT_-2.15_EST']
from mathutils import Vector
target=Vector([3557.0150637817155,413.7477810223812,0.78])
center=sum((o.matrix_world@v.co for v in o.data.vertices),Vector())/len(o.data.vertices)
delta=o.matrix_world.inverted().to_3x3()@(target-center)
for v in o.data.vertices:v.co+=delta
o.data.update();o['wall_clearance_adjusted']=True
if 'surface_intersection' in o:del o['surface_intersection']
q=bpy.data.objects['COMP_ACCESS_復敦_1_WALL_-1']
def tree(p):return BVHTree.FromPolygons([p.matrix_world@v.co for v in p.data.vertices],[list(f.vertices) for f in p.data.polygons])
hit=bool(tree(o).overlap(tree(q)))
report={'gate_wall_intersection_after':hit,'shift_outward_m':.65,'dimensions_verified':False}
json.dump(report,open(os.path.join(root,'fudun_gate_clearance_report.json'),'w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result=report
