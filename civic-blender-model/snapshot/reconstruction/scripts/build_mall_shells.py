import bpy,bmesh,json,pathlib,datetime,shutil
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'UndergroundShells';out.mkdir(exist_ok=True);src=out/'source';src.mkdir(exist_ok=True)
for n in ['legacy.json','payload.json']:shutil.copy2('/tmp/civic-mall/'+n,src/n)
main=bpy.data.scenes['Scene'];bpy.context.window.scene=main;s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_shells_'+s+'.blend')),copy=True)
assert not bpy.data.collections.get('UNDERGROUND_SHELLS_ESTIMATED')
col=bpy.data.collections.new('UNDERGROUND_SHELLS_ESTIMATED');main.collection.children.link(col)
sc=bpy.data.scenes.new('UNDERGROUND_SHELL_COMPARISON');sc.collection.children.link(col);sc.world=main.world;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=False;sc.display.shading.show_cavity=True
mats=[]
for n,color in [('R_MALL_ESTIMATED',(.18,.56,.62,1)),('STATION_UNCLASSIFIED',(.85,.45,.15,1)),('PASSAGE_UNVERIFIED',(.43,.38,.65,1))]:
 m=bpy.data.materials.new(n);m.diffuse_color=color;mats.append(m)
rows=json.load(open(src/'payload.json'));qa=[]
for i,r in enumerate(rows):
 for part in r['parts']:
  me=bpy.data.meshes.new(r['source']+'_'+part['part']);me.from_pydata(part['mesh']['vertices'],[],part['mesh']['faces']);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);bm.to_mesh(me);bm.free();assert bad==0
  o=bpy.data.objects.new(me.name,me);col.objects.link(o);o.data.materials.append(mats[1 if i==0 else 0 if i==1 else 2]);o['source_object']=r['source'];o['status']=r['status'];o['identity']=r['identity'];o['floor_z_assumed']=-3.6;o['clear_height_assumed']=2.8
  if part['part']=='REMOVABLE_ROOF':o.hide_render=True;o.hide_set(True)
  qa.append({'object':o.name,'nonmanifold_edges':bad,'part':part['part']})
main.view_layers[0].layer_collection.children[col.name].exclude=True
cd=bpy.data.cameras.new('UNDERGROUND_SHELL_REVIEW');cam=bpy.data.objects.new(cd.name,cd);sc.collection.objects.link(cam);sc.camera=cam;cd.type='ORTHO';cd.clip_end=10000;sc.render.resolution_x=1400;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
for i,r in enumerate(rows):
 for o in col.objects:o.hide_render=o['source_object']!=r['source'] or 'REMOVABLE_ROOF' in o.name
 x0,y0,x1,y1=r['bounds'];center=Vector(((x0+x1)/2,(y0+y1)/2,-3.6));cam.location=center+Vector((0,-max(y1-y0,150)*.65,max(y1-y0,150)));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=max(x1-x0,(y1-y0)*1.4)*1.2
 sc.render.filepath=str(out/('shell_'+str(i)+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
for o in col.objects:o.hide_render='REMOVABLE_ROOF' in o.name
bpy.context.window.scene=main;file=out/('CIVIC_UNDERGROUND_SHELLS_'+s+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file))
r={'file':str(file),'shell_envelopes':3,'floor_z':-3.6,'clear_height':2.8,'qa':qa,'originals_preserved':True,'roof_hidden_for_cutaway':True,'limitations':'Legacy XY retained, not registered to official plans. Station envelope is unclassified, not asserted to be Y mall. No entrances, shops, stairs or connections built. Main scene comparison collection excluded.'};(out/'shell_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result=r
