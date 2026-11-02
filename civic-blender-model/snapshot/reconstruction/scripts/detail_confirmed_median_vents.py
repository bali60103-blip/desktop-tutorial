"""Detail eight officially labeled vent proxies within their existing estimated envelopes."""
import bpy,json,os,pathlib,math
from mathutils import Vector,Matrix
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;sc.view_layers[0].update();name='CAL3_MEDIAN_VENT_LOUVERS_EST';assert not bpy.data.collections.get(name),'Already built';col=bpy.data.collections.new(name);sc.collection.children.link(col);bpy.data.scenes['GONGZHONG_INTEGRATED_OPENINGS_EST'].collection.children.link(col);ret=bpy.data.collections.new('CAL3_RETAINED_MEDIAN_VENT_BLOCKS');sc.collection.children.link(ret);sc.view_layers[0].layer_collection.children[ret.name].exclude=True;steel=bpy.data.materials.new('CAL3_MEDIAN_LOUVER_METAL_EST');steel.diffuse_color=(.31,.35,.36,1);base=bpy.data.materials.new('CAL3_MEDIAN_VENT_CONCRETE_EST');base.diffuse_color=(.58,.57,.53,1);report=[]
for source in list(bpy.data.collections['COMPLETION_EQUIPMENT'].objects):
 if not source.name.startswith('COMP_MEDIAN_'):continue
 metadata=json.loads(source.get('source_metadata','{}'))
 if metadata.get('type') not in ['進風口','排風口']:continue
 wvs=[source.matrix_world@v.co for v in source.data.vertices];z0=min(v.z for v in wvs);z1=max(v.z for v in wvs);edges={}
 for p in source.data.polygons:
  if all(abs(wvs[i].z-z1)<1e-4 for i in p.vertices):
   for a,b in p.edge_keys:k=tuple(sorted((a,b)));edges[k]=edges.get(k,0)+1
 boundary=[e for e,c in edges.items() if c==1];assert boundary,source.name;ia,ib=max(boundary,key=lambda e:(wvs[e[1]]-wvs[e[0]]).length);h=(wvs[ib]-wvs[ia]).normalized();n=Vector((-h.y,h.x,0));center=sum((wvs[i] for i in set(i for e in boundary for i in e)),Vector())/len(set(i for e in boundary for i in e));center.z=z0;xx=[(v-center).dot(h) for v in wvs];yy=[(v-center).dot(n) for v in wvs];xmin,xmax=min(xx),max(xx);ymin,ymax=min(yy),max(yy);height=z1-z0;vs=[];fs=[];material=[]
 def box(x0,x1,y0,y1,bottom,top,mi=0,angle=0):
  k=len(vs);cy=(y0+y1)/2;cz=(bottom+top)/2
  for z in [bottom,top]:
   for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]:
    yr=cy+(y-cy)*math.cos(angle)-(z-cz)*math.sin(angle);zr=cz+(y-cy)*math.sin(angle)+(z-cz)*math.cos(angle);vs.append(tuple(h*x+n*yr+Vector((0,0,zr))))
  fs.extend([[k+i for i in f] for f in [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]]);material.extend([mi]*6)
 box(xmin,xmax,ymin,ymax,0,.12);box(xmin,xmax,ymin,ymax,height-.10,height);box(xmin,xmin+.12,ymin,ymax,.12,height-.1);box(xmax-.12,xmax,ymin,ymax,.12,height-.1)
 for y in [ymin+.085,ymax-.085]:
  for x in [xmin+.16,xmax-.16]:box(x-.035,x+.035,y-.03,y+.03,.12,height-.1,1)
 count=max(2,int((height-.35)/.12))
 for j in range(count):
  z=.22+j*(height-.44)/(count-1)
  for y,angle in [(ymin+.085,math.radians(-30)),(ymax-.085,math.radians(30))]:box(xmin+.2,xmax-.2,y-.06,y+.06,z-.012,z+.012,1,angle)
 m=bpy.data.meshes.new('VENT_DETAIL_'+metadata['id']);m.from_pydata(vs,[],fs);m.materials.append(base);m.materials.append(steel);m.update()
 for p,mi in zip(m.polygons,material):p.material_index=mi
 o=bpy.data.objects.new(m.name,m);o.location=center;col.objects.link(o);o['source_proxy']=source.name;o['source_metadata']=source['source_metadata'];o['verification_status']='Official plan confirms function only. Estimated two-sided louvers, housing and original position/size; no street-photo matching.';o['louver_pitch_target_m']=.12
 for v in m.vertices:
  assert xmin-1e-4<=v.co.dot(h)<=xmax+1e-4 and ymin-1e-4<=v.co.dot(n)<=ymax+1e-4 and -1e-4<=v.co.z<=height+1e-4
 ret.objects.link(source)
 for c in list(source.users_collection):
  if c!=ret and c.name in ['COMPLETION_EQUIPMENT','GZI_COMPLETION_EQUIPMENT']:c.objects.unlink(source)
 report.append({'source':source.name,'detail':o.name,'type':metadata['type'],'louver_blades':2*count,'envelope_preserved':True,'source_url':metadata['source']})
r={'vents_detailed':len(report),'louver_blades':sum(x['louver_blades'] for x in report),'items':report,'limits':'Four tank blocks and two exhaust-outlet blocks retained without invented shapes. OSM candidates outside median not reclassified. Vent housing positions, sizes and louver geometry are estimates.'};(out/'median_vent_detail_report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result=r
