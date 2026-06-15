"""CLI 核心：把 RPG Maker 遊戲打包成 EasyRPG 網頁版/PWA（dist/）。"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import gencache
import library
import menu
import player_fetch
import pwa
import slugify
import staging

HERE = Path(__file__).resolve().parent
DEFAULT_SOUNDFONT = HERE / "assets" / "easyrpg.soundfont"
DEFAULT_ICON = HERE / "assets" / "app_icon.png"
PLAYER_FILES = ("index.html", "index.js", "index.wasm")


class BuildError(Exception):
    pass


def _log(msg, cb=None):
    if cb:
        cb(msg)
    else:
        print(msg)


def _validate_game(game: Path, label=None):
    who = f"遊戲「{label}」" if label else "遊戲資料夾"
    if not game.is_dir():
        raise BuildError(f"{who}不存在：{game}")
    has_db = any((game / n).exists() for n in ("RPG_RT.ldb", "RPG_RT.lmt"))
    if not has_db:
        raise BuildError(f"{who}不是合法的 RPG Maker 2000/2003 遊戲（缺 RPG_RT.ldb/.lmt）：{game}")


def _read_exclude_file(path) -> list:
    if not path:
        return []
    return [ln.strip() for ln in Path(path).read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")]


def build(*, game, app_label=None, soundfont=DEFAULT_SOUNDFONT, app_icon=DEFAULT_ICON,
          rtp=None, out="dist", ignore=None, exclude_file=None,
          refresh_player=False, deploy=False, player_cache=".player-cache",
          player_url=player_fetch.PLAYER_URL, log=None) -> Path:
    game = Path(game)
    out = Path(out)
    _validate_game(game)
    app_label = app_label or game.name

    _log("下載/取用 web player…", log)
    player_dir = player_fetch.ensure_player(player_cache, url=player_url, refresh=refresh_player)

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for name in PLAYER_FILES:
        shutil.copy2(player_dir / name, out / name)

    _log("整理遊戲資料…", log)
    game_dest = out / "games" / "default"
    ignore_globs = tuple(ignore) if ignore else staging.DEFAULT_IGNORE
    staging.stage_game(
        game, game_dest, ignore_globs=ignore_globs,
        exclude_paths=_read_exclude_file(exclude_file),
        soundfont=soundfont, rtp=rtp,
    )

    _log("產生 index.json（gencache）…", log)
    gencache.write_index(game_dest)

    _log("鋪 PWA 外殼…", log)
    if app_icon:
        icon_rel = pwa.install_icon(out, app_icon)
    else:
        _log("警告：未提供 app_icon，PWA 安裝圖示將缺失（icons/icon.png 不存在）。", log)
        icon_rel = pwa.ICON_REL
    pwa.write_manifest(out, app_label, icon_rel)
    pwa.patch_index_html(out, app_label, icon_rel)
    pwa.write_service_worker(out)

    if deploy:
        import deploy as deploy_mod
        _log("部署到 GitHub Pages…", log)
        deploy_mod.deploy_gh_pages(out, log=log)

    _log(f"完成：{out}", log)
    return out


def build_library(*, games, app_label="我的遊戲庫", app_icon=DEFAULT_ICON,
                  soundfont=DEFAULT_SOUNDFONT, out="dist", ignore=None,
                  refresh_player=False, deploy=False, player_cache=".player-cache",
                  player_url=player_fetch.PLAYER_URL, log=None) -> Path:
    out = Path(out)
    if not games:
        raise BuildError("遊戲庫至少要一個遊戲。")

    specs = [dict(g) for g in games]
    taken = set()
    for g in specs:
        folder = Path(g["folder"])
        label = g.get("label") or folder.name
        _validate_game(folder, label)
        g["folder"] = folder
        g["label"] = label
        g["slug"] = slugify.slugify(label, taken)

    _log("下載/取用 web player…", log)
    player_dir = player_fetch.ensure_player(player_cache, url=player_url, refresh=refresh_player)

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for name in PLAYER_FILES:
        shutil.copy2(player_dir / name, out / name)

    if app_icon:
        icon_rel = pwa.install_icon(out, app_icon)
    else:
        _log("警告：未提供 app_icon，PWA 安裝圖示將缺失（icons/icon.png 不存在）。", log)
        icon_rel = pwa.ICON_REL
    pwa.patch_index_html(out, app_label, icon_rel)   # 先 patch player 的 index.html
    (out / "index.html").rename(out / "play.html")    # player → play.html

    _log("整理各遊戲…", log)
    ignore_globs = tuple(ignore) if ignore else staging.DEFAULT_IGNORE
    entries = library.stage_library(out, specs, soundfont=soundfont, ignore_globs=ignore_globs)

    _log("產生遊戲庫選單…", log)
    menu.write_menu(out, app_label, entries, icon_rel)  # 寫新的 index.html（網格）

    pwa.write_manifest(out, app_label, icon_rel)
    pwa.write_service_worker(out)                        # 最後：precache 全部資產

    if deploy:
        import deploy as deploy_mod
        _log("部署到 GitHub Pages…", log)
        deploy_mod.deploy_gh_pages(out, log=log)

    _log(f"完成：{out}", log)
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description="把 RPG Maker 遊戲打包成 EasyRPG 網頁版/PWA")
    p.add_argument("--game", required=True, help="遊戲資料夾（含 RPG_RT.ldb/.lmt）")
    p.add_argument("--app-label", default=None, help="App 顯示名稱（預設＝資料夾名）")
    p.add_argument("--soundfont", default=str(DEFAULT_SOUNDFONT))
    p.add_argument("--app-icon", default=str(DEFAULT_ICON))
    p.add_argument("--rtp", default=None)
    p.add_argument("--out", default="dist")
    p.add_argument("--ignore", action="append", default=None, help="忽略 glob（可重複）")
    p.add_argument("--exclude-file", default=None)
    p.add_argument("--refresh-player", action="store_true")
    p.add_argument("--deploy", action="store_true")
    args = p.parse_args(argv)
    try:
        build(
            game=args.game, app_label=args.app_label, soundfont=args.soundfont,
            app_icon=args.app_icon, rtp=args.rtp, out=args.out, ignore=args.ignore,
            exclude_file=args.exclude_file, refresh_player=args.refresh_player,
            deploy=args.deploy,
        )
    except BuildError as e:
        print("錯誤：", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
