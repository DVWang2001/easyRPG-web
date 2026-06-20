# 多個自訂取名字表 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把單一全域自訂取名字表改成多個具名字表，每個遊戲從清單挑一個使用，各字表各自編譯並快取。

**Architecture:** `library.json` 以 `name_tables` 清單取代單一 `name_table`，遊戲以 `name_table_id` 參照。每個字表編出的引擎快取在 `players/custom/<id>/`（附 `source.json` 判斷過期）。建置時把每個被用到的字表引擎複製成 `dist/player-custom-<id>/`，遊戲頁依 id 載入對應引擎。

**Tech Stack:** Python 3、tkinter（GUI）、pytest、既有 `slugify.hash_slug`、Docker（重建引擎，不在自動測試內）。

## Global Constraints

- id 用 `slugify.hash_slug(name, taken)` 產生（NFKC 後 sha256 前 16 碼，碰撞加 `-2`/`-3`）；**id 建立後固定不變**，改名不改 id。
- 遊戲 `name_table_id` 空字串/缺欄位/null = 用官方播放器（根目錄引擎）。
- 每個字表保留漢一/漢二兩頁結構（`zh_tw_1` / `zh_tw_2`），`nametable.py` 不改。
- 向後相容：能載入舊格式（`name_table` 物件 + 遊戲 `custom_player` 布林）。
- `project.save_project` 維持 UTF-8、`ensure_ascii=False`、`indent=2`、原子寫入。
- 測試指令在專案根目錄執行：`python -m pytest <path> -v`。

---

### Task 1: project.py — schema 與向後相容遷移

**Files:**
- Modify: `project.py`（`default_project`、`_normalize`）
- Test: `tests/test_project.py`

**Interfaces:**
- Consumes: `slugify.hash_slug(name, taken=None) -> str`
- Produces:
  - `default_project()` 回傳含 `"name_tables": []`（不再有 `"name_table"`）；games 每筆含 `"name_table_id": ""`（不再有 `"custom_player"`）。
  - `_normalize(data)` 把舊格式遷移成新格式。
  - 每個 name_table 形狀：`{"id": str, "name": str, "zh_tw_1": str, "zh_tw_2": str}`。

- [ ] **Step 1: 寫失敗測試**

把 `tests/test_project.py` 中舊的 name_table 測試（`test_name_table_defaults_empty`、`test_name_table_roundtrip`、`test_name_table_fills_missing`、`test_game_custom_player_flag`）整段刪除，改寫成下列測試：

```python
def test_name_tables_default_empty():
    assert project.default_project()["name_tables"] == []


def test_game_name_table_id_default_empty():
    g = project.default_project()
    # 新增遊戲時欄位齊全
    assert "custom_player" not in project.default_project()


def test_name_tables_roundtrip(tmp_path):
    p = tmp_path / "library.json"
    data = project.default_project()
    data["name_tables"] = [
        {"id": "t1", "name": "甲表", "zh_tw_1": "甲乙丙", "zh_tw_2": "丁戊"},
    ]
    data["games"] = [{"folder": "a", "label": "遊戲甲", "name_table_id": "t1"}]
    project.save_project(p, data)
    proj, _ = project.load_project(p)
    assert proj["name_tables"][0] == {
        "id": "t1", "name": "甲表", "zh_tw_1": "甲乙丙", "zh_tw_2": "丁戊"}
    assert proj["games"][0]["name_table_id"] == "t1"


def test_game_name_table_id_dropped_when_table_missing(tmp_path):
    p = tmp_path / "library.json"
    data = project.default_project()
    data["games"] = [{"folder": "a", "label": "x", "name_table_id": "nope"}]
    project.save_project(p, data)
    proj, _ = project.load_project(p)
    # 參照不存在的字表 → 設回空字串
    assert proj["games"][0]["name_table_id"] == ""


def test_legacy_name_table_migrates_to_one_table(tmp_path):
    p = tmp_path / "library.json"
    # 舊格式：單一 name_table 物件 + 遊戲 custom_player 布林
    legacy = {
        "version": 1, "lib_name": "L", "icon": "i", "soundfont": "s", "out": "dist",
        "name_table": {"zh_tw_1": "甲乙", "zh_tw_2": "丙"},
        "games": [
            {"folder": "a", "label": "舊自訂", "custom_player": True},
            {"folder": "b", "label": "舊一般", "custom_player": False},
        ],
    }
    p.write_text(__import__("json").dumps(legacy, ensure_ascii=False), encoding="utf-8")
    proj, _ = project.load_project(p)
    tables = proj["name_tables"]
    assert len(tables) == 1
    assert tables[0]["name"] == "自訂字表"
    assert tables[0]["zh_tw_1"] == "甲乙" and tables[0]["zh_tw_2"] == "丙"
    mid = tables[0]["id"]
    assert proj["games"][0]["name_table_id"] == mid   # custom_player True → 指向遷移字表
    assert proj["games"][1]["name_table_id"] == ""     # False → 空


def test_legacy_empty_name_table_no_migration(tmp_path):
    p = tmp_path / "library.json"
    legacy = {"version": 1, "name_table": {"zh_tw_1": "", "zh_tw_2": ""},
              "games": [{"folder": "a", "label": "x"}]}
    p.write_text(__import__("json").dumps(legacy, ensure_ascii=False), encoding="utf-8")
    proj, _ = project.load_project(p)
    assert proj["name_tables"] == []
    assert proj["games"][0]["name_table_id"] == ""
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_project.py -v`
Expected: FAIL（`default_project` 仍有 `name_table`、games 仍有 `custom_player`）。

- [ ] **Step 3: 改 project.py**

在檔案頂端 import 區加入 `import slugify`（與既有 import 並列）。

把 `default_project()` 內：

```python
        "all_tags": [],
        "name_table": {"zh_tw_1": "", "zh_tw_2": ""},
        "games": [],
```

改成：

```python
        "all_tags": [],
        "name_tables": [],
        "games": [],
```

在 `_normalize` 中，**先建立 name_tables 與 valid id 集合**，再正規化 games。把現有 games 正規化區塊與 name_table 區塊替換為下列邏輯。新的 `_normalize` 主體（取代 `if isinstance(data, dict):` 內的內容，all_tags 區塊保留不變）：

```python
def _normalize(data) -> dict:
    """以 default 為底補齊缺欄位；遷移舊 name_table/custom_player → name_tables/name_table_id。"""
    proj = default_project()
    if isinstance(data, dict):
        for k in ("version", "lib_name", "icon", "soundfont", "out"):
            if data.get(k) is not None:
                proj[k] = data[k]

        # --- name_tables：新格式優先；否則從舊 name_table 遷移 ---
        tables, taken_ids = [], set()
        raw_tables = data.get("name_tables")
        if isinstance(raw_tables, list):
            for t in raw_tables:
                if not isinstance(t, dict):
                    continue
                name = str(t.get("name") or "").strip() or "自訂字表"
                tid = str(t.get("id") or "").strip()
                if not tid or tid in taken_ids:
                    tid = slugify.hash_slug(name, taken_ids)
                taken_ids.add(tid)
                tables.append({"id": tid, "name": name,
                               "zh_tw_1": str(t.get("zh_tw_1") or ""),
                               "zh_tw_2": str(t.get("zh_tw_2") or "")})
        migrated_id = ""
        if not tables:
            old = data.get("name_table")
            z1 = str(old.get("zh_tw_1") or "") if isinstance(old, dict) else ""
            z2 = str(old.get("zh_tw_2") or "") if isinstance(old, dict) else ""
            games_have_custom = any(
                isinstance(g, dict) and g.get("custom_player")
                for g in (data.get("games") or []))
            if z1 or z2 or games_have_custom:
                migrated_id = slugify.hash_slug("自訂字表", taken_ids)
                taken_ids.add(migrated_id)
                tables.append({"id": migrated_id, "name": "自訂字表",
                               "zh_tw_1": z1, "zh_tw_2": z2})
        proj["name_tables"] = tables
        valid_ids = {t["id"] for t in tables}

        # --- games ---
        games = data.get("games")
        if isinstance(games, list):
            norm = []
            for g in games:
                if not isinstance(g, dict):
                    continue
                nid = str(g.get("name_table_id") or "").strip()
                if nid not in valid_ids:
                    nid = migrated_id if g.get("custom_player") else ""
                norm.append({
                    "folder": g.get("folder") or "",
                    "label": g.get("label") or "",
                    "cover": g.get("cover") or None,
                    "rtp": g.get("rtp") or None,
                    "tags": [str(t).strip() for t in (g.get("tags") or [])
                             if str(t).strip()],
                    "name_table_id": nid,
                })
            proj["games"] = norm

        # 全域標籤清單：明確清單（去重去空白）優先，再補上各遊戲用到但不在清單的
        ordered, seen = [], set()
        for t in (data.get("all_tags") or []):
            t = str(t).strip()
            if t and t not in seen:
                seen.add(t)
                ordered.append(t)
        for g in proj["games"]:
            for t in g["tags"]:
                if t not in seen:
                    seen.add(t)
                    ordered.append(t)
        proj["all_tags"] = ordered
    return proj
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_project.py -v`
Expected: PASS（全部）。

- [ ] **Step 5: Commit**

```bash
git add project.py tests/test_project.py
git commit -m "feat(project): name_tables 清單取代單一 name_table（含舊檔遷移）"
```

---

### Task 2: customplayer.py — 帶 id 重建、source.json、引擎查詢

**Files:**
- Modify: `customplayer.py`
- Test: `tests/test_customplayer.py`

**Interfaces:**
- Produces:
  - `rebuild_custom_player(table_id: str, zh_tw_1: str, zh_tw_2: str, log=None) -> Path`（輸出到 `players/custom/<table_id>/`，並寫 `source.json`）。
  - `engine_dir(table_id: str) -> Path` 回傳 `CUSTOM_DIR / table_id`。
  - `has_engine(table_id: str) -> bool`（該目錄含 index.html/js/wasm）。
  - `is_current(table: dict) -> bool`（已編且 `source.json` 內容 == 該字表的 zh_tw_1/zh_tw_2）。

- [ ] **Step 1: 寫失敗測試**

把 `tests/test_customplayer.py` 的 `test_rebuild_no_docker_raises` 內呼叫改成三參數，並新增 `engine_dir`/`has_engine`/`is_current` 測試：

```python
import json
import customplayer


def test_check_env_no_docker_raises(monkeypatch):
    monkeypatch.setattr(customplayer.shutil, "which", lambda _x: None)
    with pytest.raises(customplayer.BuildEnvError):
        customplayer.check_env()


def test_rebuild_no_docker_raises(monkeypatch):
    monkeypatch.setattr(customplayer.shutil, "which", lambda _x: None)
    with pytest.raises(customplayer.BuildEnvError):
        customplayer.rebuild_custom_player("tid", "甲乙", "丙丁")


def test_engine_dir_and_has_engine(monkeypatch, tmp_path):
    monkeypatch.setattr(customplayer, "CUSTOM_DIR", tmp_path)
    d = customplayer.engine_dir("abc")
    assert d == tmp_path / "abc"
    assert customplayer.has_engine("abc") is False
    d.mkdir()
    for f in customplayer.PLAYER_FILES:
        (d / f).write_text("x")
    assert customplayer.has_engine("abc") is True


def test_is_current(monkeypatch, tmp_path):
    monkeypatch.setattr(customplayer, "CUSTOM_DIR", tmp_path)
    table = {"id": "abc", "name": "甲", "zh_tw_1": "甲乙", "zh_tw_2": "丙"}
    assert customplayer.is_current(table) is False           # 還沒編
    d = tmp_path / "abc"
    d.mkdir()
    (d / "source.json").write_text(
        json.dumps({"zh_tw_1": "甲乙", "zh_tw_2": "丙"}), encoding="utf-8")
    assert customplayer.is_current(table) is True            # 內容相符
    table["zh_tw_1"] = "改了"
    assert customplayer.is_current(table) is False           # 內容變了 → 過期
```

確保檔案頂端有 `import pytest`。

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_customplayer.py -v`
Expected: FAIL（`engine_dir`/`has_engine`/`is_current` 未定義；`rebuild_custom_player` 參數數不符）。

- [ ] **Step 3: 改 customplayer.py**

頂端 import 區加 `import json`。把 `rebuild_custom_player` 改成帶 id 並輸出到子資料夾，新增三個查詢函式：

```python
def engine_dir(table_id: str) -> Path:
    return CUSTOM_DIR / table_id


def has_engine(table_id: str) -> bool:
    d = engine_dir(table_id)
    return all((d / f).exists() for f in PLAYER_FILES)


def is_current(table: dict) -> bool:
    """已編且 source.json 內容與該字表 zh_tw_1/zh_tw_2 相符。"""
    p = engine_dir(table.get("id") or "") / "source.json"
    if not p.exists():
        return False
    try:
        sig = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return sig == {"zh_tw_1": table.get("zh_tw_1") or "",
                   "zh_tw_2": table.get("zh_tw_2") or ""}


def rebuild_custom_player(table_id: str, zh_tw_1: str, zh_tw_2: str, log=None) -> Path:
    """產生字表 → 容器內重編 → 把 index.html/js/wasm 複製到 players/custom/<table_id>/。"""
    check_env()
    _log(log, "產生自訂取名字表 window_keyboard.cpp…")
    patched = nametable.render(TEMPLATE.read_text(encoding="utf-8"), zh_tw_1, zh_tw_2)
    tmp = HERE / "players" / "build" / "_patched_window_keyboard.cpp"
    tmp.write_text(patched, encoding="utf-8")

    _log(log, "複製字表進容器…")
    _stream(["docker", "cp", str(tmp),
             f"{CONTAINER}:/work/Player/src/window_keyboard.cpp"], log)

    _log(log, "重新編譯自訂播放器（約數分鐘）…")
    _stream(["docker", "exec", CONTAINER, "bash", "/scripts/player.sh"], log)

    out_dir = engine_dir(table_id)
    _log(log, f"取出 index.html/js/wasm 到 {out_dir}…")
    out_dir.mkdir(parents=True, exist_ok=True)
    for fn in PLAYER_FILES:
        _stream(["docker", "cp", f"{CONTAINER}:{_OUT}/{fn}", str(out_dir / fn)], log)
    (out_dir / "source.json").write_text(
        json.dumps({"zh_tw_1": zh_tw_1, "zh_tw_2": zh_tw_2}, ensure_ascii=False),
        encoding="utf-8")

    _log(log, f"✓ 自訂播放器已更新：{out_dir}")
    return out_dir
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_customplayer.py -v`
Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add customplayer.py tests/test_customplayer.py
git commit -m "feat(customplayer): 每字表編到 players/custom/<id>/＋source.json 過期判斷"
```

---

### Task 3: library.py — entry 帶 name_table_id

**Files:**
- Modify: `library.py`
- Test: `tests/test_library.py`

**Interfaces:**
- Consumes: 遊戲 dict 含 `name_table_id`（Task 1）。
- Produces: `stage_library` 回傳的每個 entry 含 `"name_table_id": str`（不再有 `"custom"`）。

- [ ] **Step 1: 寫失敗測試**

看 `tests/test_library.py` 第 23、37 行附近用到 `custom_player`/`custom` 的斷言，改成 `name_table_id`。打開檔案找到建立 games 與斷言 entries 的地方，把：

```python
         "tags": ["RPG", "漢化"], "custom_player": True},
```

改成：

```python
         "tags": ["RPG", "漢化"], "name_table_id": "tid1"},
```

並把驗證 entry 的斷言（原本檢查 `entry["custom"] is True` / 未給時為 `False`）改成：

```python
    assert entries[0]["name_table_id"] == "tid1"
    # 未給 name_table_id → 空字串
    assert entries[1]["name_table_id"] == ""
```

（若該檔案測試是用其他變數名，沿用其結構，只把 `custom`→`name_table_id`、`True`→`"tid1"`、`False`→`""`。）

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_library.py -v`
Expected: FAIL（entry 仍只有 `custom`）。

- [ ] **Step 3: 改 library.py**

把 docstring 與 `entries.append(...)` 改成帶 name_table_id：

```python
def stage_library(out, games, *, soundfont=None, ignore_globs=staging.DEFAULT_IGNORE):
    """games: list of {folder, label, slug, cover(opt), tags(opt), name_table_id(opt)}。
    回傳選單用 entries: list of {label, slug, cover_rel, tags, name_table_id}。"""
```

把：

```python
        entries.append({"label": g["label"], "slug": slug, "cover_rel": cover_rel,
                        "tags": list(g.get("tags") or []),
                        "custom": bool(g.get("custom_player"))})
```

改成：

```python
        entries.append({"label": g["label"], "slug": slug, "cover_rel": cover_rel,
                        "tags": list(g.get("tags") or []),
                        "name_table_id": str(g.get("name_table_id") or "")})
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_library.py -v`
Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add library.py tests/test_library.py
git commit -m "feat(library): stage entry 帶 name_table_id 取代 custom 布林"
```

---

### Task 4: pwa.py — 遊戲頁依 name_table_id 選引擎

**Files:**
- Modify: `pwa.py`（`write_game_pages`）
- Test: `tests/test_build_library.py`（在 Task 5 一起驗證；本任務先看單元層級）

**Interfaces:**
- Consumes: entry 含 `name_table_id`（Task 3）。
- Produces: `engine = "player-custom-<id>/"`（有 id）或 `""`（無）。

- [ ] **Step 1: 改 pwa.py**

在 `write_game_pages` 迴圈內，把：

```python
        # 自訂取名字表的遊戲載入 player-custom/ 引擎；其餘用根目錄官方引擎。
        engine = "player-custom/" if e.get("custom") else ""
```

改成：

```python
        # 有指定字表的遊戲載入 player-custom-<id>/ 引擎；其餘用根目錄官方引擎。
        table_id = e.get("name_table_id") or ""
        engine = ("player-custom-" + table_id + "/") if table_id else ""
```

迴圈內其餘用到 `engine` 的程式（`src="..."` 取代、`shell` 路徑、canvas_fix）皆沿用 `engine` 變數，不需改。

- [ ] **Step 2: 跑既有 pwa 相關測試確認不爆**

Run: `python -m pytest tests/ -k "pwa or game_pages" -v`
Expected: PASS 或無相符測試（不報錯即可）；整合驗證在 Task 5。

- [ ] **Step 3: Commit**

```bash
git add pwa.py
git commit -m "feat(pwa): 遊戲頁依 name_table_id 載入 player-custom-<id> 引擎"
```

---

### Task 5: easyrpg_web_build.py — 複製各字表引擎、缺引擎報錯

**Files:**
- Modify: `easyrpg_web_build.py`（import customplayer；取代 player-custom 區塊）
- Test: `tests/test_build_library.py`

**Interfaces:**
- Consumes: `customplayer.engine_dir(id)`、`customplayer.has_engine(id)`（Task 2）；entry 含 `name_table_id`（Task 3）。
- Produces: 每個被用到的 id → `dist/player-custom-<id>/index.js`、`index.wasm`；缺引擎丟 `BuildError`。

- [ ] **Step 1: 改寫測試**

把 `tests/test_build_library.py` 的 `test_build_library_per_game_custom_player` 與 `test_build_library_custom_player_missing_engine_errors` 整段換成下列（用 `customplayer.CUSTOM_DIR` monkeypatch，遊戲用 `name_table_id`）：

```python
def test_build_library_per_game_name_table(tmp_path, monkeypatch):
    import customplayer
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    # 假的自訂引擎：players/custom/<id>/
    custom_root = tmp_path / "custom"
    monkeypatch.setattr(customplayer, "CUSTOM_DIR", custom_root)
    tid = slugify.hash_slug("甲表")
    eng = custom_root / tid
    eng.mkdir(parents=True)
    (eng / "index.html").write_text("<html></html>")
    (eng / "index.js").write_text("// custom js")
    (eng / "index.wasm").write_bytes(b"\0custom")
    g1 = tmp_path / "A"
    _game(g1, "1")
    g2 = tmp_path / "B"
    _game(g2, "2")
    out = tmp_path / "dist"

    core.build_library(
        games=[{"folder": g1, "label": "自訂遊戲", "cover": None, "name_table_id": tid},
               {"folder": g2, "label": "一般遊戲", "cover": None}],
        app_icon=None, soundfont=None, out=out,
        player_cache=tmp_path / "cache", player_url=tarball.resolve().as_uri(),
    )

    s1 = slugify.hash_slug("自訂遊戲")
    s2 = slugify.hash_slug("一般遊戲")
    assert (out / ("player-custom-" + tid) / "index.js").read_text() == "// custom js"
    assert (out / ("player-custom-" + tid) / "index.wasm").exists()
    a = (out / f"play-{s1}.html").read_text(encoding="utf-8")
    assert 'src="player-custom-' + tid + '/index.js"' in a
    b = (out / f"play-{s2}.html").read_text(encoding="utf-8")
    assert 'src="index.js"' in b and "player-custom" not in b


def test_build_library_name_table_missing_engine_errors(tmp_path, monkeypatch):
    import customplayer
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    monkeypatch.setattr(customplayer, "CUSTOM_DIR", tmp_path / "nope")
    g1 = tmp_path / "A"
    _game(g1, "1")
    out = tmp_path / "dist"
    try:
        core.build_library(
            games=[{"folder": g1, "label": "自訂", "cover": None,
                    "name_table_id": "missingid"}],
            app_icon=None, soundfont=None, out=out,
            player_cache=tmp_path / "cache", player_url=tarball.resolve().as_uri(),
        )
        assert False, "缺自訂引擎應報錯"
    except core.BuildError as e:
        assert "自訂" in str(e)
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_build_library.py -k name_table -v`
Expected: FAIL（build 仍找 `player-custom/` 單一目錄、用 `custom` 旗標）。

- [ ] **Step 3: 改 easyrpg_web_build.py**

頂端 import 區加 `import customplayer`（與其他 import 並列）。把現有的 player-custom 區塊（約 162–174 行）：

```python
    # 有遊戲勾「使用自訂取名字表」→ 多放一套自訂引擎到 player-custom/（只有這些遊戲用它）。
    if any(e.get("custom") for e in entries):
        _log("放入自訂播放器引擎（player-custom/）…", log)
        try:
            custom_dir = player_fetch.ensure_player(player_cache, variant="custom")
        except FileNotFoundError as e:
            raise BuildError(
                "有遊戲勾選「使用自訂取名字表」，但尚未建置自訂播放器（players/custom 不存在）。"
                "請先在 GUI「編輯取名字表 → 重建自訂播放器」。") from e
        pc = out / "player-custom"
        pc.mkdir(parents=True, exist_ok=True)
        for name in ("index.js", "index.wasm"):
            shutil.copy2(custom_dir / name, pc / name)
```

換成（逐 id 複製，缺引擎指名報錯）：

```python
    # 每個被用到的字表 → 多放一套自訂引擎到 player-custom-<id>/（只有指定的遊戲用它）。
    used_ids = sorted({e.get("name_table_id") for e in entries if e.get("name_table_id")})
    for tid in used_ids:
        if not customplayer.has_engine(tid):
            who = next((e["label"] for e in entries if e.get("name_table_id") == tid), tid)
            raise BuildError(
                f"遊戲「{who}」用到的自訂取名字表尚未建置自訂播放器"
                f"（缺 players/custom/{tid}）。請先在 GUI「字表管理 → 重建」。")
        _log(f"放入自訂播放器引擎（player-custom-{tid}/）…", log)
        src = customplayer.engine_dir(tid)
        pc = out / ("player-custom-" + tid)
        pc.mkdir(parents=True, exist_ok=True)
        for name in ("index.js", "index.wasm"):
            shutil.copy2(src / name, pc / name)
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_build_library.py -v`
Expected: PASS（全部，含改寫的兩個）。

- [ ] **Step 5: Commit**

```bash
git add easyrpg_web_build.py tests/test_build_library.py
git commit -m "feat(build): 每字表引擎複製到 player-custom-<id>/＋缺引擎指名報錯"
```

---

### Task 6: GUI — 字表管理清單、遊戲下拉、表格欄

**Files:**
- Modify: `easyrpg_web_gui.py`
- Test: `tests/test_gui_smoke.py`

**Interfaces:**
- Consumes: `App.name_tables`（list）、`customplayer.rebuild_custom_player(id, z1, z2, log)`、`customplayer.is_current(table)`、`slugify.hash_slug`。
- Produces:
  - `App.name_tables: list`（取代 `App.name_table: dict`）。`_save` 寫 `"name_tables"`。
  - `GameDialog(... name_table_id="", name_tables=())`，`result` 含 `"name_table_id"`（取代 `custom_player`）。

- [ ] **Step 1: 改寫 gui_smoke 測試**

把 `tests/test_gui_smoke.py` 的 `test_game_custom_player_persists` 與 `test_name_table_dialog_saves` 換成下列（其餘測試不動）：

```python
def test_game_name_table_id_persists(tmp_path):
    import slugify
    with _headless_app(tmp_path) as (gui, app, root):
        tid = slugify.hash_slug("甲表")
        app.name_tables = [{"id": tid, "name": "甲表", "zh_tw_1": "甲", "zh_tw_2": ""}]
        app.games.append({"folder": "x", "label": "甲", "cover": None,
                          "rtp": None, "tags": [], "name_table_id": tid})
        app._save()
        data, _ = gui.project.load_project(app.project_path)
        assert data["games"][-1]["name_table_id"] == tid
        dlg = gui.GameDialog(root, folder="x", label="甲",
                             name_table_id=tid, name_tables=app.name_tables)
        dlg.destroy()


def test_name_tables_save_roundtrip(tmp_path):
    import slugify
    with _headless_app(tmp_path) as (gui, app, root):
        tid = slugify.hash_slug("甲表")
        app.name_tables = [{"id": tid, "name": "甲表",
                            "zh_tw_1": "甲乙丙", "zh_tw_2": "丁戊"}]
        app._save()
        data, _ = gui.project.load_project(app.project_path)
        assert data["name_tables"] == [
            {"id": tid, "name": "甲表", "zh_tw_1": "甲乙丙", "zh_tw_2": "丁戊"}]
```

> 註：沿用該檔既有的 headless app fixture/context（上面寫成 `_headless_app(tmp_path)`，請對齊檔案中現有的建立方式——若現有測試是直接 `gui.App(root, ...)` 就照那個寫法，重點是 `app.name_tables` 與 `GameDialog(name_table_id=..., name_tables=...)`）。

先讀 `tests/test_gui_smoke.py` 既有的 app 建立樣式再對齊。

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_gui_smoke.py -v`
Expected: FAIL（`App.name_tables`、`GameDialog(name_table_id=...)` 尚未存在）。

- [ ] **Step 3: 改 GameDialog（下拉選字表）**

頂端 import 區加 `import slugify`。

`GameDialog.__init__` 簽名把 `custom_player=False` 換成 `name_table_id="", name_tables=()`：

```python
    def __init__(self, parent, folder="", label="", cover="", rtp="", tags=(),
                 available_tags=(), name_table_id="", name_tables=()):
```

刪除 `self.v_custom = tk.BooleanVar(...)`，改存字表清單與目前選擇：

```python
        self.name_tables = list(name_tables)
        self._nt_id = name_table_id
```

把原本第 62–64 行的 Checkbutton：

```python
        ttk.Checkbutton(self, text="使用自訂取名字表（自建播放器）",
                        variable=self.v_custom).grid(
            row=7, column=0, columnspan=3, sticky="w", padx=8, pady=(6, 0))
```

換成下拉選單（顯示名稱，值對應 id；「（無）」= 空 id）：

```python
        ttk.Label(self, text="取名字表").grid(row=7, column=0, sticky="w", padx=8, pady=(6, 0))
        self._nt_labels = ["（無）"] + [t["name"] for t in self.name_tables]
        self.cb_nt = ttk.Combobox(self, values=self._nt_labels, width=22, state="readonly")
        cur = next((i + 1 for i, t in enumerate(self.name_tables)
                    if t["id"] == self._nt_id), 0)
        self.cb_nt.current(cur)
        self.cb_nt.grid(row=7, column=1, sticky="w", padx=4, pady=(6, 0))
```

`_ok` 的 result dict 把 `"custom_player": bool(self.v_custom.get())` 換成：

```python
            "name_table_id": self._selected_nt_id(),
```

並新增方法：

```python
    def _selected_nt_id(self):
        i = self.cb_nt.current()
        if i <= 0:
            return ""
        return self.name_tables[i - 1]["id"]
```

- [ ] **Step 4: 改 App（name_tables 狀態、save、表格欄、開啟字表管理）**

`App.__init__`：把 `self.name_table: dict = dict(proj["name_table"])` 換成：

```python
        self.name_tables: list = [dict(t) for t in proj["name_tables"]]
```

`_save()`：把 `"name_table": dict(self.name_table),` 換成 `"name_tables": [dict(t) for t in self.name_tables],`，並把 games 內 `"custom_player": bool(g.get("custom_player"))` 換成 `"name_table_id": str(g.get("name_table_id") or "")`。

`_refresh_tree()`：把 `custom = "✓" if g.get("custom_player") else ""` 換成顯示字表名稱：

```python
            nid = g.get("name_table_id") or ""
            custom = next((t["name"] for t in self.name_tables if t["id"] == nid), "")
```

`_add()` / `_edit()`：把傳給 `GameDialog` 的 `custom_player=...` 換成 `name_table_id=..., name_tables=self.name_tables`。`_edit` 範例：

```python
        dlg = GameDialog(self.root, str(g.get("folder") or ""), g.get("label") or "",
                         g.get("cover") or "", g.get("rtp") or "",
                         tags=list(g.get("tags") or []),
                         available_tags=list(self.all_tags),
                         name_table_id=str(g.get("name_table_id") or ""),
                         name_tables=self.name_tables)
```

`_add` 同理加 `name_tables=self.name_tables`（它本來就傳 `available_tags`）。

`_edit_name_table` 改成開新的管理清單：

```python
    def _edit_name_table(self):
        NameTableManager(self)
```

把主視窗按鈕文字「編輯取名字表…」改成「字表管理…」（第 210 行）。

- [ ] **Step 5: 用清單管理對話框取代 NameTableDialog**

把整個 `NameTableDialog` 類別換成 `NameTableManager`（清單）＋ `NameTableEditor`（編單一字表，沿用舊的兩個 ScrolledText）：

```python
class NameTableManager(tk.Toplevel):
    """管理多個取名字表：新增/改名/刪除/編輯字格/重建（各自快取於 players/custom/<id>/）。"""

    def __init__(self, app: "App"):
        super().__init__(app.root)
        self.app = app
        self.title("字表管理")
        self.transient(app.root)

        self.lb = tk.Listbox(self, width=40, height=8)
        self.lb.grid(row=0, column=0, rowspan=6, padx=8, pady=8)
        ttk.Button(self, text="新增", width=8, command=self._add).grid(row=0, column=1, padx=4)
        ttk.Button(self, text="改名", width=8, command=self._rename).grid(row=1, column=1, padx=4)
        ttk.Button(self, text="編輯字格", width=8, command=self._edit).grid(row=2, column=1, padx=4)
        ttk.Button(self, text="刪除", width=8, command=self._delete).grid(row=3, column=1, padx=4)
        ttk.Button(self, text="重建", width=8, command=self._rebuild).grid(row=4, column=1, padx=4)
        ttk.Button(self, text="關閉", width=8, command=self.destroy).grid(row=5, column=1, padx=4)
        ttk.Label(self, text="提示：重建需要 Docker；進度在主視窗 log 區。",
                  foreground="#888").grid(row=6, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 8))
        self._refresh()

    def _refresh(self):
        self.lb.delete(0, "end")
        for t in self.app.name_tables:
            mark = "✓" if customplayer.is_current(t) else "⚠未編/過期"
            self.lb.insert("end", f"{t['name']}  [{mark}]")

    def _sel(self):
        s = self.lb.curselection()
        return s[0] if s else None

    def _taken_ids(self):
        return {t["id"] for t in self.app.name_tables}

    def _add(self):
        name = _ask_name(self, "新增字表", "字表名稱：")
        if not name:
            return
        tid = slugify.hash_slug(name, self._taken_ids())
        self.app.name_tables.append({"id": tid, "name": name, "zh_tw_1": "", "zh_tw_2": ""})
        self.app._save()
        self._refresh()

    def _rename(self):
        i = self._sel()
        if i is None:
            return
        name = _ask_name(self, "改名", "新名稱：", self.app.name_tables[i]["name"])
        if name:
            self.app.name_tables[i]["name"] = name   # id 不變
            self.app._save()
            self.app._refresh_tree()
            self._refresh()

    def _edit(self):
        i = self._sel()
        if i is None:
            return
        NameTableEditor(self, self.app.name_tables[i])

    def _delete(self):
        i = self._sel()
        if i is None:
            return
        t = self.app.name_tables[i]
        if not messagebox.askyesno("刪除字表", f"確定刪除「{t['name']}」？\n指向它的遊戲會改用官方播放器。"):
            return
        for g in self.app.games:
            if g.get("name_table_id") == t["id"]:
                g["name_table_id"] = ""
        del self.app.name_tables[i]
        self.app._save()
        self.app._refresh_tree()
        self._refresh()

    def _rebuild(self):
        i = self._sel()
        if i is None:
            return
        t = self.app.name_tables[i]
        z1, z2, tid = t["zh_tw_1"], t["zh_tw_2"], t["id"]

        def work():
            try:
                customplayer.rebuild_custom_player(tid, z1, z2, log=self.app._emit)
                self.app._emit(f"✓ 字表「{t['name']}」已重建。")
            except Exception as e:  # noqa: BLE001 — 回報任何錯誤給使用者
                self.app._emit(f"✗ 重建失敗：{e}")
            finally:
                self.app.root.after(0, self._refresh)

        threading.Thread(target=work, daemon=True).start()


class NameTableEditor(tk.Toplevel):
    """編輯單一字表的漢一/漢二字格。"""

    def __init__(self, manager: "NameTableManager", table: dict):
        super().__init__(manager)
        self.manager = manager
        self.table = table
        self.title(f"編輯字表：{table['name']}")
        self.transient(manager)

        ttk.Label(self, text="漢一（第一頁，依序貼上要出現的中文字）").grid(
            row=0, column=0, sticky="w", padx=8, pady=(8, 0))
        self.t1 = ScrolledText(self, width=46, height=5)
        self.t1.grid(row=1, column=0, padx=8)
        self.t1.insert("1.0", table.get("zh_tw_1", ""))
        ttk.Label(self, text="漢二（第二頁）").grid(row=2, column=0, sticky="w", padx=8, pady=(8, 0))
        self.t2 = ScrolledText(self, width=46, height=5)
        self.t2.grid(row=3, column=0, padx=8)
        self.t2.insert("1.0", table.get("zh_tw_2", ""))
        bar = ttk.Frame(self)
        bar.grid(row=4, column=0, pady=8)
        ttk.Button(bar, text="儲存", command=self._save).pack(side="left", padx=4)
        ttk.Button(bar, text="關閉", command=self.destroy).pack(side="left", padx=4)

    def _save(self):
        self.table["zh_tw_1"] = self.t1.get("1.0", "end").strip()
        self.table["zh_tw_2"] = self.t2.get("1.0", "end").strip()
        self.manager.app._save()
        self.manager._refresh()
```

並在 `NameTableManager` 上方加一個小工具函式（用 tkinter 內建對話框，避免自製 modal）：

```python
def _ask_name(parent, title, prompt, initial=""):
    from tkinter import simpledialog
    s = simpledialog.askstring(title, prompt, initialvalue=initial, parent=parent)
    return s.strip() if s else ""
```

- [ ] **Step 6: 跑測試確認通過**

Run: `python -m pytest tests/test_gui_smoke.py -v`
Expected: PASS。

- [ ] **Step 7: 全測試**

Run: `python -m pytest tests/ -v`
Expected: PASS（全部）。

- [ ] **Step 8: Commit**

```bash
git add easyrpg_web_gui.py tests/test_gui_smoke.py
git commit -m "feat(gui): 多字表管理清單＋遊戲下拉選字表＋表格顯示字表名"
```

---

## 收尾驗證

- [ ] 跑全套測試：`python -m pytest tests/ -v` → 全綠。
- [ ] 手動 sanity：開 GUI（`python easyrpg_web_gui.py`）→ 字表管理新增兩個字表、編輯字格、遊戲設定下拉選不同字表、主視窗表格顯示字表名稱。（重建需 Docker，可略過或實測。）
- [ ] 用既有舊 `library.json` 開一次，確認舊 `custom_player` 遊戲自動指向遷移字表、不報錯。

## Self-Review 註記（已檢查）

- **Spec 覆蓋**：資料模型(Task1)、建置快取/source.json(Task2)、dist 複製(Task5)、PWA 引擎(Task4)、GUI 管理+下拉(Task6)、library entry(Task3)、向後相容(Task1)皆有對應任務。
- **型別一致**：name_table 形狀 `{id,name,zh_tw_1,zh_tw_2}`、entry/game 用 `name_table_id` 字串、`rebuild_custom_player(table_id, z1, z2, log)` 全程一致。
- **player_fetch**：不再用 `BUNDLED["custom"]` 給 build（改 `customplayer.engine_dir/has_engine`）；`player_fetch.py` 本身不需改（其 custom 變體已無人用，留著不影響）。
