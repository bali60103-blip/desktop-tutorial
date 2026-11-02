"""Build a separate fully mapped block context with instanced, explicitly inferred recessed facades."""
import bpy,json,pathlib,math,time,collections
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'BlockFacades';start=BUILD_START;end=BUILD_END
if start==0:
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'BEFORE_BLOCK_FACADES.blend'),copy=True)
 source=bpy.data.scenes['CIVIC_COMPLETE_WORKING_ASSEMBLY'];sc=bpy.data.scenes.new('CIVIC_BLOCKS_FACADES_WORKING')
 for c in source.collection.children:
  if c.name not in ['COMPLETION_FRONTAGE','COMPLETION_ISSUE_MARKERS']:sc.collection.children.link(c)
 for o in source.collection.objects:
  if o.name not in sc.objects:sc.collection.objects.link(o)
 for name in ['BLOCK_BUILDING_CORES','BLOCK_RECESSED_FACADES','BLOCK_ROOFS','BLOCK_FACADE_ASSETS']:
  c=bpy.data.collections.new(name);sc.collection.children.link(c)
 sc.world=source.world.copy();sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.render.resolution_percentage=100;sc.camera=source.camera
 bpy.context.window.scene=sc;sc.view_layers[0].update()
 for name in ['COMPLETION_REMOVABLE_ROOFS','CALIBRATION_RETAINED_CONFLICT_OBJECTS','BLOCK_FACADE_ASSETS']:
  sc.view_layers[0].layer_collection.children[name].exclude=True
 mats=[]
 for name,color in [('CIVIC_FACADE_WALL',(.64,.59,.51,1)),('CIVIC_FACADE_GLASS',(.075,.17,.22,1)),('CIVIC_FACADE_FRAME',(.26,.28,.29,1)),('CIVIC_FACADE_ROOF',(.32,.34,.35,1))]:
  m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.diffuse_color=color;mats.append(m)
 assets=bpy.data.collections['BLOCK_FACADE_ASSETS']
 for kind,label in enumerate(['RESIDENTIAL','OFFICE','SERVICE','ENTRY','SOLID','BALCONY']):
  vs=[];fs=[];mi=[]
  def cube(x0,x1,y0,y1,z0,z1,mat=0):
   if min(x1-x0,y1-y0,z1-z0)<1e-7:return
   k=len(vs);vs.extend([(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]);fs.extend([[k+i for i in f] for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]]);mi.extend([mat]*6)
  if kind==4:cube(-.5,.5,0,.18,-.5,.5)
  else:
   xw=.38 if kind in [1,3,5] else .31;zb=-.5 if kind in [3,5] else (-.32 if kind==1 else -.20);zt=.32 if kind==1 else .26
   cube(-.5,-xw,0,.18,-.5,.5);cube(xw,.5,0,.18,-.5,.5);cube(-xw,xw,0,.18,-.5,zb);cube(-xw,xw,0,.18,zt,.5)
   cube(-xw+.015,xw-.015,.125,.14,zb+.012,zt-.012,1)
   cube(-xw,xw,.095,.14,zt-.018,zt,2);cube(-xw,xw,.095,.14,zb,zb+.018,2);cube(-xw,-xw+.012,.095,.14,zb,zt,2);cube(xw-.012,xw,.095,.14,zb,zt,2)
   if kind in [0,1,5]:cube(-.006,.006,.09,.14,zb,zt,2)
   if kind==2:
    for j in range(5):
     zz=zb+(zt-zb)*(j+1)/6;cube(-xw,xw,-.025,.12,zz-.015,zz+.015,2)
   if kind not in [3,5]:cube(-xw-.02,xw+.02,-.09,.18,zb-.022,zb+.003,2)
   if kind==3:cube(xw-.07,xw-.05,.065,.12,-.13,.03,2)
   if kind==5:
    cube(-.46,.46,-.95,.18,-.56,-.5,2);cube(-.46,.46,-.95,-.90,-.5,-.18,1);cube(-.46,-.44,-.95,.05,-.5,-.18,1);cube(.44,.46,-.95,.05,-.5,-.18,1);cube(-.46,.46,-.97,-.89,-.19,-.17,2)
  m=bpy.data.meshes.new('FAC_MODULE_'+str(kind));m.from_pydata(vs,[],fs);m.update()
  for mat in mats:m.materials.append(mat)
  for p,mat in zip(m.polygons,mi):p.material_index=mat
  o=bpy.data.objects.new(str(kind).zfill(2)+'_'+label,m);assets.objects.link(o);o['status']='Estimated reusable facade geometry; real facade proportions unverified'
 ng=bpy.data.node_groups.new('CIVIC_RECESSED_FACADE_INSTANCES','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');n=ng.nodes;inp=n.new('NodeGroupInput');output=n.new('NodeGroupOutput');ci=n.new('GeometryNodeCollectionInfo');ci.inputs['Collection'].default_value=assets;ci.inputs['Separate Children'].default_value=True;ci.inputs['Reset Children'].default_value=True;inst=n.new('GeometryNodeInstanceOnPoints');inst.inputs['Pick Instance'].default_value=True;ng.links.new(inp.outputs['Geometry'],inst.inputs['Points']);ng.links.new(ci.outputs['Instances'],inst.inputs['Instance'])
 for name,typ,target in [('facade_module','INT','Instance Index'),('facade_scale','FLOAT_VECTOR','Scale'),('facade_rotation','FLOAT_VECTOR','Rotation')]:
  a=n.new('GeometryNodeInputNamedAttribute');a.data_type=typ;a.inputs['Name'].default_value=name;ng.links.new(a.outputs['Attribute'],inst.inputs[target])
 ng.links.new(inst.outputs['Instances'],output.inputs['Geometry']);bpy.app.driver_namespace['CIVIC_BLOCK_PAYLOAD']=json.load(open(out/'facade_payload.json'))
else:sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc
payload=bpy.app.driver_namespace.get('CIVIC_BLOCK_PAYLOAD')
if payload is None:payload=json.load(open(out/'facade_payload.json'));bpy.app.driver_namespace['CIVIC_BLOCK_PAYLOAD']=payload
mats=[bpy.data.materials[n] for n in ['CIVIC_FACADE_WALL','CIVIC_FACADE_GLASS','CIVIC_FACADE_FRAME','CIVIC_FACADE_ROOF']];corecol=bpy.data.collections['BLOCK_BUILDING_CORES'];faccol=bpy.data.collections['BLOCK_RECESSED_FACADES'];roofcol=bpy.data.collections['BLOCK_ROOFS'];built=[]
for r in payload[start:end]:
 name='BLOCK_'+r['osm_id']
 if bpy.data.objects.get(name+'_CORE'):continue
 allv=[v for c in r['cores'] for v in c['vertices']]
 if not allv:continue
 org=Vector(allv[0]);vs=[];fs=[]
 for c in r['cores']:
  off=len(vs);vs.extend([tuple(Vector(v)-org) for v in c['vertices']]);fs.extend([[i+off for i in f] for f in c['faces']])
 m=bpy.data.meshes.new(name+'_CORE');m.from_pydata(vs,[],fs);m.materials.append(mats[0]);m.update();o=bpy.data.objects.new(name+'_CORE',m);o.location=org;corecol.objects.link(o);core_obj=o
 for k in ['osm_id','name','block_id','height_m','height_status','facade_status','is_building_part','first_row']:
  if r[k] is not None:o[k]=r[k]
 pts=r['points']
 if pts:
  m=bpy.data.meshes.new(name+'_FACADE_POINTS');m.from_pydata([tuple(Vector(p['position'])-org) for p in pts],[],[])
  for key,typ,source in [('facade_module','INT','module'),('facade_scale','FLOAT_VECTOR','scale'),('facade_rotation','FLOAT_VECTOR','rotation')]:
   a=m.attributes.new(name=key,type=typ,domain='POINT')
   if typ=='INT':a.data.foreach_set('value',[p[source] for p in pts])
   else:a.data.foreach_set('vector',[x for p in pts for x in p[source]])
  o=bpy.data.objects.new(name+'_FACADE',m);o.parent=core_obj;o.location=(0,0,0);faccol.objects.link(o);mod=o.modifiers.new('Recessed facade modules','NODES');mod.node_group=bpy.data.node_groups['CIVIC_RECESSED_FACADE_INSTANCES'];o['osm_id']=r['osm_id'];o['status']=r['facade_status'];o['instance_count']=len(pts)
 for j,roof in enumerate(r['roofs']):
  m=bpy.data.meshes.new(name+'_ROOF'+str(j));m.from_pydata([tuple(Vector(v)-org) for v in roof['vertices']],[],roof['faces']);m.materials.append(mats[3]);m.update();o=bpy.data.objects.new(name+'_ROOF'+str(j),m);o.parent=core_obj;o.location=(0,0,0);roofcol.objects.link(o);o['status']=roof['status']
 built.append(r['osm_id'])
sc['facade_status']='All facade modules estimated; mapped building parts retained; full site completeness not verified';sc.view_layers[0].update();(out/('build_batch_'+str(start)+'.json')).write_text(json.dumps({'start':start,'end':end,'built':built,'total':len(payload)},ensure_ascii=False));result={'built':len(built),'core_objects':len(corecol.objects),'facade_objects':len(faccol.objects),'total_payload':len(payload),'range':[start,end]}
