"""下載、快取並解壓 EasyRPG 官方預編 web player（WASM）。"""
from __future__ import annotations

import shutil
import tarfile
import urllib.request
from pathlib import Path

PLAYER_URL = "https://easyrpg.org/downloads/player/latest/easyrpg-player-latest-js.tar.gz"

HERE = Path(__file__).resolve().parent
# 本機並存的播放器：official＝官方版備份、custom＝自建（自訂取名字表）。
BUNDLED = {
    "official": HERE / "players" / "official",
    "custom": HERE / "players" / "custom",
}
PLAYER_FILES = ("index.html", "index.js", "index.wasm")


def _has_player_files(d: Path) -> bool:
    return all((d / f).exists() for f in PLAYER_FILES)


def _download(url: str, dest: Path, timeout: int = 120) -> None:
    with urllib.request.urlopen(url, timeout=timeout) as resp, open(dest, "wb") as f:
        shutil.copyfileobj(resp, f)


def _find_player_root(extracted: Path) -> Path:
    """回傳含 index.wasm 的目錄（tarball 可能多包一層）。"""
    for wasm in extracted.rglob("index.wasm"):
        return wasm.parent
    raise FileNotFoundError("解壓後找不到 index.wasm，下載的 player 格式可能變了。")


def ensure_player(cache_dir, url: str = PLAYER_URL, refresh: bool = False,
                  variant: str = "auto") -> Path:
    # variant: "auto"＝下載官方最新（預設，行為不變）；"custom"/"official"＝用本機並存版本。
    if variant in BUNDLED:
        d = BUNDLED[variant]
        if _has_player_files(d):
            return d
        raise FileNotFoundError(
            f"找不到「{variant}」播放器：{d}（需含 index.html/index.js/index.wasm）")

    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    tarball = cache_dir / "easyrpg-player-latest-js.tar.gz"
    extracted = cache_dir / "player"

    if refresh:
        if tarball.exists():
            tarball.unlink()
        if extracted.exists():
            shutil.rmtree(extracted)

    if not tarball.exists():
        _download(url, tarball)

    if not extracted.exists():
        extracted.mkdir(parents=True)
        with tarfile.open(tarball, "r:gz") as tar:
            tar.extractall(extracted, filter="data")

    return _find_player_root(extracted)
