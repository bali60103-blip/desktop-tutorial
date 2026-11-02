import bpy,bmesh,json,pathlib,datetime
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'YTopTransitions';out.mkdir(exist_ok=True);p=json.load(open(root/'YMallEntrances/source/y_entrance_payload.json'));s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_top_transition_'+s+'.blend')),copy=True)
main=bpy.data.scenes['Scene'];sc=bpy.data.scenes['Y_MALL_ENTRANCE_COMPARISON'];assert not bpy.data.collections.get('Y_TOP_TRANSITIONS_ESTIMATED');col=bpy.data.collections.new('Y_TOP_TRANSITIONS_ESTIMATED');main.collection.children.link(col);sc.collection.children.link(col);main.view_layers[0].layer_collection.children[col.name].exclude=True
mat=bpy.data.materials.get('Y_ESTIMATED_stairs');wall=bpy.data.materials.get('Y_STAIR_CONCRETE_EST');faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)];qa=[]
def prism(name,a,d,n,lo,hi,z0,za,zb,material):
 xy=[a+d*(-.3)+n*lo,a+n*lo,a+n*hi,a+d*(-.3)+n*hi];vs=[(v.x,v.y,z0) for v in xy]+[(v.x,v.y,z) for v,z in zip(xy,[za,zb,zb,za])];me=bpy.data.meshes.new(name);me.from_pydata(vs,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);assert bad==0;bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);col.objects.link(o);me.materials.append(material);o['status']='Model-relative top transition: sidewalk +0.15, old top step0, B1 -3.6. Assumed geometry, not survey.';qa.append(name)
for e in p['entries']:
 if e['ref'] not in ['Y9','Y10']:continue
 a=Vector(e['live_xy']);d=(Vector(e['lower_landing_xy'])-a).normalized();n=Vector((-d.y,d.x));ref=e['ref'];prism(ref+'_TOP_STEP_015',a,d,n,-1.2,1.2,-.08,.15,.15,mat)
 for side in [-1,1]:
  lo,hi=sorted([side*1.2,side*1.35]);prism(ref+'_TOP_SIDE_'+str(side),a,d,n,lo,hi,-.08,1.05,.9,wall)
cam=sc.camera
for ref in ['Y9','Y10']:
 e=next(e for e in p['entries'] if e['ref']==ref);a=Vector((*e['live_xy'],0));cam.location=a+Vector((5,-6,5));cam.rotation_euler=(a-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=8;sc.render.filepath=str(out/(ref+'_top_transition.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
file=out/('CIVIC_Y_TOP_TRANSITIONS_'+s+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));r={'file':str(file),'entries':['Y9','Y10'],'new_meshes':len(qa),'nonmanifold_edges':0,'top_step_z':.15,'old_top_step_z':0,'tread_m':.3,'risers_to_B1':25,'B1_z':-3.6,'limitation':'Geometry matches existing modeled sidewalk height, not real-world survey; no verified code compliance. Existing main scene unchanged.'};(out/'top_transition_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result=r
