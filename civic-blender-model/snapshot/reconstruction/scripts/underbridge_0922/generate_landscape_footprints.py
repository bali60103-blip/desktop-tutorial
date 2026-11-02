"""Generate estimated hedge footprints within existing median, excluding ramps and objects.
No generated coordinate or dimension is a survey measurement.
"""
import json,sys
from shapely.geometry import Polygon,box,LineString
from shapely.ops import unary_union
root=sys.argv[1]
data=json.load(open(root+'/landscape_context.json'))['geometry']
med=[]
blocks=[]
for ob in data:
 if 'vertices' in ob:
  vs=ob['vertices'];ps=[]
  for f in ob['faces']:
   if min(vs[i][2] for i in f)>.17:
    p=Polygon([(vs[i][0],vs[i][1]) for i in f])
    if p.is_valid and p.area>1e-6:ps.append(p)
  med.append(unary_union(ps))
 else:
  a,b=ob['bounds'];blocks.append(box(a[0],a[1],b[0],b[1]).buffer(.45))
median=unary_union(med).buffer(-.3)
blocked=unary_union(blocks)
# Gaps deliberately left at junctions, access ramps and approximate transverse paths.
ranges=[(1110,1185,'SBu9uXniGhP4O-HNyevkIw',1),
(1240,1288,'ZgE-HFiWqHTECOSw8S6Kgg',1),
(1294,1320,'ZgE-HFiWqHTECOSw8S6Kgg',1),
(1350,1367,'ZgE-HFiWqHTECOSw8S6Kgg',1),
(1458,1478,'g1qfNHBGxt8bQ9Mxtk4-WQ',2),
(1524,1542,'9Xu4q5UelsxwgV3WUg6tDg',2),
(1547,1566,'9Xu4q5UelsxwgV3WUg6tDg',2),
(1602,1634,'kQpshBYGSJVRbdO4dhjoBg',2),
(1645,1671,'kQpshBYGSJVRbdO4dhjoBg',2),
(1676,1696,'kQpshBYGSJVRbdO4dhjoBg',2),
(1702,1722,'EJnaX5A24nUes5wWotO5yg',2),
(1728,1743,'EJnaX5A24nUes5wWotO5yg',2),
(1773,1800,'Jse0dXNcWtnaiOTs5a4Vqw',1),
(1806,1832,'Jse0dXNcWtnaiOTs5a4Vqw',1),
(1840,1897,'Jse0dXNcWtnaiOTs5a4Vqw',1)]
out=[]
for start,end,pano,nrows in ranges:
 for side in ([1,-1] if nrows==2 else [1]):
  points=[]
  for x in range(start,end+1,2):
   cut=median.intersection(LineString([(x,400),(x,850)]))
   if cut.is_empty:continue
   y=(cut.bounds[3]-.8) if side==1 else (cut.bounds[1]+.8)
   points.append((x,y))
  if len(points)<2:continue
  geom=LineString(points).buffer(.55,cap_style=2).intersection(median).difference(blocked)
  parts=list(geom.geoms) if hasattr(geom,'geoms') else [geom]
  for p in parts:
   if p.geom_type!='Polygon' or p.area<.5:continue
   out.append({'id':f'HEDGE_{start}_{side}_{len(out):03d}','pano':pano,'outer':list(p.exterior.coords)[:-1],'holes':[list(r.coords)[:-1] for r in p.interiors],'height':.65,'base_z':.18,'area':p.area})
json.dump({'footprints':out,'full_corridor_complete':False,'dimensions_verified':False,'method':'Manual visible hedge ranges; median-constrained estimated footprints; existing obstruction buffers retained','limitations':['Cross-path locations estimated','Existing median and obstruction coordinates are unverified','Only photographed ranges represented']},open(root+'/landscape_011_018_manifest.json','w'),indent=2)
print(json.dumps({'count':len(out),'area':sum(x['area'] for x in out)}))
