import json,pathlib,math
from shapely.geometry import Polygon,LineString
from shapely import constrained_delaunay_triangles
p=json.load(open('/tmp/civic-parking-segments/sections.json'))
for r in p['sections']:
 r['meshes']=[]
 for level in range(1,r['levels']+1):
  poly=Polygon(r['outline'],r['interlevel_hole'] if level==1 else [])
  assert poly.is_valid
  top=-3.6*level;vs=[];fs=[];index={}
  def vert(x,y,z):
   k=(round(x,6),round(y,6),round(z,6))
   if k not in index:index[k]=len(vs);vs.append(k)
   return index[k]
  for tri in constrained_delaunay_triangles(poly).geoms:
   cs=list(tri.exterior.coords)[:-1];fs.extend([[vert(x,y,top) for x,y in cs],[vert(x,y,top-.3) for x,y in cs[::-1]]])
  for ring in [poly.exterior]+list(poly.interiors):
   cs=list(ring.coords)
   for a,b in zip(cs,cs[1:]):fs.append([vert(*a,top-.3),vert(*b,top-.3),vert(*b,top),vert(*a,top)])
  r['meshes'].append({'name':r['name']+'_B'+str(level),'vertices':vs,'faces':fs})
 if r['levels']==2:
  axis=LineString(r['axis_live']);a=axis.interpolate(axis.length/2-18);b=axis.interpolate(axis.length/2+18);dx,dy=b.x-a.x,b.y-a.y;l=math.hypot(dx,dy);nx,ny=-dy/l,dx/l;vs=[];fs=[]
  for i in range(73):
   t=i/72;dist=l*t;g=-3.6/(l-3)
   dz=g*dist*dist/6 if dist<3 else (-3.6-g*(l-dist)**2/6 if dist>l-3 else g*(dist-1.5))
   x,y=a.x+dx*t,a.y+dy*t;z=-3.6+dz
   vs.extend([(x-nx*1.75,y-ny*1.75,z-.25),(x+nx*1.75,y+ny*1.75,z-.25),(x+nx*1.75,y+ny*1.75,z),(x-nx*1.75,y-ny*1.75,z)])
  for i in range(72):
   a0=i*4;b0=a0+4;fs.extend([(a0,b0,b0+1,a0+1),(a0+1,b0+1,b0+2,a0+2),(a0+2,b0+2,b0+3,a0+3),(a0+3,b0+3,b0,a0)])
  fs.extend([(3,2,1,0),tuple(range(len(vs)-4,len(vs)))])
  r['meshes'].append({'name':r['name']+'_B1_B2_RAMP_ASSUMED','vertices':vs,'faces':fs})
  r['ramp_camera']={'location':[a.x-dx/l*2,a.y-dy/l*2,-1.4],'target':[b.x,b.y,-6.5]}
 # For sections without any mapped candidates, use explicitly estimated source-plan-relative candidates.
 if not r['entrances']:
  fractions=[.30,.78] if r['name']=='林金' else [.08]
  line=LineString(r['axis_live'])
  for i,f in enumerate(fractions):
   q=line.interpolate(line.length*f);r['entrances'].append({'osm_id':None,'xy':[q.x,q.y],'status':'ASSUMED plan-relative entrance candidate; exact association and dimensions unknown'})
p['overlaps']=[]
for i,a in enumerate(p['sections']):
 for b in p['sections'][i+1:]:
  area=Polygon(a['outline']).intersection(Polygon(b['outline'])).area
  if area>1:p['overlaps'].append({'sections':[a['name'],b['name']],'area_m2':area,'status':'Estimated envelope overlap, not confirmed underground connection'})
pathlib.Path('/tmp/civic-parking-segments/payload.json').write_text(json.dumps(p,ensure_ascii=False))
print({'sections':len(p['sections']),'meshes':sum(len(r['meshes']) for r in p['sections']),'overlaps':p['overlaps']})
