"""Recess the two assumed comparison drains instead of leaving their pans inside solid paving."""
import bpy,json,pathlib,os,math
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];col=bpy.data.collections['CAL3_YANJI_PHOTO_COMPARISON'];assert not bpy.data.collections.get('CAL3_RETAINED_YANJI_DRAIN_SLABS');keep=bpy.data.collections.new('CAL3_RETAINED_YANJI_DRAIN_SLABS');sc.collection.children.link(keep);anchor=Vector((4215.1324,348.2492,0));angle=math.atan2(-5.75,55);d=Vector((math.cos(angle),math.sin(angle),0));n=Vector((-d.y,d.x,0));faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)];created=[];records=[]
def surface(x):
 if x<=0:return 0.,0.
 return .8*(55-x)/25,-1.8-1.8*(x-30)/25
# Only the flat first and final linear slab segments are reconstructed.
def piece(name,a,b,left,right,bot,top,material):
 ya,za=surface(a);yb,zb=surface(b);vs=[(a,ya+left,za+bot),(b,yb+left,zb+bot),(b,yb+right,zb+bot),(a,ya+right,za+bot),(a,ya+left,za+top),(b,yb+left,zb+top),(b,yb+right,zb+top),(a,ya+right,za+top)];me=bpy.data.meshes.new(name);me.from_pydata([tuple(d*x+n*y+Vector((0,0,z))) for x,y,z in vs],[],faces);me.materials.append(material);me.update();o=bpy.data.objects.new(name,me);o.location=anchor;col.objects.link(o);o['status']='Estimated recessed drain on unadopted comparison. Remaining slab thickness is not structurally validated.';created.append(o)
for tag,index,start,end,x in [('UPPER',0,-8,0,-.8),('LOWER',3,30,55,53.5)]:
 old=bpy.data.objects['YANJI_PHOTO_RAMP_'+str(index)];pan=bpy.data.objects['YANJI_DETAIL_DRAIN_PAN_'+tag];mat=old.data.materials[0];dark=pan.data.materials[0]
 for o in [old,pan]:keep.objects.link(o);col.objects.unlink(o)
 a,b=x-.15,x+.15
 for suffix,x0,x1,y0,y1,bot,top in [('BEFORE',start,a,-2.9,2.9,-.2,0),('AFTER',b,end,-2.9,2.9,-.2,0),('LEFT',a,b,-2.9,-2.8,-.2,0),('RIGHT',a,b,2.8,2.9,-.2,0),('UNDER',a,b,-2.8,2.8,-.2,-.15)]:piece('YANJI_RECESSED_'+tag+'_'+suffix,x0,x1,y0,y1,bot,top,mat)
 for suffix,x0,x1,y0,y1,bot,top in [('BASE',a,b,-2.8,2.8,-.15,-.13),('EDGE_A',a,a+.015,-2.8,2.8,-.13,0),('EDGE_B',b-.015,b,-2.8,2.8,-.13,0),('EDGE_L',a+.015,b-.015,-2.8,-2.785,-.13,0),('EDGE_R',a+.015,b-.015,2.785,2.8,-.13,0)]:piece('YANJI_DRAIN_CHANNEL_'+tag+'_'+suffix,x0,x1,y0,y1,bot,top,dark)
 records.append({'drain':tag,'recess_m':.15,'pan_interior_depth_m':.13,'remaining_under_slab_m':.05,'outfall':'not modeled or surveyed','status':'Geometry comparison only; not a drainage or structural design'})
sc.view_layers[0].layer_collection.children[keep.name].exclude=True;r={'drains':records,'old_objects_retained':len(keep.objects),'new_mesh_objects':len(created),'adopted':False};(out/'yanji_drain_recess_report.json').write_text(json.dumps(r,indent=2));bpy.context.window.scene=sc;sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result=r
