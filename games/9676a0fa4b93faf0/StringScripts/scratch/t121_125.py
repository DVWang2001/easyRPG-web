# -*- coding: utf-8 -*-
"""翻譯寫入 - Map0121~0125"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from write_translation import write_translated

# Map0121 (獲得盆栽)
write_translated("Map0121.txt.trans.txt", [
    "1. [MARKER: Message] ",
    "　　　　　　　　　獲得了盆栽！！",
])

# Map0122 (建設中的工地)
write_translated("Map0122.txt.trans.txt", [
    "1. [MARKER: Message] 士兵「",
    "這裡還在建設中。",
    "太危險了，請勿靠近。",
    "2. [MARKER: Message] 士兵「",
    "這裡還在建設中。",
    "太危險了，請勿靠近。",
    "3. [MARKER: Message] 男子「",
    "這裡到底會蓋出什麼東西來呢……。",
    "4. [MARKER: Message] 工地主任「",
    "餵！你在偷懶什麼啊！！",
    "……哎呀，真是失禮了……。",
])

# Map0123 (JOKER被流漸必殺技擊敗)
write_translated("Map0123.txt.trans.txt", [
    "1. [MARKER: Message] JOKER「",
    "呼……呼……逃到這裡的話應該就沒事了吧……。",
    "2. [MARKER: Message] JOKER「",
    "可……可惡……。",
    "唯獨你們這幫人……。",
    "3. [MARKER: Message] JOKER「",
    "D……DANDY……你這……！！！",
    "嘎哈ッ！！！！",
    "4. [MARKER: Message] DANDY「",
    "……JOKER……。",
    "5. [MARKER: Message] ",
    "　　　　　　獲得了丹迪盾牌！",
    "6. [MARKER: Message] 流漸「",
    "哈哈哈！你逃不掉的！！",
    "7. [MARKER: Message] JOKER「",
    "哇啊啊——！！別過來啊怪物！！！",
    "8. [MARKER: Message] 流漸「",
    "讓你瞧瞧我的必殺技！！",
    "見識了就受死吧！！！！",
    "9. [MARKER: Message] 流漸「",
    "哈啊啊————！！！！",
    "10. [MARKER: Message] JOKER「",
    "住手啊啊啊啊——————！！！",
    "11. [MARKER: Message] JOKER「",
    "\\S[2]………………………………………………。",
    "12. [MARKER: Message] 流漸「",
    "哼……！！！",
])

# Map0125 (安德烈坐在王座上)
write_translated("Map0125.txt.trans.txt", [
    "1. [MARKER: Message] 安德烈「",
    "這裡的王座，坐起來還挺舒服的呢～。",
])

print("Map0121-0125 done.")
