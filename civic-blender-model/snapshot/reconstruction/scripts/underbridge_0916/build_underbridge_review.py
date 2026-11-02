import os
import bpy,json,pathlib,collections,math,shutil
from mathutils import Vector
src=pathlib.Path(os.environ.get('CIVIC_AUDIT_DIR','underbridge_work'));base=bpy.data.scenes['CIVIC_FULL_CORRIDOR_PRESENTATION'];original_path=pathlib.Path(bpy.data.filepath);out=original_path.parent/'Underbridge_20260916';out.mkdir(exist_ok=True)
assert not bpy.data.scenes.get('CIVIC_UNDERBRIDGE_MASSING_20260916')
sc=base.copy();sc.name='CIVIC_UNDERBRIDGE_MASSING_20260916';sc.use_fake_user=True;sc['source_scene']=base.name;sc['status']='In progress. No full-corridor dimensional verification.';bpy.context.window.scene=sc
col=bpy.data.collections.new('UB_LINSEN_OBSERVED_MASSES_EST');sc.collection.children.link(col);payload=json.load(open(src/'linsen_mass_payload.json'));mats={}
for kind,color in [('CURB',(.45,.45,.4,1)),('SHRUB',(.18,.32,.14,1))]:
 m=bpy.data.materials.new('UB_'+kind);m.diffuse_color=color;mats[kind]=m
for p in payload['pieces']:
 vs=p['mesh']['v'];origin=Vector(vs[0]);me=bpy.data.meshes.new(p['name']);me.from_pydata([Vector(v)-origin for v in vs],[],p['mesh']['f']);me.materials.append(mats[p['kind']]);me.update();o=bpy.data.objects.new(me.name,me);col.objects.link(o);o.location=origin;o['confidence']='Streetview morphology only; XY and dimensions estimated';o['source_pano']='CIABIhBqmk8t_Jr0KkpQi4oI1qoM';o['review_segment']='UB_X+014';o['pending']='Confirm curb outline and height, all column positions, equipment box, fence, and signals'
errors=[]
for o in col.objects:
 e=collections.Counter(tuple(sorted(k)) for f in o.data.polygons for k in f.edge_keys)
 if any(n!=2 for n in e.values()):errors.append(o.name)
assert not errors
# Audit markers are viewport-only; do not change animation cameras.
audit=json.load(open(src/'underbridge_coverage.json'));marks=bpy.data.collections.new('UB_REVIEW_COVERAGE_PENDING');sc.collection.children.link(marks)
for seg in audit['segments']:
 o=bpy.data.objects.new(seg['id'],None);marks.objects.link(o);o.location=(*seg['xy'],.5);o.empty_display_type='CIRCLE';o.empty_display_size=3;o.hide_render=True;o['status']='Pending full streetview and size review';o['existing_candidates']=len(seg['objects'])
 for_missing=seg['id']=='UB_X+014'
 if for_missing:seg['streetview_status']='partial_one_view';seg['observed_categories']=['planter','shrub','column','column_fence','equipment_enclosure','traffic_signal'];seg['added_mass_objects']=[o.name for o in col.objects]
sc['coverage_index']='underbridge_coverage.json';sc['fully_verified_segments']=0
# Separate rendering scene keeps animation unchanged.
review=sc.copy();review.name='UB_LINSEN_REVIEW_20260916';review.use_fake_user=True;review.timeline_markers.clear();cd=bpy.data.cameras.new('UB_LINSEN_REVIEW_CAMERA');cam=bpy.data.objects.new(cd.name,cd);review.collection.objects.link(cam);cam.location=(1400,695,2.5);target=Vector((1440,710,1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='PERSP';cd.lens=28;review.camera=cam;review.render.engine='BLENDER_WORKBENCH';review.display.shading.color_type='MATERIAL';review.display.shading.show_cavity=True;review.render.resolution_x=1200;review.render.resolution_y=800;review.render.resolution_percentage=100;review.render.filepath=str(out/'UB_LINSEN_REVIEW.png');bpy.context.window.scene=review;bpy.ops.render.render(write_still=True,scene=review.name)
(out/'underbridge_coverage.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
report={'scene':sc.name,'coverage_segments':len(audit['segments']),'fully_verified_segments':0,'partial_streetview_segments':1,'new_mass_meshes':len(col.objects),'mesh_errors':errors,'baseline_unchanged':True,'dimensions':'Estimated, not real measured sizes','remaining':'All segments require completion; special ramps/interchanges need explicit extra coverage; Linsen partial'};(out/'checkpoint.json').write_text(json.dumps(report,indent=2))
for p in src.glob('*.py'):shutil.copy2(p,out/p.name)
bpy.context.window.scene=sc;bpy.ops.wm.save_as_mainfile(filepath=str(original_path.with_name('CIVIC_UNDERBRIDGE_WORKING_20260916.blend')));result=report
