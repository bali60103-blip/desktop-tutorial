# 關卡 A 已確認；阶段01資料取得與階段02前置

使用者於本輪回覆「好」，確認全線為總範圍、先詳做高架及台北車站—中山地下街交會區。採用關卡A文件內第一排認定及地下範圍建議。新增停車場公中、塔城段列入清單；原六處清單不是全線完整清單。

本輪先備份 stage01_sources.py，再執行：

```sh
uv run --with osmium --with pypdfium2 --with pillow python reconstruction/scripts/stage01_sources.py --mode plans --output SOURCE_FOLDER
uv run --with osmium --with pypdfium2 --with pillow python reconstruction/scripts/stage01_sources.py --mode osm --pbf INPUT_PBF --output SOURCE_FOLDER
```

计划輸出：官方平面圖本地副本、頁面預覽、來源雜湊、全段具名市民大道道路、地下入口候選。導覽圖與無比例示意圖不直接轉成公尺幾何。OSM 入口不視為實測控制點；高程保持null。

進入關卡B前，需辨識可靠控制點及圖面方向、比例、非等比或分段排版。若尚不能對位，先交代缺口與改善方案，不假造地下樓層高度。
