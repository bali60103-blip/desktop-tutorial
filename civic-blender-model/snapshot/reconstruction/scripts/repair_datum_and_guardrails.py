"""Repair synthetic datum rendering and add assumed B1 opening guardrails."""
import bpy,bmesh,json,pathlib,datetime,math
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'UndergroundCavity';out.mkdir(exist_ok=True)
sc=bpy.data.scenes['Scene'];bpy.context.window.scene=sc
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_guardrails_'+stamp+'.blend')),copy=True)
datum=bpy.data.objects['GROUND_DATUM_Z0_not_surveyed_terrain']
datum.hide_render=True;datum.hide_set(True);datum['render_correction']='Synthetic single-face reference datum, not terrain; render visibility now matches viewport. Its booleans produced spurious vertical faces.'
for m in datum.modifiers:
 if m.name=='PILOT_UNDERGROUND_VOID_ASSUMED':m.show_viewport=False;m.show_render=False
col=bpy.data.collections.new('B1_OPENING_GUARDRAILS_ASSUMED');sc.collection.children.link(col)
mat=bpy.data.materials.get('PILOT_GUARDRAIL_YELLOW') or bpy.data.materials.new('PILOT_GUARDRAIL_YELLOW');mat.diffuse_color=(.95,.55,.06,1)
ang=math.atan2(721.741783-731.106122,1288.333559-1128.846965);v=Vector((math.cos(ang),math.sin(ang),0));n=Vector((-v.y,v.x,0));center=Vector((1208.59026,726.42395,-3.6))
def box(name,x,y,z,dx,dy,dz):
 bm=bmesh.new();bmesh.ops.create_cube(bm,size=1);me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free()
 o=bpy.data.objects.new(name,me);col.objects.link(o);o.location=center+v*x+n*y+Vector((0,0,z));o.rotation_euler.z=ang;o.scale=(dx,dy,dz);me.materials.append(mat);o['status']='Assumed pilot guardrail, not as-built or code approval'
for sign in [-1,1]:
 for i in range(19):box('B1_GUARD_POST',-18+i*2,sign*2.3,.55,.08,.08,1.1)
 for z in [.55,1.06]:box('B1_GUARD_RAIL',0,sign*2.3,z,36,.06,.06)
# All three landing tops are already covered by floor slabs; confirm previous suppression.
landings=[{'name':o.name,'hidden':o.hide_render} for o in bpy.data.objects if o.name.endswith('_BOTTOM_LANDING')]
qa=[]
for o in col.objects:
 bm=bmesh.new();bm.from_mesh(o.data);qa.append(sum(not e.is_manifold for e in bm.edges));bm.free()
assert max(qa)==0
for camera in bpy.data.collections['UNDERGROUND_RAMP_CAMERAS'].objects:camera.data.clip_start=.15;camera.data.clip_end=500
frame=sc.frame_current;oldcam=sc.camera;oldpath=sc.render.filepath
for frameid,name in [(101,'RAMP_CAM_EAST_1F_B1'),(102,'RAMP_CAM_WEST_1F_B1'),(103,'RAMP_CAM_B1_B2')]:
 sc.frame_set(frameid);sc.camera=bpy.data.objects[name];sc.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
sc.frame_set(frame);sc.camera=oldcam;sc.render.filepath=oldpath
file=out/('CIVIC_UNDERGROUND_GUARDRAILS_'+stamp+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file))
result={'file':str(file),'datum_render_visible':False,'guardrail_meshes':len(qa),'nonmanifold_edges':sum(qa),'guardrail_height_m':1.1,'post_spacing_m':2,'landings':landings,'limitations':'Assumed 200x24 pilot. Datum hidden is a reference-display correction, not real excavation. No pier moved; seven conflicts remain. No street-view or satellite geometry correction claimed.'}
(out/'cavity_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
