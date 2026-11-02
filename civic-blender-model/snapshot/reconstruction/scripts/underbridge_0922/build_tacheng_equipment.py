import bpy,json,pathlib,math,collections
from mathutils import Vector
sc=bpy.data.scenes['CIVIC_UNDERBRIDGE_MASSING_20260916'];prev=bpy.context.window.scene;out=pathlib.Path(bpy.data.filepath).parent/'Underbridge_20260922';out.mkdir(exist_ok=True)
assert not bpy.data.collections.get('UB_TACHENG_EQUIPMENT_PHOTO_EST')
col=bpy.data.collections.new('UB_TACHENG_EQUIPMENT_PHOTO_EST');sc.collection.children.link(col)
a=math.radians(-11);u=Vector((math.cos(a),math.sin(a),0));n=Vector((-math.sin(a),math.cos(a),0));base=Vector((49,955.5,0));mats={}
for k,c in [('CONCRETE',(.48,.48,.43,1)),('TOWER',(.16,.18,.18,1)),('EQUIPMENT',(.43,.44,.38,1)),('ROOF',(.18,.25,.18,1)),('LOUVRE',(.25,.27,.25,1))]:
 m=bpy.data.materials.new('UB_TACHENG_'+k);m.diffuse_color=c;mats[k]=m
names=[]
def make(name,vs,faces,mat):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],faces);me.materials.append(mats[mat]);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);o.location=base;o['source_pano']='m8uPsNjtR14tfM0vA6DBXA';o['evidence_date']='2025-02';o['confidence']='Observed morphology; position and all metric dimensions estimated';o['review_segment']='UB_X+000';names.append(o.name);return o
def xyz(x,y,z):return tuple(u*x+n*y+Vector((0,0,z)))
def box(name,c,d,mat):
 vs=[xyz(c[0]+x*d[0]/2,c[1]+y*d[1]/2,c[2]+z*d[2]/2) for z in [-1,1] for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]];return make(name,vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)
box('UB_TACHENG_ROW_PLINTH_EST',(0,0,.75),(15.6,3,1.2),'CONCRETE')
for i in range(4):
 x=-5.85+i*3.9;box('UB_TACHENG_HOUSING_%d_EST'%i,(x,0,2.1),(3.8,2.8,1.5),'EQUIPMENT')
 vs=[xyz(x+dx,y,z) for dx,y,z in [(-2,-1.6,2.85),(2,-1.6,2.85),(2,1.6,2.85),(-2,1.6,2.85),(-.4,0,3.3),(.4,0,3.3)]]
 make('UB_TACHENG_HIP_CAP_%d_EST'%i,vs,[(0,3,2,1),(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)],'ROOF')
 for j in [-1,1]:box('UB_TACHENG_LOUVRE_%d_%d_EST'%(i,j),(x+j*.9,1.415,2.15),(1.4,.04,.95),'LOUVRE')
box('UB_TACHENG_TOWER_PLINTH_EST',(12.4,1.5,.3),(6.7,6.7,.3),'CONCRETE')
box('UB_TACHENG_LOUVRED_TOWER_MASS_EST',(12.4,1.5,3.825),(6.4,6.4,6.75),'TOWER')
box('UB_TACHENG_SERVICE_LANDING_EST',(0,3,.45),(3.6,2.6,.6),'CONCRETE')
box('UB_TACHENG_SERVICE_STEP_1_EST',(0,4.7,.225),(3.6,.6,.15),'CONCRETE')
box('UB_TACHENG_SERVICE_STEP_2_EST',(0,4.1,.3),(3.6,.6,.3),'CONCRETE')
bpy.context.window.scene=sc;sc.view_layers[0].update();errors=[]
for o in col.objects:
 ec=collections.Counter(tuple(sorted(e)) for f in o.data.polygons for e in f.edge_keys)
 if any(v!=2 for v in ec.values()):errors.append(o.name)
assert not errors
# Mesh-level overlap test against existing structures, not a comprehensive clearance test.
from mathutils.bvhtree import BVHTree
hits=[]
for o in col.objects:
 ov=[o.matrix_world@v.co for v in o.data.vertices];ob=BVHTree.FromPolygons(ov,[list(f.vertices) for f in o.data.polygons])
 for q in sc.objects:
  if q.type!='MESH' or not q.name.startswith(('DECK_','UNVERIFIED_Pier_')):continue
  bb=[q.matrix_world@Vector(v) for v in q.bound_box]
  if any(max(v[k] for v in ov)<min(v[k] for v in bb) or min(v[k] for v in ov)>max(v[k] for v in bb) for k in range(3)):continue
  qb=BVHTree.FromPolygons([q.matrix_world@v.co for v in q.data.vertices],[list(f.vertices) for f in q.data.polygons]);pairs=ob.overlap(qb)
  if pairs:hits.append({'new':o.name,'existing':q.name,'triangle_pairs':len(pairs)})
# Isolated assembly QA, without modifying animation or original scene geometry.
review=bpy.data.scenes.new('UB_TACHENG_EQUIPMENT_REVIEW');review.use_fake_user=True;review.collection.children.link(col);cd=bpy.data.cameras.new('UB_TACHENG_REVIEW_CAMERA');cam=bpy.data.objects.new(cd.name,cd);review.collection.objects.link(cam);cam.location=base+n*35+u*10+Vector((0,0,10));cam.rotation_euler=(base+u*4+Vector((0,0,2.5))-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=32;review.camera=cam;review.render.engine='BLENDER_WORKBENCH';review.display.shading.color_type='MATERIAL';review.display.shading.show_cavity=True;review.render.resolution_x=1200;review.render.resolution_y=800;review.render.resolution_percentage=100;review.render.filepath=str(out/'TACHENG_EQUIPMENT_MASSING.png');bpy.context.window.scene=review;bpy.ops.render.render(write_still=True,scene=review.name)
if hits:
 sc.collection.children.unlink(col)
 for o in col.objects:o['adoption']='Review only due structural intersection'
r={'objects':names,'mesh_errors':errors,'structural_intersections':hits,'adopted_as_estimated_working_mass':not bool(hits),'dimensions_verified':False,'source_url':'https://www.google.com/maps/@25.0502083,121.5109346,3a,90y,192h,90t/data=!3m4!1e1!3m2!1sm8uPsNjtR14tfM0vA6DBXA!2e0','assumptions':{'equipment_row_length':15.6,'equipment_top':3.3,'tower_width_depth':6.4,'tower_top':7.2,'position':'Visual placement relative panorama, not triangulated'},'remaining':['Actual XY and dimensions','Road/sidewalk footprint clearance','Equipment function and exact count','Tower top is obscured in source photo']};(out/'tacheng_equipment_report.json').write_text(json.dumps(r,indent=2));bpy.context.window.scene=prev;bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result=r
