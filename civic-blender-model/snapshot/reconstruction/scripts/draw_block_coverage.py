import json,pathlib,math
from PIL import Image,ImageDraw,ImageFont
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/BlockFacades');blocks=json.load(open(out/'blocks.json'));buildings=json.load(open(out/'buildings_selected.json'));W,H=3000,850;allpoints=[]
def rings(g):
 if g['type']=='Polygon':return g['coordinates']
 return [ring for p in g['coordinates'] for ring in p]
for b in blocks:allpoints.extend([p for ring in rings(b['geometry']) for p in ring])
x0=min(p[0] for p in allpoints);x1=max(p[0] for p in allpoints);y0=min(p[1] for p in allpoints);y1=max(p[1] for p in allpoints);scale=min((W-100)/(x1-x0),(H-180)/(y1-y0));im=Image.new('RGB',(W,H),(19,27,34));d=ImageDraw.Draw(im);font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf',24);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf',18)
def pos(q):return (50+(q[0]-x0)*scale,100+(y1-q[1])*scale)
for b in blocks:
 for ring in rings(b['geometry']):d.line([pos(p) for p in ring],fill=(76,133,141),width=1)
for b in buildings:
 color=(234,167,91) if b['first_row'] else (139,159,170)
 for ring in rings(b['geometry']):d.polygon([pos(p) for p in ring],fill=color)
d.text((40,20),'市民大道｜第一排所在街廓擴充：303 個道路圍合範圍 / 3,604 個已繪製建物與分部',font=font,fill='white');d.text((40,H-75),'橘色：第一排建物　灰色：街廓內建物／分部　藍綠線：道路廊帶近似街廓（非地籍界）',font=small,fill=(221,228,233));d.text((40,H-43),'來源：使用者提供 OSM 2026-09-08；立面比例為估算，不代表逐棟實景還原。',font=small,fill=(221,228,233));im.save(out/'街廓覆蓋圖.png');print(str(out/'街廓覆蓋圖.png'))
