"""Estimated handrail detail on existing generated parking stair flights; no compliance claim."""
import bpy,json,pathlib,os,math,datetime
from mathutils import Vector
root=pathlib.Path(os.environ['CIVIC_MODEL_ROOT']);out=root/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc
assert not bpy.data.collections.get('CAL3_PARKING_STAIR_HANDRAILS'),'Already built'
bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_STAIR_DETAIL_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True)
paths=[p for p in json.load(open(root/'Calibration/checked_paths.json')) if p['id'].startswith('CORE_') and p['id'].endswith(('_A','_B'))];blocked={p['path'] for p in json.load(open(root/'CalibrationRound2/headroom_check.json'))['issues']};col=bpy.data.collections.new('CAL3_PARKING_STAIR_HANDRAILS');sc.collection.children.link(col);mat=bpy.data.materials.new('CAL3_HANDRAIL_STEEL_EST');mat.diffuse_color=(.5,.53,.56,1);report=[]
for p in paths:
 a=Vector(p['a']);b=Vector(p['b']);d=b-a;h=Vector((d.x,d.y,0)).normalized();n=Vector((-h.y,h.x,0));vs=[];fs=[];origin=a.copy()
 def tube(a,b,radius):
  direction=(b-a).normalized();axis=direction.cross(Vector((0,0,1)))
  if axis.length<.01:axis=Vector((1,0,0))
  axis.normalize();other=direction.cross(axis).normalized();start=len(vs);N=10
  for center in [a,b]:
   for i in range(N):vs.append(tuple(center+radius*(axis*math.cos(i*math.tau/N)+other*math.sin(i*math.tau/N))-origin))
  fs.extend([tuple(start+i for i in reversed(range(N))),tuple(start+N+i for i in range(N))]);fs.extend([(start+i,start+(i+1)%N,start+(i+1)%N+N,start+i+N) for i in range(N)])
 for side in [-1,1]:
  offset=n*(side*(p['halfwidth']+.07));ta=a+offset+Vector((0,0,.9));tb=b+offset+Vector((0,0,.9));tube(ta,tb,.035)
  count=max(2,math.ceil(Vector((d.x,d.y,0)).length/1.0)+1)
  for j in range(count):
   q=a.lerp(b,j/(count-1))+offset;tube(q,q+Vector((0,0,.9)),.025)
 m=bpy.data.meshes.new('RAIL_'+p['id']);m.from_pydata(vs,[],fs);m.materials.append(mat);m.update();o=bpy.data.objects.new('RAIL_'+p['id'],m);o.location=origin;col.objects.link(o);o['status']='Estimated handrail geometry; original stairs and 15 known path conflicts remain. Not measured or code certification.';o['source_path']=p['id'];o['height_assumed_m']=.9;o['existing_path_blocked']=p['id'] in blocked
 counts={}
 for f in m.polygons:
  for key in f.edge_keys:counts[key]=counts.get(key,0)+1
 assert all(v==2 for v in counts.values()),o.name
 report.append({'path':p['id'],'object':o.name,'known_obstructed_path':p['id'] in blocked,'vertices':len(vs)})
r={'flights_detailed':len(report),'handrails_per_flight':2,'assumed_height_m':.9,'rail_radius_m':.035,'post_radius_m':.025,'clear_width_preserved_m':'Existing path width; rail centers are 0.07m outside its edges','limitations':'Terminal extensions, landing continuity, substrate attachment, accessibility and real dimensions remain unverified. Blocked paths are not cleared by adding detail.','paths':report};(out/'stair_handrail_report.json').write_text(json.dumps(r,indent=2));bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result={k:v for k,v in r.items() if k!='paths'}
