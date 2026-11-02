"""One visually tracked portal; approximate image-ray XY, not surveyed dimensions."""
import bpy,os,json,pathlib,datetime,math,collections
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'PriorityNodes_20260914';main=bpy.context.window.scene
assert not bpy.data.collections.get('P1_XINSHENG_OBSERVED_PORTAL_01')
bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_OBSERVED_PORTAL_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True)
# Approximate ray intersections: screen width538, horizontal FOV75, yaw270.
# Two same-date panoramas; manual pillar center pixels are not survey observations.
A=(303481.4433214655,2770997.3145974344);B=(303480.2650249761,2771010.400697088)
root=out.parent;reg=json.load(open(root/'registration.json'));origin=reg['origin_epsg3826'];t=reg['live_to_twd97'];ang=math.radians(t['rotation_degrees']);c=math.cos(ang);s=math.sin(ang)
def live(p):
 x=p[0]-origin[0]-t['translation'][0];y=p[1]-origin[1]-t['translation'][1];return Vector(((c*x+s*y)/t['scale'],(-s*x+c*y)/t['scale'],0))
a,b=live(A),live(B);across=(b-a).normalized();along=Vector((across.y,-across.x,0));mid=(a+b)/2
col=bpy.data.collections.new('P1_XINSHENG_OBSERVED_PORTAL_01');col.use_fake_user=True
sc=bpy.data.scenes.new('P1_PORTAL_PHOTO_PROPORTION_REVIEW');sc.use_fake_user=True;sc.collection.children.link(col)
mat=bpy.data.materials.new('P1_PORTAL_PHOTO_WHITE');mat.diffuse_color=(.72,.73,.69,1)
def box(name,center,wx,wy,z0,z1):
 v=[center+along*x+across*y+Vector((0,0,z)) for z in (z0,z1) for x,y in [(-wx/2,-wy/2),(wx/2,-wy/2),(wx/2,wy/2),(-wx/2,wy/2)]]
 me=bpy.data.meshes.new(name);me.from_pydata([p-mid for p in v],[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);me.materials.append(mat);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);o.location=mid;o['status']='Visible rectangular portal form; XY approximate two-view ray intersection; all dimensions estimated';return o
for label,p in [('S',a),('N',b)]:
 box('P1_OBSERVED_PORTAL_COLUMN_'+label,p,2,1.8,0,10.5)
box('P1_OBSERVED_PORTAL_CROSSBEAM',mid,2,(b-a).length+1.8,10.5,12)
# Render only evidence geometry: no implication of validated mainline integration.
cd=bpy.data.cameras.new('P1_PORTAL_REVIEW');cam=bpy.data.objects.new(cd.name,cd);sc.collection.objects.link(cam);cam.location=mid+along*28+Vector((0,0,7));cam.rotation_euler=(mid+Vector((0,0,6))-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=23;sc.camera=cam;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='MATERIAL';sc.render.resolution_x=1000;sc.render.resolution_y=800;sc.render.resolution_percentage=100;sc.render.filepath=str(out/'P1_OBSERVED_PORTAL_01.png')
bpy.context.window.scene=sc;sc.view_layers[0].update();errors=[]
for o in col.objects:
 ec=collections.Counter(tuple(sorted(e)) for p in o.data.polygons for e in p.edge_keys)
 if any(n!=2 for n in ec.values()):errors.append(o.name)
assert not errors
bpy.ops.render.render(write_still=True,scene=sc.name)
report={'source_panoramas':[{'id':'3QqW5-St5dq9zaCpfhdbbw','lat':25.0461501,'lon':121.5303078,'south_pixel_x':309,'north_pixel_x':463},{'id':'LyDE7zKTZ6cDVJfCjJg6jg','lat':25.0461762,'lon':121.5302139,'south_pixel_x':276,'north_pixel_x':505}],'imagery_date':'2025-02','method':'Manual same-pillar pixel centers; yaw270, approximate horizontal FOV75, viewport538; ray intersection in EPSG3826, then inverse registration. Lens, yaw, panorama positional errors not solved.','pillar_xy':[list(a),list(b)],'center_spacing_m':(b-a).length,'dimension_assumptions':{'column_along':2,'column_across':1.8,'crossbeam_bottom':10.5,'crossbeam_top':12,'ground':0},'geometry_meshes':3,'closed_mesh_errors':errors,'status':'Isolated photo-proportion study. Not linked into main/ramp scene.','conflict':'Current mainline z8 conflicts with this provisional photo-proportion height. Need joint deck/portal calibration before integration.','unmodeled':'Bearing pads are not clearly resolved in imagery; no pads invented. Other visible portals not equidistantly generated.'}
(out/'xinsheng_observed_portal_report.json').write_text(json.dumps(report,indent=2));bpy.context.window.scene=main;bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result=report
