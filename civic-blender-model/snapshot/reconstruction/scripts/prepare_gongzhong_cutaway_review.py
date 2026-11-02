import json,os,pathlib
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
from shapely import constrained_delaunay_triangles
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';r=json.load(open(out/'gongzhong_integrated_openings_payload.json'));hole=Polygon(r['new_hole_xy']);cx,cy=hole.centroid.coords[0];window=box(cx-5,cy-5,cx+5,cy+5);rows=[]
for row in r['items']:
 if row['source']=='CAL_GROUND_ROADS_OFFICIAL_XY_0_FIX0':continue
 vs=row['vertices'];z0=min(v[2] for v in vs);z1=max(v[2] for v in vs);p=unary_union([Polygon([vs[i][:2] for i in f]) for f in row['faces'] if all(abs(vs[i][2]-z1)<.0001 for i in f)]).intersection(window)
 if not row['source'].endswith('B2_FLOOR'):p=p.intersection(box(cx-5,cy+1.5,cx+5,cy+5))
 verts=[];faces=[]
 for poly in list(p.geoms) if hasattr(p,'geoms') else [p]:
  if poly.is_empty:continue
  for tri in constrained_delaunay_triangles(poly).geoms:
   co=list(orient(tri,1).exterior.coords)[:-1];k=len(verts);verts.extend([[x,y,z] for z in [z0,z1] for x,y in co]);faces.extend([[k+i for i in f] for f in [(2,1,0),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)]])
 rows.append({'source':row['source'],'vertices':verts,'faces':faces})
(out/'gongzhong_cutaway_payload.json').write_text(json.dumps({'center':[cx,cy,-3.6],'surfaces':rows,'scope':'Review cutaway only; front half of upper slabs hidden to reveal stairs'}))
