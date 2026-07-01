# -*- coding: utf-8 -*-
"""翻譯寫入 - Map0111~0115"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from write_translation import write_translated

# Map0111 (排水溝提示)
write_translated("Map0111.txt.trans.txt", [
    "1. [MARKER: Message] ",
    "　　　　　底部隱約能看見類似排水溝的東西。",
    "　　　　　　 但現在似乎是關閉著的。",
])

# Map0112 (獲得托馬霍克)
write_translated("Map0112.txt.trans.txt", [
    "1. [MARKER: Message] ",
    "　　　　　　　獲得了托馬霍克！！",
])

# Map0114 (水流聲提示)
write_translated("Map0114.txt.trans.txt", [
    "1. [MARKER: Message] ",
    "　　　　　某處傳來了水流的聲音。",
    "2. [MARKER: Message] ",
    "　　　　　某處傳來了水流的聲音。",
])

# Map0115 (JOKER求救)
write_translated("Map0115.txt.trans.txt", [
    "1. [MARKER: Message] JOKER「",
    "救命啊～～～！！",
])

print("Map0111-0115 done.")
