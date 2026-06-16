import importlib
import json

import pytest

import easyrpg_web_build as core


def test_gui_imports_and_references_core():
    mod = importlib.import_module("easyrpg_web_gui")
    assert mod.core is core
    assert hasattr(mod, "App")
    assert callable(core.build_library)
    assert callable(core.build)


def _make_root():
    import tkinter as tk
    try:
        return tk.Tk()
    except tk.TclError:
        pytest.skip("此環境無法初始化 Tk（無顯示）")


def test_app_loads_existing_library(tmp_path):
    import easyrpg_web_gui as gui
    lib = tmp_path / "library.json"
    lib.write_text(json.dumps({
        "version": 1, "lib_name": "測試庫", "icon": "i.png",
        "soundfont": "s.sf2", "out": "dist",
        "games": [{"folder": "", "label": "甲", "cover": None, "rtp": None},
                  {"folder": "", "label": "乙", "cover": None, "rtp": None}],
    }, ensure_ascii=False), encoding="utf-8")
    root = _make_root()
    try:
        app = gui.App(root, project_path=lib)
        assert app.lib_name.get() == "測試庫"
        assert len(app.games) == 2
        assert len(app.tree.get_children()) == 2
    finally:
        root.destroy()


def test_app_autosaves_on_mutation(tmp_path):
    import easyrpg_web_gui as gui
    lib = tmp_path / "library.json"
    root = _make_root()
    try:
        app = gui.App(root, project_path=lib)
        app.games.append({"folder": "", "label": "新遊戲", "cover": None, "rtp": None})
        app._refresh_tree()
        app._save()
        text = lib.read_text(encoding="utf-8")
        assert "新遊戲" in text                       # 中文不被跳脫
        data = json.loads(text)
        assert data["games"][-1]["label"] == "新遊戲"
    finally:
        root.destroy()


def test_app_saves_tags(tmp_path):
    import easyrpg_web_gui as gui
    lib = tmp_path / "library.json"
    root = _make_root()
    try:
        app = gui.App(root, project_path=lib)
        app.games.append({"folder": "", "label": "有標籤的遊戲",
                          "cover": None, "rtp": None, "tags": ["RPG", "漢化"]})
        app._refresh_tree()
        app._save()
        data = json.loads(lib.read_text(encoding="utf-8"))
        assert data["games"][-1]["tags"] == ["RPG", "漢化"]
    finally:
        root.destroy()


def test_gamedialog_builds_and_collects_tags(tmp_path):
    import easyrpg_web_gui as gui
    root = _make_root()
    try:
        dlg = gui.GameDialog(root, folder="C:/g", label="甲",
                             tags=["RPG"], available_tags=["RPG", "漢化", "動作"])
        # 下拉選一個現有標籤 → 加入這個遊戲
        dlg.cb_tag.set("漢化")
        dlg._add_tag()
        assert dlg.selected_tags == ["RPG", "漢化"]
        # 重複加入不會變兩次
        dlg.cb_tag.set("漢化")
        dlg._add_tag()
        assert dlg.selected_tags == ["RPG", "漢化"]
        dlg.destroy()
    finally:
        root.destroy()


def test_game_custom_player_persists(tmp_path):
    import easyrpg_web_gui as gui
    lib = tmp_path / "library.json"
    root = _make_root()
    try:
        app = gui.App(root, project_path=lib)
        app.games.append({"folder": "", "label": "自訂遊戲", "cover": None,
                          "rtp": None, "tags": [], "custom_player": True})
        app._refresh_tree()
        app._save()
        data = json.loads(lib.read_text(encoding="utf-8"))
        assert data["games"][-1]["custom_player"] is True
        dlg = gui.GameDialog(root, folder="x", label="甲", custom_player=True)
        assert dlg.v_custom.get() is True
        dlg.destroy()
    finally:
        root.destroy()


def test_name_table_dialog_saves(tmp_path):
    import easyrpg_web_gui as gui
    lib = tmp_path / "library.json"
    root = _make_root()
    try:
        app = gui.App(root, project_path=lib)
        dlg = gui.NameTableDialog(app)
        dlg.t1.insert("end", "甲乙丙")
        dlg.t2.insert("end", "丁戊")
        dlg._save()
        assert app.name_table == {"zh_tw_1": "甲乙丙", "zh_tw_2": "丁戊"}
        data = json.loads(lib.read_text(encoding="utf-8"))
        assert data["name_table"] == {"zh_tw_1": "甲乙丙", "zh_tw_2": "丁戊"}
        dlg.destroy()
    finally:
        root.destroy()


def test_app_loads_and_saves_all_tags(tmp_path):
    import easyrpg_web_gui as gui
    lib = tmp_path / "library.json"
    lib.write_text(json.dumps({
        "all_tags": ["RPG", "漢化"],
        "games": [{"folder": "", "label": "甲", "tags": ["動作"]}],
    }, ensure_ascii=False), encoding="utf-8")
    root = _make_root()
    try:
        app = gui.App(root, project_path=lib)
        # 載入時 all_tags＝明確清單＋遊戲用到的聯集
        assert app.all_tags == ["RPG", "漢化", "動作"]
        # 主視窗新增全域標籤名稱
        app.new_tag.set("神作")
        app._add_tag()
        assert "神作" in app.all_tags
        data = json.loads(lib.read_text(encoding="utf-8"))
        assert "神作" in data["all_tags"]
    finally:
        root.destroy()
