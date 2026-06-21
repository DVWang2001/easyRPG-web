import pwa


def test_install_web_assets_copies_js_css(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    copied = pwa.install_web_assets(dist)
    # 受版控的前端資產都複製進 dist（firebase-config.js 已 gitignore，新 clone 不一定有，不在此斷言）
    for name in ("account.js", "walkthrough.js", "walkthrough.css",
                 "community.js", "community.css"):
        assert (dist / name).exists(), name
        assert name in copied
    # 規則檔是給 Console 用的 artifact，不部署
    assert not (dist / "firestore.rules").exists()
    # 金鑰範本不部署（站長填好的真實 firebase-config.js 才部署）
    assert not (dist / "firebase-config.example.js").exists()
    assert "firebase-config.example.js" not in copied
