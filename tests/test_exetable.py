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


def test_extract_collects_all_tables_dedup_han_only(tmp_path):
    digits = list("１２３４５６７８９０")
    # 兩段字表（中間夾數字列＋空白隔開）→ 應收集兩段的漢字、濾掉全形數字
    blob = (b"\x00" * 50 + _table(list(POOL1)) + _table(digits)
            + b"\x00" * 200 + _table(list(POOL2)) + b"\x00" * 50)
    (tmp_path / "RPG_RT.exe").write_bytes(blob)
    chars = exetable.extract_chars(tmp_path)
    assert chars.startswith(POOL1[:10])
    assert set(POOL1) <= set(chars) and set(POOL2) <= set(chars)   # 兩段都收進來
    assert all(0x4E00 <= ord(c) <= 0x9FFF for c in chars)          # 只有漢字
    assert "１" not in chars                                       # 全形數字被濾掉
    assert len(chars) == len(set(chars))                           # 去重


def test_extract_pages_reflow_two_pages(tmp_path):
    blob = (b"\x00" * 50 + _table(list(POOL1)) + b"\x00" * 200
            + _table(list(POOL2)) + b"\x00" * 50)
    (tmp_path / "RPG_RT.exe").write_bytes(blob)
    chars = exetable.extract_chars(tmp_path)
    z1, z2 = exetable.extract_pages(tmp_path)
    cap = nametable.CAPACITY
    assert len(z1) == cap                 # 總字數 > 一頁 → 第一頁填滿
    assert z1 == chars[:cap]
    assert z2 == chars[cap:2 * cap]       # 其餘溢到第二頁


def test_extract_pages_single_table_fits_one_page(tmp_path):
    # 只有一段、字數 <=一頁 → 全進漢一，漢二空（如某些遊戲只有一頁鍵盤）
    one = list(POOL1)[:nametable.CAPACITY]
    (tmp_path / "RPG_RT.exe").write_bytes(b"\x00" * 50 + _table(one) + b"\x00" * 50)
    z1, z2 = exetable.extract_pages(tmp_path)
    assert z1 == "".join(one)
    assert z2 == ""


def test_extract_pages_caps_at_two_pages(tmp_path):
    big = list(POOL1 + POOL2)  # >172 不可能，但 >86 可測上限
    (tmp_path / "RPG_RT.exe").write_bytes(b"\x00" * 50 + _table(big) + b"\x00" * 50)
    z1, z2 = exetable.extract_pages(tmp_path)
    assert len(z1) == nametable.CAPACITY
    assert len(z1) + len(z2) <= 2 * nametable.CAPACITY


def test_extract_pages_missing_exe(tmp_path):
    assert exetable.extract_pages(tmp_path) == ("", "")


def test_extract_pages_no_table_returns_empty(tmp_path):
    (tmp_path / "RPG_RT.exe").write_bytes(b"\x00\x01\x02\x03" * 500)
    assert exetable.extract_pages(tmp_path) == ("", "")
