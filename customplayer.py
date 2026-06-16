"""用 Docker 容器重編 EasyRPG Player 自訂網頁播放器（套用自訂取名字表）。

需要本機有 Docker，且已建好 `ezbuild` 容器與依賴（見 players/build/）。
依賴只需建一次；之後改字重編只重編 Player 本體（數分鐘）。
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import nametable

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "players" / "build" / "src-ref" / "window_keyboard.cpp"
CUSTOM_DIR = HERE / "players" / "custom"
CONTAINER = "ezbuild"
PLAYER_FILES = ("index.html", "index.js", "index.wasm")
_LIBLCF = "/work/buildscripts/emscripten/lib/pkgconfig/liblcf.pc"
_OUT = "/work/Player/build/emscripten-release"


class BuildEnvError(RuntimeError):
    """Docker / 建置環境不齊全。"""


def _log(log, msg):
    if not log:
        return
    try:
        log(msg)
    except UnicodeEncodeError:
        # 某些主控台(如 Windows cp950)無法編碼 ✓ 等字元;退而求其次。
        log(msg.encode("ascii", "replace").decode("ascii"))


def check_env() -> None:
    """確認 docker 可用、容器在跑、依賴已建好；否則丟 BuildEnvError。"""
    if not shutil.which("docker"):
        raise BuildEnvError("找不到 docker —— 請先安裝並啟動 Docker Desktop。")
    r = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", CONTAINER],
                       capture_output=True, text=True)
    if r.returncode != 0 or r.stdout.strip() != "true":
        raise BuildEnvError(
            f"建置容器「{CONTAINER}」不存在或未啟動。請先依 players/build/README.md 建立環境。")
    r = subprocess.run(["docker", "exec", CONTAINER, "test", "-f", _LIBLCF])
    if r.returncode != 0:
        raise BuildEnvError("容器內依賴尚未建好（缺 liblcf）。請先執行依賴建置（deps.sh）。")


def _stream(cmd, log) -> None:
    _log(log, "$ " + " ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        _log(log, line.rstrip())
    code = proc.wait()
    if code != 0:
        raise BuildEnvError(f"指令失敗（exit {code}）：{' '.join(cmd)}")


def rebuild_custom_player(zh_tw_1: str, zh_tw_2: str, log=None) -> Path:
    """產生自訂取名字表 → 容器內重編 → 把 index.html/js/wasm 複製到 players/custom/。"""
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

    _log(log, "取出 index.html/js/wasm 到 players/custom/…")
    CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
    for fn in PLAYER_FILES:
        _stream(["docker", "cp", f"{CONTAINER}:{_OUT}/{fn}", str(CUSTOM_DIR / fn)], log)

    _log(log, f"✓ 自訂播放器已更新：{CUSTOM_DIR}")
    return CUSTOM_DIR
