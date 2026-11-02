"""User-selected comparison only: cap top -0.20m, fixed cap bottom/pier/deck, bearing stacks.
Sampled girder intersections guide positions, not as-built bearing schedules.
"""
import bpy,bmesh,json,pathlib,datetime,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=pathlib.Path(ROOT);root.mkdir(exist_ok=True);sc=bpy.context.scene;stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(root/('before_bearing_'+stamp+'.blend')),copy=True)
name='STAGE05_BEARING_COMPARISON_ASSUMED';old=bpy.data.scenes.get(name)
if old:bpy.data.scenes.remove(old)
oldcol=bpy.data.collections.get('BEARING_OPTION_CAP_MINUS_020')
if oldcol:
 for o in list(oldcol.objects):bpy.data.objects.remove(o,do_unlink=True)
 bpy.data.collections.remove(oldcol)
scene=bpy.data.scenes.new(name);scene.world=sc.world;col=bpy.data.collections.new('BEARING_OPTION_CAP_MINUS_020');scene.collection.children.link(col)
for n in ['04_Elevated_deck_estimated','05_Parapets_estimated','06_Steel_girders_estimated','GROUND_FULL_01_OFFICIAL_AND_ESTIMATED','GROUND_FULL_02_CROSSINGS_AND_RAMPS_ESTIMATED']:scene.collection.children.link(bpy.data.collections[n])
source=bpy.data.collections['07_Piers_legacy_UNVERIFIED']
for o in source.objects:
 if '_CAP_' not in o.name:scene.collection.objects.link(o)
def material(name,color):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
concrete=material('OPTION_LOWERED_CAP',(.5,.6,.68));steel=material('OPTION_BEARING_STEEL',(.35,.4,.43));rubber=material('OPTION_BEARING_CORE',(.08,.10,.11))
def make(name,vs,fs,m):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(m);o=bpy.data.objects.new(name,me);col.objects.link(o);o['status']='USER-SELECTED GEOMETRIC COMPARISON; bearing type/dimensions/positions unverified';return o

def tree(o):return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(f.vertices) for f in o.data.polygons])
# Map global face indices back to individual bottom-flange source objects.
vs=[];fs=[];owners=[]
for o in bpy.data.collections['06_Steel_girders_estimated'].objects:
 if not o.name.endswith('_bottom'):continue
 off=len(vs);vs.extend([o.matrix_world@v.co for v in o.data.vertices])
 for f in o.data.polygons:fs.append([i+off for i in f.vertices]);owners.append(o.name)
girders=BVHTree.FromPolygons(vs,fs);rows=[];bearing_rows=[];skipped=[]
def cube(name,x,y,z,dx,dy,dz,m):
 pts=[(x+sx*dx/2,y+sy*dy/2,z+sz*dz/2) for sx,sy,sz in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
 return make(name,pts,[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],m)
for cap in source.objects:
 if '_CAP_' not in cap.name or cap.hide_render:continue
 pts=[cap.matrix_world@v.co for v in cap.data.vertices];lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)];top=hi[2]-.2;capbvh=tree(cap);newpts=[(p.x,p.y,lo[2]+(p.z-lo[2])*(top-lo[2])/(hi[2]-lo[2])) for p in pts]
 new=make('LOWERED_'+cap.name,newpts,[list(f.vertices) for f in cap.data.polygons],concrete);new['original_cap']=cap.name;new['top_delta_m']=-.2
 hits={}
 for ix in range(9):
  for iy in range(41):
   x=lo[0]+(hi[0]-lo[0])*(ix+.5)/9;y=lo[1]+(hi[1]-lo[1])*(iy+.5)/41
   ch,_,_,_=capbvh.ray_cast(Vector((x,y,hi[2]+.5)),Vector((0,0,-1)),1)
   if ch is None:continue
   h,_,idx,_=girders.ray_cast(Vector((x,y,hi[2]-.05)),Vector((0,0,1)),.5)
   if h is not None and abs(h.z-hi[2])<.002:hits.setdefault(owners[idx],[]).append(h)
 added=0
 for girder,points in hits.items():
  # Pick the sample nearest group centroid whose entire 0.3x0.3 footprint fits both solids.
  avg=sum(points,Vector())/len(points);chosen=None
  for q in sorted(points,key=lambda q:(q-avg).length):
   valid=True
   for dx,dy in [(-.15,-.15),(-.15,.15),(.15,-.15),(.15,.15)]:
    x,y=q.x+dx,q.y+dy;ch,_,_,_=capbvh.ray_cast(Vector((x,y,hi[2]+.5)),Vector((0,0,-1)),1);h,_,idx,_=girders.ray_cast(Vector((x,y,hi[2]-.05)),Vector((0,0,1)),.5)
    if ch is None or h is None or owners[idx]!=girder or abs(h.z-hi[2])>.002:valid=False;break
   if valid:chosen=q;break
  if chosen is None:skipped.append({'cap':cap.name,'girder':girder,'reason':'0.3m square footprint did not fit sampled cap/flange intersection'});continue
  q=chosen;ident=cap.name+'_'+str(added)
  # 0.025 steel / 0.15 core / 0.025 steel = selected0.20m stack.
  cube('BEARING_BASE_'+ident,q.x,q.y,top+.0125,.3,.3,.025,steel)
  cube('BEARING_CORE_'+ident,q.x,q.y,top+.1,.27,.27,.15,rubber)
  cube('BEARING_TOP_'+ident,q.x,q.y,top+.1875,.3,.3,.025,steel)
  bearing_rows.append({'cap':cap.name,'girder':girder,'xy':[q.x,q.y],'bottom_z':top,'top_z':top+.2,'original_girder_underside_z':hi[2],'gap_error_m':abs(top+.2-hi[2]),'footprint_m':[.3,.3],'corner_contact_check':'four sampled corners fit cap and flange'});added+=1
 rows.append({'cap':cap.name,'original_bottom_z':lo[2],'original_top_z':hi[2],'comparison_top_z':top,'bearing_stacks_added':added})
qa=[]
for o in col.objects:
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);bm.to_mesh(o.data);bm.free();qa.append(bad)
assert not any(qa)
camd=bpy.data.cameras.new('BEARING_DETAIL_CAMERA');cam=bpy.data.objects.new(camd.name,camd);scene.collection.objects.link(cam);scene.camera=cam
focus=min(bearing_rows,key=lambda q:(q['xy'][0]-1197)**2+(q['xy'][1]-733)**2);x,y=focus['xy'];cam.location=(x+4,y-8,7);cam.rotation_euler=(Vector((x,y,5.5))-cam.location).to_track_quat('-Z','Y').to_euler();camd.type='ORTHO';camd.ortho_scale=6
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True;scene.render.resolution_x=1700;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(root/'bearing_comparison_detail.png');bpy.ops.render.render(write_still=True,scene=scene.name)
bpy.context.window.scene=sc;file=root/('CIVIC_BEARING_OPTION_'+stamp+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));result={'file':str(file),'scene':scene.name,'lowered_caps':len(rows),'bearing_stacks':len(bearing_rows),'caps_without_stacks':[r['cap'] for r in rows if r['bearing_stacks_added']==0],'unfitted_intersections':skipped,'caps':rows,'bearings':bearing_rows,'new_meshes':len(qa),'nonmanifold_edges':sum(qa),'main_original_geometry_unchanged':True,'camera_count':len(bpy.data.collections['CIVIC_CAMERAS_500M_NORTH_SOUTH'].objects),'status':'Comparison only: 0.20m stack and type assumed; no load calculations, anchors, movement or seismic design; unresolved 7 pier groups retained'};(root/'bearing_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));result={k:v for k,v in result.items() if k not in ['caps','bearings','unfitted_intersections']}
