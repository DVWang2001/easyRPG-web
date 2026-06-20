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
    off, cells = max(runs, key=lambda r: len(set(r[1])))
    assert "".join(cells).startswith(POOL1[:10])
    assert len(cells) >= 70


def test_locate_tables_rejects_repeated_garbage():
    # 一大段重複同字（300 次）＋ 一個真字表（多樣）。應選真字表、剔除重複雜訊。
    garbage = ["脞"] * 300
    data = (b"\x00" * 40 + _table(garbage) + b"\x00" * 40
            + _table(list(POOL1)) + b"\x00" * 40)
    runs = exetable.locate_tables(data, "cp950")
    assert runs
    allchars = set().union(*(set(c) for _, c in runs))
    assert "脞" not in allchars      # 重複雜訊被剔除
    assert "艾" in allchars          # 真字表被選中


def test_extract_two_runs_map_to_two_pages_faithfully(tmp_path):
    # 兩段（兩頁）→ 漢一=第一頁、漢二=第二頁，原字原序保留（忠實還原）
    blob = (b"\x00" * 50 + _table(list(POOL1)) + b"\x00" * 200
            + _table(list(POOL2)) + b"\x00" * 50)
    (tmp_path / "RPG_RT.exe").write_bytes(blob)
    z1, z2 = exetable.extract_pages(tmp_path)
    assert z1 == POOL1[:nametable.CAPACITY]
    assert z2 == POOL2[:nametable.CAPACITY]


def test_extract_keeps_fullwidth_latin_and_digits(tmp_path):
    # 忠實還原：全形英文字母與數字也要原樣保留，不能只留漢字
    page = list("ＡＢＣＤＥ１２３４５") + list(POOL1)   # 前段英數、後段漢字
    (tmp_path / "RPG_RT.exe").write_bytes(b"\x00" * 40 + _table(page) + b"\x00" * 40)
    z1, _ = exetable.extract_pages(tmp_path)
    assert z1.startswith("ＡＢＣＤＥ１２３４５")          # 英數原樣保留
    assert set(POOL1[:10]) <= set(z1)                     # 漢字也在


def test_extract_single_run_splits_two_pages(tmp_path):
    one = list(POOL1 + POOL2)  # 單段、>一頁容量 → 自動切兩頁
    (tmp_path / "RPG_RT.exe").write_bytes(b"\x00" * 50 + _table(one) + b"\x00" * 50)
    z1, z2 = exetable.extract_pages(tmp_path)
    cap = nametable.CAPACITY
    assert len(z1) == cap
    assert z1 + z2 == "".join(one)[:2 * cap]


def test_extract_single_page_fits_one_page(tmp_path):
    # 只有一段、字數 <=一頁 → 全進漢一，漢二空
    one = list(POOL1)  # 70 <= 86
    (tmp_path / "RPG_RT.exe").write_bytes(b"\x00" * 50 + _table(one) + b"\x00" * 50)
    z1, z2 = exetable.extract_pages(tmp_path)
    assert z1 == "".join(one)
    assert z2 == ""


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


def test_extract_pages_missing_exe(tmp_path):
    assert exetable.extract_pages(tmp_path) == ("", "")


def test_extract_pages_no_table_returns_empty(tmp_path):
    (tmp_path / "RPG_RT.exe").write_bytes(b"\x00\x01\x02\x03" * 500)
    assert exetable.extract_pages(tmp_path) == ("", "")
