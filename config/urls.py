"""
URL configuration for ShopCMS platform.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from core.api import api
from core.views import serve_media
from digital.views import download_file
from plugins.loader import get_plugin_urlpatterns, register_api_routers
from tenants.views.storefront import storefront_404

register_api_routers(api)

urlpatterns = [
    # Local disk media must be routable in production when Nginx is not in front
    # (e.g. Nginx Proxy Manager → Gunicorn). Nginx still serves /media/ when used.
    re_path(r"^media/(?P<path>.*)$", serve_media),
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),
    path("download/<str:token>/", download_file, name="digital_download"),
    path("", include("tenants.urls")),
] + get_plugin_urlpatterns()

handler404 = storefront_404

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    try:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),  # noqa: F821
        ] + urlpatterns
    except ImportError:
        pass
