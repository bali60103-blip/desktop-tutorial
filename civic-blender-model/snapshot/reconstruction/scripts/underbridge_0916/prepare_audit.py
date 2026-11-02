import os
import pathlib,json,math,os,collections
from shapely.geometry import LineString,Point,box
from shapely.ops import unary_union
from pyproj import Transformer
root=pathlib.Path(os.environ['CIVIC_MODEL_ROOT']);out=pathlib.Path(os.environ.get('CIVIC_AUDIT_DIR','underbridge_work'));reg=json.load(open(root/'registration.json'));r=reg['live_to_twd97'];o=reg['origin_epsg3826'];ang=math.radians(r['rotation_degrees']);c,s=math.cos(ang),math.sin(ang)
def live(p):
 x,y=p[0]-o[0]-r['translation'][0],p[1]-o[1]-r['translation'][1];return ((c*x+s*y)/r['scale'],(-s*x+c*y)/r['scale'])
ways=json.load(open(root/'data/osm.json'))['ways'];bridge=[w for w in ways if w.get('tags',{}).get('name')=='市民大道高架道路'];lines=[LineString([live(p) for p in w['xy']]) for w in bridge];corridor=unary_union([l.buffer(18) for l in lines]);axis=LineString([live(p) for p in json.load(open(root/'Cameras_200m/camera_stations.json'))['axis_twd97']]);inv=json.load(open(pathlib.Path(os.environ.get('CIVIC_AUDIT_DIR','underbridge_work'))/'scene_inventory.json'));parts=[];tr=Transformer.from_crs(3826,4326,always_xy=True)
xmin,ymin,xmax,ymax=corridor.bounds
for i in range(math.floor(xmin/100),math.ceil(xmax/100)):
 window=box(i*100,ymin-1,(i+1)*100,ymax+1);g=corridor.intersection(window)
 if g.is_empty:continue
 p=g.representative_point();q=(o[0]+r['translation'][0]+r['scale']*(c*p.x-s*p.y),o[1]+r['translation'][1]+r['scale']*(s*p.x+c*p.y));lon,lat=tr.transform(*q)
 parts.append({'id':'UB_X%+04d'%i,'x_start':i*100,'x_end':(i+1)*100,'xy':[p.x,p.y],'lat':lat,'lon':lon,'streetview_status':'not_reviewed','dimensions_status':'not_verified','objects':[]})
for v in inv['objects']:
 if not v['visible'] or v['hide_render'] or v['hi'][2]<-.1 or v['lo'][2]>7.7:continue
 p=box(v['lo'][0],v['lo'][1],v['hi'][0],v['hi'][1])
 if not p.intersects(corridor):continue
 if p.area>10000:continue
 cen=p.centroid;idx=math.floor(cen.x/100);seg=next((a for a in parts if a['id']=='UB_X%+04d'%idx),None)
 if seg is None:continue
 n=v['name'];cat='other'
 for key,tokens in [('structure',['Pier','CAP','GIRDER','DECK']),('equipment',['VENT','MACHINE','SHAFT','EQUIP']),('access',['RAMP','STAIR','ENTRANCE','PORTAL']),('landscape',['TREE','PLANT','ISLAND']),('street_furniture',['LIGHT','FENCE','SIGN','GUARD','BOLLARD'])]:
  if any(t.lower() in n.lower() for t in tokens):cat=key;break
 seg['objects'].append({'name':n,'category':cat,'bounds':[v['lo'],v['hi']],'verification':'existing_model_not_proof'})
report={'scope':'100m easting strips covering mapped Civic elevated mainline incl western and eastern curved approaches; not chainage. Ramps/interchanges require separate extensions. Candidate bbox assignment is approximate.','source_scene':inv['scene'],'segments':parts,'segment_count':len(parts),'existing_candidates':sum(len(p['objects']) for p in parts),'complete':False}
(out/'underbridge_coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print({k:v for k,v in report.items() if k!='segments'});print([(p['id'],len(p['objects'])) for p in parts])
