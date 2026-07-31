"""Tests for color code helpers."""

from products.utils import color_swatch_css, normalize_color_code, parse_color_codes


def test_parse_single_and_multi_colors():
    assert parse_color_codes("#111111") == ["#111111"]
    assert parse_color_codes("#111,#fff") == ["#111", "#fff"]
    assert parse_color_codes("#aaa / #bbb") == ["#aaa", "#bbb"]
    assert parse_color_codes("") == []


def test_normalize_and_swatch():
    assert normalize_color_code("#111 , #222") == "#111,#222"
    assert color_swatch_css("#f00") == "#f00"
    assert "conic-gradient" in color_swatch_css("#111,#fff")
