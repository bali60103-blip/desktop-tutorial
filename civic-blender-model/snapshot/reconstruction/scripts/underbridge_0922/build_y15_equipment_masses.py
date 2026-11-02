"""Two observed enclosure masses near Y15, estimated geometry and placement.
The 2025-05 panorama is used. 2012 imagery is historical reference only.
"""
import bpy, math, os, json
from mathutils import Vector
from collections import Counter
assert bpy.context.scene.name=='CIVIC_UNDERBRIDGE_MASSING_20260916'
name='UB_Y15_PAIRED_ENCLOSURES_PHOTO_EST'
assert not bpy.data.collections.get(name), 'Already built'
c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c)
root=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922')
url='https://www.google.com/maps/@25.0492765,121.514265,3a,75y,103h,90t/data=!3m4!1e1!3m2!1smodALEC3WgErR-jyX2zyUA!2e0'
made=[]
mat=bpy.data.materials.new('UB_Y15_ENCLOSURE_STONE_EST');mat.diffuse_color=(.5,.45,.35,1);mat.use_nodes=True
mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=mat.diffuse_color
for side,xy in [('N',(436,864)),('S',(436,847))]:
 for part,w,d,z,h in [('PLINTH',5.2,3.8,0,.15),('BODY',4.8,3.4,.15,1.85),('COPING',5.1,3.7,2,.18),('TOP',4.8,3.4,2.18,.12)]:
  nm='UB_Y15_'+side+'_'+part+'_EST';a=math.radians(-14)
  v=[]
  for zz in [z,z+h]:
   for xx,yy in [(-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2)]:v.append((xy[0]+xx*math.cos(a)-yy*math.sin(a),xy[1]+xx*math.sin(a)+yy*math.cos(a),zz))
  me=bpy.data.meshes.new(nm);me.from_pydata(v,[],[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);me.update()
  ob=bpy.data.objects.new(nm,me);c.objects.link(ob);me.materials.append(mat)
  for k,val in {'source_url':url,'imagery_date':'2025-05','dimensions_status':'estimated, not measured','xy_status':'estimated from visible relation to two mapped bridge decks; not triangulated','function_status':'unknown enclosure; ventilation/electrical identity unconfirmed','review_required':True,'segment':'UB_X+004'}.items():ob[k]=val
  made.append(ob)
bpy.context.view_layer.update()
def bounds(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]
conflicts=[]
for ob in made:
 a,b=bounds(ob)
 for q in bpy.context.scene.objects:
  if q.type!='MESH' or q in made:continue
  lo,hi=bounds(q)
  if all(min(b[i],hi[i])-max(a[i],lo[i])>.01 for i in range(3)):
   conflicts.append([ob.name,q.name]);ob['aabb_conflict']=q.name
report={'collection':name,'objects':len(made),'aabb_conflicts':conflicts,'dimensions_verified':False,'full_corridor_complete':False,'limits':['two visible masses only','no assumed internal function','subsurface connections unknown','XY and dimensions require calibration']}
json.dump(report,open(os.path.join(root,'y15_equipment_report.json'),'w'),indent=2)
p=os.path.join(root,'west_streetview_notes.json');notes=json.load(open(p))
new=[{'segment':'UB_X+004','pano':'modALEC3WgErR-jyX2zyUA','date':'2025-05','source_url':url,'observed':['two stone-clad rectangular enclosures on separate medians','low shrub strip','Y15 covered entrance','column base picket guard'],'status':'partial_ground_view','dimensions_verified':False},
{'segment':'UB_X+004','pano':'7jxY9aXs4Z8BllYteOtqlw','date':'2025-05','source_url':'https://www.google.com/maps/@25.0491877,121.5149281,3a,75y,103h,90t/data=!3m4!1e1!3m2!1s7jxY9aXs4Z8BllYteOtqlw!2e0','observed':['Taiyuan junction','long corrugated enclosure/canopy','large exposed white and green pipes','solid roadside wall','traffic signal and control cabinets'],'status':'partial_ground_view_objects_pending','dimensions_verified':False}]
for v in new:
 if not any(x['pano']==v['pano'] for x in notes['views']):notes['views'].append(v)
notes['historical_only_panos']=['Q2f8s_yNPawNoPIM_8kU7g']
notes['unresolved_column_mapping']={'visible_label':'P120','pano':'moMq0z-UBTjiDjOudI-lmw','note':'Observed label; existing legacy pier ID correspondence unconfirmed. Do not attach verified label to a guessed legacy pier.'}
json.dump(notes,open(p,'w'),indent=2,ensure_ascii=False)
# Synchronize partial coverage without promoting any strip to complete.
cp=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260916','underbridge_coverage.json')
coverage=json.load(open(cp))
for seg in coverage['segments']:
 views=[v for v in notes['views'] if v['segment']==seg['id']]
 if views:seg['streetview_status']='partial_ground_view';seg['panorama_refs']=[v['pano'] for v in views]
 seg['dimensions_status']='not_verified'
coverage['complete']=False
json.dump(coverage,open(cp,'w'),indent=2,ensure_ascii=False)
summary={'scope':coverage['scope'],'complete':False,'segments':[{k:v for k,v in s.items() if k!='objects'} for s in coverage['segments']]}
json.dump(summary,open(os.path.join(root,'coverage_progress.json'),'w'),indent=2,ensure_ascii=False)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result=report
