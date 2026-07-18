"""Payment gateway registry."""

from payments.providers.base import PaymentGateway

_registry: dict[str, PaymentGateway] = {}


def register(gateway_cls):
    instance = gateway_cls()
    _registry[gateway_cls.codename] = instance
    return gateway_cls


def get_gateway(codename: str) -> PaymentGateway | None:
    return _registry.get(codename)


def list_gateways() -> list[PaymentGateway]:
    return list(_registry.values())
