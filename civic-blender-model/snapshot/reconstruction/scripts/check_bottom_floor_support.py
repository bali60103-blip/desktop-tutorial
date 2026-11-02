import bpy,json,pathlib,os
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;sc.view_layers[0].update();rows=json.load(open(out/'bottom_floor_opening_inventory.json'));results=[]
for row in rows:
 o=bpy.data.objects[row['object']];vs=[o.matrix_world@v.co for v in o.data.vertices];z1=max(v.z for v in vs);tree=BVHTree.FromPolygons(vs,[list(p.vertices) for p in o.data.polygons]);miss=[];count=0
 for p in row['paths']:
  a,b=Vector(p['a']),Vector(p['b']);d=b-a;n=Vector((-d.y,d.x,0)).normalized()
  for j in range(1,10):
   for side in [-.8,0,.8]:
    q=a.lerp(b,j/10)+n*(side*p['halfwidth']);q.z=z1+.05;hit,_,_,_=tree.ray_cast(q,Vector((0,0,-1)),.1);count+=1
    if hit is None:miss.append({'path':p['id'],'fraction':j/10,'side':side,'xy':list(q)[:2]})
 results.append({'floor':o.name,'samples':count,'support_misses':miss})
r={'sampled_floors':len(results),'samples':sum(x['samples'] for x in results),'support_misses':sum(len(x['support_misses']) for x in results),'items':results,'limits':'Sampled vertical slab presence below current stair envelopes; not load capacity or foundation validation'};(out/'bottom_floor_support_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result={'floors':[{'floor':x['floor'],'samples':x['samples'],'misses':len(x['support_misses'])} for x in results]}
