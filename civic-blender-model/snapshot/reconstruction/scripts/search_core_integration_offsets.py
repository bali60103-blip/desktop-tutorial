import bpy,json,pathlib,os,collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;lc=sc.view_layers[0].layer_collection.children['COMPLETION_REMOVABLE_ROOFS'];old=lc.exclude;lc.exclude=False;sc.view_layers[0].update();cases=json.load(open(out/'core_relocation_candidates.json'));dg=bpy.context.evaluated_depsgraph_get();reports=[]
try:
 for case in cases:
  points=[Vector(p['a'])+Vector(c['translation']) for p in case['paths'] for c in case['candidates']]+[Vector(p['b'])+Vector(c['translation']) for p in case['paths'] for c in case['candidates']];xmin=min(p.x for p in points)-5;xmax=max(p.x for p in points)+5;ymin=min(p.y for p in points)-5;ymax=max(p.y for p in points)+5;vs=[];fs=[];owners=[];editable=[];section=case['section'];core=case['core']
  for o in sc.objects:
   if o.type!='MESH' or not o.visible_get(view_layer=sc.view_layers[0]):continue
   if any(c.name in ['BLOCK_RECESSED_FACADES','BLOCK_FACADE_ASSETS'] for c in o.users_collection):continue
   bb=[o.matrix_world@Vector(v) for v in o.bound_box]
   if min(p.x for p in bb)>xmax or max(p.x for p in bb)<xmin or min(p.y for p in bb)>ymax or max(p.y for p in bb)<ymin or min(p.z for p in bb)>2.3 or max(p.z for p in bb)<-8:continue
   if o.name.startswith('COMP_'+section+'_CORE'+str(core)+'_') or o.name.startswith(('RAIL_'+case['prefix'],'GUARD_'+case['prefix'])):continue
   own_slab=o.name.startswith('COMP_'+section+'_B') and o.name.endswith(('_FLOOR','_PERIMETER')) or o.name=='COMP_ROOF_ACCESS_'+section+'_0'
   flatground=(any(c.name in ['COMPLETION_GROUND_HIGHWAY','BLOCK_CONTEXT_GROUND','COMPLETION_MARKINGS'] for c in o.users_collection) and min(p.z for p in bb)>=-.65 and max(p.z for p in bb)<=.4)
   if own_slab or flatground:editable.append(o.name);continue
   e=o.evaluated_get(dg);m=e.to_mesh();base=len(vs);vs.extend([o.matrix_world@v.co for v in m.vertices]);fs.extend([[base+i for i in p.vertices] for p in m.polygons]);owners.extend([o.name]*len(m.polygons));e.to_mesh_clear()
  tree=BVHTree.FromPolygons(vs,fs);results=[]
  for c in case['candidates']:
   offset=Vector(c['translation']);hits=collections.Counter()
   for p in case['paths']:
    a=Vector(p['a'])+offset;b=Vector(p['b'])+offset;d=b-a;n=Vector((-d.y,d.x,0)).normalized()
    for j in range(1,20):
     for side in [-.8,0,.8]:
      q=a.lerp(b,j/20)+n*(side*p['halfwidth'])+Vector((0,0,.2));_,_,idx,_=tree.ray_cast(q,Vector((0,0,1)),p['height']-.2)
      if idx is not None:hits[owners[idx]]+=1
   results.append({**c,'hits':dict(hits),'hit_count':sum(hits.values())})
  clear=[r for r in results if r['hit_count']==0];chosen=min(clear,key=lambda r:abs(r['distance_m'])+abs(r['lateral_m'])*2) if clear else None;reports.append({'section':section,'core':core,'prefix':case['prefix'],'chosen':chosen,'candidate_count':len(results),'best_candidates':sorted(results,key=lambda r:(r['hit_count'],abs(r['distance_m'])+2*abs(r['lateral_m'])))[:5],'requires_opening_updates':editable})
finally:lc.exclude=old;sc.view_layers[0].update()
r={'cases':reports,'scope':'Candidates stay inside prior estimated parking outlines and avoid other modeled obstacles in sampled headroom rays. Own parking floors/perimeters/roof and thin ground surfaces intentionally excluded because relocated openings would need rebuilding. Not adopted or survey-corrected.'};(out/'core_integration_search.json').write_text(json.dumps(r,indent=2));result={'cases':[{k:v for k,v in r.items() if k not in ['requires_opening_updates','best_candidates']} for r in reports]}
