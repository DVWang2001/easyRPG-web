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
