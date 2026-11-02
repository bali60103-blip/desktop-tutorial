"""Partial Street View masses at Zhengzhou Road; all dimensions/XY estimated.
Run in the existing CIVIC_UNDERBRIDGE_MASSING_20260916 scene.
This is not full corridor verification or an as-built survey.
"""
import bpy, math, json, os
from collections import Counter
from mathutils import Vector

SCENE = 'CIVIC_UNDERBRIDGE_MASSING_20260916'
COLLECTION = 'UB_ZHENGZHOU_002_003_PHOTO_EST'
assert bpy.context.scene.name == SCENE
assert not bpy.data.collections.get(COLLECTION), 'Already built; inspect rather than duplicate'
root = os.path.join(os.path.dirname(bpy.data.filepath), 'Underbridge_20260922')
os.makedirs(root, exist_ok=True)
coll = bpy.data.collections.new(COLLECTION)
bpy.context.scene.collection.children.link(coll)
made=[]
sources={
 '002':'https://www.google.com/maps/@25.0494753,121.5128275,3a,90y,20h,90t/data=!3m4!1e1!3m2!1srOneZw1Hy2btmcnrLp2cjQ!2e0',
 '003':'https://www.google.com/maps/@25.0494051,121.5138901,3a,90y,193h,90t/data=!3m4!1e1!3m2!1smoMq0z-UBTjiDjOudI-lmw!2e0'}
materials={}
for name,color in [('soil',(.23,.18,.12,1)),('shrub',(.15,.25,.08,1)),('curb',(.56,.54,.47,1)),('rock',(.37,.34,.29,1)),('wall',(.49,.43,.35,1))]:
 m=bpy.data.materials.get('UB_ZZ_'+name) or bpy.data.materials.new('UB_ZZ_'+name)
 m.diffuse_color=color; m.use_nodes=True
 m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=color
 materials[name]=m

def prism(name, poly, bottom, top, material, center, angle, segment):
 a=math.radians(angle);c,s=math.cos(a),math.sin(a)
 points=[(center[0]+x*c-y*s,center[1]+x*s+y*c) for x,y in poly]
 n=len(points);vs=[(x,y,z) for z in (bottom,top) for x,y in points]
 faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
 faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(vs,[],faces);mesh.update()
 o=bpy.data.objects.new(name,mesh);coll.objects.link(o);o.data.materials.append(materials[material])
 o['source_url']=sources[segment];o['evidence']='visible morphology; approximate working mass'
 o['xy_status']='estimated from panorama position and road direction; not triangulated'
 o['dimensions_status']='estimated, not measured';o['height_status']='estimated relative to ground Z=0'
 o['segment']='UB_X+'+segment;o['review_required']=True;made.append(o)
 return o

def rect(name,x,y,w,d,z0,z1,mat,center,angle,seg):
 return prism(name,[(x-w/2,y-d/2),(x+w/2,y-d/2),(x+w/2,y+d/2),(x-w/2,y+d/2)],z0,z1,mat,center,angle,seg)

# Small visible patches only. The ends are work boundaries, not surveyed island ends.
for seg,center,angle in [('002',(244,909),-20),('003',(349,878),-14)]:
 rect('UB_ZZ_'+seg+'_SOIL_PATCH_EST',0,0,18,3.6,0,.14,'soil',center,angle,seg)
 # Side curbs only; omit invented end caps across an unverified continuation.
 for y in [-1.9,1.9]:rect('UB_ZZ_'+seg+'_CURB_EST_'+str(y),0,y,18,.25,0,.28,'curb',center,angle,seg)
 for i,(x,y,w,d,h) in enumerate([(-6,.6,3,1.5,.48),(-1,-.5,3.8,1.8,.38),(5,.5,3.2,1.4,.52)]):
  poly=[(x-w/2,y-d*.25),(x-w*.3,y-d/2),(x+w*.35,y-d*.4),(x+w/2,y+d*.2),(x+w*.15,y+d/2),(x-w*.45,y+d*.4)]
  prism('UB_ZZ_'+seg+'_SHRUB_PATCH_EST_'+str(i),poly,.14,h,'shrub',center,angle,seg)
 if seg=='002':
  for i,(x,y,w,d,h) in enumerate([(-7,-.7,1.4,.9,.7),(-5,-.7,.9,.7,.5)]):
   poly=[(x-w*.5,y),(x-w*.25,y-d*.5),(x+w*.3,y-d*.4),(x+w*.5,y+d*.1),(x,y+d*.5)]
   prism('UB_ZZ_002_LANDSCAPE_ROCK_EST_'+str(i),poly,.14,h,'rock',center,angle,seg)

# The wall seen eastward from 002 and westward from 003 may be the same facility.
# One candidate prevents duplicating an unverified match. Function/top/depth unresolved.
o=rect('UB_ZZ_SHARED_LOW_ENCLOSURE_EST',0,0,8,3.0,0,1.6,'wall',(294,902),-20,'002')
o['alternate_view']=sources['003'];o['identity_status']='possible same enclosure in both views; unresolved'
o['function_status']='unknown; do not label confirmed ventilation or electrical equipment'

bpy.context.view_layer.update()
# Broad-phase collisions: conservatively catch all existing low-volume objects near additions.
def bounds(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box]
 return ([min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)])
existing=[(o,bounds(o)) for o in bpy.context.scene.objects if o.type=='MESH' and o not in made]
clashes=[]
for o in made:
 a,b=bounds(o)
 for q,(c,d) in existing:
  if c[2]<0 or d[2]>6:continue
  if all(min(b[i],d[i])-max(a[i],c[i])>.01 for i in range(3)):
   clashes.append([o.name,q.name]);o['aabb_conflict']=q.name
bad=[]
for o in made:
 edges=Counter(tuple(sorted(e)) for f in o.data.polygons for e in f.edge_keys)
 if any(n!=2 for n in edges.values()):bad.append(o.name)
report={'collection':COLLECTION,'objects':len(made),'names':[o.name for o in made],
 'non_closed_meshes':bad,'aabb_conflicts':clashes,'full_corridor_complete':False,
 'dimensions_verified':False,'coverage':'two local patches, not entire 100m strips',
 'open_issues':['island endpoints/widths unmeasured','wall identity and function unresolved','column guard placement still requires matching','subsurface containment not checked']}
with open(os.path.join(root,'zhengzhou_landscape_report.json'),'w') as f:json.dump(report,f,indent=2)
note_path=os.path.join(root,'west_streetview_notes.json')
notes=json.load(open(note_path))
for seg,pano,date,obs in [('002','rOneZw1Hy2btmcnrLp2cjQ','2024-12',['round column without visible base fence','irregular shrub patches','exposed soil','landscape rocks','low masonry enclosure']),('003','moMq0z-UBTjiDjOudI-lmw','2025-05',['round column with picket base guard','shrub median','drainage openings in curb','low masonry enclosure','bridge pipework','traffic signals'])]:
 if not any(v['pano']==pano for v in notes['views']):notes['views'].append({'segment':'UB_X+'+seg,'pano':pano,'date':date,'source_url':sources[seg],'status':'partial_ground_view','observed':obs,'dimensions_verified':False})
with open(note_path,'w') as f:json.dump(notes,f,indent=2,ensure_ascii=False)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result=report
