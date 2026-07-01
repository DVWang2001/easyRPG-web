# -*- coding: utf-8 -*-
"""翻譯寫入 - Map0062~0066"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from write_translation import write_translated

# Map0062 (中國城鎮民家與商人)
write_translated("Map0062.txt.trans.txt", [
    "1. [MARKER: Message] 商人「",
    "下次，我打算去這裡東北邊的「中國」",
    "推銷商品呢。",
    "2. [MARKER: Message] 商人「",
    "所以旅行的必需品「回復符」，",
    "不多買一點可不行呢。",
    "3. [MARKER: Message] 商人「",
    "如果各位也是旅人，",
    "請不要疏忽了準備喔。",
    "不然之後可是會吃苦頭的。",
    "4. [MARKER: Message] 男子「",
    "穿著這種裝備，",
    "真的能走路嗎……。",
    "5. [MARKER: Message] 戰士「",
    "如果穿上堅固的鎧甲，雖然不怕敵人的攻擊，",
    "但敏捷度就會下降……。",
    "6. [MARKER: Message] 戰士「",
    "\\.……\\.……\\.……但要是穿輕裝，又不知道能不能扛得住魔物的攻擊……。",
    "唔～～嗯……真是兩難啊……。",
])

# Map0063 (中國城鎮民家2)
write_translated("Map0063.txt.trans.txt", [
    "1. [MARKER: Message] 女子「",
    "我丈夫正在海邊",
    "生營火喔。",
    "2. [MARKER: Message] 女子「",
    "這個國家的戰爭，到底什麼時候才會結束呢……。",
])

# Map0064 (中國城鎮老婆婆家)
write_translated("Map0064.txt.trans.txt", [
    "1. [MARKER: Message] 老婆婆「",
    "最近房子周圍總有小孩在徘徊……。",
    "是有什麼事情嗎……。",
    "2. [MARKER: Message] 老婆婆「",
    "最近在房子周圍徘徊的小孩，",
    "已經不見了喔。",
    "3. [MARKER: Message] 老婆婆「",
    "人一走，多多少少又會覺得有些寂寞呢。",
])

# Map0065 (中國巨船港口防線 - 遭遇中國兵團)
write_translated("Map0065.txt.trans.txt", [
    "1. [MARKER: Message] 以藏「",
    "嗯？",
    "2. [MARKER: Message] 士兵「",
    "可不能讓你們再往前走一步！！！",
    "3. [MARKER: Message] 奧斯卡「",
    "果然還是被捷足先登了嗎……。",
    "4. [MARKER: Message] 以藏「",
    "\\S[2]真是有夠麻煩的……。",
    "5. [MARKER: Message] 士兵「",
    "賭上我們「中國兵團」的名號，",
    "一定要排除入侵者！！！",
    "6. [MARKER: Message] 士兵「",
    "\\S[2]願榮光歸於中國！！！",
    "7. [MARKER: Message] 奧斯卡「",
    "要是可以，本來想悄悄解決的呢。",
    "8. [MARKER: Message] 以藏「",
    "明明那麼招搖地入侵，虧你說得出這種話……。",
    "9. [MARKER: Message] 奧斯卡「",
    "\\S[2]……總……總而言之，",
    "我們先前進吧。",
    "10. [MARKER: Message] 以藏「",
    "嗯？",
    "11. [MARKER: Message] 士兵「",
    "可不能讓你們再往前走一步！！！",
    "12. [MARKER: Message] 奧斯卡「",
    "果然還是被捷足先登了嗎……。",
    "13. [MARKER: Message] 以藏「",
    "\\S[2]真是有夠麻煩的……。",
    "14. [MARKER: Message] 士兵「",
    "賭上我們「中國兵團」的名號，",
    "一定要排除入侵者！！！",
    "15. [MARKER: Message] 士兵「",
    "\\S[2]願榮光歸於中國！！！",
])

# Map0066 (中國城鎮旅店與餐廳)
write_translated("Map0066.txt.trans.txt", [
    "1. [MARKER: Message] 旅店老闆娘「",
    "客人，請不要進去那裡！",
    "2. [MARKER: Message] 旅店老闆娘「",
    "客人，請不要進去那裡！",
    "3. [MARKER: Message] 店主「",
    "歡迎光臨，中華餐廳",
    "在這一邊喔。",
    "4. [MARKER: Message] 老爺爺「",
    "\\S[3]難……\\.難吃……。",
    "5. [MARKER: Message] 女子「",
    "我家爺爺啊，不管吃什麼",
    "都會說「難吃」呢。\\.",
    "是不是年輕的時候，吃過相當不得了的美食呢……。",
    "6. [MARKER: Message] 小孩「",
    "\\C[5]\\>太美味了！！\\<",
    "7. [MARKER: Message] 母親「",
    "我們家這孩子，完全不挑食，",
    "什麼都吃喔！",
    "8. [MARKER: Message] 父親「",
    "什麼都吃是很好啦，",
    "但前陣子他差點把輪胎給吞下去，",
    "真是嚇死我了……。",
    "9. [MARKER: Message] 女服務生「",
    "這裡不管過多久，生意都好不起來呢\\.……這裡……。\\.",
    "我是不是該考慮重新找工作了呢……。",
])

print("Map0062-0066 done.")
