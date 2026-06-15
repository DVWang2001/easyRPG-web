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

    # push must use -f
    push_cmds = [c for c in cmds if "push" in c]
    assert push_cmds, "plan must contain a push command"
    assert any("-f" in c for c in push_cmds), "push must use -f (force)"

    # --work-tree must point at dist
    work_tree_cmds = [c for c in cmds if "--work-tree" in c]
    assert work_tree_cmds, "plan must contain --work-tree commands"
    assert any(str(dist) in c for c in work_tree_cmds), "--work-tree must reference dist"

    # last command must be 'git switch <orig-branch>' to restore the branch
    last = cmds[-1]
    assert last[0] == "git", "last command must be a git command"
    assert last[1] == "switch", "last command must be 'git switch'"
    orig_branch = last[2]
    assert orig_branch and orig_branch != "-", "last command must switch to a real branch name"
