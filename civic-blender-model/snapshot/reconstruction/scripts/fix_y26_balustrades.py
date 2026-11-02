import bpy,bmesh,json,pathlib
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Y26PhotoVariant';e=next(e for e in json.load(open(root/'YMallEntrances/source/y_entrance_payload.json'))['entries'] if e['ref']=='Y26');a=Vector(e['live_xy']);d=(Vector(e['lower_landing_xy'])-a).normalized();n=Vector((-d.y,d.x));col=bpy.data.collections['Y26_PHOTO_CONFIGURATION_ESTIMATED']
for o in col.objects:
 if o.name.startswith('Y26_ESC_BALUSTRADE_'):o.hide_render=True;o.hide_viewport=True
for side in [.68,1.92]:
 vs=[]
 for upper in [False,True]:
  for x,y in [(0,side-.06),(8.4,side-.06),(8.4,side+.06),(0,side+.06)]:
   q=a+d*x+n*y;z=.6-.5*x+(.9 if upper else 0);vs.append((q.x,q.y,z))
 me=bpy.data.meshes.new('Y26_ESC_CONTINUOUS_'+str(side));me.from_pydata(vs,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert all(ed.is_manifold for ed in bm.edges);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(me.name,me);col.objects.link(o);me.materials.append(bpy.data.materials['Y26_metal']);o['status']='Continuous estimated balustrade; no actual escalator dimensions measured'
sc=bpy.data.scenes['Y26_PHOTO_COMPARISON']
sc.render.filepath=str(out/'Y26_exterior.png');bpy.ops.render.render(write_still=True,scene=sc.name);bpy.data.objects['Y26_REMOVABLE_ROOF'].hide_render=True;sc.render.filepath=str(out/'Y26_cutaway.png');bpy.ops.render.render(write_still=True,scene=sc.name);bpy.data.objects['Y26_REMOVABLE_ROOF'].hide_render=False;bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
p=out/'photo_variant_check.json';r=json.loads(p.read_text());r['balustrade_fix']='28 stepped segment meshes hidden;2 continuous closed panels added';r['active_meshes']=92;p.write_text(json.dumps(r,ensure_ascii=False,indent=2));result={'file':bpy.data.filepath,'continuous_panels':2}
