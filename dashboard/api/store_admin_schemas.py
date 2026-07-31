"""Store Admin API schemas."""

from ninja import Schema


class DashboardStatsSchema(Schema):
    store_name: str
    store_slug: str
    store_type: str
    status: str
    total_customers: int
    active_customers: int
    total_staff: int
    total_domains: int
    enabled_plugins: int
    tax_enabled: bool
    currency: str
    total_products: int
    total_orders: int
    pending_orders: int
    pending_comments: int = 0
    total_revenue: int
    orders_today: int
    new_customers_today: int


class MemberSchema(Schema):
    id: int
    user_id: int
    phone: str
    full_name: str
    role: str
    status: str
    is_primary: bool
    created_at: str


class GeneralSettingsSchema(Schema):
    name: str
    slug: str
    store_type: str
    currency: str
    timezone: str
    language: str
    theme_slug: str


class GeneralSettingsUpdateSchema(Schema):
    name: str | None = None
    currency: str | None = None
    timezone: str | None = None
    language: str | None = None


class TaxSettingsSchema(Schema):
    tax_enabled: bool
    tax_percent: str
    tax_on_shipping: bool = False
    plugin_active: bool = False


class TaxSettingsUpdateSchema(Schema):
    tax_enabled: bool | None = None
    tax_percent: float | None = None
    tax_on_shipping: bool | None = None


class SettingsOverviewSchema(Schema):
    general: GeneralSettingsSchema
    tax: TaxSettingsSchema
    payment: dict
    shipping: dict
    theme: dict


class UserStatusUpdateSchema(Schema):
    status: str


class UserRoleUpdateSchema(Schema):
    role: str


class TeamMemberCreateSchema(Schema):
    phone: str
    role: str
    first_name: str = ""
    last_name: str = ""


class PluginItemSchema(Schema):
    codename: str
    name: str
    is_enabled: bool


class ReportsSummarySchema(Schema):
    period_days: int
    new_customers: int
    total_customers: int
    total_orders: int
    total_revenue: int
    top_products: list
    orders_by_status: dict
    message: str


class ModuleStubSchema(Schema):
    items: list
    total: int
    message: str = ""
