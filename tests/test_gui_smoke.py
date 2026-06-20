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


def test_gamedialog_extract_fills_selected_table(tmp_path, monkeypatch):
    import easyrpg_web_gui as gui
    monkeypatch.setattr(gui.messagebox, "showinfo", lambda *a, **k: None)
    root = _make_root()
    try:
        app = gui.App(root, project_path=tmp_path / "library.json")
        tid = gui.slugify.hash_slug("甲表")
        app.name_tables = [{"id": tid, "name": "甲表", "pages": []}]
        dlg = gui.GameDialog(root, folder="C:/g", label="甲",
                             name_table_id=tid, name_tables=app.name_tables, app=app)
        pages = [{"label": "頁１", "chars": "甲乙丙"}, {"label": "頁２", "chars": "丁戊"}]
        dlg._apply_extracted(pages, "")     # 模擬抽取結果填入選定字表
        assert app.name_tables[0]["pages"] == pages
        dlg.destroy()
    finally:
        root.destroy()


def test_gamedialog_extract_creates_table_when_none_selected(tmp_path, monkeypatch):
    import easyrpg_web_gui as gui
    monkeypatch.setattr(gui.messagebox, "showinfo", lambda *a, **k: None)
    root = _make_root()
    try:
        app = gui.App(root, project_path=tmp_path / "library.json")
        assert app.name_tables == []
        dlg = gui.GameDialog(root, folder="C:/g", label="乙遊戲",
                             name_tables=app.name_tables, app=app)   # 未選字表
        dlg._apply_extracted([{"label": "頁１", "chars": "子丑"}], "")
        assert len(app.name_tables) == 1                  # 自動新建
        assert app.name_tables[0]["name"] == "乙遊戲"
        assert app.name_tables[0]["pages"][0]["chars"] == "子丑"
        dlg.destroy()
    finally:
        root.destroy()


def test_gamedialog_extract_names_known_table(tmp_path, monkeypatch):
    # 抽到聖靈火神2003字表的特徵 → 新建字表自動命名為「聖靈火神2003字表」（非遊戲名）
    import easyrpg_web_gui as gui
    monkeypatch.setattr(gui.messagebox, "showinfo", lambda *a, **k: None)
    root = _make_root()
    try:
        app = gui.App(root, project_path=tmp_path / "library.json")
        dlg = gui.GameDialog(root, folder="C:/g", label="某遊戲",
                             name_tables=app.name_tables, app=app)
        pages = [{"label": "頁２", "chars": "子力小大天中太夫月幻日毛文古艾白玉世冬加Ｘ"},
                 {"label": "頁１", "chars": "貝利芙芬拉欣東雨依武秀金耶肯青法奇皇宜兒昂Ｙ"}]
        dlg._apply_extracted(pages, "")
        assert app.name_tables[0]["name"] == "聖靈火神2003字表"
        dlg.destroy()
    finally:
        root.destroy()


def test_gamedialog_extract_nothing_found_leaves_tables(tmp_path, monkeypatch):
    import easyrpg_web_gui as gui
    monkeypatch.setattr(gui.messagebox, "showwarning", lambda *a, **k: None)
    root = _make_root()
    try:
        app = gui.App(root, project_path=tmp_path / "library.json")
        dlg = gui.GameDialog(root, folder="C:/g", label="丙",
                             name_tables=app.name_tables, app=app)
        dlg._apply_extracted([], "")                      # 找不到 → 不建表
        assert app.name_tables == []
        dlg.destroy()
    finally:
        root.destroy()


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


def test_nametable_editor_multipage_save(tmp_path):
    import easyrpg_web_gui as gui
    root = _make_root()
    try:
        app = gui.App(root, project_path=tmp_path / "library.json")
        tid = gui.slugify.hash_slug("甲表")
        app.name_tables = [{"id": tid, "name": "甲表",
                            "pages": [{"label": "頁１", "chars": "甲乙"}]}]
        mgr = gui.NameTableManager(app)
        ed = gui.NameTableEditor(mgr, app.name_tables[0])
        ed._add_page()                       # 新增第二頁
        ed.tabs[1][0].set("頁２")            # 第二頁頁名
        ed.tabs[1][1].insert("1.0", "丙丁")  # 第二頁字
        ed._save()
        pages = app.name_tables[0]["pages"]
        assert len(pages) == 2
        assert pages[0]["chars"] == "甲乙" and pages[1]["chars"] == "丙丁"
        assert pages[1]["label"] == "頁２"
        ed.destroy()
        mgr.destroy()
    finally:
        root.destroy()


def test_game_name_table_id_persists(tmp_path):
    import slugify
    import easyrpg_web_gui as gui
    lib = tmp_path / "library.json"
    root = _make_root()
    try:
        app = gui.App(root, project_path=lib)
        tid = slugify.hash_slug("甲表")
        app.name_tables = [{"id": tid, "name": "甲表",
                            "pages": [{"label": "頁１", "chars": "甲"}]}]
        app.games.append({"folder": "x", "label": "甲", "cover": None,
                          "rtp": None, "tags": [], "name_table_id": tid})
        app._save()
        data = json.loads(lib.read_text(encoding="utf-8"))
        assert data["games"][-1]["name_table_id"] == tid
        dlg = gui.GameDialog(root, folder="x", label="甲",
                             name_table_id=tid, name_tables=app.name_tables)
        dlg.destroy()
    finally:
        root.destroy()


def test_name_tables_save_roundtrip(tmp_path):
    import slugify
    import easyrpg_web_gui as gui
    lib = tmp_path / "library.json"
    root = _make_root()
    try:
        app = gui.App(root, project_path=lib)
        tid = slugify.hash_slug("甲表")
        app.name_tables = [{"id": tid, "name": "甲表",
                            "pages": [{"label": "頁１", "chars": "甲乙丙"},
                                      {"label": "頁２", "chars": "丁戊"}]}]
        app._save()
        data = json.loads(lib.read_text(encoding="utf-8"))
        assert data["name_tables"] == [
            {"id": tid, "name": "甲表",
             "pages": [{"label": "頁１", "chars": "甲乙丙"},
                       {"label": "頁２", "chars": "丁戊"}]}]
    finally:
        root.destroy()


def test_gamedialog_preserves_name_table_id():
    import easyrpg_web_gui as gui
    root = _make_root()
    try:
        dlg = gui.GameDialog(root, folder="C:/g", label="甲", name_table_id="tid1",
                             name_tables=[{"id": "tid1", "name": "甲表", "pages": []}])
        dlg.v_folder.set("C:/g")
        dlg.v_label.set("甲")
        dlg._ok()
        assert dlg.result["name_table_id"] == "tid1"
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
