"""Run inside Blender with AUDIT_PATH and OUTPUT_DIR. Snapshot before changes.
Adds map references only, without inventing underground geometry or elevations.
"""
import bpy,json,pathlib,datetime
p=json.loads(pathlib.Path(AUDIT_PATH).read_text());root=pathlib.Path(OUTPUT_DIR);root.mkdir(parents=True,exist_ok=True)
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');prior=bpy.data.filepath
bpy.ops.wm.save_as_mainfile(filepath=str(root/('before_zhonglin_'+stamp+'.blend')),copy=True)
name='STAGE03_ZHONGLIN__XY_ONLY_Z_UNKNOWN'
old=bpy.data.collections.get(name)
if old:
 for ob in list(old.objects):bpy.data.objects.remove(ob,do_unlink=True)
 bpy.data.collections.remove(old)
c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c)
for e in p['entrances']:
 ob=bpy.data.objects.new('ZL_'+e['label']+'_OSM_CANDIDATE',None);c.objects.link(ob);ob.location=(*e['live_xy'],0);ob.empty_display_type='CIRCLE';ob.empty_display_size=3;ob.show_name=True;ob.show_in_front=True;ob['osm_id']=e['osm_id'];ob['elevation']='UNKNOWN; displayed at Z=0';ob['vehicle_height_limit_m']=1.8;ob['status']=e['status']
for r in p['routes']:
 cu=bpy.data.curves.new('ZL_ACCESS_'+r['osm_id'],'CURVE');cu.dimensions='3D';sp=cu.splines.new('POLY');sp.points.add(len(r['live_xy'])-1)
 for v,q in zip(sp.points,r['live_xy']):v.co=(*q,.5,1)
 ob=bpy.data.objects.new(cu.name,cu);c.objects.link(ob);ob.hide_render=True;ob.show_in_front=True;ob['status']=r['status'];ob['display_z_not_elevation']=.5
c['stairs_unlocated']=4;c['B1_floor_elevation']='UNKNOWN';c['B2_floor_elevation']='UNKNOWN';c['plan_scale']='UNREGISTERED'
bpy.context.scene['GATE_B']='NOT PASSED: Zhonglin access XY candidates added; stairs, plan scale, B1/B2 elevations unresolved'
bpy.ops.wm.save_as_mainfile(filepath=str(root/('03_zhonglin_review_'+stamp+'.blend')))
result={'file':bpy.data.filepath,'previous_file':prior,'reference_objects':len(c.objects),'underground_geometry_added':False}
(root/'blender_zhonglin_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
