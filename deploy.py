"""把 dist/ 內容 push 到 gh-pages 分支（GitHub Pages）。

用 git plumbing：以暫存 index 把 dist 當工作樹做出一棵 tree → commit-tree → 直接
force-push 到 refs/heads/gh-pages。全程不切換分支、不動主工作樹與主 index，因此不論
本機是否已存在 gh-pages 分支都能運作（舊作法 `git switch --orphan gh-pages` 在本機
已有該分支時會 fatal: a branch named 'gh-pages' already exists / exit 128）。
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

_MSG = "deploy: 更新 GitHub Pages"


def _plan(branch: str, remote: str) -> list:
    """dry-run 用的指令樣板（tree/commit 為真執行時才產生，這裡用佔位字串）。"""
    ref = f"refs/heads/{branch}"
    return [
        ["git", "add", "-A"],
        ["git", "write-tree"],
        ["git", "commit-tree", "<tree>", "-m", _MSG],
        ["git", "push", "-f", remote, f"<commit>:{ref}"],
    ]


def deploy_gh_pages(dist, remote: str = "origin", branch: str = "gh-pages",
                    dry_run: bool = False, log=None) -> list:
    dist = Path(dist).resolve()
    ref = f"refs/heads/{branch}"
    if dry_run:
        return _plan(branch, remote)

    # 暫存 index + 把 dist 當工作樹；不影響主 index/工作樹。
    index_file = Path(tempfile.gettempdir()) / f"easyrpg-web-deploy-{os.getpid()}.index"
    env = {**os.environ,
           "GIT_INDEX_FILE": str(index_file),
           "GIT_WORK_TREE": str(dist)}

    def run(cmd, capture=False):
        if log:
            log("$ " + " ".join(cmd))
        if capture:
            return subprocess.check_output(cmd, env=env, text=True).strip()
        subprocess.run(cmd, env=env, check=True)
        return None

    try:
        run(["git", "add", "-A"])
        tree = run(["git", "write-tree"], capture=True)
        commit = run(["git", "commit-tree", tree, "-m", _MSG], capture=True)
        run(["git", "push", "-f", remote, f"{commit}:{ref}"])
    finally:
        try:
            index_file.unlink()
        except OSError:
            pass

    return [
        ["git", "add", "-A"],
        ["git", "write-tree"],
        ["git", "commit-tree", tree, "-m", _MSG],
        ["git", "push", "-f", remote, f"{commit}:{ref}"],
    ]
