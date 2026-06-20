import exetable
import nametable

# 真實字表是「幾乎全不同字」的；測試用實際 Big5 名字用字（取自真實遊戲鍵盤）。
POOL1 = ("艾芙萊荷英莫茵莉茲莎菲葵夢葛蕾蓋薩華蘭蘇琪理瑪瑞瓊妲妮姬姆娜"
         "林森札杜柏格柯梅樂雨雷電雪雲零宇宙安空寧賓賽汀沃沙法洛波派凌"
         "溫湯思恩意愛絲紅紗約")                                            # 70 不同字
POOL2 = ("納緹緣維紫索夜代依伊俠修倫傑迪達遜提拉捷拿示奈席摩雅羅科利列阿"
         "隆德衛比門哈狄特路斯凱頓歐諾勒吉昆夏麥黎泰喬曼魯爾麗嘉可亞西瓦"
         "司貝因巴尼凡丹弗金史克布卡米日月明聖")                            # 多個不同字


def _cell(ch, stride=12):
    b = ch.encode("cp950")
    return b + b"\x00" * (stride - len(b))


def _table(chars, stride=12):
    return b"".join(_cell(c, stride) for c in chars)


def test_read_encoding_default_big5(tmp_path):
    assert exetable.read_encoding(tmp_path) == "cp950"


def test_read_encoding_from_ini(tmp_path):
    (tmp_path / "RPG_RT.ini").write_text(
        "[RPG_RT]\nGameTitle=x\n[EasyRPG]\nEncoding=936\n", encoding="utf-8")
    assert exetable.read_encoding(tmp_path) == "gbk"


def test_read_encoding_unknown_falls_back(tmp_path):
    (tmp_path / "RPG_RT.ini").write_text("[EasyRPG]\nEncoding=\n", encoding="utf-8")
    assert exetable.read_encoding(tmp_path) == "cp950"


def test_is_keyboard_cell():
    assert exetable.is_keyboard_cell("艾".encode("cp950"), "cp950") == "艾"
    assert exetable.is_keyboard_cell("１".encode("cp950"), "cp950") == "１"   # 全形數字
    assert exetable.is_keyboard_cell(b"\x00\x01", "cp950") is None
    assert exetable.is_keyboard_cell(b"A", "cp950") is None                   # 不足 2 bytes


def test_locate_tables_finds_run_among_noise():
    data = b"\x00" * 100 + _table(list(POOL1)) + b"\xff" * 100
    runs = exetable.locate_tables(data, "cp950")
    assert runs
    off, cells, stride = max(runs, key=lambda r: len(set(r[1])))
    assert "".join(cells).startswith(POOL1[:10])
    assert len(cells) >= 70
    assert stride == 12


def test_locate_tables_rejects_repeated_garbage():
    # 一大段重複同字（300 次）＋ 一個真字表（多樣）。應選真字表、剔除重複雜訊。
    garbage = ["脞"] * 300
    data = (b"\x00" * 40 + _table(garbage) + b"\x00" * 40
            + _table(list(POOL1)) + b"\x00" * 40)
    runs = exetable.locate_tables(data, "cp950")
    assert runs
    allchars = set().union(*(set(r[1]) for r in runs))
    assert "脞" not in allchars      # 重複雜訊被剔除
    assert "艾" in allchars          # 真字表被選中


def _labeled(chars, label, stride=12):
    """字表段後面接一個 <label> 頁籤控制格（模擬 exe 結構）。"""
    return _table(chars, stride) + b"\x3c" + label.encode("cp950") + b"\x3e" + b"\x00" * 10


def test_extract_two_pages_with_labels(tmp_path):
    # 兩段（兩頁）→ 各自一頁，原字原序保留，頁名從 <…> 抽出（忠實還原）
    blob = (b"\x00" * 50 + _labeled(list(POOL1), "頁１") + b"\x00" * 200
            + _labeled(list(POOL2), "頁２") + b"\x00" * 50)
    (tmp_path / "RPG_RT.exe").write_bytes(blob)
    pages = exetable.extract_table(tmp_path)
    assert len(pages) == 2
    assert pages[0] == {"label": "頁１", "chars": POOL1[:nametable.CAPACITY]}
    assert pages[1] == {"label": "頁２", "chars": POOL2[:nametable.CAPACITY]}


def test_extract_label_defaults_when_absent(tmp_path):
    (tmp_path / "RPG_RT.exe").write_bytes(b"\x00" * 50 + _table(list(POOL1)) + b"\x00" * 50)
    pages = exetable.extract_table(tmp_path)
    assert pages[0]["label"] == "頁1"     # 抽不到 <…> → 頁N


def test_extract_keeps_fullwidth_latin_and_digits(tmp_path):
    # 忠實還原：全形英文字母與數字也要原樣保留，不能只留漢字
    page = list("ＡＢＣＤＥ１２３４５") + list(POOL1)
    (tmp_path / "RPG_RT.exe").write_bytes(b"\x00" * 40 + _table(page) + b"\x00" * 40)
    chars = exetable.extract_table(tmp_path)[0]["chars"]
    assert chars.startswith("ＡＢＣＤＥ１２３４５")        # 英數原樣保留
    assert set(POOL1[:10]) <= set(chars)                   # 漢字也在


def test_extract_caps_each_page(tmp_path):
    big = list(POOL1 + POOL2)  # 單段、>一頁容量
    (tmp_path / "RPG_RT.exe").write_bytes(b"\x00" * 50 + _table(big) + b"\x00" * 50)
    pages = exetable.extract_table(tmp_path)
    assert len(pages[0]["chars"]) == nametable.CAPACITY


def test_extract_handles_fullwidth_latin_prefix(tmp_path):
    # 鍵盤前幾列是全形英文字母（Ａ-Ｚ ａ-ｚ）時不該中斷字表偵測；
    # 忠實還原 → 英文與後段漢字都要保留。
    latin = list("ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
                 "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔ")          # 46 全形英文
    han = list("子力小大天中太夫月幻日毛文古艾白玉世冬加卡平多巧弗米西安")  # 28 漢字
    (tmp_path / "RPG_RT.exe").write_bytes(b"\x00" * 40 + _table(latin + han) + b"\x00" * 40)
    chars = exetable.extract_chars(tmp_path)
    assert set("子力小大天中太夫") <= set(chars)             # 漢字保留
    assert "Ａ" in chars and "ａ" in chars                   # 全形英文也保留（忠實）


def test_is_keyboard_cell_accepts_fullwidth_latin():
    assert exetable.is_keyboard_cell("Ａ".encode("cp950"), "cp950") == "Ａ"
    assert exetable.is_keyboard_cell("ｚ".encode("cp950"), "cp950") == "ｚ"


def test_recognize_shengling_huoshen():
    pages = [
        {"label": "頁２", "chars": "ＡＢＣ子力小大天中太夫月幻日毛文古艾白玉世冬加"},
        {"label": "頁１", "chars": "貝利芙芬拉欣東雨依武秀金耶肯青法奇皇宜兒昂哈思"},
    ]
    assert exetable.recognize(pages) == "聖靈火神2003字表"


def test_recognize_unknown_returns_empty():
    assert exetable.recognize([{"label": "頁１", "chars": "甲乙丙丁戊"}]) == ""
    assert exetable.recognize([]) == ""


def test_identify_engine_don_miguel(tmp_path):
    # exe 含 Don Miguel RM2000 鍵盤特徵（半形英數）→ 辨識但不抽中文字表
    (tmp_path / "RPG_RT.exe").write_bytes(
        b"\x00garbage\x24\x00\x00\x001234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ\x00code")
    assert exetable.identify_engine(tmp_path) == "Don Miguel RM2000 英文字表"
    assert exetable.extract_table(tmp_path) == []   # 不抽成中文字表


def test_identify_engine_unknown(tmp_path):
    (tmp_path / "RPG_RT.exe").write_bytes(b"\x00" * 200)
    assert exetable.identify_engine(tmp_path) == ""
    assert exetable.identify_engine(tmp_path / "nope") == ""


def test_extract_missing_exe(tmp_path):
    assert exetable.extract_table(tmp_path) == []


def test_extract_no_table_returns_empty(tmp_path):
    (tmp_path / "RPG_RT.exe").write_bytes(b"\x00\x01\x02\x03" * 500)
    assert exetable.extract_table(tmp_path) == []
