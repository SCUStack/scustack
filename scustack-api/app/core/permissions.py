import enum


class Permission(enum.StrEnum):
    MATERIALS_READ = 'materials:read'
    MATERIALS_CREATE = 'materials:create'
    MATERIALS_DELETE_OWN = 'materials:delete:own'
    MATERIALS_DELETE_ANY = 'materials:delete:any'
    MATERIALS_MODERATE = 'materials:moderate'
    MATERIALS_PIN = 'materials:pin'
    USERS_MANAGE = 'users:manage'
    AUDIT_READ = 'audit:read'


ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    'visitor': {Permission.MATERIALS_READ},
    'student': {
        Permission.MATERIALS_READ,
        Permission.MATERIALS_CREATE,
        Permission.MATERIALS_DELETE_OWN,
    },
    'contributor': {
        Permission.MATERIALS_READ,
        Permission.MATERIALS_CREATE,
        Permission.MATERIALS_DELETE_OWN,
    },
    'maintainer': {
        Permission.MATERIALS_READ,
        Permission.MATERIALS_CREATE,
        Permission.MATERIALS_DELETE_ANY,
        Permission.MATERIALS_MODERATE,
        Permission.MATERIALS_PIN,
        Permission.USERS_MANAGE,
        Permission.AUDIT_READ,
    },
    'admin': set(Permission),
}
