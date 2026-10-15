# RPG Maker 2000 遊戲翻譯完整工作流程指南

> **適用範圍**：透過 EasyRPG / RPG Maker 2000 StringScripts 格式進行繁體中文本地化翻譯。

---

## 目錄

1. [前置分析：認識 StringScripts 目錄結構](#1-前置分析認識-stringscripts-目錄結構)
2. [工具腳本說明](#2-工具腳本說明)
3. [標準翻譯工作流程](#3-標準翻譯工作流程)
4. [翻譯品質規範](#4-翻譯品質規範)
5. [自動化校對流程](#5-自動化校對流程)
6. [已知 Bug 與修復方法](#6-已知-bug-與修復方法)
7. [Database 檔案翻譯](#7-database-檔案翻譯)
8. [常見字元相容性問題](#8-常見字元相容性問題)
9. [快速參考：角色名稱字典](#9-快速參考角色名稱字典)

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
| `Map0001.txt` ~ `Map00XX.txt` | Message-based | 地圖對話腳本，含 `#Message#`/`##` 標籤 |
| `Database/Vocab.txt` | Tag-based | UI 詞彙（戰鬥訊息、選單文字等） |
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

### 2.2 `proofread.py` — 自動化校對工具

**功能**：批次校對所有已翻譯的地圖檔案，檢查四個品質指標。

```bash
python scratch/proofread.py
```

#### 校對項目

1. **BOM 編碼驗證**：確認輸出檔案有 UTF-8 BOM
2. **標籤結構比對**：`#Message#`、`##`、`Select Face Graphic` 數量與原始一致
3. **日文假名殘留檢查**：偵測訊息區塊內的平假名/片假名
4. **日式標點符號檢查**：偵測 `ー`（長音符）、`・`（中點）

#### 更新校對清單

每完成一個檔案就加入清單：

```python
# proofread.py 第 83 行附近
files_to_check = (
    [f"Map{i:04d}.txt" for i in range(1, 12)] +
    ["Map0018.txt", "Map0019.txt", "Map0020.txt", "Map0021.txt",
     "Map0022.txt", "Map0023.txt", "Map0024.txt", "Map0025.txt"]
)
```

> **規則**：每完成 5 個檔案，執行一次批次校對。

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

### Step 5：加入校對清單並執行校對

更新 `proofread.py` 的 `files_to_check` 清單，然後執行：

```bash
python scratch/proofread.py
```

確認**所有項目**均顯示 `[OK]`。

### Step 6：重複直到全部完成

---

## 4. 翻譯品質規範

### 4.1 語言風格

- 使用**繁體中文（台灣）**
- 保持角色個性：
  - 說話加「喵」的貓型角色 → 結尾加「喵」
  - 古風武士角色 → 使用文言詞彙（「妳」、「彼」、「也」）
  - 現代少女角色 → 自然口語

### 4.2 角色名稱字典（建立後統一使用）

| 日文原名 | 中文譯名 | 備註 |
|----------|----------|------|
| 鞍春 | 鞍春 | 主角（不翻譯） |
| タマ / 小玉 | 小玉 | 貓妖姬，說話加「喵」 |
| 真実 | 真實 | 真實的名字 |
| 狐姫 | 狐狸公主 / 公主 | 依上下文選用 |
| おジジ | 老頭子 | 老爺爺型妖怪 |
| マコト | 真實 | 真實的愛稱 |
| 雪乃 | 雪乃 | 人名不翻譯 |
| 和真 | 和真 | 人名不翻譯 |
| 綾 / Ｆ鬼 | 綾 | 女性醫師 |

### 4.3 格式規範

- **省略號**：一律使用 `…`（U+2026），**禁止**使用 `⋯`（U+22EF）
- **破折號**：使用 `—`（U+2014）
- **不翻譯**：`Select Face Graphic`、`#Message#`、`##` 等指令行
- **保留**：所有 `\` 開頭的控制碼

---

## 5. 自動化校對流程

### 每 5 個檔案校對一次

```bash
python scratch/proofread.py
```

### 校對通過標準

每個檔案必須全部顯示 `[OK]`：

```
--- Checking File: MapXXXX.txt ---
[OK] BOM encoding is valid (UTF-8 BOM).
[OK] Tag structure matches origin perfectly. ({...})
[OK] No Japanese hiragana/katakana residue in messages.
[OK] Punctuation formatting (ー/・) is clean.
```

### 常見校對錯誤處理

#### `[ERROR] Tag '##' mismatch!`

→ 翻譯條目數量和原始不符，回頭檢查 `.translated.txt` 的條目數量

#### `[WARNING] Japanese characters found`

→ 翻譯中有平假名/片假名殘留，逐一找出並翻譯

#### `[ERROR] missing UTF-8 BOM encoding`

→ 使用 PowerShell 手動加 BOM：

```powershell
$content = [System.IO.File]::ReadAllText("MapXXXX.txt", [System.Text.Encoding]::UTF8)
$bom = [byte[]](0xEF, 0xBB, 0xBF)
$bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
[System.IO.File]::WriteAllBytes("MapXXXX.txt", $bom + $bytes)
```

---

## 6. 已知 Bug 與修復方法

### Bug 1：省略號顯示為 `????`

**症狀**：遊戲中省略號（`⋯`）顯示為問號

**原因**：`⋯`（U+22EF）不在 RPG Maker 2000 字型字元集內

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

> ⚠️ **預防措施**：翻譯時從一開始就使用 `…` 而非 `⋯`。

---

### Bug 2：`Select Face Graphic` 指令顯示為對話文字

**症狀**：遊戲畫面顯示 `{{{{{{{{{ Select Face Graphic: F??, 4, Left, Normal }}}}}}}}}`

**原因**：`translator.py` 的 `reconstruct()` 在倒序重建時，若翻譯行數與原始行數不同，會導致後續的 `Select Face Graphic` 指令行跑進 `#Message#` 區塊內。

**高風險場景**：`Database/Troops.txt`（戰鬥對話），因為其 Message 區塊與 `Select Face Graphic` 指令交錯排列，結構更複雜。

**修復步驟**：

1. 讀取 `scratch/to_translate/Troops.txt.meta.json`，確認每個 message 的 `start_line_idx` 和 `end_line_idx`
2. 讀取原始檔案骨架（`Select Face Graphic`、`#Message#`、`##`、`---PageN---`）
3. **直接手動重建**整個 `Database/Troops.txt`，將翻譯文字填入正確的 `#Message#` / `##` 區塊
4. 確認修復後的檔案有 UTF-8 BOM

**驗證指令**：

```powershell
$content = Get-Content "Database\Troops.txt" -Raw -Encoding UTF8
$msgCount = ([regex]::Matches($content, '#Message#')).Count
$endCount = ([regex]::Matches($content, '##')).Count
Write-Host "#Message#: $msgCount, ##: $endCount"
# 兩個數字必須相等，且等於 meta.json 中的 items 數量
```

**預防措施**：`Troops.txt` 翻譯時，確保每個條目的行數與原始 meta.json 記載的 `(end_line_idx - start_line_idx + 1)` **相同**，不要增減行數。

---

### Bug 3：計數不符（Count mismatch）

**症狀**：`Warning: Count mismatch! Expected 39 translated items, but parsed 40.`

**原因**：翻譯對照檔的條目數量與原始 `.trans.txt` 不一致，通常是：
- 不小心把一個多行條目拆分成兩個（多一條）
- 遺漏翻譯某條（少一條）

**修復**：
1. 計算 `.trans.txt` 的最大編號
2. 計算 `.translated.txt` 的最大編號
3. 逐條比對找出多/少的位置
4. 合併或補充使數量吻合

**範例（合併多餘條目）**：

原本（錯誤，40 條）：
```
29. 但我這個人，
不管對方是誰，
30. 受了挑釁就一定奉陪到底。
31. 本喵退出喵！
```

修正後（正確，39 條）：
```
29. 但我這個人，
不管對方是誰，
受了挑釁就一定奉陪到底。
30. 本喵退出喵！
```

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

```bash
python scratch/translator.py import Database/Vocab.txt scratch/to_translate/Vocab.txt.translated.txt Database/Vocab.txt
python scratch/translator.py import Database/Items.txt scratch/to_translate/Items.txt.translated.txt Database/Items.txt
python scratch/translator.py import Database/Skills.txt scratch/to_translate/Skills.txt.translated.txt Database/Skills.txt
python scratch/translator.py import Database/Monsters.txt scratch/to_translate/Monsters.txt.translated.txt Database/Monsters.txt
python scratch/translator.py import Database/Conditions.txt scratch/to_translate/Conditions.txt.translated.txt Database/Conditions.txt
python scratch/translator.py import Database/Animations.txt scratch/to_translate/Animations.txt.translated.txt Database/Animations.txt
python scratch/translator.py import Database/Attributes.txt scratch/to_translate/Attributes.txt.translated.txt Database/Attributes.txt
python scratch/translator.py import Database/Hero.txt scratch/to_translate/Hero.txt.translated.txt Database/Hero.txt
python scratch/translator.py import Database/Terrain.txt scratch/to_translate/Terrain.txt.translated.txt Database/Terrain.txt
# Troops.txt 建議手動重建，見 Bug 2 說明
```

---

## 8. 常見字元相容性問題

RPG Maker 2000 / EasyRPG 字型支援的字元有限，翻譯時必須避免使用以下字元：

| 禁止使用 | Unicode | 替代方案 |
|----------|---------|----------|
| `⋯`（數學省略號） | U+22EF | `…`（U+2026）|
| `…`（全形三點） | 可用 | ✅ 使用此字元 |
| 少見漢字、特殊符號 | 各異 | 遊戲中測試確認 |

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

在新遊戲開始翻譯前，先建立此表格並在整個翻譯過程中嚴格遵守。

| 日文原名 | 面立識別（臉圖） | 中文譯名 | 說話特徵 |
|----------|-----------------|----------|----------|
| 自建自填 | Ｆ＊＊ | 自建自填 | 自建自填 |

---

## 10. 完整工作清單（Checklist）

### 初始準備

- [ ] 確認 `StringScripts_Origin/` 目錄存在且完整
- [ ] 確認 `scratch/translator.py` 和 `scratch/proofread.py` 已就緒
- [ ] 建立角色名稱字典
- [ ] 執行 `python scratch/translator.py list` 掌握所有待翻譯檔案

### 每個檔案的翻譯流程

- [ ] 閱讀 `.trans.txt` 理解脈絡
- [ ] 撰寫 `.translated.txt`（條目數對齊）
- [ ] 執行 `translator.py import` 匯入
- [ ] 確認無 `Count mismatch` 警告
- [ ] 每 5 個檔案執行 `proofread.py` 批次校對
- [ ] 所有校對項目皆為 `[OK]`

### 最終收尾

- [ ] 翻譯所有 Database 檔案
- [ ] 執行全域字元相容性修復（省略號等）
- [ ] 執行完整校對確認
- [ ] 在遊戲中實際測試

### 測試要點

- [ ] 對話文字正常顯示，無 `????` 亂碼
- [ ] 無 `Select Face Graphic` 指令顯示為對話文字
- [ ] 戰鬥訊息（Vocab）正常顯示
- [ ] 道具、技能名稱正常顯示

---

## 附錄：translator.py 工作原理

### Message-based 檔案（地圖/Troops）

解析流程：
1. 偵測 `#Message#` → 開始記錄訊息內容
2. 遇到 `##` → 結束，記錄 `start_line_idx` 和 `end_line_idx`
3. 偵測 `Select Face Graphic: 名稱` → 記錄當前臉圖

重建流程（**倒序替換**）：
1. 從最後一個 message 往前逐一替換
2. 使用 `new_lines[start:end+1] = val_lines`（支援行數增減）
3. 倒序確保前面 items 的 line index 不受影響

> ⚠️ **限制**：若某個 item 的翻譯行數與原始不同，且 item 後方緊接著 `Select Face Graphic` 指令，重建後可能發生行位移導致指令行跑進 Message 區塊。`Troops.txt` 特別容易出現此問題，建議手動重建。

### Tag-based 檔案（Database）

解析流程：
1. 偵測 `#TagName#` 標籤行
2. 取下一行作為待翻譯值
3. 記錄 `line_idx`

重建流程：同樣倒序替換，但每次只替換單行，無行數不符問題。

---

*此文件依據《滿月之夜的公主》繁體中文翻譯實戰經驗整理，2026-05-21*
