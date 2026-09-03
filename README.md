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
- `data_sources.md` — 資料來源清單與限制說明
