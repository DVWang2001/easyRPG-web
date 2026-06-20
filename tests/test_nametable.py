from pathlib import Path

import nametable

TEMPLATE = Path("players/build/src-ref/window_keyboard.cpp").read_text(encoding="utf-8")


def _pages(c1, c2, l1="漢一", l2="漢二"):
    return [{"label": l1, "chars": c1}, {"label": l2, "chars": c2}]


def test_render_changes_page_labels():
    out = nametable.render(TEMPLATE, _pages("甲乙丙", "丁戊己"))
    assert '"<漢一>"' in out
    assert '"<漢二>"' in out
    assert '"<翻頁>"' not in out
    assert '"<前頁>"' not in out
    assert '"<確定>"' in out  # DONE_ZH_TW 不變


def test_render_custom_page_labels():
    # 頁名不一定是漢一/漢二 —— 用各頁自己的 label
    out = nametable.render(TEMPLATE, _pages("甲", "乙", l1="頁１", l2="頁２"))
    assert '"<頁１>"' in out and '"<頁２>"' in out
    assert '"<漢一>"' not in out


def test_render_inserts_user_chars_and_drops_poetry():
    out = nametable.render(TEMPLATE, _pages("甲乙丙", "丁戊己"))
    for ch in "甲乙丙丁戊己":
        assert f'"{ch}"' in out
    assert "泉" not in out
    assert "幾" not in out


def test_render_lays_chars_row_major():
    out = nametable.render(TEMPLATE, _pages("0123456789ABCDEFG", ""))
    assert '{"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}' in out


def test_render_keeps_control_cells_bare():
    out = nametable.render(TEMPLATE, _pages("甲", "乙"))
    assert "NEXT_PAGE, \"\", DONE" in out
    assert '"NEXT_PAGE"' not in out
    assert '"DONE"' not in out


def test_render_empty_page_has_only_controls():
    out = nametable.render(TEMPLATE, _pages("", ""))
    assert '{"", "", "", "", "", "", "", "", "", ""}' in out


def test_render_truncates_beyond_two_pages():
    # 超過兩頁只渲染前兩頁（EasyRPG 鍵盤限制）
    pages = [{"label": "頁１", "chars": "甲"}, {"label": "頁２", "chars": "乙"},
             {"label": "頁３", "chars": "丙"}]
    out = nametable.render(TEMPLATE, pages)
    assert '"甲"' in out and '"乙"' in out
    assert '"丙"' not in out          # 第三頁被截斷


def test_render_single_page_fills_first_only():
    out = nametable.render(TEMPLATE, [{"label": "頁１", "chars": "甲乙"}])
    assert '"甲"' in out and '"乙"' in out
    assert '"<頁１>"' in out


SCENE_TEMPLATE = Path("players/build/src-ref/scene_name.cpp").read_text(encoding="utf-8")


def test_patch_scene_name_guards_letter_symbol_for_big5():
    out = nametable.patch_scene_name(SCENE_TEMPLATE)
    # Letter/Symbol 兩頁改成「非 Big5 才加」→ 繁中遊戲只剩自訂兩頁
    assert "if (!Player::IsBig5()) {" in out
    # 兩個 push_back 仍在（被包進 if 內），但原本「無條件加」的形式不再
    assert "layouts.push_back(Window_Keyboard::Letter);" in out
    assert "layouts.push_back(Window_Keyboard::Symbol);" in out
    idx = out.index("if (!Player::IsBig5()) {")
    assert "Letter" in out[idx:idx + 120] and "Symbol" in out[idx:idx + 120]


def test_patch_scene_name_idempotent_safe_when_absent():
    # 找不到目標時原樣回傳（不爆）
    assert nametable.patch_scene_name("無關內容") == "無關內容"
