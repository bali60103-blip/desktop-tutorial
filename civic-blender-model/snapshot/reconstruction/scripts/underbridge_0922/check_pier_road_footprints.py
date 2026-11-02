import json,sys
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import make_valid
d=json.load(open(sys.argv[1]))
def shape(o):
    return unary_union([make_valid(Polygon(f)) for f in o['faces'] if len(f)>=3])
roads=[(r['name'],shape(r)) for r in d['roads']]
road=unary_union([g for _,g in roads]);median=unary_union([shape(r) for r in d['medians']])
rows=[]
for p in d['piers']:
    g=shape(p);r=g.intersection(road);outside=r.difference(median)
    status='ROAD_OVERLAP_REVIEW' if outside.area>.01 else 'WITHIN_MODELED_MEDIAN' if g.difference(median).area<.01 else 'NO_MAPPED_ROAD_OVERLAP'
    rows.append({'pier':p['name'],'xy':list(g.centroid.coords[0]),'footprint_m2':g.area,'road_overlap_m2':r.area,'road_outside_median_m2':outside.area,'outside_median_m2':g.difference(median).area,'roads':[n for n,rg in roads if g.intersection(rg).area>.01],'status':status,'real_world_verified':False})
out={'basis':'Evaluated mesh XY footprint intersection; modeled road minus modeled median, not verified vehicle lane geometry. Piers use bottom faces. No movement applied.','counts':{s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})},'piers':rows}
json.dump(out,open(sys.argv[2],'w'),indent=2)
print(json.dumps({'counts':out['counts'],'conflicts':[r for r in rows if r['status']=='ROAD_OVERLAP_REVIEW'][:20]}))
