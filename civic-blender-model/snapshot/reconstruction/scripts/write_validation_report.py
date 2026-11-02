import json,pathlib,hashlib,datetime
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Validation'
def read(n):return json.load(open(out/n))
a=read('technical_audit.json');w=read('walk_envelope_audit.json');f=read('final_validation_check.json');m=read('assets_metadata_check.json');n=sum(c['samples'] for c in w['checks']);rays=sum(c['obstacle_rays'] for c in w['checks'])
text=f'''# 市民大道模型驗證紀錄

驗證日期：{datetime.datetime.now().isoformat(timespec='seconds')}。本次驗證已出具結果，**整體模型尚未通過最終驗收**。

目前模型：`{a['file']}`。原始模型、修正前完整快照與被替換網格皆保留。GitHub 備份的是指令及報告，`.blend` 完整檔在本機。

## 本次重跑結果

| 檢查 | 結果 | 範圍及證據 |
|---|---|---|
| 基礎網格 | 主場景通過本次指標 | {a['totals']['used_mesh_datablocks']:,} 個使用中的 mesh datablock；主渲染物件異常由 2 降為 0。全檔仍有 {a['mesh_issue_count']} 個保留來源／舊模型／平面網格標記，未宣告全檔封閉。見 technical_audit.json。 |
| 修改器輸出 | **未通過** | 道路 3 條、分隔島 2 條多面共邊；兩者邊界邊與零面積面均為 0。這些布林結果不包含在基礎網格的通過結論內。 |
| 地下入口行走抽樣 | 通過指定路徑 | 19 個直梯比較入口＋Y26 B 整合版，共 {n} 個位置、{rays:,} 條障礙射線，碰撞 0；中心腳底缺乏支撐 0。含屋頂與渲染隱藏玻璃，排除封存舊件。 |
| 行走範圍限制 | 不是完整動線驗收 | 直徑 0.60m、高 1.80m；下方 0.20m 排除以容許鄰接踏階。樓梯每階中點、連接段約 0.2m 取樣；非連續掃掠、非輪椅／消防／全模型碰撞檢查。 |
| 道路相機 | 通過 | 106 支、53 組南北配對；正常間距 200m，末段 195.0465m；重複視角 0、舊 500m 相機 0。 |
| 停車場相機 | 保留 | 9 支坡道相機；數量不代表真實出入口已完整建模。 |
| 顯示及外部資產 | 通過本次指標 | 視窗遠裁切 30,000m；無非有限變換、零縮放或不合法相機參數。3 個外部資產均存在。 |
| 來源標记 | 已盤點，非來源真實性認證 | {m['mesh_objects_with_explicit_provenance_or_assumption_fields']} 個網格物件有來源／假設／高度等屬性。其餘須參照集合與階段報告；未逐筆證實現地。 |
| 渲染 | 已檢視 Y26 修正版 | Y26_clearance_verified.png。屋頂及玻璃的剖視隱藏是展示設定；檢查後相機及屋頂設定已復原。未逐張驗收全部道路相機渲染。 |

## 已修正

1. 道路模型 (5950.9243, 895.3669)，Z=-0.25～0 的四面共邊：拆開局部面群的頂點連結，不移動座標。基礎網格恢復封閉流形。
2. 建物模型 (3525.7981, 978.7774)，Z=0～12 的零寬度牆面：合併該面的精確重複頂點，刪除退化面；未調整建物位置或高度。
3. Y26 B 樓梯末兩階：原中心線檢查漏掉身體側向碰撞，抽樣發現 20 次側牆命中。將舊地下街邊牆依完整估算梯口切開並封存過時牆片；重跑命中為 0。

以上修正均為工作模型生成錯誤修復，不能證明真實 Y26 方位或尺寸。

## 全範圍仍未通過項目與改善方式

| 項目 | 問題／證據 | 改善方式 |
|---|---|---|
| 道路及分隔島布林 | 修改器新增 5 條非流形共邊 | 保留可編輯原案，另產生布林後清理版；核對洞口面積、坡道邊界與坐標後再採用，避免只封面堵住洞口。 |
| 柱位 | 036、114、408、438、534、540、674 共 7 組替代移柱未通過估算分隔島範圍篩選 | 先以可定位街景／橋墩表定柱，再重做車道、坡道淨空檢查；無資料保留冲突，不任意移到車道。 |
| 高架支承 | 3 組柱帽 577、680、681 未裝支承；114 處候選交集放不下比較支承 | 核對梁底與柱帽實形後重建局部；0.20m 支承及柱帽降低僅為比較假設。 |
| 高架匝道分合流 | 47 段原模型封端已做，但實際寬度、標高及合流幾何未校準 | 用同時期正射影像、街景與高程控制點核對；封閉網格不代表匝道位置正確。 |
| 停車場外框 | 敦延／延吉約 85m 長、2040m² 重疊保留；公園路控制投影差約 60.73m | 以官方平面圖定界，保留兩個外框比較，不能視為已確認地下連通。 |
| 停車場內部 | 8 段、14 樓板、6 通用層間坡道是比較版；不等同各段真實坡道、車位、機房 | 按各段平面圖重做端部迴轉及坡道；查樓板開口與車行淨空。 |
| 地下街與 Y26 | 既有地下輪廓身分與範圍未獨立驗證；Y26 建物長軸方位只是替代推估 | 保留 A/B；用可定位入口照片或測量圖核對，再整合地面。19 直梯不是19個真實入口形式。 |
| 高程與地形 | B1/B2=-3.6/-7.2m、地下街淨高2.8m均為使用者選定假設；地面不是實測地形 | 建立獨立高程控制與地面縱坡，不能將OSM同源配準視為實測驗證。 |
| 第一排建物 | 527 棟比較量體；581 候選缺高度，且多重多邊形來源未完整涵蓋 | 補來源輪廓，以官方高度／可定位影像／周邊建物估算，逐棟標記可信度。 |
| 分隔島及高架下 | 設備候選資料不等於所有機房、通風井、設施已定位建模 | 按路段拍攝時間與坐標盤點，補實體量體與通行寬度。 |
| 南北分隔分析與疊圖系統 | 本次未驗證產業資料完整性及南北差異因果 | 另做產業分類、步行穿越距離與出入口網路指標；目前模型不可直接作為因果結論。 |

## 大關卡判定

A：範圍工作表可追蹤，來源完整性仍有缺口。B：實測座標／高程未通過。C：地下與道路樣板技術檢查部分通過，幾何與現地疑慮仍存。D：全段整合／動線／逐相機渲染未通過。E：最終現況還原驗收未通過。

本次把能執行的網格、指定路徑、相機、資產與比較渲染檢查做完並記錄；尚無資料或未執行的檢查明列，不以推估替代通過。

原始結果：technical_audit.json、walk_envelope_audit.json、repair_check.json、final_validation_check.json、assets_metadata_check.json；before_*.json 保留修正前結果。跨階段問題參考原 BearingDetail、ParkingSections、FullFrontageSolids、Worksheet04_05 報告，未聲稱本次重新實測。
'''
(out/'VALIDATION_REPORT_zh-TW.md').write_text(text)
files=[p for p in out.iterdir() if p.suffix in ['.json','.md','.png']]+[pathlib.Path(a['file'])]
manifest=[]
for p in files:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 manifest.append({'file':str(p),'bytes':p.stat().st_size,'sha256':h.hexdigest(),'backup':'local binary' if p.suffix in ['.blend','.png'] else 'GitHub report'})
(out/'validation_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print({'report':str(out/'VALIDATION_REPORT_zh-TW.md'),'files_hashed':len(manifest),'samples':n,'rays':rays})
