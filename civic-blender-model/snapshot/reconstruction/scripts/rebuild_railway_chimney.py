"""Replace generic windowed chimney and duplicate equipment proxy; official 45m height, estimated profile."""
import bpy,json,os,pathlib,math,datetime
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;name='CAL3_RAILWAY_CHIMNEY';assert not bpy.data.collections.get(name),'Already built';bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_CHIMNEY_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True);col=bpy.data.collections.new(name);sc.collection.children.link(col);ret=bpy.data.collections.new('CAL3_RETAINED_CHIMNEY_PROXIES');sc.collection.children.link(ret);sources=['COMP_OSM_EQUIP_1342705709','BLOCK_w1342705709_CORE','BLOCK_w1342705709_FACADE'];centers=[Vector(v) for v in next(r for r in json.load(open(out/'equipment_detail_inventory.json')) if r['name']==sources[0])['bounds']];center=sum(centers,Vector())/8;center.z=0;archived=[]
for key in sources:
 o=bpy.data.objects[key];ret.objects.link(o)
 for c in list(o.users_collection):
  if c!=ret and (c.name.startswith('GZI_') or c.name in ['COMPLETION_EQUIPMENT','BLOCK_BUILDING_CORES','BLOCK_RECESSED_FACADES']):c.objects.unlink(o)
 o['retained_reason']='Chimney is not a windowed building or a 2.4m equipment box';archived.append(key)
sc.view_layers[0].layer_collection.children[ret.name].exclude=True;mat=bpy.data.materials.new('CAL3_CHIMNEY_CONCRETE_EST');mat.diffuse_color=(.52,.52,.49,1);dark=bpy.data.materials.new('CAL3_CHIMNEY_INTERIOR_EST');dark.diffuse_color=(.13,.14,.14,1);steel=bpy.data.materials['CAL3_HANDRAIL_STEEL_EST'];N=48;vs=[];fs=[];profile=[(0,1.39),(2,1.36),(35,1.02),(43,.96),(45,.94),(45,.77),(43,.79),(35,.83),(2,1.14),(0,1.16)]
for z,r in profile:
 for j in range(N):vs.append((r*math.cos(j*math.tau/N),r*math.sin(j*math.tau/N),z))
for i in range(len(profile)):
 k=(i+1)%len(profile)
 for j in range(N):q=(j+1)%N;fs.append((i*N+j,i*N+q,k*N+q,k*N+j))
m=bpy.data.meshes.new('RAILWAY_CHIMNEY_45M_BODY');m.from_pydata(vs,[],fs);m.materials.append(mat);m.materials.append(dark);m.update();o=bpy.data.objects.new(m.name,m);o.location=center;col.objects.link(o)
for p in m.polygons:p.use_smooth=True;p.material_index=1 if p.index//N>=5 else 0
o['official_height_m']=45.0;o['source_url']='https://www.nrm.gov.tw/News_Content2.aspx?n=3313&s=138273&sms=13762';o['osm_id']='w1342705709';o['verification_status']='Height45m supported by National Railway Museum. OSM center/footprint retained. Taper, wall thickness and base datum estimated; no internal engineering model.';o['photo_url']='https://file.moc.gov.tw/001/Upload/OldFiles/AdminUploads/information/large/fe8d1ce3-c31c-4c4d-9d29-524d4a5bec7f.jpg';o['base_radius_est_m']=1.39;o['top_radius_est_m']=.94
# Keep the existing full-scene integration alternative current.
bpy.data.scenes['GONGZHONG_INTEGRATED_OPENINGS_EST'].collection.children.link(col)
review=bpy.data.scenes.new('RAILWAY_CHIMNEY_DETAIL_REVIEW');review.collection.children.link(col);review.world=sc.world;cd=bpy.data.cameras.new('CHIMNEY_REVIEW_CAMERA');cam=bpy.data.objects.new(cd.name,cd);review.collection.objects.link(cam);target=center+Vector((0,0,22));cam.location=target+Vector((42,-65,15));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=52;review.camera=cam;review.render.engine='BLENDER_WORKBENCH';review.render.resolution_x=700;review.render.resolution_y=1000;review.render.resolution_percentage=100;review.display.shading.color_type='MATERIAL';review.display.shading.show_shadows=False;review.display.shading.show_cavity=True;review.render.image_settings.file_format='PNG';review.render.filepath=str(out/'RAILWAY_CHIMNEY_DETAIL.png');bpy.ops.render.render(write_still=True,scene=review.name)
edges={}
for p in m.polygons:
 for e in p.edge_keys:edges[e]=edges.get(e,0)+1
assert all(v==2 for v in edges.values());assert abs(max(v.co.z for v in m.vertices)-45)<1e-5
r={'object':o.name,'source_url':o['source_url'],'photo_url':o['photo_url'],'height_m':45,'height_evidence':'National Railway Museum official page','center_xy':list(center)[:2],'archived':archived,'removed_generic_window_instances':112,'profile_z_radius_est_m':profile,'mesh_closed':True,'limits':'Real profile dimensions/base elevation unverified. Smoke/antenna/ladder fixtures not inferred from indistinct pixels.'};(out/'railway_chimney_report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));bpy.context.window.scene=sc;sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result=r
