import os
import bpy,math,json,pathlib,collections
from mathutils import Vector
sc=bpy.data.scenes['CIVIC_UNDERBRIDGE_MASSING_20260916'];out=pathlib.Path(bpy.data.filepath).parent/'Underbridge_20260916'
assert not bpy.data.collections.get('UB_LINSEN_FIXED_OBJECTS_EST')
col=bpy.data.collections.new('UB_LINSEN_FIXED_OBJECTS_EST');sc.collection.children.link(col);bpy.data.scenes['UB_LINSEN_REVIEW_20260916'].collection.children.link(col)
mat={}
for k,c in [('structure',(.7,.71,.67,1)),('equipment',(.64,.57,.42,1)),('fence',(.27,.29,.27,1))]:
 m=bpy.data.materials.new('UB_LINSEN_'+k);m.diffuse_color=c;mat[k]=m
origin=Vector((1434,709.2818876,0));names=[]
def mesh(name,vs,fs,kind):
 me=bpy.data.meshes.new(name);me.from_pydata([Vector(v)-origin for v in vs],[],fs);me.materials.append(mat[kind]);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);o.location=origin;o['source_pano']='CIABIhBqmk8t_Jr0KkpQi4oI1qoM';o['confidence']='Observed type; XY, metric size and elevation ESTIMATED. Not dimension-verified.';o['position_method']='First pier pair working station x1434; transverse OSM deck axes. Longitudinal position NOT triangulated.';names.append(o.name)
def cube(name,c,d,kind):
 v=[(c[0]+x*d[0]/2,c[1]+y*d[1]/2,c[2]+z*d[2]/2) for z in [-1,1] for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]];mesh(name,v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],kind)
def ring(name,x,y,outer,inner,lo,hi,kind):
 n=32;v=[(x+r*math.cos(i*2*math.pi/n),y+r*math.sin(i*2*math.pi/n),z) for z,r in [(lo,outer),(hi,outer),(lo,inner),(hi,inner)] for i in range(n)];f=[]
 for i in range(n):
  j=(i+1)%n;f.extend([(i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j),(n+i,n+j,3*n+j,3*n+i),(j,i,2*n+i,2*n+j)])
 mesh(name,v,f,kind)
for label,y in [('N',715.2883353),('S',703.2754399)]:
 # Solid column cylinder, no internal hole.
 n=32;v=[(1434+math.cos(i*2*math.pi/n),y+math.sin(i*2*math.pi/n),z) for z in [.18,4.8] for i in range(n)];f=[list(reversed(range(n))),list(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)];mesh('UB_LINSEN_FIRST_COLUMN_'+label+'_EST',v,f,'structure')
 ring('UB_LINSEN_COLUMN_GUARD_'+label+'_EST',1434,y,1.32,1.24,.18,1.03,'fence')
cube('UB_LINSEN_CROSSHEAD_EST',(1434,709.2818876,5.2),(2,14.2,.8),'structure')
cube('UB_LINSEN_EQUIPMENT_ENCLOSURE_EST',(1440,707.9,1.28),(3,1.8,2.2),'equipment')
errors=[]
for o in col.objects:
 ec=collections.Counter(tuple(sorted(e)) for p in o.data.polygons for e in p.edge_keys)
 if any(n!=2 for n in ec.values()):errors.append(o.name)
assert not errors
r={'new_objects':names,'mesh_errors':errors,'status':'Provisional massing, not final calibration','assumptions':['First-pair longitudinal station x1434 provisional','Transverse positions use mapped deck axes','Column diameter2m, existing deck-height assumption retained','Fence represented as solid volume, not actual opaque surface','Equipment position/size approximate'],'remaining':['Confirm against second pano or measured plan','Trim landscaping at actual base locations','Check median containment and road clearance','Add signals only after pose identification']};(out/'linsen_fixed_objects_report.json').write_text(json.dumps(r,indent=2));sc['status']='Partial Linsen fixed-object masses added; all positions/dimensions awaiting final calibration';review=bpy.data.scenes['UB_LINSEN_REVIEW_20260916'];bpy.context.window.scene=review;bpy.ops.render.render(write_still=True,scene=review.name);sc.collection.children.unlink(col);r['adopted_in_working_scene']=False;r['placement_conflict']='Tentative south column outside existing median; keep in review only';(out/'linsen_fixed_objects_report.json').write_text(json.dumps(r,indent=2));bpy.context.window.scene=sc;bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result=r
