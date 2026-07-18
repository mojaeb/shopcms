"""Cache key builders for ShopCMS namespaces."""


def product_filter_options(store_id: int, category_slug: str | None = None) -> str:
    suffix = category_slug or "all"
    return f"shopcms:products:{store_id}:filter_options:{suffix}"


def report_summary(store_id: int, days: int) -> str:
    return f"shopcms:reports:{store_id}:summary:{days}"


def report_sales(store_id: int, days: int) -> str:
    return f"shopcms:reports:{store_id}:sales:{days}"


def store_namespace(store_id: int) -> str:
    return f"shopcms:store:{store_id}:*"
