"""Replace averaged-carriageway axis with a connected mapped road path, never cutting through blocks."""
import json,pathlib,math,heapq,collections
from shapely.geometry import LineString
from pyproj import Transformer
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Calibration';g=json.load(open('/tmp/civic-calibration/road_graph.json'));adj=collections.defaultdict(dict)
for a,b,d in g['edges']:a=tuple(a);b=tuple(b);adj[a][b]=adj[b][a]=d
start=min(adj);end=max(adj);dist={start:0};prev={};heap=[(0,start)]
while heap:
 dd,a=heapq.heappop(heap)
 if dd!=dist[a]:continue
 if a==end:break
 for b,w in adj[a].items():
  nd=dd+w
  if nd<dist.get(b,float('inf')):dist[b]=nd;prev[b]=a;heapq.heappush(heap,(nd,b))
path=[end]
while path[-1]!=start:path.append(prev[path[-1]])
path.reverse();line=LineString(path);reg=json.load(open(root/'registration.json'));f=reg['live_to_twd97'];ang=math.radians(f['rotation_degrees']);org=[reg['origin_epsg3826'][i]+f['translation'][i] for i in [0,1]];back=Transformer.from_crs(3826,4326,always_xy=True);to=Transformer.from_crs(4326,3826,always_xy=True)
def live(x,y):
 x-=org[0];y-=org[1];return [(math.cos(ang)*x+math.sin(ang)*y)/f['scale'],(-math.sin(ang)*x+math.cos(ang)*y)/f['scale']]
rows=[];ss=list(range(0,int(line.length)+1,200));ss.append(line.length)
for i,s in enumerate(ss):
 p=line.interpolate(s);lon,lat=back.transform(p.x,p.y);q=live(p.x,p.y);n=live(*to.transform(lon,lat+.001));d=math.dist(q,n);label=f'{int(s)//1000:02d}K{int(s)%1000:03d}' if i<len(ss)-1 else 'END';rows.append({'index':i,'chainage_m':s,'label':label,'twd97':[p.x,p.y],'lonlat':[lon,lat],'live_xy':q,'true_north_live_unit':[(n[j]-q[j])/d for j in [0,1]],'regular_200m_station':s%200==0})
old=json.load(open(root/'Cameras_200m/camera_stations.json'));diff=[]
for r in rows:
 before=next((v for v in old['stations'] if v['label']==r['label']),None)
 if before:diff.append({'label':r['label'],'movement_m':math.dist(before['live_xy'],r['live_xy']),'before':before['live_xy'],'after':r['live_xy']})
r={'method':'Shortest continuous undirected path along mapped named tertiary/tertiary_link road segments from westernmost to easternmost road node. Analysis chainage only, not official engineering chainage. Replaces midpoint averaging through Songshan/Nangang buildings. Road XY retained; selection does not validate legal pedestrian/camera placement.','route_length_m':line.length,'axis_twd97':path,'stations':rows,'changes':diff};(out/'corrected_camera_stations.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print({'length_m':line.length,'station_pairs':len(rows),'moves_over20m':sum(v['movement_m']>20 for v in diff),'max_movement_m':max(v['movement_m'] for v in diff)})
