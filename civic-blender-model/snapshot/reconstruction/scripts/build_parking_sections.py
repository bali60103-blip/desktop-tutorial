"""Build user-authorized parking section comparison, not registered as-built garages."""
import bpy,bmesh,json,pathlib,datetime
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'ParkingSections';out.mkdir(exist_ok=True)
main=bpy.data.scenes['Scene'];bpy.context.window.scene=main;s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_parking_sections_'+s+'.blend')),copy=True)
p=json.load(open('/tmp/civic-parking-segments/payload.json'));col=bpy.data.collections.new('PARKING_8_SECTIONS_COMPARISON_ASSUMED');main.collection.children.link(col)
mat=bpy.data.materials.new('PARKING_SECTION_BLUE');mat.diffuse_color=(.13,.4,.65,1);orange=bpy.data.materials.new('PARKING_ENTRY_CANDIDATE_ORANGE');orange.diffuse_color=(.9,.4,.08,1)
cams=[];qa=[]
for r in p['sections']:
 for m in r['meshes']:
  me=bpy.data.meshes.new(m['name']);me.from_pydata(m['vertices'],[],m['faces']);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);bm.to_mesh(me);bm.free();assert bad==0
  me.materials.append(mat);o=bpy.data.objects.new(m['name'],me);col.objects.link(o);o['status']='ESTIMATED COMPARISON: 24m width and -3.6m/level; not surveyed';o['extent_status']=r['extent_status'];o['official_floor_count']=r['levels'];qa.append({'name':o.name,'nonmanifold_edges':bad})
 # Wire outline at reference ground Z for plan comparison.
 cu=bpy.data.curves.new(r['name']+'_ESTIMATED_EXTENT','CURVE');cu.dimensions='3D';cu.bevel_depth=.06;sp=cu.splines.new('POLY');sp.points.add(len(r['outline'])-1)
 for v,xy in zip(sp.points,r['outline']):v.co=(*xy,0,1)
 ob=bpy.data.objects.new(cu.name,cu);col.objects.link(ob)
 for i,entry in enumerate(r['entrances']):
  bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=12,radius1=.8,radius2=0,depth=2);me=bpy.data.meshes.new('ENTRY_MARKER');bm.to_mesh(me);bm.free();me.materials.append(orange);o=bpy.data.objects.new(r['name']+'_ENTRY_CANDIDATE_'+str(i),me);col.objects.link(o);o.location=(*entry['xy'],1);o['status']=entry['status'];o['osm_id']=str(entry['osm_id'])
 if r.get('ramp_camera'):
  cd=bpy.data.cameras.new(r['name']+'_B1_B2_CAMERA');cam=bpy.data.objects.new(cd.name,cd);col.objects.link(cam);cam.location=r['ramp_camera']['location'];cam.rotation_euler=(Vector(r['ramp_camera']['target'])-cam.location).to_track_quat('-Z','Y').to_euler();cd.lens=24;cd.clip_end=600;cams.append(cam.name)
main.view_layers[0].layer_collection.children[col.name].exclude=True
sc=bpy.data.scenes.new('PARKING_SECTIONS_COMPARISON');sc.collection.children.link(col);sc.world=main.world;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=False;sc.display.shading.show_cavity=False
cd=bpy.data.cameras.new('PARKING_OVERVIEW');cam=bpy.data.objects.new(cd.name,cd);sc.collection.objects.link(cam);sc.camera=cam;cam.location=(2100,-2000,1400);cam.rotation_euler=(Vector((2100,800,-4))-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=5300;cd.clip_end=15000;sc.render.resolution_x=1800;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
sc.render.filepath=str(out/'all_sections_B1.png');bpy.ops.render.render(write_still=True,scene=sc.name)
for o in col.objects:
 if o.type=='MESH' and '_B1' in o.name and '_B1_B2' not in o.name:o.hide_render=True
sc.render.filepath=str(out/'all_sections_lower_levels.png');bpy.ops.render.render(write_still=True,scene=sc.name)
for o in col.objects:
 if o.type=='MESH' and '_B1' in o.name and '_B1_B2' not in o.name:o.hide_render=False
bpy.context.window.scene=main;file=out/('CIVIC_PARKING_SECTIONS_'+s+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file))
report={'file':str(file),'parking_sections':8,'floor_slabs':14,'interlevel_comparison_ramps':6,'ramp_cameras':cams,'geometry_checks':qa,'entry_candidate_markers':sum(len(r['entrances']) for r in p['sections']),'overlaps':p['overlaps'],'controls':p['controls'],'limitations':'Separate comparison scene; all section widths and depths estimated. No stall arrangement, surveyed ramps, equipment or physical underground-street links claimed. Gongyuan road control projects over 60m; Yanji +/-100m is assumed. Main original model remains intact.'};(out/'parking_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));result={k:v for k,v in report.items() if k not in ['geometry_checks','controls','ramp_cameras']}
