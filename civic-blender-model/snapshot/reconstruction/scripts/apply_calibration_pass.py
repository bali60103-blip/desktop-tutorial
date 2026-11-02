"""Reversible source-semantic and model-consistency corrections. Not survey certification."""
import bpy,json,pathlib,math,time,collections
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Calibration';stamp=time.strftime('%Y%m%d_%H%M%S');sc=bpy.data.scenes['CIVIC_COMPLETE_WORKING_ASSEMBLY']
bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_CALIBRATION_'+stamp+'.blend')),copy=True)
report={'before_file':bpy.data.filepath,'ground':[],'removed_aboveground_entities':[],'camera_updates':[],'limitations':['Ground cuts follow provisional access paths, not measured openings.','Road route sampling fixes mapped-road consistency, not legal pedestrian placement.','No new absolute elevation datum established.']}
col=bpy.data.collections['COMPLETION_GROUND_HIGHWAY'];payload=json.load(open(out/'openings_payload.json'));oldobjects={r['replaces']:bpy.data.objects.get(r['replaces']) for r in payload['parts']}
for r in payload['parts']:
 if bpy.data.objects.get(r['name']):raise RuntimeError('Calibration already applied: '+r['name'])
 vs=r['mesh']['vertices'];org=Vector(vs[0]);m=bpy.data.meshes.new(r['name']);m.from_pydata([tuple(Vector(v)-org) for v in vs],[],r['mesh']['faces']);m.update();o=bpy.data.objects.new(r['name'],m);o.location=org;col.objects.link(o)
 old=oldobjects[r['replaces']]
 if old:
  for mat in old.data.materials:m.materials.append(mat)
 o['calibration_status']=r['status'];o['replaces']=r['replaces'];o['provenance']='Calibration/openings_payload.json'
for name,o in oldobjects.items():
 if o and o.name in col.objects:col.objects.unlink(o);report['ground'].append(name)
# Superseded small comparison ground patches remain in their source collections.
patch=bpy.data.collections.get('Y_GROUND_OPENINGS_COMPARISON');mall=bpy.data.collections.get('COMPLETION_MALLS')
if patch and mall:
 for o in list(patch.objects):
  if o.name in mall.objects and o.type=='MESH' and 'GROUND' in o.name:mall.objects.unlink(o)
front=bpy.data.collections['COMPLETION_FRONTAGE'];rows=json.load(open(root/'CompletionPass/source/first_row.json'))['buildings']
for r in rows:
 if r['tags'].get('location')!='underground':continue
 matches=[o for o in list(front.objects) if ('_'+r['osm_id']+'_') in o.name or str(o.get('osm_id',''))==r['osm_id']]
 for o in matches:
  front.objects.unlink(o);report['removed_aboveground_entities'].append({'object':o.name,'osm_id':r['osm_id'],'name':r['name'],'reason':'OSM location=underground; above-ground extrusion was a classification error'})
sc.view_layers[0].update();dg=bpy.context.evaluated_depsgraph_get();stations=json.load(open(out/'corrected_camera_stations.json'))['stations'];newground=[o for o in col.objects if o.name.startswith('CAL_GROUND_')]
for r in stations:
 x,y=r['live_xy'];z=0
 for o in newground:
  inv=o.matrix_world.inverted();hit,loc,n,idx=o.ray_cast(inv@Vector((x,y,2)),inv.to_3x3()@Vector((0,0,-1)),distance=3)
  if hit:z=max(z,(o.matrix_world@loc).z)
 for side,sign in [('N',1),('S',-1)]:
  name='CIVIC200_'+r['label']+'_'+side;o=bpy.data.objects.get(name)
  if not o:raise RuntimeError('Missing expected camera '+name)
  before=list(o.location);o.location=(x,y,z+1.7);n=r['true_north_live_unit'];o.rotation_euler=Vector((n[0]*sign,n[1]*sign,0)).to_track_quat('-Z','Y').to_euler();o.data.clip_end=30000;o['chainage_m']=r['chainage_m'];o['calibration_status']='Mapped connected road route; provisional camera location';o['longitude']=r['lonlat'][0];o['latitude']=r['lonlat'][1];report['camera_updates'].append({'name':name,'before':before,'after':list(o.location)})
sc.view_layers[0].update();bad=[]
for o in newground:
 m=o.data;ec=collections.Counter(tuple(sorted(e)) for p in m.polygons for e in p.edge_keys);zero=sum(p.area<1e-10 for p in m.polygons);nf=sum(not all(math.isfinite(x) for x in v.co) for v in m.vertices);edge=sum(n!=2 for n in ec.values())
 if zero or nf or edge:bad.append({'name':o.name,'zero_area':zero,'nonfinite':nf,'nonmanifold_edges':edge})
report['ground_mesh_issues']=bad;report['new_ground_objects']=len(newground);report['all_cameras']=sum(o.type=='CAMERA' for o in sc.objects)
path=str(out/('CIVIC_CALIBRATION_'+stamp+'.blend'));bpy.ops.wm.save_as_mainfile(filepath=path);report['file']=path;(out/'applied_calibration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));result={'file':path,'new_ground_objects':len(newground),'mesh_issues':bad,'removed_entities':report['removed_aboveground_entities'],'cameras_updated':len(report['camera_updates'])}
