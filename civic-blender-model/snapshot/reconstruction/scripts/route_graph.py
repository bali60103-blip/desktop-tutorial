import json,re,math,collections,heapq
from pyproj import Transformer
p=json.load(open('/tmp/civic-stage01/civic_all_named_ways.geojson'))['features'];to=Transformer.from_crs(4326,3826,always_xy=True);adj=collections.defaultdict(dict)
for f in p:
 t=f['properties']
 if not re.fullmatch('市民大道[一二三四五六七八]段',t.get('name','')) or t.get('highway') not in ['tertiary','tertiary_link'] or t.get('bridge')=='yes' or t.get('tunnel')=='yes':continue
 coords=[tuple(round(v,3) for v in to.transform(*q)) for q in f['geometry']['coordinates']]
 for a,b in zip(coords,coords[1:]):adj[a][b]=adj[b][a]=math.dist(a,b)
seen=set();comps=[]
for a in adj:
 if a in seen:continue
 stack=[a];c=[];seen.add(a)
 while stack:
  v=stack.pop();c.append(v)
  for w in adj[v]:
   if w not in seen:seen.add(w);stack.append(w)
 comps.append(c)
print([(len(c),min(x[0] for x in c),max(x[0] for x in c)) for c in sorted(comps,key=len,reverse=True)])
json.dump({'nodes':[list(k) for k in adj],'edges':[[list(a),list(b),d] for a,row in adj.items() for b,d in row.items() if a<b]},open('/tmp/civic-calibration/road_graph.json','w'))
