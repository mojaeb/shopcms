"""Super Admin API schemas."""

from ninja import Schema


class DashboardStatsSchema(Schema):
    total_stores: int
    active_stores: int
    inactive_stores: int
    total_domains: int
    total_themes: int
    total_plugins: int


class ThemeSchema(Schema):
    id: int
    name: str
    slug: str
    directory: str
    is_default: bool


class StoreListSchema(Schema):
    id: int
    name: str
    slug: str
    store_type: str
    status: str
    currency: str
    theme_slug: str | None = None
    domain_count: int = 0
    member_count: int = 0
    tax_enabled: bool
    created_at: str


class StoreDetailSchema(StoreListSchema):
    timezone: str
    language: str
    tax_percent: str
    theme_id: int | None = None
    default_theme_id: int | None = None


class StoreCreateSchema(Schema):
    name: str
    slug: str
    store_type: str = "physical"
    theme_id: int | None = None
    default_theme_id: int | None = None
    currency: str = "IRR"
    timezone: str = "Asia/Tehran"
    language: str = "fa"
    status: str = "active"
    tax_enabled: bool = False
    tax_percent: float = 0
    domains: list[str] = []


class StoreUpdateSchema(Schema):
    name: str | None = None
    slug: str | None = None
    store_type: str | None = None
    theme_id: int | None = None
    default_theme_id: int | None = None
    currency: str | None = None
    timezone: str | None = None
    language: str | None = None
    status: str | None = None
    tax_enabled: bool | None = None
    tax_percent: float | None = None


class DomainSchema(Schema):
    id: int
    domain: str
    is_primary: bool
    ssl_enabled: bool
    redirect_to_primary: bool
    is_active: bool


class DomainCreateSchema(Schema):
    domain: str
    is_primary: bool = False
    ssl_enabled: bool = True
    redirect_to_primary: bool = False
    is_active: bool = True


class DomainUpdateSchema(Schema):
    domain: str | None = None
    is_primary: bool | None = None
    ssl_enabled: bool | None = None
    redirect_to_primary: bool | None = None
    is_active: bool | None = None


class StoreAdminSchema(Schema):
    id: int
    phone: str
    full_name: str
    is_primary: bool
    created_at: str


class StoreAdminCreateSchema(Schema):
    phone: str
    first_name: str = ""
    last_name: str = ""
    is_primary: bool = False


class PluginSchema(Schema):
    id: int
    codename: str
    name: str
    description: str
    compatible_store_types: list


class StorePluginSchema(Schema):
    plugin: PluginSchema
    is_enabled: bool
    settings: dict
    store_plugin_id: int | None = None


class StorePluginUpdateSchema(Schema):
    is_enabled: bool
    settings: dict = {}


class TaxSettingsSchema(Schema):
    tax_enabled: bool
    tax_percent: str


class TaxSettingsUpdateSchema(Schema):
    tax_enabled: bool | None = None
    tax_percent: float | None = None


class PaymentSettingsSchema(Schema):
    gateways: list = []
    default_gateway: str = ""
    zarinpal: dict = {}
    idpay: dict = {}
    mellat: dict = {}


class ShippingSettingsSchema(Schema):
    providers: list = []
    default_provider: str = ""
    post: dict = {}
    tipax: dict = {}
    free_shipping_threshold: float = 0
