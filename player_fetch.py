"""下載、快取並解壓 EasyRPG 官方預編 web player（WASM）。"""
from __future__ import annotations

import shutil
import tarfile
import urllib.request
from pathlib import Path

PLAYER_URL = "https://easyrpg.org/downloads/player/latest/easyrpg-player-latest-js.tar.gz"


def _find_player_root(extracted: Path) -> Path:
    """回傳含 index.wasm 的目錄（tarball 可能多包一層）。"""
    for wasm in extracted.rglob("index.wasm"):
        return wasm.parent
    raise FileNotFoundError("解壓後找不到 index.wasm，下載的 player 格式可能變了。")


def ensure_player(cache_dir, url: str = PLAYER_URL, refresh: bool = False) -> Path:
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
        urllib.request.urlretrieve(url, tarball)

    if not extracted.exists():
        extracted.mkdir(parents=True)
        with tarfile.open(tarball, "r:gz") as tar:
            tar.extractall(extracted)

    return _find_player_root(extracted)
