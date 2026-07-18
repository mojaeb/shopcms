"""Theme template tags."""

from django import template

from tenants.theme.engine import ThemeEngine

register = template.Library()


@register.simple_tag(takes_context=True)
def theme_template(context, template_name: str) -> str:
    """Resolve themed template path."""
    store = context.get("store")
    return ThemeEngine().resolve(template_name, store)


@register.simple_tag(takes_context=True)
def theme_include(context, partial: str) -> str:
    """Resolve partial path for includes."""
    store = context.get("store")
    return ThemeEngine().include_path(partial, store)


@register.filter
def theme_asset(theme_slug: str, filename: str) -> str:
    """Build static asset path for theme."""
    return f"/static/themes/{theme_slug}/{filename}"
