"""Seat generated rail posts on actual modeled stair tread surfaces."""
import bpy,json,pathlib,os,re,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=pathlib.Path(os.environ['CIVIC_MODEL_ROOT']);out=root/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];paths={p['id']:p for p in json.load(open(root/'Calibration/checked_paths.json'))};count=0;miss=[]
for o in bpy.data.collections['CAL3_PARKING_STAIR_HANDRAILS'].objects:
 key=o['source_path'];match=re.fullmatch(r'CORE_(.+)_(\d+)_B(\d+)_([AB])',key);section,core,level,flight=match.groups();prefix='COMP_'+section+'_CORE'+core+'_L'+level+'_'+flight;stairs=[s for s in sc.objects if s.type=='MESH' and re.fullmatch(re.escape(prefix)+r'\d+',s.name)];vs=[];fs=[]
 for s in stairs:
  off=len(vs);vs.extend([s.matrix_world@v.co for v in s.data.vertices]);fs.extend([[off+i for i in p.vertices] for p in s.data.polygons])
 tree=BVHTree.FromPolygons(vs,fs);p=paths[key];d=Vector(p['b'])-Vector(p['a']);nposts=max(2,math.ceil(Vector((d.x,d.y,0)).length)+1)
 local_misses=0
 for side in range(2):
  for j in range(nposts):
   base=(side*(1+nposts)+1+j)*20
   if j in [0,nposts-1] and not o.get('endposts_inset_006m',False):
    delta=d/Vector((d.x,d.y,0)).length*(.06 if j==0 else -.06)
    for k in range(20):o.data.vertices[base+k].co+=delta
   center=sum((o.matrix_world@o.data.vertices[base+k].co for k in range(10)),Vector())/10;hit,_,_,_=tree.ray_cast(center+Vector((0,0,.4)),Vector((0,0,-1)),1)
   if hit is None:local_misses+=1;miss.append({'object':o.name,'post':j,'side':side});continue
   for k in range(10):o.data.vertices[base+k].co.z=hit.z-o.location.z
   count+=1
 o.data.update();o['endposts_inset_006m']=True;o['posts_seated_on_modeled_treads']=local_misses==0
r={'posts_seated':count,'misses':miss,'note':'Posts seated on current estimated stair surfaces; base plates and real structural attachment not inferred.'};(out/'handrail_seating_check.json').write_text(json.dumps(r,indent=2));bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result=r
