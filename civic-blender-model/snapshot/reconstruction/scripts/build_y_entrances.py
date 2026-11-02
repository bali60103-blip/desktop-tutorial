import bpy,bmesh,json,pathlib,datetime,shutil
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'YMallEntrances';out.mkdir(exist_ok=True);src=out/'source';src.mkdir(exist_ok=True)
for n in ['entries.json','y_entrance_payload.json','y_plan.pdf']:shutil.copy2('/tmp/civic-mall/'+n,src/n)
p=json.load(open(src/'y_entrance_payload.json'));main=bpy.data.scenes['Scene'];
if bpy.context.window:bpy.context.window.scene=main
s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_y_entrances_'+s+'.blend')),copy=True)
assert not bpy.data.collections.get('Y_MALL_ENTRANCE_COMPARISON_ESTIMATED')
col=bpy.data.collections.new('Y_MALL_ENTRANCE_COMPARISON_ESTIMATED');main.collection.children.link(col);sc=bpy.data.scenes.new('Y_MALL_ENTRANCE_COMPARISON');sc.collection.children.link(col);sc.world=main.world;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=False;sc.display.shading.show_cavity=True
mats={}
for name,c in [('stairs',(.88,.5,.12,1)),('floor',(.15,.5,.6,1)),('wall',(.3,.65,.69,1)),('roof',(.4,.45,.5,1))]:
 m=bpy.data.materials.new('Y_ESTIMATED_'+name);m.diffuse_color=c;mats[name]=m
qa=[]
for p0 in p['parts']:
 me=bpy.data.meshes.new(p0['name']);me.from_pydata(p0['mesh']['vertices'],[],p0['mesh']['faces']);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);bm.to_mesh(me);bm.free();assert bad==0
 o=bpy.data.objects.new(me.name,me);col.objects.link(o);me.materials.append(mats[p0['kind']]);o['status']=p['assumptions'];o['part']=p0['kind']
 if p0['kind']=='roof':o.hide_render=True;o.hide_set(True)
 qa.append({'object':o.name,'nonmanifold_edges':bad})
for e in p['entries']:
 cu=bpy.data.curves.new(e['ref']+'_LABEL','FONT');cu.body=e['ref']+' EST';cu.size=1.3;o=bpy.data.objects.new(cu.name,cu);col.objects.link(o);o.location=(*e['live_xy'],.4);o['osm_id']=str(e['osm_id']);o['status']='OSM entrance XY; geometry estimate'
main.view_layers[0].layer_collection.children[col.name].exclude=True
cd=bpy.data.cameras.new('Y_ENTRANCE_REVIEW');cam=bpy.data.objects.new(cd.name,cd);sc.collection.objects.link(cam);sc.camera=cam;cd.type='ORTHO';cd.clip_end=10000;sc.render.resolution_x=1400;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
for ref in ['Y13','Y27','Y12']:
 e=next(x for x in p['entries'] if x['ref']==ref);center=Vector((*e['live_xy'],-2));cam.location=center+Vector((30,-38,40));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=65;sc.render.filepath=str(out/(ref+'_comparison.png'));bpy.ops.render.render(write_still=True,scene=sc.name)

if bpy.context.window:bpy.context.window.scene=main
file=out/('CIVIC_Y_ENTRANCES_'+s+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));r={'file':str(file),'entrance_comparisons':len([e for e in p['entries'] if e['built']]),'mesh_count':len(qa),'nonmanifold_edges':sum(x['nonmanifold_edges'] for x in qa),'entries':p['entries'],'assumptions':p['assumptions'],'official_plan':p['official_plan'],'unfinished':'Actual stair directions, escalators, lifts, stairwell sidewalls, ground excavation and shop layout remain unresolved; comparison only'};(out/'y_entrance_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result={k:v for k,v in r.items() if k!='entries'}
