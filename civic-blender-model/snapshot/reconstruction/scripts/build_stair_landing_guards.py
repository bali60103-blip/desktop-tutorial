import bpy,json,pathlib,os,math
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';root=out.parent;sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];paths={p['id']:p for p in json.load(open(root/'Calibration/checked_paths.json'))};col=bpy.data.collections.new('CAL3_PARKING_LANDING_GUARDS');sc.collection.children.link(col);mat=bpy.data.materials['CAL3_HANDRAIL_STEEL_EST'];report=[]
for key,p in paths.items():
 if not key.startswith('CORE_') or not key.endswith('_LANDING'):continue
 prefix=key.removesuffix('_LANDING');pa=paths[prefix+'_A'];pb=paths[prefix+'_B'];a=Vector(pa['a']);end=Vector(pa['b']);h=end-a;h.z=0;h.normalize();n=Vector((-h.y,h.x,0));origin=Vector(p['a']);z=origin.z
 start=end-n*(pa['halfwidth']+.07)+Vector((0,0,.9));finish=Vector(pb['a'])+n*(pb['halfwidth']+.07)+Vector((0,0,.9));_,section,core,level,_=key.split('_');landing=bpy.data.objects['COMP_'+section+'_CORE'+core+'_L'+level[1:]+'_LANDING'];outer=max((landing.matrix_world@v.co-end).dot(h) for v in landing.data.vertices)-.08;c=start+h*outer;c.z=z+.9;d=finish+h*outer;d.z=z+.9;vs=[];fs=[]
 def tube(a,b,r):
  direction=(b-a).normalized();u=direction.cross(Vector((0,0,1)))
  if u.length<.01:u=Vector((1,0,0))
  u.normalize();v=direction.cross(u).normalized();k=len(vs);N=10
  for q in [a,b]:
   for i in range(N):vs.append(tuple(q+r*(u*math.cos(i*math.tau/N)+v*math.sin(i*math.tau/N))-origin))
  fs.extend([tuple(k+i for i in reversed(range(N))),tuple(k+N+i for i in range(N))]);fs.extend([(k+i,k+(i+1)%N,k+(i+1)%N+N,k+i+N) for i in range(N)])
 for x,y in [(start,c),(c,d),(d,finish)]:tube(x,y,.035)
 for j in range(5):
  top=c.lerp(d,j/4);bottom=top.copy();bottom.z=z;tube(bottom,top,.025)
 m=bpy.data.meshes.new('GUARD_'+key);m.from_pydata(vs,[],fs);m.materials.append(mat);m.update();o=bpy.data.objects.new('GUARD_'+key,m);o.location=origin;col.objects.link(o);o['status']='Estimated exterior landing guard connecting outer flight rails. Opening between flights retained. Actual guard infill, loading and compliance unverified.';o['source_path']=key;o['guard_outer_edge_clearance_m']=.08;report.append({'object':o.name,'landing_path':key,'post_count':5})
 # Keep previously created public-core comparison in sync; copy objects without moving originals.
 if key.startswith('CORE_\u516c\u4e2d_0_'):
  compare=bpy.data.collections['CAL3_GONGZHONG_CORE_COMPARISON'];delta=Vector(json.load(open(out/'gongzhong_offset_comparison.json'))['first_mall_clear_candidate']['translation'])
  for label,shift,color in [('ORIGINAL',Vector(),(.85,.34,.1,1)),('OFFSET_5M',delta,(.12,.65,.42,1))]:
   clone=o.copy();clone.name='GZ_'+label+'_'+o.name;clone.location+=shift;clone.color=color;compare.objects.link(clone)
r={'landings':len(report),'guard_height_m':.9,'posts':len(report)*5,'status':'Estimated geometric detail, no claim of measured construction or code compliance','items':report};(out/'landing_guard_report.json').write_text(json.dumps(r,indent=2));review=bpy.data.scenes['GONGZHONG_CORE_OFFSET_COMPARISON'];bpy.ops.render.render(write_still=True,scene=review.name);bpy.context.window.scene=sc;sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result={k:v for k,v in r.items() if k!='items'}
