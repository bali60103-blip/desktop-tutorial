import json,pathlib,os,math
from shapely.geometry import Polygon,LineString
from shapely.affinity import translate
from shapely.ops import unary_union
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sections={s['name']:s for s in json.load(open(out.parent/'ParkingSections/source/payload.json'))['sections']};paths=json.load(open(out.parent/'Calibration/checked_paths.json'));cases=[]
for section,core,sign in [('\u516c\u4e2d',0,1),('\u6566\u5ef6',1,-1),('\u5ef6\u5409',0,1)]:
 key='CORE_'+section+'_'+str(core)+'_';pp=[p for p in paths if p['id'].startswith(key)];a=pp[0]['a'];b=pp[0]['b'];dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);t=(dx/length,dy/length);outline=Polygon(sections[section]['outline']);envelope=unary_union([LineString([p['a'][:2],p['b'][:2]]).buffer(p['halfwidth']+.12,cap_style=2) for p in pp]);candidates=[]
 for offset in range(5,151,5):
  for lateral in [0,-2,-4,-6]:
   x,y=t[0]*offset*sign-t[1]*lateral,t[1]*offset*sign+t[0]*lateral
   if outline.buffer(.05).covers(translate(envelope,xoff=x,yoff=y)):candidates.append({'distance_m':offset*sign,'lateral_m':lateral,'translation':[x,y,0]})
 cases.append({'section':section,'core':core,'prefix':key,'paths':pp,'candidates':candidates})
(out/'core_relocation_candidates.json').write_text(json.dumps(cases));print([(c['section'],c['core'],len(c['candidates'])) for c in cases])
