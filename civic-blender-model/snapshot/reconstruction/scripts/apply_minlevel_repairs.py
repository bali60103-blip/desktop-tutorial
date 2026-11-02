import os
import bpy,pathlib,json,math,collections
from mathutils import Vector
root=pathlib.Path(os.environ['CIVIC_MODEL_ROOT']);out=root/'CalibrationRound3';sc=bpy.context.scene
bpy.ops.wm.save_as_mainfile(filepath=str(out/'BEFORE_MINLEVEL_REPAIRS.blend'),copy=True)
ids=json.load(open(out/'minlevel_target_ids.json'));keep=bpy.data.collections.new('CAL3_RETAINED_MINLEVEL');sc.collection.children.link(keep)
for o in list(sc.objects):
 if o.get('osm_id') in ids and o.type=='MESH':
  keep.objects.link(o)
  for c in list(o.users_collection):
   if c!=keep:c.objects.unlink(o)
  o.name='BEFORE_MINLEVEL_'+o.name
sc.view_layers[0].layer_collection.children[keep.name].exclude=True
s=pathlib.Path('reconstruction/scripts/build_block_facades.py').read_text();s=s[s.index("mats=[bpy.data.materials[n]"):];s=s.replace("sc['facade_status']='All facade modules estimated; mapped building parts retained; full site completeness not verified'","sc['facade_status']='TNH photo-informed grid; other facades estimated; min_level corrections included'")
payload=json.load(open(out/'minlevel_payload.json'));start=0;end=len(payload);exec(compile(s,'<minlevel-build>','exec'))
for r in payload:
 o=bpy.data.objects.get('BLOCK_'+r['osm_id']+'_CORE')
 if o:o['base_z_m']=r['base_z_m'];o['calibration_status']='Source-tag vertical-range consistency; not surveyed elevation'
sc.view_layers[0].update();bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result={'updated':len(payload),'originals_preserved':len(keep.objects),'file':bpy.data.filepath};(out/'applied_minlevel.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
