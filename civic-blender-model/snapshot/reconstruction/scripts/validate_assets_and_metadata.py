import bpy,json,pathlib,math,collections
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/Validation')
assets=[]
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file:
  p=bpy.path.abspath(im.filepath);assets.append({'type':'image','name':im.name,'path':p,'exists':pathlib.Path(p).is_file()})
for lib in bpy.data.libraries:
 p=bpy.path.abspath(lib.filepath);assets.append({'type':'library','path':p,'exists':pathlib.Path(p).is_file()})
nonfinite=[];zeroscale=[];meta=[]
for o in bpy.data.objects:
 if not all(math.isfinite(x) for row in o.matrix_world for x in row):nonfinite.append(o.name)
 if any(abs(s)<1e-9 for s in o.scale):zeroscale.append(o.name)
 if o.type=='MESH':
  fields={k:str(o[k])[:300] for k in o.keys() if any(t in k.lower() for t in ['status','source','assum','verif','height','osm'])}
  if fields:meta.append({'object':o.name,'fields':fields})
invalidcams=[o.name for o in bpy.data.objects if o.type=='CAMERA' and (o.data.clip_end<=o.data.clip_start or o.data.lens<=0 or o.data.ortho_scale<=0)]
missing= [x for x in assets if not x['exists']]
r={'file':bpy.data.filepath,'missing_external_assets':missing,'external_asset_count':len(assets),'nonfinite_transforms':nonfinite,'zero_scale_objects':zeroscale,'invalid_camera_parameters':invalidcams,'mesh_objects_with_explicit_provenance_or_assumption_fields':len(meta),'metadata_examples':meta[:30],'limits':'Metadata presence does not validate provenance correctness; absence may be covered by collection/report-level tags. External file existence does not establish accuracy.'}
(out/'assets_metadata_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result={k:v for k,v in r.items() if k!='metadata_examples'}
