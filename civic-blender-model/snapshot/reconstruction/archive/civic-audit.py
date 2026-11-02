import bpy,json,pathlib,math
from mathutils import Vector
P=pathlib.Path('/tmp/civic-rebuild');root=pathlib.Path((P/'output_root.txt').read_text());scene=bpy.context.scene
# Keep hypothetical cap crossbeams within their mapped carriageway rather than centered on an old offset pier.
reg=json.loads((P/'registration.json').read_text());origin=[reg['origin_epsg3826'][i]+reg['live_to_twd97']['translation'][i] for i in range(2)]
segments=[]
for w in json.loads((P/'osm.json').read_text())['ways']:
 if w['tags'].get('highway')=='trunk' and '市民大道高架' in w['tags'].get('name',''):
  pts=[Vector((x-origin[0],y-origin[1])) for x,y in w['xy']]
  segments.extend(zip(pts,pts[1:]))
for o in bpy.data.collections['07_Piers_legacy_UNVERIFIED'].objects:
 if not o.name.endswith('_CAP_ESTIMATED'):continue
 c=sum((v.co for v in o.data.vertices),Vector())/len(o.data.vertices);p=Vector((c.x,c.y));best=None
 for a,b in segments:
  v=b-a;t=max(0,min(1,(p-a).dot(v)/max(v.length_squared,1e-8)));q=a+t*v;dist=(p-q).length
  if best is None or dist<best[0]:best=(dist,q)
 delta=best[1]-p
 for v in o.data.vertices:v.co.x+=delta.x;v.co.y+=delta.y
 o['confidence']='Hypothetical cap centered on nearest mapped carriageway; shaft remains unverified legacy XY'
for o in bpy.context.selected_objects:o.select_set(False)
bpy.context.view_layer.objects.active=None
for scr in bpy.data.screens:
 for a in scr.areas:
  if a.type=='VIEW_3D':
   s=a.spaces.active;s.region_3d.view_perspective='CAMERA';s.region_3d.view_camera_zoom=0;s.region_3d.view_camera_offset=(0,0);s.overlay.show_extras=False
counts={c.name:len(c.objects) for c in bpy.data.collections['CIVIC_REBUILD__METERS__SOURCE_TAGGED'].children}
objs=list(bpy.data.collections['CIVIC_REBUILD__METERS__SOURCE_TAGGED'].all_objects);bad=sum(1 for o in objs if o.type=='MESH' for v in o.data.vertices if not all(math.isfinite(t) for t in v.co))
result={'file':bpy.data.filepath,'units':'METRIC','scale_length':scene.unit_settings.scale_length,'collections':counts,'nonfinite_vertices':bad,'archive_hidden':bpy.data.collections['90_ORIGINAL_MODEL_ARCHIVE'].hide_viewport,'total_new_collection_objects':len(objs),'geometry_accuracy':'NOT survey verified; see source_manifest.json','verified_pier_count':0}
(root/'final_scene_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
# Export actual final GIS footprint references for supplemental layers separately.
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
