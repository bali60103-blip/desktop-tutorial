import bpy,json,os,pathlib,math,datetime,collections
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;r=json.load(open(out/'parking_opening_guards_payload.json'));name='PARKING_B1_OPENING_GUARDS_0912_EST';assert not bpy.data.collections.get(name),'Already built'
bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_OPENING_GUARDS_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True)
col=bpy.data.collections.new(name);sc.collection.children.link(col);mat=bpy.data.materials.get('PILOT_GUARDRAIL_YELLOW') or bpy.data.materials.new('PARKING_GUARD_YELLOW');mat.diffuse_color=(.95,.55,.06,1);report=[]
for row in r['items']:
 a,b=Vector(row['a']),Vector(row['b']);d=(b-a).normalized();n=Vector((-d.y,d.x,0));z=Vector((0,0,1));L=(b-a).length;vs=[];fs=[]
 def box(center,dx,dy,dz):
  k=len(vs)
  for x,y,h in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]:vs.append(center+d*x*dx/2+n*y*dy/2+z*h*dz/2-a)
  fs.extend([[k+i for i in f] for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]])
 count=math.ceil(L/row['post_spacing_max'])+1
 for i in range(count):
  p=a.lerp(b,i/(count-1));box(p+z*.55,.06,.06,1.1);box(p+z*.004,.10,.10,.008)
 for h in [.55,1.075]:box((a+b)/2+z*h,L,.05,.05)
 edges=collections.Counter(tuple(sorted((f[i],f[(i+1)%len(f)]))) for f in fs for i in range(len(f)));assert all(v==2 for v in edges.values())
 me=bpy.data.meshes.new('PARKING_OPENING_GUARD');me.from_pydata(vs,[],fs);me.materials.append(mat);me.update();o=bpy.data.objects.new('B1_EDGE_GUARD_'+row['section']+'_'+str(row['edge'])+'_'+str(row['part']),me);col.objects.link(o);o.location=a;o['status']='ESTIMATED B1 opening edge guard: not surveyed, not engineered crash protection';o['height_m']=1.1;o['source']='Existing estimated opening geometry; footprint support checked';report.append({'object':o.name,'posts':count,'length_m':L,'floor':row['floor'],'a':row['a'],'b':row['b']})
sc.view_layers[0].update();(out/'parking_opening_guards_report.json').write_text(json.dumps({'runs':len(report),'posts':sum(x['posts'] for x in report),'items':report,'scope':r['scope']},ensure_ascii=False,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(out/'CIVIC_UNDERGROUND_COMPLETION_20260912.blend'));result={'runs':len(report),'posts':sum(x['posts'] for x in report),'height_m':1.1}
