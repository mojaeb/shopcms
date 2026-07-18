"""
URL configuration for ShopCMS platform.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.api import api
from digital.views import download_file
from plugins.loader import get_plugin_urlpatterns, register_api_routers
from tenants.views.storefront import storefront_404

register_api_routers(api)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),
    path("download/<str:token>/", download_file, name="digital_download"),
    path("", include("tenants.urls")),
] + get_plugin_urlpatterns()

handler404 = storefront_404

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    try:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),  # noqa: F821
        ] + urlpatterns
    except ImportError:
        pass
