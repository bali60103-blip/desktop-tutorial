import os,json,pathlib,math
from shapely.geometry import LineString,shape,mapping
from shapely.ops import nearest_points,substring
root=pathlib.Path(os.environ['CIVIC_MODEL_ROOT']);out=root/'PriorityNodes_20260914';out.mkdir(exist_ok=True)
reg=json.load(open(root/'registration.json'));origin=reg['origin_epsg3826'];t=reg['live_to_twd97'];ang=math.radians(t['rotation_degrees']);c=math.cos(ang);s=math.sin(ang)
def live(p):
 x=p[0]-origin[0]-t['translation'][0];y=p[1]-origin[1]-t['translation'][1];return [(c*x+s*y)/t['scale'],(-s*x+c*y)/t['scale']]
stations=json.load(open(root/'Cameras_200m/camera_stations.json'))['stations'];axis=LineString([x['live_xy'] for x in stations]);ways=json.load(open(root/'data/osm.json'))['ways'];anchors=[]
for label,keys in [('LIN_SEN',['林森北路','林森南路']),('XIN_SHENG',['新生高架'])]:
 candidates=[]
 for w in ways:
  if not any(k in w['tags'].get('name','') for k in keys) or len(w['xy'])<2:continue
  line=LineString([live(p) for p in w['xy']]);a,b=nearest_points(axis,line);chain=axis.project(a)
  if 400<chain<1600:candidates.append((a.distance(b),chain,w['id'],w['tags']['name'],list(a.coords[0])))
 assert candidates,label
 row=min(candidates);anchors.append({'label':label,'distance_m':row[0],'chainage_m':row[1],'osm_id':row[2],'name':row[3],'live_xy':row[4]})
a,b=[r['chainage_m'] for r in anchors];assert 200<b-a<1000,(a,b)
rows=json.load(open(root/'CalibrationRound3/corrected_rows_context.json'));nodes=[]
for id,f0,f1 in [('A1',.02,.23),('A2',.27,.55),('A3',.57,.74)]:
 lo=a+(b-a)*f0;hi=a+(b-a)*f1;line=substring(axis,lo,hi);poly=line.buffer(24,cap_style=2);context=line.buffer(90,cap_style=2)
 selected=[{'osm_id':r['osm_id'],'name':r['name'],'height_m':r['height_m'],'height_status':r['height_status'],'first_row':r['first_row']} for r in rows if shape(r['geometry']).intersects(context)]
 nodes.append({'id':id,'chainage_interval_m':[lo,hi],'fraction_interval':[f0,f1],'axis':mapping(line),'working_focus_polygon':mapping(poly),'context_polygon':mapping(context),'source_records':selected,'status':'Schematic red-box position interpolated between mapped road anchors; extent and 24m/90m buffers are working review assumptions, not measured boundaries'})
r={'priority':'P1','source':'User one-page potential-node diagram, A1-A3 west to east','anchors':anchors,'nodes':nodes,'registration_limit':'Axis is piecewise 200m camera-station interpolation. Fractions visually read from schematic red boxes. Neither mapping nor polygon is survey control.'};(out/'priority_a_registration.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print({'anchors':anchors,'nodes':[{'id':n['id'],'chainage':n['chainage_interval_m'],'source_records':len(n['source_records'])} for n in nodes]})
