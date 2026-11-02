"""Blender: paired north/south cameras, scene timeline markers and source metadata.
ROOT supplied. Original active camera restored; review objects do not render.
"""
import bpy,json,pathlib,datetime
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT='/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/Cameras_200m'
root=pathlib.Path(ROOT);p=json.loads((root/'camera_stations.json').read_text());sc=bpy.context.scene;s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');prior=sc.camera.name if sc.camera else None
bpy.ops.wm.save_as_mainfile(filepath=str(root/('before_cameras_'+s+'.blend')),copy=True)
# Preserve parking cameras and retain distinct review views. Remove replaced route cameras and unused camera objects.
protected={o.name:tuple(o.matrix_world[i][j] for i in range(4) for j in range(4)) for o in bpy.data.objects if o.type=='CAMERA' and (any('PARKING' in c.name or 'UNDERGROUND_RAMP_CAMERAS'==c.name for c in o.users_collection) or o.name=='RAMP_ENTRY_CAMERA')}
removed=[]
for o in list(bpy.data.objects):
 if o.type!='CAMERA' or o.name in protected:continue
 if o.name.startswith('CIVIC500_') or (not o.users_collection and not any(x.camera==o for x in bpy.data.scenes)):
  removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
for scene in bpy.data.scenes:
 for marker in list(scene.timeline_markers):
  if marker.name.startswith('CIVIC500_'):scene.timeline_markers.remove(marker)
old=bpy.data.collections.get('CIVIC_CAMERAS_500M_NORTH_SOUTH')
if old and not old.objects:bpy.data.collections.remove(old)
name='CIVIC_CAMERAS_200M_NORTH_SOUTH';c=bpy.data.collections.get(name)
if c:
 for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
 bpy.data.collections.remove(c)
c=bpy.data.collections.new(name);sc.collection.children.link(c)
for m in list(sc.timeline_markers):
 if m.name.startswith('CIVIC200_'):sc.timeline_markers.remove(m)
def bvh(objects):
 vs=[];fs=[]
 for o in objects:
  if o.type!='MESH':continue
  off=len(vs);vs.extend([o.matrix_world@v.co for v in o.data.vertices]);fs.extend([[i+off for i in f.vertices] for f in o.data.polygons])
 return BVHTree.FromPolygons(vs,fs,all_triangles=False)
surfaces=[bpy.data.objects[n] for n in ['GROUND_ROADS_OFFICIAL_XY','GROUND_ROADS_ESTIMATED_GAPS','GROUND_SIDEWALKS_WITH_ESTIMATED_RAMPS','GROUND_MEDIAN_WORKING_ESTIMATED']];ground=bvh(surfaces)
piers=bvh([o for o in bpy.data.collections['07_Piers_legacy_UNVERIFIED'].objects if not o.hide_render]);rows=[]
for st in p['stations']:
 x,y=st['live_xy'];hit,normal,idx,dist=ground.ray_cast(Vector((x,y,3)),Vector((0,0,-1)),10);z=hit.z if hit is not None else 0
 for side,sign in [('N',1),('S',-1)]:
  name=f"CIVIC200_{st['label']}_{side}";d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);c.objects.link(o);o.location=(x,y,z+1.7);direction=Vector((*st['true_north_live_unit'],0))*sign;o.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();d.lens=28;d.sensor_width=36;d.clip_start=.1;d.clip_end=12000;d.display_size=3
  o['chainage_m']=st['chainage_m'];o['section']=st['section'];o['direction']='TRUE_NORTH' if side=='N' else 'TRUE_SOUTH';o['coordinate_source']=p['method'];o['height_above_modeled_surface_m']=1.7;o['surface_hit']=hit is not None;o['lonlat']=json.dumps(st['lonlat']);o['source_surface_z_is_estimated']=True
  ph,pn,pi,pdist=piers.ray_cast(o.location,direction,30)
  frame=1001+st['index']*2+(side=='S');m=sc.timeline_markers.new('CIVIC200_'+st['label']+'_'+side,frame=int(frame));m.camera=o
  rows.append({'camera':name,'chainage_m':st['chainage_m'],'section':st['section'],'position':list(o.location),'direction':list(direction),'timeline_frame':int(frame),'modeled_surface_hit':hit is not None,'pier_obstruction_within_30m':float(pdist) if ph is not None else None})
sc.camera=bpy.data.objects.get(prior) if prior and prior in bpy.data.objects else c.objects[0];sc.frame_end=max(sc.frame_end,1106);sc['CIVIC200_USAGE']='Camera collection CIVIC_CAMERAS_200M_NORTH_SOUTH. Timeline camera markers frame1001=N at0m, frame1002=S at0m, then200m pairs. End station separately tagged. Analysis chainage only.'
assert all(n in bpy.data.objects and tuple(bpy.data.objects[n].matrix_world[i][j] for i in range(4) for j in range(4))==v for n,v in protected.items())
file=root/('CIVIC_CAMERAS_200M_'+s+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));result={'file':str(file),'station_pairs':len(p['stations']),'camera_count':len(rows),'route_length_m':p['route_length_m'],'cameras':rows,'unresolved_pier_groups_retained':7,'removed_camera_names':removed,'preserved_parking_camera_names':list(protected),'underground_mall_working_floor_z':-3.6,'underground_mall_working_clear_height':2.8,'mall_geometry_changed_by_this_script':False};(root/'camera_build_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));result={k:v for k,v in result.items() if k!='cameras'}
