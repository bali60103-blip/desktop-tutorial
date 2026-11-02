import bpy,json,os,pathlib,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;sc.view_layers[0].update();r=json.load(open(out/'parking_opening_guards_report.json'));checked=0;miss=[]
for row in r['items']:
 o=sc.objects[row['floor']];tree=BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons]);a,b=Vector(row['a']),Vector(row['b']);d=(b-a).normalized();n=Vector((-d.y,d.x,0))
 for i in range(row['posts']):
  p=a.lerp(b,i/(row['posts']-1))
  for dx,dy in [(0,0),(-.05,-.05),(-.05,.05),(.05,-.05),(.05,.05)]:
   q=p+d*dx+n*dy+Vector((0,0,.03));hit=tree.ray_cast(q,Vector((0,0,-1)),.06)[0];checked+=1
   if hit is None:miss.append({'object':row['object'],'post':i,'corner':[dx,dy]})
r={'sampled_baseplate_points':checked,'unsupported_points':miss,'scope':'Existing slab presence under post footplates, not anchorage or structural verification'};(out/'parking_opening_guards_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result={'samples':checked,'unsupported':len(miss)}
