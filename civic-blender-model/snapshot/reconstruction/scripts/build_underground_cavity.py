"""Excavate only synthetic datum in assumed pilot; retain real source geometry."""
import bpy,bmesh,json,pathlib,datetime,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934')
out=root/'UndergroundCavity';out.mkdir(exist_ok=True)
sc=bpy.data.scenes['Scene'];bpy.context.window.scene=sc
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_cavity_'+stamp+'.blend')),copy=True)
datum=bpy.data.objects['GROUND_DATUM_Z0_not_surveyed_terrain']
col=bpy.data.collections.new('UNDERGROUND_PILOT_EXCAVATION_ASSUMED');sc.collection.children.link(col)
ang=math.atan2(721.741783-731.106122,1288.333559-1128.846965)
vs=[(x*100,y*12,z) for x,y,z in [(-1,-1,-7.2),(-1,-1,.02),(-1,1,-7.2),(-1,1,.02),(1,-1,-7.2),(1,-1,.02),(1,1,-7.2),(1,1,.02)]]
me=bpy.data.meshes.new('PILOT_VOID');me.from_pydata(vs,[],[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]);me.update()
c=bpy.data.objects.new('PILOT_VOID_200x24_ASSUMED',me);col.objects.link(c);c.location=(1208.59026,726.42395,0);c.rotation_euler.z=ang;c.hide_render=True;c.display_type='WIRE';c.hide_set(True);c['evidence']='Assumed test cell; not surveyed excavation or parking footprint'
mod=datum.modifiers.new('PILOT_UNDERGROUND_VOID_ASSUMED','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=c
bpy.context.view_layer.update()
# Retain landing meshes but suppress exact coplanar duplicate where floor covers entire landing.
landings=[]
for o in bpy.data.objects:
 if not o.name.endswith('_BOTTOM_LANDING'):continue
 level=-7.2 if o.name.startswith('B1_TO_B2') else -3.6
 slabnames=['B2_SLAB'] if level<-5 else ['B1_SLAB_west','B1_SLAB_east']
 pts=[o.matrix_world@v.co for v in o.data.vertices if abs((o.matrix_world@v.co).z-level)<.01]
 contained=False
 for name in slabnames:
  slab=bpy.data.objects[name];inv=slab.matrix_world.inverted();bb=[Vector(v) for v in slab.bound_box]
  if pts and all(all(min(v[i] for v in bb)-.002 <= (inv@p)[i] <= max(v[i] for v in bb)+.002 for i in range(3)) for p in pts):contained=True
 if contained:
  o.hide_render=True;o.hide_set(True);o['suppressed_reason']='Coplanar landing fully covered by selected-level slab; geometry retained'
 landings.append({'name':o.name,'suppressed':contained})
deps=bpy.context.evaluated_depsgraph_get();e=datum.evaluated_get(deps);em=e.to_mesh()
tree=BVHTree.FromPolygons([datum.matrix_world@v.co for v in em.vertices],[list(f.vertices) for f in em.polygons]);e.to_mesh_clear()
checks=[]
for p in json.loads((root/'RampDetail/ramp_paths.json').read_text()):
 b=Vector(p['samples'][-1]);a=Vector(p['samples'][0]);d=b-a;d.z=0;d.normalize()
 hit,n,idx,dist=tree.ray_cast(b-d*2+Vector((0,0,1)),d,12)
 checks.append({'ramp':p['name'],'datum_obstruction_next_12m':list(hit) if hit is not None else None})
assert all(r['datum_obstruction_next_12m'] is None for r in checks)
# Shorten near/far ratio for close underground inspection.
for camera in bpy.data.collections['UNDERGROUND_RAMP_CAMERAS'].objects:
 camera.data.clip_start=.15;camera.data.clip_end=500
frame=sc.frame_current;oldcam=sc.camera;oldpath=sc.render.filepath
for frameid,name in [(101,'RAMP_CAM_EAST_1F_B1'),(102,'RAMP_CAM_WEST_1F_B1'),(103,'RAMP_CAM_B1_B2')]:
 sc.frame_set(frameid);sc.camera=bpy.data.objects[name];sc.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
sc.frame_set(frame);sc.camera=oldcam;sc.render.filepath=oldpath
file=out/('CIVIC_UNDERGROUND_CAVITY_'+stamp+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file))
result={'file':str(file),'datum_void_m':[200,24,7.22],'landings':landings,'datum_rays':checks,'limitations':'Assumed pilot envelope only. No real pier moved. No surveyed geometry or structural/traffic clearance approval. Existing seven pier conflicts remain.'}
(out/'cavity_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
