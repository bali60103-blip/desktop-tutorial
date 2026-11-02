import bpy,json,pathlib
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/BlockFacades');payload=json.load(open(out/'facade_payload.json'));bpy.app.driver_namespace['CIVIC_BLOCK_PAYLOAD']=payload
for r in payload[:20]:
 core=bpy.data.objects.get('BLOCK_'+r['osm_id']+'_CORE');o=bpy.data.objects.get('BLOCK_'+r['osm_id']+'_FACADE')
 if o:
  o.data.attributes['facade_module'].data.foreach_set('value',[p['module'] for p in r['points']]);o.parent=core;o.location=(0,0,0)
 for j in range(len(r['roofs'])):
  roof=bpy.data.objects.get('BLOCK_'+r['osm_id']+'_ROOF'+str(j))
  if roof:roof.parent=core;roof.location=(0,0,0)
result={'refreshed':20,'payload_records':len(payload)}
