import bpy,os,pathlib,json,math,collections
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;sc.view_layers[0].update();bad=[];checked=set();vertices=0;gn=0
for o in sc.objects:
 if not all(math.isfinite(x) for row in o.matrix_world for x in row):bad.append({'object':o.name,'issue':'nonfinite_transform'})
 if any(abs(x)<1e-9 for x in o.scale):bad.append({'object':o.name,'issue':'zero_scale'})
 for m in o.modifiers:
  if m.type=='NODES':
   gn+=1
   if m.node_group is None:bad.append({'object':o.name,'issue':'missing_geometry_node_group'})
 if o.type=='MESH' and o.data.as_pointer() not in checked:
  checked.add(o.data.as_pointer());vertices+=len(o.data.vertices)
  if any(not math.isfinite(c) for v in o.data.vertices for c in v.co):bad.append({'object':o.name,'issue':'nonfinite_mesh_vertex'})
markers=sorted((m for m in sc.timeline_markers if m.name.startswith('EW_1SEC_')),key=lambda m:m.frame);camera_issues=[];oldframe=sc.frame_current
for i,m in enumerate(markers):
 if m.frame!=1+24*i:camera_issues.append({'marker':m.name,'issue':'unexpected_frame'})
 if not m.camera or m.camera.get('direction')!='TOWARD_BOULEVARD_AXIS':camera_issues.append({'marker':m.name,'issue':'camera_direction_metadata'})
 if m.camera and (m.camera.data.clip_start<=0 or m.camera.data.clip_end<=m.camera.data.clip_start):camera_issues.append({'marker':m.name,'issue':'invalid_clipping'})
for m in markers[::25]+markers[-1:]:
 sc.frame_set(m.frame)
 if sc.camera!=m.camera:camera_issues.append({'marker':m.name,'issue':'binding_not_active'})
sc.frame_set(oldframe);missing=[]
for image in bpy.data.images:
 if image.source=='FILE' and not image.packed_file and image.filepath and not pathlib.Path(bpy.path.abspath(image.filepath)).is_file():missing.append(image.name)
for lib in bpy.data.libraries:
 if not pathlib.Path(bpy.path.abspath(lib.filepath)).is_file():missing.append(lib.name)
r={'main_scene':sc.name,'mesh_datablocks_checked':len(checked),'mesh_vertices_checked':vertices,'geometry_node_modifiers':gn,'geometry_issues':bad,'route_cameras':len(markers),'animation_duration_seconds':(sc.frame_end-sc.frame_start+1)/(sc.render.fps/sc.render.fps_base),'frame_range':[sc.frame_start,sc.frame_end],'camera_issues':camera_issues,'missing_external_assets':missing,'collection_counts':{c.name:len(c.objects) for c in sc.collection.children},'limits':'Finite geometry, available assets and animation bindings only. Does not validate all facade dimensions, continuous clearance, cadastral position or real-world appearance.'};(out/'integrated_asset_animation_audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result={k:v for k,v in r.items() if k!='collection_counts'}
