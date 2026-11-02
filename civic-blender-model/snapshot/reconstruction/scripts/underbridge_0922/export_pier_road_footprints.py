import bpy,os,json,re
from mathutils import Vector
root=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922')
scene=bpy.context.scene;dg=bpy.context.evaluated_depsgraph_get()
out={'piers':[],'roads':[],'medians':[]}
for o in scene.objects:
 if o.type!='MESH':continue
 group='piers' if re.fullmatch(r'UNVERIFIED_Pier_\d+',o.name) else 'roads' if o.name.startswith('CAL_GROUND_ROADS_OFFICIAL_XY') else 'medians' if o.name.startswith(('CAL_GROUND_MEDIAN_WORKING','UB_MEDIAN_0_WITH')) else None
 if group is None:continue
 e=o.evaluated_get(dg);m=e.to_mesh();verts=[e.matrix_world@v.co for v in m.vertices];faces=[]
 zmin=min(v.z for v in verts);zmax=max(v.z for v in verts)
 for p in m.polygons:
  vs=[verts[i] for i in p.vertices]
  if group=='piers' and not all(v.z<=zmin+.01 for v in vs):continue
  xy=[[float(v.x),float(v.y)] for v in vs]
  area=abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(xy,xy[1:]+xy[:1])))/2
  if area>1e-6:faces.append(xy)
 if not faces and group=='piers':faces=[[[float(v.x),float(v.y)] for v in verts if v.z<=zmin+.01]]
 out[group].append({'name':o.name,'faces':faces,'zmin':zmin,'zmax':zmax})
 e.to_mesh_clear()
json.dump(out,open(os.path.join(root,'pier_road_footprints.json'),'w'))
result={'counts':{k:len(v) for k,v in out.items()}}
