"""Expose estimated west entrance and add observed canopy fascia, medallions and railing."""
import bpy,json,os,pathlib,math
from mathutils import Vector
root=pathlib.Path(os.environ['CIVIC_MODEL_ROOT']);out=root/'CalibrationRound3';e=json.loads((out/'jingfu_evidence.json').read_text());col=bpy.data.collections['CAL3_JINGFU_TEMPLE'];p=e['live_polygons']['roof'];can=e['live_polygons']['canopy'];x0=min(v[0] for v in p);y0=min(v[1] for v in p);origin=Vector((x0,y0,0));faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
for o in list(col.objects):
 if o.name.startswith('JINGFU_GATE_'):o.location.x-=1.1
# Keep source roof proxy; gate relocation resolves buried detail, not survey registration.
def mesh(n,vs,fs,mat):
 m=bpy.data.meshes.new(n);m.from_pydata([tuple(Vector(v)-origin) for v in vs],[],fs);m.materials.append(bpy.data.materials['JINGFU_'+mat]);m.update();o=bpy.data.objects.new(n,m);o.location=origin;col.objects.link(o);o['evidence_level']='L1';o['dimensions_status']='Estimated from source photo proportions';return o
def box(n,a,b,c,d,z,w,mat):mesh(n,[(a,c,z),(b,c,z),(b,d,z),(a,d,z),(a,c,w),(b,c,w),(b,d,w),(a,d,w)],faces,mat)
x=min(v[0] for v in can);lo=min(v[1] for v in can);hi=max(v[1] for v in can)
box('JINGFU_FRONT_FASCIA',x-.1,x+.12,lo,hi,2.62,2.96,'red')
box('JINGFU_FRONT_RAIL',x-.35,x-.29,lo+.15,hi-.15,.95,1.02,'metal')
for i in range(17):
 y=lo+.2+(hi-lo-.4)*i/16;box('JINGFU_RAIL_PICKET_'+str(i),x-.35,x-.3,y-.022,y+.022,.08,.99,'metal')
for i in range(3):
 cy=lo+(hi-lo)*(i+1)/4;cz=3.58;r=.66;vs=[(xx,cy+r*math.cos(a*math.tau/32),cz+r*math.sin(a*math.tau/32)) for xx in [x+.05,x+.17] for a in range(32)];mesh('JINGFU_SIGN_MEDALLION_EST_'+str(i),vs,[tuple(reversed(range(32))),tuple(range(32,64))]+[(a,(a+1)%32,(a+1)%32+32,a+32) for a in range(32)],'tile')
sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];cam=bpy.data.objects['JINGFU_REVIEW'];center=Vector((x0+3,(lo+max(v[1] for v in p))/2,2));cam.location=center+Vector((-24,-8,6));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();old=sc.camera;sc.camera=cam;sc.render.filepath=str(out/'JINGFU_CONTEXT_REVIEW.png');bpy.ops.render.render(write_still=True,scene=sc.name);sc.camera=old
issues=[]
for o in col.objects:
 if o.type!='MESH':continue
 counts={}
 for f in o.data.polygons:
  for k in f.edge_keys:counts[k]=counts.get(k,0)+1
 if any(v!=2 for v in counts.values()):issues.append(o.name)
r={'objects':len(col.objects),'mesh_check_issues':issues,'level':'L1','unresolved':['Unmeasured roof and ornament profiles','No interior survey','Photo sign lettering and detailed ornaments not reconstructed','Road/bridge registration remains uncertain'],'entrance_detail':'West gate moved clear of estimated body; canopy fascia, three sign discs and front rail added'};(out/'jingfu_model_check.json').write_text(json.dumps(r,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(out/'CIVIC_PHOTO_CALIBRATION_20260911.blend'));result=r
