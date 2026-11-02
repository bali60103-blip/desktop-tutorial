exec(open('/tmp/civic-assemble.py').read().split('sw=[]')[0])
g=shape(json.loads((P/'median-derived.json').read_text()))
for i,p in enumerate(polygons(g)):
 if p.area<8:continue
 mesh('MEDIAN_CANDIDATE_'+str(i),p,0,.18,'13_Median_gap_inference',dict(source='Gap between official road and sidewalk layers, clipped to estimated deck footprint',confidence='Inferred bridge-under space / median candidate; category and exact curb edge unverified, not survey result'))
(P/'supplement_payload.json').write_text(json.dumps(out,ensure_ascii=False))
print('supplement_objects',len(out))
