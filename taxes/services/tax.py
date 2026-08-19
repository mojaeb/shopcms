"""Tax calculation service."""

import logging
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from carts.models import Cart
from taxes.enums import TaxRuleScope
from taxes.models import TaxRule
from tenants.models import Store, StoreSetting

logger = logging.getLogger(__name__)


class TaxError(Exception):
    pass


class TaxService:
    """Calculate tax for carts and checkout."""

    def is_tax_active(self, store: Store) -> bool:
        """Store.tax_enabled is the checkout switch; plugin is kept in sync on save."""
        return bool(store.tax_enabled)

    def sync_plugin(self, store: Store) -> None:
        """Keep the tax plugin aligned with the store flag so the plugins tab matches."""
        from plugins.services.plugin import PluginError, PluginService
        from tenants.models import Plugin

        plugin, _ = Plugin.objects.get_or_create(
            codename="tax",
            defaults={
                "name": "مالیات",
                "description": "محاسبه مالیات در سبد و تسویه",
                "is_active": True,
            },
        )
        if not plugin.is_active:
            plugin.is_active = True
            plugin.save(update_fields=["is_active"])
        try:
            PluginService().set_enabled(store, "tax", bool(store.tax_enabled))
        except (Plugin.DoesNotExist, PluginError):
            logger.warning("Could not sync tax plugin for store %s", store.slug)

    def get_tax_settings(self, store: Store) -> dict:
        return {
            "tax_enabled": store.tax_enabled,
            "tax_percent": str(store.tax_percent),
            "tax_on_shipping": self._get_tax_on_shipping(store),
            "plugin_active": self.is_tax_active(store),
        }

    @transaction.atomic
    def update_tax_settings(self, store: Store, data: dict) -> dict:
        fields = []
        if "tax_enabled" in data:
            store.tax_enabled = data["tax_enabled"]
            fields.append("tax_enabled")
        if "tax_percent" in data:
            store.tax_percent = data["tax_percent"]
            fields.append("tax_percent")
        if fields:
            store.save(update_fields=[*fields, "updated_at"])

        if "tax_on_shipping" in data:
            self._set_tax_on_shipping(store, bool(data["tax_on_shipping"]))

        self.sync_plugin(store)
        return self.get_tax_settings(store)

    def calculate_for_cart(self, store: Store, cart: Cart, shipping_cost: Decimal = Decimal("0")) -> dict:
        totals = self._cart_subtotals(cart)
        return self._calculate(
            store,
            items=totals["items"],
            subtotal=totals["subtotal"],
            discount=totals["discount"],
            shipping_cost=shipping_cost,
        )

    def calculate_preview(
        self,
        store: Store,
        subtotal: Decimal,
        discount: Decimal,
        shipping_cost: Decimal = Decimal("0"),
        items: list | None = None,
    ) -> dict:
        return self._calculate(store, items=items or [], subtotal=subtotal, discount=discount, shipping_cost=shipping_cost)

    def list_rules(self, store: Store):
        return TaxRule.objects.filter(store=store).select_related("category", "product")

    @transaction.atomic
    def create_rule(self, store: Store, data: dict) -> TaxRule:
        self._validate_rule_data(store, data)
        return TaxRule.objects.create(store=store, **data)

    @transaction.atomic
    def update_rule(self, store: Store, rule_id: int, data: dict) -> TaxRule:
        try:
            rule = TaxRule.objects.get(pk=rule_id, store=store)
        except TaxRule.DoesNotExist:
            raise TaxError("قانون مالیات یافت نشد")

        self._validate_rule_data(store, data, rule=rule)
        for field, value in data.items():
            setattr(rule, field, value)
        rule.save()
        return rule

    @transaction.atomic
    def delete_rule(self, store: Store, rule_id: int) -> None:
        deleted, _ = TaxRule.objects.filter(pk=rule_id, store=store).delete()
        if not deleted:
            raise TaxError("قانون مالیات یافت نشد")

    def serialize_rule(self, rule: TaxRule) -> dict:
        return {
            "id": rule.id,
            "name": rule.name,
            "rate_percent": str(rule.rate_percent),
            "scope": rule.scope,
            "category_id": rule.category_id,
            "category_name": rule.category.name if rule.category_id else None,
            "product_id": rule.product_id,
            "product_name": rule.product.name if rule.product_id else None,
            "is_active": rule.is_active,
            "priority": rule.priority,
        }

    def _calculate(
        self,
        store: Store,
        items: list,
        subtotal: Decimal,
        discount: Decimal,
        shipping_cost: Decimal,
    ) -> dict:
        if not self.is_tax_active(store) or subtotal <= 0:
            return self._empty_result(store)

        taxable_items = max(Decimal("0"), subtotal - discount)
        if taxable_items <= 0 and shipping_cost <= 0:
            return self._empty_result(store)

        rules = list(
            TaxRule.objects.filter(store=store, is_active=True)
            .select_related("category", "product")
            .order_by("-priority")
        )
        has_specific_rules = any(r.scope != TaxRuleScope.ALL for r in rules)

        if has_specific_rules and items:
            tax_amount = self._calculate_itemized(store, items, subtotal, discount, rules)
        else:
            rate = store.tax_percent
            tax_amount = self._apply_rate(taxable_items, rate)

        if self._get_tax_on_shipping(store) and shipping_cost > 0:
            tax_amount += self._apply_rate(shipping_cost, store.tax_percent)

        tax_amount = tax_amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        return {
            "enabled": True,
            "tax": str(int(tax_amount)),
            "taxable_amount": str(int(taxable_items)),
            "default_rate": str(store.tax_percent),
            "tax_on_shipping": self._get_tax_on_shipping(store),
            "grand_total": str(int(taxable_items + shipping_cost + tax_amount)),
        }

    def _calculate_itemized(self, store, items, subtotal, discount, rules) -> Decimal:
        discount_ratio = (discount / subtotal) if subtotal > 0 else Decimal("0")
        total_tax = Decimal("0")

        for item in items:
            line_total = item["line_total"]
            taxable_line = line_total * (Decimal("1") - discount_ratio)
            rate = self._resolve_rate(item["product_id"], item.get("category_id"), rules, store.tax_percent)
            total_tax += self._apply_rate(taxable_line, rate)

        return total_tax

    def _resolve_rate(self, product_id: int, category_id: int | None, rules: list, default_rate: Decimal) -> Decimal:
        for rule in rules:
            if rule.scope == TaxRuleScope.PRODUCT and rule.product_id == product_id:
                return rule.rate_percent
        for rule in rules:
            if rule.scope == TaxRuleScope.CATEGORY and rule.category_id and rule.category_id == category_id:
                return rule.rate_percent
        for rule in rules:
            if rule.scope == TaxRuleScope.ALL:
                return rule.rate_percent
        return default_rate

    def _apply_rate(self, amount: Decimal, rate: Decimal) -> Decimal:
        if amount <= 0 or rate <= 0:
            return Decimal("0")
        return (amount * rate) / Decimal("100")

    def _cart_subtotals(self, cart: Cart) -> dict:
        from carts.services.cart import CartService

        totals = CartService().calculate_totals(cart)
        cart_items = cart.items.select_related("product", "product__category").all()
        items = [
            {
                "product_id": item.product_id,
                "category_id": item.product.category_id,
                "line_total": item.line_total,
            }
            for item in cart_items
        ]
        return {
            "subtotal": totals["subtotal"],
            "discount": totals["discount"],
            "items": items,
        }

    def _empty_result(self, store: Store) -> dict:
        return {
            "enabled": False,
            "tax": "0",
            "taxable_amount": "0",
            "default_rate": str(store.tax_percent),
            "tax_on_shipping": self._get_tax_on_shipping(store),
            "grand_total": "0",
        }

    def _get_tax_on_shipping(self, store: Store) -> bool:
        setting = StoreSetting.objects.filter(store=store, group="tax", key="on_shipping").first()
        return bool(setting.value) if setting else False

    def _set_tax_on_shipping(self, store: Store, enabled: bool) -> None:
        StoreSetting.objects.update_or_create(
            store=store,
            group="tax",
            key="on_shipping",
            defaults={"value": enabled},
        )

    def _validate_rule_data(self, store: Store, data: dict, rule: TaxRule | None = None) -> None:
        scope = data.get("scope", rule.scope if rule else TaxRuleScope.ALL)
        if scope == TaxRuleScope.CATEGORY and not data.get("category_id") and not (rule and rule.category_id):
            raise TaxError("دسته‌بندی برای قانون مالیات الزامی است")
        if scope == TaxRuleScope.PRODUCT and not data.get("product_id") and not (rule and rule.product_id):
            raise TaxError("محصول برای قانون مالیات الزامی است")

        if data.get("category_id"):
            from products.models import Category

            if not Category.objects.filter(pk=data["category_id"], store=store).exists():
                raise TaxError("دسته‌بندی نامعتبر است")
        if data.get("product_id"):
            from products.models import Product

            if not Product.objects.filter(pk=data["product_id"], store=store).exists():
                raise TaxError("محصول نامعتبر است")
