"""Read-only scope audit. No Blender mutation; standard-library Python only."""
import argparse, collections, hashlib, json, pathlib, html

def run(model_root, corridor, output):
    output.mkdir(parents=True, exist_ok=True)
    geo=json.loads(corridor.read_text());fs=geo['features']
    points=[p for f in fs for p in f['geometry']['coordinates']]
    bounds=[min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
    manifest=[]
    for p in sorted(model_root.iterdir()):
        if p.is_file() and p.suffix in ['.blend','.py','.json','.md']:
            manifest.append({'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'github_binary_backup':False if p.suffix=='.blend' else None})
    audit={'input_feature_count':len(fs),'bounds_wgs84':bounds,'highway_counts':dict(collections.Counter(f['properties'].get('highway') for f in fs)), 'road_names':sorted(set(f['properties'].get('name','') for f in fs)), 'scope_status':'Existing input does not establish coverage of all sections of Civic Boulevard. Gate A pending.', 'baseline':json.loads((model_root/'final_scene_check.json').read_text()),'assets':manifest}
    audit['baseline']['file']='${CIVIC_MODEL_ROOT}/01_civic_georeferenced_rebuild.blend'
    (output/'scope_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
    x0,y0,x1,y1=bounds
    def xy(p):return (70+(p[0]-x0)/(x1-x0)*1040,310-(p[1]-y0)/(y1-y0)*180)
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="640" viewBox="0 0 1200 640"><rect width="1200" height="640" fill="#f4f2eb"/><g font-family="sans-serif" fill="#203438"><text x="60" y="55" font-size="27">關卡 A｜現有資料範圍與缺口</text><text x="60" y="88" font-size="16">上圖為原始 GeoJSON 路線；經緯度示意，不供量距。地下範圍尚未對位。</text>']
    for f in fs:
        color='#167d8c' if f['properties'].get('highway')=='trunk' else '#aaa08b'
        s=' '.join('%.1f,%.1f'%xy(p) for p in f['geometry']['coordinates'])
        svg.append(f'<polyline points="{s}" fill="none" stroke="{color}" stroke-width="2"/>')
    svg.append(f'<text x="60" y="360" font-size="15">現有經度範圍 {x0:.5f}–{x1:.5f}；東側後續路段需重新取得完整路線</text>')
    for i,(title,detail) in enumerate([('地上：第一排建物','按實際臨路面選取；120m 裁切帶不是第一排定義'),('地下：停車場與地下街','先建立設施／樓層／出入口清單，不以分隔島寬度推估地下邊界'),('結構：未查證柱位','241 處沿用假設；不能用於實際淨寬或阻隔量測')]):
        y=410+i*65;svg.append(f'<text x="60" y="{y}" font-size="19">{html.escape(title)}</text><text x="60" y="{y+25}" font-size="15">{html.escape(detail)}</text>')
    svg.append('</g></svg>');(output/'gate_A_scope.svg').write_text(''.join(svg))
    print(json.dumps({'features':len(fs),'bounds':bounds,'output':str(output)},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model-root',required=True,type=pathlib.Path);p.add_argument('--corridor',required=True,type=pathlib.Path);p.add_argument('--output',required=True,type=pathlib.Path);a=p.parse_args();run(a.model_root,a.corridor,a.output)
