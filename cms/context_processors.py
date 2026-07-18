"""CMS context processor."""

from tenants.context import get_current_store
from cms.services.cms import CMSService


def cms_context(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        return {}
    cms = CMSService()
    return cms.get_storefront_context(store)
