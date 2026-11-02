"""Extend the Jianfu photo-side retaining wall to below-grade level in working scene only."""
import bpy,os,json
scene=bpy.data.scenes['CIVIC_UNDERBRIDGE_MASSING_20260916']
original=bpy.data.objects['COMP_ACCESS_建復_0_WALL_-1']
replacement=bpy.data.objects['UB_JIANFU_WALL_FENCE_EST_RAMP_WALL_UPPER_EST']
assert original.name in scene.objects
# Existing upper-box bottom was Z=.9; continue down to the deepest existing ramp level.
for v in replacement.data.vertices:
 if v.co.z<1.0:v.co.z=-3.85
replacement.data.update()
replacement['height_status']='estimated continuous retaining wall from -3.85 to +2.20m, not surveyed'
replacement['original_preserved']=original.name
def contains(c):return original.name in c.all_objects
def clone_branch(c):
 copy=bpy.data.collections.new(c.name+'_JIANFU_LOCAL')
 for ob in c.objects:copy.objects.link(replacement if ob==original else ob)
 for child in c.children:copy.children.link(clone_branch(child) if contains(child) else child)
 return copy
branches=[]
for c in list(scene.collection.children):
 if contains(c):
  new=clone_branch(c);scene.collection.children.link(new);scene.collection.children.unlink(c);branches.append([c.name,new.name])
if original.name in scene.collection.objects:scene.collection.objects.unlink(original)
# Review scene also swaps original for the new continuous wall.
review=bpy.data.scenes.get('UB_JIANFU_WALL_FENCE_REVIEW')
if review and original.name in review.collection.objects:review.collection.objects.unlink(original)
assert original.name not in scene.objects
report={'old_wall_in_working':False,'old_wall_preserved':original.users>0,'replacement':replacement.name,'estimated_top':2.2,'estimated_bottom':-3.85,'cloned_branches':branches,'dimensions_verified':False,'note':'Continuous comparison retaining wall; below-grade flat bottom remains a simplification'}
root=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922')
json.dump(report,open(os.path.join(root,'jianfu_continuous_wall_report.json'),'w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result=report
