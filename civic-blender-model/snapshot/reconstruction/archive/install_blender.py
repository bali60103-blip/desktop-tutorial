import bpy,json,pathlib,math,shutil
from mathutils import Vector
P=pathlib.Path('/tmp/civic-rebuild');root=pathlib.Path((P/'output_root.txt').read_text());payload=json.loads((P/'build_payload.json').read_text())
assert bpy.data.filepath==str(root/'01_civic_georeferenced_rebuild.blend'),'Refusing to edit unexpected file'
scene=bpy.context.scene
# Preserve all original objects, materials and hierarchy under a hidden archive.
archive=bpy.data.collections.new('90_ORIGINAL_MODEL_ARCHIVE');scene.collection.children.link(archive)
for c in list(scene.collection.children):
 if c!=archive:archive.children.link(c);scene.collection.children.unlink(c)
archive.hide_viewport=True;archive.hide_render=True
for o in list(scene.collection.objects):scene.collection.objects.unlink(o);archive.objects.link(o)
rootcol=bpy.data.collections.new('CIVIC_REBUILD__METERS__SOURCE_TAGGED');scene.collection.children.link(rootcol)
cols={}
colors={'01':(.58,.67,.67,1),'02':(.13,.17,.20,1),'03':(.73,.50,.20,1),'04':(.25,.33,.38,1),'05':(.63,.70,.72,1),'06':(.23,.40,.44,1),'07':(.85,.40,.08,1),'08':(.90,.08,.26,1),'09':(.65,.42,.17,1),'10':(.72,.74,.75,1)}
materials={}
def collection(n):
 if n not in cols:
  c=bpy.data.collections.new(n);rootcol.children.link(c);cols[n]=c
 return cols[n]
def mat(key):
 if key not in materials:
  m=bpy.data.materials.new('CIVIC_'+key);m.diffuse_color=colors.get(key,(.7,.7,.7,1));m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Roughness'].default_value=.82;materials[key]=m
 return materials[key]
bad=0
for rec in payload['objects']:
 me=bpy.data.meshes.new(rec['name']);me.from_pydata(rec['vertices'],[],rec['faces']);bad+=int(me.validate());me.update()
 o=bpy.data.objects.new(rec['name'],me);collection(rec['layer']).objects.link(o);o.data.materials.append(mat(rec['layer'][:2]))
 for k,v in rec['props'].items():o[k]=v if v is not None else 'unknown'
 o['CRS']='EPSG:3826, local offset in scene metadata';o['units']='m'
cols['08_Official_column_candidates_HIDDEN'].hide_viewport=True;cols['08_Official_column_candidates_HIDDEN'].hide_render=True
# Retain context buildings, explicitly not claiming their old default heights are measured.
orig=bpy.data.objects.get('Buildings_Massing')
if orig:
 o=orig.copy();o.data=orig.data.copy();o.name='Buildings_context__OSM_XY__HEIGHTS_UNVERIFIED';collection('10_Buildings_context').objects.link(o);o.data.materials.clear();o.data.materials.append(mat('10'))
 for p in o.data.polygons:p.material_index=0
 o['confidence']='Existing OSM footprint massing; 12m/default and floor-derived heights are unverified. Landmark matches in building_matches.json';o.hide_set(False);o.hide_viewport=False;o.hide_render=False
median=bpy.data.objects.get('Civic_Blvd_Median_分隔島')
if median:
 o=median.copy();o.data=median.data.copy();o.name='MEDIAN_legacy__OUTLINE_UNVERIFIED';collection('09_Median_legacy_UNVERIFIED').objects.link(o);o.data.materials.clear();o.data.materials.append(mat('09'));o['confidence']='Previous procedural continuous median, NOT official surveyed outline; retained hidden pending correction';o.hide_set(False);o.hide_viewport=False;o.hide_render=False
 cols['09_Median_legacy_UNVERIFIED'].hide_viewport=True;cols['09_Median_legacy_UNVERIFIED'].hide_render=True
# A plain analysis datum, no invented terrain levels.
b=payload['bounds_local'];cx=(b[0][0]+b[1][0])/2;cy=(b[0][1]+b[1][1])/2
me=bpy.data.meshes.new('Datum');me.from_pydata([(cx-6000,cy-4000,-.14),(cx+6000,cy-4000,-.14),(cx+6000,cy+4000,-.14),(cx-6000,cy+4000,-.14)],[],[(0,1,2,3)]);o=bpy.data.objects.new('GROUND_DATUM_Z0_not_surveyed_terrain',me);collection('11_Presentation').objects.link(o)
m=bpy.data.materials.new('Datum_offwhite');m.diffuse_color=(.88,.88,.84,1);o.data.materials.append(m)
def camera(n,pos,target,scale):
 d=bpy.data.cameras.new(n);d.type='ORTHO';d.ortho_scale=scale;d.clip_end=50000;o=bpy.data.objects.new(n,d);collection('11_Presentation').objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
overview=camera('CAM_01_Full_corridor',(cx,cy-2900,4200),(cx,cy,0),7200)
detail=camera('CAM_02_Jinshan_detail',(2000,440,185),(2070,640,0),290)
top=camera('CAM_03_GIS_overlay',(cx,cy,7000),(cx,cy,0),7100)
scene.camera=detail
sun=bpy.data.lights.new('Civic_daylight','SUN');sun.energy=2.0;sun.angle=.35;o=bpy.data.objects.new('Civic_daylight',sun);collection('11_Presentation').objects.link(o);o.rotation_euler=(.45,-.5,-.5)
scene.world.color=(.4,.4,.4);scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=950;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene['CIVIC_CRS']='EPSG:3826';scene['CIVIC_REGISTRATION']=json.dumps(payload['registration'],ensure_ascii=False);scene['CIVIC_SOURCE_STATUS']='Official XY: sidewalks and historic road extents. Estimated: bridge width, all vertical dimensions, girders, parapets. Amber supports: legacy unverified positions. Official column candidates hidden.'
scene['CIVIC_LOCAL_ORIGIN_TWD97']=payload['local_origin'];scene['CIVIC_OUTPUT_FOLDER']=str(root)
for scr in bpy.data.screens:
 for area in scr.areas:
  if area.type=='VIEW_3D':
   space=area.spaces.active;space.clip_end=50000;space.shading.color_type='MATERIAL';space.region_3d.view_perspective='CAMERA'
doc=bpy.data.texts.new('READ_ME__DATA_CONFIDENCE');doc.write('CIVIC — 地理對位重建工作版\n官方人行道與歷史道路範圍已對位。橋面寬度、鋼梁、護欄和高度為估算。橘色橋墩沿用舊模型假設，尚未取得實測柱位。原始模型在隱藏 archive。\n請勿以此模型作竣工或測量成果。\n詳見同目錄 README.md 與 source_manifest.json。')
for fn in ['registration.json','building_matches.json','rebuild_features_TWD97.geojson']:
 shutil.copy2(P/fn,root/fn)
shutil.copy2('/tmp/civic-assemble.py',root/'assemble_geometry.py');shutil.copy2('/tmp/civic-install-blender.py',root/'install_blender.py')
result={'objects_created':len(payload['objects']),'mesh_validation_repairs':bad,'counts':payload['counts'],'file':str(root/'01_civic_georeferenced_rebuild.blend')}
(root/'build_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(root/'01_civic_georeferenced_rebuild.blend'))
