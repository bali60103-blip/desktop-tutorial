import bpy,json,os,pathlib,datetime,collections,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'PriorityNodes_20260914';p=json.load(open(out/'xinsheng_barrier_opening_payload.json'));r=json.load(open(out/'xinsheng_ramp_payload.json'))
main=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];sc=bpy.data.scenes['P1_XINSHENG_RAMP_COMPARISON'];original=bpy.data.objects['PARAPET_48776372_1']
assert not bpy.data.collections.get('P1_XINSHENG_BARRIER_OPENING_EST')
before={'markers':len([m for m in main.timeline_markers if m.camera]),'objects':len(main.objects),'cameras':len([o for o in main.objects if o.type=='CAMERA'])}
bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_RAMP_OPENING_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True)
bpy.context.window.scene=sc
# Clone only this scene's root collection membership; all original geometry is retained.
old=bpy.data.collections['COMPLETION_GROUND_HIGHWAY'];cl=old.copy();cl.name='P1_RAMP_COMPLETION_GROUND_HIGHWAY';sc.collection.children.link(cl);sc.collection.children.unlink(old);cl.objects.unlink(original)
assert original.name not in sc.objects
col=bpy.data.collections.new('P1_XINSHENG_BARRIER_OPENING_EST');sc.collection.children.link(col);new=[]
for i,g in enumerate(p['parts']):
 origin=Vector(g['vertices'][0]);me=bpy.data.meshes.new('P1_MAINLINE_OPENING_%02d_EST'%i);me.from_pydata([Vector(v)-origin for v in g['vertices']],[],g['faces']);me.update()
 for m in original.data.materials:me.materials.append(m)
 obj=bpy.data.objects.new(me.name,me);col.objects.link(obj);obj.location=origin;obj['status']=p['assumption'];obj['source_object']=original.name;new.append(obj)
sc.view_layers[0].update();errors=[]
for o in new:
 edges=collections.Counter(tuple(sorted(e)) for f in o.data.polygons for e in f.edge_keys)
 if any(n!=2 for n in edges.values()):errors.append(o.name)
assert not errors
verts=[];faces=[]
for o in bpy.data.collections['P1_XINSHENG_RAMP_EST'].objects:
 if 'RAMP_DECK' not in o.name:continue
 base=len(verts);verts.extend(o.matrix_world@v.co for v in o.data.vertices);faces.extend([base+i for i in f.vertices] for f in o.data.polygons)
bvh=BVHTree.FromPolygons(verts,faces);hits=[]
for o in list(new)+[o for o in sc.objects if o.name.startswith('PARAPET_') and o.type=='MESH' and o.visible_get()]:
 other=BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(f.vertices) for f in o.data.polygons]);n=len(bvh.overlap(other))
 if n:hits.append({'object':o.name,'triangle_pairs':n})
# Three comparison-only cameras. Long axis positions derive from the modeled ramp.
axis=r['shared_axis'];coords=axis['coordinates'] if isinstance(axis,dict) else axis
start=Vector((*coords[0],8));end=Vector((*coords[-1],.15));d=(start-end).normalized()
camcol=bpy.data.collections.new('P1_XINSHENG_DETAIL_CAMERAS');sc.collection.children.link(camcol)
for label,eye,target,lens in [('MOUTH',end-d*18+Vector((0,0,1.7)),start,24),('MERGE',start+Vector((0,0,20)),start+Vector((-20,0,0)),24),('AXIAL',end-d*35+Vector((0,0,18)),start,35)]:
 data=bpy.data.cameras.new('P1_RAMP_'+label);cam=bpy.data.objects.new(data.name,data);camcol.objects.link(cam);data.lens=lens;data.clip_end=3000;cam.location=eye;cam.rotation_euler=(target-eye).to_track_quat('-Z','Y').to_euler();cam['status']='Model review camera; not exact panorama pose';sc.camera=cam;sc.render.filepath=str(out/('P1_RAMP_'+label+'_V2.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
report={'replacement_meshes':len(new),'closed_mesh_errors':errors,'barrier_deck_intersections':hits,'removed_barrier_plan_area_m2':p['removed_area'],'assumptions':p['assumption'],'adopted_in_main':False,'pending':['Visual confirmation of opening extent','Support ownership and geometry','Deck overlap and driving clearance','Measured elevation and widths'],'main_before':before}
bpy.context.window.scene=main;after={'markers':len([m for m in main.timeline_markers if m.camera]),'objects':len(main.objects),'cameras':len([o for o in main.objects if o.type=='CAMERA'])};assert before==after;assert original.name in main.objects
report['main_after']=after;(out/'xinsheng_ramp_opening_report.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(out/'CIVIC_PRIORITY_A_RAMP_REVIEW_20260914.blend'));result=report
