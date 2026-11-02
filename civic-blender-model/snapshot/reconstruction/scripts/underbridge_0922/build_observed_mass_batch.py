"""Build a dated Street View mass manifest without changing existing objects.
Manifest coordinates and dimensions are estimates, never survey measurements.
Usage in Blender: set MANIFEST to a JSON path before executing this file.
"""
import bpy,json,math,os,random
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from collections import Counter

assert bpy.context.scene.name=='CIVIC_UNDERBRIDGE_MASSING_20260916'
manifest=json.load(open(MANIFEST))
name=manifest['batch_name'];assert bpy.data.collections.get(name) is None,'Batch exists'
working=bpy.context.scene
coll=bpy.data.collections.new(name);working.collection.children.link(coll)
palette={'stone':(.50,.46,.38,1),'louvre':(.20,.23,.19,1),'roof':(.13,.25,.20,1),'soil':(.23,.20,.15,1),'rock':(.4,.39,.34,1),'shrub':(.12,.25,.07,1)}
mats={}
for k,col in palette.items():
 m=bpy.data.materials.get('UB_BATCH_'+k) or bpy.data.materials.new('UB_BATCH_'+k);m.use_nodes=True;m.diffuse_color=col
 m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=col;mats[k]=m
views={v['pano']:v for v in manifest['observations']}
created=[]
for item in manifest['masses']:
 cx,cy,cz=item['center'];w,d,h=item['size'];a=math.radians(item['angle']);kind=item['kind']
 if kind=='box':
  vs=[(x*w/2,y*d/2,z*h/2) for z in [-1,1] for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]]
  fs=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 elif kind=='hip':
  vs=[(-w/2,-d/2,0),(w/2,-d/2,0),(w/2,d/2,0),(-w/2,d/2,0),(-w*.23,0,h),(w*.23,0,h)]
  fs=[(3,2,1,0),(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)]
 elif kind=='rock':
  rng=random.Random(item['id']);vs=[]
  for z,scale in [(0,1),(h*.6,.85)]:
   for i in range(8):
    t=i*math.pi/4;f=rng.uniform(.8,1)
    vs.append((math.cos(t)*w*.5*scale*f,math.sin(t)*d*.5*scale*f,z))
  vs.append((w*.05,-d*.08,h));fs=[tuple(reversed(range(8)))]
  fs.extend((i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8))
  fs.extend((8+i,8+(i+1)%8,16) for i in range(8))
 else:raise ValueError(kind)
 vs=[(cx+x*math.cos(a)-y*math.sin(a),cy+x*math.sin(a)+y*math.cos(a),cz+z) for x,y,z in vs]
 nm=name+'_'+item['id']+'_EST';me=bpy.data.meshes.new(nm);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new(nm,me);coll.objects.link(ob);me.materials.append(mats[item['material']])
 view=views[item['pano']]
 source='https://www.google.com/maps/@'+str(view['lat'])+','+str(view['lon'])+',3a,75y,'+str(view.get('heading',100))+'h,90t/data=!3m4!1e1!3m2!1s'+view['pano']+'!2e0'
 for k,v in {'source_url':source,'imagery_date':view['date'],'segment':item['segment'],'dimensions_status':'estimated from visible proportions, not measured','xy_status':'estimated placement constrained by existing working median','height_status':'estimated ground-relative Z','review_required':True,'placement_note':item.get('placement_note','manual photo-proportion placement; not triangulated')}.items():ob[k]=v
 created.append(ob)
bpy.context.view_layer.update()
def bounds(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [tuple(min(v[i] for v in p) for i in range(3)),tuple(max(v[i] for v in p) for i in range(3))]
def bvh(o):
 return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons],all_triangles=False)
existing=[(o,bounds(o)) for o in working.objects if o.type=='MESH' and o not in created]
cache={};conflicts=[];candidates=[]
for ob in created:
 a,b=bounds(ob);tree=None
 for q,(lo,hi) in existing:
  if hi[2]<=.181:continue # Ground contact checked separately; not an obstruction.
  if all(min(b[i],hi[i])-max(a[i],lo[i])>.015 for i in range(3)):
   candidates.append([ob.name,q.name]);tree=tree or bvh(ob)
   if q.name not in cache:cache[q.name]=bvh(q)
   if tree.overlap(cache[q.name]):conflicts.append([ob.name,q.name]);ob['surface_intersection']=q.name
med=[o for o in working.objects if o.type=='MESH' and (o.name.startswith('CAL_GROUND_MEDIAN_WORKING') or o.get('original_preserved','').startswith('CAL_GROUND_MEDIAN_WORKING'))]
outside=[]
for ob in created:
 pts=[ob.data.vertices[i].co for i in range(min(4,len(ob.data.vertices)))];bad=0
 for v in pts:
  ok=False
  for m in med:
   inv=m.matrix_world.inverted()
   if m.ray_cast(inv@Vector((v.x,v.y,2)),inv.to_3x3()@Vector((0,0,-1)),distance=5)[0]:ok=True;break
  if not ok:bad+=1
 if bad:outside.append({'name':ob.name,'outside_samples':bad});ob['median_sample_issue']=bad
not_closed=[]
for ob in created:
 edges=Counter(tuple(sorted(e)) for p in ob.data.polygons for e in p.edge_keys)
 if any(n!=2 for n in edges.values()):not_closed.append(ob.name)
report={'batch':name,'object_count':len(created),'names':[o.name for o in created],'surface_intersections':conflicts,'aabb_candidates':candidates,'median_sample_issues':outside,'non_closed_meshes':not_closed,'dimensions_verified':False,'full_corridor_complete':False,'limits':['surface test does not prove volumetric containment or clearance','median checks are sampled against an estimated model','one-side views leave occluded objects unresolved']}
root=os.path.dirname(MANIFEST)
json.dump(report,open(os.path.join(root,name+'_report.json'),'w'),indent=2)
# Keep the exact manifest embedded for recovery even when temporary files disappear.
text=bpy.data.texts.new(name+'_MANIFEST.json');text.write(json.dumps(manifest,indent=2,ensure_ascii=False))
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result=report
