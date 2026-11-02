"""Write data/key_metrics.csv: the model's headline numbers, each with its
evidence type and the civic report it was copied from.

These rows are transcribed by hand from prose reports (Markdown / docstrings),
so they live here instead of being parsed. Paths are relative to the civic
repository (and to ../snapshot/).

性質（evidence）:
  官方資料     官方或建築師公布的數字
  模型統計     Blender 模型內物件的計數或量測，不是現地測量
  估算         為了建模而推估的尺寸、位置或數量
  使用者選定   使用者指定的工作假設
  佔位資料     原始模型裡的預設／重複幾何，不能當成數據用
  檢查結果     對模型跑的幾何或抽樣檢查
"""
import csv
import os

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "key_metrics.csv")

R = []


def m(cat, item, value, unit, evidence, date, source, note=""):
    R.append(dict(類別=cat, 項目=item, 數值=value, 單位=unit, 性質=evidence,
                  日期=date, 來源檔案=source, 備註=note))


# ---- 原始基地模型 site model 市民大道new.blend ----
S = "原始基地模型"
m(S, "行道樹樹冠", 10000, "個", "佔位資料", "2026-09-09", "src/measure_blend_model.py; CLAUDE.md",
  "每個都是 3.00×2.60×3.00 m，各維度標準差 4e-06；只有位置可用，樹冠面積／體積不可計算")
m(S, "樹幹", 10000, "個", "佔位資料", "2026-09-09", "src/measure_blend_model.py", "與樹冠同為一致幾何")
m(S, "建物量體（分離後）", 19592, "個", "模型統計", "2026-09-09",
  "src/measure_blend_model.py; reconstruction/archive/registration.json")
m(S, "建物高度推算方式", "building:levels × 3.2", "m／層", "估算", "2026-09-09", "CLAUDE.md")
m(S, "高度剛好為預設 12.0 m 的比例", 42.4, "%", "佔位資料", "2026-09-09", "CLAUDE.md; README.md",
  "高度統計因此同時報「全部」與「排除預設值」")
m(S, "建物高度缺值率（北／南）", "30.4 / 29.7", "%", "模型統計", "2026-09-09", "README.md")
m(S, "護欄高", 1.1, "m", "佔位資料", "2026-09-09", "CLAUDE.md", "與隔音牆是同一段幾何的兩個高度版本，不是兩個實測物件")
m(S, "隔音牆高", 3.0, "m", "佔位資料", "2026-09-09", "CLAUDE.md", "同上")
m(S, "高架軸線旁人行天橋／地下道", "3 / 0", "座", "模型統計", "2026-09-09",
  "README.md; src/measure_blend_model.py", "軸線 6.53 km；同段 32 條車行匝道（OSM）")
m(S, "貼線 100 m 內北側／南側建物平均高度比", 1.5, "倍", "模型統計", "2026-09-09", "README.md",
  "200 m 外反轉；以排除預設高度的子集計算")
m(S, "量測結果檔 data/processed/h_blend.json", "未進版控", "", "檢查結果", "2026-09-09", "CLAUDE.md",
  "橋墩組數、柱距、橋面面積等完整輸出只在本機，需用 Blender 匯出後重跑 run_all.sh")

# ---- 重建基準 01_civic_georeferenced_rebuild.blend ----
S = "重建基準版集合"
for name, n, ev in [("01_Sidewalks_official_XY 人行道（官方平面）", 376, "模型統計"),
                    ("02_Roads_official_extent 道路（官方範圍）", 211, "模型統計"),
                    ("03_Islands_estimated_width 分隔島", 2, "估算"),
                    ("04_Elevated_deck_estimated 高架橋面", 30, "估算"),
                    ("05_Parapets_estimated 護牆", 60, "估算"),
                    ("06_Steel_girders_estimated 鋼梁", 360, "估算"),
                    ("07_Piers_legacy_UNVERIFIED 舊橋墩物件", 482, "估算"),
                    ("08_Official_column_candidates_HIDDEN 官方柱位候選", 13, "模型統計"),
                    ("13_Median_gap_inference 分隔島空隙推論", 7, "估算"),
                    ("新增集合物件合計", 1552, "模型統計"),
                    ("已驗證為測量位置的橋墩", 0, "檢查結果")]:
    m(S, name, n, "個", ev, "2026-09-09", "reconstruction/reports/scope_audit.json")

# ---- 地面層 ----
S = "地面層（一至八段）"
G = "reconstruction/reports/ground_full/REVIEW.md"
m(S, "官方歷史道路面", 152, "筆", "官方資料", "2026-09-10", G, "年代約 2014–2016，不保證現況")
m(S, "官方人行道輪廓", 375, "筆", "官方資料", "2026-09-10", G)
m(S, "具一至八段名稱的地面 OSM 路線", 106, "條 way", "模型統計", "2026-09-10", G + "; reconstruction/docs/GATE_B.md",
  "另有高架 way 30 條")
m(S, "OSM 穿越點", 163, "個", "模型統計", "2026-09-10", G, "47 個重複抑制、116 個生成標線，合計 1,980 片標線")
m(S, "候選路緣降坡", 208, "處", "估算", "2026-09-10", G, "不證明現地存在或符合無障礙規範")
m(S, "具 CEN_MEDIAN 面積的官方道路", 84, "筆", "官方資料", "2026-09-10", G, "分隔島形狀由車道間隙估算，寬度上限 12 m")
m(S, "道路面高程／厚度", "Z=0 / 0.25", "m", "估算", "2026-09-10", G, "未復原實際縱坡")
m(S, "人行道／路緣／分隔島高", "0.15 / 0.17 / 0.18", "m", "估算", "2026-09-10", G)
m(S, "中林樣段路緣石／鋪磚", "623 / 20,066", "塊", "估算", "2026-09-10", G, "只有中林樣段有此細節")

# ---- 高架 ----
S = "高架與橋下"
W = "reconstruction/reports/worksheet04_05/REVIEW.md"
SP = "reconstruction/reports/underbridge_0922/span_height_notes.md"
m(S, "柱身（估算柱位）", 241, "個", "估算", "2026-09-10", W + "; " + SP, "0 處確認為測量柱位")
m(S, "柱帽組（隱藏 111 個重複後）", 130, "組", "模型統計", "2026-09-10", W, "不能當作現地橋墩或橋孔數")
m(S, "柱位衝突", 7, "組", "檢查結果", "2026-09-10", W,
  "036、114、408、438、534、540、674；移柱搜尋（兩向 1–20 m）全部無解，原位紅色標記")
m(S, "支承比較版：柱帽頂降低", -0.20, "m", "使用者選定", "2026-09-10", "reconstruction/docs/WORKSHEET.md",
  "127 組降低、473 組估算支承、3 組無適配（577、680、681）、114 處交會待解")
m(S, "匝道分合流封端", 47, "段", "估算", "2026-09-10", "reconstruction/checkpoints/validation_20260910/VALIDATION_REPORT_zh-TW.md",
  "寬度、標高與合流幾何未校準")
m(S, "候選柱間跨段", 116, "跨", "模型統計", "2026-09-22", SP, "依 30 條橋面中心線配對；非確認的真實跨徑")
m(S, "有部分地面對應的跨段", 82, "跨", "模型統計", "2026-09-22", SP)
m(S, "淨高缺測跨段", 34, "跨", "檢查結果", "2026-09-22", SP, "缺值保留空白，不以零補")
m(S, "橋面歸屬不明的柱位", 19, "個", "檢查結果", "2026-09-22", SP)
m(S, "需人工判讀的端點連接", 8, "組", "檢查結果", "2026-09-22", SP)
m(S, "間距超過 60 m 的跨段", 69, "跨", "檢查結果", "2026-09-22", SP, "需檢查漏柱或誤配")
m(S, "未組成跨段的柱位", 2, "個", "檢查結果", "2026-09-22",
  "reconstruction/reports/underbridge_0922/span_height_coverage_gaps.json", "598、621；另有 13 條橋面路徑無量測")
m(S, "模型橋面取樣高度", "約 8", "m", "佔位資料", "2026-09-22", SP, "舊模型統一假設，沒有實際縱坡")
m(S, "模型取樣淨高", "5.42–5.60", "m", "模型統計", "2026-09-22", SP, "不能當現場通行尺寸")
m(S, "官方 D028 市民大道高架橋主橋：總長", 5802.5, "m", "官方資料", "2026-09-22", SP,
  "https://bridge.nco.taipei/bms2/guest/bridge/inventory.aspx?vid=28846")
m(S, "官方 D028：孔數", 160, "孔", "官方資料", "2026-09-22", SP, "主橋範圍不等於模型配對範圍，不能用 160−116 推漏跨")
m(S, "官方 D028：淨寬", "18–28.5", "m", "官方資料", "2026-09-22", SP)

# ---- 地下 ----
S = "地下停車場與地下街"
V = "reconstruction/checkpoints/validation_20260910/VALIDATION_REPORT_zh-TW.md"
C = "reconstruction/checkpoints/calibration_20260910/校準報告.md"
m(S, "B1／B2 樓板高程", "-3.6 / -7.2", "m", "使用者選定", "2026-09-10", W, "無測量高程基準")
m(S, "地下街淨高", 2.8, "m", "使用者選定", "2026-09-10", V)
m(S, "文獻地下結構層高", "約 5.7 / 5.4", "m", "官方資料", "2026-09-10", C,
  "中華顧問工程司 2014 文獻印刷頁 88；層高不等於淨高，未用來改模型")
m(S, "停車場段數／樓板／層間坡道", "8 / 14 / 6", "段／片／條", "估算", "2026-09-10", V, "通用比較版，不是各段真實配置")
m(S, "車位分隔線構件", 1919, "個", "估算", "2026-09-10", "reconstruction/checkpoints/completion_20260910/WORKING_MODEL_README.md",
  "不是停車格數")
m(S, "地面至 B1 估算坡道", 13, "條", "估算", "2026-09-10", "reconstruction/checkpoints/completion_20260910/WORKING_MODEL_README.md")
m(S, "地下街新增構件（柱列、隔間、燈具、R1 樓梯）", 702, "個", "估算", "2026-09-10",
  "reconstruction/checkpoints/completion_20260910/WORKING_MODEL_README.md", "未編造店名")
m(S, "敦延／延吉外框重疊", "約 85 m／2,040 m²", "", "檢查結果", "2026-09-10", V, "保留兩個外框，未確認地下連通")
m(S, "公園路控制投影差", 60.73, "m", "檢查結果", "2026-09-10", V)
m(S, "台北車站周邊 M/R/Y 入口候選", 28, "個", "模型統計", "2026-09-10", "reconstruction/docs/GATE_B.md", "9 個標號可在官方圖辨識")
m(S, "捷運官方出口座標", 14, "點", "官方資料", "2026-09-10", "reconstruction/docs/SEARCH_AND_ESTIMATION.md",
  "台北車站 M1–M8、中山站 1–6；資料集更新日 2026-08-04")
m(S, "官方出口與 OSM 同名點差距 M2／M3／M6／M8", "10.32 / 10.10 / 13.41 / 18.39", "m", "檢查結果", "2026-09-10",
  "reconstruction/docs/SEARCH_AND_ESTIMATION.md", "來源差異，未判定哪個錯")
m(S, "中林試作坡道：東側", "37.953 m，9.485%", "", "估算", "2026-09-10", W, "落差 3.6 m；未含緩和段")
m(S, "中林試作坡道：西側", "45.018 m，7.997%", "", "估算", "2026-09-10", W)
m(S, "中林試作坡道：B1–B2", "36 m，10%", "", "估算", "2026-09-10", W)
m(S, "地下試作包絡", "200 × 24", "m", "估算", "2026-09-10", W, "不是中林停車場真實平面")
m(S, "分隔島設備圖面標示（中林＋林金）", 14, "個", "官方資料", "2026-09-10", "reconstruction/median_equipment/README.md",
  "各為進風 2、排風 2、水塔 2、發電機排煙 1；不等於 14 棟設備房，無實測尺寸")
m(S, "OSM 設備候選（道路 70 m 內）", 15, "筆", "模型統計", "2026-09-10", "reconstruction/median_equipment/README.md",
  "11 筆有輪廓、4 筆只有點")
m(S, "OSM 通風井改為估算外殼", 20, "處", "估算", "2026-09-11", "reconstruction/reports/MAPPED_VENT_PROGRESS.md",
  "46 個代理物件隱藏保留")

# ---- 建物 ----
S = "建物與街廓"
B = "reconstruction/checkpoints/block_facades_20260910/街廓立面報告.md"
for item, val, unit, ev, note in [
        ("近似街廓", 303, "個", "估算", "道路廊帶圍合，不是地籍界"),
        ("建物與建築分部", 3604, "筆", "模型統計", "含塔樓、裙樓分部，不是門牌或棟數"),
        ("第一排獨立輪廓", 1106, "個", "模型統計", ""),
        ("新納入街廓內建物／分部", 2498, "筆", "模型統計", ""),
        ("有立面構件的物件", 3397, "個", "估算", "其餘 207 個棚架／頂棚類"),
        ("立面模組實例", 628551, "組", "估算", "窗、門、實牆、陽台等；不是窗戶總數"),
        ("街廓地面、側街與人行道分區", 640, "個", "估算", ""),
        ("改用非住宅模板的建物（寺廟、學校、華山等）", 108, "筆", "估算", "")]:
    m(S, item, val, unit, ev, "2026-09-10", B, note)
m(S, "缺高度、以鄰近建物中位數估算", 581, "棟", "估算", "2026-09-10",
  "reconstruction/checkpoints/completion_20260910/WORKING_MODEL_README.md",
  "500 m 內最多 5 棟有高度建物的中位數；無資料時 13.2 m")
m(S, "美麗信花園酒店高度", 51.2, "m", "估算", "2026-09-12", "reconstruction/reports/WORKING_CHECKPOINT_20260912.md",
  "原 6.6 m 估算改正；不確定度約 6 m")
m(S, "南港展覽館二館高度", 46.05, "m", "官方資料", "2026-09-10", C, "建築師公布")
m(S, "京站複合開發高度", 69.95, "m", "官方資料", "2026-09-10", C, "不可套到整個商場底座")
m(S, "松山車站共構分棟高度", "81 / 84.8", "m", "官方資料", "2026-09-10", C, "分屬不同量體")
m(S, "華山通風建物（西／東）", "7.2±1.5 / 4.2±1.0", "m", "估算", "2026-09-12", "reconstruction/reports/PHOTO_EVIDENCE_0912.md",
  "依 2019-08 街景；範圍是假設，不是統計信賴區間")
m(S, "中崙站雨棚／服務棚", "5.6 / 4.4", "m", "估算", "2026-09-12", "reconstruction/reports/WORKING_CHECKPOINT_20260912.md",
  "取代原兩個 26.4 m 量體")

# ---- 全場景 ----
S = "全場景統計"
WC = "reconstruction/reports/WORKING_CHECKPOINT_20260912.md"
m(S, "可見物件（09-12 工作檔）", 21601, "個", "模型統計", "2026-09-12", "reconstruction/reports/current_completion_audit_0912.json")
m(S, "可見網格（09-12 工作檔）", 21445, "個", "模型統計", "2026-09-12", "reconstruction/reports/current_completion_audit_0912.json")
m(S, "地標替換新增構件", 3930, "個", "估算", "2026-09-12", WC)
m(S, "16 處替換的網格合計", 6494, "個", "估算", "2026-09-12", WC)
m(S, "使用中的 mesh datablock（09-10 驗證版）", 6317, "個", "模型統計", "2026-09-10", V)
m(S, "帶來源／假設／高度屬性的網格物件", 5636, "個", "模型統計", "2026-09-10", V, "已盤點，非來源真實性認證")
m(S, "布林修改器非流形共邊", 5, "條", "檢查結果", "2026-09-10", V, "道路 3、分隔島 2；未通過")
m(S, "完成版新增網格", 4954, "個", "估算", "2026-09-10", "reconstruction/checkpoints/completion_20260910/WORKING_MODEL_README.md")
m(S, "延後處理問題（嵌入 Blender 文字資料 CIVIC_DEFERRED_ISSUES.json）", 637, "筆", "檢查結果", "2026-09-10",
  "reconstruction/checkpoints/completion_20260910/all_deferred_issues.json")

# ---- 檢查 ----
S = "通行與淨空檢查"
m(S, "地下入口行走抽樣", "801 位置／20,025 射線／碰撞 0", "", "檢查結果", "2026-09-10", V,
  "19 個直梯入口＋Y26 B；人體包絡直徑 0.60 m、高 1.80 m；不是完整動線驗收")
m(S, "含頂板淨空抽樣", "117 路徑／6,669 點", "", "檢查結果", "2026-09-12", "reconstruction/reports/headroom_checkpoint_0912.json")
m(S, "淨空受阻路徑（主場景）", 15, "條", "檢查結果", "2026-09-12", "reconstruction/reports/headroom_checkpoint_0912.json",
  "主要在公中與地下街、敦延／延吉交會；另外未採用的公中比較版 9 條")
m(S, "最低樓板支撐缺失", 13, "點", "檢查結果", "2026-09-12", "reconstruction/reports/bottom_core_edge_conflicts.json", "兩個估算核心邊緣")
m(S, "樓梯開口封補", "16（11 洞＋5 缺口）", "處", "檢查結果", "2026-09-12", "reconstruction/reports/UNDERGROUND_PROGRESS_0912.md",
  "樓梯包絡取樣 1,296 點")
m(S, "B1 坡道開口護欄", "10 段／195 柱", "", "估算", "2026-09-12", "reconstruction/reports/PHOTO_EVIDENCE_0912.md",
  "975 個底板點都有樓板支撐；非錨定或法規認證")

# ---- 相機 ----
S = "相機與動畫"
m(S, "道路相機", 106, "支", "模型統計", "2026-09-10", C, "53 組南北配對、每 200 m；分析路徑約 10.316 km，末段 195.0465 m")
m(S, "坡道／地下相機", 22, "支", "模型統計", "2026-09-10", C)
m(S, "每 500 m 南北觀察相機", "22 組／44 台", "", "模型統計", "2026-09-10", "reconstruction/reports/cameras_500m/README.md",
  "0–10,000 m 共 21 站，加東端 10,395.046 m")
m(S, "動畫", "24 fps，第 1–2544 幀", "", "模型統計", "2026-09-12", "reconstruction/reports/current_completion_audit_0912.json",
  "由東向西，每 24 幀切換相機")
m(S, "仍有遮擋的道路視角", 5, "個", "檢查結果", "2026-09-12", "reconstruction/reports/full_corridor_review_0912.json")

# ---- 影像覆蓋 ----
S = "街景與影像覆蓋"
UB = "reconstruction/reports/underbridge_0922/coverage_checkpoint.json"
m(S, "09-10 道路站點街景查詢", "53 站全部無可用影像", "", "檢查結果", "2026-09-10", C, "只代表當時讀不到")
m(S, "NLSC PHOTO2 正射圖磚", 262, "張", "官方資料", "2026-09-10", C, "航測正射影像，不是衛星")
m(S, "橋下 100 m 條帶", 66, "條", "模型統計", "2026-09-22", UB, "依東距切分，不是里程")
m(S, "已使用全景", 79, "張", "檢查結果", "2026-09-22", UB)
m(S, "有相機觀測的條帶", 51, "條", "檢查結果", "2026-09-22", UB, "任何部分觀測 58 條")
m(S, "完全核實（可見性＋尺寸）的條帶", 0, "條", "檢查結果", "2026-09-22", UB)
m(S, "橋下候選物件（09-16）", 1217, "個", "模型統計", "2026-09-16", "reconstruction/reports/underbridge_0916/README.md")
m(S, "橋下估算量體網格（拓樸檢查）", 215, "個", "估算", "2026-09-22",
  "reconstruction/reports/underbridge_0922/mass_topology_checkpoint.json", "尺寸全部估算")

# ---- 關卡 ----
S = "檢查關卡"
for gate, status in [("A 範圍", "已由使用者確認"), ("B 座標與高程", "未通過"), ("C 地下與道路樣板", "未通過（技術檢查部分通過）"),
                     ("D 全段整合／動線", "未通過"), ("E 最終現況還原驗收", "未通過")]:
    m(S, gate, status, "", "檢查結果", "2026-09-10", V + "; reconstruction/docs/WORKSHEET.md")

with open(OUT, "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=list(R[0]))
    w.writeheader()
    w.writerows(R)
print(f"key_metrics.csv: {len(R)} rows")
