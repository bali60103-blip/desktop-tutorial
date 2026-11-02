"""Account for supports and deck paths omitted by candidate-span grouping."""
import bpy,json,os
ROOT=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922')
a=json.load(open(os.path.join(ROOT,'span_height_audit.json')))
ctx=json.load(open(os.path.join(ROOT,'span_height_context.json')))
used={n for sp in a['spans'] for n in sp['start_piers']+sp['end_piers']}
covered={d for sp in a['spans'] for d in sp['decks']}
unused=[p for p in ctx['piers'] if p['name'] not in used]
missing=[p for p in ctx['paths'] if p['deck'] not in covered]
out={'piers_total':len(ctx['piers']),'piers_used_as_candidate_boundaries':len(used),'piers_not_in_any_candidate_span':[p['name'] for p in unused],'decks_without_candidate_spans':[p['deck'] for p in missing],'explanation':'Assignment to a deck does not mean a valid adjacent support pair exists. Unpaired paths may include ramps and branches. These have NOT been measured as spans.','full_height_verification_complete':False}
scene=bpy.data.scenes[ctx['scene']]
col=bpy.data.collections.get('UB_SPAN_HEIGHT_COVERAGE_GAPS')
if col is None:
 col=bpy.data.collections.new('UB_SPAN_HEIGHT_COVERAGE_GAPS');scene.collection.children.link(col)
for key,xy,kind in [('HEIGHT_UNPAIRED_'+p['name'],p['xy'],'unpaired_pier') for p in unused]+[('HEIGHT_UNMEASURED_'+p['deck'],p['points'][len(p['points'])//2],'deck_without_candidate_span') for p in missing]:
 ob=col.objects.get(key)
 if ob is None:ob=bpy.data.objects.new(key,None);col.objects.link(ob)
 ob.location=(*xy,10.);ob.empty_display_type='CIRCLE';ob.empty_display_size=3.
 ob['issue']=kind;ob['height_verified']=False;ob['measurement_status']='Missing adjacent-support measurement; review actual support mapping'
json.dump(out,open(os.path.join(ROOT,'span_height_coverage_gaps.json'),'w'),ensure_ascii=False,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result=out
