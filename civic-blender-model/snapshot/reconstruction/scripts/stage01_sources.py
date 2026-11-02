"""Acquire source plans and full named-road coverage; never invent elevations.
Run with osmium, pypdfium2 and pillow installed. Source downloads are local only.
"""
import argparse,json,pathlib,urllib.request,hashlib,math,subprocess
import osmium
import pypdfium2 as pdfium
from PIL import Image, ImageDraw

SOURCES={
 'zhonglin_floors_2021':'https://www-ws.gov.taipei/001/Upload/455/relfile/22477/8370555/a70a6f8a-c272-4f25-810e-49ba98995741.pdf',
 'zhonglin_linjin_facilities':'https://www-ws.gov.taipei/001/Upload/455/relfile/22477/9158834/adb80235-54e8-477f-8357-90b9c1625e5f.pdf',
 'jianfu_existing_2020':'https://www-ws.gov.taipei/001/Upload/455/relfile/22477/8197155/ecc2e858-6fd3-4f0b-b234-645e35dde037.pdf',
 'gongzhong_tacheng':'https://www-ws.gov.taipei/001/Upload/455/relfile/22477/8540006/2ca614b1-c650-424a-8287-4ec92f2c2561.pdf',
 'taipei_main_information':'https://web.metro.taipei/img/ALL/INFOPDF/051.pdf',
 'zhongshan_mall_information':'https://web.metro.taipei/c/img/ZhongshanMetroMall.pdf'}

def download(out):
    records=[]
    for key,url in SOURCES.items():
        rec={'id':key,'url':url,'geometry_status':'unregistered source plan; not surveyed XY/Z'}
        try:
            path=out/(key+'.pdf')
            if not path.exists():
                try:
                    data=urllib.request.urlopen(url,timeout=60).read()
                except urllib.error.URLError:
                    # macOS curl uses its certificate trust implementation. Do not disable TLS verification.
                    subprocess.run(['curl','--fail','--location','--max-time','90',url,'-o',str(path)],check=True,capture_output=True)
                    data=path.read_bytes()
                if not data.startswith(b'%PDF'):raise ValueError('not a PDF')
                path.write_bytes(data)
            rec['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            doc=pdfium.PdfDocument(str(path));rec['pages']=len(doc);thumbs=[];texts=[]
            for i,page in enumerate(doc):
                textpage=page.get_textpage();texts.append(textpage.get_text_range())
                scale=min(1.7,2000/max(page.get_size()));im=page.render(scale=scale).to_pil().convert('RGB');im.save(out/(key+f'_p{i+1:02}.png'))
                im.thumbnail((480,290));thumbs.append(im.copy())
            (out/(key+'.txt')).write_text('\n\n'.join(texts))
            sheet=Image.new('RGB',(1000,320*math.ceil(len(thumbs)/2)),'#eeeeee');d=ImageDraw.Draw(sheet)
            for i,im in enumerate(thumbs):
                x=(i%2)*500;y=(i//2)*320;sheet.paste(im,(x,y+25));d.text((x+5,y+4),f'{key} page {i+1}',fill='black')
            sheet.save(out/(key+'_contact.png'));rec['download']='ok'
        except Exception as e:rec['download']='failed';rec['error']=str(e)
        records.append(rec);print(json.dumps(rec,ensure_ascii=False),flush=True)
    (out/'source_register.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))

class Ways(osmium.SimpleHandler):
    def __init__(self):super().__init__();self.rows=[];self.ids=set()
    def way(self,w):
        if '市民大道' not in w.tags.get('name',''):return
        ids=[n.ref for n in w.nodes];self.ids.update(ids);self.rows.append({'id':w.id,'tags':dict(w.tags),'nodes':ids})
class Nodes(osmium.SimpleHandler):
    def __init__(self,ids):super().__init__();self.ids=ids;self.xy={};self.entrances=[]
    def node(self,n):
        if n.id in self.ids:self.xy[n.id]=[n.location.lon,n.location.lat]
        if not (121.48<n.location.lon<121.68 and 25.02<n.location.lat<25.08):return
        tags=dict(n.tags)
        if tags.get('railway')=='subway_entrance' or tags.get('amenity')=='parking_entrance':
            self.entrances.append({'type':'Feature','geometry':{'type':'Point','coordinates':[n.location.lon,n.location.lat]},'properties':{'osm_id':n.id,**tags,'status':'OSM candidate; identity and source-plan correspondence pending','elevation_m':None}})
def extract(pbf,out):
    a=Ways();a.apply_file(str(pbf));print('named ways collected',len(a.rows),flush=True)
    b=Nodes(a.ids);b.apply_file(str(pbf));features=[];missing=[]
    for w in a.rows:
        if not all(n in b.xy for n in w['nodes']):missing.append(w['id']);continue
        coords=[b.xy[n] for n in w['nodes']]
        if not all(121.48<x<121.68 and 25.02<y<25.08 for x,y in coords):continue
        features.append({'type':'Feature','geometry':{'type':'LineString','coordinates':coords},'properties':{'osm_id':w['id'],**w['tags']}})
    for fn,fs in [('civic_all_named_ways.geojson',features),('entrance_candidates.geojson',b.entrances)]:
        (out/fn).write_text(json.dumps({'type':'FeatureCollection','features':fs},ensure_ascii=False))
    report={'named_ways':len(features),'entrance_candidates':len(b.entrances),'missing_node_ways':missing,'road_names':sorted(set(f['properties'].get('name','') for f in features)),'note':'Named-way extraction, not a validated continuous axis or a complete entrance inventory. Entrance selection covers broad Taipei bbox, not only Civic Boulevard.'}
    (out/'extraction_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--pbf',type=pathlib.Path);p.add_argument('--mode',choices=['plans','osm'],required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    if a.mode=='plans':download(a.output)
    else:
        if a.pbf is None:p.error('--pbf required for osm mode')
        extract(a.pbf,a.output)
