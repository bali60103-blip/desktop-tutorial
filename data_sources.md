# 資料來源與限制說明

## 為什麼不是「真正的人口流動」資料

逐小時、精細到街廓範圍的人口移動熱力圖,實務上只有電信業者(中華電信/台灣大哥大/遠傳)
的手機信令聚合資料才做得到。這類資料屬於電信業者的商業資產,**不是公開資料**,通常需要
付費採購或透過公部門合作專案才能取得,一般開發環境無法直接存取。

本專案改用台北市開放資料中,可作為「活動熱度代理指標(proxy)」的資料集,涵蓋市民大道
一段(大同區,環河北路至中山北路一帶)方圓 2 公里內的捷運站與 YouBike 站點。**這些代理
指標反映的是「進出捷運站/借還單車的人次」,不是逐街廓的真實人流分布**,精細度和準確度都
遠低於真正的電信信令資料。

## 使用的資料集

| 資料集 | 提供單位 | 內容 | 連結 |
|---|---|---|---|
| 臺北捷運各站分時進出量統計OD | 臺北大眾捷運股份有限公司 / data.taipei | 各站逐小時進出站人次 | https://data.taipei/dataset/detail?id=63f31c7e-7fc3-418b-bd82-b95158755b4d |
| 臺北捷運各站進出人次 | 臺北大眾捷運股份有限公司 / data.taipei | 各站進出人次(輔助對照) | https://data.taipei/dataset/detail?id=178ebf06-0451-4ac1-bbba-c255ca1fdac6 |
| YouBike2.0臺北市公共自行車即時資訊 | 臺北市政府交通局 / data.gov.tw / data.taipei | 各站即時可借/可還車輛數(僅即時,無現成逐小時歷史資料,需自行每小時輪詢累積) | https://data.gov.tw/dataset/137993 |

範圍內納入計算的捷運站(依 `src/config.py` 的座標與 2km 半徑篩選):
台北車站、北門、中山、雙連、西門、善導寺、台大醫院、大橋頭、民權西路、小南門。

## 市民大道的真實路網幾何

前面的疊圖工具(`tools/boundary_overlay_map.html`)裡的市民大道是手畫的示意直線,不是
真實座標。要對照真實地區,`src/fetch_road_network.py` 改用 OpenStreetMap 的 Overpass API
抓市民大道(一段到七段)所有路段的實際經緯度線型:

| 資料集 | 提供單位 | 內容 | 連結 |
|---|---|---|---|
| OpenStreetMap way 幾何(`name~"^市民大道"`) | OpenStreetMap 貢獻者 / Overpass API | 市民大道各路段的真實節點座標 | https://overpass-api.de/api/interpreter(可先用 https://overpass-turbo.eu/ 預覽查詢) |

流程:`fetch_road_network.py` 抓回 `data/mingsheng_road.geojson`(真實座標的
GeoJSON),`build_road_overlay.py` 讀這個檔案、依真實經緯度等比例投影,畫出
`output/real_road_map.html`(含經緯度格線與比例尺)。**這張圖只畫路網本身**——商家密度、
連鎖品牌、建物樓齡、認知地圖邊界等圖層目前仍是示意資料,要疊上真實內容得各自找資料源
(例如商業登記開放資料、建物登記、或實際問卷)。

### 手動查詢 + 上傳,繞過這個 session 連不出去的問題

因為這個 session 連不上 Overpass API(見下一節),實際可行的路徑是:你自己在
[overpass-turbo.eu](https://overpass-turbo.eu/) 貼查詢、Export → GeoJSON 下載,再把檔案
直接上傳到對話裡。已驗證過一次:2026-09-09 這樣抓到 `name~"^市民大道"` 的完整匯出(93
筆 way,環河北路到松山車站一帶),流程是:

1. `src/filter_road_segments.py <上傳的原始匯出.geojson>` —— 只留下高架道路本體與各段
   （一~五段)的路型,排除巷弄側支與出入口匝道(這些也會被 `name~"^市民大道"` 誤抓進來,
   但不是道路本身),輸出到 `data/mingsheng_road.geojson`。
2. `src/build_road_overlay.py` —— 照前面說的畫出 `output/real_road_map.html`。
3. 需要「貼著真實路線兩側街廓」的 POI 查詢時,`src/build_corridor_query.py` 會用
   `市民大道高架道路`(全線唯一連續的實體結構)的真實節點座標,依經度分箱平滑出中心線,
   算出左右 ±300m 的緩衝多邊形,輸出成 Overpass 的 `poly` 查詢(`output/corridor_query.txt`),
   讓查詢範圍全程貼著道路彎曲的實際路線,而不是一個矩形框。**已知缺口**:高架道路本體只到
   塔悠路一帶,離松山車站還有約 700 公尺;那段的「市民大道五段」在 OSM 上是幾段不相連的
   路型片段,用經度分箱平均硬接會產生自我交叉的錯誤多邊形(已經試過、確認有問題後改回不接),
   要接上那 700 公尺需要真正的線段合併(如 `shapely.ops.linemerge`),目前沒有為了這一小段
   加這個依賴——那段如果要涵蓋,建議另外用一個簡單的矩形框查詢就好。

## 這次工作階段(session)的一項技術限制

執行這次任務的沙盒環境,其對外網路政策(egress policy)直接封鎖了 `data.taipei` 與
YouBike 資料所在的 `tcgbusfs.blob.core.windows.net`(以 `curl` 直接測試,兩者都收到
`CONNECT tunnel failed, response 403`,屬機構網路政策封鎖,並非可繞過的技術問題)。
同一個政策也擋掉了 `overpass-api.de` 與 `nominatim.openstreetmap.org`(同樣是
`CONNECT tunnel failed, response 403`),所以 `fetch_road_network.py` 也沒辦法在這個
session 裡連上 Overpass API 抓市民大道的真實路網座標。

**這代表我在這個 session 裡沒有辦法實際抓到真實資料、也沒辦法產生真正基於實際數字的
24 小時熱力圖畫面或真實路網疊圖。** `src/` 底下的抓取與繪圖程式已經寫好並用假資料做過煙霧測試
(smoke test)確認邏輯正確,但你需要在**沒有被封鎖這些網域的環境**(例如你自己的
電腦、或允許外部網路的 GitHub Actions)執行 `fetch_mrt_hourly.py` / `fetch_road_network.py`
才能拿到真正的數字與座標。

另外,`fetch_mrt_hourly.py` 裡的 API 資源 ID(`RESOURCE_ID`)與欄位名稱對照表
(`COLUMN_MAP`)是依照 data.taipei 一般的 API 慣例與資料集頁面上看到的中文欄位名稱猜測
撰寫,**沒有辦法從這個 session 連線驗證**。實際執行前,請先打開上表的資料集連結,點選
頁面上的「API」分頁確認真正的 resource id 與回傳格式,再對照修改。
