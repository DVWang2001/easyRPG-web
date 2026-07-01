# RPG Maker 2000/2003 遊戲翻譯完整工作流程指南

> **適用範圍**：透過 EasyRPG / RPG Maker 2000 & 2003 StringScripts 格式進行繁體中文本地化翻譯。
> 本指南結合《滿月之夜的公主》、《RPG Maker 2003 樣品遊戲》與《Soul of Dandizm（丹迪之魂）》繁中漢化實戰經驗編寫。

---

## 目錄

1. [前置分析：認識 StringScripts 目錄結構](#1-前置分析認識-stringscripts-目錄結構)
2. [工具腳本說明](#2-工具腳本說明)
3. [標準翻譯工作流程](#3-標準翻譯工作流程)
4. [翻譯品質規範](#4-翻譯品質規範)
5. [一鍵式自動化品質校對流程](#5-一鍵式自動化品質校對流程)
6. [已知 Bug 與修復方法](#6-已知-bug-與修復方法)
7. [Database 檔案翻譯](#7-database-檔案翻譯)
8. [常見字元相容性問題](#8-常見字元相容性問題)
9. [快速參考：角色名稱字典](#9-快速參考角色名稱字典)
10. [完整工作清單（Checklist）](#10-完整工作清單checklist)

---

## 1. 前置分析：認識 StringScripts 目錄結構

### 目錄配置

```
StringScripts/              ← 翻譯工作目錄（輸出位置）
StringScripts_Origin/       ← 原始日文檔案（只讀，不能修改）
StringScripts/Database/     ← 資料庫類翻譯輸出
StringScripts/scratch/      ← 工具腳本與暫存目錄
StringScripts/scratch/to_translate/  ← 翻譯對照檔輸入/輸出
```

### 檔案類型

| 檔案 | 類型 | 說明 |
|------|------|------|
| `Map0001.txt` ~ `Map00XX.txt` | Message-based | 地圖對話腳本，含 `#Message#`/`##` 標籤與選擇支 `#Choice#` |
| `Database/Vocab.txt` | Tag-based | UI 詞彙（戰鬥訊息、選單文字、商店與旅店對白等） |
| `Database/Items.txt` | Tag-based | 道具名稱與說明 |
| `Database/Skills.txt` | Tag-based | 技能名稱、說明、使用訊息 |
| `Database/Monsters.txt` | Tag-based | 怪物名稱 |
| `Database/Conditions.txt` | Tag-based | 狀態效果名稱與訊息 |
| `Database/Troops.txt` | Message-based | 戰鬥中的對話（含 `Select Face Graphic` 指令） |
| `Database/Animations.txt` | Tag-based | 動畫名稱 |
| `Database/Attributes.txt` | Tag-based | 屬性名稱 |
| `Database/Hero.txt` | Tag-based | 角色名稱與稱號 |
| `Database/Terrain.txt` | Tag-based | 地形名稱 |

### 空白檔案識別

部分 `MapXXXX.txt` 大小僅 3 bytes（只有 BOM），代表無對話內容，**直接跳過**。

---

## 2. 工具腳本說明

所有腳本放在 `scratch/` 目錄下，執行目錄為 `StringScripts/`。

### 2.1 `translator.py` — 核心翻譯工具

**功能**：從原始檔案提取待翻譯文字，並將翻譯後的文字重新寫回正確格式。

> ⚠️ **RPG Maker 2003 冒號標籤支持**：
> 在 RPG Maker 2003 的 `Vocab.txt` 中，Tag 可能含有冒號（如 `#ShopA:Buy#`）。需確保 `translator.py` 中的 `tag_match` 正則表達式修正為 `r'^#([^#]+)#(?:\s*\[\d+\])?'`，以避免漏掉商店或旅店對白。

#### 指令用法

```bash
# 匯出待翻譯文字
python scratch/translator.py export <原始檔路徑>
# 範例：python scratch/translator.py export ../StringScripts_Origin/Map0001.txt

# 匯入翻譯結果
python scratch/translator.py import <原始檔路徑> <翻譯對照檔> <輸出檔>
# 範例：
python scratch/translator.py import ../StringScripts_Origin/Map0001.txt \
    scratch/to_translate/Map0001.txt.translated.txt \
    Map0001.txt
```

#### 匯出格式（`.trans.txt`）

每個條目的格式如下：
```
1. [MARKER: Message] [FACE: F鞍春] 原文第一行
原文第二行（多行直接續接）
2. [MARKER: Message] [FACE: Ｆタマ] 第二條原文
```

#### 翻譯對照檔格式（`.translated.txt`）

```
1. 翻譯第一行
翻譯第二行（多行直接續接，不需要編號）
2. 翻譯第二條
```

> **重要**：編號必須連續不跳號，且數量必須與 `.trans.txt` 的條目數**完全一致**。

### 2.2 `check_translation_quality.py` — 一鍵品質檢測工具

**功能**：批次掃描所有已翻譯的地圖與資料庫檔案（包含戰鬥對話、共同事件），檢查編碼、假名、中點及控制代碼等品質指標，並輸出無亂碼報告。

```bash
python scratch/check_translation_quality.py
```

#### 檢測項目

1. **CP950 (Big5) 編碼相容性**：偵測文字中是否含有不被 Big5 支援的字元（包含日文漢字、簡體字），避免在遊戲中直接顯示為問號 `?`。
2. **日文假名殘留**：透過正則表達式攔截 `#Message#`、`#Choice#` 顯示區塊中的日文平假名與片假名（排除 `Select Face Graphic` 行中的素材檔名）。
3. **中點與標點符號**：檢查是否殘留日文中點 `・`、半形中點 `･`、或舊省略號 `⋯`，要求代換為支援度最好的全形中點 `·` (U+00B7)。
4. **不支援的控制代碼**：在 RPG Maker 2000/EasyRPG 繁中環境下，若出現 `\S[n]` 速度控制代碼，會導致顯示出錯或字元錯置，必須予以清除。

#### 輸出報告

檢測完成後，將在 `scratch/translation_validation_report.txt` 輸出完整報告，明確標出問題檔案、行號、問題類型與上下文內容。

> **規則**：每次執行 `import_all.py` 匯入後，應立即執行品質檢測，確保 `Total Issues Found` 歸零。

### 2.3 `translate_choices.py` 與 `import_all.py` — 選擇支翻譯與一鍵匯入

**功能**：
* `translate_choices.py`：由於 `translator.py` 無法解析地圖檔案中的 `#Choice#` 到 `##` 選項區塊，此腳本針對生成的地圖 `.txt` 檔案進行地圖選項的字串替換（如 `１分コース`、`老婆の話を聞く` 等）。
* `import_all.py`：一鍵批次匯入指令。依序對所有檔案執行 `translator.py import` 重建，並在末端自動調用 `translate_choices.py` 對選項進行漢化。

---

## 3. 標準翻譯工作流程

### Step 1：確認待翻譯清單

```bash
python scratch/translator.py list
```

輸出示例：
```
Filename                            | Type          | Items to Translate
Map0001.txt                         | Message-based | 9
Map0002.txt                         | Message-based | 145
```

空白檔案（0 條目）直接跳過。

### Step 2：讀取待翻譯文字

打開對應的 `.trans.txt` 對照檔：
```
scratch/to_translate/Map0002.txt.trans.txt
```
仔細閱讀原文，理解場景脈絡、人物關係，再開始翻譯。

### Step 3：撰寫翻譯對照檔

建立 `.translated.txt` 檔案，格式要求：

```
1. 翻譯文字（第一行可直接接在編號後）
如果有多行，直接換行不需要標記
2. 第二條翻譯
3. 包含控制碼的翻譯：\.\S[2]要照抄控制碼
4. 多行翻譯：
第二行
第三行
```

#### 控制碼對照表

| 控制碼 | 意義 | 翻譯規則 |
|--------|------|----------|
| `\.` | 文字顯示暫停（點擊後繼續） | **照抄，不刪除** |
| `\S[N]` | 切換文字速度 | **照抄** |
| `\C[N]` | 切換文字顏色 | **照抄** |
| `$d` | 頁面結束後繼續 | **照抄** |
| `$e` | 聲音效果 | **照抄** |
| `$n` | 換行後暫停 | **照抄** |
| `\S[N]...\S[M]` | 速度段落 | **照抄** |

#### ⚠️ 防爆框（排版預防）
* RPG Maker 2003 的對話框在左側有頭像（Face Graphic）顯示時，一行的最大寬度通常只有 **18-20 個全形中文字**。
* 超過此長度的行，在遊戲中會直接超出邊界被截斷。
* **避免使用過長的半形英文字母/拼音**。英文與拼音會佔用大量橫向空間，且無法自動換行，極易引發爆框。

### Step 4：匯入翻譯

```bash
python scratch/translator.py import ../StringScripts_Origin/MapXXXX.txt \
    scratch/to_translate/MapXXXX.txt.translated.txt \
    MapXXXX.txt
```

成功輸出：
```
Successfully imported translation. Reconstructed file saved to MapXXXX.txt
```
若出現 `Warning: Count mismatch!`，立即停下來修正翻譯檔的條目數量。

### Step 4.5：執行地圖選擇支 Choice 漢化
執行批次匯入時，需確保已執行 `translate_choices.py` 對產出地圖檔案（如 `Map0003.txt`、`Map0004.txt`）中的日文選項進行取代。

### Step 5：執行一鍵式品質校對
執行校對工具，確認無任何假名殘留、控制代碼錯誤或編碼問題：
```bash
python scratch/check_translation_quality.py
```
確認輸出報告顯示「Total issues found: 0」。

### Step 6：重複直到全部完成

---

## 4. 翻譯品質規範

### 4.1 語言風格

- 使用**繁體中文（台灣）**。
- 保持角色個性：
  - 說話加「喵」的貓型角色 → 結尾加「喵」
  - 古風武士角色 → 使用文言詞彙（「妳」、「彼」、「也」）
  - 現代少女角色 → 自然口語
- **暱稱在地化**：日文中的人名加語氣詞 `ちゃん`（Chan），在翻譯為繁體中文時應轉換為「`妹妹`」（如 `葉月妹妹`、`翔子妹妹`），避免直譯。

### 4.2 格式規範

- **省略號**：一律使用 `…`（U+2026），**禁止**使用 `⋯`（U+22EF）。
- **破折號**：使用 `—`（U+2014）。
- **引號**：使用全形 `「` 與 `」`、`『` 與 `』`。
- **保護系統資源檔名**：`Select Face Graphic: 名稱` 中的圖片檔名（例如 `はづき１`、`一一子`）是引擎尋找圖片素材所用，**絕對不能翻譯**，否則會因找不到檔案導致遊戲崩潰。

---

## 5. 一鍵式自動化品質校對流程

為了相容 Big-5 繁體中文執行環境，在發佈前必須使用此腳本進行全域校驗。

### 5.1 全域校對 `check_translation_quality.py`
完成匯入後執行：
```bash
python scratch/check_translation_quality.py
```
它會自動處理全部 218 個檔案（地圖檔與資料庫檔案），確保在 LMU 與 LDB 檔案重建後無任何格式毀損。

### 5.2 雙重檢測與過濾原理
1. **Big5 (CP950) 編碼測試**：嘗試將對話文字進行 `.encode('cp950')` 測試，捕獲不支援的字元（如日文漢字 `売`、`毎` 等）。
2. **假名正則過濾**：因為日文平假名與片假名在 Big5 擴充字元集中可能擁有編碼位置（能順利通過 encode 測試），但在繁中 RPG 引擎中會全部顯示為問號 `?`。因此必須使用正則表達式 `[\u3040-\u309f\u30a0-\u30ff]` 對 `#Message#` 與 `#Choice#` 顯示區塊進行強制過濾，確保無假名殘留（如日文促音 `ッ` 等）。
3. **系統資源排除**：檢測時自動跳過 `Select Face Graphic` 標籤行，避免系統臉圖檔名中的日文產生誤報。
4. **控制代碼排除**：自動過濾無效或會造成崩潰的 `\S[n]` 速度控制代碼。
5. **中點標點符號**：統一檢測日文中點 `・`，要求改為最相容的 `·` (U+00B7)。

---

## 6. 已知 Bug 與修復方法

### Bug 1：省略號顯示為 `????`

**症狀**：遊戲中省略號（`⋯`）顯示為問號。
**原因**：`⋯`（U+22EF）不在 RPG Maker 2000/2003 中文字型字元集內。
**修復**：全域替換所有翻譯完的 `.txt` 檔案：

```powershell
$files = Get-ChildItem -Path "." -Filter "Map*.txt" -File
$files += Get-ChildItem -Path "Database" -Filter "*.txt" -File

foreach ($file in $files) {
    $content = [System.IO.File]::ReadAllText($file.FullName, [System.Text.Encoding]::UTF8)
    if ($content -match '⋯') {
        $newContent = $content -replace '⋯', '…'
        $bom = [byte[]](0xEF, 0xBB, 0xBF)
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($newContent)
        [System.IO.File]::WriteAllBytes($file.FullName, $bom + $bytes)
        Write-Host "Fixed: $($file.Name)"
    }
}
```

---

### Bug 2：`Select Face Graphic` 指令顯示為對話文字

**症狀**：遊戲畫面顯示 `{{{{{{{{{ Select Face Graphic: F??, 4, Left, Normal }}}}}}}}}`。
**原因**：`translator.py` 在倒序重建時，若翻譯行數與原始行數不同，會導致後續的 `Select Face Graphic` 指令行跑進 `#Message#` 區塊內。
**高風險場景**：`Database_Troops.txt`（戰鬥對話），其 Message 區塊與臉圖指令交錯排列，結構更複雜。
**修復與防範機制**：
1. 確保 `import_all.py` 批次導入腳本已針對 `Database_Troops.txt` 實施與地圖事件（Message-based）相同的欄位區塊重建。
2. 升級品質檢測腳本，將 `Database_Troops.txt` 以及 `Database_CommonEvents.txt` 等含有對話的資料庫檔案，一併納入與地圖相同的訊息區塊過濾。
3. 如果檢測到 `Select Face Graphic` 標記出現在 `#Message#` 與 `##` 的對話內文區塊中，腳本會立即回報格式受損。此時可透過對比原始檔案，校正翻譯對照檔中的行數結構。

---

### Bug 3：計數不符（Count mismatch）

**症狀**：`Warning: Count mismatch! Expected 39 translated items, but parsed 40.`
**原因**：翻譯對照檔的條目數量與原始 `.trans.txt` 不一致。
**修復**：計算兩邊的最大編號，逐條比對找出多/少的位置，合併或補充使數量吻合。

---

### Bug 4：對話或選項在 Big-5 環境下顯示為問號 `?`

**症狀**：遊戲對話或選擇選項出現 `????`，即使文字檔中看起來正常。
**原因**：地圖檔（`.lmu`）中殘留了日文假名（如平假名、片假名、或 `ヶ` 等字元），或是使用了不支援的日文漢字（如 `辻`、`売`、`毎`）。
**修復**：
1. 使用 `check_big5.py` 找出殘留字元及其檔案。
2. 在翻譯對照檔或 `translate_choices.py` 選項取代字典中，將其替換為相容的繁體中文。
3. 重新執行匯入，並使用二進位工具重新寫回 `.lmu` 與 `.ldb` 遊戲檔。

---

### Bug 5：對話框英文字元過長導致爆框（文字超出邊界）

**症狀**：對話框文字後半截消失，無法顯示。
**原因**：使用半形英文字母或拼音作為諧音說明時，字元佔用空間過大（且引擎不會對英文自動折行）。
**解決方案**：
* 避免使用長英文拼音（如將 `かねだじゅういちこ` 讀音拼寫為 `Kaneda Juichiko`）。
* 在地化為中文「姓名標點切分說明」（例如：將原本三行拼音改為：第一行 `女孩　　「順帶一提，請讀作`、第二行 `『金田·十一子』喔。可不是`、第三行 `『金田一·始子』喔」`），既能完美點出笑點，又能確保字數精簡、不爆框。

---

## 7. Database 檔案翻譯

### 工作流程

Database 檔案使用 **Tag-based** 格式（非 Message-based），翻譯方式相同。

```bash
python scratch/translator.py import Database/Vocab.txt \
    scratch/to_translate/Vocab.txt.translated.txt \
    Database/Vocab.txt
```

### 注意事項

1. **`Troops.txt` 特殊處理**：戰鬥對話同樣是 Message-based，結構複雜，建議直接手動重建而非依賴 translator.py 重建。
2. **分隔行保留**：`--------------------`（20個破折號）是遊戲內部的分隔標記，翻譯時直接保留原樣。
3. **全批次匯入指令**：
   直接執行 `python scratch/import_all.py`，它會自動將所有地圖檔與資料庫檔案匯出並執行 Choice 選項取代。

---

## 8. 常見字元相容性問題

RPG Maker 2000 / EasyRPG 字型支援的字元有限，翻譯時必須避免使用以下字元，並進行全域替換：

| 原始日文漢字/符號 | Big-5 繁體中文替代字 | 說明 |
|:---:|:---:|---|
| `売` | `賣` | |
| `却` | `卻` | |
| `旧` | `舊` | |
| `毎` | `每` | |
| `衆` | `眾` | |
| `説` | `說` | |
| `辻` | `十字路口 / 辻` | Big-5 不支援「辻」字，地圖選項需替換 |
| `・` | `·` (U+00B7) | 日文中點，改用 Big-5 相容間隔號 |
| `ー` | `~` | 日文長音，改用波浪號 |
| `～` | `~` | 全形波浪號，在某些系統會亂碼，改用半形 |
| `♪` | `~ / (空)` | 音符符號，Big-5 不相容，需刪除或以波浪號替換 |
| `\S[n]` | (空) | 不被 RPG Maker 2000 支援的速度代碼，需刪除 |
| `ッ` | (空) | 日文促音，會被顯示為問號，翻譯時必須去除 |

### 全域修復腳本

若已完成翻譯但存在字元問題，使用以下 PowerShell 腳本修復：

```powershell
# 執行目錄：StringScripts/
$mapFiles = Get-ChildItem -Path "." -Filter "Map*.txt" -File
$dbFiles  = Get-ChildItem -Path "Database" -Filter "*.txt" -File
$allFiles = $mapFiles + $dbFiles

foreach ($file in $allFiles) {
    $content = [System.IO.File]::ReadAllText($file.FullName, [System.Text.Encoding]::UTF8)
    $changed = $false

    # 修復省略號
    if ($content -match '⋯') {
        $content = $content -replace '⋯', '…'
        $changed = $true
    }

    if ($changed) {
        $bom = [byte[]](0xEF, 0xBB, 0xBF)
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
        [System.IO.File]::WriteAllBytes($file.FullName, $bom + $bytes)
        Write-Host "Fixed: $($file.Name)"
    }
}
```

---

## 9. 快速參考：角色名稱字典

在開始翻譯前，先建立此表格並在整個翻譯過程中嚴格遵守。

### 9.1 《滿月之夜的公主》譯名對照表

| 日文原名 | 面立識別（臉圖） | 中文譯名 | 說話特徵 |
|:---:|:---:|:---:|---|
| 鞍春 | Ｆ鞍春 | 鞍春 | 主角，不翻譯 |
| タマ / 小玉 | Ｆタマ | 小玉 | 貓妖姬，說話尾接「喵」 |
| 真実 | Ｆ真実 | 真實 | 真實的名字 |
| 狐姫 | Ｆ狐姫 | 狐狸公主 / 公主 | 依上下文選用 |
| おジジ | Ｆおジジ | 老頭子 | 老爺爺型妖怪 |
| マコト | (無) | 真實 | 真實的愛稱 |
| 雪乃 | (無) | 雪乃 | 人名不翻譯 |
| 和真 | (無) | 和真 | 人名不翻譯 |
| 綾 / Ｆ鬼 | Ｆ鬼 | 綾 | 女性醫師 |

### 9.2 《樣品遊戲》譯名對照表

| 日文原名 | 中文譯名 | 說話特徵 / 備註 |
|:---:|:---:|---|
| `はづき` | `織部葉月` | 女主角 |
| `サブ` | `薩布` | 新浪潮歌手組合 |
| `ヨネ次` | `米次` | 新浪潮歌手組合 |
| `かねだじゅういちこ` | `金田十一子` | 女偵探（自稱），讀音為 Kaneda Juichiko |
| `きんだいちはじめこ` | `金田一始子` | 被誤認的名字，讀音為 Kindaichi Hajimeko |
| `しょうこ` | `翔子` | TAROT 店員 |
| `ひびき` | `響` | TAROT 店長代理 |

### 9.3 《Soul of Dandizm（丹迪之魂）》譯名對照表

| 日文原名 | 中文譯名 | 說話特徵 / 備註 |
|:---:|:---:|---|
| `イゾウ` | `以藏` | 男主角，冷酷卻富有正義感，古風劍客 |
| `オスカー` / `オスカ` | `奧斯卡` | 智囊戰友，貴族出身，使用波坦金號 |
| `オンドレ` | `安德烈` | 以藏敬愛的大哥（熱血兄貴大行進） |
| `ジョジョリーナ` | `喬喬莉娜` | 主力女隊友，性格豪爽 |
| `リュウゼン` | `流漸` | 重要劇情人物，掌握不死之身秘密的天才 |
| `リード` / `リード＝アレン` | `里德·艾倫` | 俠盜，提供地道潛入情報 |
| `DANDY` / `ダンディ` | `DANDY / 丹迪` | 指引主角群的大哥角色 |
| `アルフ` | `阿爾夫` | 支援攻擊角色 |
| `マサル` | `阿勝` | 支援攻擊角色，崇拜 DANDY |
| `オルベ` | `奧爾貝` | DANDY 的弟弟，以骷髏之姿留在崩塌世界中 |
| `ダンダリオン` | `丹達里恩` | 最終 Boss，欲收集以藏的原始生命體基因以振興故鄉 |

---

## 10. 完整工作清單（Checklist）

### 初始準備

- [ ] 確認 `StringScripts_Origin/` 目錄存在且完整。
- [ ] 確認 `scratch/translator.py` 與 `scratch/check_translation_quality.py` 已就緒。
- [ ] 建立角色名稱字典。
- [ ] 執行 `python scratch/translator.py list` 掌握所有待翻譯檔案。

### 每個檔案的翻譯流程

- [ ] 閱讀 `.trans.txt` 理解脈絡。
- [ ] 撰寫 `.translated.txt`（條目數對齊）。
- [ ] 執行 `translator.py import` 匯入，或執行 `import_all.py` 一鍵處理。
- [ ] 確認無 `Count mismatch` 警告。
- [ ] 檢查每行字數長度，有頭像時不超過 18-20 全形字，預防爆框。
- [ ] 執行 `check_translation_quality.py` 確保對話及選項中 100% 無假名、控制碼與非 Big-5 字元殘留。
- [ ] 所有校對項目皆為 `[OK]`。

### 最終收尾

- [ ] 翻譯所有 Database 檔案。
- [ ] 執行全域字元相容性修復（省略號、波浪號、音符等）。
- [ ] 使用二進位匯入工具，將產出的 `.txt` 檔案寫回 `.lmu` 地圖檔與 `.ldb` 資料庫檔中。
- [ ] 在遊戲中實際測試，確認無 `?` 亂碼、無爆框、無臉圖指令跑出。

---

*此文件依據《滿月之夜的公主》、《RPG Maker 2003 樣品遊戲》與《Soul of Dandizm（丹迪之魂）》繁體中文翻譯實戰經驗整理，最後更新：2026-05-22*
