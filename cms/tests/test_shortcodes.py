"""Tests for shortcode engine."""

import pytest

from cms.models import Shortcode
from cms.services.shortcodes import expand_shortcodes, parse_attrs
from tenants.models import Domain, Store, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default-sc", directory="default", is_default=True)
    s = Store.objects.create(name="SC Shop", slug="sc-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="sc.local")
    return s


def test_parse_attrs():
    assert parse_attrs(' src="https://a.com" alt=\'x\' w=10') == {
        "src": "https://a.com",
        "alt": "x",
        "w": "10",
    }


def test_image_shortcode():
    html = expand_shortcodes('[image src="https://cdn.example/a.jpg" alt="عکس"/]')
    assert 'src="https://cdn.example/a.jpg"' in html
    assert 'alt="عکس"' in html
    assert "sc-image" in html
    assert "[image" not in html


def test_grid_1_2_shortcode():
    html = expand_shortcodes("[grid-1-2]<p>a</p><p>b</p>[/grid-1-2]")
    assert 'class="sc-grid sc-grid-1-2"' in html
    assert "<p>a</p><p>b</p>" in html


def test_nested_shortcodes():
    text = (
        '[grid-1-2]'
        '[image src="https://x.com/1.jpg"/]'
        '[image src="https://x.com/2.jpg"/]'
        "[/grid-1-2]"
    )
    html = expand_shortcodes(text)
    assert "sc-grid-1-2" in html
    assert "https://x.com/1.jpg" in html
    assert "https://x.com/2.jpg" in html
    assert "[image" not in html
    assert "[grid" not in html


def test_feature_and_cta_shortcodes():
    html = expand_shortcodes(
        '[feature icon="truck" title="ارسال" text="سریع"/][cta label="خرید" href="/products/"/]'
    )
    assert "sc-feature" in html
    assert "ارسال" in html
    assert 'data-lucide="truck"' in html
    assert 'href="/products/"' in html
    assert "sc-cta" in html


def test_contact_item_shortcode():
    html = expand_shortcodes(
        '[contact-item icon="phone" label="تلفن" value="123" href="tel:123"/]'
    )
    assert "sc-contact-item" in html
    assert 'href="tel:123"' in html
    assert "تلفن" in html
    assert 'data-lucide="phone"' in html
    assert html.strip().startswith("<a ")


def test_note_shortcode():
    html = expand_shortcodes('[note text="ساعات کاری"/]')
    assert "sc-note" in html
    assert "ساعات کاری" in html
    assert "sc-note-text" in html


def test_heading_section_split_shortcodes():
    html = expand_shortcodes(
        '[section tone="soft"]'
        '[heading title="عنوان" text="توضیح"/]'
        '[split image="https://x.com/a.jpg" alt="a"]'
        '[lead text="متن لید"/]'
        "[/split]"
        "[/section]"
    )
    assert 'data-tone="soft"' in html
    assert "sc-heading-title" in html
    assert "عنوان" in html
    assert "sc-split" in html
    assert "https://x.com/a.jpg" in html
    assert "متن لید" in html
    assert "[section" not in html
    assert "[split" not in html


@pytest.mark.django_db
def test_custom_store_shortcode(store):
    Shortcode.objects.create(
        store=store,
        name="box",
        label="باکس",
        html_template='<div class="my-box" data-color="{{color}}">{{content}}</div>',
        is_self_closing=False,
    )
    html = expand_shortcodes('[box color="red"]سلام[/box]', store)
    assert 'class="my-box"' in html
    assert 'data-color="red"' in html
    assert "سلام" in html


@pytest.mark.django_db
def test_store_override_builtin(store):
    Shortcode.objects.create(
        store=store,
        name="image",
        label="تصویر سفارشی",
        html_template='<figure class="custom"><img src="{{src}}" /></figure>',
        is_self_closing=True,
    )
    html = expand_shortcodes('[image src="https://z.com/p.png"/]', store)
    assert "<figure class=\"custom\">" in html
    assert "sc-image" not in html
