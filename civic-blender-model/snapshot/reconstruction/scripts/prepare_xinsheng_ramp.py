import os,json,pathlib,math
from shapely.geometry import LineString,Point,Polygon,box,mapping
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
from shapely import constrained_delaunay_triangles
root=pathlib.Path(os.environ['CIVIC_MODEL_ROOT']);out=root/'PriorityNodes_20260914';reg=json.load(open(root/'registration.json'));o=reg['origin_epsg3826'];t=reg['live_to_twd97'];ang=math.radians(t['rotation_degrees']);c=math.cos(ang);s=math.sin(ang)
def live(p):
 x=p[0]-o[0]-t['translation'][0];y=p[1]-o[1]-t['translation'][1];return [(c*x+s*y)/t['scale'],(-s*x+c*y)/t['scale']]
ways={w['id']:w for w in json.load(open(root/'data/osm.json'))['ways']};ids=[51362366,51362367,51362403,51362368];lines={i:LineString([live(p) for p in ways[i]['xy']]) for i in ids};shared=LineString(list(lines[51362403].coords)+list(lines[51362368].coords)[1:]);L=shared.length
# West shared split meets existing mainline at estimated z=8m. East ramp mouth z=.15m.
def height(x,y):
 q=shared.project(Point(x,y))/L;return 8-(8-.15)*(3*q*q-2*q*q*q)
footprint=unary_union([line.buffer(4.0 if i in [51362403,51362368] else 2.25,cap_style=2,join_style=2) for i,line in lines.items()]);footprint=orient(footprint,1)
# Densify edges and triangulation with transverse cuts to retain the variable profile.
cuts=[footprint]
for distance in range(5,int(L),5):
 p=shared.interpolate(distance);a=shared.interpolate(max(0,distance-.1));b=shared.interpolate(min(L,distance+.1));dx,dy=b.x-a.x,b.y-a.y;n=math.hypot(dx,dy);dx/=n;dy/=n
 # long halfplane split via shapely split
 from shapely.ops import split
 cutter=LineString([(p.x-dy*100,p.y+dx*100),(p.x+dy*100,p.y-dx*100)])
 cuts=[v for g in cuts for v in split(g,cutter).geoms if v.area>.000001]
def mesh_polys(polys,zlo,zhi):
 vs=[];fs=[];idx={};coverage=unary_union(polys)
 def vert(x,y,z):
  offset=round(z-height(x,y),4);x=round(x,5);y=round(y,5);k=(x,y,round(height(x,y)+offset,5))
  if k not in idx:idx[k]=len(vs);vs.append(list(k))
  return idx[k]
 for poly in polys:
  for tri in constrained_delaunay_triangles(orient(poly,1)).geoms:
   co=list(orient(tri,1).exterior.coords)[:-1];fs.append([vert(x,y,height(x,y)+zhi) for x,y in co]);fs.append([vert(x,y,height(x,y)+zlo) for x,y in reversed(co)])
 # Boundary subdivided by cut intersections, ensuring same vertices as triangulation.
 edges={}
 for poly in polys:
  for ring in [poly.exterior,*poly.interiors]:
   co=list(ring.coords)
   for a,b in zip(co,co[1:]):
    k=tuple(sorted((tuple(round(v,5) for v in a),tuple(round(v,5) for v in b))))
    edges[k]=edges.get(k,0)+1
 for (a,b),count in edges.items():
  if count!=1:continue
  # Orient boundary by testing which side lies inside footprint.
  dx,dy=b[0]-a[0],b[1]-a[1];norm=math.hypot(dx,dy);mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
  if not coverage.covers(Point(mid[0]-dy/norm*.001,mid[1]+dx/norm*.001)):a,b=b,a
  fs.append([vert(*a,height(*a)+zlo),vert(*b,height(*b)+zlo),vert(*b,height(*b)+zhi),vert(*a,height(*a)+zhi)])
 return {'vertices':vs,'faces':fs}
pieces=[{'name':'P1_XINSHENG_RAMP_DECK_%03d_EST'%i,'material':'ROAD','mesh':mesh_polys([p.simplify(1e-8)],-.45,0)} for i,p in enumerate(cuts)]
# Separate simple closed prism pieces for edge barriers; skip all three open mouths.
endpoints=[Point(lines[51362366].coords[-1]),Point(lines[51362367].coords[0]),Point(shared.coords[-1])]
def strip(a,b,width,zlo,zhi):
 dx,dy=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dy);nx=-dy/l*width/2;ny=dx/l*width/2;corners=[(a[0]-nx,a[1]-ny),(b[0]-nx,b[1]-ny),(b[0]+nx,b[1]+ny),(a[0]+nx,a[1]+ny)];vs=[[x,y,height(x,y)+z] for z in [zlo,zhi] for x,y in corners];return {'vertices':vs,'faces':[[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]}
co=list(footprint.exterior.coords)
for edge,(a,b) in enumerate(zip(co,co[1:])):
 mid=Point((a[0]+b[0])/2,(a[1]+b[1])/2)
 if any(mid.distance(p)<4.2 for p in endpoints):continue
 length=math.dist(a,b);num=max(1,math.ceil(length/5))
 for j in range(num):
  p=[a[k]+(b[k]-a[k])*j/num for k in range(2)];q=[a[k]+(b[k]-a[k])*(j+1)/num for k in range(2)];pieces.append({'name':'P1_XIN_RAMP_EDGE_%d_%d'%(edge,j),'material':'CONCRETE','mesh':strip(p,q,.28,0,.95)})
# Double yellow lines and flexible posts seen in Street View; sizes/spacing estimated.
for offset in [-.12,.12]:
 line=shared.offset_curve(offset)
 for j in range(math.ceil(line.length/4)):
  a=line.interpolate(min(line.length,j*4));b=line.interpolate(min(line.length,(j+1)*4))
  if a.distance(b)<.001:continue
  pieces.append({'name':'P1_XIN_DOUBLE_YELLOW_%s_%d'%(offset,j),'material':'YELLOW','mesh':strip(a.coords[0],b.coords[0],.1,.006,.012)})
for j in range(8,int(L)-8,8):
 p=shared.interpolate(j);a=(p.x-.045,p.y);b=(p.x+.045,p.y);pieces.append({'name':'P1_XIN_DELINEATOR_'+str(j),'material':'YELLOW','mesh':strip(a,b,.09,.015,.765)})
# Per-piece closedness check. Main continuous slab may expose seam issues for correction.
errors=[]
for p in pieces:
 counts={}
 for f in p['mesh']['faces']:
  for a,b in zip(f,f[1:]+f[:1]):k=tuple(sorted((a,b)));counts[k]=counts.get(k,0)+1
 if any(v!=2 for v in counts.values()):errors.append({'name':p['name'],'bad_edges':sum(v!=2 for v in counts.values())})
assert not errors,errors
r={'osm_ids':ids,'shared_length_m':L,'width_estimates_m':{'shared':8,'branches':4.5},'endpoint_elevations_est_m':{'west':8,'east':.15},'max_profile_grade_est':1.5*7.85/L,'footprint':mapping(footprint),'shared_axis':mapping(shared),'pieces':pieces,'limitations':['Widths, smooth vertical profile, 0.45m slab, barrier heights and post spacing are estimates','Support geometry not reconstructed until mainline/ramp ownership and clearance are checked','Existing mainline barriers may obstruct ramp entry/exit; flag and inspect before adoption'],'source':'junction_ramp_streetview_20260914.json'};(out/'xinsheng_ramp_payload.json').write_text(json.dumps(r,ensure_ascii=False));print({'pieces':len(pieces),'length':L,'max_grade':r['max_profile_grade_est'],'mesh_errors':errors})
