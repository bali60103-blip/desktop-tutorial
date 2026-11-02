import json,pathlib,math,urllib.request,concurrent.futures,time,shutil,hashlib,subprocess
from PIL import Image,ImageDraw
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Calibration';out.mkdir(exist_ok=True);tiles=out/'tiles';tiles.mkdir(exist_ok=True);(out/'stations_current').mkdir(exist_ok=True);(out/'source').mkdir(exist_ok=True)
for n in ['wmts_capabilities.xml','ceci_structures.pdf']:
 p=pathlib.Path('/tmp/civic-calibration')/n
 if p.exists():shutil.copy2(p,out/'source'/n)
from pyproj import Transformer
rows=json.load(open(out/'corrected_camera_stations.json'))['stations'];reg=json.load(open(root/'registration.json'));f=reg['live_to_twd97'];ang=math.radians(f['rotation_degrees']);org=[reg['origin_epsg3826'][i]+f['translation'][i] for i in [0,1]];tf=Transformer.from_crs(3826,4326,always_xy=True)
for c in json.load(open(out/'model_geometry.json'))['cameras']:
 if c['name'].startswith('CIVIC200_') or c['name']=='FRONTAGE_HEIGHT_CAMERA':continue
 x,y=c['location'][:2];xx=org[0]+f['scale']*(math.cos(ang)*x-math.sin(ang)*y);yy=org[1]+f['scale']*(math.sin(ang)*x+math.cos(ang)*y);rows.append({'label':c['name'],'lonlat':list(tf.transform(xx,yy)),'live_xy':[x,y],'kind':'parking_camera'})
z=18;N=2**z
def tile(lon,lat):return ((lon+180)/360*N,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*N)
required=set()
for r in rows:
 x,y=tile(*r['lonlat']);r['tile_xy']=[x,y]
 for dx in [-1,0,1]:
  for dy in [-1,0,1]:required.add((int(x)+dx,int(y)+dy))
def fetch(q):
 x,y=q;p=tiles/f'{z}_{x}_{y}.jpg';u=f'https://wmts.nlsc.gov.tw/wmts/PHOTO2/default/GoogleMapsCompatible/{z}/{y}/{x}'
 try:
  if not p.exists():
   subprocess.run(['curl','--fail','--silent','--show-error','--max-time','25',u,'-o',str(p)],check=True,capture_output=True)
  im=Image.open(p);im.verify();return {'tile':[z,x,y],'url':u,'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'ok':True}
 except Exception as e:return {'tile':[z,x,y],'url':u,'ok':False,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(fetch,sorted(required)))
for r in rows:
 x,y=r['tile_xy'];ix,iy=int(x),int(y);im=Image.new('RGB',(768,800),'white')
 for dx in [-1,0,1]:
  for dy in [-1,0,1]:
   p=tiles/f'{z}_{ix+dx}_{iy+dy}.jpg'
   if p.exists():
    try:im.paste(Image.open(p).convert('RGB'),((dx+1)*256,(dy+1)*256))
    except:pass
 px=(x-ix+1)*256;py=(y-iy+1)*256;d=ImageDraw.Draw(im);d.ellipse((px-5,py-5,px+5,py+5),outline='red',width=2);d.text((8,776),r['label']+' | NLSC PHOTO2 | acquisition date unknown',fill='black');im.save(out/'stations_current'/(r['label']+'.jpg'));r['image']=str(out/'stations_current'/(r['label']+'.jpg'));r['pixel_center']=[px,py];r['tile_origin']=[ix-1,iy-1];r['zoom']=z
manifest={'source':'NLSC PHOTO2 orthophoto, not satellite-specific sensor; do not infer current acquisition date from retrieval time','service':'https://maps.nlsc.gov.tw/S09SOA/pro/Wmts_ajax_main.jsp','zoom':z,'stations':rows,'tiles':results,'fetched_at':time.strftime('%Y-%m-%dT%H:%M:%S'),'failures':sum(not r['ok'] for r in results)};(out/'imagery_current.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print({'tiles':len(results),'failures':manifest['failures'],'station_images':len(rows)})
