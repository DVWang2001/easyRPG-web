from pathlib import Path

import deploy


def test_deploy_dry_run_returns_git_plan(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("x")

    cmds = deploy.deploy_gh_pages(dist, branch="gh-pages", dry_run=True)

    joined = "\n".join(" ".join(c) for c in cmds)
    assert "gh-pages" in joined
    assert any("push" in c for c in cmds)
