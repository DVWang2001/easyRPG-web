import os
import stat

import easyrpg_web_build as core


def test_force_rmtree_removes_readonly_files(tmp_path):
    # 模擬 RPG Maker 唯讀素材被 copy2 帶進 dist 後，重建時 rmtree 要能清掉。
    d = tmp_path / "dist"
    (d / "games" / "1" / "Music").mkdir(parents=True)
    f = d / "games" / "1" / "Music" / "ro.mid"
    f.write_bytes(b"MThd")
    os.chmod(f, stat.S_IREAD)  # 唯讀

    core._force_rmtree(d)

    assert not d.exists()


def test_force_rmtree_missing_path_is_ok(tmp_path):
    # 不存在的路徑不該丟例外（呼叫端只在 exists() 時用，但保險）。
    core._force_rmtree(tmp_path / "nope")
