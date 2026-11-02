"""Close only simple four-edge ramp end loops; preserve every existing vertex."""
import bpy,bmesh,json,pathlib,datetime
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'RampTopology';out.mkdir(exist_ok=True)
sc=bpy.data.scenes['Scene'];bpy.context.window.scene=sc;s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_ramp_topology_'+s+'.blend')),copy=True)
rows=[]
for o in bpy.data.collections['Civic_Blvd_Ramps_Real'].objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data);bad=sum(not e.is_manifold for e in bm.edges);edges=[e for e in bm.edges if e.is_boundary]
 if not bad:bm.free();rows.append({'name':o.name,'status':'already closed'});continue
 # Only repair the exact generator pattern: two separate simple quadrilateral ends.
 pending=set(edges);loops=[]
 while pending:
  e=pending.pop();group={e};stack=[e]
  while stack:
   cur=stack.pop()
   for v in cur.verts:
    for nb in v.link_edges:
     if nb in pending:pending.remove(nb);group.add(nb);stack.append(nb)
  loops.append(group)
 if bad!=8 or len(loops)!=2 or any(len(g)!=4 for g in loops):
  bm.free();rows.append({'name':o.name,'status':'unresolved topology; pattern not recognized','bad_edges':bad});continue
 original=[tuple(v.co) for v in o.data.vertices];old=o.data;old.use_fake_user=True
 bmesh.ops.holes_fill(bm,edges=edges,sides=4);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 after=sum(not e.is_manifold for e in bm.edges);assert after==0
 new=old.copy();new.name=old.name+'_CLOSED_ENDS';bm.to_mesh(new);bm.free()
 assert len(new.vertices)==len(original) and all((v.co-Vector(p)).length<1e-6 for v,p in zip(new.vertices,original))
 o.data=new;o['topology_repair']='Closed two original four-edge end loops; vertex positions unchanged';o['geometry_status']='Legacy estimated route/width/elevation; not satellite or as-built verified'
 rows.append({'name':o.name,'status':'two end caps added','before_bad_edges':bad,'after_bad_edges':after,'vertex_positions_unchanged':True})
# Isolated geometry render for one repaired ramp; no claim of surveyed alignment.
review=bpy.data.scenes.new('RAMP_TOPOLOGY_DETAIL');review.world=sc.world
target=bpy.data.objects['Ramp_00_市民大道入口匝道'];review.collection.objects.link(target)
pts=[target.matrix_world@Vector(p) for p in target.bound_box];center=sum(pts,Vector())/8;extent=max(max(p[i] for p in pts)-min(p[i] for p in pts) for i in [0,1])
cd=bpy.data.cameras.new('RAMP_TOPOLOGY_CAM');cam=bpy.data.objects.new(cd.name,cd);review.collection.objects.link(cam);review.camera=cam;cam.location=center+Vector((extent*.3,-extent*.8,extent*.6));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=max(20,extent*1.3);cd.clip_end=10000
review.render.engine='BLENDER_WORKBENCH';review.display.shading.color_type='MATERIAL';review.display.shading.show_shadows=False;review.render.resolution_x=1400;review.render.resolution_y=900;review.render.resolution_percentage=100;review.render.filepath=str(out/'ramp_topology_detail.png');bpy.ops.render.render(write_still=True,scene=review.name)
bpy.context.window.scene=sc;file=out/('CIVIC_RAMP_TOPOLOGY_'+s+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file))
report={'file':str(file),'objects':rows,'repaired':sum(r['status']=='two end caps added' for r in rows),'limitations':'Topology only. Names in legacy ramp collection include other roads. No change to routes, widths, grades or merge geometry; these need imagery/source verification.'};(out/'topology_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));result={k:v for k,v in report.items() if k!='objects'}
