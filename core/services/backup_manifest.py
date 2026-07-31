"""Backup export/import model specifications."""

from collections.abc import Callable

from django.apps import apps
from django.db.models import Q

MANIFEST_VERSION = 1


def _model(label: str):
    app_label, model_name = label.split(".")
    return apps.get_model(app_label, model_name)


def store_export_specs() -> list[tuple[str, Callable]]:
    """Ordered model exporters for per-store backup (parents before children)."""
    Tag = _model("products.Tag")
    Category = _model("products.Category")
    Brand = _model("products.Brand")
    ProductAttribute = _model("products.ProductAttribute")
    ProductAttributeValue = _model("products.ProductAttributeValue")
    Product = _model("products.Product")
    ProductVariant = _model("products.ProductVariant")
    ProductImage = _model("products.ProductImage")
    ProductVideo = _model("products.ProductVideo")
    Inventory = _model("products.Inventory")
    MediaFile = _model("files.MediaFile")
    FileThumbnail = _model("files.FileThumbnail")
    Page = _model("cms.Page")
    Menu = _model("cms.Menu")
    Banner = _model("cms.Banner")
    Slider = _model("cms.Slider")
    Widget = _model("cms.Widget")
    MenuItem = _model("cms.MenuItem")
    ContentBlock = _model("cms.ContentBlock")
    Slide = _model("cms.Slide")
    Shortcode = _model("cms.Shortcode")
    Coupon = _model("carts.Coupon")
    GiftCard = _model("carts.GiftCard")
    Cart = _model("carts.Cart")
    CartItem = _model("carts.CartItem")
    CouponUsage = _model("carts.CouponUsage")
    GiftCardUsage = _model("carts.GiftCardUsage")
    ShippingZone = _model("shipping.ShippingZone")
    ShippingMethod = _model("shipping.ShippingMethod")
    ShippingPrice = _model("shipping.ShippingPrice")
    ShippingRule = _model("shipping.ShippingRule")
    TaxRule = _model("taxes.TaxRule")
    CustomerAddress = _model("addresses.CustomerAddress")
    PaymentTransaction = _model("payments.PaymentTransaction")
    Order = _model("orders.Order")
    OrderItem = _model("orders.OrderItem")
    Shipment = _model("orders.Shipment")
    OrderHistory = _model("orders.OrderHistory")
    Invoice = _model("orders.Invoice")
    WishlistItem = _model("wishlists.WishlistItem")
    Comment = _model("comments.Comment")
    CommentLike = _model("comments.CommentLike")
    BlogCategory = _model("blog.BlogCategory")
    BlogTag = _model("blog.BlogTag")
    BlogPost = _model("blog.BlogPost")
    BlogComment = _model("blog.BlogComment")
    ProductDigitalAsset = _model("digital.ProductDigitalAsset")
    DownloadLicense = _model("digital.DownloadLicense")
    SubscriptionPlan = _model("subscriptions.SubscriptionPlan")
    CustomerSubscription = _model("subscriptions.CustomerSubscription")
    SubscriptionRenewal = _model("subscriptions.SubscriptionRenewal")
    NotificationChannel = _model("notifications.NotificationChannel")
    NotificationLog = _model("notifications.NotificationLog")
    Domain = _model("tenants.Domain")
    StoreSetting = _model("tenants.StoreSetting")
    StorePlugin = _model("tenants.StorePlugin")
    LayoutSettings = _model("cms.LayoutSettings")
    StoreMembership = _model("accounts.StoreMembership")

    return [
        ("tenants.Domain", lambda s: Domain.objects.filter(store=s)),
        ("tenants.StoreSetting", lambda s: StoreSetting.objects.filter(store=s)),
        ("tenants.StorePlugin", lambda s: StorePlugin.objects.filter(store=s)),
        ("cms.LayoutSettings", lambda s: LayoutSettings.objects.filter(store=s)),
        ("accounts.StoreMembership", lambda s: StoreMembership.objects.filter(store=s)),
        ("products.Tag", lambda s: Tag.objects.filter(store=s)),
        ("products.Category", lambda s: Category.objects.filter(store=s)),
        ("products.Brand", lambda s: Brand.objects.filter(store=s)),
        ("products.ProductAttribute", lambda s: ProductAttribute.objects.filter(store=s)),
        ("products.ProductAttributeValue", lambda s: ProductAttributeValue.objects.filter(attribute__store=s)),
        ("products.Product", lambda s: Product.objects.filter(store=s)),
        ("products.ProductVariant", lambda s: ProductVariant.objects.filter(product__store=s)),
        ("products.ProductImage", lambda s: ProductImage.objects.filter(product__store=s)),
        ("products.ProductVideo", lambda s: ProductVideo.objects.filter(product__store=s)),
        (
            "products.Inventory",
            lambda s: Inventory.objects.filter(Q(product__store=s) | Q(variant__product__store=s)),
        ),
        ("files.MediaFile", lambda s: MediaFile.objects.filter(store=s)),
        ("files.FileThumbnail", lambda s: FileThumbnail.objects.filter(media_file__store=s)),
        ("cms.Page", lambda s: Page.objects.filter(store=s)),
        ("cms.Menu", lambda s: Menu.objects.filter(store=s)),
        ("cms.Banner", lambda s: Banner.objects.filter(store=s)),
        ("cms.Slider", lambda s: Slider.objects.filter(store=s)),
        ("cms.Widget", lambda s: Widget.objects.filter(store=s)),
        ("cms.MenuItem", lambda s: MenuItem.objects.filter(menu__store=s)),
        ("cms.ContentBlock", lambda s: ContentBlock.objects.filter(page__store=s)),
        ("cms.Slide", lambda s: Slide.objects.filter(slider__store=s)),
        ("cms.Shortcode", lambda s: Shortcode.objects.filter(store=s)),
        ("carts.Coupon", lambda s: Coupon.objects.filter(store=s)),
        ("carts.GiftCard", lambda s: GiftCard.objects.filter(store=s)),
        ("carts.Cart", lambda s: Cart.objects.filter(store=s)),
        ("carts.CartItem", lambda s: CartItem.objects.filter(cart__store=s)),
        ("carts.CouponUsage", lambda s: CouponUsage.objects.filter(coupon__store=s)),
        ("carts.GiftCardUsage", lambda s: GiftCardUsage.objects.filter(gift_card__store=s)),
        ("shipping.ShippingZone", lambda s: ShippingZone.objects.filter(store=s)),
        ("shipping.ShippingMethod", lambda s: ShippingMethod.objects.filter(store=s)),
        ("shipping.ShippingPrice", lambda s: ShippingPrice.objects.filter(method__store=s)),
        ("shipping.ShippingRule", lambda s: ShippingRule.objects.filter(method__store=s)),
        ("taxes.TaxRule", lambda s: TaxRule.objects.filter(store=s)),
        ("addresses.CustomerAddress", lambda s: CustomerAddress.objects.filter(store=s)),
        ("payments.PaymentTransaction", lambda s: PaymentTransaction.objects.filter(store=s)),
        ("orders.Order", lambda s: Order.objects.filter(store=s)),
        ("orders.OrderItem", lambda s: OrderItem.objects.filter(order__store=s)),
        ("orders.Shipment", lambda s: Shipment.objects.filter(order__store=s)),
        ("orders.OrderHistory", lambda s: OrderHistory.objects.filter(order__store=s)),
        ("orders.Invoice", lambda s: Invoice.objects.filter(order__store=s)),
        ("wishlists.WishlistItem", lambda s: WishlistItem.objects.filter(store=s)),
        ("comments.Comment", lambda s: Comment.objects.filter(store=s)),
        ("comments.CommentLike", lambda s: CommentLike.objects.filter(comment__store=s)),
        ("blog.BlogCategory", lambda s: BlogCategory.objects.filter(store=s)),
        ("blog.BlogTag", lambda s: BlogTag.objects.filter(store=s)),
        ("blog.BlogPost", lambda s: BlogPost.objects.filter(store=s)),
        ("blog.BlogComment", lambda s: BlogComment.objects.filter(store=s)),
        ("digital.ProductDigitalAsset", lambda s: ProductDigitalAsset.objects.filter(store=s)),
        ("digital.DownloadLicense", lambda s: DownloadLicense.objects.filter(store=s)),
        ("subscriptions.SubscriptionPlan", lambda s: SubscriptionPlan.objects.filter(store=s)),
        ("subscriptions.CustomerSubscription", lambda s: CustomerSubscription.objects.filter(store=s)),
        ("subscriptions.SubscriptionRenewal", lambda s: SubscriptionRenewal.objects.filter(subscription__store=s)),
        ("notifications.NotificationChannel", lambda s: NotificationChannel.objects.filter(store=s)),
        ("notifications.NotificationLog", lambda s: NotificationLog.objects.filter(store=s)),
    ]
