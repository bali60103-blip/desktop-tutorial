"""Preserve original references and add operator XY markers for comparison."""
import bpy,json,pathlib,datetime
p=json.loads(pathlib.Path(PAYLOAD).read_text());root=pathlib.Path(ROOT);root.mkdir(parents=True,exist_ok=True);s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bpy.ops.wm.save_as_mainfile(filepath=str(root/('before_official_controls_'+s+'.blend')),copy=True)
name='B_OPERATOR_EXIT_COORDINATES__Z_UNKNOWN';old=bpy.data.collections.get(name)
if old:
 for o in list(old.objects):bpy.data.objects.remove(o,do_unlink=True)
 bpy.data.collections.remove(old)
c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c)
for r in p['controls']:
 o=bpy.data.objects.new('OFFICIAL_XY_'+r['name'],None);c.objects.link(o);o.location=(*r['live_xy'],0);o.empty_display_type='CIRCLE';o.empty_display_size=3;o.show_name=True;o.show_in_front=True;o['source']=r['source'];o['status']=r['status'];o['comparison']=json.dumps(r['osm_comparisons'],ensure_ascii=False)
 for m in r['osm_comparisons']:
  cu=bpy.data.curves.new('XY_DELTA_'+r['name'],'CURVE');cu.dimensions='3D';sp=cu.splines.new('POLY');sp.points.add(1)
  for v,q in zip(sp.points,[r['live_xy'],m['osm_live_xy']]):v.co=(*q,.8,1)
  ob=bpy.data.objects.new(cu.name,cu);c.objects.link(ob);ob.hide_render=True;ob['distance_m']=m['distance_m'];ob['status']='Source discrepancy vector, not correction direction'
bpy.ops.wm.save_as_mainfile(filepath=str(root/('B_operator_controls_'+s+'.blend')))
result={'file':bpy.data.filepath,'official_markers':len(p['controls']),'objects':len(c.objects),'flags':p['flags'],'previous_markers_preserved':True}
(root/'blender_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
