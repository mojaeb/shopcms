"""Cache key builders for ShopCMS namespaces."""


def product_filter_options(store_id: int, category_slug: str | None = None) -> str:
    suffix = category_slug or "all"
    return f"shopcms:products:{store_id}:filter_options:{suffix}"


def product_list(store_id: int, params_hash: str) -> str:
    return f"shopcms:products:{store_id}:list:{params_hash}"


def product_detail(store_id: int, slug: str) -> str:
    return f"shopcms:products:{store_id}:detail:{slug}"


def report_summary(store_id: int, days: int) -> str:
    return f"shopcms:reports:{store_id}:summary:{days}"


def report_sales(store_id: int, days: int) -> str:
    return f"shopcms:reports:{store_id}:sales:{days}"


def cms_page(store_id: int, slug: str) -> str:
    return f"shopcms:cms:{store_id}:page:{slug}"


def blog_list(store_id: int, params_hash: str) -> str:
    return f"shopcms:blog:{store_id}:list:{params_hash}"


def blog_detail(store_id: int, slug: str) -> str:
    return f"shopcms:blog:{store_id}:detail:{slug}"


def store_namespace(store_id: int) -> str:
    return f"shopcms:store:{store_id}:*"
