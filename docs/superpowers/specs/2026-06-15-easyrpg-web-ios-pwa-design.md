# easyRPG-web — 把 RPG Maker 遊戲打包成 iOS 可玩的網頁版 / PWA

- 狀態：已通過設計討論（brainstorming），待寫實作計畫
- 日期：2026-06-15
- 專案路徑：`C:\opensource\easyRPG-web\`（與既有 Android apk builder `C:\opensource\easyRPG` 完全分開）

## 背景

使用者原本以為要打包成「能跑 iOS 的 App」，但只有 Windows、沒有 Mac，也不接受雲端 Mac/CI。

硬限制：**原生、已簽章的 iOS `.ipa` 一定要在 macOS + Xcode 上編譯與簽章，Windows 做不到。** 這是 Apple 鎖死的，沒有任何工具能在純 Windows 上繞過。

可行的替代路線（皆 Windows-only 可行）經討論後選定 **路線 A：網頁版 / PWA**。

關鍵事實（已查證）：
- EasyRPG **沒有**官方 iOS App Store App。
- EasyRPG 有官方 **Web/WASM（Emscripten）** 版本，能在瀏覽器直接跑 RPG Maker 2000/2003 遊戲。
- EasyRPG 提供**預編好的** web player 檔（`index.html` / `index.wasm` / `index.js`）→ **本工具不需編譯、不需 Docker**。
- 自架遊戲：遊戲夾放 `games/default/`（單一遊戲會自動啟動、無選單），需先跑 `gencache` 產生 `index.json`（因 RPG Maker 檔案無副檔名）。
- 自訂音色：在遊戲夾放 `easyrpg.soundfont`（SF2）再跑一次 `gencache` → **「MIDI 比照 Windows」的賣點在網頁版一樣成立**。官方提醒 SF2 別過大（現有 Windows 音色 3.1 MB，OK）。

## 目標 / 非目標

**目標**
- 在純 Windows 上，把一個 RPG Maker 2000/2003 遊戲資料夾，打包成一個**自包含的靜態網頁 App**。
- 部署到 GitHub Pages 後，iPhone 用 Safari 開、按「加入主畫面」即得一個**全螢幕、有圖示、可離線**的 App。
- MIDI 音色比照 Windows（沿用既有 `easyrpg.soundfont`）。
- 提供 **GUI 系統**（圖形介面），讓不想打指令的人也能選遊戲、設定、一鍵打包/部署。

**非目標**
- 原生 `.ipa`、App Store 上架。
- 自行用 Emscripten 編譯 EasyRPG Player（改用官方預編 WASM）。
- 與既有 Android apk builder 共用程式碼或 repo（刻意分開）。

## 架構 / Pipeline（無 Docker、無編譯）

```
遊戲資料夾 ──┐
SF2 音色 ────┼─► stage 到 dist/games/default/（套排除規則 + 注入 easyrpg.soundfont）
(選) RTP ───┘
官方預編 web player ─► 放 dist/（index.html / index.wasm / index.js）  ← 首次下載並快取
gencache（純 Python 重寫）─► 產生 dist/games/default/index.json
PWA 外殼 ─► dist/manifest.webmanifest + dist/icons/ + dist/service-worker.js
                              │
                              ▼
                    dist/（自包含靜態網站）
                ├─ 本機測試：python -m http.server
                └─ 上線：push 到 gh-pages 分支 → HTTPS 網址
```

設計原則：每個單元職責單一、可獨立測試。`gencache.py` 與 staging 邏輯都不依賴網路或 Docker，可離線單元測試。

## 元件（全部位於 `C:\opensource\easyRPG-web\`）

| 檔案 | 角色 | 依賴 |
|---|---|---|
| `easyrpg_web_build.py` | 跨平台 CLI 核心：驗證遊戲 → staging → 注入 SF2 →（選）灌 RTP → 呼叫 gencache → 鋪 PWA 外殼 → 輸出 `dist/` | Python 標準庫 |
| `easyrpg_web_gui.py` | **跨平台 GUI**（Tkinter，鏡射既有 `easyrpg_gui.py` 風格）：表單選遊戲/音色/圖示/RTP/輸出、deploy 勾選、Build 按鈕、threading+queue 跑非阻塞建置並即時顯示 log。**薄前端**，`import easyrpg_web_build as core` 呼叫核心，不重複邏輯 | Python 標準庫（Tkinter） |
| `gencache.py` | **純 Python 重寫**官方 gencache：遞迴掃 `games/default/`，輸出符合 EasyRPG 格式、帶副檔名的 `index.json` | Python 標準庫 |
| `player/`（快取夾） | 首次下載的官方預編 web player；之後走快取，`--refresh-player` 強制更新 | 網路（僅首次） |
| `pwa/`（模板夾） | `manifest.webmanifest` 模板、`service-worker.js` 模板、由 `--app-icon` 產各尺寸圖示的邏輯 | Python 標準庫（PNG 縮放：優先標準庫/無依賴方案，必要時記為待確認） |
| `deploy`（`--deploy` 旗標或 `deploy.py`） | 一鍵把 `dist/` push 到 `gh-pages`（用 `git` / `gh`） | git / gh CLI |
| `啟動GUI.bat` | Windows 主入口：啟動 `easyrpg_web_gui.py`（UTF-8 BOM，依既有專案的中文 .ps1/.bat 規則） | — |
| `啟動.bat` | Windows CLI 啟動器（進階／批次用） | — |
| `run.sh` | macOS/Linux 啟動器（LF、no-BOM） | — |
| `README.md` | 安裝、用法、iPhone 加入主畫面步驟 | — |

## CLI 介面（沿用既有工具參數風格）

```
python easyrpg_web_build.py --game "C:/Games/花嫁之冠" --app-label 花嫁之冠 \
    [--soundfont PATH]    # 預設用內附 Windows 音色 easyrpg.soundfont
    [--app-icon PATH]     # 產生 PWA 各尺寸圖示，預設用內附 app_icon.png
    [--rtp PATH]          # 遊戲缺素材時先灌入
    [--exclude-file PATH] # 排除清單（每行一個相對路徑）
    [--ignore GLOB]...    # 忽略 glob，未給則用內建（*.bak, *.trans …）
    [--out DIR]           # 輸出夾，預設 dist/
    [--deploy]            # 完成後 push 到 gh-pages
    [--refresh-player]    # 強制重抓官方 web player
```

產物：`dist/`（自包含靜態網站）。

## GUI 系統（Tkinter，跨平台）

設計原則：GUI 是 CLI 核心的**薄前端**——所有實際工作（驗證／staging／gencache／PWA／deploy）都在 `easyrpg_web_build.py`，GUI 只負責收集參數、呼叫核心、顯示進度。鏡射既有 `easyrpg_gui.py` 的結構（Tkinter + ttk + ScrolledText、`threading`+`queue` 非阻塞、`import easyrpg_web_build as core`）。

版面（單一視窗）：
- **遊戲資料夾**：`filedialog` 選夾 + 路徑欄。
- **App 名稱**：文字欄（預設＝資料夾名）。
- **音色 SF2**：路徑欄 + 選檔（預設內附 Windows 音色）。
- **App 圖示**：路徑欄 + 選檔（預設內附 `app_icon.png`）。
- **RTP（選填）**：路徑欄 + 選夾。
- **輸出夾**：路徑欄（預設 `dist/`）。
- **勾選：完成後部署到 GitHub Pages（`--deploy`）**、**勾選：強制更新 web player（`--refresh-player`）**。
- **「開始打包」按鈕** → 背景執行緒跑核心，**即時 log**（ScrolledText，透過 queue 由工作執行緒回報），完成跳出成功/失敗訊息與輸出路徑。
- 主入口：`啟動GUI.bat`（Windows）/ `run.sh`（macOS/Linux）。

## PWA / 離線（GitHub Pages = HTTPS，故 service worker 可用）

- `manifest.webmanifest`：`display: standalone`、`orientation`、`name`/`short_name` = `--app-label`、`start_url`、圖示 180 / 192 / 512。
- `service-worker.js`：首次載入後**快取 wasm + index.json + 全部遊戲資產**，之後**完全離線可玩、可隨身帶出門**。
- iOS Safari 「加入主畫面」→ 全螢幕、自訂圖示、獨立啟動。

## 部署（GitHub Pages）

- `--deploy`：把 `dist/` 內容 push 到目標 repo 的 `gh-pages` 分支（或 `docs/`），啟用 Pages 後得到 HTTPS 網址。
- 文件中提供本機測試指引：於 `dist/` 跑 `python -m http.server`，iPhone 同 Wi-Fi 連 PC 區網 IP 先驗證（注意：純 http 在非 localhost 下 service worker 不會啟用，離線需上 HTTPS 才生效）。

## 測試策略

- **`gencache.py` 單元測試**：對小型假遊戲夾執行，斷言 `index.json` 結構與帶副檔名清單正確。
- **staging 排除規則測試**：斷言 `*.bak` / `*.trans` 與自訂排除項不進 `dist/`。
- **音色注入測試**：斷言 `easyrpg.soundfont` 出現在 `dist/games/default/` 且被 `index.json` 收錄。
- **端對端煙霧測試**：以 `python -m http.server` 起 `dist/`，確認 `index.html` 可載入、單一遊戲自動啟動（無選單）。
- **PWA 檢查**：斷言 `manifest.webmanifest`、各尺寸圖示、`service-worker.js` 皆產出且被 `index.html` 正確引用。
- **GUI 煙霧測試**：`easyrpg_web_gui.py` 能匯入並建構視窗（可用無頭/虛擬顯示或僅測核心呼叫封裝），確認它只透過 `core` 呼叫、不重複邏輯。

## 已知風險 / 待實作時確認

1. **官方 web player 下載來源**：鎖定穩定的 archive / CI artifact 網址，抽成設定常數；`--refresh-player` 可更新。
2. **gencache 格式對齊**：用真實遊戲在官方線上播放器交叉比對 `index.json` 格式，確保自家純 Python 版相容。
3. **iOS Safari PWA 配額**：28 MB 遊戲預期 OK，但大型快取上限需實機驗證。
4. **PWA 圖示縮放**：優先無第三方依賴（若需 Pillow 等，記為明確依賴並寫進 README）。
5. **單一遊戲自動啟動**：確認預編 player 在 `games/default/` 單一遊戲時確實免 `?game=` 參數即自動啟動。

## 與既有專案的關係

- 全新、獨立、自足；不與 `C:\opensource\easyRPG`（Android apk builder）共用 repo 或程式碼。
- 可參考既有 `easyrpg_build.py` 的 staging / 排除 / 參數風格，但**複製而非依賴**。
- 沿用既有專案的中文檔案編碼規則：中文 `.bat`/`.ps1` 存 UTF-8 BOM；`.sh` 存 LF、no-BOM。
