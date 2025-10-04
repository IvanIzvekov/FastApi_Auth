from datetime import datetime
from uuid import UUID

class SessionEntity:
    def __init__(self, id: UUID=None,
                 user_id: UUID=None,
                 is_active: bool=None,
                 created_at: datetime=None,
                 expire_at: datetime=None,
                 device: str=None
                 ):
        self.id = id
        self.user_id = user_id
        self.is_active = is_active
        self.created_at = created_at
        self.expire_at = expire_at
        self.device = device


class UserEntity:
    def __init__(self, id: UUID=None,
                 email: str=None,
                 first_name: str=None,
                 last_name: str=None,
                 patronymic: str | None=None,
                 is_active: bool=None,
                 created_at: datetime=None,
                 updated_at: datetime=None,
                 hash_password: str=None,
                 deleted_at: datetime=None
                 ):
        self.id = id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.patronymic = patronymic
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at
        self.hash_password = hash_password
        self.deleted_at = deleted_at

class RoleEntity:
    def __init__(self, id: UUID=None,
                 name: str=None,
                 created_at: datetime=None,
                 updated_at: datetime=None
                 ):
        self.id = id
        self.name = name
        self.created_at = created_at
        self.updated_at = updated_at

class PermissionEntity:
    def __init__(self, id: UUID=None, name: str=None):
        self.id = id
        self.name = name