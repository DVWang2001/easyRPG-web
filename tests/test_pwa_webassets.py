import pwa


def test_install_web_assets_copies_js_css(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    copied = pwa.install_web_assets(dist)
    # 地基與功能的前端資產都複製進 dist
    for name in ("account.js", "walkthrough.js", "walkthrough.css", "firebase-config.js"):
        assert (dist / name).exists(), name
        assert name in copied
    # 規則檔是給 Console 用的 artifact，不部署
    assert not (dist / "firestore.rules").exists()
