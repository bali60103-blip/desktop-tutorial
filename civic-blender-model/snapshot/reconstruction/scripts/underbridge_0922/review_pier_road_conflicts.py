"""Street-view review variant: omit two unverified supports from the U-turn opening.
The original supports remain in an excluded collection and other scenes. This is
a comparison, not a surveyed support relocation or structural validation.
"""
import bpy,json,os,datetime
scene=bpy.context.scene
root=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(bpy.data.filepath),'BEFORE_PIER_ROAD_REVIEW_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend'),copy=True)
audit=json.load(open(os.path.join(root,'pier_road_overlap_input.json')))
col=bpy.data.collections.get('UB_PIER_ROAD_CONFLICT_REVIEW')
if col is None:col=bpy.data.collections.new('UB_PIER_ROAD_CONFLICT_REVIEW');scene.collection.children.link(col)
for r in audit['piers']:
 if r['status']!='ROAD_OVERLAP_REVIEW':continue
 name='ROAD_CONFLICT_'+r['pier'];ob=col.objects.get(name)
 if ob is None:ob=bpy.data.objects.new(name,None);col.objects.link(ob)
 ob.location=(*r['xy'],.3);ob.empty_display_type='CIRCLE';ob.empty_display_size=1.6;ob.show_in_front=True
 ob['overlap_area_m2']=r['road_outside_median_m2'];ob['real_world_verified']=False
 ob['review_status']='Needs street-view matching; no automatic relocation'
sources=[
 {'pano':'PdYrpyY5JzRWty-6BTCaYw','date':'2025-05','heading':0,'observation':'Open U-turn passage ahead; columns on island to west of opening'},
 {'pano':'thep3S5iPBSW9exGL5CO_g','date':'2025-05','heading':90,'observation':'Paired columns inside landscaped island; U-turn opening beyond stone enclosure'}]
for v in sources:v['url']='https://www.google.com/maps/@?api=1&map_action=pano&pano='+v['pano']+'&heading='+str(v['heading'])+'&pitch=0'
# Rebuild only collection paths containing the disputed objects in the current scene.
targets={scene.objects[n] for n in ['UNVERIFIED_Pier_518','UNVERIFIED_Pier_519','UNVERIFIED_Pier_518_CAP_ESTIMATED'] if scene.objects.get(n)}
preserve=bpy.data.collections.get('UB_UTURN_DISPUTED_SUPPORTS_ORIGINAL')
if preserve is None:
 preserve=bpy.data.collections.new('UB_UTURN_DISPUTED_SUPPORTS_ORIGINAL');scene.collection.children.link(preserve)
 for o in targets:preserve.objects.link(o)
 memo={}
 def filtered(c):
  if c in memo:return memo[c]
  if not any(o in targets for o in c.all_objects):return c
  nc=bpy.data.collections.new(c.name+'_UTURN_REVIEW');memo[c]=nc
  nc.hide_render=c.hide_render;nc.hide_viewport=c.hide_viewport
  for o in c.objects:
   if o not in targets:nc.objects.link(o)
  for ch in c.children:nc.children.link(filtered(ch))
  return nc
 for c in list(scene.collection.children):
  if c==preserve:continue
  nc=filtered(c)
  if nc!=c:scene.collection.children.unlink(c);scene.collection.children.link(nc)
 for o in list(scene.collection.objects):
  if o in targets:scene.collection.objects.unlink(o)
 bpy.context.view_layer.update()
def exclude(lc):
 if lc.collection==preserve:lc.exclude=True
 for ch in lc.children:exclude(ch)
for vl in scene.view_layers:exclude(vl.layer_collection)
for n in ['UNVERIFIED_Pier_518','UNVERIFIED_Pier_519']:
 marker=col.objects.get('ROAD_CONFLICT_'+n)
 if marker:marker['review_status']='Original excluded in U-turn comparison; no replacement XY accepted'
audit['streetview_review']={'sources':sources,'comparison_excluded_supports':[o.name for o in targets],'decision':'Keep U-turn opening clear in comparison only; support correspondence and replacement positions unresolved','resolved_real_world_conflicts':0}
json.dump(audit,open(os.path.join(root,'pier_road_overlap_review.json'),'w'),ensure_ascii=False,indent=2)
t=bpy.data.texts.get('CIVIC_pier_road_overlap_review.json') or bpy.data.texts.new('CIVIC_pier_road_overlap_review.json')
t.clear();t.write(json.dumps(audit,ensure_ascii=False,indent=2))
scene['height_audit_requires_support_review']=True
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result={'marked':len(col.objects),'originals_excluded':[o.name for o in targets],'counts':audit['counts'],'real_world_resolved':0}
