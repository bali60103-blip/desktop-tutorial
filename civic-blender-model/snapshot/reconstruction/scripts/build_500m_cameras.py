"""Blender: paired north/south cameras, scene timeline markers and source metadata.
ROOT supplied. Original active camera restored; review objects do not render.
"""
import bpy,json,pathlib,datetime
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=pathlib.Path(ROOT);p=json.loads((root/'camera_stations.json').read_text());sc=bpy.context.scene;s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');prior=sc.camera
bpy.ops.wm.save_as_mainfile(filepath=str(root/('before_cameras_'+s+'.blend')),copy=True)
name='CIVIC_CAMERAS_500M_NORTH_SOUTH';c=bpy.data.collections.get(name)
if c:
 for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
 bpy.data.collections.remove(c)
c=bpy.data.collections.new(name);sc.collection.children.link(c)
for m in list(sc.timeline_markers):
 if m.name.startswith('CIVIC500_'):sc.timeline_markers.remove(m)
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
  name=f"CIVIC500_{st['label']}_{side}";d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);c.objects.link(o);o.location=(x,y,z+1.7);direction=Vector((*st['true_north_live_unit'],0))*sign;o.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();d.lens=28;d.sensor_width=36;d.clip_start=.1;d.clip_end=15000;d.display_size=3
  o['chainage_m']=st['chainage_m'];o['section']=st['section'];o['direction']='TRUE_NORTH' if side=='N' else 'TRUE_SOUTH';o['coordinate_source']=p['method'];o['height_above_modeled_surface_m']=1.7;o['surface_hit']=hit is not None;o['lonlat']=json.dumps(st['lonlat']);o['source_surface_z_is_estimated']=True
  ph,pn,pi,pdist=piers.ray_cast(o.location,direction,30)
  frame=1+st['index']*2+(side=='S');m=sc.timeline_markers.new('CIVIC500_'+st['label']+'_'+side,frame=int(frame));m.camera=o
  rows.append({'camera':name,'chainage_m':st['chainage_m'],'section':st['section'],'position':list(o.location),'direction':list(direction),'timeline_frame':int(frame),'modeled_surface_hit':hit is not None,'pier_obstruction_within_30m':float(pdist) if ph is not None else None})
sc.camera=prior;sc['CIVIC500_USAGE']='Camera collection CIVIC_CAMERAS_500M_NORTH_SOUTH. Timeline camera markers frame1=N at0m, frame2=S at0m, then500m pairs. End station separately tagged. Analysis chainage only.'
file=root/('CIVIC_CAMERAS_500M_'+s+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));result={'file':str(file),'station_pairs':len(p['stations']),'camera_count':len(rows),'route_length_m':p['route_length_m'],'cameras':rows,'unresolved_pier_groups_retained':7};(root/'camera_build_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));result={k:v for k,v in result.items() if k!='cameras'}
