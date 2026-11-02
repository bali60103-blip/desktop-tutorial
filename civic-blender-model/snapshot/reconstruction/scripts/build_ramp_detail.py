"""Selected-depth ramp work model: smooth end grades, side curbs/walls, drainage grates,
reversible ground apertures and structural connection audit. All detail dimensions assumed.
"""
import bpy,bmesh,json,pathlib,math,datetime
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=pathlib.Path(ROOT);root.mkdir(exist_ok=True);sc=bpy.context.scene;stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(root/('before_ramp_detail_'+stamp+'.blend')),copy=True)
ug=bpy.data.collections['WORKSHEET04_B_DEPTH__ASSUMED_PILOT_CELL'];name='WORKSHEET04_RAMP_DETAIL_ASSUMED';col=bpy.data.collections.get(name)
if col:
 for o in list(col.objects):bpy.data.objects.remove(o,do_unlink=True)
 bpy.data.collections.remove(col)
col=bpy.data.collections.new(name);sc.collection.children.link(col)
section=bpy.data.scenes['STAGE04_B_SELECTED_OPEN_SECTION'];section.collection.children.link(col)
def mat(name,c):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.diffuse_color=(*c,1);return m
concrete=mat('RAMP_CONCRETE',(.52,.55,.58));asphalt=mat('RAMP_FINISH',(.2,.25,.29));metal=mat('RAMP_GRATE',(.08,.1,.12));yellow=mat('RAMP_EDGE_LINE',(.95,.65,.08))
def mesh(name,vs,fs,m):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(m);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);o['status']='ESTIMATED WORK MODEL - not as-built or code approved';return o

def sweep(name,samples,side,lo,hi,bottom,top,m):
 vs=[];fs=[]
 for p in samples:vs.extend([p+side*lo+Vector((0,0,bottom)),p+side*hi+Vector((0,0,bottom)),p+side*hi+Vector((0,0,top)),p+side*lo+Vector((0,0,top))])
 for i in range(len(samples)-1):
  a=i*4;b=a+4
  fs.extend([(a,b,b+1,a+1),(a+1,b+1,b+2,a+2),(a+2,b+2,b+3,a+3),(a+3,b+3,b,a)])
 fs.extend([(3,2,1,0),tuple(range(len(vs)-4,len(vs)))]);return mesh(name,vs,fs,m)
checks=[];cutters=[];paths=[]
for name in ['EAST_0_TO_B1_ASSUMED','WEST_0_TO_B1_ASSUMED','B1_TO_B2_TEST_RAMP']:
 old=bpy.data.objects[name];points=[old.matrix_world@v.co for v in old.data.vertices][:4];a=(points[0]+points[1])/2;b=(points[2]+points[3])/2;vector=b-a;length=math.hypot(vector.x,vector.y);along=Vector((vector.x/length,vector.y/length,0));side=Vector((-along.y,along.x,0));transition=3.;g=(b.z-a.z)/(length-transition)
 def dz(s):
  if s<transition:return g*s*s/(2*transition)
  if s>length-transition:return (b.z-a.z)-g*(length-s)**2/(2*transition)
  return g*(s-transition/2)
 count=math.ceil(length/.25);samples=[a+along*(length*i/count)+Vector((0,0,dz(length*i/count))) for i in range(count+1)]
 old.hide_render=True;old.hide_set(True);old['replaced_by_detail']=True
 surf=sweep(name+'_PROFILE',samples,side,-1.75,1.75,-.25,0,asphalt)
 for sign in [-1,1]:
  lo,hi=sorted([sign*1.75,sign*1.90]);sweep(name+f'_CURB_{sign}',samples,side,lo,hi,-.25,.15,concrete)
  # Retaining edge/wall is kept outside the 3.5m usable ramp width.
  lo,hi=sorted([sign*1.90,sign*2.05]);sweep(name+f'_WALL_{sign}',samples,side,lo,hi,-.25,.90,concrete)
  lo,hi=sorted([sign*1.58,sign*1.68]);sweep(name+f'_LINE_{sign}',samples,side,lo,hi,.002,.006,yellow)
 for end,dist in [('TOP',.6),('BOTTOM',length-.6)]:
  for i in range(32):
   # Short bars across a 0.3m channel; appearance only, drain hydraulics not modeled.
   q=a+along*dist+side*(-1.55+i*.1)+Vector((0,0,dz(dist)+.006));sweep(name+'_GRATE_'+end+str(i),[q-along*.15,q+along*.15],side,-.025,.025,-.02,0,metal)
 # Horizontal bottom landing blends at the selected level; extension is an assumption.
 sweep(name+'_BOTTOM_LANDING',[b,b+along*3],side,-1.75,1.75,-.25,0,asphalt)
 if '0_TO_B1' in name:
  # Start cut after a short lip; slab still carries the very first near-flat ramp portion.
  pts=[a+along*.25,b+along*2.5];pts=[Vector((p.x,p.y,0)) for p in pts]
  cutter=sweep(name+'_APERTURE_CUTTER',pts,side,-2.06,2.06,-10,1,metal);cutter.hide_render=True;cutter.display_type='WIRE';cutter.hide_set(True);cutters.append(cutter)
 checks.append({'ramp':name,'length_m':length,'rise_m':b.z-a.z,'transition_length_each_m':transition,'maximum_grade':abs(g),'start_z':samples[0].z,'end_z':samples[-1].z,'endpoint_error_m':(samples[-1]-b).length,'landing_extension_m':3,'clear_width_m':3.5,'outer_width_m':4.1,'limitations':'No surveyed profile, turning envelope, waterproofing or hydraulic design; clearance must be checked separately.'})
 paths.append({'name':name,'samples':[list(p) for p in samples]})
# Reversible booleans: keep unmodified mesh copy on each object and leave modifiers unapplied.
cut_records=[]
for name in ['GROUND_ROADS_OFFICIAL_XY','GROUND_MEDIAN_WORKING_ESTIMATED','GROUND_DATUM_Z0_not_surveyed_terrain']:
 o=bpy.data.objects.get(name)
 if not o:continue
 before=len(o.data.polygons)
 for cutter in cutters:
  mod=o.modifiers.new('RAMP_APERTURE_ESTIMATED','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
 evaluated=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=evaluated.to_mesh();after=len(me.polygons);evaluated.to_mesh_clear();cut_records.append({'object':name,'base_faces':before,'evaluated_faces':after,'status':'Unapplied modifiers; source mesh preserved. Face-count change does not alone verify opening.'})
# Inspect actual modeled girder underside at each retained cap center, using downward rays.
vs=[];fs=[]
for o in bpy.data.collections['06_Steel_girders_estimated'].objects:
 off=len(vs);vs.extend([o.matrix_world@v.co for v in o.data.vertices]);fs.extend([[i+off for i in f.vertices] for f in o.data.polygons])
bvh=BVHTree.FromPolygons(vs,fs);support=[]
for o in bpy.data.collections['07_Piers_legacy_UNVERIFIED'].objects:
 if '_CAP_' not in o.name or o.hide_render:continue
 pts=[o.matrix_world@Vector(p) for p in o.bound_box];x=(min(p.x for p in pts)+max(p.x for p in pts))/2;y=(min(p.y for p in pts)+max(p.y for p in pts))/2;zt=max(p.z for p in pts)
 hit,no,idx,dist=bvh.ray_cast(Vector((x,y,zt-1)),Vector((0,0,1)),5)
 support.append({'cap':o.name,'sample_xy':[x,y],'cap_top':zt,'girder_underside_z':hit.z if hit is not None else None,'vertical_space_for_bearing_m':hit.z-zt if hit is not None else None,'status':'Do not insert bearing without available gap or redesign; one sample cannot verify full contact'})
qa=[]
for o in col.objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);bm.to_mesh(o.data);bm.free();qa.append({'object':o.name,'nonmanifold_edges':bad})
assert all(q['nonmanifold_edges']==0 for q in qa)
# Render independent section scene so main-scene 500m markers cannot override the camera.
cam=section.camera;cam.location=(1208,670,5);cam.rotation_euler=(Vector((1208,726,-4))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=65;section.render.resolution_x=1800;section.render.resolution_y=1000;section.render.filepath=str(root/'ramp_transition_section.png');bpy.ops.render.render(write_still=True,scene=section.name)
bpy.context.window.scene=sc;file=root/('CIVIC_RAMP_DETAIL_'+stamp+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));result={'file':str(file),'ramps':checks,'ground_apertures':cut_records,'mesh_count':len(qa),'nonmanifold_edges':sum(q['nonmanifold_edges'] for q in qa),'support_samples':support,'camera_count':len(bpy.data.collections['CIVIC_CAMERAS_500M_NORTH_SOUTH'].objects),'status':'Working model. Ground openings and profile hypotheses need evidence; original pier positions retained; B/C not passed'};(root/'ramp_detail_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(root/'ramp_paths.json').write_text(json.dumps(paths));result={k:v for k,v in result.items() if k!='support_samples'}
