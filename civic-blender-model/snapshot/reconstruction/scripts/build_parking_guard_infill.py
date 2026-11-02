"""Estimated vertical pickets and post footplates; no surveyed detail or compliance claim."""
import bpy,json,os,pathlib,math,re
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;sc.view_layers[0].update();name='CAL3_PARKING_GUARD_INFILL';assert not bpy.data.collections.get(name),'Already built';col=bpy.data.collections.new(name);sc.collection.children.link(col);paths={p['id']:p for p in json.load(open(out.parent/'Calibration/checked_paths.json'))};mat=bpy.data.materials['CAL3_HANDRAIL_STEEL_EST'];report=[];miss=[]
for rail in list(bpy.data.collections['CAL3_PARKING_STAIR_HANDRAILS'].objects)+list(bpy.data.collections['CAL3_PARKING_LANDING_GUARDS'].objects):
 key=rail['source_path'];origin=rail.location.copy();vs=[];fs=[];seats=[];pickets=0;plates=0
 def tube(a,b,r=.012):
  k=len(vs);N=8
  for q in [a,b]:
   for i in range(N):vs.append(tuple(q+Vector((r*math.cos(i*math.tau/N),r*math.sin(i*math.tau/N),0))-origin))
  fs.extend([list(reversed(range(k,k+N))),list(range(k+N,k+2*N))]);fs.extend([[k+i,k+(i+1)%N,k+(i+1)%N+N,k+i+N] for i in range(N)])
 def plate(q,h,n):
  k=len(vs)
  for z in [0,.008]:
   for x,y in [(-.05,-.05),(.05,-.05),(.05,.05),(-.05,.05)]:vs.append(tuple(q+h*x+n*y+Vector((0,0,z))-origin))
  fs.extend([[k+i for i in f] for f in [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]])
 if key.endswith('_LANDING'):
  p=paths[key];a=Vector(p['a']);b=Vector(p['b']);h=(b-a).normalized();n=Vector((-h.y,h.x,0));c=sum((rail.matrix_world@rail.data.vertices[i].co for i in range(10,20)),Vector())/10;d=sum((rail.matrix_world@rail.data.vertices[i].co for i in range(30,40)),Vector())/10;posts=[]
  for j in range(5):
   q=sum((rail.matrix_world@rail.data.vertices[60+j*20+i].co for i in range(10)),Vector())/10;posts.append(q);plate(q,h,n);plates+=1
  count=math.ceil((d-c).length/.14)
  for j in range(1,count):
   top=c.lerp(d,j/count);bottom=top.copy();bottom.z=a.z
   if min((bottom-q).length for q in posts)<.065:continue
   tube(bottom,top);seats.append(list(bottom));pickets+=1
 else:
  p=paths[key];a=Vector(p['a']);b=Vector(p['b']);d=b-a;h=Vector((d.x,d.y,0)).normalized();n=Vector((-h.y,h.x,0));nposts=max(2,math.ceil(Vector((d.x,d.y,0)).length)+1);section,core,level,flight=re.fullmatch(r'CORE_(.+)_(\d+)_B(\d+)_([AB])',key).groups();prefix='COMP_'+section+'_CORE'+core+'_L'+level+'_'+flight;verts=[];faces=[]
  for s in sc.objects:
   if s.type!='MESH' or not re.fullmatch(re.escape(prefix)+r'\d+',s.name):continue
   base=len(verts);verts.extend(s.matrix_world@v.co for v in s.data.vertices);faces.extend([[base+i for i in p.vertices] for p in s.data.polygons])
  tree=BVHTree.FromPolygons(verts,faces)
  for sideidx,side in enumerate([-1,1]):
   posts=[]
   for j in range(nposts):
    k=(sideidx*(1+nposts)+1+j)*20;q=sum((rail.matrix_world@rail.data.vertices[k+i].co for i in range(10)),Vector())/10;posts.append(q);plate(q,h,n);plates+=1
   count=math.ceil(Vector((d.x,d.y,0)).length/.14)
   for j in range(1,count):
    q=a.lerp(b,j/count)+n*(side*(p['halfwidth']+.07));top=q+Vector((0,0,.9))
    if min(Vector((q.x-t.x,q.y-t.y,0)).length for t in posts)<.065:continue
    hit,_,_,_=tree.ray_cast(top,Vector((0,0,-1)),1.3)
    if hit is None:miss.append({'path':key,'fraction':j/count,'side':side});continue
    tube(hit,top);seats.append(list(hit));pickets+=1
 m=bpy.data.meshes.new('INFILL_'+key);m.from_pydata(vs,[],fs);m.materials.append(mat);m.update();edges={}
 for f in m.polygons:
  for e in f.edge_keys:edges[e]=edges.get(e,0)+1
 assert all(v==2 for v in edges.values()),key
 o=bpy.data.objects.new(m.name,m);o.location=origin;col.objects.link(o);o['source_path']=key;o['status']='ESTIMATED vertical guard pickets and 100mm post plates. Sizes, infill arrangement and fixings unverified; does not resolve blocked paths.';report.append({'object':o.name,'path':key,'pickets':pickets,'plates':plates,'seats':seats})
# Full integrated estimate scene shares unshifted detail, isolates relocated public core.
integrated=bpy.data.scenes['GONGZHONG_INTEGRATED_OPENINGS_EST'];icol=col.copy();icol.name='GZI_'+name;integrated.collection.children.link(icol);offset=Vector(json.load(open(out/'gongzhong_integrated_model.json'))['translation']);compare=bpy.data.collections['CAL3_GONGZHONG_CORE_COMPARISON']
for o in list(col.objects):
 if not o['source_path'].startswith('CORE_公中_0_'):continue
 clone=o.copy();clone.name='GZI_'+o.name;clone.location+=offset;icol.objects.unlink(o);icol.objects.link(clone)
 for label,shift,color in [('ORIGINAL',Vector(),(.85,.34,.1,1)),('OFFSET_5M',offset,(.12,.65,.42,1))]:
  clone=o.copy();clone.name='GZ_'+label+'_'+o.name;clone.location+=shift;clone.color=color;compare.objects.link(clone)
r={'objects':len(report),'pickets':sum(x['pickets'] for x in report),'footplates':sum(x['plates'] for x in report),'seating_misses':miss,'assumptions':{'picket_diameter_m':.024,'maximum_nominal_spacing_m':.14,'footplate_m':[.1,.1,.008]},'scope':'Model detail only. Retained wider gaps at existing support posts not a code assessment; real construction and fastening not verified.','items':report};(out/'guard_infill_report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result={k:v for k,v in r.items() if k!='items'}
