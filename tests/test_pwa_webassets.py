import pwa


def test_install_web_assets_copies_js_css(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    copied = pwa.install_web_assets(dist)
    # 受版控的前端資產都複製進 dist（firebase-config.js 已 gitignore，新 clone 不一定有，不在此斷言）
    for name in ("account.js", "walkthrough.js", "walkthrough.css",
                 "community.js", "community.css",
                 "favorites.js", "favorites.css", "playtime.js",
                 "profile.js", "profile.css",
                 "savepanel.js", "savepanel.css",
                 "popular.js", "popular.css",
                 "announce.js", "announce.css"):
        assert (dist / name).exists(), name
        assert name in copied
    # 規則檔是給 Console 用的 artifact，不部署
    assert not (dist / "firestore.rules").exists()
    # 金鑰範本不部署（站長填好的真實 firebase-config.js 才部署）
    assert not (dist / "firebase-config.example.js").exists()
    assert "firebase-config.example.js" not in copied


def test_playtime_has_no_toplevel_firebase_import():
    """離線時 gstatic 抓不到；頂層 import 會讓整支模組不執行，一秒都記不到。"""
    src = (pwa.WEB_DIR / "playtime.js").read_text(encoding="utf-8")
    for line in src.splitlines():
        assert not line.startswith("import "), line
        assert not line.startswith("} from"), line
