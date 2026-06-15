import json
from pathlib import Path

import gencache


def _make_game(root: Path):
    (root / "RPG_RT.ldb").write_text("x")
    (root / "RPG_RT.lmt").write_text("x")
    (root / "easyrpg.soundfont").write_bytes(b"SF2")
    cs = root / "CharSet"
    cs.mkdir()
    (cs / "Hero.png").write_bytes(b"png")
    cfg = root / "Config"
    cfg.mkdir()
    (cfg / "settings.ini").write_text("a=b")


def test_root_files_keep_extension(tmp_path):
    _make_game(tmp_path)
    cache = gencache.generate_index(tmp_path)["cache"]
    assert cache["rpg_rt.ldb"] == "RPG_RT.ldb"
    assert cache["easyrpg.soundfont"] == "easyrpg.soundfont"


def test_subdir_strips_extension_and_has_dirname(tmp_path):
    _make_game(tmp_path)
    cache = gencache.generate_index(tmp_path)["cache"]
    charset = cache["charset"]
    assert charset["_dirname"] == "CharSet"
    assert charset["hero"] == "Hero.png"


def test_ini_keeps_extension_in_subdir(tmp_path):
    _make_game(tmp_path)
    cache = gencache.generate_index(tmp_path)["cache"]
    assert cache["config"]["settings.ini"] == "settings.ini"


def test_metadata_version_2(tmp_path):
    _make_game(tmp_path)
    meta = gencache.generate_index(tmp_path)["metadata"]
    assert meta["version"] == 2
    assert len(meta["date"]) == 10


def test_write_index_writes_utf8_json(tmp_path):
    _make_game(tmp_path)
    out = gencache.write_index(tmp_path)
    assert out == tmp_path / "index.json"
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["metadata"]["version"] == 2
