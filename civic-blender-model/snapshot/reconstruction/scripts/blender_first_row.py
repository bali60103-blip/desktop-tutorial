"""Blender QA outlines and explicit-height wireframes. No assumed floor conversion."""
import bpy,json,pathlib,datetime
p=json.loads(pathlib.Path(PAYLOAD).read_text());root=pathlib.Path(ROOT);root.mkdir(parents=True,exist_ok=True);s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bpy.ops.wm.save_as_mainfile(filepath=str(root/('before_buildings_'+s+'.blend')),copy=True)
name='STAGE05_ZHONGLIN_FRONTAGE_CANDIDATES'
old=bpy.data.collections.get(name)
if old:
 for ob in list(old.objects):bpy.data.objects.remove(ob,do_unlink=True)
 bpy.data.collections.remove(old)
c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c)
for r in p['buildings']:
 cu=bpy.data.curves.new('FRONTAGE_'+r['osm_id'],'CURVE');cu.dimensions='3D'
 def line(coords):
  sp=cu.splines.new('POLY');sp.points.add(len(coords)-1)
  for v,q in zip(sp.points,coords):v.co=(*q,1)
 for poly in r['rings']:
  for ring in [poly['outer']]+poly['holes']:
   line([(*q,.7) for q in ring])
   if r['height_m'] is not None:
    line([(*q,r['height_m']) for q in ring])
    for q in ring[:-1]:line([(*q,0),(*q,r['height_m'])])
 ob=bpy.data.objects.new(cu.name+('_'+r['name'] if r['name'] else ''),cu);c.objects.link(ob);ob.hide_render=True;ob.show_in_front=True
 ob['osm_id']=r['osm_id'];ob['height_status']=r['height_status'];ob['height_m']='UNKNOWN' if r['height_m'] is None else r['height_m'];ob['levels']=r['levels'] or 'UNKNOWN';ob['status']=r['status'];ob['base_elevation']='UNKNOWN; local Z=0 assumed solely for QA wireframe';ob['source_tags']=json.dumps(r['tags'],ensure_ascii=False)
c['scope']='Zhonglin pilot only';c['method']='Street-normal first-hit candidates; not certified frontage'
bpy.ops.wm.save_as_mainfile(filepath=str(root/('05_building_review_'+s+'.blend')))
result={'file':bpy.data.filepath,'candidate_objects':len(c.objects),'summary':p['summary'],'existing_buildings_changed':False}
(root/'blender_first_row_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
