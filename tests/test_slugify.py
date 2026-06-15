import slugify


def test_basic_lowercase_and_spaces():
    assert slugify.slugify("Hero Quest") == "hero-quest"


def test_removes_unsafe_chars():
    assert slugify.slugify('a/b:c*?"<>|d') == "abcd"


def test_keeps_cjk():
    assert slugify.slugify("花嫁之冠") == "花嫁之冠"


def test_empty_falls_back():
    assert slugify.slugify("   ") == "game"
    assert slugify.slugify("/:*") == "game"


def test_uniqueness_with_taken_set():
    taken = set()
    assert slugify.slugify("Hero", taken) == "hero"
    assert slugify.slugify("Hero", taken) == "hero-2"
    assert slugify.slugify("Hero", taken) == "hero-3"
