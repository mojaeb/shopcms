"""Store repository."""

from core.repositories import BaseRepository
from tenants.models import Domain, Store


class StoreRepository(BaseRepository[Store]):
    model = Store

    def get_by_slug(self, slug: str) -> Store | None:
        try:
            return self.model.objects.select_related("theme", "default_theme").get(slug=slug)
        except self.model.DoesNotExist:
            return None

    def get_active_by_id(self, store_id: int) -> Store | None:
        try:
            return (
                self.model.objects.select_related("theme", "default_theme")
                .filter(status="active")
                .get(pk=store_id)
            )
        except self.model.DoesNotExist:
            return None


class DomainRepository(BaseRepository[Domain]):
    model = Domain

    def get_by_host(self, host: str) -> Domain | None:
        try:
            return (
                self.model.objects.select_related(
                    "store",
                    "store__theme",
                    "store__default_theme",
                )
                .filter(domain=host.lower(), is_active=True, store__status="active")
                .first()
            )
        except self.model.DoesNotExist:
            return None

    def get_primary_for_store(self, store: Store) -> Domain | None:
        return self.model.objects.filter(store=store, is_primary=True, is_active=True).first()
