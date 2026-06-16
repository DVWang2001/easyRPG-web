# 自訂 EasyRPG 網頁播放器（自訂取名字表）

`players/custom/` 的 `index.html/js/wasm` 是「改過繁中取名字表」的 EasyRPG Player，
由本資料夾的 Docker 流程建出。GUI 的「編輯取名字表 → 重建自訂播放器」會自動呼叫
（見 `customplayer.py`）。`players/custom/` 不進版控（每台機器自行重建）。

## 為什麼要自建
取名選字格的字寫死在 EasyRPG Player 原始碼（`src/window_keyboard.cpp` 的
Trad. Chinese 1/2 兩表），遊戲檔/打包工具都改不了 → 只能改原始碼後重編 WASM。

## 一次性環境建置（之後改字重編只要幾分鐘）

需求：**Docker Desktop（執行中）**。在 repo 根目錄執行：

```bash
# 1) 建建置用 image（debian:12-slim + 工具鏈，含新版 meson）
docker build -t easyrpg-emcc -f players/build/Dockerfile players/build

# 2) 起常駐容器（具名 volume 放建置快取；scripts 唯讀掛載）
docker rm -f ezbuild 2>/dev/null
docker run -d --name ezbuild -v ezbuild_work:/work \
  -v "<repo 絕對路徑>/players/build:/scripts:ro" easyrpg-emcc

# 3) 建依賴工具鏈（emsdk 5.0.5 + 各函式庫 + liblcf）—— 很久（數十分鐘）
docker exec ezbuild bash /scripts/deps.sh
```

完成後即可由 GUI 重建，或手動 `docker exec ezbuild bash /scripts/player.sh`。

## 檔案
- `Dockerfile` — 建置環境（glibc 基底；**不可用 Alpine**，emsdk 工具鏈是 glibc）。
- `deps.sh` — 建依賴工具鏈（一次性）。
- `player.sh` — 編 Player 本體（含 nlohmann_json cmake config 修補）。
- `src-ref/window_keyboard.cpp` — 取名字表樣板（`nametable.render` 以它為底替換）。
- `src-ref/*` — 其餘 EasyRPG 原始碼/preset 參考。

## 踩過的雷（已寫進 Dockerfile/player.sh）
- Alpine 不行（musl）→ 用 debian:12-slim。
- apt 的 meson 太舊 → harfbuzz 找不到 freetype（pip 裝新版 meson）。
- cmake < 3.23 不認 presets v4 → debian:12 的 3.25 可；舊環境需升級。
- buildscripts 的 cleanup 刪了 `share/`，連帶 nlohmann_json 的 cmake config → `player.sh` 自動補一份。
