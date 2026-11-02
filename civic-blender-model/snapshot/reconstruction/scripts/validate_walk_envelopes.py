"""Read-only sampled walking envelopes; assumptions, not accessibility certification."""
import bpy,json,math,pathlib,collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934'); out=root/'Validation'
def tree_for(scene):
 vs=[];fs=[];names=[];included=[]
 for o in scene.objects:
  if o.type!='MESH' or o.hide_viewport:continue
  # Physical glazing/roofs hidden for cutaway rendering must remain obstacles.
  off=len(vs);vs.extend(o.matrix_world@v.co for v in o.data.vertices)
  fs.extend([[off+i for i in f.vertices] for f in o.data.polygons]);names.extend([o.name]*len(o.data.polygons));included.append(o.name)
 return BVHTree.FromPolygons(vs,fs),names,included
checks=[]
def audit(label,path,scene):
 tree,names,included=tree_for(scene);hits=[];unsupported=[];rays=0
 for j,(x,y,z) in enumerate(path):
  for k in range(9):
   dx=dy=0
   if k:dx=.30*math.cos((k-1)*math.tau/8);dy=.30*math.sin((k-1)*math.tau/8)
   # 20cm foot exclusion tolerates adjacent 15cm stair rise under body footprint.
   hit,normal,idx,dist=tree.ray_cast(Vector((x+dx,y+dy,z+.20)),Vector((0,0,1)),1.60);rays+=1
   if hit is not None:hits.append({'sample':j,'object':names[idx],'hit_xyz':list(hit),'kind':'vertical'})
  for h in [.45,.9,1.35,1.75]:
   for k in range(4):
    d=Vector((math.cos(k*math.pi/4),math.sin(k*math.pi/4),0));a=Vector((x,y,z+h))-d*.30
    hit,normal,idx,dist=tree.ray_cast(a,d,.60);rays+=1
    if hit is not None:hits.append({'sample':j,'object':names[idx],'hit_xyz':list(hit),'kind':'body_cross_section'})
  hit,normal,idx,dist=tree.ray_cast(Vector((x,y,z+.05)),Vector((0,0,-1)),.10)
  if hit is None:unsupported.append(j)
 counts=dict(collections.Counter(h['object'] for h in hits))
 checks.append({'label':label,'scene':scene.name,'samples':len(path),'obstacle_rays':rays,'physical_meshes':len(included),'collision_hits':len(hits),'hit_objects':counts,'hit_examples':hits[:30],'unsupported_center_samples':unsupported})
entries=json.load(open(root/'YMallEntrances/source/y_entrance_payload.json'))['entries'];sc=bpy.data.scenes['Y_MALL_ENTRANCE_COMPARISON']
# Cache BVH per scene.
original_tree_for=tree_for;cache={}
def tree_for(scene):
 if scene.name not in cache:cache[scene.name]=original_tree_for(scene)
 return cache[scene.name]
for e in entries:
 if not e['built']:continue
 a=Vector(e['live_xy']);d=(Vector(e['lower_landing_xy'])-a).normalized();path=[]
 for j in range(24):
  q=a+d*(j*.3+.15);path.append((q.x,q.y,-j*.15))
 # Include lower flight mouth and continuing branch into mall.
 end=max(7.8,(Vector(e['lower_landing_xy'])-a).length)
 for j in range(math.ceil((end-7.2)/.2)):
  q=a+d*(7.25+j*.2);path.append((q.x,q.y,-3.6))
 audit(e['ref'],path,sc)
# Y26 B uses rotated photo staircase, offset towards walking lane (local y=-1).
o=bpy.data.objects['Y26_REMOVABLE_ROOF_AXIS_ALT'];a=Vector((121.83073261286829,926.8633642997104));ang=math.radians(164.5862136259);d=Vector((math.cos(ang),math.sin(ang)));n=Vector((-d.y,d.x));path=[]
for j in range(28):
 q=a+d*(j*.3+.15)-n;path.append((q.x,q.y,.6-j*.15))
p=json.load(open(root/'Y26Orientation/integrated_payload.json'))
for aa,bb in zip(p['walk_path_xy'],p['walk_path_xy'][1:]):
 aa=Vector(aa);bb=Vector(bb);steps=max(1,math.ceil((bb-aa).length/.2))
 for j in range(steps+1):
  q=aa.lerp(bb,j/steps);path.append((q.x,q.y,-3.6))
audit('Y26_B_INTEGRATED',path,bpy.data.scenes['Y26_B_INTEGRATED_COMPARISON'])
issues=[]
for name in ['GROUND_ROADS_OFFICIAL_XY','Buildings_context__OSM_XY__HEIGHTS_UNVERIFIED']:
 o=bpy.data.objects[name];m=o.data;ec=collections.defaultdict(list)
 for p in m.polygons:
  for e in p.edge_keys:ec[tuple(sorted(e))].append(p.index)
 bad=[{'vertex_indices':list(e),'world_endpoints':[list(o.matrix_world@m.vertices[i].co) for i in e],'face_indices':f} for e,f in ec.items() if len(f)>2]
 zero=[{'face':p.index,'vertices':[list(o.matrix_world@m.vertices[i].co) for i in p.vertices]} for p in m.polygons if p.area<1e-10]
 issues.append({'object':name,'multi_face_edges':bad,'zero_area_faces':zero})
mods=[{'object':o.name,'modifier':m.name,'type':m.type,'render':m.show_render,'viewport':m.show_viewport} for o in bpy.data.objects for m in o.modifiers]
r={'file':bpy.data.filepath,'method':'Sampled 0.60m diameter, 1.80m high envelope; vertical rays exclude bottom 0.20m. Raw physical meshes including cutaway-hidden roofs/glazing, excluding archived hide_viewport meshes. Not continuous swept collision or regulatory validation. Floor support checked at center only.','checks':checks,'localized_mesh_issues':issues,'modifiers':mods}
(out/'walk_envelope_audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result={'checks':[{'label':c['label'],'samples':c['samples'],'collisions':c['collision_hits'],'objects':c['hit_objects'],'unsupported':len(c['unsupported_center_samples'])} for c in checks],'localized_mesh_issues':issues,'modifier_count':len(mods)}
