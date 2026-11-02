import json,pathlib,html,urllib.parse,hashlib,shutil,collections
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'BlockFacades';check=json.load(open(out/'final_model_check.json'));sel=json.load(open(out/'selection_summary.json'));summary=json.load(open(out/'facade_summary.json'));model=pathlib.Path(check['file']);camera_files=sorted((out/'camera_renders').glob('*.png'));baseline=json.load(open(root/'Calibration/camera_review_index.json'));index=[]
for r in baseline:
 r=dict(r);r['orthophoto']='../Calibration/'+r['orthophoto'];r['visual_review']='Full block/facade model contact-sheet review; inferred facades, not street-photo matching';r['model_version']=model.name;index.append(r)
(out/'camera_review_index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2))
text=f'''# 市民大道街廓與立面工作模型

**本階段完成選取範圍內已繪製建物的街廓擴充與估算立面。尚未完成逐棟實景還原。**

## 這次完成的範圍

| 項目 | 數量／內容 |
|---|---|
| 道路廊帶圍合範圍 | {sel['selected_street_blocks']}個，皆未碰到擷取範圍邊界；為近似街廓，不是地籍界 |
| 建物與建築分部 | {sel['mapped_buildings_and_parts']:,}筆，包含一個原有道路廊帶服務建物 |
| 原第一排覆蓋 | {sel['first_row_buildings']:,}個獨立輪廓；小型建物已補回，重合輪廓以對應表保存 |
| 新納入街廓內建物／分部 | {sel['interior_buildings_and_parts']:,}筆 |
| 有立面構件的物件 | {check['counts']['BLOCK_RECESSED_FACADES']:,}個；其餘207個棚架／頂棚類保留屋頂及估算支撐 |
| 立面模組實例 | {summary['facade_instances']:,}組，包含窗、門、實牆、陽台等；不是窗戶總數 |
| 街廓地面、側街與人行道 | 640個分區物件；側街寬度、地面Z=0和人行道尺寸仍含估算 |
| 相機檢查圖 | {len(camera_files)}張：106道路視角及22坡道視角 |

建物數量包含母建築和塔樓、裙樓等分部，不能當作獨立門牌或實際建築棟數。

## 立面做法

窗洞以牆面構件圍成、玻璃向內退約12cm，具有實際凹入幾何；另加入窗框、窗台、入口、設備百葉、陽台及屋頂收邊。各棟以OSM編號掛接，立面與屋頂依附母建物，方便單獨替換。

相鄰量體遮住的界面改為實牆；陽台經近鄰範圍篩查，避免明顯穿入鄰棟。這不是完整的連續碰撞證明。寺廟、學校、華山工業建物等共108筆已調整模板類型，沒有一律套用住宅陽台。

京站、臺北文創與松山車站已納入資料中的塔樓／裙樓分部，保留退縮與不同高度；並非將整個基地拉成單一方塊。多數高度仍來自OSM樓層推估或同街廓已知高度的中位數；原有可用高度來源持續保留。

立面以Geometry Nodes共用構件保留，未實體化成數千萬面。`BLOCK_BUILDING_CORES`是核心量體，`BLOCK_RECESSED_FACADES`是可替換立面，`BLOCK_CONTEXT_GROUND`是周邊地面。這讓下一輪依真實立面逐棟替換時，可保留地理位置與建物ID。

## 驗證

- 完成所有本次核心、屋頂、地面網格的非有限座標、零面積面及封閉邊檢查；立面點位另檢查模組索引、比例及座標。結果見`final_model_check.json`。
- 完成128張道路／坡道模型視角輸出與聯絡表目視檢查。近景與鳥瞰圖用於檢查建築分部、開窗及街廓連續性，不能替代現場照片。
- 原有106道路相機、22坡道相機與總覽相機均保留；另有一支立面檢查相機。開啟模型時的3D視窗已設為全段範圍。
- 原校準場景仍保留在同檔案，另有建置前及中途`.blend`快照。

## 尚未核實

窗型、開口位置、材料、陽台、騎樓、招牌與空調等細節未逐棟比照照片；這版不能當作測繪立面或竣工模型。地面標高、部分建築高度與分隔島設備尺度仍有估算。

本輪53個道路站點的街景頁全部回覆無可用圖像；只代表這次未能讀取，不表示現場沒有街景。相機對照頁右側是國土測繪PHOTO2正射俯視圖，**不是同視角街景**。

先前校準的15條地下淨空衝突路徑仍保留標記，主要為公中與地下街、敦延與延吉等估算外框交會。這些問題沒有因立面完成而被標成已解決。5個居住建築輪廓帶有負layer標籤、以及部分屋頂高度／樓層數矛盾，也列為資料復核項目，不由單一layer標籤直接推定真實標高。

街廓邊界採道路廊帶平面圍合，含高架道路；線在平面交會不代表行人可以同層穿越。未被OSM繪製的建物仍可能缺漏。

## 檔案與備份

- 模型：`{model.name}`
- 主場景：`CIVIC_BLOCKS_FACADES_WORKING`
- 原場景：`CIVIC_COMPLETE_WORKING_ASSEMBLY`
- `街廓覆蓋圖.png`：第一排與街廓內建物範圍
- `立面版相機檢查.html`：128相機圖與正射定位對照
- `全段街廓.png`、`中林街廓近景.png`、`臺北文創分部近景.png`、`松山街廓近景.png`：渲染檢查
- `BEFORE_BLOCK_FACADES.blend`、`CIVIC_BLOCKS_FACADES_PROGRESS.blend`：建置前及中途備份
- `source/`、`scripts/`、`facade_payload.json`：來源、指令與可重建參數

指令與報告備份至[devteam-del/civic](https://github.com/devteam-del/civic/tree/reconstruction/stage-00-scope-audit/reconstruction)。大型模型、圖磚及渲染留在本機；未宣稱`.blend`已推至GitHub。
'''
(out/'街廓立面報告.md').write_text(text)
head='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>市民大道立面版相機檢查</title><style>body{margin:0;background:#182027;color:#edf4f7;font:16px system-ui}header{padding:22px;position:sticky;top:0;background:#182027f5;z-index:2}h1{margin:0 0 8px;font-size:24px}input,select{font:inherit;padding:8px;margin:4px}main{max-width:1500px;margin:auto;padding:20px}.card{border:1px solid #45535d;padding:16px;margin:20px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:14px}img{width:100%;background:#111}.warn{color:#ffcf88}a{color:#80d5ed}small{display:block;line-height:1.7}figure{margin:0}figcaption{padding:8px 0}@media(max-width:700px){.pair{grid-template-columns:1fr}}</style><header><h1>市民大道｜完整街廓・估算立面</h1><div class="warn">128相機模型檢查。立面尚未逐棟實景核實；右圖是正射俯視定位，不是同角度街景。</div><input id="q" placeholder="搜尋里程或相機名稱"><select id="type"><option value="">全部128</option><option value="road">道路106</option><option value="parking">坡道22</option></select><a href="街廓立面報告.md">工作紀錄</a> · <a href="街廓覆蓋圖.png">街廓範圍</a></header><main>'''
cards=[]
for r in index:
 e=html.escape;cards.append(f'<article class="card" data-type="{r["type"]}" data-name="{e(r["name"])}"><h2>{e(r["name"])}</h2><div class="pair"><figure><a href="{urllib.parse.quote(r["model_image"])}"><img loading="lazy" src="{urllib.parse.quote(r["model_image"])}"></a><figcaption>完整街廓模型：窗型、材料與陽台為估算</figcaption></figure><figure><a href="{urllib.parse.quote(r["orthophoto"])}"><img loading="lazy" src="{urllib.parse.quote(r["orthophoto"])}"></a><figcaption>NLSC PHOTO2正射定位參考</figcaption></figure></div><p class="warn">逐相機街景透視比較：尚未完成</p><small>街景頁查詢狀態：{e(r["street_status"])}</small><a href="{e(r["street_url"])}" target="_blank" rel="noopener">查詢此位置街景</a></article>')
tail='''</main><script>function filter(){const q=document.querySelector('#q').value.toLowerCase(),t=document.querySelector('#type').value;document.querySelectorAll('.card').forEach(c=>c.hidden=!(c.dataset.name.toLowerCase().includes(q)&&(!t||t===c.dataset.type)))}document.querySelector('#q').oninput=filter;document.querySelector('#type').onchange=filter;</script></html>''';(out/'立面版相機檢查.html').write_text(head+''.join(cards)+tail)
sc=out/'scripts';sc.mkdir(exist_ok=True)
names=['extract_street_blocks.py','refine_block_boundaries.py','prepare_frontage_blocks.py','prepare_facade_modules.py','refine_facade_semantics.py','complete_small_frontage.py','retain_corridor_service_building.py','prepare_block_context.py','validate_facade_payload.py','build_block_facades.py','build_block_context.py','validate_save_block_facades.py','render_facade_preview.py','render_block_cameras.py','render_block_overviews.py','assemble_block_camera_sheets.py','draw_block_coverage.py','write_block_facade_report.py']
for name in names:shutil.copy2(pathlib.Path('/tmp/civic-stage00/reconstruction/scripts')/name,sc/name)
(out/'REBUILD_ORDER.md').write_text('Run source extraction, refine_block_boundaries, prepare_frontage_blocks, prepare_facade_modules, refine_facade_semantics, complete_small_frontage, retain_corridor_service_building, prepare_block_context, validate_facade_payload. In the calibrated Blender file run build_block_facades in ranges using BUILD_START/BUILD_END, then build_block_context and validate_save_block_facades. Geometry stages use the registered local-metre coordinates in registration.json. The scripts retain the original calibrated scene and build a separate facade scene. Facade geometry is estimated.\n')
manifest={'model':model.name,'model_bytes':model.stat().st_size,'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'camera_images':len(camera_files),'checked_blocks':sel['selected_street_blocks'],'building_records':sel['mapped_buildings_and_parts'],'facade_instances':summary['facade_instances'],'backup_scope':'Scripts and text checkpoints on GitHub; .blend, source geometry payloads and imagery local'};(out/'deliverable_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print(manifest)
