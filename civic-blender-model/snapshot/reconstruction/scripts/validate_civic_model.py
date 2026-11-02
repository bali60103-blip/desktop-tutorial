"""Read-only technical audit. Mesh edge counts do not assert real-world accuracy."""
import bpy,json,pathlib,math,collections,datetime
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/Validation');out.mkdir(exist_ok=True)
def visible_ids(sc):
 ids=set()
 def walk(lc,parent=True):
  enabled=parent and not lc.exclude and not lc.collection.hide_render
  if enabled:
   ids.update(o.name for o in lc.collection.objects if not o.hide_render)
  for child in lc.children:walk(child,enabled)
 walk(sc.view_layers[0].layer_collection);return ids
scene_ids={s.name:visible_ids(s) for s in bpy.data.scenes};main_ids=scene_ids['Scene'];mesh_users=collections.defaultdict(list)
for o in bpy.data.objects:
 if o.type=='MESH':mesh_users[o.data.name].append(o.name)
issues=[];totals=collections.Counter();main_issues=[]
for m in bpy.data.meshes:
 if m.name not in mesh_users:continue
 totals['used_mesh_datablocks']+=1;totals['vertices']+=len(m.vertices);totals['polygons']+=len(m.polygons);edges=collections.Counter();bad_faces=[];zero_area=0;nan=sum(not all(math.isfinite(x) for x in v.co) for v in m.vertices)
 for f in m.polygons:
  ix=list(f.vertices)
  if len(ix)!=len(set(ix)):bad_faces.append(f.index)
  if f.area<1e-10:zero_area+=1
  for a,b in zip(ix,ix[1:]+ix[:1]):edges[(min(a,b),max(a,b))]+=1
 boundary=sum(n==1 for n in edges.values());nonmanifold=sum(n>2 for n in edges.values());loose=sum(tuple(sorted(e.vertices)) not in edges for e in m.edges)
 if boundary or nonmanifold or bad_faces or zero_area or nan or loose:
  row={'mesh':m.name,'object_names':mesh_users[m.name],'boundary_edges':boundary,'edges_with_more_than_two_faces':nonmanifold,'repeated_index_faces':bad_faces[:20],'repeated_index_face_count':len(bad_faces),'zero_area_faces':zero_area,'nonfinite_vertices':nan,'loose_edges':loose,'main_render_objects':[n for n in mesh_users[m.name] if n in main_ids]};issues.append(row)
  if row['main_render_objects']:main_issues.append(row)
for s in bpy.data.scenes:
 for v in s.view_layers:v.update()
camera_groups=collections.defaultdict(list)
for o in bpy.data.objects:
 if o.type=='CAMERA':
  key=tuple(round(v,4) for row in o.matrix_world for v in row)+(o.data.type,round(o.data.lens,3),round(o.data.ortho_scale,3));camera_groups[str(key)].append(o.name)
route=bpy.data.collections.get('CIVIC_CAMERAS_200M_NORTH_SOUTH');stations=collections.defaultdict(list)
for o in route.objects:stations[float(o.get('chainage_m',-1))].append(o.get('direction'))
station_keys=sorted(stations);camera_check={'route_count':len(route.objects),'station_pairs':len(stations),'bad_direction_pairs':{str(k):v for k,v in stations.items() if sorted(v)!=['TRUE_NORTH','TRUE_SOUTH']},'regular_spacing_m':[round(b-a,4) for a,b in zip(station_keys,station_keys[1:])],'old_500m_count':sum(o.name.startswith('CIVIC500_') for o in bpy.data.objects),'duplicate_camera_views':[v for v in camera_groups.values() if len(v)>1],'parking_ramp_cameras':[o.name for o in bpy.data.objects if o.type=='CAMERA' and (o.name.startswith('RAMP_CAM_') or o.name.endswith('_B1_B2_CAMERA'))]}
report={'timestamp':datetime.datetime.now().isoformat(),'file':bpy.data.filepath,'totals':dict(totals),'mesh_issue_count':len(issues),'main_render_mesh_issue_count':len(main_issues),'mesh_issues':issues,'main_render_mesh_issues':main_issues,'camera_check':camera_check,'scene_visible_object_counts':{k:len(v) for k,v in scene_ids.items()},'viewport_clip_end':[a.spaces.active.clip_end for w in bpy.context.window_manager.windows for a in w.screen.areas if a.type=='VIEW_3D'],'interpretation':'Boundary edges and zero-area flags require review by object purpose. Source planes, curves converted to mesh and open cutaways are not automatically defects. No as-built, structural, collision-all-pairs, fire-egress or dimensional verification asserted.'};(out/'technical_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));result={k:v for k,v in report.items() if k not in ['mesh_issues','main_render_mesh_issues','camera_check']};result['camera_summary']={k:v for k,v in camera_check.items() if k!='regular_spacing_m'}
