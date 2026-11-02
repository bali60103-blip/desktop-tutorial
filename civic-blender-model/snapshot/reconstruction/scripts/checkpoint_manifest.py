"""Hash all local .blend backups; record locations, not an assertion of cloud backup."""
import pathlib,hashlib,json,argparse,datetime
p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--out',required=True);a=p.parse_args();root=pathlib.Path(a.root);rows=[]
for f in sorted(root.rglob('*.blend')):
 h=hashlib.sha256()
 with f.open('rb') as stream:
  for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
 rows.append({'path_relative_to_backup_root':str(f.relative_to(root)),'bytes':f.stat().st_size,'sha256':h.hexdigest()})
result={'created_at':datetime.datetime.now().astimezone().isoformat(),'storage':'Local desktop only; GitHub receives this manifest and scripts, not model binaries','gate_status':{'A':'accepted scope; see Stage00 records','B':'in progress, not passed','C':'not passed','D':'not passed','E':'not passed'},'models':rows}
pathlib.Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'models_hashed':len(rows),'total_bytes':sum(x['bytes'] for x in rows)}))
