from pathlib import Path

import pwa


def test_patch_index_html_injects_pwa_tags(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text(
        "<html><head><title>EasyRPG</title></head><body>x</body></html>",
        encoding="utf-8",
    )

    pwa.patch_index_html(dist, "花嫁之冠", "icons/icon.png")

    html = (dist / "index.html").read_text(encoding="utf-8")
    assert 'rel="manifest"' in html
    assert 'manifest.webmanifest' in html
    assert 'apple-touch-icon' in html
    assert 'apple-mobile-web-app-capable' in html
    assert 'serviceWorker' in html
    assert html.count("</head>") == 1


def test_patch_index_html_without_head_uses_body(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html><body>x</body></html>", encoding="utf-8")

    pwa.patch_index_html(dist, "App", "icons/icon.png")

    html = (dist / "index.html").read_text(encoding="utf-8")
    assert 'rel="manifest"' in html
    assert 'serviceWorker' in html
