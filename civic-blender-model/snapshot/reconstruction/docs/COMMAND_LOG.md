# 工作指令與執行記錄

使用者：開始執行工作表；在檢查關口提出模型疑慮、可能錯誤位置與改善方案；寫指令過程均備份 GitHub。

2026-09-09：唯讀檢查桌面工作模型、現有 repo remote 與 GitHub 權限。確定備份目標 devteam-del/civic；舊本機 remote intern824/civic 未更改。建立 reconstruction/stage-00-scope-audit 分支。

新增 scripts/audit_scope.py、工作表、關卡A問題表、地下來源表；保存前一版腳本 archive。先提交這批指令，再执行audit_scope。此階段不修改 Blender 幾何。

待執行命令（路徑以使用者本地來源參數代入）：

```sh
python3 reconstruction/scripts/audit_scope.py --model-root MODEL_FOLDER --corridor CORRIDOR_GEOJSON --output reconstruction/reports
```

首批遠端備份：c6a607adc69a58faa5a2116e64461147e83996f8。備份完成後執行 audit_scope.py 成功：93 features；WGS84 bounds 121.5037481,25.0439955,121.5658228,25.050951。產生範圍圖、資產 SHA256 與檢查JSON。py_compile 因沙盒外快取寫入受限失敗；改用不寫檔 ast.parse 語法檢查通過。SVG XML檢查通過。Blender 幾何未修改。關卡A範圍選項已送使用者確認。

本輪使用者確認關卡A。脚本各批執行前已提交 GitHub。stage01_sources取得6份PDF(33頁)、全段具名OSM路線與入口候選。Python憑證驗證與市府憑證不相容，改用保持TLS驗證的系統curl並成功；未使用insecure。prepare_control_review產生136條路線、28入口候選。Blender初次匯入因OSM編號超過整數範圍中止，已提交字串ID修正和可重建圖層處理後成功重跑；原始與中止版本皆保留。最终另存新控制檢查副本，未新增地下結構。已以瀏覽器檢视SVG並讀取代表原圖。關卡B不放行尺度與高程依賴的詳模。
