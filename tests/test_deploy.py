from pathlib import Path

import deploy


def test_deploy_dry_run_returns_git_plan(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("x")

    cmds = deploy.deploy_gh_pages(dist, branch="gh-pages", dry_run=True)

    joined = "\n".join(" ".join(c) for c in cmds)
    # 推到 gh-pages、且用 -f（強制全量取代）
    assert "gh-pages" in joined
    push_cmds = [c for c in cmds if "push" in c]
    assert push_cmds, "plan must contain a push command"
    assert any("-f" in c for c in push_cmds), "push must use -f (force)"
    # 推送目標是 refs/heads/gh-pages
    assert any("refs/heads/gh-pages" in arg for c in cmds for arg in c)
    # 用 git plumbing：write-tree + commit-tree（不切換分支、不依賴本機 gh-pages 是否存在）
    assert any(c[:2] == ["git", "write-tree"] for c in cmds)
    assert any(c[:2] == ["git", "commit-tree"] for c in cmds)
    # 不再切換分支（舊的 git switch --orphan 在本機已有 gh-pages 時會 exit 128）
    assert not any("switch" in c for c in cmds), "plan must not switch branches"
