# 都市高速公路・前後3D量體對比

用 [three.js](https://threejs.org/) 打造的互動式 3D 檢視器，把三個「都市高速公路前後對比」
案例（日本橋首都高地下化、Cross-Bronx Expressway、West Side Highway）的建物與公路量體，從
2D平面圖延伸成可自由旋轉、縮放的 3D 示意模型 —— 拆除高架後「天空重新打開」的效果，3D比2D
平面圖更直觀。

打開方式：**這一頁不能直接雙擊 `index.html` 開啟**（瀏覽器基於安全性，會擋掉 `file://`
底下的 ES module／CORS 請求）。請在此資料夾內啟動一個本機伺服器，例如：

```bash
cd 3d-expressway-comparisons
python3 -m http.server 8000
# 瀏覽器開 http://localhost:8000/
```

或任何等效的靜態伺服器（`npx serve`、VS Code Live Server…）都可以。

## 操作方式

- 上方切換三個案例（日本橋／Cross-Bronx／West Side Highway），各自套用自己的 Before／After
  量體與預設鏡頭視角。
- Before／After 切換各案例的高速公路狀態（日本橋：高架↔拆除+地下化指示；Cross-Bronx：
  路堑/高架本身共通,只切換加蓋覆土段與自行車連結;West Side Highway：高架↔拆除+新公園碼頭)。
- 滑鼠拖曳＝旋轉、滾輪＝縮放、右鍵拖曳＝平移（three.js `OrbitControls`），「重置視角」回到
  該案例的預設鏡頭。
- 街廓量體／標籤兩個核取方塊可個別開關。

## 技術與檔案結構

- `index.html` — 頁面外殼（工具列／圖例／說明文字），透過 `<script src="./bundle.min.js">`
  載入打包好的 3D 邏輯（純古典 script，不用 ES module，所以本機用一般靜態伺服器即可，不需要
  額外設定 MIME type 或 CORS 標頭）。
- `src/main.js` — 可讀的原始碼（3D場景建構邏輯＋三案例的座標資料，資料本身沿用對應 2D
  對比頁的座標，直接把2D的x/y當作3D的x/z讀取,再依建物量體給定高度)。
- `bundle.min.js` — 用 [esbuild](https://esbuild.github.io/) 把 `src/main.js` 連同
  `three`（v0.169）與其 `OrbitControls` addon 一起打包壓縮出的單一檔案，**已包含完整
  three.js 函式庫本身**，瀏覽器端不需要另外連線任何 CDN。

重新產生 `bundle.min.js`（修改 `src/main.js` 後）：

```bash
npm install --no-save esbuild@0.24 three@0.169
npx esbuild src/main.js --bundle --format=iife --target=es2019 --minify --outfile=bundle.min.js
```

## 建物高度與量體是怎麼來的

3D建物量體並非測量或BIM模型，而是把對應 2D 對比頁裡「示意建物輪廓」直接往上擠出
（extrude）一個概略高度：知名地標（三井大樓、COREDO日本橋等）用一般認知中的大致樓層規模
估計；Tokiwabashi Tower（TOKYO TORCH）取其公開規劃樓高約390m 這類確實查證過的數字；其餘
一般街廓建物與再開發量體高度純屬示意，用來傳達「高架拆除後天空重新打開」的空間感，不是
精確樓高。三個案例各自的街廓／道路／河道座標資料，查核方式與資料來源限制，請見各自的 2D
對比頁 README：

- [`../nihonbashi-shutoko-undergrounding/`](../nihonbashi-shutoko-undergrounding/)
- [`../cross-bronx-expressway-reimagined/`](../cross-bronx-expressway-reimagined/)
- [`../west-side-highway-manhattan/`](../west-side-highway-manhattan/)
