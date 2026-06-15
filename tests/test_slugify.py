import slugify


def test_basic_lowercase_and_spaces():
    assert slugify.slugify("Hero Quest") == "hero-quest"


def test_unsafe_chars_become_dashes():
    assert slugify.slugify('a/b:c*?"<>|d') == "a-b-c-d"


def test_cjk_becomes_ascii_fallback():
    # 中文名沒有 ASCII 英數 → 退回 "game"（顯示名稱另外保留原文）
    assert slugify.slugify("花嫁之冠") == "game"


def test_slug_is_always_ascii():
    # 核心保證：任何輸入都產出純 ASCII（player 的 ?game= 不解碼，非 ASCII 會壞）
    for name in ["花嫁之冠", "勇者傳說", "2003月藍傳奇i~異界", "教育(漢化)"]:
        assert slugify.slugify(name).isascii()


def test_cjk_names_get_unique_ascii():
    taken = set()
    assert slugify.slugify("花嫁之冠", taken) == "game"
    assert slugify.slugify("勇者傳說", taken) == "game-2"


def test_mixed_keeps_ascii_part():
    assert slugify.slugify("education(已完成)") == "education"


def test_empty_falls_back():
    assert slugify.slugify("   ") == "game"
    assert slugify.slugify("/:*") == "game"


def test_uniqueness_with_taken_set():
    taken = set()
    assert slugify.slugify("Hero", taken) == "hero"
    assert slugify.slugify("Hero", taken) == "hero-2"
    assert slugify.slugify("Hero", taken) == "hero-3"


def test_removes_ampersand():
    assert slugify.slugify("A & B") == "a-b"
