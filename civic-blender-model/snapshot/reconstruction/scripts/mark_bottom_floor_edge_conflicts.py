"""Retain two estimated core/footprint conflicts as non-rendering review markers."""
import bpy,json,os,pathlib
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3'
sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc
col=bpy.data.collections.get('REVIEW_BOTTOM_CORE_EDGES_0912')
if col is None:
 col=bpy.data.collections.new('REVIEW_BOTTOM_CORE_EDGES_0912');sc.collection.children.link(col)
r=json.load(open(out/'bottom_floor_support_check.json'));groups={}
for row in r['items']:
 for p in row['support_misses']:groups.setdefault(p['path'],{'floor':row['floor'],'samples':[]})['samples'].append(p)
for name,row in groups.items():
 o=bpy.data.objects.get('REVIEW_EDGE_'+name)
 if o is None:o=bpy.data.objects.new('REVIEW_EDGE_'+name,None);col.objects.link(o)
 floor=bpy.data.objects[row['floor']];z=max((floor.matrix_world@v.co).z for v in floor.data.vertices)
 pts=row['samples'];o.location=(sum(p['xy'][0] for p in pts)/len(pts),sum(p['xy'][1] for p in pts)/len(pts),z+.2)
 o.empty_display_type='SPHERE';o.empty_display_size=.5;o.show_in_front=True;o.hide_render=True
 o['status']='UNRESOLVED: estimated core crosses estimated parking footprint; survey/plan registration required'
 o['sample_count']=len(pts);o['options']='Align core within footprint after plan registration; compare footprint correction only with evidence'
 row['marker']=o.name
(out/'bottom_core_edge_conflicts.json').write_text(json.dumps(groups,ensure_ascii=False,indent=2))
sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/'CIVIC_UNDERGROUND_COMPLETION_20260912.blend'))
result={'marked_cores':len(groups),'missed_samples':r['support_misses'],'footprints_expanded':False}
