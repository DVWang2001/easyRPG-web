# EasyRPG → iOS 網頁版 / PWA 打包工具

把 RPG Maker 2000/2003 遊戲打包成**自包含的網頁 App**，部署到 GitHub Pages 後，
iPhone 用 Safari 開、按「加入主畫面」即得**全螢幕、有圖示、可離線**的 App，MIDI 音色比照 Windows。
**純 Windows 可用，不需 Mac、不需編譯。**

## 為什麼是網頁版而不是 .ipa？
原生 iOS `.ipa` 一定要 macOS + Xcode 編譯與簽章（Apple 鎖死），Windows 做不到。
網頁/PWA 是純 Windows 能完成、又能在 iPhone 上像 App 一樣全螢幕離線遊玩的方案。

## 前置需求
- Python 3.8+（僅標準庫）。
- 一個 GitHub repo（要用 GitHub Pages 上線時）。

## GUI（推薦）
- Windows：雙擊 `啟動GUI.bat`
- macOS/Linux：`./run.sh`

選遊戲資料夾 →（可改名稱/音色/圖示）→「開始打包」→ 產物在 `dist/`。

## CLI
```
python easyrpg_web_build.py --game "C:/Games/花嫁之冠" --app-label 花嫁之冠
```
| 參數 | 說明 |
|---|---|
| `--game`（必） | 遊戲資料夾（含 `RPG_RT.ldb`/`.lmt`） |
| `--app-label` | App 名稱（預設＝資料夾名） |
| `--soundfont` | SF2 音色（預設內附 Windows 音色） |
| `--app-icon` | App 圖示 PNG（預設內附） |
| `--rtp` | RTP 資料夾，先灌入再打包 |
| `--ignore` | 忽略 glob（可重複；預設排除 `*.bak`/`*.trans` 等） |
| `--exclude-file` | 排除清單檔（每行一個相對路徑） |
| `--out` | 輸出夾（預設 `dist`） |
| `--refresh-player` | 強制重抓官方 web player |
| `--deploy` | 完成後 push 到 `gh-pages` |

## 本機測試
```
cd dist && python -m http.server
```
電腦瀏覽器開 `http://localhost:8000` 應自動啟動遊戲。
手機同 Wi-Fi 可開 `http://<電腦區網IP>:8000`（注意：純 http 非 localhost 時 service worker 不啟用，離線功能要上 HTTPS 才生效）。

## 上線到 GitHub Pages（iPhone 安裝）
1. `--deploy`（或手動把 `dist/` 內容 push 到 `gh-pages` 分支）。
2. repo 設定啟用 Pages（來源選 `gh-pages`）。
3. iPhone Safari 開該 HTTPS 網址 → 分享 →「加入主畫面」→ 全螢幕 App。

## 注意
- 音色 SF2 別過大（內附 Windows 音色約 3 MB，OK）。
- 遊戲依賴 RTP 時請用 `--rtp` 一併打包。
