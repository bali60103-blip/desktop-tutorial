import json,pathlib,html,math,urllib.parse,hashlib,shutil
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Calibration';report=json.load(open(out/'final_checkpoint.json'));stations=json.load(open(out/'corrected_camera_stations.json'));imagery=json.load(open(out/'imagery_current.json'));street=[]
for p in sorted(out.glob('street_batch_*.json')):street+=json.load(open(p))
street={r['label']:r for r in street};(out/'streetview_availability.json').write_text(json.dumps(list(street.values()),ensure_ascii=False,indent=2));imgs={r['label']:r for r in imagery['stations']};sight={r['name']:r for r in json.load(open(out/'scene_audit.json'))['camera_sightlines']};rows=[]
for p in sorted((out/'camera_renders').glob('*.png')):
 name=p.stem;road=name.startswith('CIVIC200_');label=name.split('_')[1] if road else name;im=imgs[label];lon,lat=im['lonlat'];heading=180 if road and name.endswith('_S') else 0;url=f'https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}&heading={heading}&pitch=0&fov=65.47';sv=street.get(label);status=sv['status'] if sv else 'parking viewpoint not independently checked; road checks unavailable';rr={'name':name,'type':'road' if road else 'parking','model_image':'camera_renders/'+p.name,'orthophoto':str(pathlib.Path(im['image']).relative_to(out)),'lonlat':[lon,lat],'street_url':url,'street_status':status,'actual_street_comparison':'NOT_COMPLETED','visual_review':'Model contact-sheet inspected; simplified estimated massing, not photorealistic site reconstruction','near_obstruction':sight.get(name)};rows.append(rr)
(out/'camera_review_index.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
text='''# 市民大道校準紀錄

**狀態：模型修正與檢查已執行；整輪現地校準尚未完成。不能把本版當作竣工還原。**

## 本版已套用的修改

- 道路相機改採連續的已繪製市民大道道路路徑，每200m南北各一支，保留53對、106支；另保留22支坡道相機及1支總覽相機。路徑約10.316km，是分析里程，不是官方工程樁號。沒有將整条道路或高架任意平移。
- 移除組合場景內5個誤拉成地上量體的地下設施：K區地下街、捷運台北車站、中山地下街、松山地下車站、南港地下站。來源的 `location=underground` 已明示地下位置；原版本留在快照。
- 49處現有工作模型入口的地面開口完成幾何整合。路緣、標線與R1上方兩層重疊頂板同步清理；這些切口跟隨估算入口，不能當作實際開挖位置。
- 12個擋路的生成柱及1片生成隔間移至排除的比較集合；170個舊中林坡道樣板物件退出組合場景，原方案保留。
- 672塊生成踏階原本向下填滿、阻擋下層樓梯，已改為估算0.20m厚踏階。這是模型修正，不是結構改造方案。
- 南港展覽館二館總量體高度由16.5m估算值改為建築師公布的46.05m；OSM外框和簡化屋頂仍待細部校核。

## 檢查結果與限制

| 項目 | 實際結果 | 尚不能證明的事項 |
|---|---|---|
| 平面影像 | 53個原道路站點的官方正射疊圖已目視篩查；更新後另建立75個道路／坡道位置對照圖，262張所需圖磚成功取得 | 高架下機房、柱腳與入口受遮擋，不能由橋面影像判定地面精確位置 |
| 道路／高架 | 大致追隨已繪製線位；沒有足夠控制點支持全局改線 | 逐段橋緣、分合流曲線、所有橋墩中心與路寬的測量精度 |
| 修改網格 | 5441個可見修改物件通過非有限座標、零面積面及封閉邊檢查 | 不代表所有交疊消失，也不代表結構正確 |
| 平面通行代理檢查 | 117段路徑對柱體／隔間的代理交會檢查未再檢出；49處地面開口無剩餘覆蓋 | 非完整車輛轉彎或連續三維掃掠檢查 |
| 含頂板淨空 | 6669次向上射線抽樣；修正後仍有15段路徑命中遮擋 | 不可標為通行驗收通過；主要牽涉公中與地下街重疊、敦延／延吉重疊及延吉入口牆 |
| 相機 | 106道路＋22坡道視角輸出與目視篩查；另保留1總覽相機 | 正射圖是俯視定位參考，不能冒充同視角街景 |
| 街景 | 53道路站點逐一查詢，頁面全部回覆無可用街景圖像 | 128視角的實景透視比較未完成；不推論現場本來就沒有街景 |

## 仍需現地證據的部分

1. 絕對標高：目前地面Z=0、停車場B1/B2=-3.6/-7.2m仍是假設。中華顧問工程司文獻提供約5.7/5.4m結構層高，與現模型不同；層高不等於淨高，也不能直接換成相對路面深度。未任意重設全部地下層。
2. 機房：官方平面圖能佐證部分設施存在，無法由標籤推得實際長寬高；高架遮擋正射影像，街景又未成功提供圖像，因此14個地面設備估算位置及尺寸仍未校準。6m×0.6m的LED招牌尺寸未被誤用為機房尺寸。
3. 地標：京站公布的69.95m為複合開發高度，不能把整個商場底座拉到該高度；松山車站81/84.8m分屬不同量體，仍須辨識塔樓外框。其他無高度建物的鄰房估算沒有被改稱實測。
4. 15條淨空衝突路徑已在 Blender 的 `CALIBRATION_UNRESOLVED_POSITIONS` 標記。敦延／延吉外框仍遵照先前選擇保留比較，沒有為了消除警示而挖穿另一個停車場。
5. 03K800南向相機中央視線約0.4m即碰到估算橋柱；04K400北向距建物約2.35m。保持分析樁距並列入相機遮擋紀錄，未移動未驗證橋柱以美化畫面。

## 來源

- [國土測繪圖資服務雲](https://maps.nlsc.gov.tw/S09SOA/pro/Wmts_ajax_main.jsp)：PHOTO2正射影像；原53站影像可見NLSC2024浮水印，下載日期不代表拍攝日期。是航測正射影像，未宣稱衛星感測器。
- [臺北市橋梁管理系統：市民大道主橋D028](https://bridge.nco.taipei/bms2/guest/bridge/inventory.aspx?vid=28846)：橋梁範圍與寬度參考，非逐柱座標表。
- [中華顧問工程司2014年工程文獻](https://www.ceci.org.tw/Upload/Download/BE9F1DB3-1378-4492-BE0A-F183E2BE3798.pdf)：印刷頁88地下結構層高。
- [建築師發表：南港展覽館二館](https://www.twarchitect.org.tw/works/國家會展中心南港展覽館二館/)：46.05m總高度。
- [京站開發案建築師資料](https://www.onenessarchitects.com/project/Redium-Parcel-9-Taipei-Main-Station-BOT-Joint-Development?lang=tw)：複合量體高度與樓層用途。
- [建築師發表：松山車站共構](https://www.twarchitect.org.tw/works/潤泰松山車站共構bot/)：分棟高度。

## 檔案

- 模型：`CIVIC_CALIBRATION_20260910_192914.blend`
- 相機對照：`相機檢查.html`、`camera_review_index.json`
- 每條淨空命中物件：`headroom_check.json`
- 修改前快照：`BEFORE_CALIBRATION_20260910_192914.blend`、`BEFORE_HEADROOM_CORRECTIONS.blend`
- 生成與校驗腳本備份於GitHub `devteam-del/civic` 的 `reconstruction/stage-00-scope-audit`；大型Blender檔及影像留本機。
'''
(out/'校準報告.md').write_text(text)
head='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>市民大道相機校核</title><style>body{margin:0;background:#182027;color:#edf4f7;font:16px system-ui}header{padding:24px;position:sticky;top:0;background:#182027ee;z-index:2}h1{margin:0 0 8px;font-size:24px}input,select{font:inherit;padding:8px;margin:4px}main{max-width:1500px;margin:auto;padding:20px}.card{border:1px solid #45535d;padding:16px;margin:20px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:14px}img{width:100%;background:#111}.warn{color:#ffcf88}a{color:#80d5ed}small{display:block;line-height:1.7}figure{margin:0}figcaption{padding:8px 0}@media(max-width:700px){.pair{grid-template-columns:1fr}}</style><header><h1>市民大道｜128相機模型檢查</h1><div class="warn">街景透視比對尚未完成。右圖為官方正射俯視定位參考，不是同視角街景。</div><input id="q" placeholder="搜尋里程、相機名稱"><select id="type"><option value="">全部</option><option value="road">道路106</option><option value="parking">坡道22</option></select><a href="校準報告.md">完整校準紀錄</a></header><main>'''
cards=[]
for r in rows:
 e=html.escape;obs=r['near_obstruction'];note=''
 if obs and obs['distance_m'] is not None and obs['distance_m']<3:note=f"中央視線近距遮擋：{obs['central_ray_hit']}，約{obs['distance_m']:.2f}m。"
 cards.append(f'<article class="card" data-type="{r["type"]}" data-name="{e(r["name"])}"><h2>{e(r["name"])}</h2><div class="pair"><figure><a href="{urllib.parse.quote(r["model_image"])}"><img loading="lazy" src="{urllib.parse.quote(r["model_image"])}"></a><figcaption>模型：估算量體與已套用修正</figcaption></figure><figure><a href="{urllib.parse.quote(r["orthophoto"])}"><img loading="lazy" src="{urllib.parse.quote(r["orthophoto"])}"></a><figcaption>NLSC PHOTO2 正射定位參考（紅點為相機平面位置）</figcaption></figure></div><p class="warn">實景透視比較：未完成。{e(note)}</p><small>經緯度 {r["lonlat"]}｜街景查詢狀態：{e(r["street_status"])}</small><a href="{e(r["street_url"])}" target="_blank" rel="noopener">開啟該位置街景查詢</a></article>')
tail='''</main><script>function filter(){const q=document.querySelector('#q').value.toLowerCase(),t=document.querySelector('#type').value;document.querySelectorAll('.card').forEach(c=>c.hidden=!(c.dataset.name.toLowerCase().includes(q)&&(!t||t===c.dataset.type)))}document.querySelector('#q').oninput=filter;document.querySelector('#type').onchange=filter;</script></html>'''
(out/'相機檢查.html').write_text(head+''.join(cards)+tail)
# Keep rerunnable inputs and scripts beside the deliverable, not only in temporary directories.
scriptout=out/'scripts';scriptout.mkdir(exist_ok=True)
for p in pathlib.Path('/tmp/civic-stage00/reconstruction/scripts').glob('*calibration*.py'):shutil.copy2(p,scriptout/p.name)
for name in ['calibrate_route_axis.py','prepare_calibrated_openings.py','fetch_current_camera_orthos.py','prepare_flow_corrections.py','apply_flow_corrections.py','prepare_secondary_opening_corrections.py','export_secondary_opening_surfaces.py']:
 p=pathlib.Path('/tmp/civic-stage00/reconstruction/scripts')/name;shutil.copy2(p,scriptout/name)
shutil.copy2('/tmp/civic-calibration/road_graph.json',out/'source/road_graph.json');shutil.copy2('/tmp/civic-calibration/route_graph.py',scriptout/'route_graph.py');shutil.copy2('/tmp/civic-calibration/check_streetviews.cjs',scriptout/'check_streetviews.cjs')
print({'camera_cards':len(rows),'road_station_street_checks':len(street),'no_imagery':sum(r['no_imagery_message'] for r in street.values()),'report':str(out/'校準報告.md')})
