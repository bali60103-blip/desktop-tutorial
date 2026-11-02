"""Build isolated frontage comparison; preserve main context without double geometry."""
import bpy,bmesh,json,pathlib,datetime
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'FullFrontageSolids';out.mkdir(exist_ok=True)
main=bpy.data.scenes['Scene'];bpy.context.window.scene=main;s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_frontage_'+s+'.blend')),copy=True)
p=json.load(open('/tmp/civic-frontage-full/solids/payload.json'));col=bpy.data.collections.new('FRONTAGE_FULL_HEIGHT_COMPARISON');main.collection.children.link(col)
mats=[]
for name,c in [('FRONTAGE_HEIGHT_TAG',(.15,.55,.42)),('FRONTAGE_HEIGHT_ASSUMED',(.73,.49,.16))]:
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.diffuse_color=(*c,1);mats.append(m)
report=[]
for r in p['buildings']:
 name='FRONTAGE_SOLID_'+r['osm_id'];me=bpy.data.meshes.new(name);me.from_pydata(r['vertices'],[],r['faces']);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);bm.to_mesh(me);bm.free();assert bad==0
 me.materials.append(mats[int(r['height_status'].startswith('ASSUMED'))]);o=bpy.data.objects.new(name,me);col.objects.link(o)
 o['osm_id']=r['osm_id'];o['height_status']=r['height_status'];o['height_m']=r['height_m'];o['source_tags']=json.dumps(r['tags'],ensure_ascii=False);o['scope']='First-hit frontage candidate; base Z=0 assumed; compare before replacing existing context'
 report.append({k:r[k] for k in ['osm_id','name','height_m','height_status']})
main.view_layers[0].layer_collection.children[col.name].exclude=True
sc=bpy.data.scenes.new('FULL_FRONTAGE_HEIGHT_COMPARISON');sc.collection.children.link(col)
for name in ['GROUND_FULL_01_OFFICIAL_AND_ESTIMATED','GROUND_FULL_02_CROSSINGS_AND_RAMPS_ESTIMATED']:sc.collection.children.link(bpy.data.collections[name])
sc.world=main.world;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=False;sc.display.shading.show_cavity=False
camd=bpy.data.cameras.new('FRONTAGE_HEIGHT_CAMERA');cam=bpy.data.objects.new(camd.name,camd);sc.collection.objects.link(cam);sc.camera=cam;cam.location=(5600,-6500,6000);cam.rotation_euler=(Vector((5600,800,0))-cam.location).to_track_quat('-Z','Y').to_euler();camd.type='ORTHO';camd.ortho_scale=12000;camd.clip_end=30000
sc.render.resolution_x=1600;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.render.filepath=str(out/'frontage_height_comparison.png');bpy.ops.render.render(write_still=True,scene=sc.name)
# Five overlapping panels for geometry inspection along the corridor.
for index,x in enumerate([1700,3800,5900,8000,10100]):
 cam.location=(x,-1800,1800);cam.rotation_euler=(Vector((x,850,10))-cam.location).to_track_quat('-Z','Y').to_euler();camd.ortho_scale=2800
 sc.render.filepath=str(out/('frontage_panel_'+str(index+1)+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
bpy.context.window.scene=main
file=out/('CIVIC_FRONTAGE_COMPARISON_'+s+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file))
result={'file':str(file),'solids':report,'unknown_height_candidates_retained_in_original_context':p['unknown_retained'],'new_mesh_nonmanifold_edges':0,'main_context_replaced':False,'limitations':'Full-axis candidates with parsable height or levels only; missing heights and multipolygon omissions remain. Original context retained without double geometry in main scene.'};(out/'frontage_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
