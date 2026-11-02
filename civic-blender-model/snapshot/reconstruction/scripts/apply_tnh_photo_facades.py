import os
import bpy,pathlib,json,math,collections
from mathutils import Vector
root=pathlib.Path(os.environ['CIVIC_MODEL_ROOT']);out=root/'CalibrationRound3';sc=bpy.context.scene
assert sc.name=='CIVIC_BLOCKS_FACADES_WORKING'
if not (out/'BEFORE_ROUND3.blend').exists():bpy.ops.wm.save_as_mainfile(filepath=str(out/'BEFORE_ROUND3.blend'),copy=True)
ids=json.load(open(out/'tnh_target_ids.json'));keep=bpy.data.collections.new('CAL3_RETAINED_TNH_GENERIC');sc.collection.children.link(keep)
for o in list(sc.objects):
 if o.get('osm_id') in ids and o.type=='MESH':
  keep.objects.link(o)
  for c in list(o.users_collection):
   if c!=keep:c.objects.unlink(o)
  o.name='BEFORE_CAL3_'+o.name
sc.view_layers[0].layer_collection.children[keep.name].exclude=True
assets=bpy.data.collections.new('TNH_PHOTO_GRID_ASSETS');sc.collection.children.link(assets)
colors=[('TNH_GRID_CONCRETE',(.69,.68,.61,1)),('TNH_RECESSED_GLASS',(.095,.19,.24,1)),('TNH_DARK_FRAME',(.20,.22,.23,1))];mats=[]
for n,col in colors:
 m=bpy.data.materials.get(n) or bpy.data.materials.new(n);m.diffuse_color=col;mats.append(m)
for kind in range(6):
 vs=[];fs=[];mi=[]
 def box(x0,x1,y0,y1,z0,z1,mat):
  k=len(vs);vs.extend([(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]);fs.extend([[k+i for i in f] for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]]);mi.extend([mat]*6)
 if kind==4:box(-.5,.5,0,.64,-.5,.5,0)
 else:
  box(-.5,-.455,0,.64,-.5,.5,0);box(.455,.5,0,.64,-.5,.5,0)
  box(-.455,.455,0,.64,.435,.5,0)
  if kind!=3:box(-.455,.455,0,.64,-.5,-.435,0)
  box(-.455,.455,.555,.575,-.435,.435,1)
  box(-.455,.455,.48,.60,-.02,.01,2)
  for x in [-.23,0,.23]:box(x-.005,x+.005,.53,.59,-.435,.435,2)
  # Mid-storey exterior horizontal shade visible in published close-up; section dimensions estimated.
  if kind!=3:box(-.455,.455,-.05,.61,.16,.205,0)
 me=bpy.data.meshes.new('TNH_GRID_MODULE_'+str(kind));me.from_pydata(vs,[],fs);me.update()
 for m in mats:me.materials.append(m)
 for p,m in zip(me.polygons,mi):p.material_index=m
 ob=bpy.data.objects.new(str(kind).zfill(2)+'_TNH_PHOTO_GRID',me);assets.objects.link(ob);ob['status']='Photo-informed grid character; dimensions estimated'
ng=bpy.data.node_groups['CIVIC_RECESSED_FACADE_INSTANCES'].copy();ng.name='TNH_PHOTO_GRID_INSTANCES'
for n in ng.nodes:
 if n.bl_idname=='GeometryNodeCollectionInfo':n.inputs['Collection'].default_value=assets
sc.view_layers[0].update();sc.view_layers[0].layer_collection.children[assets.name].exclude=True
# Run only the reusable object construction portion; no scene initialization or original payload replacement.
s=pathlib.Path('reconstruction/scripts/build_block_facades.py').read_text();s=s[s.index("mats=[bpy.data.materials[n]"):];s=s.replace("bpy.data.node_groups['CIVIC_RECESSED_FACADE_INSTANCES']","ng");s=s.replace("sc['facade_status']='All facade modules estimated; mapped building parts retained; full site completeness not verified'","sc['tnh_facade_status']='Official-photo-informed grid; detailed measurements remain estimated'")
payload=json.load(open(out/'facade_payload.json'));start=0;end=len(payload)
exec(compile(s,'<build-tnh>','exec'))
for oid in ids:
 core=bpy.data.objects.get('BLOCK_'+oid+'_CORE')
 if core:
  core.data.materials.clear();core.data.materials.append(mats[0] if mats[0].name.startswith('TNH') else bpy.data.materials['TNH_GRID_CONCRETE']);core['photo_source']='https://www.taipeinewhorizon.com.tw/explore-venue';core['photo_dimensions_status']='Visual character observed; 4.5m bay,0.56m recess and3.3m floor intervals estimated'
sc.view_layers[0].update();bpy.ops.wm.save_as_mainfile(filepath=str(out/'CIVIC_PHOTO_CALIBRATION_20260911.blend'));result={'file':bpy.data.filepath,'tnh_records':len(ids),'facade_instances':sum(len(r['points']) for r in payload),'preserved_old_objects':len(keep.objects)};(out/'applied_tnh.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
