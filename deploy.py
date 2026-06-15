"""把 dist/ 內容 push 到 gh-pages 分支（GitHub Pages）。"""
from __future__ import annotations

import subprocess
from pathlib import Path


def _plan(dist: Path, remote: str, branch: str) -> list:
    # 用 git 的 --work-tree 把 dist 當工作樹，提交到孤立分支再 push。
    return [
        ["git", "switch", "--orphan", branch],
        ["git", "--work-tree", str(dist), "add", "-A"],
        ["git", "--work-tree", str(dist), "commit", "-m", "deploy: 更新 GitHub Pages"],
        ["git", "push", "-f", remote, branch],
    ]


def deploy_gh_pages(dist, remote: str = "origin", branch: str = "gh-pages",
                    dry_run: bool = False, log=None) -> list:
    dist = Path(dist)
    cmds = _plan(dist, remote, branch)
    if dry_run:
        return cmds
    for cmd in cmds:
        if log:
            log("$ " + " ".join(cmd))
        subprocess.run(cmd, check=True)
    return cmds
