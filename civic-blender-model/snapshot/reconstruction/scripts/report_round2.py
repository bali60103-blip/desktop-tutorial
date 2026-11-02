import pathlib,json,hashlib,shutil,ast
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/CalibrationRound2');src=out/'source';src.mkdir(exist_ok=True);shutil.copy2('/tmp/yanji_official.pdf',src/'延吉段官方地面與B1示意圖.pdf')
url='https://www-ws.gov.taipei/Download.ashx?icon=..pdf&n=MDctNS0x5biC5rCR5aSn6YGT5bu25ZCJ5q6156S65oSP5ZyWKOePvuazgeWclikucGRm&u=LzAwMS9VcGxvYWQvNDU1L3JlbGZpbGUvMjI0NzcvODE5NzE1NS84NmZjNTAzZi02YTYwLTQxOTctYmE3ZC05ZTIxMGYwZTVmNDAucGRm'
facts={'source_url':url,'retrieved':'2026-09-11','source_sha256':hashlib.sha256((src/'延吉段官方地面與B1示意圖.pdf').read_bytes()).hexdigest(),'observations':['B1 shown; official parking directory separately states one underground level','Stair1 near Yanji Street; Stair2 near Jingfu Temple','A/B/F supply air; C exhaust air; D water tank; E generator air outlet'],'limits':'Schematic with no usable georeferenced control or absolute elevations; do not treat pixel distance as measured scale.'};(out/'source_evidence.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2))
check=json.load(open(out/'final_check.json'));model=pathlib.Path(check['file']);manifest={'model':model.name,'bytes':model.stat().st_size,'sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'backup_scope':'Scripts/checkpoints GitHub; blend/PDF/render local'};(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
(out/'第二輪校準紀錄.md').write_text('''# 第二輪校準 2026-09-11

本輪完成一處估算幾何修正，未完成全部實景校準。

- 最新模型延吉段原本已只有B1。確認後未刪除任何樓層；B1=-3.6m仍是估算標高。
- 沿既有延吉坡道在外牆建立2.7m估算開口，移除約0.8903m²牆體平面範圍。這是消除生成衝突，並非已由實測證明的位置或通行寬度。原坡道寬約2.2m仍待校準，不代表車行設計合規。
- 新牆網格封閉邊與有限座標檢查通過。117條路徑、6669個向上射線樣點重查，延吉坡道該條路徑不再命中外牆。
- 原先未完整納入的校正屋頂重新加入檢查，公中CORE_公中_0_B1_B新增受阻記錄。舊15條中修正1條、新發現1條，目前仍15條。抽樣不是連續淨空或轉彎掃掠認證。
- 更新15處衝突標記；公中地下街與停車場交會、敦延／延吉估算外框重疊均維持待核對。
- 原始校準場景、昨日存檔及本輪修改前快照保留。只在目前工作場景換入新停車場與標記集合。
- 延吉坡道相機已重新渲染並目視檢視；影像仍可見估算地下構件，不能當作通行已全面無障礙的證明。

官方平面圖：地面層及B1示意，兩處樓梯及送排風、水塔、發電機出風口可辨識；未提供可直接對位的尺寸與絕對標高，尚未據此搬動設備或重畫敦延／延吉界線。

來源：'''+url+'''

下一步：以圖面街口控制点校準延吉入口、樓梯與設備平面位置，避免強行套用示意圖比例；其後校準地標立面。所有街廓立面仍是估算版。臺北文創來源頁本輪讀取失敗，未作新的實景立面修正。
''')
sc=out/'scripts';sc.mkdir(exist_ok=True)
names=['export_yanji_wall.py','prepare_yanji_entry_cut.py','apply_yanji_entry_cut.py','check_round2_headroom.py','render_round2_entry.py','finish_round2.py','report_round2.py']
items=[]
for n in names:
 p=pathlib.Path('/tmp/civic-stage00/reconstruction/scripts')/n;ast.parse(p.read_text());shutil.copy2(p,sc/n);items.append({'path':'reconstruction/scripts/'+n,'mode':'100644','type':'blob','content':p.read_text()})
for n in ['第二輪校準紀錄.md','source_evidence.json','final_check.json','manifest.json']:
 items.append({'path':'reconstruction/checkpoints/calibration_round2_20260911/'+n,'mode':'100644','type':'blob','content':(out/n).read_text()})
pathlib.Path('/tmp/round2_backup.json').write_text(json.dumps(items,ensure_ascii=False));print(manifest)
