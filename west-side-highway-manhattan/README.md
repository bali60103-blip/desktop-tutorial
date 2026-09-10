# West Side Highway 前後平面圖對比

單一自足的互動式 HTML 頁面，以平面圖比較曼哈頓 Meatpacking District(Gansevoort St ／
Little West 12th St 一帶)在 Miller Highway 高架時期(1929–1973)與現今 Route 9A 平面大道
＋Hudson River Park(2001年起,含 Little Island、Gansevoort Peninsula)的差異。

打開方式：直接用瀏覽器開啟 [`index.html`](index.html)，不需安裝、不依賴外部 CDN。

## 這一頁與另外兩頁的差異

三個案例代表都市高速公路處理的三種不同路徑：

| | 日本橋 | Cross-Bronx | West Side Highway |
|---|---|---|---|
| 處理方式 | 地下化(遷入新隧道) | 加蓋(公路原地保留,上方覆土) | 拆除(改為平面道路) |
| 現況階段 | 已核准動工,2035/2040目標年度 | 願景研究階段,無官方時程 | **已完成**(1989拆除,2001大道完工,2023最新公園開放) |

這一頁的「前後」是**已經發生的歷史事實**,不是規劃願景,所以時間軸沒有「非定案」但書,
可以放心當作已完成案例參考。

## 功能

同系列互動邏輯：高架時期／現況切換、左右拉桿比對、圖層核取方塊(知名地標／水岸公園碼頭／
親水步道與植栽／文字標籤),狀態即時同步到網址參數(`state`／`landmarks`／`piers`／
`riverwalk`／`labels`／`compare`／`pos`)。下方附時間軸,涵蓋1929通車、1973年12月15日
崩塌、Westway方案破局、1989拆除、2001大道完工、2021 Little Island、2023 Gansevoort
Peninsula 開幕等節點。

## 資料限制

這次工作環境的對外網路政策封鎖了 OpenStreetMap、Google Maps、Wikipedia 等地圖資料源
(`curl`／`WebFetch` 皆收到 403/EGRESS_BLOCKED),因此**無法取得實測建物輪廓或地圖圖磚**。
街廓、建物量體、道路與水岸線形是依網路搜尋取得的百科全書條目與媒體報導文字內容(見頁尾
連結)手繪重建的示意圖,細節已簡化,非測量成果。
