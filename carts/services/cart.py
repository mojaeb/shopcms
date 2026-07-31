"""Cart service layer."""

import logging

from django.db import transaction
from carts.models import Cart, CartItem
from carts.services.discount import DiscountError, DiscountService
from products.enums import ProductStatus, ProductType
from products.models import Product, ProductVariant
from products.services.product import ProductService

logger = logging.getLogger(__name__)


class CartError(Exception):
    pass


class CartService:
    """Business logic for shopping carts."""

    def __init__(self):
        self.product_service = ProductService()
        self.discount_service = DiscountService()

    def get_or_create_cart(self, store, request) -> Cart:
        user = self._resolve_user(request)
        session_key = self._ensure_session_key(request)

        if user:
            cart, _ = Cart.objects.get_or_create(store=store, user=user)
            guest_cart = Cart.objects.filter(store=store, session_key=session_key, user__isnull=True).first()
            if guest_cart and guest_cart.pk != cart.pk:
                self.merge_carts(guest_cart, cart)
            return cart

        cart, _ = Cart.objects.get_or_create(store=store, session_key=session_key, user=None)
        return cart

    def merge_on_login(self, store, request, user) -> Cart:
        session_key = self._ensure_session_key(request)
        user_cart, _ = Cart.objects.get_or_create(store=store, user=user)
        guest_cart = Cart.objects.filter(store=store, session_key=session_key, user__isnull=True).first()
        if guest_cart and guest_cart.pk != user_cart.pk:
            self.merge_carts(guest_cart, user_cart)
        return user_cart

    @transaction.atomic
    def merge_carts(self, source: Cart, target: Cart) -> Cart:
        if source.pk == target.pk:
            return target

        for item in source.items.select_related("product", "variant"):
            existing = target.items.filter(product=item.product, variant=item.variant).first()
            if existing:
                existing.quantity += item.quantity
                existing.save(update_fields=["quantity", "updated_at"])
            else:
                item.cart = target
                item.save(update_fields=["cart", "updated_at"])

        if source.coupon_id and not target.coupon_id:
            target.coupon_id = source.coupon_id
        if source.gift_card_id and not target.gift_card_id:
            target.gift_card_id = source.gift_card_id
        if source.coupon_id or source.gift_card_id:
            target.save(update_fields=["coupon", "gift_card", "updated_at"])

        source.delete()
        logger.info("Merged guest cart %s into cart %s", source.pk, target.pk)
        return target

    @transaction.atomic
    def add_item(self, cart: Cart, product_slug: str, variant_id: int | None = None, quantity: int = 1) -> CartItem:
        if quantity < 1:
            raise CartError("تعداد نامعتبر است")

        try:
            product = Product.objects.get(store=cart.store, slug=product_slug, status=ProductStatus.ACTIVE)
        except Product.DoesNotExist:
            raise CartError("محصول یافت نشد")

        variant = None
        if product.product_type == ProductType.VARIABLE:
            if not variant_id:
                raise CartError("لطفاً تنوع محصول را انتخاب کنید")
            try:
                variant = ProductVariant.objects.get(pk=variant_id, product=product, is_active=True)
            except ProductVariant.DoesNotExist:
                raise CartError("تنوع محصول یافت نشد")
            unit_price = variant.price
            self._check_stock(product, variant, quantity)
        else:
            unit_price = product.base_price
            self._check_stock(product, None, quantity)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={"quantity": quantity, "unit_price": unit_price},
        )
        if not created:
            new_qty = item.quantity + quantity
            self._check_stock(product, variant, new_qty)
            item.quantity = new_qty
            item.unit_price = unit_price
            item.save(update_fields=["quantity", "unit_price", "updated_at"])

        cart.save(update_fields=["updated_at"])
        return item

    @transaction.atomic
    def update_item(self, cart: Cart, item_id: int, quantity: int) -> Cart | None:
        try:
            item = cart.items.select_related("product", "variant").get(pk=item_id)
        except CartItem.DoesNotExist:
            raise CartError("آیتم سبد یافت نشد")

        if quantity <= 0:
            item.delete()
            cart.save(update_fields=["updated_at"])
            return cart

        self._check_stock(item.product, item.variant, quantity)
        item.quantity = quantity
        item.save(update_fields=["quantity", "updated_at"])
        cart.save(update_fields=["updated_at"])
        return cart

    @transaction.atomic
    def remove_item(self, cart: Cart, item_id: int) -> Cart:
        deleted, _ = cart.items.filter(pk=item_id).delete()
        if not deleted:
            raise CartError("آیتم سبد یافت نشد")
        cart.save(update_fields=["updated_at"])
        return cart

    @transaction.atomic
    def apply_coupon(self, cart: Cart, code: str) -> Cart:
        try:
            coupon = self.discount_service.validate_coupon(cart, code)
        except DiscountError as e:
            raise CartError(str(e))
        cart.coupon = coupon
        cart.gift_card = None
        cart.save(update_fields=["coupon", "gift_card", "updated_at"])
        return cart

    @transaction.atomic
    def apply_gift_card(self, cart: Cart, code: str) -> Cart:
        try:
            gift = self.discount_service.validate_gift_card(cart, code)
        except DiscountError as e:
            raise CartError(str(e))
        cart.gift_card = gift
        cart.coupon = None
        cart.save(update_fields=["coupon", "gift_card", "updated_at"])
        return cart

    @transaction.atomic
    def remove_coupon(self, cart: Cart) -> Cart:
        cart.coupon = None
        cart.save(update_fields=["coupon", "updated_at"])
        return cart

    @transaction.atomic
    def remove_gift_card(self, cart: Cart) -> Cart:
        cart.gift_card = None
        cart.save(update_fields=["gift_card", "updated_at"])
        return cart

    def clear_cart(self, cart: Cart) -> Cart:
        cart.items.all().delete()
        cart.coupon = None
        cart.gift_card = None
        cart.save(update_fields=["coupon", "gift_card", "updated_at"])
        return cart

    def get_item_count(self, cart: Cart) -> int:
        return sum(item.quantity for item in cart.items.all())

    def calculate_totals(self, cart: Cart) -> dict:
        result = self.discount_service.calculate_discounts(cart)
        return {
            "subtotal": result["subtotal"],
            "discount": result["discount"],
            "coupon_discount": result["coupon_discount"],
            "gift_discount": result["gift_discount"],
            "total": result["total"],
            "item_count": result["item_count"],
        }

    def serialize_cart(self, cart: Cart) -> dict:
        items = cart.items.select_related("product", "variant", "product__brand").prefetch_related(
            "product__images",
            "variant__attributes__attribute",
        )
        totals = self.calculate_totals(cart)
        coupon_data = None
        if cart.coupon_id:
            c = cart.coupon
            coupon_data = {
                "code": c.code,
                "discount_type": c.discount_type,
                "value": str(c.value),
                "scope": c.scope,
            }

        gift_data = None
        if cart.gift_card_id:
            g = cart.gift_card
            gift_data = {
                "code": g.code,
                "balance": str(int(g.balance)),
            }

        from taxes.services.tax import TaxService

        tax_result = TaxService().calculate_for_cart(cart.store, cart)

        return {
            "id": cart.id,
            "items": [self._serialize_item(item) for item in items],
            "coupon": coupon_data,
            "gift_card": gift_data,
            **{k: str(v) for k, v in totals.items() if k != "item_count"},
            "item_count": totals["item_count"],
            "tax": tax_result["tax"],
            "tax_enabled": tax_result["enabled"],
        }

    def _serialize_item(self, item: CartItem) -> dict:
        product = item.product
        inv = self.product_service._get_product_inventory(product)
        if item.variant_id:
            variant_inv = getattr(item.variant, "inventory", None)
            if variant_inv:
                inv = {
                    "available": variant_inv.available,
                    "in_stock": variant_inv.is_in_stock,
                    "track_inventory": variant_inv.track_inventory,
                }

        return {
            "id": item.id,
            "product_id": product.id,
            "product_slug": product.slug,
            "product_name": product.name,
            "variant_id": item.variant_id,
            "variant_label": self._variant_label(item.variant) if item.variant_id else None,
            "quantity": item.quantity,
            "unit_price": str(item.unit_price),
            "line_total": str(item.line_total),
            "image": product.primary_image,
            "in_stock": inv["in_stock"],
            "max_available": inv["available"] if inv["track_inventory"] else None,
        }

    def _check_stock(self, product: Product, variant: ProductVariant | None, required_quantity: int):
        if required_quantity <= 0:
            return

        if variant:
            inv = getattr(variant, "inventory", None)
            if inv and inv.track_inventory and inv.available < required_quantity:
                raise CartError("موجودی کافی نیست")
            return

        inv = product.inventory_items.first()
        if inv and inv.track_inventory and inv.available < required_quantity:
            raise CartError("موجودی کافی نیست")

    def _variant_label(self, variant: ProductVariant) -> str:
        attrs = list(variant.attributes.select_related("attribute").all())
        if attrs:
            return " / ".join(f"{a.attribute.name}: {a.value}" for a in attrs)
        return variant.sku or str(variant.id)

    def _resolve_user(self, request):
        from accounts.models import User
        from accounts.services.jwt import JWTService

        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            payload = JWTService().verify_access_token(auth_header[7:])
            if payload:
                user = User.objects.filter(pk=int(payload["sub"]), is_active=True).first()
                if user:
                    return user

        if getattr(request, "user", None) and request.user.is_authenticated:
            return request.user
        return None

    def _ensure_session_key(self, request) -> str:
        if not request.session.session_key:
            request.session.create()
        return request.session.session_key
