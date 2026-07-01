# -*- coding: utf-8 -*-
"""批次二：Conditions、Attributes、Terrain、ChipSet"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from write_translation import write_translated

# ============================================================
# Database_Conditions.txt  （狀態異常）
# ============================================================
write_translated("Database_Conditions.txt.trans.txt", [
    "1. [TAG: Name] 戰鬥不能",
    "2. [TAG: InflictedOnAlly] 倒下了！",
    "3. [TAG: InflictedOnEnemy] 擊倒了！",
    "4. [TAG: Recovered] 站起來了！",
    "5. [TAG: Name] 中毒",
    "6. [TAG: InflictedOnAlly] 中毒了！",
    "7. [TAG: InflictedOnEnemy] 中毒了！",
    "8. [TAG: AlreadyInflicted] 已經中毒了！",
    "9. [TAG: Recovered] 毒解除了！",
    "10. [TAG: Name] 黑暗",
    "11. [TAG: InflictedOnAlly] 陷入黑暗中！",
    "12. [TAG: InflictedOnEnemy] 陷入黑暗中！",
    "13. [TAG: AlreadyInflicted] 已陷入黑暗！",
    "14. [TAG: Recovered] 黑暗消散了！",
    "15. [TAG: Name] 沉默",
    "16. [TAG: InflictedOnAlly] 沉默了！",
    "17. [TAG: InflictedOnEnemy] 使其沉默！",
    "18. [TAG: AlreadyInflicted] 已陷入沉默！",
    "19. [TAG: Recovered] 沉默解除了！",
    "20. [TAG: Name] 暴走",
    "21. [TAG: InflictedOnAlly] 暴走了！",
    "22. [TAG: InflictedOnEnemy] 使其暴走！",
    "23. [TAG: AlreadyInflicted] 已在暴走中！",
    "24. [TAG: Recovered] 恢復理智了！",
    "25. [TAG: Name] 混亂",
    "26. [TAG: InflictedOnAlly] 陷入混亂！",
    "27. [TAG: InflictedOnEnemy] 使其混亂！",
    "28. [TAG: AlreadyInflicted] 已陷入混亂！",
    "29. [TAG: Recovered] 恢復理智了！",
    "30. [TAG: Name] 睡眠",
    "31. [TAG: InflictedOnAlly] 睡著了！",
    "32. [TAG: InflictedOnEnemy] 使其入睡！",
    "33. [TAG: AlreadyInflicted] 已經睡著了！",
    "34. [TAG: Continuing] 正在沉睡中……",
    "35. [TAG: Recovered] 清醒過來了！",
    "36. [TAG: Name] 麻痺",
    "37. [TAG: InflictedOnAlly] 麻痺無法動彈！",
    "38. [TAG: InflictedOnEnemy] 使其麻痺！",
    "39. [TAG: AlreadyInflicted] 已陷入麻痺！",
    "40. [TAG: Continuing] 麻痺無法動彈！",
    "41. [TAG: Recovered] 麻痺解除了！",
    "42. [TAG: Name] 踉蹌",
    "43. [TAG: InflictedOnAlly] 失去平衡了！",
    "44. [TAG: InflictedOnEnemy] 失去平衡了！",
    "45. [TAG: Continuing] 正在踉蹌……",
    "46. [TAG: Recovered] 正在踉蹌……",
    "47. [TAG: Name] 震驚",
    "48. [TAG: InflictedOnAlly] 嚇得愣住了！",
    "49. [TAG: InflictedOnEnemy] 嚇得愣住了！",
    "50. [TAG: Continuing] 愣在原地……",
    "51. [TAG: Recovered] 愣在原地……",
    "52. [TAG: Name] 貧血",
    "53. [TAG: InflictedOnAlly] 貧血發作了！",
    "54. [TAG: InflictedOnEnemy] 陷入貧血！",
    "55. [TAG: AlreadyInflicted] 看起來還頭暈目眩",
    "56. [TAG: Continuing] 「血不夠了……",
    "57. [TAG: Recovered] 從貧血中恢復了！",
    "58. [TAG: Name] 精神汙染",
    "59. [TAG: InflictedOnAlly] 被詛咒了！",
    "60. [TAG: InflictedOnEnemy] 被詛咒了！",
    "61. [TAG: AlreadyInflicted] 已經被詛咒了！",
    "62. [TAG: Recovered] 詛咒解除了！",
    "63. [TAG: Name] 石化",
    "64. [TAG: InflictedOnAlly] 身體正在石化！",
    "65. [TAG: InflictedOnEnemy] 身體正在石化！",
    "66. [TAG: AlreadyInflicted] 已經石化了。",
    "67. [TAG: Recovered] 身體恢復原狀了！",
])

# ============================================================
# Database_Attributes.txt  （屬性）
# ============================================================
write_translated("Database_Attributes.txt.trans.txt", [
    "1. [TAG: Name] 劍",
    "2. [TAG: Name] 槍",
    "3. [TAG: Name] 打擊",
    "4. [TAG: Name] 弓",
    "5. [TAG: Name] 火焰",
    "6. [TAG: Name] 冰冷",
    "7. [TAG: Name] 雷電",
    "8. [TAG: Name] 水",
    "9. [TAG: Name] 大地",
    "10. [TAG: Name] 風",
    "11. [TAG: Name] 神聖",
    "12. [TAG: Name] 暗黑",
    "13. [TAG: Name] 攻擊力",
    "14. [TAG: Name] 防禦力",
    "15. [TAG: Name] 精神力",
    "16. [TAG: Name] 敏捷性",
    "17. [TAG: Name] 吸收",
    "18. [TAG: Name] 槍械",
    "19. [TAG: Name] 獸",
    "20. [TAG: Name] 時空劍",
    "21. [TAG: Name] 召喚",
    "22. [TAG: Name] 流星",
])

# ============================================================
# Database_Terrain.txt  （地形）
# ============================================================
write_translated("Database_Terrain.txt.trans.txt", [
    "1. [TAG: Name] 草原",
    "2. [TAG: Name] 森林",
    "3. [TAG: Name] 沙漠",
    "4. [TAG: Name] 荒地",
    "5. [TAG: Name] 毒沼",
    "6. [TAG: Name] 雪原",
    "7. [TAG: Name] 雪原：森林",
    "8. [TAG: Name] 傷害地板",
    "9. [TAG: Name] 海：淺灘",
    "10. [TAG: Name] 海：外海",
    "11. [TAG: Name] 地下城",
    "12. [TAG: Name] 水路",
    "13. [TAG: Name] 懸崖",
])

# ============================================================
# Database_ChipSet.txt  （地圖元件組）
# ============================================================
write_translated("Database_ChipSet.txt.trans.txt", [
    "1. [TAG: Name] 基礎組",
    "2. [TAG: Name] 外觀組",
    "3. [TAG: Name] 室內組",
    "4. [TAG: Name] 地下城組",
    "5. [TAG: Name] 船艦組",
    "6. [TAG: Name] 外觀組２",
    "7. [TAG: Name] 外觀組３",
    "8. [TAG: Name] 白柱外觀",
    "9. [TAG: Name] 通用元件組",
    "10. [TAG: Name] 外觀組（暗）",
    "11. [TAG: Name] 通用元件組２",
    "12. [TAG: Name] 外觀組翻轉",
    "13. [TAG: Name] 最終迷宮",
    "14. [TAG: Name] 通用元件組３",
    "15. [TAG: Name] 漆黑",
    "16. [TAG: Name] 基礎組翻轉",
    "17. [TAG: Name] 機工士",
])

print("\n=== Batch 2 (Conditions/Attributes/Terrain/ChipSet) done ===")
