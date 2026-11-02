"""Generate georeferenced conflict review targets without moving model piers."""
import json,math,pathlib
from pyproj import Transformer
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934')
reg=json.loads((root/'registration.json').read_text())
cfg=reg['live_to_twd97'];ang=math.radians(cfg['rotation_degrees']);s=cfg['scale']
origin=[reg['origin_epsg3826'][i]+cfg['translation'][i] for i in range(2)]
tf=Transformer.from_crs(3826,4326,always_xy=True)
official=json.load(open('/tmp/civic-rebuild/civic-official-piers.geojson'))['features']
out=[]
for g in json.loads((root/'Worksheet04_05/pier_alternatives.json').read_text())['groups']:
 if g['original_overlap_m2']<=0:continue
 x,y=g['center_xy'];X=origin[0]+s*(math.cos(ang)*x-math.sin(ang)*y);Y=origin[1]+s*(math.sin(ang)*x+math.cos(ang)*y)
 lon,lat=tf.transform(X,Y)
 near=sorted(official,key=lambda f:math.dist(f['geometry']['coordinates'],[X,Y]))[:3]
 out.append({**g,'twd97':[X,Y],'lonlat':[lon,lat],
 'streetview_url':f'https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}',
 'satellite_url':f'https://www.google.com/maps/@?api=1&map_action=map&center={lat},{lon}&zoom=20&basemap=satellite',
 'nearest_official_points':[{'properties':f['properties'],'distance_to_cap_center_m':round(math.dist(f['geometry']['coordinates'],[X,Y]),3)} for f in near],
 'decision':'Unresolved. Nearest official point is not established as same pier. Street image observation required.'})
pathlib.Path('/tmp/civic-pier-imagery').mkdir(exist_ok=True)
pathlib.Path('/tmp/civic-pier-imagery/review_targets.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps([{'cap':g['cap'],'lonlat':g['lonlat'],'nearest_m':g['nearest_official_points'][0]['distance_to_cap_center_m']} for g in out],ensure_ascii=False,indent=2))
