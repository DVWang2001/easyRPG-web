# -*- coding: utf-8 -*-
"""翻譯寫入 - Map0204"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from write_translation import write_translated

# Map0204 (稀有商品商人)
write_translated("Map0204.txt.trans.txt", [
    "1. [MARKER: Message] 男子「",
    "喔喔，真是久違的稀客啊！！\\.",
    "來來，我這裡賣的可都是罕見的稀有商品喔，",
    "請務必捧場買一些回去吧！！",
])

print("Map0204 done.")
