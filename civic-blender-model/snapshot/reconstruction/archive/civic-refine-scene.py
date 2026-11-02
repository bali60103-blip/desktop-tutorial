import bpy,json,pathlib,math
from mathutils import Vector
P=pathlib.Path('/tmp/civic-rebuild');root=pathlib.Path((P/'output_root.txt').read_text());scene=bpy.context.scene
coll=bpy.data.collections['07_Piers_legacy_UNVERIFIED']
deckdata=json.loads((P/'build_payload.json').read_text())['objects'];decklines=[]
reg=json.loads((P/'registration.json').read_text());origin=[reg['origin_epsg3826'][i]+reg['live_to_twd97']['translation'][i] for i in range(2)]
for w in json.loads((P/'osm.json').read_text())['ways']:
 if w['tags'].get('highway')=='trunk' and '市民大道高架' in w['tags'].get('name',''):
  pts=[Vector((x-origin[0],y-origin[1])) for x,y in w['xy']];width=int(w['tags'].get('lanes','2'))*3.25+2
  for a,b in zip(pts,pts[1:]):decklines.append((a,b,width))
def nearest(p):
 best=None
 for a,b,width in decklines:
  v=b-a;t=max(0,min(1,(p-a).dot(v)/max(v.length_squared,1e-8)));q=a+v*t;dist=(p-q).length
  if best is None or dist<best[0]:best=(dist,q,v.normalized(),width)
 return best
caps=0
for o in list(coll.objects):
 pts=[o.matrix_world@v.co for v in o.data.vertices];center=sum(pts,Vector())/len(pts);x,y=center.x,center.y;material=o.data.materials[0]
 vs=[];faces=[];N=24
 for z in [0,4.8]:
  for j in range(N):vs.append((x+math.cos(j*2*math.pi/N),y+math.sin(j*2*math.pi/N),z))
 faces.append(tuple(reversed(range(N))));faces.append(tuple(range(N,N*2)))
 for j in range(N):k=(j+1)%N;faces.append((j,k,k+N,j+N))
 me=bpy.data.meshes.new(o.name+'_circular');me.from_pydata(vs,[],faces);me.materials.append(material);o.data=me;o['confidence']='Legacy unverified XY. Circular 2m diameter shaft + estimated cap; circular form referenced to user PDF BEFORE photos, dimensions not measured.'
 _,q,v,width=nearest(Vector((x,y)));n=Vector((-v.y,v.x));vertices=[]
 for z in [4.8,5.6]:
  for along,across in [(-.75,-width*.43),(.75,-width*.43),(.75,width*.43),(-.75,width*.43)]:
   p=Vector((x,y))+v*along+n*across;vertices.append((p.x,p.y,z))
 me=bpy.data.meshes.new(o.name+'_cap');me.from_pydata(vertices,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);me.materials.append(material);cap=bpy.data.objects.new(o.name+'_CAP_ESTIMATED',me);coll.objects.link(cap);cap['confidence']='Hypothetical support cap, not as-built geometry';caps+=1
# Correct the inspection camera to the actual bridge axis.
cam=bpy.data.objects['CAM_02_Jinshan_detail'];cam.location=(2210,370,85);target=Vector((2100,510,5));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=190
# Named reference anchors retain precise OSM identities without claiming measured height.
refs=bpy.data.collections.new('12_Landmark_reference_anchors');bpy.data.collections['CIVIC_REBUILD__METERS__SOURCE_TAGGED'].children.link(refs)
matched=json.loads((P/'building_matches.json').read_text());ids={m['osm_id']:m for m in matched if m.get('name')};n=0
for w in json.loads((P/'osm.json').read_text())['ways']:
 if w['id'] in ids and w['tags'].get('name') in ['台北車站','臺北車站','三創生活園區','微風廣場','凱撒大飯店']:
  xy=w['xy'][:-1];x=sum(p[0] for p in xy)/len(xy)-origin[0];y=sum(p[1] for p in xy)/len(xy)-origin[1];o=bpy.data.objects.new('REF_'+w['tags']['name'],None);refs.objects.link(o);o.location=(x,y,2);o.empty_display_size=8;o.show_name=True;o['osm_id']=w['id'];o['footprint_match']=json.dumps(ids[w['id']],ensure_ascii=False);o['height_status']='Existing massing height unverified';n+=1
scene.camera=cam;scene['CIVIC_CURRENT_WARNING']='Amber columns are unverified legacy positions; do not treat as real pillar survey.'
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result={'caps_added':caps,'reference_anchors':n}
