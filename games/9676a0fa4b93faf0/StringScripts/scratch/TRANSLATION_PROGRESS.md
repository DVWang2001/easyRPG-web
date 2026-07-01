# Soul of Dandizm 漢化翻譯進度表

## 工作流程說明

1. **翻譯來源**：`scratch/to_translate/*.trans.txt`（原始日文）
2. **翻譯輸出**：`scratch/to_translate/*.translated.txt`（AI翻譯結果）
3. **寫入遊戲**：執行 `python scratch/import_all.py`（將 translated.txt 寫入 StringScripts/）

### 翻譯規則（重要！）
- 不使用任何外部翻譯 API（Google/DeepL等），由 AI 直接翻譯
- 翻譯成**繁體中文（台灣用語）**
- `.translated.txt` 保留 `[MARKER: Message] [FACE: ...]` 標籤供校對
- 最終 import 時，`translator.py` 會自動剝除這些標籤
- **控制代碼必須原樣保留**：`\S[n]`、`\N[n]`、`\C[n]`、`\V[n]`、`\.`、`\|`、`\!`、`\^`、`$g`

### 寫入工具
- `scratch/write_translation.py`：輔助寫入函式
- 用法：在翻譯腳本頂部 `from write_translation import write_translated`
- `write_translated("Map0020.txt.trans.txt", ["1. [MARKER: Message] 以藏「", "翻譯內容...", ...])`

---

## 固定人名對照表（嚴格遵守）

| 日文原文 | 繁體中文譯名 |
|----------|------------|
| イゾウ | 以藏 |
| オスカー | 奧斯卡 |
| DANDY | DANDY（保留） |
| ﾁｮﾁｮﾘｰﾅ / チョチョリーナ | 喬喬莉娜 |
| 流漸 | 流漸（漢字保留） |
| オンドレ | 安德烈 |
| ベア | 貝爾 |
| マサル | 阿勝 |
| 真っ黒 | 漆黑 |
| アルフ | 阿爾夫 |
| リード＝アレン | 里德・艾倫 |
| リード | 里德 |
| ナポレオン | 拿破崙 |
| ウィルス | 病毒 |
| ベルサイユ | 凡爾賽 |
| バスチーユ | 巴士底 |
| エルミ | 艾爾米 |
| ネオ＝ジャパン | 新日本 |

---

## 各檔案翻譯狀態

> 圖例：✅ AI翻譯完成 | ⚠️ Google機翻（需重翻） | ❌ 未翻譯

### Database 資料庫檔案

| 檔案 | 狀態 | 備註 |
|------|------|------|
| Database_Animations.txt | ✅ AI翻譯完成 | 動畫名稱 |
| Database_Attributes.txt | ✅ AI翻譯完成 | 屬性名（劍/槍/炎等） |
| Database_ChipSet.txt | ✅ AI翻譯完成 | 地圖元件組名 |
| Database_Commons_Common0001.txt | ✅ AI翻譯完成 | 公共事件 |
| Database_Conditions.txt | ✅ AI翻譯完成 | 狀態異常 |
| Database_Hero.txt | ✅ AI翻譯完成 | 角色名/職稱 |
| Database_Items.txt | ✅ AI翻譯完成 | 道具名/說明 |
| Database_Monsters.txt | ✅ AI翻譯完成 | 怪物名 |
| Database_Skills.txt | ✅ AI翻譯完成 | 技能名/說明 |
| Database_Terrain.txt | ✅ AI翻譯完成 | 地形名 |
| Database_Troops.txt | ✅ AI翻譯完成 | 戰鬥對話 |
| Database_Vocab.txt | ✅ AI翻譯完成 | 系統詞彙 |

### Map 地圖事件檔案

| 檔案 | 狀態 | 場景說明 |
|------|------|---------|
| Map0001.txt | ✅ AI翻譯完成 | 廢墟凡爾賽城外 |
| Map0002.txt | ✅ AI翻譯完成 | 凡爾賽城鎮（街道/監獄城） |
| Map0003.txt | ✅ AI翻譯完成 | 安德烈的家（治癒雞） |
| Map0004.txt | ✅ AI翻譯完成 | 遊戲開場動畫 |
| Map0005.txt | ✅ AI翻譯完成 | 奧斯卡宅邸（接任務） |
| Map0006.txt | ✅ AI翻譯完成 | 法國城堡（調查英國艦隊） |
| Map0007.txt | ✅ AI翻譯完成 | 艾爾米港鎮（船舶中心） |
| Map0009.txt | ✅ AI翻譯完成 | 艾爾米酒吧（流浪鋼琴師） |
| Map0010.txt | ✅ AI翻譯完成 | 小商店 |
| Map0011.txt | ✅ AI翻譯完成 | DANDY & 喬喬莉娜 vs 阿拉斯托爾 |
| Map0012.txt | ✅ AI翻譯完成 | 港口船邊 |
| Map0020.txt | ✅ AI翻譯完成 | 英國城鎮（外牆區） |
| Map0021.txt | ✅ AI翻譯完成 | 英國高台旅館 |
| Map0022.txt | ✅ AI翻譯完成 | 民宅 |
| Map0025.txt | ✅ AI翻譯完成 | 英國城堡前船務中心 |
| Map0026.txt | ✅ AI翻譯完成 | 印度城鎮（湖面跳板） |
| Map0027.txt | ✅ AI翻譯完成 | 埃及（喬喬莉娜加入） |
| Map0028.txt | ✅ AI翻譯完成 | 新日本機械都市（接受潛入任務） |
| Map0029.txt | ✅ AI翻譯完成 | 中國城鎮 |
| Map0030.txt | ✅ AI翻譯完成 | 上鎖的門 |
| Map0031.txt | ✅ AI翻譯完成 | 蘇聯邊境梯子事件 |
| Map0032.txt | ✅ AI翻譯完成 | 澳洲小村 |
| Map0033.txt | ✅ AI翻譯完成 | 丹迪神殿入口（阿勝加入） |
| Map0034.txt | ✅ AI翻譯完成 | 神殿試練之間 |
| Map0035.txt | ✅ AI翻譯完成 | 丹迪神殿內部與DANDY |
| Map0036.txt | ✅ AI翻譯完成 | 瑪麗研究室大決戰（流漸覺醒） |
| Map0037.txt | ✅ AI翻譯完成 | 巴士底監獄迷宮走廊 |
| Map0038.txt | ✅ AI翻譯完成 | 巴士底監獄牢房 |
| Map0039.txt | ✅ AI翻譯完成 | 新日本城市（機械商店） |
| Map0040.txt | ✅ AI翻譯完成 | 新生新日本號船艙內部 |
| Map0041.txt | ✅ AI翻譯完成 | 上鎖的門 |
| Map0042.txt | ✅ AI翻譯完成 | 印度民家與機工士 |
| Map0043.txt | ✅ AI翻譯完成 | 中國巨船港口 |
| Map0045.txt | ✅ AI翻譯完成 | 中國巨船內部通道 |
| Map0046.txt | ✅ AI翻譯完成 | 中國巨船內部旋轉地板 |
| Map0047.txt | ✅ AI翻譯完成 | 中國巨船內部監獄/兵營 |
| Map0048.txt | ✅ AI翻譯完成 | 中國巨船內部 ID卡房間 |
| Map0050.txt | ✅ AI翻譯完成 | 中國皇宮（末代皇帝與約會） |
| Map0052.txt | ✅ AI翻譯完成 | 打開大門 |
| Map0053.txt | ✅ AI翻譯完成 | 印度市區房屋與倉庫 |
| Map0054.txt | ✅ AI翻譯完成 | 澳洲小村後方路徑 |
| Map0055.txt | ✅ AI翻譯完成 | 神殿騎士指示 |
| Map0056.txt | ✅ AI翻譯完成 | 澳洲小村旅館 |
| Map0057.txt | ✅ AI翻譯完成 | 澳洲小村第一次見DANDY |
| Map0058.txt | ✅ AI翻譯完成 | 新日本核心電腦室（大型場景） |
| Map0059.txt | ✅ AI翻譯完成 | 印度酒吧 |
| Map0061.txt | ✅ AI翻譯完成 | 印度酒吧後台（護胸甲裝備） |
| Map0062.txt | ✅ AI翻譯完成 | 中國城鎮民家與商人 |
| Map0063.txt | ✅ AI翻譯完成 | 中國城鎮民家2 |
| Map0064.txt | ✅ AI翻譯完成 | 中國城鎮老婆婆家 |
| Map0065.txt | ✅ AI翻譯完成 | 中國巨船港口防線（遭遇中國兵團） |
| Map0066.txt | ✅ AI翻譯完成 | 中國城鎮旅店與餐廳 |
| Map0067.txt | ✅ AI翻譯完成 | 精神世界門口 |
| Map0070.txt | ✅ AI翻譯完成 | 流漸精神世界1（大戰記憶） |
| Map0072.txt | ✅ AI翻譯完成 | 流漸精神世界2（遭遇病毒） |
| Map0073.txt | ✅ AI翻譯完成 | 精神世界脫逃 |
| Map0074.txt | ✅ AI翻譯完成 | 流漸精神世界（病毒戰） |
| Map0076.txt | ✅ AI翻譯完成 | 拿破崙的真面目與安德烈救場 |
| Map0078.txt | ✅ AI翻譯完成 | 以藏視角（阻礙通行） |
| Map0079.txt | ✅ AI翻譯完成 | 核心電腦室（與 GODZILLER 的對話） |
| Map0080.txt | ✅ AI翻譯完成 | 拿破崙與 JOKER 殺害複製人流漸 |
| Map0081.txt | ✅ AI翻譯完成 | 被士兵發現1 |
| Map0082.txt | ✅ AI翻譯完成 | 被士兵發現2 |
| Map0083.txt | ✅ AI翻譯完成 | 被擊暈的士兵 |
| Map0084.txt | ✅ AI翻譯完成 | 時間異常的世界（安德烈與貝爾尋找以藏） |
| Map0085.txt | ✅ AI翻譯完成 | 澳洲小村咖啡廳 Brother Soul |
| Map0086.txt | ✅ AI翻譯完成 | 遭受襲擊後的澳洲小村 |
| Map0087.txt | ✅ AI翻譯完成 | 地下丹迪神殿入口盤查 |
| Map0088.txt | ✅ AI翻譯完成 | 埃及港口開港與各角色重逢 |
| Map0089.txt | ✅ AI翻譯完成 | 埃及港口買票出海與世界局勢變動 |
| Map0090.txt | ✅ AI翻譯完成 | 遭遇海難漂流 |
| Map0091.txt | ✅ AI翻譯完成 | 俄羅斯基地（阿爾夫的委託與阻擊，大型場景） |
| Map0093.txt | ✅ AI翻譯完成 | 獲得管理室鑰匙 |
| Map0094.txt | ✅ AI翻譯完成 | 舊水道與地下牢房 |
| Map0096.txt | ✅ AI翻譯完成 | 偏僻小村的日常與老頭們的相聲 |
| Map0097.txt | ✅ AI翻譯完成 | 以藏的夢境與媽媽的聲音 |
| Map0098.txt | ✅ AI翻譯完成 | 科洛愛的款待與以藏身世的暗示 |
| Map0099.txt | ✅ AI翻譯完成 | 村長與格鬥家鮎的情報 |
| Map0100.txt | ✅ AI翻譯完成 | 特產商販 |
| Map0101.txt | ✅ AI翻譯完成 | 格鬥家鮎加入隊伍 |
| Map0103.txt | ✅ AI翻譯完成 | 獲得米修拉爾系列裝備 |
| Map0104.txt | ✅ AI翻譯完成 | 澳洲小村城鎮民家 |
| Map0105.txt | ✅ AI翻譯完成 | 澳洲小村城鎮路人 |
| Map0106.txt | ✅ AI翻譯完成 | 蘇聯大總統辦公室（戈巴契夫大戰與戈爾比公主） |
| Map0107.txt | ✅ AI翻譯完成 | 旅店休息 |
| Map0109.txt | ✅ AI翻譯完成 | 逃獄回憶與爭吵 |
| Map0111.txt | ✅ AI翻譯完成 | 排水溝提示 |
| Map0112.txt | ✅ AI翻譯完成 | 獲得托馬霍克 |
| Map0114.txt | ✅ AI翻譯完成 | 水流聲提示 |
| Map0115.txt | ✅ AI翻譯完成 | JOKER求救 |
| Map0116.txt | ✅ AI翻譯完成 | 救出 DANDY 與 JOKER 的搶奪聖劍 |
| Map0118.txt | ✅ AI翻譯完成 | 獲得無畏聖劍與佐助的引路 |
| Map0119.txt | ✅ AI翻譯完成 | 出發提示 |
| Map0120.txt | ✅ AI翻譯完成 | 奧斯卡身世揭曉與世界局勢劇變（關鍵劇情） |
| Map0121.txt | ✅ AI翻譯完成 | 獲得盆栽 |
| Map0122.txt | ✅ AI翻譯完成 | 建設中的工地 |
| Map0123.txt | ✅ AI翻譯完成 | JOKER 被流漸必殺技擊敗 |
| Map0125.txt | ✅ AI翻譯完成 | 安德烈坐在王座上 |
| Map0128.txt | ✅ AI翻譯完成 | 拿破崙大殿對決與幕後黑手現身（大型場景，關鍵劇情） |
| Map0130.txt | ✅ AI翻譯完成 | 神殿地下咖啡廳對話與戰前決心 |
| Map0131.txt | ✅ AI翻譯完成 | 魔法劍士購買斬斷光芒之劍 |
| Map0132.txt | ✅ AI翻譯完成 | 最終迷宮突入與幕後黑手談論 DANDY 身世 |
| Map0135.txt | ✅ AI翻譯完成 | 最終 BOSS 戰（丹達里恩戰，大型場景，關鍵劇情） |
| Map0140.txt | ✅ AI翻譯完成 | 世外桃源森林村莊與喬喬莉娜收服龍小弟 |
| Map0141.txt | ✅ AI翻譯完成 | 故障的主電腦與獲得流漸莫比烏斯之刃 |
| Map0142.txt | ✅ AI翻譯完成 | 神殿強者試練之間 |
| Map0143.txt | ✅ AI翻譯完成 | 智力試練（天使階級與所司之理謎題，大型場景） |
| Map0144.txt | ✅ AI翻譯完成 | 敏捷之間入口與說明 |
| Map0146.txt | ✅ AI翻譯完成 | 敏捷試練通過判定 |
| Map0147.txt | ✅ AI翻譯完成 | 敏捷挑戰中與判定 |
| Map0148.txt | ✅ AI翻譯完成 | 印度民居與咖哩倉庫 |
| Map0149.txt | ✅ AI翻譯完成 | 印度皇宮與咖哩神教對話 |
| Map0150.txt | ✅ AI翻譯完成 | 印度市區民居 |
| Map0151.txt | ✅ AI翻譯完成 | 法國港口售票處船票購買 |
| Map0152.txt | ✅ AI翻譯完成 | 里德精銳對陣克羅塞爾 |
| Map0153.txt | ✅ AI翻譯完成 | 新手村酒吧懸賞單與委託（開頭與多週目設定） |
| Map0154.txt | ✅ AI翻譯完成 | 以藏床前驚醒，夢見與拿破崙之對話 |
| Map0155.txt | ✅ AI翻譯完成 | 損壞的主電腦與結局探索 |
| Map0156.txt | ✅ AI翻譯完成 | 巨大飛空艇新日本號與突擊準備（大型場景，關鍵劇情） |
| Map0157.txt | ✅ AI翻譯完成 | 飛空艇廁所，獲得超強力馬達 |
| Map0158.txt | ✅ AI翻譯完成 | 飛空艇引導與埃及魔劍莫比烏斯之刃封印位置 |
| Map0159.txt | ✅ AI翻譯完成 | 封印魔劍的丹迪試煉門 |
| Map0161.txt | ✅ AI翻譯完成 | 魔劍保管庫與管理人 |
| Map0162.txt | ✅ AI翻譯完成 | 回憶/幻影，小奧與捉迷藏小女孩 |
| Map0163.txt | ✅ AI翻譯完成 | 培養槽與人造人實驗人偶 |
| Map0165.txt | ✅ AI翻譯完成 | 安德烈與以藏異空間會合 |
| Map0166.txt | ✅ AI翻譯完成 | 異空間遇見貝爾，貝爾加入 |
| Map0167.txt | ✅ AI翻譯完成 | 異空間遇到奧爾貝與約定（支線高潮劇情） |
| Map0168.txt | ✅ AI翻譯完成 | 異空間崩壞民居對話 |
| Map0171.txt | ✅ AI翻譯完成 | 突擊美國最大出力 |
| Map0172.txt | ✅ AI翻譯完成 | 美國突入防禦網，流漸英勇犧牲（大型場景，關鍵劇情） |
| Map0174.txt | ✅ AI翻譯完成 | 以藏的故鄉村莊借宿 |
| Map0175.txt | ✅ AI翻譯完成 | 英國核彈室與尋找流漸的緣起 |
| Map0176.txt | ✅ AI翻譯完成 | 以藏故鄉，與老哥安德烈對話（大型場景，學會熱血兄貴大行進） |
| Map0178.txt | ✅ AI翻譯完成 | 獲得大師神衣 |
| Map0180.txt | ✅ AI翻譯完成 | 裝備與道具合成大師對話（大型場景） |
| Map0204.txt | ✅ AI翻譯完成 | 稀有商品商人對話 |

---

## 給下一個接手模型的指引

### 接手步驟
1. 閱讀本文件確認目前進度
2. 讀取 `scratch/to_translate/<檔名>.trans.txt` 取得原始日文
3. 自行翻譯（不使用外部API）
4. 使用 `write_translated()` 函式寫入 `.translated.txt`
5. 更新本文件的進度表（將 ⚠️ 改為 ✅）
6. 全部完成後執行：`python scratch/import_all.py`

### 範例翻譯腳本結構
```python
# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from write_translation import write_translated

write_translated("Map0020.txt.trans.txt", [
    "1. [MARKER: Message] 以藏「",
    "好燙！！！",
    "2. [MARKER: Message] 男子「",
    "這樣看著火……",
    # ... 繼續翻譯
])
```

### 優先處理順序（建議）
1. 優先翻譯 Database 剩餘檔案（較小，且影響全域顯示）
2. 再按 Map 編號由小到大依序翻譯
3. 大型場景（Map0058、Map0091、Map0128、Map0135、Map0143、Map0156、Map0176、Map0180）最後處理

### 最後更新
- 日期：2026-05-21（持續更新中）
- 已完成：140 個檔案（Database ×2 + Map ×138，全部完成！）
- 待完成：0 個檔案（🎉 全文本 AI 翻譯寫入完畢！）
