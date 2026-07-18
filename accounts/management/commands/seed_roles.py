"""Seed default roles and permissions."""

from django.core.management.base import BaseCommand

from accounts.enums import RoleScope
from accounts.models import Permission, Role

ROLES = [
    {"codename": "store_admin", "name": "Store Admin", "scope": RoleScope.STORE},
    {"codename": "manager", "name": "Manager", "scope": RoleScope.STORE},
    {"codename": "content", "name": "Content", "scope": RoleScope.STORE},
    {"codename": "products", "name": "Products", "scope": RoleScope.STORE},
    {"codename": "orders", "name": "Orders", "scope": RoleScope.STORE},
    {"codename": "reports", "name": "Reports", "scope": RoleScope.STORE},
    {"codename": "support", "name": "Support", "scope": RoleScope.STORE},
    {"codename": "customer", "name": "Customer", "scope": RoleScope.STORE},
]

PERMISSIONS = [
    {"codename": "products.view", "name": "View Products", "group": "products"},
    {"codename": "products.create", "name": "Create Products", "group": "products"},
    {"codename": "products.edit", "name": "Edit Products", "group": "products"},
    {"codename": "products.delete", "name": "Delete Products", "group": "products"},
    {"codename": "orders.view", "name": "View Orders", "group": "orders"},
    {"codename": "orders.manage", "name": "Manage Orders", "group": "orders"},
    {"codename": "customers.view", "name": "View Customers", "group": "customers"},
    {"codename": "blog.manage", "name": "Manage Blog", "group": "content"},
    {"codename": "comments.moderate", "name": "Moderate Comments", "group": "content"},
    {"codename": "files.manage", "name": "Manage Files", "group": "content"},
    {"codename": "reports.view", "name": "View Reports", "group": "reports"},
    {"codename": "settings.manage", "name": "Manage Settings", "group": "settings"},
    {"codename": "backup.manage", "name": "Manage Backups", "group": "settings"},
    {"codename": "security.view", "name": "View Security Audit", "group": "security"},
]

ROLE_PERMISSIONS = {
    "manager": [
        "products.view", "products.create", "products.edit",
        "orders.view", "orders.manage", "customers.view", "reports.view",
        "settings.manage",
        "backup.manage",
        "security.view",
    ],
    "content": ["blog.manage", "comments.moderate", "files.manage"],
    "products": ["products.view", "products.create", "products.edit", "products.delete", "files.manage"],
    "orders": ["orders.view", "orders.manage", "customers.view"],
    "reports": ["reports.view"],
    "support": ["orders.view", "customers.view"],
    "customer": [],
}


class Command(BaseCommand):
    help = "Seed default roles and permissions"

    def handle(self, *args, **options):
        perm_map = {}
        for perm_data in PERMISSIONS:
            perm, created = Permission.objects.get_or_create(
                codename=perm_data["codename"],
                defaults={
                    "name": perm_data["name"],
                    "group": perm_data["group"],
                },
            )
            perm_map[perm.codename] = perm
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created permission: {perm.codename}"))

        for role_data in ROLES:
            role, created = Role.objects.get_or_create(
                codename=role_data["codename"],
                defaults={
                    "name": role_data["name"],
                    "scope": role_data["scope"],
                    "is_system": True,
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created role: {role.codename}"))

            perm_codenames = ROLE_PERMISSIONS.get(role.codename, [])
            if perm_codenames:
                role.permissions.set([perm_map[c] for c in perm_codenames if c in perm_map])

        self.stdout.write(self.style.SUCCESS("Roles and permissions seeded successfully."))
