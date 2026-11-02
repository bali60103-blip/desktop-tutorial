import bpy,json,pathlib
from mathutils import Vector
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/BlockFacades');sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];r=json.load(open(out/'context_payload.json'));col=bpy.data.collections.new('BLOCK_CONTEXT_GROUND');sc.collection.children.link(col);mats={}
for kind,color in [('LAND',(.43,.45,.43,1)),('ROAD',(.13,.15,.17,1)),('SIDEWALK',(.59,.58,.55,1))]:
 m=bpy.data.materials.new('BLOCK_CONTEXT_'+kind);m.diffuse_color=color;mats[kind]=m
for p in r['parts']:
 v=p['mesh']['vertices'];org=Vector(v[0]);m=bpy.data.meshes.new(p['name']);m.from_pydata([tuple(Vector(q)-org) for q in v],[],p['mesh']['faces']);m.materials.append(mats[p['kind']]);m.update();o=bpy.data.objects.new(p['name'],m);o.location=org;col.objects.link(o);o['status']=r['status']
sc.view_layers[0].update();result={'ground_objects':len(col.objects),'status':r['status']}
