"""User-selected retaining wall extension. All heights are working assumptions."""
import bpy,bmesh,json,pathlib,datetime
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'RampRetainingWalls';out.mkdir(exist_ok=True)
sc=bpy.data.scenes['Scene'];bpy.context.window.scene=sc;stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_retaining_'+stamp+'.blend')),copy=True)
col=bpy.data.collections.new('RAMP_RETAINING_WALLS_ASSUMED');sc.collection.children.link(col)
mat=bpy.data.materials.get('RAMP_CONCRETE')
rows=[]
for path in json.loads((root/'RampDetail/ramp_paths.json').read_text()):
 if '0_TO_B1' not in path['name']:continue
 points=[Vector(p) for p in path['samples']];d=points[-1]-points[0];d.z=0;d.normalize();side=Vector((-d.y,d.x,0))
 for sign in [-1,1]:
  lo,hi=sorted([sign*1.90,sign*2.05]);vs=[];fs=[]
  for p in points:
   bottom=p.z-.25;top=max(p.z+.9,-.14)
   vs.extend([(p.x+side.x*lo,p.y+side.y*lo,bottom),(p.x+side.x*hi,p.y+side.y*hi,bottom),(p.x+side.x*hi,p.y+side.y*hi,top),(p.x+side.x*lo,p.y+side.y*lo,top)])
  for i in range(len(points)-1):
   a=i*4;b=a+4;fs.extend([(a,b,b+1,a+1),(a+1,b+1,b+2,a+2),(a+2,b+2,b+3,a+3),(a+3,b+3,b,a)])
  fs.extend([(3,2,1,0),tuple(range(len(vs)-4,len(vs)))])
  name=path['name']+'_RETAINING_'+str(sign);me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
  bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume();bm.to_mesh(me);bm.free();assert bad==0 and volume>0
  o=bpy.data.objects.new(name,me);col.objects.link(o)
  if mat:me.materials.append(mat)
  o['status']='User-selected estimated retaining wall, not surveyed or structural design'
  o['assumed_ground_underside_m']=-.14;o['thickness_m']=.15
  old=bpy.data.objects[path['name']+'_WALL_'+str(sign)];old.hide_render=True;old.hide_set(True);old['replaced_by']=name
  rows.append({'name':name,'nonmanifold_edges':bad,'volume_m3':volume,'bottom_z_min':min(p.z for p in points)-.25,'top_at_bottom_end_m':max(points[-1].z+.9,-.14),'inner_offset_m':1.9,'thickness_m':.15})
# Link new walls into existing detail scenes so section previews remain consistent.
for name in ['RAMP_ENTRANCE_DETAIL_REVIEW','STAGE04_B_SELECTED_OPEN_SECTION']:
 scene=bpy.data.scenes.get(name)
 if scene and col.name not in scene.collection.children:scene.collection.children.link(col)
oldframe=sc.frame_current;oldcam=sc.camera;oldpath=sc.render.filepath
for frame,name in [(101,'RAMP_CAM_EAST_1F_B1'),(102,'RAMP_CAM_WEST_1F_B1')]:
 sc.frame_set(frame);sc.camera=bpy.data.objects[name];sc.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
sc.frame_set(oldframe);sc.camera=oldcam;sc.render.filepath=oldpath
file=out/('CIVIC_RETAINING_WALLS_'+stamp+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file))
result={'file':str(file),'new_walls':rows,'ramp_usable_width_m':3.5,'original_walls_retained_hidden':4,'piers_moved':0,'limitations':'Ground underside -0.14m, wall thickness .15m and original ramp profile are assumptions. Not structural design. West pier conflict remains. B1-B2 walls unchanged.'}
(out/'retaining_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
