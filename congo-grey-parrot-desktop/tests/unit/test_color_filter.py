from congo_grey_parrot.ui.color_filter import FILTERS, android_color_matrix, invert_hex_colors, map_color


def test_filter_names():
    assert FILTERS == (
        "none",
        "invert",
        "smart_invert",
        "protanopia",
        "deuteranopia",
        "tritanopia",
        "grayscale",
    )


def test_invert_and_grayscale():
    assert map_color("invert", 1, 1, 1) == (0, 0, 0)
    assert map_color("invert", 0, 0, 0) == (1, 1, 1)
    red, green, blue = map_color("grayscale", 1, 0, 0)
    assert red == green == blue
    assert abs(red - 0.2126) < 1e-4


def test_color_filters_separate_red_and_green():
    for name in ("protanopia", "deuteranopia", "tritanopia"):
        red = map_color(name, 1, 0, 0)
        green = map_color(name, 0, 1, 0)
        distance = sum(abs(left - right) for left, right in zip(red, green))
        assert distance > 0.2
        assert android_color_matrix(name) is not None
        assert len(android_color_matrix(name)) == 20


def test_named_dark_themes():
    from congo_grey_parrot.ui.theme import THEMES, build_stylesheet

    expected = {
        "kuro": "#6d46c2",
        "pink_void": "#b43b78",
        "red_void": "#b43b3b",
        "yellow_void": "#1a1404",
    }
    for name, color in expected.items():
        assert name in THEMES
        assert color in build_stylesheet(name)


def test_smart_invert_flips_stylesheet_colors():
    assert invert_hex_colors("background: #000000; color: #ffffff;") == "background: #ffffff; color: #000000;"
    assert android_color_matrix("smart_invert") is None
    assert android_color_matrix("none") is None
