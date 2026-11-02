"""Widen assumed B1 cutout for detailed ramp walls, sample openings and cap/girder spaces.
ROOT supplied. The grid samples are internal model consistency, not structural validation.
"""
import bpy,bmesh,json,pathlib,math,datetime
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=pathlib.Path(ROOT);sc=bpy.context.scene;s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(root/('before_connection_check_'+s+'.blend')),copy=True)
center=Vector((1208.59026,726.42395,-3.75));angle=math.atan2(721.741783-731.106122,1288.333559-1128.846965);n=Vector((-math.sin(angle),math.cos(angle),0))
for side,sign in [('north',1),('south',-1)]:
 o=bpy.data.objects['B1_SLAB_'+side];o.dimensions.y=9.94;o.location=center+n*(7.03*sign);o['opening_width_m']=4.12
bpy.context.view_layer.update()
def tree(objects):
 vs=[];fs=[];deps=bpy.context.evaluated_depsgraph_get()
 for o in objects:
  if o.type!='MESH':continue
  e=o.evaluated_get(deps);me=e.to_mesh();off=len(vs);vs.extend([o.matrix_world@v.co for v in me.vertices]);fs.extend([[i+off for i in f.vertices] for f in me.polygons]);e.to_mesh_clear()
 return BVHTree.FromPolygons(vs,fs)
cover=tree([bpy.data.objects[name] for name in ['GROUND_ROADS_OFFICIAL_XY','GROUND_MEDIAN_WORKING_ESTIMATED','GROUND_DATUM_Z0_not_surveyed_terrain']]+[o for o in bpy.data.collections['WORKSHEET04_B_DEPTH__ASSUMED_PILOT_CELL'].objects if o.name.startswith('B1_SLAB')])
paths=json.loads((root/'ramp_paths.json').read_text());clearance=[]
for path in paths:
 vals=[]
 for index in range(4,len(path['samples'])-4,4):
  q=Vector(path['samples'][index]);hit,no,idx,d=cover.ray_cast(q+Vector((0,0,.02)),Vector((0,0,1)),12)
  if hit is not None:vals.append({'sample':index,'clearance_m':hit.z-q.z})
 clearance.append({'ramp':path['name'],'overhead_hits':len(vals),'minimum_sampled_clearance_m':min(v['clearance_m'] for v in vals) if vals else None,'samples':vals,'scope':'Vertical centerline only; excludes columns, beams, services and turning envelope'})
girders=tree(list(bpy.data.collections['06_Steel_girders_estimated'].objects));caps=[]
for o in bpy.data.collections['07_Piers_legacy_UNVERIFIED'].objects:
 if '_CAP_' not in o.name or o.hide_render:continue
 pts=[o.matrix_world@Vector(v) for v in o.bound_box];lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)];hits=[]
 for ix in range(5):
  for iy in range(21):
   x=lo[0]+(hi[0]-lo[0])*(ix+.5)/5;y=lo[1]+(hi[1]-lo[1])*(iy+.5)/21;hit,no,idx,d=girders.ray_cast(Vector((x,y,hi[2]-.1)),Vector((0,0,1)),4)
   if hit is not None:hits.append(hit.z-hi[2])
 caps.append({'cap':o.name,'grid_hits':len(hits),'minimum_gap_m':min(hits) if hits else None,'maximum_gap_m':max(hits) if hits else None})
# Entrance detail in an independent review scene, using actual modified ground objects.
scene=bpy.data.scenes.new('RAMP_ENTRANCE_DETAIL_REVIEW')
for name in ['GROUND_FULL_01_OFFICIAL_AND_ESTIMATED','GROUND_FULL_02_CROSSINGS_AND_RAMPS_ESTIMATED','WORKSHEET04_B_DEPTH__ASSUMED_PILOT_CELL','WORKSHEET04_RAMP_DETAIL_ASSUMED']:scene.collection.children.link(bpy.data.collections[name])
camd=bpy.data.cameras.new('RAMP_ENTRY_CAMERA');cam=bpy.data.objects.new(camd.name,camd);scene.collection.objects.link(cam);scene.camera=cam;cam.location=(1255,690,27);cam.rotation_euler=(Vector((1265,723,-2))-cam.location).to_track_quat('-Z','Y').to_euler();camd.type='ORTHO';camd.ortho_scale=60;scene.world=sc.world;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True;scene.render.resolution_x=1700;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.render.filepath=str(root/'ramp_entry_detail.png');bpy.ops.render.render(write_still=True,scene=scene.name)
bpy.context.window.scene=sc;bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result={'file':bpy.data.filepath,'B1_opening_width_m':4.12,'clearance_checks':clearance,'cap_grid_samples':caps,'cap_grid_hit_count':sum(x['grid_hits']>0 for x in caps),'camera_count':len(bpy.data.collections['CIVIC_CAMERAS_500M_NORTH_SOUTH'].objects),'limitations':'Model probes only. Missing roof gives no clearance certification; grid does not establish bearing locations.'};(root/'connection_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));result={k:v for k,v in result.items() if k not in ['cap_grid_samples','clearance_checks']}
