"""Cut a photo-observed U-turn gap in a scene-local copy of the median.
The opening is observed, but its 23m working length and placement are estimated.
Other scenes keep the original collection and mesh.
"""
import bpy,math,json,os
from mathutils import Vector
from collections import Counter
scene=bpy.context.scene
assert scene.name=='CIVIC_UNDERBRIDGE_MASSING_20260916'
assert bpy.context.mode=='OBJECT'
original=bpy.data.objects['CAL_GROUND_MEDIAN_WORKING_ESTIMATED_0']
assert original.name in scene.objects
name='UB_MEDIAN_0_WITH_STATION_UTURN_EST'
assert bpy.data.objects.get(name) is None,'Correction exists'
ob=original.copy();ob.data=original.data.copy();ob.name=name;scene.collection.objects.link(ob)
cx,cy=854,780;a=math.radians(-10);w,d=23,70
v=[(cx+x*w/2*math.cos(a)-y*d/2*math.sin(a),cy+x*w/2*math.sin(a)+y*d/2*math.cos(a),z) for z in [-1,2] for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]]
me=bpy.data.meshes.new('UB_TEMP_GAP_CUTTER');me.from_pydata(v,[],[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);me.update()
cutter=bpy.data.objects.new('UB_TEMP_GAP_CUTTER',me);scene.collection.objects.link(cutter)
mod=ob.modifiers.new('Photo_observed_Uturn_estimate','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
bpy.context.view_layer.update()
with bpy.context.temp_override(object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(cutter,do_unlink=True)
def contains(c):return original.name in c.all_objects
def clone_branch(c):
 copy=bpy.data.collections.new(c.name+'_UB_LOCAL')
 for o in c.objects:copy.objects.link(ob if o==original else o)
 for child in c.children:copy.children.link(clone_branch(child) if contains(child) else child)
 return copy
replaced=[]
for c in list(scene.collection.children):
 if contains(c):
  new=clone_branch(c);scene.collection.children.link(new);scene.collection.children.unlink(c);replaced.append([c.name,new.name])
if original.name in scene.collection.objects:scene.collection.objects.unlink(original)
if replaced and ob.name in scene.collection.objects:scene.collection.objects.unlink(ob)
ob['source_url']='https://www.google.com/maps/@25.0483018,121.5187415,3a,75y,100h,90t/data=!3m4!1e1!3m2!1sPdYrpyY5JzRWty-6BTCaYw!2e0'
ob['source_date']='2025-05';ob['xy_status']='23m opening at local (854,780), angle -10deg estimated from ground panorama sequence'
ob['original_preserved']=original.name;ob['review_required']=True
bpy.context.view_layer.update()
edges=Counter(tuple(sorted(e)) for p in ob.data.polygons for e in p.edge_keys)
inv=ob.matrix_world.inverted();gap_hit=ob.ray_cast(inv@Vector((cx,cy,2)),inv.to_3x3()@Vector((0,0,-1)),distance=5)[0]
original_in_baseline=original.name in bpy.data.scenes['CIVIC_FULL_CORRIDOR_PRESENTATION'].objects
assert not gap_hit,'Opening was not cut'
assert original.name not in scene.objects,'Original median still visible in working scene'
report={'new_object':ob.name,'original_in_baseline':original_in_baseline,'original_in_working':original.name in scene.objects,'gap_center_still_hits':gap_hit,'nonmanifold_edge_count':sum(n!=2 for n in edges.values()),'scene_local_branches':replaced,'estimated_opening_length_m':23,'dimensions_verified':False,'remaining_issue':'legacy estimated piers near opening require separate street-view alignment'}
conflicts=[]
for oldname in ['UNVERIFIED_Pier_518','UNVERIFIED_Pier_519']:
 old=bpy.data.objects.get(oldname)
 if old and old.name in scene.objects:
  pts=[old.matrix_world@Vector(v) for v in old.bound_box];x=sum(p.x for p in pts)/8;y=sum(p.y for p in pts)/8
  mark=bpy.data.objects.new('REVIEW_UTURN_CONFLICT_'+oldname,None);scene.collection.objects.link(mark);mark.location=(x,y,.3);mark.empty_display_type='CIRCLE';mark.empty_display_size=2;mark.hide_render=True
  mark['issue']='Legacy estimated pier overlaps estimated street-view U-turn opening';mark['status']='unresolved; compare median-constrained relocation with real position'
  conflicts.append({'name':oldname,'xy':[x,y]})
report['conflicting_legacy_piers']=conflicts
root=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922');json.dump(report,open(os.path.join(root,'station_uturn_correction_report.json'),'w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result=report
