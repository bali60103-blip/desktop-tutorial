"""Compare modeled support extents to modeled deck footprints, not surveyed pier positions."""
import argparse,json,pathlib
from shapely.geometry import MultiPoint,Point
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--out',required=True);a=p.parse_args();d=json.load(open(a.input));decks=[]
for r in d['decks']:
 pts=r['vertices'];decks.append((r,MultiPoint([(x,y) for x,y,z in pts]).convex_hull,min(z for x,y,z in pts),max(z for x,y,z in pts)))
rows=[]
for s in d['supports']:
 pts=s['vertices'];x=(min(p[0] for p in pts)+max(p[0] for p in pts))/2;y=(min(p[1] for p in pts)+max(p[1] for p in pts))/2;zmax=max(p[2] for p in pts);q=Point(x,y)
 covers=[(r,g,zlo,zhi) for r,g,zlo,zhi in decks if g.covers(q)]
 nearest=min(decks,key=lambda v:v[1].distance(q))
 flags=[]
 if not covers:flags.append('CENTER_OUTSIDE_DECK_CONVEX_ENVELOPE')
 # Z interval is only a broad bound on a potentially sloped deck; do not auto-correct.
 rows.append({'object':s['name'],'center_xy':[x,y],'top_z':zmax,'overlapping_decks':[r['name'] for r,g,zlo,zhi in covers],'nearest_deck':nearest[0]['name'],'distance_to_deck_envelope_m':round(nearest[1].distance(q),3),'deck_global_bottom_z':nearest[2],'top_to_deck_global_bottom_m':round(nearest[2]-zmax,3),'flags':flags})
result={'scope':'Internal model consistency only, no as-built pier verification','method':'World-space mesh vertices; convex deck XY envelopes and global minimum Z. Slopes, girders, bearings and local contact require detailed inspection. Positive deck gap is not automatically a defect.','summary':{'support_objects':len(rows),'deck_objects':len(decks),'centers_outside_all_deck_envelopes':sum(bool(r['flags']) for r in rows),'max_xy_distance_m':max(r['distance_to_deck_envelope_m'] for r in rows)},'objects':rows}
pathlib.Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result['summary']))
