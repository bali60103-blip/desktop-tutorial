"""Bind existing road cameras to one-second timeline cuts, east to west, N then S."""
import bpy,pathlib,os,json,re,datetime
root=pathlib.Path(os.environ['CIVIC_MODEL_ROOT']);out=root/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc
cams=[o for o in sc.objects if o.type=='CAMERA' and re.fullmatch(r'CIVIC200_(?:\d{2}K\d{3}|END)_[NS]',o.name)]
assert cams,'No road cameras found'
def station(o):
 label=o.name.split('_')[1]
 return float('inf') if label=='END' else int(label[:2])*1000+int(label[3:])
cams.sort(key=lambda o:(-station(o),o.name[-1]))
assert all(cams[i].matrix_world.translation.x>=cams[i+1].matrix_world.translation.x-.02 for i in range(len(cams)-1)),'Route order is not east-to-west; inspect registration'
assert len({o.name for o in cams})==len(cams)
assert not [m for m in sc.timeline_markers if m.camera and not m.name.startswith('EW_1SEC_')],'Existing camera cuts need preservation review'
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');snapshot=out/('BEFORE_CAMERA_ANIMATION_'+stamp+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(snapshot),copy=True)
old={'fps':sc.render.fps,'fps_base':sc.render.fps_base,'start':sc.frame_start,'end':sc.frame_end,'frame_current':sc.frame_current,'camera':sc.camera.name if sc.camera else None,'markers':[{'name':m.name,'frame':m.frame,'camera':m.camera.name if m.camera else None} for m in sc.timeline_markers]}
for m in list(sc.timeline_markers):
 if m.name.startswith('EW_1SEC_'):sc.timeline_markers.remove(m)
sc.render.fps=24;sc.render.fps_base=1.0;sc.frame_start=1;sc.frame_end=len(cams)*24;sc.frame_step=1;sc.use_preview_range=False;sc.sync_mode='FRAME_DROP'
rows=[]
for i,o in enumerate(cams):
 frame=1+i*24;m=sc.timeline_markers.new('EW_1SEC_%03d_%s'%(i+1,o.name.removeprefix('CIVIC200_')),frame=frame);m.camera=o;rows.append({'second':i,'start_frame':frame,'end_frame':frame+23,'camera':o.name,'x':o.matrix_world.translation.x,'y':o.matrix_world.translation.y})
sc.camera=cams[0];sc['camera_animation']='East to west, same station N then S, 1 second per existing road camera, 24fps. Parking cameras excluded.'
checks=[]
for f in [1,24,25,48,49,1+(len(cams)//2)*24,sc.frame_end]:
 sc.frame_set(f);expected=cams[(f-1)//24].name;actual=sc.camera.name if sc.camera else None;checks.append({'frame':f,'expected':expected,'actual':actual});assert actual==expected,(f,expected,actual)
sc.frame_set(1)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
r={'scene':sc.name,'fps':24,'camera_count':len(cams),'duration_seconds':len(cams),'start_frame':1,'end_frame':sc.frame_end,'order':'East to west; north-facing then south-facing at each station','excluded':'Parking and review cameras','backup_file':snapshot.name,'previous_timeline':old,'switch_checks':checks,'cuts':rows};(out/'camera_animation_east_west.json').write_text(json.dumps(r,indent=2));bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result={k:v for k,v in r.items() if k not in ['previous_timeline','cuts']}
