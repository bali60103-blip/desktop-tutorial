import json,pathlib,collections,math
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/BlockFacades');rows=json.load(open(out/'facade_payload.json'));bad=[];ct=0
for r in rows:
 for j,m in enumerate(r['cores']+r['roofs']):
  ct+=1;vs=m['vertices'];fs=m['faces'];ec=collections.Counter(tuple(sorted((f[i],f[(i+1)%len(f)]))) for f in fs for i in range(len(f)));repeated=sum(len(set(f))<3 or len(set(f))!=len(f) for f in fs);nf=sum(not all(math.isfinite(v) for v in p) for p in vs);edges=sum(v!=2 for v in ec.values())
  if repeated or nf or edges:bad.append({'osm_id':r['osm_id'],'component':j,'repeated_faces':repeated,'nonfinite':nf,'nonmanifold_edges':edges})
r={'building_records':len(rows),'mesh_components':ct,'bad_components':bad,'facade_instances':sum(len(r['points']) for r in rows),'status':'Payload index/finite/edge check; inferred facade proportions not site-verified'};(out/'payload_validation.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print({k:v for k,v in r.items() if k!='bad_components'});print('bad',len(bad),bad[:10])
