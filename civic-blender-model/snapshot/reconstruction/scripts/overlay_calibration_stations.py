import json,pathlib,math
from PIL import Image,ImageDraw
from pyproj import Transformer
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Calibration';manifest=json.load(open(out/'imagery_manifest.json'));reg=json.load(open(root/'registration.json'));f=reg['live_to_twd97'];org=[reg['origin_epsg3826'][i]+f['translation'][i] for i in [0,1]];ang=math.radians(f['rotation_degrees']);back=Transformer.from_crs(3826,4326,always_xy=True);geoms=[]
for r in json.load(open(out/'model_geometry.json'))['meshes']:
 if not r['name'].startswith(('DECK_','RAMP_','COMP_ACCESS_','COMP_MEDIAN_','COMP_OSM_EQUIP_')):continue
 polys=[]
 for face in r['faces']:
  vs=[r['vertices'][i] for i in face];p=Polygon([v[:2] for v in vs])
  if p.is_valid and p.area>.001:polys.append(p)
 if polys:geoms.append((r['name'],unary_union(polys)))
def pixel(x,y,r):
 a=org[0]+f['scale']*(math.cos(ang)*x-math.sin(ang)*y);b=org[1]+f['scale']*(math.sin(ang)*x+math.cos(ang)*y);lon,lat=back.transform(a,b);N=2**r['zoom'];return ((lon+180)/360*N-r['tile_origin'][0])*256,((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*N-r['tile_origin'][1])*256
(out/'overlays').mkdir(exist_ok=True)
for r in manifest['stations']:
 im=Image.open(r['image']).convert('RGB');draw=ImageDraw.Draw(im);x,y=r['live_xy'];clip=box(x-260,y-260,x+260,y+260)
 for name,g in geoms:
  if not g.intersects(clip):continue
  gg=g.intersection(clip);color='magenta' if name.startswith('DECK_') else ('cyan' if name.startswith('RAMP_') else 'yellow')
  for p in [gg] if gg.geom_type=='Polygon' else getattr(gg,'geoms',[]):
   if p.geom_type=='Polygon':draw.line([pixel(*q,r) for q in p.exterior.coords],fill=color,width=2)
 im.save(out/'overlays'/(r['label']+'.jpg'))
# Sheets for screening all 53 stations, six per sheet at usable resolution.
for start in range(0,len(manifest['stations']),6):
 sheet=Image.new('RGB',(1536,2400),'white')
 for j,r in enumerate(manifest['stations'][start:start+6]):sheet.paste(Image.open(out/'overlays'/(r['label']+'.jpg')),((j%2)*768,(j//2)*800))
 sheet.save(out/f'sheet_{start//6+1:02d}.jpg')
(out/'overlay_footprints.json').write_text(json.dumps([{'name':name,'geometry':g.__geo_interface__} for name,g in geoms]));print({'station_overlays':len(manifest['stations']),'sheets':math.ceil(len(manifest['stations'])/6),'footprints':len(geoms)})
