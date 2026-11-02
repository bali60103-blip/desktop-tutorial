"""Inventory the current scene rather than treating old checkpoint counts as completion."""
import bpy,json,pathlib,os,math,collections
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;sc.view_layers[0].update();rows=json.load(open(out/'corrected_rows_context.json'))
visible=[o for o in sc.objects if o.visible_get()];names={o.name for o in visible};coverage=[]
for row in rows:
 ident=row['osm_id'];cores=('BLOCK_'+ident+'_CORE') in names;coverage.append({'osm_id':ident,'first_row':row.get('first_row'), 'name':row.get('name'),'core_visible':bool(cores),'height_status':row.get('height_status')})
missing=[r for r in coverage if not r['core_visible']];bad=[o.name for o in visible if not all(math.isfinite(x) for line in o.matrix_world for x in line)];markers=sorted([m for m in sc.timeline_markers if m.name.startswith('EW_1SEC_')],key=lambda m:m.frame);camera_bad=[]
for m in markers:
 if not m.camera or m.camera.type!='CAMERA':camera_bad.append(m.name)
assets=[]
for im in bpy.data.images:
 if im.source=='FILE' and not im.packed_file and not pathlib.Path(bpy.path.abspath(im.filepath)).exists():assets.append(im.name)
r={'visible_objects':len(visible),'visible_meshes':sum(o.type=='MESH' for o in visible),'source_building_records':len(rows),'visible_core_matches':len(rows)-len(missing),'missing_exact_core_names':missing,'nonfinite_transforms':bad,'missing_image_assets':assets,'animation':{'markers':len(markers),'fps':sc.render.fps,'frame_start':sc.frame_start,'frame_end':sc.frame_end,'invalid_bindings':camera_bad,'uniform_24_frame_spacing':all(b.frame-a.frame==24 for a,b in zip(markers,markers[1:]))},'scope':'Exact-name source coverage audit. Replacement landmark and equipment objects require separate reconciliation. Visible geometry does not prove photo accuracy.'};(out/'current_completion_audit_0912.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result={k:v for k,v in r.items() if k!='missing_exact_core_names'};result['missing_core_sample']=missing[:12]
