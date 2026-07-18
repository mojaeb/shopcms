"""User device tracking service."""

import hashlib

from django.utils import timezone

from accounts.models import User, UserDevice
from core.utils.request import get_client_ip, get_user_agent


class DeviceService:
    """Record and manage user login devices."""

    def build_device_key(self, request, user: User | None = None) -> str:
        ip = get_client_ip(request) or ""
        ua = get_user_agent(request)
        raw = f"{user.pk if user else ''}:{ip}:{ua}"
        return hashlib.sha256(raw.encode(), usedforsecurity=False).hexdigest()

    def record_login(self, request, user: User, name: str = "") -> UserDevice:
        device_key = self.build_device_key(request, user)
        ip = get_client_ip(request)
        ua = get_user_agent(request)
        device, _ = UserDevice.objects.update_or_create(
            user=user,
            device_key=device_key,
            defaults={
                "name": name or self._guess_name(ua),
                "ip_address": ip,
                "user_agent": ua,
                "last_seen": timezone.now(),
                "is_revoked": False,
            },
        )
        return device

    def list_devices(self, user: User):
        return UserDevice.objects.filter(user=user, is_revoked=False).order_by("-last_seen")

    def revoke_device(self, user: User, device_id: int) -> bool:
        updated = UserDevice.objects.filter(user=user, id=device_id, is_revoked=False).update(is_revoked=True)
        return updated > 0

    def _guess_name(self, user_agent: str) -> str:
        ua = user_agent.lower()
        if "mobile" in ua or "android" in ua or "iphone" in ua:
            return "موبایل"
        if "windows" in ua:
            return "ویندوز"
        if "mac" in ua:
            return "مک"
        if "linux" in ua:
            return "لینوکس"
        return "مرورگر"
