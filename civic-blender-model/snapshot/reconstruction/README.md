# 市民大道地上地下還原

本目錄為使用者新增的地上地下重建工作；既有 severance-pipeline 保留。

- docs/WORKSHEET.md：階段、關卡、備份規則。
- docs/GATE_A.md：範圍提案、模型疑慮、改善方案。
- docs/SOURCES_UNDERGROUND.md：地下資料初查。
- scripts/audit_scope.py：唯讀範圍盤點，使用標準函式庫。
- archive/：之前工作版的實際腳本與來源記錄；包含當時本機路徑，不可直接當成可攜建置程式重跑。
- reports/：可重查的檢查產物與模型檔雜湊；不代表 .blend 已備份到 GitHub。

執行：`python3 reconstruction/scripts/audit_scope.py --model-root MODEL_FOLDER --corridor CORRIDOR_GEOJSON --output reconstruction/reports`

新建模應在範圍關卡確認後進行。每個階段都保留未知，不以假設模型計算真實阻隔。
