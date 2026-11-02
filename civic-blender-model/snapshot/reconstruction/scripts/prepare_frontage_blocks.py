import pathlib,json,math,statistics,re,collections
from shapely.geometry import Polygon,LineString,shape,box
from shapely.ops import unary_union,polygonize
from shapely import set_precision,make_valid,STRtree
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'BlockFacades';streets=json.load(open(out/'source/streets_plan_boundaries.json'));raw=json.load(open(out/'source/buildings.json'));first=json.load(open(root/'CompletionPass/source/first_row.json'))['buildings'];first=[r for r in first if r['tags'].get('location')!='underground'];fp=[unary_union([Polygon(t['outer'],t['holes']) for t in r['rings']]) for r in first];domain=box(min(g.bounds[0] for g in fp)-1100,min(g.bounds[1] for g in fp)-1100,max(g.bounds[2] for g in fp)+1100,max(g.bounds[3] for g in fp)+1100)
lines=[set_precision(LineString(r['xy']).intersection(domain),.01) for r in streets];network=unary_union(lines+[domain.boundary]);blocks=[p for p in polygonize(network) if p.area>200];tree=STRtree(blocks);selected=set();unmatched=[]
for r,g in zip(first,fp):
 cand=[int(i) for i in tree.query(g)];rated=sorted([(blocks[i].intersection(g).area/g.area,i) for i in cand],reverse=True)
 if rated and rated[0][0]>.25:selected.add(rated[0][1])
 else:unmatched.append(r['osm_id'])
chosen=[blocks[i] for i in sorted(selected)];bt=STRtree(chosen);domainboundary=domain.boundary;blockrows=[{'id':'BLOCK_'+str(i).zfill(3),'geometry':p.__geo_interface__,'area_m2':p.area,'boundary_complete':p.distance(domainboundary)>.1,'status':'Public street-corridor plan polygon; elevated crossings are not at-grade connectivity; not cadastral boundary'} for i,p in enumerate(chosen)];firstids={'w'+r['osm_id'] for r in first};known={str(r['osm_id']):r['height_m'] for r in json.load(open(root/'FullFrontageSolids/source/solids_payload.json'))['buildings']};estimated={str(r['extra']['osm_id']):r['extra']['height_m'] for r in json.load(open(root/'CompletionPass/payload.json'))['parts'] if r['group']=='FRONTAGE'};buildings=[];seen=set();skipped=[]
def num(s):
 try:return float(re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)',str(s)).group(1))
 except:return None
for r in raw:
 t=r['tags'];oid=r['osm_id']
 if t.get('location')=='underground' or t.get('building:levels')=='0':continue
 g=set_precision(make_valid(shape(r['geometry'])),.01)
 if g.is_empty or g.area<4:continue
 candidates=[int(i) for i in bt.query(g)];rated=sorted([(chosen[i].intersection(g).area/g.area,i) for i in candidates],reverse=True);isfirst=oid in firstids
 if not isfirst and (not rated or rated[0][0]<.35):continue
 key=g.normalize().wkb
 if key in seen:continue
 seen.add(key);height=num(t.get('height'));levels=num(t.get('building:levels'));base=num(t.get('min_height')) or 0
 if height is not None:status='OSM explicit height; unmeasured'
 elif levels is not None:height=levels*3.3;status='OSM floor count x estimated3.3m'
 elif oid[1:] in known:height=known[oid[1:]];status='Preserved prior OSM-derived height'
 elif oid[1:] in estimated:height=estimated[oid[1:]];status='Preserved previous neighbor-height estimate'
 else:status='Needs block-neighbor height estimate'
 if oid=='w558011740':height=46.05;status='Architect publication46.05m; roof form simplified'
 buildings.append({'osm_id':oid,'name':t.get('name',''),'tags':t,'geometry':g.__geo_interface__,'block_id':'BLOCK_'+str(rated[0][1]).zfill(3) if rated else None,'first_row':isfirst,'height_m':height,'base_z_m':base,'height_status':status,'area_m2':g.area,'facade_status':'Generic inferred architectural detailing; not photo-calibrated facade','is_building_part':'building:part' in t})
# Estimate new interior heights from mapped neighbors in the same street block, with an explicit fallback.
blockknown=collections.defaultdict(list)
for r in buildings:
 if r['height_m'] and not r['height_status'].startswith('Preserved previous'):blockknown[r['block_id']].append(r['height_m'])
for r in buildings:
 if not r['height_m']:
  h=blockknown.get(r['block_id'],[]);r['height_m']=statistics.median(h) if h else 13.2;r['height_status']='Estimated median of known heights in selected block' if h else 'Estimated13.2m fallback; no height source'
 if r['height_m']<=r['base_z_m']+.6:r['base_z_m']=0;r['height_status']+='; invalid min_height discarded'
summary={'selected_street_blocks':len(chosen),'closed_selected_blocks':sum(r['boundary_complete'] for r in blockrows),'mapped_buildings_and_parts':len(buildings),'first_row_buildings':sum(r['first_row'] for r in buildings),'interior_buildings_and_parts':sum(not r['first_row'] for r in buildings),'input_first_row_unmatched_to_closed_blocks':unmatched,'underground_excluded':True,'height_status_counts':dict(collections.Counter(r['height_status'] for r in buildings)),'scope':'All mapped building areas selected by frontage-containing road blocks; unmapped site buildings may be missing. Facades will be explicitly estimated.'};(out/'blocks.json').write_text(json.dumps(blockrows,ensure_ascii=False));(out/'buildings_selected.json').write_text(json.dumps(buildings,ensure_ascii=False));(out/'selection_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(summary)
