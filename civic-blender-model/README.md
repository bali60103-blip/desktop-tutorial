# 市民大道 Blender 模型資料彙整

這個資料夾把散在 GitHub 各處、與市民大道 Blender 模型有關的資料集中在一起：模型版本、座標配準、構件數量、檢查結果、未解問題和引用來源。

- **資料來源**：[devteam-del/civic](https://github.com/devteam-del/civic) commit `f7dd17c`（2026-09-22）的 `reconstruction/` 全部檔案，以及 `src/` 裡和 Blender 有關的程式。也對照了本 repo 的 `claude/minsheng-road-division-verify-fio18t` 分支（civic 的前身），內容是同一批程式的舊版。
- **數字都是從已提交的報告抄出來的**，每個數字都標明出處檔案。這次沒有打開任何 `.blend` 檔。
- **不包含**：`city-analysis-comparison` 的 `render_models.py` 也是 Blender 腳本，但它畫的是日本橋、Cross-Bronx、West Side 三個國外案例，不是市民大道模型，所以沒有收進來。

## 先看這裡：GitHub 上沒有的東西

1. **模型本體不在任何 GitHub repo 裡。** 所有 `.blend` 都只存在原本那台電腦。報告裡記錄的位置是 `~/Desktop/site model 市民大道new.blend` 和 `/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/…`。
2. **最重要的幾個版本沒有雜湊值。** 106 個版本名裡有 74 個記錄了 SHA256。但原始模型 `site model 市民大道new.blend`，以及 09-12 之後的所有工作檔，都沒有記錄。這些工作檔包括 `CIVIC_FULL_CORRIDOR_WORKING_20260912`、`CIVIC_UNDERBRIDGE_WORKING_20260916`、`BEFORE_SPAN_HEIGHT_MARKERS_20260922`。所以無法用 GitHub 上的資料確認，本機那份檔案就是報告描述的那一版。
3. **原始模型的量測結果沒有存檔。** `src/measure_blend_model.py` 會產生 `data/processed/h_blend.json`（橋墩組數、柱距、橋面面積、護欄長度等），但這個資料夾設定成不進版控。GitHub 上只剩 README 和 CLAUDE.md 引用的幾個數字。
4. **其他留在本機的檔案**（報告自己註明）：渲染圖、街景截圖、照片、`span_height_audit.json` 完整逐點檔（約 3.8 MB）、每站 CSV、各批次的網格載荷。

建議下次在那台電腦上補兩件事：替上面幾個 `.blend` 算 SHA256 寫進清冊，並把 `h_blend.json` 存一份到 GitHub。

## 兩套座標配準相差約 5.2 公尺

模型裡的座標都要加上一個平移量，才會落在 TWD97（EPSG:3826）上。兩組工作各算了一次：

| | 重建工作（reconstruction） | 南北分隔分析（src） |
|---|---|---|
| 方法 | 用建物輪廓中心對 OSM 建物，做相似轉換 | 用模型內 `OSM_Major_Roads` 點雲做最近鄰，只解平移 |
| 平移後原點 X | 301,495.61 | 301,499.60 |
| 平移後原點 Y | 2,770,459.51 | 2,770,462.78 |
| 比例／旋轉 | 0.999998／−0.00008° | 驗證值 0.9998／+0.07° |
| 誤差描述 | 保留 1,062 組檢核，中位數 0.01 m，P90 0.51 m | — |

兩邊的建物分量都是 19,592 個，應該是同一個原始模型。平移量差 dx = 3.99 m、dy = 3.27 m，合計約 5.2 m。兩者都只是「對齊 OSM」，不是測量控制點。這裡不判斷哪一套比較準，但跨兩組資料疊圖時要先統一用哪一套。詳見 `data/registration_comparison.json`。

## 模型怎麼演變

| 日期 | 版本 | 內容 |
|---|---|---|
| 09-09 以前 | `site model 市民大道new.blend` | 使用者原始基地模型：橋墩、護欄、建物量體、行道樹 |
| 09-09 | `00_original_live_snapshot` → `01_civic_georeferenced_rebuild` | 快照原始模型，配準到 EPSG:3826，整理成 13 個集合 |
| 09-09～09-10 | `02_control_review`…`GROUND_*`、`STAGE45_*`、`DETAIL_01` | 官方控制點、地面全八段、中林地下試作、柱帽與支承 |
| 09-10 | `CIVIC_VALIDATION_REPAIRED`、`CIVIC_FULL_WORKING_PASS`、`CIVIC_303_BLOCKS_FACADES_WORKING` | 驗證修補、全段補建（停車場、地下街、第一排建物）、303 個街廓與立面 |
| 09-10～09-11 | `CIVIC_CALIBRATION_*`、`CIVIC_PHOTO_CALIBRATION_20260911` | 正射影像校準、相機重排、通風井 |
| 09-12 | `CIVIC_FULL_CORRIDOR_WORKING_20260912` | 全段整合工作檔：21,601 個可見物件 |
| 09-14 | `CIVIC_PRIORITY_A_WORKING_20260914` | 華山、新生匝道等優先節點 |
| 09-16 | `CIVIC_UNDERBRIDGE_WORKING_20260916` | 橋下空間盤點的基準 |
| 09-22 | （在 09-16 工作檔上繼續） | 橋下設備、植栽量體；柱間淨高檢查 |

完整清單見 `data/model_versions.csv`，含操作前快照、檔案大小，以及每個雜湊記在哪個報告。

## 模型內容（重點數字）

完整 115 項見 `data/key_metrics.csv`。每列都標有「性質」：官方資料、模型統計、估算、使用者選定、佔位資料、檢查結果。

| 部分 | 重點 |
|---|---|
| 地面層 | 一至八段；152 筆官方道路面（2014–2016）、375 筆官方人行道、163 個穿越點、208 處**估算**路緣坡道 |
| 高架 | 241 個柱位（**0 個是測量位置**）、130 組柱帽、30 條橋面；7 組柱位落在分隔島外的衝突仍未解 |
| 柱間淨高（09-22） | 116 個候選跨段，34 跨量不到；模型淨高約 5.42–5.60 m，但橋面一律設在約 8 m，**不能當現場數字** |
| 地下 | 8 段停車場、B1／B2 = −3.6／−7.2 m（**使用者選定假設**）、地下街淨高 2.8 m（假設）、1,919 個車位線構件（不是車位數） |
| 建物 | 303 個近似街廓、3,604 筆建物與分部、第一排 1,106 個；581 棟缺高度，用鄰近建物中位數估算 |
| 全場景 | 21,601 個可見物件、21,445 個可見網格（09-12） |
| 相機 | 106 支道路相機（每 200 m 南北各一）、22 支坡道／地下相機、24 fps 動畫 2,544 幀 |
| 橋下（09-22） | 66 條 100 m 條帶、79 張全景、0 條完全核實；215 個估算量體網格 |
| 官方對照 | D028 市民大道高架橋主橋：總長 5,802.5 m、160 孔、淨寬 18–28.5 m |

## 不能當成實測的資料

- **行道樹**：原始模型的 10,000 個樹冠完全一樣（3.00 × 2.60 × 3.00 m），只有位置能用。
- **建物高度**：原始模型用樓層數 × 3.2 m 推算，42.4% 剛好是 12.0 m 預設值。重建版的立面也全是估算。
- **護欄 1.1 m 和隔音牆 3.0 m**：其實是同一段幾何的兩種高度，不是兩個實測物件。
- **高程**：地面 Z = 0、橋面約 8 m、B1／B2 = −3.6／−7.2 m 都是假設，沒有測量高程基準。
- **柱位、設備、匝道**：位置和尺寸都是估算，報告一再註明「不可描述為已測量」。

## 檢查關卡與未解問題

| 關卡 | 狀態 |
|---|---|
| A 範圍 | 使用者已確認 |
| B 座標與高程 | 未通過 |
| C 地下與道路樣板 | 未通過（技術檢查部分通過） |
| D 全段整合／動線 | 未通過 |
| E 最終現況還原驗收 | 未通過 |

`data/open_issues.csv` 整理了 767 筆未解問題，來源有四處：09-10 的 637 筆延後問題、09-12 的淨空與樓板檢查、09-22 的橋下與跨段檢查。

| 類型 | 筆數 |
|---|---:|
| 建物高度未核實 | 581 |
| 跨距超過 60 m（需查漏柱或誤配） | 69 |
| 柱位歸屬哪條橋面不明 | 19 |
| 淨空受阻路徑 | 15 |
| 設備位置與尺寸未核實 | 14 |
| 入口方向與地面開挖待處理 | 13 |
| 沒有淨高量測的橋面路徑 | 13 |
| 停車場配置全為估算 | 8 |
| 跨段端點待判讀 | 8 |
| 柱位衝突 | 7 |
| 其他（重疊、支承、高程基準、非流形等） | 20 |

## 檔案說明

| 檔案 | 內容 |
|---|---|
| `data/key_metrics.csv` | 115 項重點數字，附性質、日期、出處 |
| `data/model_versions.csv` | 106 個 `.blend` 版本：時間、SHA256、大小、記錄在哪 |
| `data/open_issues.csv` | 767 筆未解問題，附模型內局部座標 |
| `data/registration_comparison.json` | 兩套座標配準並列與差值 |
| `data/sources_cited.csv` | 報告引用過的 143 個網址（官方資料、街景、文獻） |
| `data/file_index.csv` | 快照內 583 個檔案的大小、最後修改的 commit 與日期 |
| `data/build_stats.json` | 以上各表的統計 |
| `snapshot/` | civic `f7dd17c` 的原始檔複本，目錄結構不變；`SNAPSHOT.json` 有每個檔案的 SHA256 |
| `scripts/` | 產生以上檔案的程式 |

CSV 都存成 UTF-8（含 BOM），Excel 可以直接開。出處路徑都相對於 civic repo，也就是相對於這裡的 `snapshot/`。唯一例外是 civic 的 `CLAUDE.md`，在快照裡改名為 `CLAUDE.civic.md`，免得被當成這個資料夾的 Claude 指示。

## 重新產生

civic 更新後，可以重新產生一次：

```bash
git clone https://github.com/devteam-del/civic /path/to/civic
python3 civic-blender-model/scripts/build_data_package.py /path/to/civic
python3 civic-blender-model/scripts/key_metrics.py
```

`build_data_package.py` 會自動從 civic 重抓版本、問題、來源、索引和快照。`key_metrics.py` 的數字是人工從報告文字抄錄的，civic 有新報告時要手動更新。
