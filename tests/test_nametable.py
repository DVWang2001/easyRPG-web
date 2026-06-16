from pathlib import Path

import nametable

TEMPLATE = Path("players/build/src-ref/window_keyboard.cpp").read_text(encoding="utf-8")


def test_render_changes_page_labels():
    out = nametable.render(TEMPLATE, "甲乙丙", "丁戊己")
    assert '"<漢一>"' in out
    assert '"<漢二>"' in out
    assert '"<翻頁>"' not in out
    assert '"<前頁>"' not in out
    assert '"<確定>"' in out  # DONE_ZH_TW 不變


def test_render_inserts_user_chars_and_drops_poetry():
    out = nametable.render(TEMPLATE, "甲乙丙", "丁戊己")
    for ch in "甲乙丙丁戊己":
        assert f'"{ch}"' in out
    # 原本的詩句字(TC1 開頭 "泉"、TC2 開頭 "幾")應被換掉
    assert "泉" not in out
    assert "幾" not in out


def test_render_lays_chars_row_major():
    out = nametable.render(TEMPLATE, "0123456789ABCDEFG", "")
    # 前 10 個排在第一列
    assert '{"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}' in out


def test_render_keeps_control_cells_bare():
    out = nametable.render(TEMPLATE, "甲", "乙")
    # NEXT_PAGE / DONE 是識別字,不可加引號
    assert "NEXT_PAGE, \"\", DONE" in out
    assert '"NEXT_PAGE"' not in out
    assert '"DONE"' not in out


def test_render_empty_page_has_only_controls():
    out = nametable.render(TEMPLATE, "", "")
    # 空頁:第一列全空
    assert '{"", "", "", "", "", "", "", "", "", ""}' in out
