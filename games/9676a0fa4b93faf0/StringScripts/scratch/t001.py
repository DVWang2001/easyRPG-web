# -*- coding: utf-8 -*-
"""翻譯寫入 - Map0001, Map0003, Map0004"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from write_translation import write_translated

# ─────────────────────────────────────────────
# Map0001  (廢墟凡爾賽城外)
# ─────────────────────────────────────────────
write_translated("Map0001.txt.trans.txt", [
    "1. [MARKER: Message] 以藏「",
    "凡爾賽……？",
    "全毀了……。",
    "2. [MARKER: Message] 喬喬莉娜「",
    "丹迪大人，去找他——$g",
    "3. [MARKER: Message] ",
    "廢墟一片，根本無法進入。",
])

# ─────────────────────────────────────────────
# Map0003  (安德烈的家／治癒雞)
# ─────────────────────────────────────────────
write_translated("Map0003.txt.trans.txt", [
    "1. [MARKER: Message] 安德烈「",
    "嘿——！奧斯卡！！",
    "2. [MARKER: Message] 雞「",
    "咕——咕——！！！",
    "3. [MARKER: Message] 以藏「",
    "好燙！！",
    "4. [MARKER: Message] 奧斯卡「",
    "真的很熱。",
    "5. [MARKER: Message] 以藏「",
    "要不要稍微休息一下？",
    "6. [MARKER: Message] 奧斯卡「",
    "雖然是以藏的家……可以休息一下嗎？",
    "7. [MARKER: Message] 雞「",
    "咕——咕——！！",
    "8. [MARKER: Message] 以藏「",
    "大哥，我一直很好奇，",
    "這隻雞到底是怎麼回事？",
    "9. [MARKER: Message] 安德烈「",
    "那可不得了，這傢伙聲帶有治癒效果，",
    "是全世界只有一隻的珍貴雞。",
    "10. [MARKER: Message] 安德烈「",
    "是我以前旅行時發現的。",
    "光聽牠的聲音就能消除疲勞。",
    "11. [MARKER: Message] 雞「",
    "咕——咕——！！！",
    "12. [MARKER: Message] ",
    "　　　　　　　　　　全員回復！！",
    "13. [MARKER: Message] [FACE: 主人公2, 10, Left, Normal] 安德烈「",
    "醒了嗎，以藏。\\.",
    "雖然有點突然，但公會傳來",
    "通知了。",
    "14. [MARKER: Message] [FACE: イゾウ, 1, Right, Flip Horizontal] 以藏「",
    "反正肯定是奧斯卡吧……",
    "15. [MARKER: Message] [FACE: Erase] 安德烈「",
    "真好啊你，被心愛的奧斯卡差來差去……",
    "16. [MARKER: Message] [FACE: Erase] 以藏「",
    "把他當心愛的",
    "是大哥你吧？",
    "17. [MARKER: Message] [FACE: Erase] 安德烈「",
    "……呃……$g……",
    "18. [MARKER: Message] [FACE: Erase] 以藏「",
    "………………………………",
    "總之我先去了。",
    "19. [MARKER: Message] [FACE: Erase] 安德烈「",
    "去之前先存個檔！",
    "20. [MARKER: Message] [FACE: Erase] 安德烈「",
    "先存個檔吧。",
])

# ─────────────────────────────────────────────
# Map0004  (開場動畫 / 遊戲標題)
# ─────────────────────────────────────────────
write_translated("Map0004.txt.trans.txt", [
    "1. [MARKER: Message] ",
    "　　　　　　　　　　　\\S[2]您……",
    "2. [MARKER: Message] ",
    "　　　　　\\S[2]您曾有過這樣的感覺嗎？",
    "3. [MARKER: Message] ",
    "　　　　　Ｓｏｕｌ　Ｏｆ　Ｄａｎｄｉｚｕｍ",
    "4. [MARKER: Message] ",
    "　　　　　　新曆２０３年　８月１５日",
    "5. [MARKER: Message] ",
    "　　　　　這個故事，從監獄都市凡爾賽的",
    "　　　　　一間「萬事屋」的早晨開始……",
    "6. [MARKER: Message] ＊「",
    "喂——起床啦——！！",
    "7. [MARKER: Message] ＊「",
    "唔……嗯……",
    "好睏……",
    "8. [MARKER: Message] \\N[1]「",
    "呼啊啊啊，睡眠不足……",
])

print("Map0001 / Map0003 / Map0004 done.")
