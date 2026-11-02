"""L1 roof-outline proxy with photo-informed western gate and canopy; no survey claim."""
import bpy,json,pathlib,math,os
from mathutils import Vector
root=pathlib.Path(os.environ['CIVIC_MODEL_ROOT']);out=root/'CalibrationRound3'
e=json.loads((out/'jingfu_evidence.json').read_text());sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING']
if bpy.data.collections.get('CAL3_JINGFU_TEMPLE'):raise RuntimeError('Already built; inspect existing collection before replacing')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'BEFORE_JINGFU.blend'))
col=bpy.data.collections.new('CAL3_JINGFU_TEMPLE');sc.collection.children.link(col)
poly=e['live_polygons']['roof'];origin=Vector((sum(p[0] for p in poly)/len(poly),sum(p[1] for p in poly)/len(poly),0))
mats={}
for n,c in [('wall',(.62,.43,.29,1)),('tile',(.47,.19,.09,1)),('red',(.65,.06,.035,1)),('gold',(.78,.53,.14,1)),('dark',(.09,.07,.06,1)),('metal',(.38,.4,.41,1))]:
 m=bpy.data.materials.new('JINGFU_'+n);m.diffuse_color=c;mats[n]=m
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def mesh(name,vs,fs,mat):
 m=bpy.data.meshes.new(name);m.from_pydata([tuple(Vector(v)-origin) for v in vs],[],fs);m.materials.append(mats[mat]);m.update();o=bpy.data.objects.new(name,m);o.location=origin;col.objects.link(o);o['evidence_level']='L1';o['dimensions_status']='ESTIMATED: roof trace and photo proportions; no survey';o['source_record']='jingfu_evidence.json';return o
def box(n,x0,x1,y0,y1,z0,z1,mat):return mesh(n,[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],faces,mat)
def prism(n,p,z0,z1,mat):
 k=len(p);return mesh(n,[(x,y,z) for z in [z0,z1] for x,y in p],[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)],mat)
prism('JINGFU_ROOF_OUTLINE_BODY_EST',poly,.12,3.4,'wall');prism('JINGFU_ROOF_OUTLINE_EAVE_EST',poly,3.4,3.6,'tile')
# Separate north and south roof strips follow traced visible lobes. Curved eave profile inferred.
x0=min(p[0] for p in poly);x1=max(p[0] for p in poly);y0=min(p[1] for p in poly);y1=max(p[1] for p in poly)
def roof(n,a,b,c,d,base,ridge):
 profile=[(a,base+.15),(a+(b-a)*.15,base),(a+(b-a)*.5,ridge),(a+(b-a)*.85,base),(b,base+.15)]
 vs=[(x,y,z+dz) for dz in [-.14,0] for y in [c,d] for x,z in profile];fs=[]
 for k in range(4):fs.extend([(k,k+1,6+k,5+k),(10+k,15+k,16+k,11+k)])
 fs.extend([(0,5,15,10),(4,14,19,9),tuple(list(range(5))+list(reversed(range(10,15)))),tuple(list(range(5,10))+list(reversed(range(15,20))))]);mesh(n,vs,fs,'tile')
roof('JINGFU_CURVED_ROOF_PROXY',x0+.3,x1-.3,y0+.3,(y0+y1)/2,3.7,5.0)
roof('JINGFU_NORTH_ROOF_PROXY',x0+4,x1-.2,(y0+y1)/2,y1-.2,3.7,4.8)
can=e['live_polygons']['canopy'];prism('JINGFU_CANOPY_EST',can,2.65,2.82,'red')
for i,(x,y) in enumerate(can):box('JINGFU_CANOPY_POST_'+str(i),x-.07,x+.07,y-.07,y+.07,.05,2.65,'metal')
# West-facing gateway approximated, not an exact ornament reconstruction.
gy=y0+2.2;gx=x0+.45
for i,dy in enumerate([-1.55,1.55]):box('JINGFU_GATE_POST_'+str(i),gx-.2,gx+.2,gy+dy-.2,gy+dy+.2,0,3.1,'red')
box('JINGFU_GATE_LINTEL',gx-.28,gx+.28,gy-1.8,gy+1.8,2.65,3.12,'gold');box('JINGFU_GATE_RECESS',gx+.3,gx+.36,gy-1.2,gy+1.2,.15,2.65,'dark')
roof('JINGFU_GATE_ROOF_EST',gx-.7,gx+.8,gy-2.05,gy+2.05,3.15,3.75)
# Small red lantern proxies under the south canopy. No sign or commercial-photo reproduction.
for i in range(5):
 cx=min(p[0] for p in can)+.4;cy=min(p[1] for p in can)+.7+i*1.0
 verts=[(cx+.18*math.cos(a*math.tau/12),cy+.18*math.sin(a*math.tau/12),z) for z in [2.15,2.5] for a in range(12)]
 mesh('JINGFU_LANTERN_PROXY_'+str(i),verts,[tuple(reversed(range(12))),tuple(range(12,24))]+[(a,(a+1)%12,(a+1)%12+12,a+12) for a in range(12)],'red')
issues=[]
for o in col.objects:
 edgecounts={}
 for f in o.data.polygons:
  for key in f.edge_keys:edgecounts[key]=edgecounts.get(key,0)+1
 if any(v!=2 for v in edgecounts.values()):issues.append({'object':o.name,'issue':'nonmanifold edge count'})
 if any(not math.isfinite(v) for p in o.data.vertices for v in p.co):issues.append({'object':o.name,'issue':'nonfinite'})
camdata=bpy.data.cameras.new('JINGFU_REVIEW');cam=bpy.data.objects.new('JINGFU_REVIEW',camdata);col.objects.link(cam);cam.location=origin+Vector((-24,-16,12));cam.rotation_euler=(origin+Vector((0,0,2))-cam.location).to_track_quat('-Z','Y').to_euler();camdata.lens=40
oldcam=sc.camera;sc.camera=cam;sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=1280;sc.render.resolution_y=800;sc.render.resolution_percentage=100;sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.render.image_settings.file_format='PNG';sc.render.filepath=str(out/'JINGFU_CONTEXT_REVIEW.png');bpy.ops.render.render(write_still=True,scene=sc.name);sc.camera=oldcam
r={'objects':len(col.objects),'mesh_check_issues':issues,'status':'L1 estimated model; contextual visual review and registration uncertainty remain','origin':list(origin)};(out/'jingfu_model_check.json').write_text(json.dumps(r,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(out/'CIVIC_PHOTO_CALIBRATION_20260911.blend'));result=r
