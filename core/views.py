"""Serve locally stored media files."""

from django.conf import settings
from django.views.static import serve


def serve_media(request, path):
    """Serve a file from MEDIA_ROOT.

    Wired explicitly so uploads work when Gunicorn is the public backend
    (Nginx Proxy Manager → shopcms-web). Prefer Nginx /media/ in production.
    """
    return serve(request, path, document_root=str(settings.MEDIA_ROOT))
