# -*- coding: utf-8 -*-
"""翻譯寫入 - Map0101~0105"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from write_translation import write_translated

# Map0101 (格鬥家鮎加入隊伍)
write_translated("Map0101.txt.trans.txt", [
    "1. [MARKER: Message] 武術家「",
    "去中國修練拳法的弟弟，",
    "不知道最近過得還好嗎……。",
    "2. [MARKER: Message] 鮎「",
    "沒錯，我就是\|\^",
    "3. [MARKER: Message] 鮎「",
    "不過……找我有何貴幹啊？",
    "4. [MARKER: Message] 以藏「",
    "聽說，你在北美洲那邊看到了城堡的蹤影……。",
    "5. [MARKER: Message] 鮎「",
    "喔，對啊！因為只有我一個人看到，",
    "所以根本就沒有人相信我……。",
    "6. [MARKER: Message] 鮎「",
    "那正好是我在進行環美大陸馬拉松的",
    "時候發生的事……。",
    "7. [MARKER: Message] 鮎「",
    "我真的看到了喔，\\.在傳聞中什麼都沒有的",
    "美國東北部岩山之中，有座城堡……！！！",
    "8. [MARKER: Message] 鮎「",
    "而且，那可不是普通城堡！",
    "那座城堡竟然是懸空漂浮著的喔！",
    "9. [MARKER: Message] 奧斯卡「",
    "很可疑呢，\\.非常可疑。",
    "10. [MARKER: Message] 以藏「",
    "是啊，有股那群陰險傢伙的臭味撲鼻而來呢。",
    "11. [MARKER: Message] 鮎「",
    "你們幾個……難道正在尋找那座城堡嗎！？\\.",
    "說不定我看到的只是幻覺而已喔！",
    "12. [MARKER: Message] 以藏「",
    "是不是幻覺，等調查過後再說。\\.",
    "現在，我們最需要的就是情報。",
    "13. [MARKER: Message] 鮎「",
    "\\S[2]……。\\|",
    "吶，\\.\S[1]也能帶我一起去嗎？",
    "14. [MARKER: Message] 以藏「",
    "\\|哈？",
    "15. [MARKER: Message] 鮎「",
    "既然你們是要去確認我說的話，那我也",
    "多少會感到有點責任在呢。",
    "16. [MARKER: Message] 鮎「",
    "所以，我要用我自己的雙眼去確認。\\.",
    "我看到的到底是不是真的……。",
    "17. [MARKER: Message] 以藏「",
    "不行，這對你們一般人來說太危險了。",
    "18. [MARKER: Message] 鮎「",
    "這點你可以放心。\\.",
    "我可不是笨蛋。",
    "如果有危險的話，我會自己保護好自己的。",
    "19. [MARKER: Message] 奧斯卡「",
    "以藏，現在沒時間在這種地方磨蹭了。\\.",
    "既然他都這麼說了，帶上他也無妨。",
    "20. [MARKER: Message] 鮎「",
    "那邊的大姐還挺明事理的嘛。\\.",
    "喲西！ 那就決定囉！",
    "21. [MARKER: Message] 奧斯卡「",
    "不過，我們可沒空去保護你喔。",
    "這點請你先想清楚，我們才會帶你去的。",
    "22. [MARKER: Message] 鮎「",
    "啊啊，那是當然的囉。",
    "23. [MARKER: Message] ",
    "　　　　　就這樣帶上了鮎，以藏一行人",
    "　　　　　　回到了新日本號上。",
])

# Map0103 (獲得米修拉爾系列裝備)
write_translated("Map0103.txt.trans.txt", [
    "1. [MARKER: Message] ",
    "　　　　　　　　獲得了魔神劍！！",
    "2. [MARKER: Message] ",
    "　　　　　獲得了米修拉爾戒指！！",
    "3. [MARKER: Message] ",
    "　　　　　獲得了米修拉爾頭盔！！",
    "4. [MARKER: Message] ",
    "　　　　　獲得了米修拉爾爪！！",
])

# Map0104 (澳洲小村城鎮民家)
write_translated("Map0104.txt.trans.txt", [
    "1. [MARKER: Message] 侍從「",
    "聽說在這個村子，在丹迪神殿建成之前，",
    "只是一片普通的草原呢。",
])

# Map0105 (澳洲小村城鎮路人)
write_translated("Map0105.txt.trans.txt", [
    "1. [MARKER: Message] 男子「",
    "哎呀，你們各位也是要去丹迪神殿的嗎？",
    "最近去的人真是越來越多了呢……。",
])

print("Map0101-0105 done.")
