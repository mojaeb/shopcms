"""Django Ninja rate throttling classes."""

from ninja.throttling import AnonRateThrottle, SimpleRateThrottle


class OTPSendRateThrottle(SimpleRateThrottle):
    scope = "otp_send"

    def get_cache_key(self, request):
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class AuthRefreshRateThrottle(SimpleRateThrottle):
    scope = "auth_refresh"

    def get_cache_key(self, request):
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class APIAnonRateThrottle(AnonRateThrottle):
    scope = "anon"
