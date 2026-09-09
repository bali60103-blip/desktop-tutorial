# CLAUDE.md

給任何在這個 repo 工作的 Claude session 看的說明。**開工前先讀 `.claude/progress/` 底下所有檔案**，那是各個 session 的工作紀錄。

## 專案是什麼

市民大道一段（大同區，環河北路至中山北路一帶）周邊的**活動熱度分析**，用台北市開放資料當代理指標。

三條主線：

1. **逐小時活動熱力圖** — 捷運分時進出量 + YouBike 站點，方圓 2km，輸出 `output/heatmap.html`
2. **真實路網疊圖與走廊查詢** — 從 OSM 抓市民大道實際線型，算出貼著道路彎曲的 ±300m 緩衝多邊形，產生 Overpass `poly` 查詢
3. **南北分隔假設檢驗**（`src/severance/`）— 十項可查證量測 + 五條平行幹道對照，判定市民大道是否真的造成南北分隔。結論：**成立**，7 項支持、1 項反證、2 項不採用。輸出 `tools/civic_blvd_severance.html`

   注意這條線的**空間範圍與另外兩條不同**：熱力圖與走廊查詢限於市民大道**一段**（2km 半徑），分隔檢驗涵蓋**整段 6,533 m 高架**（忠孝橋／環河北路→基隆路一段），因為障礙效應是高架結構的性質，不是某一段的性質。市民大道作為街道全長 13.6 km，但六～八段沒有高架，不在假設範圍內。

細節看 `README.md`（使用方式、檔案結構）與 `data_sources.md`（資料來源、限制）。

## 最重要的前提

**這不是真正的人口流動資料。** 精細的手機信令人流屬電信業者商業資產，非公開。目前用的是「進出捷運站／借還單車人次」當 proxy，精細度遠低於信令資料。任何產出的說明都必須保留這個限制，不要寫成「真實人流」。

## 已知缺口（別重複踩）

- **雲端 session 連不出去**：`data.taipei`、`tcgbusfs.blob.core.windows.net`、`overpass-api.de`、`nominatim.openstreetmap.org` 全部被 egress policy 擋（`CONNECT tunnel failed, response 403`）。這是機構網路政策，不是可繞過的技術問題。需要真實資料時：在本機跑，或請使用者自己在 overpass-turbo.eu 查完 Export GeoJSON 上傳。
  - **`src/severance/` 這條線不受影響**：它讀本機的 `~/Downloads/taiwan-260908.osm.pbf`（pyosmium），完全不連網就能跑完整條 pipeline。如果熱力圖那條線之後也需要離網跑，同一份 pbf 就能供應路網與 POI。
- **`fetch_mrt_hourly.py` 的 `RESOURCE_ID` 與 `COLUMN_MAP` 是猜的**，沒有連線驗證過。實際跑之前要先打開 data.taipei 資料集頁的「API」分頁對照。
- **走廊查詢在松山車站方向缺約 700 公尺**：高架道路本體只到塔悠路。那段「市民大道五段」在 OSM 上是不相連的片段，用經度分箱平均硬接會產生自我交叉的多邊形（已試過、確認有問題後改回不接）。
  - **原因已查明，而且不是 linemerge 能解決的**：`src/severance/build_axis.py` 診斷出在光復南路一帶（東向 306,800–307,400），平面的「市民大道五段」與高架橋面**真的分岔到相距約 300 公尺**（五段北偏）。所以把兩者混在一起做分箱平均，得到的中線在地面上根本不存在——自我交叉是這個的症狀，不是插值精度問題。
  - **可用的解法**：只取高架橋面的 way（`name=市民大道高架道路`、`highway=trunk`、`bridge=yes`），20 m 分箱取中位數，剔除偏離 9 箱滾動中位數 60 m 以上的箱，再 5 箱移動平均。得到 6,533 m、彎曲率 1.030 的乾淨中線，**不需要 `shapely.ops.linemerge`**。走廊查詢若要補那 700 公尺，照這個方法重建軸線即可。
- ~~疊圖工具裡的商家密度、連鎖品牌、建物樓齡、認知地圖邊界目前都還是示意資料~~ **已處理**（2026-09-09）。兩個工具的示意資料都換成實測值，換不了的明確留白：
  - `tools/boundary_comparison.html` — 六項實測（商家密度、路口密度、貼線與走廊建物高度、停車與綠地佔比），四項留白（連鎖占比、建物樓齡、騎樓一致度、認知地圖）。留白列顯示「待補資料 · 不計入指數」且**不納入分界指數平均**。seed 由 `src/severance/build_boundary_rows.py` 產生。
  - `tools/boundary_overlay_map.html` — 圖層由 `src/severance/build_overlay_strip.py` 產生。**建物樓齡層已換成建物量體高度**（樓齡需要執照年份資料集，沒有）；**認知地圖層留空且預設關閉**。
  - **連鎖品牌只有 16.2% 的商家 POI 帶 `brand` tag**，所以那一層只標「已知連鎖門市在哪」，不能拿來算連鎖／獨立比例——沒有 tag 不代表是獨立店。
- **`boundary_comparison.html` 的分界指數不能單獨當證據**：它是南北相對差異的平均，而 `measure_industry.py` 的 placebo 檢定顯示，偏移 ±300／±450 m 的假想線（整條都在同一側）分歧度是 0.145–0.263，真實軸線 0.213 落在區間內。「兩側不一樣」在市中心是常態。真正區分市民大道與五條平行幹道的是**路緣活動凹陷**（市民大道 +67%，對照組全為負）與**繞路成本**（多走 209 m vs 145–173 m）。
- **基地模型（`~/Desktop/site model 市民大道new.blend`）有兩處佔位資料，別當實測用**：
  - 10,000 個樹冠網格是**完全一致的佔位幾何**（每個 3.00 × 2.60 × 3.00 m，各維度標準差 < 1e-4）→ 樹冠面積／體積不可計算。可用的只有樹木位置。
  - 建物高度是 `building:levels` × 3.2 m，**42.4% 剛好落在 12.0 m 預設值** → 高度統計要同時報「全部」與「排除預設值」。兩側缺值率相近（北 30.4%、南 29.7%）。
  - 護欄（1.1 m）與隔音牆（3.0 m）是同一段幾何的兩個高度版本，不是兩個實測物件。

## 分支

- `main` — 已合併 PR #1
- `claude/minsheng-road-division-verify-fio18t` — 目前主要工作分支（路網篩選 + 走廊查詢）
- `claude/citizen-road-population-heatmap-bsvgw7` — 熱力圖與真實路面底圖
- `claude/base-model-availability-y6iw63` — 建築量體／地標商業活動分析
- `design-class` — 只有 initial commit，尚未推送

## 兩個 session 併行工作的規矩

這個 repo 同時被兩邊使用，**動的是磁碟上同一份檔案**：

- `cowork-cloud` — 雲端 Cowork session，透過連接的資料夾操作
- `claude-code-local` — Mac 上的 Claude Code

規矩：

1. **開工前先讀 `.claude/progress/*.md`**，看另一邊做到哪。
2. **不要同時改同一個檔案。** 要嘛分工不同 branch，要嘛同一時間只有一邊在動。
3. **做完一段就記錄**：

   ```sh
   CLAUDE_SESSION_LABEL=<你的標籤> sh tools/save_progress.sh "這輪做了什麼"
   ```

   Claude Code 這邊已經由 `.claude/settings.json` 的 Stop / SessionEnd hook 自動執行，不用手動記得。
4. 每個 session 寫**自己的**進度檔，所以兩邊同時寫不會衝突。git 狀態沒變又沒帶筆記時腳本會自動跳過，不會灌一堆空條目。

## 推送限制

雲端 session 這邊**沒有 GitHub 憑證**，`git fetch` / `git push` 會失敗（`could not read Username for 'https://github.com'`）。雲端這邊只能 commit 到本地；**push 要在 Mac 上做**（GitHub Desktop 或已登入的 Claude Code）。

## 待整理

- `claude code/` — 只有一個空的 `repo` 目錄，看起來是誤建的
- `dedede/` — 整個專案的另一份拷貝（README、src、data、data_sources.md），像是某次操作把 repo 複製進自己裡面

兩者都還沒進版控，處置方式待使用者確認。

### 設計論述 PDF 的三個潛力節點，與實測繞路的落差

`市民高架都市空間活化論述_1150610.pdf` p10 用路口名界定 A/B/C 三區。把那些路口名
用重建的軸線換算成里程（`config.PDF_ZONES`）之後，跟實測繞路係數對照：

| 區 | 範圍 | 里程 | 區內繞路平均 | 最差 | >2x |
|---|---|---|---|---|---|
| A 街頭競演 | 林森北—新生高架 | 2,040–2,740 m | 1.64x | 2.45x | 14% |
| B 藝文通學 | 建國高架—復興南北 | 3,398–4,095 m | 1.77x | 2.33x | 29% |
| C 夜間漫步 | 復興南北—敦化南北 | 4,095–4,641 m | 1.47x | 2.00x | 0% |
| — | 三區之外 | — | 1.72x | **3.93x** | 28% |

**三區沒有對準最嚴重的斷點。** 最差的三個取樣點（里程 6,000 / 6,200 / 6,300 m，
2.84–3.93x，最多多走 880 m）全部落在**三區以東**、基隆路那一段，論述完全沒有處理。
而 C 區（夜間漫步）反而是實測**最不分隔**的一段（平均 1.47x、沒有任何點超過 2x），
比走廊平均還好。這不代表 C 區的提案沒有價值——夜間活動的理由跟穿越阻隔是兩件事——
但如果要用「縫合南北」當論述主軸，A/B/C 的位置需要重新檢討，或者把基隆路端補進來。

### 已定案（2026-09-09，使用者確認）

- **`tools/civic_blvd_severance.html` 不進版控**（1.83 MB，資料內嵌才能離線單檔開啟）。已加進 `.gitignore`；clone 之後跑 `sh src/severance/run_all.sh` 產生。`data/raw/`、`data/processed/`、`data/blend/`、`*.npy` 同理，都是可重生的中間產物。
- **軸線東端是基隆路一段，不是光復南路**（光復南路在里程 5,188 m，距東端還有 1.3 km）。這點一開始標錯了，2026-09-09 已修正 CLAUDE.md、README、兩個工具的端點標籤與 `config.py`。
- **走廊剖圖維持全段 6,533 m**（不縮回一段）。`src/severance/build_overlay_strip.py` 的 `STRIP_S_MAX = None`。若日後要縮回一段，設成 `1700` 即可。
- **`.claude/`、`claude code/`、`dedede/`、`tools/save_progress.sh` 仍未進版控**，我這輪沒有動它們（`.claude/` 與 `save_progress.sh` 是雙 session 協定的基礎設施，屬於另一邊的範圍；`claude code/` 與 `dedede/` 的處置還沒定）。
