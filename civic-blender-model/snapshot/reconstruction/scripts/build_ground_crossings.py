"""Add physical markings, candidate curb ramps and consistent sidewalk openings.
Source points mapped; accessibility construction is estimated and explicitly tagged.
"""
import bpy,json,pathlib,bmesh,datetime
p=json.loads(pathlib.Path(PAYLOAD).read_text());root=pathlib.Path(ROOT);root.mkdir(parents=True,exist_ok=True);s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bpy.ops.wm.save_as_mainfile(filepath=str(root/('before_crossings_'+s+'.blend')),copy=True)
name='GROUND_FULL_02_CROSSINGS_AND_RAMPS_ESTIMATED';old=bpy.data.collections.get(name)
if old:
 for o in list(old.objects):bpy.data.objects.remove(o,do_unlink=True)
 bpy.data.collections.remove(old)
c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c)
for n in ['GROUND_SIDEWALKS_OFFICIAL_XY','GROUND_CURBS_ESTIMATED']:
 o=bpy.data.objects.get(n)
 if o:o.hide_render=True;o.hide_set(True)
checks=[]
for key,d in p['meshes'].items():
 me=bpy.data.meshes.new(key);me.from_pydata(d['vertices'],[],d['faces']);me.update();o=bpy.data.objects.new(key,me);c.objects.link(o)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.dissolve_degenerate(bm,dist=.00001,edges=list(bm.edges));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);bm.to_mesh(me);bm.free();me.update()
 mat=bpy.data.materials.new(key+'_MAT');mat.diffuse_color=(.9,.9,.87,1) if 'MARKINGS' in key else ((.63,.57,.43,1) if 'CURB_RAMPS' in key else (.6,.57,.51,1));me.materials.append(mat);o['status']='Mapped source context, estimated marking extents or curb-ramp geometry';o['assumptions']=json.dumps(p['assumptions']);o['nonmanifold_edges']=bad
 checks.append({'object':key,'faces':len(me.polygons),'nonmanifold_edges':bad})
c['remaining_field_verification']='Ramp existence, signal phase, refuge-island arrangement and exact stripe endpoints';c['source']='OSM crossing node IDs preserved in crossing_check.json'
file=root/('GROUND_CROSSINGS_'+s+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));result={'file':str(file),'checks':checks,'summary':p['summary']};(root/'crossing_build_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
