"""Run inside Blender with CONTROL_PAYLOAD and REVIEW_ROOT provided by the caller.
Adds only plan-reference markers in a new version; does not construct underground floors.
"""
import bpy,json,pathlib,datetime
payload=json.loads(pathlib.Path(CONTROL_PAYLOAD).read_text());root=pathlib.Path(REVIEW_ROOT);root.mkdir(parents=True,exist_ok=True)
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');before=bpy.data.filepath
bpy.ops.wm.save_as_mainfile(filepath=str(root/('before_controls_'+stamp+'.blend')),copy=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/('02_control_review_'+stamp+'.blend')))
for old in list(bpy.data.collections):
    if old.name.startswith('STAGE02_PLAN_REFERENCES__NOT_SURVEYED'):
        for ob in list(old.objects):bpy.data.objects.remove(ob,do_unlink=True)
        bpy.data.collections.remove(old)
col=bpy.data.collections.new('STAGE02_PLAN_REFERENCES__NOT_SURVEYED');bpy.context.scene.collection.children.link(col)
for r in payload['routes']:
    cu=bpy.data.curves.new('REF_'+str(r['id']),'CURVE');cu.dimensions='3D';sp=cu.splines.new('POLY');sp.points.add(len(r['xy'])-1)
    for v,p in zip(sp.points,r['xy']):v.co=(p[0],p[1],.4,1)
    ob=bpy.data.objects.new('REF_'+r['name']+'_'+str(r['id']),cu);col.objects.link(ob);ob.hide_render=True;ob['status']=r['status'];ob['display_z_not_elevation']=.4
for p in payload['controls']:
    ob=bpy.data.objects.new('ENTRANCE_'+p['ref']+'_'+str(p['id']),None);col.objects.link(ob);ob.location=(*p['xy'],0);ob.empty_display_type='CIRCLE';ob.empty_display_size=4;ob.show_name=True;ob.show_in_front=True
    for k,v in p.items():
        if k=='id':v=str(v)  # OSM ids can exceed Blender's signed integer custom-property range.
        ob[k]=json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else ('UNKNOWN' if v is None else v)
    ob['display_z_not_elevation']=0
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.overlay.show_extras=True
bpy.context.scene['GATE_A']='Accepted by user; full corridor scope, elevated and station/mall junction first'
bpy.context.scene['GATE_B']='NOT PASSED: map references only; underground source plans and elevations unregistered'
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result={'file':bpy.data.filepath,'previous_file':before,'reference_routes':len(payload['routes']),'entrance_markers':len(payload['controls']),'underground_geometry_added':False}
(root/'blender_control_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
