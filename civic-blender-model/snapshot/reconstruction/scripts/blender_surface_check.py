"""Run inside Blender with PAYLOAD and ROOT; non-destructive QA overlay."""
import bpy,json,pathlib,datetime
p=json.loads(pathlib.Path(PAYLOAD).read_text());root=pathlib.Path(ROOT);root.mkdir(parents=True,exist_ok=True);s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bpy.ops.wm.save_as_mainfile(filepath=str(root/('before_surface_'+s+'.blend')),copy=True)
name='STAGE04_ZHONGLIN_GROUND_QA'
old=bpy.data.collections.get(name)
if old:
 for ob in list(old.objects):bpy.data.objects.remove(ob,do_unlink=True)
 bpy.data.collections.remove(old)
c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c)
for ft in p['sidewalks']:
 cu=bpy.data.curves.new('OFFICIAL_SIDEWALK_'+str(ft['source_index']),'CURVE');cu.dimensions='3D'
 for ring in ft['rings']:
  sp=cu.splines.new('POLY');sp.points.add(len(ring)-1)
  for v,q in zip(sp.points,ring):v.co=(*q,.6,1)
 ob=bpy.data.objects.new(cu.name,cu);c.objects.link(ob);ob.hide_render=True;ob.show_in_front=True;ob['status']='Official XY outline; clipped to review extent; Z=.6 for display only'
for q in p['crossings']:
 ob=bpy.data.objects.new('CROSSING_REF_'+q['name'],None);c.objects.link(ob);ob.location=(*q['live_xy'],0);ob.empty_display_type='CIRCLE';ob.empty_display_size=3;ob.show_name=True;ob.show_in_front=True;ob['status']=q['status']
c['stairs']='1 north west block; 2 south west block; 3 and 4 south east block; exact XY unresolved'
bpy.ops.wm.save_as_mainfile(filepath=str(root/('04_surface_review_'+s+'.blend')))
result={'file':bpy.data.filepath,'qa_objects':len(c.objects),'stairs_added':0,'underground_geometry_added':False}
(root/'blender_surface_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
