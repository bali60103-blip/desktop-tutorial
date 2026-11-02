import bpy,json,pathlib,collections,math,time
from mathutils import Vector
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/BlockFacades');sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];sc.view_layers[0].update();bad=[];counts={};vertices=faces=0;instances=0
for cn in ['BLOCK_BUILDING_CORES','BLOCK_RECESSED_FACADES','BLOCK_ROOFS','BLOCK_CONTEXT_GROUND','BLOCK_FACADE_ASSETS']:
 c=bpy.data.collections[cn];counts[cn]=len(c.objects)
 for o in c.objects:
  if o.type!='MESH':continue
  m=o.data;vertices+=len(m.vertices);faces+=len(m.polygons);nf=sum(not all(math.isfinite(x) for x in v.co) for v in m.vertices)
  if cn=='BLOCK_RECESSED_FACADES':
   instances+=len(m.vertices);invalid=sum(not 0<=a.value<6 for a in m.attributes['facade_module'].data);invalid+=sum(any(not math.isfinite(x) or x<=0 for x in a.vector) for a in m.attributes['facade_scale'].data)
   if invalid or nf:bad.append({'object':o.name,'invalid_attributes':invalid,'nonfinite':nf})
  else:
   ec=collections.Counter(tuple(sorted(e)) for p in m.polygons for e in p.edge_keys);zero=sum(p.area<1e-10 for p in m.polygons);edge=sum(n!=2 for n in ec.values())
   if nf or zero or edge:bad.append({'object':o.name,'nonfinite':nf,'zero_area':zero,'nonmanifold_edges':edge})
selection=json.load(open(out/'selection_summary.json'));alias=json.load(open(out/'frontage_coverage_alias.json'));o=bpy.data.objects.get('BLOCK_'+alias['represented_by']+'_CORE')
if o:o['source_alias']=alias['source_osm_id']
# Keep a wide view on opening, independent from close-up render camera.
coords=[o.matrix_world@Vector(v) for o in bpy.data.collections['BLOCK_BUILDING_CORES'].objects for v in o.bound_box];mn=[min(v[i] for v in coords) for i in range(3)];mx=[max(v[i] for v in coords) for i in range(3)];center=Vector(((mn[0]+mx[0])/2,(mn[1]+mx[1])/2,15))
for ar in bpy.context.screen.areas:
 if ar.type=='VIEW_3D':
  s=ar.spaces.active;s.clip_start=.1;s.clip_end=30000;s.lens=35;s.region_3d.view_perspective='PERSP';s.region_3d.view_location=center;s.region_3d.view_distance=(mx[0]-mn[0])*.65;s.region_3d.view_rotation=Vector((0,7000,-6500)).to_track_quat('-Z','Y')
sc['source_scope']='303 mapped road-corridor blocks; all selected mapped building areas and parts';sc['facade_detail_status']='Estimated module proportions and placements; not photogrammetric or per-building streetview reconstruction';sc['report']=str(out/'街廓立面報告.md');path=bpy.data.filepath if str(out) in bpy.data.filepath and 'CIVIC_303_BLOCKS_FACADES_WORKING_' in bpy.data.filepath else str(out/('CIVIC_303_BLOCKS_FACADES_WORKING_'+time.strftime('%Y%m%d_%H%M%S')+'.blend'));r={'file':path,'scene':sc.name,'counts':counts,'stored_mesh_vertices':vertices,'stored_mesh_faces':faces,'facade_instances':instances,'road_cameras':sum(o.type=='CAMERA' and o.name.startswith('CIVIC200_') for o in sc.objects),'preserved_original_cameras':sum(o.type=='CAMERA' and o.name in bpy.data.scenes['CIVIC_COMPLETE_WORKING_ASSEMBLY'].objects for o in sc.objects),'mesh_attribute_issues':bad,'selected_blocks':selection['selected_street_blocks'],'building_records':selection['mapped_buildings_and_parts'],'first_row_unique_records':selection['first_row_buildings'],'original_frontage_alias':alias,'scope_status':'All selected mapped buildings constructed; unmapped buildings and actual facade details not verified','bounds':[mn,mx]};text=bpy.data.texts.get('CIVIC_BLOCK_FACADE_STATUS.json') or bpy.data.texts.new('CIVIC_BLOCK_FACADE_STATUS.json');text.clear();text.write(json.dumps(r,ensure_ascii=False,indent=2));bpy.ops.wm.save_as_mainfile(filepath=path);(out/'final_model_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result=r
