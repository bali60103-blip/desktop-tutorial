"""200m chainage on a derived boulevard analysis axis, not official engineering chainage.
Average the two carriageways via median northing at 10m easting intervals.
"""
import json,pathlib,math,re,statistics
from shapely.geometry import LineString,Point
from pyproj import Transformer
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Cameras_200m';out.mkdir(exist_ok=True)
reg=json.load(open(root/'registration.json'));fit=reg['live_to_twd97'];ang=math.radians(fit['rotation_degrees']);org=[reg['origin_epsg3826'][i]+fit['translation'][i] for i in (0,1)];to=Transformer.from_crs(4326,3826,always_xy=True);back=Transformer.from_crs(3826,4326,always_xy=True)
def live(x,y):
 x-=org[0];y-=org[1];return [(math.cos(ang)*x+math.sin(ang)*y)/fit['scale'],(-math.sin(ang)*x+math.cos(ang)*y)/fit['scale']]
lines=[]
for f in json.load(open('/tmp/civic-stage01/civic_all_named_ways.geojson'))['features']:
 t=f['properties']
 if re.fullmatch('市民大道[一二三四五六七八]段',t.get('name','')) and t.get('bridge')!='yes' and t.get('tunnel')!='yes':lines.append((t,LineString([to.transform(*q) for q in f['geometry']['coordinates']])))
xmin=min(l.bounds[0] for t,l in lines);xmax=max(l.bounds[2] for t,l in lines);axis=[];skipped=[]
for k in range(math.ceil((xmax-xmin)/10)+1):
 x=min(xmin+k*10,xmax);ys=[]
 for t,l in lines:
  coords=list(l.coords)
  for a,b in zip(coords,coords[1:]):
   if min(a[0],b[0])-1e-8<=x<=max(a[0],b[0])+1e-8:
    if abs(b[0]-a[0])<1e-8:ys.extend([a[1],b[1]])
    else:ys.append(a[1]+(x-a[0])/(b[0]-a[0])*(b[1]-a[1]))
 if ys:axis.append((x,statistics.median(ys)))
 else:skipped.append(x)
line=LineString(axis);stations=[float(s) for s in range(0,int(line.length)+1,200)]
if line.length-stations[-1]>1:stations.append(line.length)
rows=[]
for i,s in enumerate(stations):
 p=line.interpolate(s);lon,lat=back.transform(p.x,p.y);q=live(p.x,p.y);n=live(*to.transform(lon,lat+.001));dx,dy=n[0]-q[0],n[1]-q[1];d=math.hypot(dx,dy);tag=f'{int(s)//1000:02d}K{int(s)%1000:03d}' if s!=line.length else 'END'
 t,near=min(lines,key=lambda a:a[1].distance(p))
 rows.append({'index':i,'chainage_m':s,'label':tag,'section':t['name'],'twd97':[p.x,p.y],'lonlat':[lon,lat],'live_xy':q,'true_north_live_unit':[dx/d,dy/d],'regular_200m_station':s%200==0})
r={'method':'Derived monotonic west-east analysis axis from median northing of named ground carriageways sampled every10m easting. Not official centerline, survey or chainage; double carriageways not summed. Endpoint added separately.','route_length_m':line.length,'source_ways':len(lines),'skipped_easting_samples':skipped,'largest_axis_sample_gap_m':max(math.dist(a,b) for a,b in zip(axis,axis[1:])),'axis_twd97':axis,'stations':rows,'camera_settings':{'height_above_modeled_surface_m':1.7,'lens_mm':28,'sensor_width_mm':36,'directions':['true north','true south'],'tilt_degrees':0}}
(out/'camera_stations.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps({'length_m':line.length,'station_pairs':len(rows),'camera_count':len(rows)*2,'missing_axis_samples':len(skipped),'largest_sample_gap_m':r['largest_axis_sample_gap_m']}))
