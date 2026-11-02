"""Complete source-covered working volumes; all unsurveyed choices explicitly logged."""
import json,pathlib,math,statistics,runpy,shutil
from shapely.geometry import Polygon,LineString,Point,shape
from shapely.ops import unary_union,transform
from shapely import set_precision,make_valid
from pyproj import Transformer
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'CompletionPass';out.mkdir(exist_ok=True);(out/'source').mkdir(exist_ok=True)
shutil.copy2('/tmp/civic-frontage-full/first_row.json',out/'source/first_row.json')
mesh=runpy.run_path('/tmp/civic-stage00/reconstruction/scripts/prepare_mall_shells.py')['mesh'];parts=[];issues=[]
def add(name,poly,z0,z1,group,status,extra=None):
 poly=set_precision(make_valid(poly),.0001)
 for i,p in enumerate([poly] if poly.geom_type=='Polygon' else getattr(poly,'geoms',[])):
  if p.geom_type!='Polygon' or p.area<.0001:continue
  parts.append({'name':name+(('_'+str(i)) if poly.geom_type!='Polygon' else ''),'group':group,'mesh':mesh(p,z0,z1),'status':status,'extra':extra or {}})
def rect(a,d,x0,x1,y0,y1):
 n=(-d[1],d[0]);return Polygon([(a[0]+d[0]*x+n[0]*y,a[1]+d[1]*x+n[1]*y) for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]])
rows=json.load(open(out/'source/first_row.json'))['buildings'];known=json.load(open(root/'FullFrontageSolids/source/solids_payload.json'))['buildings'];ids={r['osm_id'] for r in known};centers={r['osm_id']:unary_union([Polygon(t['outer'],t['holes']) for t in r['rings']]).centroid for r in rows};kh=[(centers[r['osm_id']],r['height_m'],r['osm_id']) for r in known]
for r in rows:
 if r['osm_id'] in ids:continue
 c=centers[r['osm_id']];near=sorted([(c.distance(q),h,i) for q,h,i in kh])[:5];within=[v for v in near if v[0]<=500];h=statistics.median([v[1] for v in within]) if within else 13.2
 status='ESTIMATED nearest up-to-5 known-height frontage median within 500m; fallback13.2m; baseZ0; landmark height may differ substantially'
 for j,t in enumerate(r['rings']):add('COMP_FRONT_'+r['osm_id']+'_'+str(j),Polygon(t['outer'],t['holes']),0,h,'FRONTAGE',status,{'osm_id':r['osm_id'],'height_m':h,'height_references':within,'name':r['name']})
 issues.append({'id':'HEIGHT_'+r['osm_id'],'xy':[c.x,c.y],'type':'height_unverified','name':r['name'],'estimated_height_m':h})
parking=json.load(open(root/'ParkingSections/source/payload.json'))['sections'];sections={r['name']:r for r in parking}
for r in parking:
 name=r['name'];g=Polygon(r['outline']);line=LineString(r['axis_live']);a=line.interpolate(0);b=line.interpolate(line.length);d=((b.x-a.x)/line.length,(b.y-a.y)/line.length);aa=(a.x,a.y);L=line.length;group='PARKING';status='ESTIMATED parking internal layout; official section identity only; all dimensions and placements await calibration'
 # Keep openings for current assumed layer ramp and two surface access cores.
 cores=[rect(aa,d,s,s+4.7,7,11) for s in [10,L-14]];coreholes=unary_union(cores)
 for lev in range(1,r['levels']+1):
  z=-3.6*lev
  cut=unary_union([coreholes]+[Polygon(t) for t in (r['interlevel_hole'] if lev==1 else [])])
  add('COMP_'+name+'_B'+str(lev)+'_FLOOR',g.difference(cut),z-.3,z,group,status)
  wall=g.difference(g.buffer(-.2));add('COMP_'+name+'_B'+str(lev)+'_PERIMETER',wall,z,-.3 if lev==1 else -3.9,group,status)
  # Columns and parking striping kept away from central ramp envelope and cores.
  for s in range(20,int(L-15),8):
   for y in [-6,6]:
    col=rect(aa,d,s-.3,s+.3,y-.3,y+.3)
    if g.covers(col) and not col.intersects(coreholes):add('COMP_'+name+'_B'+str(lev)+'_COL_'+str(s)+'_'+str(y),col,z,z+3.3,group,status)
  # Roof slab kept removable for cutaway; upper floor slabs already exist separately.
  if lev==1:add('COMP_'+name+'_ROOF',g.difference(coreholes),-.30,0,group,status,{'cutaway_roof':True})
  for s in range(18,int(L-18),3):
   for side in [-1,1]:
    marking=rect(aa,d,s,s+.08,side*7,side*11) if side==1 else rect(aa,d,s,s+.08,-11,-7)
    if g.covers(marking) and not marking.intersects(coreholes):add('COMP_'+name+'_B'+str(lev)+'_BAYLINE_'+str(s)+'_'+str(side),marking,z+.005,z+.015,'MARKINGS',status)
  for ci,cp in enumerate(cores):
   # 24-step dogleg flight pair per floor:12 down, landing,12 back.
   s=[10,L-14][ci]
   for j in range(12):
    add('COMP_'+name+'_CORE'+str(ci)+'_L'+str(lev)+'_A'+str(j),rect(aa,d,s+j*.3,s+(j+1)*.3,7.1,8.3),z-.3,z+3.6-j*.15,group,status)
    add('COMP_'+name+'_CORE'+str(ci)+'_L'+str(lev)+'_B'+str(j),rect(aa,d,s+(11-j)*.3,s+(12-j)*.3,9.5,10.7),z-.3,z+1.8-j*.15,group,status)
   add('COMP_'+name+'_CORE'+str(ci)+'_L'+str(lev)+'_LANDING',rect(aa,d,s+3.3,s+4.5,7.1,10.7),z+1.5,z+1.8,group,status)
 # Machinery rooms, assumed at section ends; doors omitted from partition solids.
 for j,s in enumerate([2,L-8]):
  room=rect(aa,d,s,s+6,-11,-7);wall=room.difference(room.buffer(-.15));door=rect(aa,d,s+2,s+3.2,-7.3,-6.8);add('COMP_'+name+'_MACHINE_ROOM_'+str(j),wall.difference(door),-3.6,-.3,group,status)
  add('COMP_'+name+'_MACHINE_BLOCK_'+str(j),rect(aa,d,s+1,s+4,-10.5,-8.5),-3.6,-1.6,'EQUIPMENT',status)
 issues.append({'id':'PARK_'+name,'xy':[line.centroid.x,line.centroid.y],'type':'whole_layout_estimated','detail':'Stairs/columns/stalls/rooms are generic placeholders; stairs require slab openings and vehicle entry integration review'})
# Official inventory proves listed facility existence only. Positions distributed by stated end within each section, not real coordinates.
inv=json.load(open(root/'MedianEquipment/median_equipment_inventory.json'))['entries']
for i,e in enumerate(inv):
 r=sections[e['section']];line=LineString(r['axis_live']);frac=.12 if '西' in e['relative_location'] and not e['relative_location'].startswith('東') else .88
 frac+=((i%7)//2)*.022*(-1 if frac>.5 else 1);s=line.length*frac;q=line.interpolate(s);u=line.interpolate(min(s+1,line.length));d=(u.x-q.x,u.y-q.y);le=math.hypot(*d);d=(d[0]/le,d[1]/le)
 h=2.4 if '水塔' in e['type'] else (3.5 if '煙' in e['type'] else 1.8);w=1 if '煙' in e['type'] else 2;length=1 if '煙' in e['type'] else 3
 add('COMP_MEDIAN_'+e['id']+'_'+e['type'],rect((q.x,q.y),d,-length/2,length/2,-w/2,w/2),.15,.15+h,'EQUIPMENT','ESTIMATED position and size; official plan label only',e)
 issues.append({'id':'MEDIAN_'+e['id'],'xy':[q.x,q.y],'type':'facility_position_and_size_unverified','source':e['source']})
# OSM facilities retain mapped footprints rather than moving candidates into median.
tf=Transformer.from_crs(4326,3826,always_xy=True);ox,oy=301495.6087493267,2770459.509396812
for f in json.load(open(root/'MedianEquipment/osm_equipment_candidates.geojson'))['features']:
 p=transform(lambda x,y:tuple(v for v in tf.transform(x,y)),shape(f['geometry']));p=transform(lambda x,y:(x-ox,y-oy),p);prop=f['properties']
 if p.geom_type=='Point':p=p.buffer(1,quad_segs=2)
 add('COMP_OSM_EQUIP_'+str(prop['osm_id']),p,0,2.4,'EQUIPMENT','OSM XY; height2.4m placeholder; median membership unverified',prop)
issues.extend([{'id':'PIER_'+s,'type':'pier_conflict','detail':'Retain flagged existing geometry; imagery calibration deferred'} for s in ['036','114','408','438','534','540','674']]);issues.append({'id':'PARK_OVERLAP','type':'overlap','detail':'敦延/延吉 ~85m unresolved; retain both'})
p={'parts':parts,'issues':issues,'counts':{g:sum(x['group']==g for x in parts) for g in sorted({x['group'] for x in parts})},'stage':'Source-covered completion pass; estimated working volumes, not as-built completeness'};(out/'payload.json').write_text(json.dumps(p,ensure_ascii=False));(out/'issues.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2));print(p['counts'])
