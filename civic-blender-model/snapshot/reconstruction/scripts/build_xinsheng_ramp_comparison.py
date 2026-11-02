import bpy,json,os,pathlib,datetime,math,collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'PriorityNodes_20260914';r=json.load(open(out/'xinsheng_ramp_payload.json'));main=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];assert not bpy.data.scenes.get('P1_XINSHENG_RAMP_COMPARISON')
bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_XINSHENG_RAMP_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True)
sc=main.copy();sc.name='P1_XINSHENG_RAMP_COMPARISON';sc.use_fake_user=True;sc.timeline_markers.clear();bpy.context.window.scene=sc
col=bpy.data.collections.new('P1_XINSHENG_RAMP_EST');sc.collection.children.link(col);mats={}
for k,c in {'ROAD':(.17,.19,.20,1),'CONCRETE':(.54,.54,.49,1),'YELLOW':(.95,.64,.05,1)}.items():
 m=bpy.data.materials.new('P1_RAMP_'+k);m.diffuse_color=c;mats[k]=m
names=[];deck=[]
for p in r['pieces']:
 origin=Vector(p['mesh']['vertices'][0]);m=bpy.data.meshes.new(p['name']);m.from_pydata([Vector(v)-origin for v in p['mesh']['vertices']],[],p['mesh']['faces']);m.materials.append(mats[p['material']]);m.update();o=bpy.data.objects.new(p['name'],m);col.objects.link(o);o.location=origin;o['status']='OSM XY plus street-view morphology; width, profile, barriers and posts estimated; comparison not adopted';o['source_ids']='51362366,51362367,51362403,51362368';names.append(o.name)
 if p['material']=='ROAD':deck.append(o)
sc.view_layers[0].update();errors=[]
for o in col.objects:
 ec=collections.Counter(tuple(sorted(e)) for p in o.data.polygons for e in p.edge_keys)
 if any(v!=2 for v in ec.values()) or any(not math.isfinite(v) for p in o.data.vertices for v in p.co):errors.append(o.name)
assert not errors
vs=[];fs=[]
for o in deck:
 base=len(vs);vs.extend(o.matrix_world@v.co for v in o.data.vertices);fs.extend([base+i for i in p.vertices] for p in o.data.polygons)
bvh=BVHTree.FromPolygons(vs,fs);hits=[]
for o in sc.objects:
 if not o.name.startswith('PARAPET_') or o.type!='MESH' or not o.visible_get():continue
 coords=[o.matrix_world@v.co for v in o.data.vertices]
 if min(v.x for v in coords)>2140 or max(v.x for v in coords)<1580:continue
 other=BVHTree.FromPolygons(coords,[list(p.vertices) for p in o.data.polygons]);pairs=bvh.overlap(other)
 if pairs:hits.append({'object':o.name,'triangle_intersection_pairs':len(pairs)})
sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=1200;sc.render.resolution_y=750;sc.render.resolution_percentage=100;sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=False;sc.display.shading.show_cavity=True
cd=bpy.data.cameras.new('P1_XINSHENG_REVIEW_CAMERA');cam=bpy.data.objects.new(cd.name,cd);sc.collection.objects.link(cam);sc.camera=cam;cd.clip_end=2000
for label,eye,target,scale in [('OVERVIEW',(1840,230,230),(1850,600,4),520),('LOWER',(2090,520,10),(1980,545,5),100),('UPPER',(1735,705,32),(1710,630,7),180)]:
 cd.type='ORTHO';cd.ortho_scale=scale;cam.location=eye;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(out/('P1_XINSHENG_'+label+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
report={k:v for k,v in r.items() if k not in ['pieces','footprint','shared_axis']};report.update({'scene':sc.name,'objects':names,'mesh_count':len(names),'mesh_errors':errors,'mainline_barrier_intersections':hits,'adopted_in_main_scene':False,'main_animation_markers':len([m for m in main.timeline_markers if m.camera]),'pending':'Resolve mainline barrier cuts and pier ownership/support geometry before adoption. Cross-section and elevation remain estimated.'});(out/'xinsheng_ramp_comparison_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
bpy.context.window.scene=main;main['ramp_comparison_scene']=sc.name;bpy.ops.wm.save_as_mainfile(filepath=str(out/'CIVIC_PRIORITY_A_RAMP_REVIEW_20260914.blend'));result={'meshes':len(names),'errors':errors,'barrier_intersections':hits,'comparison_scene':sc.name,'main_unchanged':True}
