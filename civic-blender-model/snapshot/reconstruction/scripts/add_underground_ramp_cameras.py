"""One inspection camera per currently modeled underground ramp; preserve existing rigs."""
import bpy,json,pathlib,datetime
from mathutils import Vector
root=pathlib.Path(ROOT);root.mkdir(exist_ok=True);sc=bpy.context.scene;stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(root/('before_ramp_cameras_'+stamp+'.blend')),copy=True)
paths=json.loads((root.parent/'RampDetail/ramp_paths.json').read_text());name='UNDERGROUND_RAMP_CAMERAS';col=bpy.data.collections.get(name)
if col:
 for o in list(col.objects):bpy.data.objects.remove(o,do_unlink=True)
 bpy.data.collections.remove(col)
col=bpy.data.collections.new(name);sc.collection.children.link(col)
for m in list(sc.timeline_markers):
 if m.name.startswith('RAMP_CAM_'):sc.timeline_markers.remove(m)
old=(sc.camera,sc.frame_current,sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage,sc.render.filepath);rows=[]
labels={'EAST_0_TO_B1_ASSUMED':'EAST_1F_B1','WEST_0_TO_B1_ASSUMED':'WEST_1F_B1','B1_TO_B2_TEST_RAMP':'B1_B2'}
# Allocate beyond existing camera markers, leaving every prior marker intact.
first=max(101,max((m.frame for m in sc.timeline_markers),default=0)+1)
try:
 for i,p in enumerate(paths):
  pts=[Vector(q) for q in p['samples']];a=pts[min(4,len(pts)-1)];target=pts[len(pts)//2]+Vector((0,0,.6));name='RAMP_CAM_'+labels[p['name']];d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);col.objects.link(o);o.location=a+Vector((0,0,2.2));direction=target-o.location;o.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();d.lens=24;d.sensor_width=36;d.clip_start=.1;d.clip_end=2000;d.display_size=.8;o['ramp']=p['name'];o['height_above_ramp_m']=2.2;o['purpose']='Blender inspection camera looking downhill; not a real installed CCTV device';frame=first+i;m=sc.timeline_markers.new(name,frame=frame);m.camera=o
  sc.frame_set(frame);sc.camera=o;sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.render.resolution_percentage=100;sc.render.filepath=str(root/(name+'.png'));bpy.ops.render.render(write_still=True)
  rows.append({'camera':name,'ramp':p['name'],'frame':frame,'location':list(o.location),'target':list(target),'lens_mm':24,'height_above_ramp_m':2.2,'render':sc.render.filepath})
finally:
 sc.frame_set(old[1]);sc.camera=old[0];sc.render.resolution_x=old[2];sc.render.resolution_y=old[3];sc.render.resolution_percentage=old[4];sc.render.filepath=old[5]
file=root/('CIVIC_RAMP_CAMERAS_'+stamp+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));result={'file':str(file),'added_cameras':len(rows),'cameras':rows,'existing_500m_cameras':len(bpy.data.collections['CIVIC_CAMERAS_500M_NORTH_SOUTH'].objects),'scope':'Three currently modeled ramps only; other parking ramps not yet reconstructed.'};(root/'camera_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
