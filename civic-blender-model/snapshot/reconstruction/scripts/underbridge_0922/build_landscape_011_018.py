"""Build photographed hedge ranges as estimated masses. Existing objects are preserved."""
import bpy,json,os,bmesh
from collections import Counter
ROOT=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922')
manifest=json.load(open(os.path.join(ROOT,'landscape_011_018_manifest.json')))
observations=json.load(open(os.path.join(ROOT,'full_corridor_observations.json')))['observations']
views={v['pano']:v for v in observations}
s=bpy.data.scenes['CIVIC_UNDERBRIDGE_MASSING_20260916']
name='UB_LANDSCAPE_011_018_EST'
assert bpy.data.collections.get(name) is None
c=bpy.data.collections.new(name);s.collection.children.link(c)
mat=bpy.data.materials.get('UB_BATCH_shrub')
closed=[]
for it in manifest['footprints']:
 assert not it['holes']
 p=it['outer'];n=len(p);z=it['base_z'];h=it['height']
 vs=[(x,y,zz) for zz in [z,z+h] for x,y in p]
 fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]
 fs += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 me=bpy.data.meshes.new(it['id']);me.from_pydata(vs,[],fs);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 ob=bpy.data.objects.new(name+'_'+it['id'],me);c.objects.link(ob)
 if mat:me.materials.append(mat)
 v=views[it['pano']]
 ob['source_url']='https://www.google.com/maps/@'+str(v['lat'])+','+str(v['lon'])+',3a,75y,100h,90t/data=!3m4!1e1!3m2!1s'+v['pano']+'!2e0'
 ob['imagery_date']=v['date'];ob['dimensions_status']='estimated, not measured';ob['xy_status']='estimated within existing median';ob['review_required']=True
 ob['clearance_status']='Footprint excludes existing sampled obstruction bounds with 0.45m buffer; not a surveyed clearance'
 edges=Counter(tuple(sorted(e)) for f in me.polygons for e in f.edge_keys)
 if all(k==2 for k in edges.values()):closed.append(ob.name)
report={'objects':len(c.objects),'closed_meshes':len(closed),'dimensions_verified':False,'full_corridor_complete':False,'scope':'Photographed hedge strips UB011-018; other objects and occluded space unresolved'}
json.dump(report,open(os.path.join(ROOT,'landscape_011_018_report.json'),'w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result=report
