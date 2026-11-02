import bpy,bmesh,json,pathlib,datetime
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'YGroundOpenings';p=json.load(open(out/'ground_patch_payload.json'));entries=json.load(open(root/'YMallEntrances/source/y_entrance_payload.json'))['entries'];s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_ground_openings_'+s+'.blend')),copy=True)
main=bpy.data.scenes['Scene'];sc=bpy.data.scenes['Y_MALL_ENTRANCE_COMPARISON'];assert not bpy.data.collections.get('Y_GROUND_OPENINGS_COMPARISON');col=bpy.data.collections.new('Y_GROUND_OPENINGS_COMPARISON');main.collection.children.link(col);sc.collection.children.link(col);main.view_layers[0].layer_collection.children[col.name].exclude=True;m=bpy.data.materials.new('Y_GROUND_PATCH_EST');m.diffuse_color=(.5,.5,.48,1);qa=[]
for r in p['patches']:
 me=bpy.data.meshes.new(r['name']);me.from_pydata(r['mesh']['vertices'],[],r['mesh']['faces']);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);assert bad==0;bm.to_mesh(me);bm.free();o=bpy.data.objects.new(r['name'],me);col.objects.link(o);me.materials.append(m);o['status']=p['note'];o['source_surface']=r['source'];o['source_top_z']=r['top_z'];qa.append({'name':o.name,'nonmanifold_edges':bad})
vs=[];fs=[]
for o in col.objects:
 off=len(vs);vs.extend(v.co for v in o.data.vertices);fs.extend([[off+i for i in f.vertices] for f in o.data.polygons])
tree=BVHTree.FromPolygons(vs,fs);hits=[]
for e in entries:
 if e['ref'] not in p['entrances']:continue
 a=Vector(e['live_xy']);d=(Vector(e['lower_landing_xy'])-a).normalized()
 for i in range(1,24):
  q=a+d*(i*.3);loc,_,_,dist=tree.ray_cast(Vector((q.x,q.y,3)),Vector((0,0,-1)),5)
  if loc is not None:hits.append({'ref':e['ref'],'step':i})
assert not hits,hits
cam=sc.camera
for ref in p['entrances']:
 e=next(e for e in entries if e['ref']==ref);a=Vector((*e['live_xy'],-1));cam.location=a+Vector((18,-22,24));cam.rotation_euler=(a-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=35;sc.render.filepath=str(out/(ref+'_ground_opening.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
file=out/('CIVIC_Y_GROUND_OPENINGS_'+s+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));r={'file':str(file),'patched_entries':p['entrances'],'patch_meshes':len(qa),'nonmanifold_edges':0,'remaining_vertical_hits':hits,'samples':46,'limitations':p['note'],'main_ground_unchanged':True};(out/'ground_opening_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result=r
