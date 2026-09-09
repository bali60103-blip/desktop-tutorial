# 市民大道一段周邊活動熱力圖(以台北開放資料為代理指標)

以台北市開放資料(捷運各站分時進出量、YouBike 站點)作為市民大道一段(大同區,環河北路
至中山北路一帶)方圓 2 公里內「人流活動熱度」的代理指標,產生逐小時熱力圖。

**這不是真正的人口流動資料** — 精細的手機信令人流資料屬電信業者商業資產,非公開資料。
詳見 [`data_sources.md`](data_sources.md) 了解資料來源與限制,包括本次開發環境因網路
政策無法連線 data.taipei、程式碼尚未以真實資料端對端驗證過的說明。

## 使用方式

```bash
pip install -r requirements.txt
cd src

# 1. 抓取範圍內捷運站的逐小時進出站資料(需要能連上 data.taipei 的網路環境)
python fetch_mrt_hourly.py

# 2.(選用)每小時執行一次,累積 YouBike 站點快照,可搭配 cron 或排程工作
python poll_youbike.py

# 3. 產生互動式 24 小時熱力圖(含時間滑桿)
python build_heatmap.py
# 輸出於 ../output/heatmap.html,用瀏覽器開啟即可
```

## 檔案結構

- `src/config.py` — 市民大道一段中心座標、半徑、捷運站座標表
- `src/stations.py` — 依 2km 半徑篩選範圍內捷運站
- `src/fetch_mrt_hourly.py` — 抓取 data.taipei 捷運分時進出量資料
- `src/poll_youbike.py` — 輪詢 YouBike 即時資料並累積快照
- `src/build_heatmap.py` — 產生逐小時 Leaflet 熱力圖(folium HeatMapWithTime)
- `src/fetch_road_network.py` — 從 OpenStreetMap Overpass API 抓市民大道真實路網座標(GeoJSON);這個 session 連不出去時,改成自己在 overpass-turbo.eu 查、Export 成 GeoJSON 後上傳
- `src/filter_road_segments.py` — 從 Overpass 匯出的原始檔案裡,篩掉巷弄/出入口匝道,只留下市民大道本體路型
- `src/build_road_overlay.py` — 依真實經緯度等比例投影,畫出市民大道真實路網圖(含格線、比例尺)
- `src/build_corridor_query.py` — 依真實路網算出貼著道路彎曲兩側 ±300m 的緩衝多邊形,產生 Overpass `poly` 查詢(給後續 POI 查詢用)
- `tools/boundary_comparison.html` — 南北分界指數工具(獨立 HTML)。六項為實測值、四項無資料留白且不計入指數;seed 由 `src/severance/build_boundary_rows.py` 產生
- `tools/boundary_overlay_map.html` — 拉直後的走廊剖圖,商家密度/建物量體高度/已標記連鎖門市/繞路係數四層皆為實測;圖層由 `src/severance/build_overlay_strip.py` 產生
- `tools/civic_blvd_severance.html` — 南北分隔分析系統(獨立 HTML,24 個可疊圖層 + 真實地理底圖)。
  **不在版控裡**(1.83 MB,資料內嵌才能離線單檔開啟):clone 之後跑 `sh src/severance/run_all.sh` 產生
- `data_sources.md` — 資料來源清單與限制說明

## 南北分隔假設檢驗(`src/severance/`)

檢驗「市民大道高架把台北切成南北兩半」。**結論成立**,但關鍵不是穿越點少,而是**路緣活動被推開**:
市民大道的路緣商業活動凹陷 **+67%**,而八德路、忠孝東路、南京東路、長安東路、民生東路
五條平行幹道**全部是負值**(活動被吸到路緣)。符號相反就是證據。

十項判準:7 項支持、1 項反證(產業組成差異未通過 placebo 檢定)、2 項不採用(斷頭路密度、
幾何穿越點計數皆未支持假設)。不利於假設的結果一併列在產出頁面上。

**不需要網路**——讀本機 `~/Downloads/taiwan-260908.osm.pbf`,不受 egress policy 影響。

```bash
pip install -r requirements.txt
cd src/severance
sh run_all.sh          # 12 個階段,依相依順序跑完,約 3 分鐘
```

只有基地模型變更時才需要重跑 Blender 匯出(在 Blender 裡跑,不是 python3):

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b "$HOME/Desktop/site model 市民大道new.blend"     --python src/severance/blender/export_site_model.py
```

各階段:

| 腳本 | 做什麼 |
|---|---|
| `extract_osm.py` | 從 .osm.pbf 裁切走廊範圍:37,005 way / 62,732 node / 60,723 面 |
| `build_axis.py` | 由 30 條高架橋面 way 重建 6,533 m 軸線(彎曲率 1.030) |
| `measure_permeability.py` | 幾何穿越點計數(+ 五條對照幹道) |
| `measure_detour.py` | **繞路係數**:116,736 節點人行網路圖上的最短路徑 |
| `measure_structure.py` | 斷頭路、行政界線覆蓋、縱貫線覆蓋 |
| `measure_industry.py` | 產業組成 + **placebo 對照**(這一項得出反證) |
| `measure_gradient.py` | **路緣活動凹陷**(決定性判準) |
| `register_blend_model.py` | 把 Blender 基地模型配準到 EPSG:3826 |
| `measure_blend_model.py` | 橋墩/護欄、建物量體、樹冠(判定不可用) |
| `build_verdict.py` | 證據表 |
| `build_bundle.py` / `build_overlay_tool.py` | 打包 + 組出互動系統 |
| `build_boundary_rows.py` / `build_overlay_strip.py` | 餵實測值給另外兩個工具 |

### 已知限制

- **樹冠資料不可用**:基地模型的 10,000 個樹冠是完全一致的佔位幾何,樹冠面積/體積沒有計算,也不報數字。
- **建物高度是推算值**:`building:levels` × 3.2 m,42.4% 落在 12.0 m 預設值。高度統計同時報「全部」與「排除預設值」。
- **連鎖品牌只有 16.2% 覆蓋率**:只能標「已知連鎖門市在哪」,不能算連鎖/獨立比例。
- **1 組取樣點無法計算**(里程 6,100 m):該處北側 90 m 內沒有已繪製的人行網路,標為資料缺口,未計為障礙。
- **分界指數不等於因果**:南北數值差得開只證明兩側不一樣;placebo 檢定顯示這在市中心是常態。
- 只涵蓋高架段 6,533 m;市民大道全段 13.6 km,六～八段無高架,不在假設範圍內。
