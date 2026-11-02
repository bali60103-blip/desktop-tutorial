import bpy,json,pathlib,datetime,collections
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Validation';stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_validation_repairs_'+stamp+'.blend')),copy=True)
changes=[]
def counts(vs,fs):
 ec=collections.Counter(tuple(sorted((a,b))) for f in fs for a,b in zip(f,f[1:]+f[:1]))
 return {'boundary':sum(n==1 for n in ec.values()),'multiple':sum(n>2 for n in ec.values())}
def replace(o,vs,fs,reason):
 old=o.data;me=bpy.data.meshes.new(old.name+'_QA_REPAIRED');me.from_pydata(vs,[],fs);me.update()
 for mat in old.materials:me.materials.append(mat)
 assert all(p.area>1e-10 for p in me.polygons)
 assert counts(vs,fs)=={'boundary':0,'multiple':0},counts(vs,fs)
 old.use_fake_user=True;o.data=me;o['validation_repair']=reason;changes.append({'object':o.name,'reason':reason,'before_mesh_retained':old.name,'after':counts(vs,fs)})
# Separate two road solids sharing only a vertical edge, preserving every coordinate and face.
o=bpy.data.objects['GROUND_ROADS_OFFICIAL_XY'];vs=[tuple(v.co) for v in o.data.vertices];fs=[list(f.vertices) for f in o.data.polygons];edgefaces=collections.defaultdict(list)
for j,f in enumerate(fs):
 for a,b in zip(f,f[1:]+f[:1]):edgefaces[tuple(sorted((a,b)))].append(j)
# Split local face fans at nonmanifold edge endpoints; global shells may connect elsewhere.
nvs=list(vs);nfs=[list(f) for f in fs]
targets={v for e,ff in edgefaces.items() if len(ff)>2 for v in e}
for v in targets:
 incident={j for j,f in enumerate(fs) if v in f};adj=collections.defaultdict(list)
 for e,ff in edgefaces.items():
  if v in e and len(ff)==2:adj[ff[0]].append(ff[1]);adj[ff[1]].append(ff[0])
 seen=set();fan=0
 for seed in incident:
  if seed in seen:continue
  idx=v if fan==0 else len(nvs)
  if fan:nvs.append(vs[v])
  fan+=1;stack=[seed];seen.add(seed)
  while stack:
   j=stack.pop();nfs[j]=[idx if i==v else i for i in nfs[j]]
   for k in adj[j]:
    if k not in seen:seen.add(k);stack.append(k)
replace(o,nvs,nfs,'Split edge-touching road shells; no coordinate displacement')
# Collapse only exact-coincident vertex pairs on the identified degenerate building face.
o=bpy.data.objects['Buildings_context__OSM_XY__HEIGHTS_UNVERIFIED'];vs=[tuple(v.co) for v in o.data.vertices];remap={}
for p in o.data.polygons:
 if p.area<1e-10:
  bycoord={}
  for i in p.vertices:
   if vs[i] in bycoord:remap[i]=bycoord[vs[i]]
   else:bycoord[vs[i]]=i
fs=[]
for p in o.data.polygons:
 f=[remap.get(i,i) for i in p.vertices];f=list(dict.fromkeys(f))
 if len(f)>=3:fs.append(f)
replace(o,vs,fs,'Collapse exact duplicate vertices at zero-width wall; remove collapsed face')
# Remove legacy boundary wall intrusion across entire B staircase mouth.
p=json.load(open(root/'Y26Orientation/integrated_clearance_payload.json'))
for part in p['parts']:
 if 'WALL' not in part['name']:continue
 o=bpy.data.objects[part['name']];replace(o,part['mesh']['vertices'],part['mesh']['faces'],'Cut full estimated staircase footprint from legacy mall wall; preserve pre-repair mesh')
file=out/('CIVIC_VALIDATION_REPAIRED_'+stamp+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));r={'file':str(file),'changes':changes,'limits':'Geometry fixes only; no surveyed coordinates, elevations or dimensions asserted.'};(out/'repair_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result=r
