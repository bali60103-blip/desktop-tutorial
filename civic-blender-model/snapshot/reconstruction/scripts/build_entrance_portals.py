"""Model two Zhonglin height-limit portals: 1.8m from OSM, placement/shape estimated."""
import bpy,bmesh,json,pathlib,datetime
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'EntrancePortals';out.mkdir(exist_ok=True)
sc=bpy.data.scenes['Scene'];bpy.context.window.scene=sc;s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_portals_'+s+'.blend')),copy=True)
col=bpy.data.collections.new('ZHONGLIN_HEIGHT_LIMIT_PORTALS_ESTIMATED');sc.collection.children.link(col)
def material(name,c):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.diffuse_color=(*c,1);return m
yellow=material('PORTAL_YELLOW',(.95,.6,.04));black=material('PORTAL_BLACK',(.035,.035,.035))
def box(name,loc,dims,angle,mat):
 bm=bmesh.new();bmesh.ops.create_cube(bm,size=1);me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();me.materials.append(mat);o=bpy.data.objects.new(name,me);col.objects.link(o);o.location=loc;o.rotation_euler.z=angle;o.scale=dims;o['status']='Estimated shape and placement; 1.8m limit sourced from OSM entrance tag, not clearance survey';return o
rows=[]
import math
for p in json.loads((root/'RampDetail/ramp_paths.json').read_text()):
 if '0_TO_B1' not in p['name']:continue
 a,b=Vector(p['samples'][0]),Vector(p['samples'][-1]);d=b-a;d.z=0;d.normalize();side=Vector((-d.y,d.x,0));angle=math.atan2(d.y,d.x)
 # Place before ramp top so the portal doesn't consume the sloping ramp width.
 center=a-d*1.5
 for sign in [-1,1]:
  box(p['name']+'_LIMIT_POST',center+side*(sign*2.2)+Vector((0,0,1.05)),(.12,.12,2.1),angle,yellow)
  box(p['name']+'_LIMIT_BASE',center+side*(sign*2.2)+Vector((0,0,.04)),(.35,.35,.08),angle,black)
 box(p['name']+'_LIMIT_BEAM',center+Vector((0,0,1.95)),(.16,4.52,.30),angle,yellow)
 for j in range(9):
  box(p['name']+'_LIMIT_STRIPE',center+side*(-2+j*.5)+Vector((0,0,1.951)),(.165,.20,.302),angle,black)
 rows.append({'ramp':p['name'],'placement_before_top_m':1.5,'beam_bottom_z':1.8,'clear_between_posts_m':4.28,'evidence':'OSM entrance height limit 1.8m; official plan inventory two freestanding portals; exact location and shape assumed'})
for frame,name in [(101,'RAMP_CAM_EAST_1F_B1'),(102,'RAMP_CAM_WEST_1F_B1')]:
 sc.frame_set(frame);sc.camera=bpy.data.objects[name];sc.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
file=out/('CIVIC_ENTRANCE_PORTALS_'+s+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file))
result={'file':str(file),'portal_count':2,'mesh_count':len(col.objects),'portals':rows,'limitations':'Portal location and structural sizes assumed; not full vehicle clearance certification. Pier conflicts unresolved.'};(out/'portal_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
