import bpy,json,os,pathlib,datetime
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;sc.view_layers[0].update();payload=json.load(open(out/'mapped_vent_shell_payload.json'));name='CAL3_MAPPED_VENT_SHAFTS_EST';existing=bpy.data.collections.get(name)
if existing and len(existing.objects)==0:bpy.data.collections.remove(existing)
assert not bpy.data.collections.get(name),'Already built'
# Preflight all replacements before any scene mutation.
targets_by_id={}
for row in payload:
 ident=row['osm_id'];targets=[o for o in sc.objects if o.type=='MESH' and o.visible_get(view_layer=sc.view_layers[0]) and (o.get('osm_id')==ident or o.name.startswith('BLOCK_'+ident+'_ROOF') or o.name=='COMP_OSM_EQUIP_'+ident[1:])];assert targets,ident;targets_by_id[ident]=targets
bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_MAPPED_VENTS_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True);col=bpy.data.collections.new(name);sc.collection.children.link(col);integrated=bpy.data.scenes.get('GONGZHONG_INTEGRATED_OPENINGS_EST')
if integrated:integrated.collection.children.link(col)
ret=bpy.data.collections.new('CAL3_RETAINED_MAPPED_VENT_PROXIES');sc.collection.children.link(ret);sc.view_layers[0].layer_collection.children[ret.name].exclude=True;mats=[bpy.data.materials[n] for n in ['CAL3_MEDIAN_VENT_CONCRETE_EST','CAL3_MEDIAN_LOUVER_METAL_EST']];report=[]
for row in payload:
 ident=row['osm_id'];targets=targets_by_id[ident];origin=Vector(row['vertices'][0]);m=bpy.data.meshes.new('MAPPED_VENT_'+ident);m.from_pydata([tuple(Vector(v)-origin) for v in row['vertices']],[],row['faces']);m.update()
 for mat in mats:m.materials.append(mat)
 for p,idx in zip(m.polygons,row['materials']):p.material_index=idx
 counts={}
 for p in m.polygons:
  for e in p.edge_keys:counts[e]=counts.get(e,0)+1
 assert all(v==2 for v in counts.values()),ident
 o=bpy.data.objects.new(m.name,m);o.location=origin;col.objects.link(o);o['osm_id']=ident;o['source_tags']=json.dumps(row['source_tags'],ensure_ascii=False);o['verification_status']='Mapped ventilation shaft; estimated housing/louvers. Original height/elevation preserved and still unverified. Generic residential/office window modules removed.';o['height_status']=row['height_status'];o['height_m']=row['height_m'];o['base_z_m']=row['base_z_m'];o['source_url']='https://www.openstreetmap.org/way/'+ident[1:]
 for old in targets:
  ret.objects.link(old)
  for c in list(old.users_collection):
   if c!=ret and (c in list(sc.collection.children) or (integrated is not None and c in list(integrated.collection.children))):c.objects.unlink(old)
 report.append({'osm_id':ident,'new_object':o.name,'archived':[o.name for o in targets],'height_m':row['height_m'],'base_z_m':row['base_z_m'],'height_status':row['height_status'],'louver_blades':row['louver_blades']})
r={'shafts_detailed':len(report),'archived_objects':sum(len(x['archived']) for x in report),'louver_blades':sum(x['louver_blades'] for x in report),'heights_preserved':True,'items':report,'limits':'OSM type is not a field survey. Some inherited tall shaft heights are generic estimates and remain flagged; no blanket height substitution applied. Housing cladding/entry access await photos.'};(out/'mapped_vent_shell_report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/'CIVIC_PHOTO_CALIBRATION_20260911_VENTS.blend'));result={k:v for k,v in r.items() if k!='items'}
