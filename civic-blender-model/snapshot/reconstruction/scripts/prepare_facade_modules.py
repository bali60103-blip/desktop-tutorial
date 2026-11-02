"""Parametric recessed facades on mapped footprints. All facade proportions are estimated."""
import json,pathlib,math,collections,re
from shapely.geometry import shape,Polygon,Point,LineString
from shapely.geometry.polygon import orient
from shapely import make_valid,set_precision,constrained_delaunay_triangles,STRtree
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'BlockFacades';rows=json.load(open(out/'buildings_selected.json'));payload=[];issues=[];modules=collections.Counter();streetlines=[LineString(r['xy']) for r in json.load(open(out/'source/streets_plan_boundaries.json'))];streettree=STRtree(streetlines);building_geoms=[shape(r['geometry']) for r in rows];building_tree=STRtree(building_geoms)
def extrude(g,z0,z1):
 vs=[];fs=[];ids={}
 def idx(x,y,z):
  k=(round(x,6),round(y,6),round(z,6))
  if k not in ids:ids[k]=len(vs);vs.append(k)
  return ids[k]
 for t in constrained_delaunay_triangles(g).geoms:
  pts=list(orient(t,sign=1).exterior.coords)[:3];fs.append([idx(x,y,z1) for x,y in pts]);fs.append([idx(x,y,z0) for x,y in pts[::-1]])
 for ring in [g.exterior,*g.interiors]:
  cc=list(ring.coords)
  for a,b in zip(cc,cc[1:]):fs.append([idx(*a,z0),idx(*b,z0),idx(*b,z1),idx(*a,z1)])
 return {'vertices':vs,'faces':fs}
def number(v):
 try:return float(re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)',str(v)).group(1))
 except:return None
for r in rows:
 g=make_valid(shape(r['geometry']));polys=[g] if g.geom_type=='Polygon' else [p for p in g.geoms if p.geom_type=='Polygon'];t=r['tags'];height=r['height_m'];base=r['base_z_m'];btype=t.get('building:part',t.get('building','yes'));canopy=btype in ['roof','carport'];name=r['name'];kind=1 if btype in ['commercial','office','retail','hotel','hospital','civic','public','train_station','transportation'] else (2 if btype in ['industrial','warehouse','garages','garage','service'] else 0);tagged_levels=number(t.get('building:levels'));minlevels=number(t.get('building:min_level')) or (round(base/3.3) if base else 0)
 if r['osm_id']=='w1299938983':tagged_levels=17;issues.append({'id':r['osm_id'],'type':'floor_count_conflict','detail':'Architect publication17F vs OSM21levels; facade uses17 intervals with81m total height, floor spacing still inferred.'})
 if canopy and 'height' not in t:height=4.5;issues.append({'id':r['osm_id'],'type':'canopy_height_estimate','detail':'4.5m canopy estimate replaces inappropriate neighboring-building height; supports estimated.'})
 points=[];cores=[];roofmeshes=[];ringcount=0
 for pi,p in enumerate(polys):
  p=orient(set_precision(p.simplify(.06,preserve_topology=True),.001),sign=1)
  if p.area<4:continue
  if canopy:
   cores.append(extrude(p,height-.2,height));rr=p.minimum_rotated_rectangle
   for a in list(rr.exterior.coords)[:4]:
    q=set_precision(Point(a).buffer(.14,quad_segs=2).intersection(p),.001)
    if not q.is_empty and q.area>.001 and q.geom_type=='Polygon':cores.append(extrude(orient(q),base,height-.2))
   continue
  walltop=height-.55;roofh=number(t.get('roof:height')) or 0;roofmode=t.get('roof:shape','flat');roofok=False
  if roofmode in ['pyramidal','pyramid'] and 0<roofh<height-base-2 and not p.interiors:
   c=p.centroid;xy=list(p.exterior.coords)[:-1];tris=[Polygon([a,b,(c.x,c.y)]) for a,b in zip(xy,xy[1:]+xy[:1])]
   if all(p.buffer(.001).covers(q) for q in tris):
    walltop=height-roofh;v=[(x,y,walltop) for x,y in xy]+[(c.x,c.y,height)];f=[[i,(i+1)%len(xy),len(xy)] for i in range(len(xy))];lookup={(round(q[0],6),round(q[1],6)):i for i,q in enumerate(xy)}
    for tri in constrained_delaunay_triangles(p).geoms:
     face=[]
     for xx,yy in list(orient(tri,sign=1).exterior.coords)[:3][::-1]:
      k=(round(xx,6),round(yy,6))
      if k not in lookup:lookup[k]=len(v);v.append((xx,yy,walltop))
      face.append(lookup[k])
     f.append(face)
    roofmeshes.append({'vertices':v,'faces':f,'status':'OSM roof shape and height; simplified single apex'});roofok=True
  wallheight=max(.4,walltop-base);lev=max(1,int(round(tagged_levels-minlevels))) if tagged_levels else max(1,int(round(wallheight/3.3)));lev=min(80,lev);fh=wallheight/lev
  if fh<1.5:lev=max(1,int(wallheight/2.8));fh=wallheight/lev
  core=set_precision(p.buffer(-.19,join_style=2),.001)
  if core.is_empty:core=p;issues.append({'id':r['osm_id'],'type':'thin_footprint','detail':'Core inset unavailable; retained solid footprint'})
  for cp in ([core] if core.geom_type=='Polygon' else core.geoms):
   if cp.geom_type=='Polygon' and cp.area>.01:cores.append(extrude(orient(cp),base,walltop))
  rings=[p.exterior,*p.interiors];door_done=False;ec=list(p.exterior.coords);candidates=[(Point((a[0]+b[0])/2,(a[1]+b[1])/2).distance(streetlines[int(streettree.nearest(Point((a[0]+b[0])/2,(a[1]+b[1])/2)))]),i) for i,(a,b) in enumerate(zip(ec,ec[1:])) if math.dist(a,b)>1.1];door_edge=min(candidates)[1] if candidates else -1
  for ring in rings:
   cc=list(ring.coords)
   for ei,(a,b) in enumerate(zip(cc,cc[1:])):
    L=math.dist(a,b)
    if L<.08:continue
    angle=math.atan2(b[1]-a[1],b[0]-a[0]);bays=max(1,int(round(L/(4.5 if kind==2 else 3.2))));bw=L/bays
    for bay in range(bays):
     x=a[0]+(b[0]-a[0])*(bay+.5)/bays;y=a[1]+(b[1]-a[1])*(bay+.5)/bays
     outward=(math.sin(angle),-math.cos(angle));probe=Point(x+outward[0]*.3,y+outward[1]*.3);neighbors=[int(ii) for ii in building_tree.query(probe.buffer(1)) if rows[int(ii)]['osm_id']!=r['osm_id']]
     for floor in range(lev):
      module=kind
      if bw<1.1 or fh<1.5:module=4
      elif base==0 and floor==0 and not door_done and ring is rings[0] and ei==door_edge and bay==bays//2:module=3;door_done=True
      elif kind==0 and floor>0 and 2.9<fh<3.9 and bw>2 and (floor+bay)%4==0:module=5
      midz=base+(floor+.5)*fh
      cover=[ii for ii in neighbors if rows[ii]['base_z_m']<midz<rows[ii]['height_m'] and building_geoms[ii].covers(probe)]
      if cover:module=4
      elif module==5:
       far=Point(x+outward[0]*.95,y+outward[1]*.95)
       if any(rows[ii]['base_z_m']<midz<rows[ii]['height_m'] and building_geoms[ii].distance(far)<bw*.45 for ii in neighbors):module=0
      points.append({'position':[x,y,base+(floor+.5)*fh],'scale':[bw,1,fh],'rotation':[0,0,angle],'module':module});modules[str(module)]+=1
     if not roofok:points.append({'position':[x,y,height-.275],'scale':[bw,1,.55],'rotation':[0,0,angle],'module':4});modules['4']+=1
    ringcount+=1
  if not door_done and base==0:issues.append({'id':r['osm_id'],'type':'entry_not_identified','detail':'No sufficiently wide exterior segment; no inferred door carved'})
 payload.append({'osm_id':r['osm_id'],'name':name,'block_id':r['block_id'],'first_row':r['first_row'],'height_m':height,'base_z_m':base,'height_status':r['height_status'],'facade_status':'Estimated repeating recessed-window modules and inferred entry; no street-photo correspondence claimed','is_building_part':r['is_building_part'],'cores':cores,'roofs':roofmeshes,'points':points})
(out/'facade_payload.json').write_text(json.dumps(payload,ensure_ascii=False));summary={'building_records':len(payload),'core_mesh_components':sum(len(r['cores']) for r in payload),'facade_instances':sum(len(r['points']) for r in payload),'module_counts':dict(modules),'issues':issues,'approach':'Reusable recessed-wall, inset-glass, sill, service-louver, door and parapet modules. Geometry Nodes instances remain unrealized for performance. Roof outlines from mapped footprints; detailed proportions estimated.'};(out/'facade_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print({k:v for k,v in summary.items() if k!='issues'});print('issues',len(issues))
