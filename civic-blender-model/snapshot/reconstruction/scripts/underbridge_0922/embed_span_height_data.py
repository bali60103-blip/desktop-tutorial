"""Embed model span audit tables and visible height labels in the working blend."""
import bpy,os,json,datetime
scene=bpy.context.scene
assert scene.name=='CIVIC_UNDERBRIDGE_MASSING_20260916'
root=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922')
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(bpy.data.filepath),'BEFORE_HEIGHT_DATA_EMBED_'+stamp+'.blend'),copy=True)
for filename in ['span_height_audit.json','span_station_heights.csv','span_height_notes.md','span_height_coverage_gaps.json']:
 text=bpy.data.texts.get('CIVIC_'+filename) or bpy.data.texts.new('CIVIC_'+filename)
 text.clear();text.write(open(os.path.join(root,filename),encoding='utf-8-sig').read());text.use_fake_user=True
audit=json.load(open(os.path.join(root,'span_height_audit.json')))
col=bpy.data.collections.get('UB_SPAN_HEIGHT_LABELS')
if col is None:
 col=bpy.data.collections.new('UB_SPAN_HEIGHT_LABELS');scene.collection.children.link(col)
area=next((a for a in bpy.context.screen.areas if a.type=='VIEW_3D'),None)
rotation=area.spaces.active.region_3d.view_rotation.copy() if area else None
for r in audit['spans']:
 name=r['span_id']+'_HEIGHT_LABEL'
 ob=col.objects.get(name)
 if ob is None:
  cu=bpy.data.curves.new(name,'FONT');ob=bpy.data.objects.new(name,cu);col.objects.link(ob)
 h=r['sampled_min_clearance_m']
 ob.data.body=r['span_id']+'\nMODEL sampled min '+(f'{h:.2f} m' if h is not None else 'NO GROUND DATA')+'\nNOT FIELD VERIFIED'
 ob.data.size=.65;ob.data.align_x='CENTER'
 ob.location=(*r['samples'][5]['xy'],11.)
 if rotation:ob.rotation_mode='QUATERNION';ob.rotation_quaternion=rotation
 ob.show_in_front=True;ob.hide_render=True;ob['real_world_verified']=False
for name in ['UB_SPAN_HEIGHT_MODEL_AUDIT','UB_SPAN_HEIGHT_COVERAGE_GAPS','UB_SPAN_HEIGHT_LABELS']:
 c=bpy.data.collections[name];c.hide_viewport=False
 for o in c.objects:
  o.hide_viewport=False;o.hide_set(False);o.show_in_front=True
 def reveal(lc):
  if lc.collection==c:lc.exclude=False;lc.hide_viewport=False;return True
  hit=False
  for child in lc.children:hit=reveal(child) or hit
  if hit:lc.exclude=False;lc.hide_viewport=False
  return hit
 reveal(bpy.context.view_layer.layer_collection)
scene['span_height_audit_basis']='MODEL ONLY; real-world elevations remain unverified'
scene['span_height_data_text']='CIVIC_span_height_audit.json'
if area:
 area.spaces.active.overlay.show_overlays=True
 for o in bpy.context.selected_objects:o.select_set(False)
 sample=scene.objects.get('SPAN_MODEL_000_MODEL_MIDSPAN_LINE')
 if sample:
  sample.select_set(True);bpy.context.view_layer.objects.active=sample
  region=next((r for r in area.regions if r.type=='WINDOW'),None)
  if region:
   with bpy.context.temp_override(area=area,region=region):
    bpy.ops.view3d.view_selected(use_all_regions=False)
   area.spaces.active.region_3d.view_distance=max(35.,area.spaces.active.region_3d.view_distance)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result={'labels':len(col.objects),'embedded_texts':[t.name for t in bpy.data.texts if t.name.startswith('CIVIC_span_')],'saved':os.path.basename(bpy.data.filepath),'active_object':bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None}
