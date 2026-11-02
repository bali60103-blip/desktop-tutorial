import bpy,os
sc=bpy.data.scenes['GONGZHONG_INTEGRATED_OPENINGS_0912_EST'];bpy.context.window.scene=sc
states=[]
def reveal_roofs(lc):
 if lc.collection.name=='GZ12_COMPLETION_REMOVABLE_ROOFS':states.append((lc,lc.exclude));lc.exclude=False
 for child in lc.children:reveal_roofs(child)
reveal_roofs(sc.view_layers[0].layer_collection);sc.view_layers[0].update()
try:
 import bpy,json,pathlib,math,collections
 from mathutils import Vector
 from mathutils.bvhtree import BVHTree
 out=(pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3');sc=bpy.data.scenes['GONGZHONG_INTEGRATED_OPENINGS_0912_EST'];bpy.context.window.scene=sc;sc.view_layers[0].update();dg=bpy.context.evaluated_depsgraph_get();vv=[];ff=[];owner=[];roof=[];retained=set(o.name for o in bpy.data.collections['CALIBRATION_RETAINED_CONFLICT_OBJECTS'].objects);roofs=set(o.name for o in bpy.data.collections['GZ12_COMPLETION_REMOVABLE_ROOFS'].objects)
 for o in sc.objects:
  if o.type!='MESH' or o.name in retained or any(c.name in ['BLOCK_RECESSED_FACADES','BLOCK_FACADE_ASSETS','CALIBRATION_UNRESOLVED_POSITIONS'] for c in o.users_collection):continue
  if not o.visible_get(view_layer=sc.view_layers[0]) and o.name not in roofs:continue
  # Restrict to geometry spanning the underground/surface envelope; tall-building upper faces irrelevant but kept if base nearby.
  bb=[o.matrix_world@Vector(v) for v in o.bound_box]
  if min(p.z for p in bb)>2.3 or max(p.z for p in bb)<-8:continue
  e=o.evaluated_get(dg);m=e.to_mesh();vs=[list(o.matrix_world@v.co) for v in m.vertices];fs=[list(p.vertices) for p in m.polygons];base=len(vv);vv.extend(vs);ff.extend([[i+base for i in f] for f in fs]);owner.extend([o.name]*len(fs))
  if o.name in roofs:roof.append({'name':o.name,'vertices':vs,'faces':fs})
  e.to_mesh_clear()
 bvh=BVHTree.FromPolygons(vv,ff,all_triangles=False);paths=json.load(open(out/'gongzhong_integrated_paths.json'));issues=[];samples=0
 for p in paths:
  a=Vector(p['a']);b=Vector(p['b']);direction=b-a;n=Vector((-direction.y,direction.x,0)).normalized();hits=[]
  for j in range(1,20):
   q=a.lerp(b,j/20)
   for side in [-.8,0,.8]:
    pos=q+n*(side*p['halfwidth']);pos.z+=.2;samples+=1;loc,normal,index,dist=bvh.ray_cast(pos,Vector((0,0,1)),p['height']-.2)
    if index is not None:hits.append({'fraction':j/20,'side':side,'object':owner[index],'estimated_vertical_clearance_m':dist+.2,'xy':list(pos)[:2]})
  if hits:issues.append({'path':p['id'],'hits':hits})
 r={'sampled_paths':len(paths),'samples':samples,'paths_with_obstructions':len(issues),'issues':issues,'method':'Upward rays from interpolated tread/ramp height+0.2m to assumed pedestrian2.0m/vehicle2.1m envelope; includes hidden cutaway roofs. Sampling only, not continuous clearance certification.'};(out/'gongzhong_integrated_headroom_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));(out/'gongzhong_integrated_evaluated_roofs.json').write_text(json.dumps(roof,ensure_ascii=False));result={'paths':len(paths),'samples':samples,'blocked_paths':len(issues),'objects':dict(collections.Counter(h['object'] for i in issues for h in i['hits']))}
finally:
 for lc,value in states:lc.exclude=value
 sc.view_layers[0].update()

bpy.context.window.scene=bpy.data.scenes["CIVIC_BLOCKS_FACADES_WORKING"]
