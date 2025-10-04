from uuid import UUID
from datetime import datetime
from typing import List

from exceptions.custom_exceptions import ForbiddenException, RoleGetError, PermissionGetError
from repositories.role_perm_repo import RolePermissionRepository
from entities.entities import RoleEntity, PermissionEntity

class RolePermissionService:
    def __init__(self, repo: RolePermissionRepository):
        self.repo = repo

    @staticmethod
    async def check_permission(user, permission_name: str):

        if user.role is None:
            raise ForbiddenException("No role assigned")

        permissions = [p.name for p in user.roles.permissions]
        if permission_name not in permissions:
            raise ForbiddenException(f"Missing permission: {permission_name}")
        return True

    async def create_role(self, role: RoleEntity):
        role.name = role.name.strip().lower()
        return await self.repo.create_role(role=role)

    async def create_permission(self, entity_name: str, permission_type: str, is_all_attr: bool):
        permission_name = f"{entity_name}:{permission_type}" + ("_all" if is_all_attr else "")

        permission = PermissionEntity(name=permission_name)
        permission.name = permission.name.strip().lower()
        return await self.repo.create_permission(permission=permission)

    async def get_roles(self,
                        ids: list[UUID] | None = None,
                        names: str | None = None,
                        date_from: datetime | None = None,
                        date_to: datetime | None = None):

        names = [name.strip().lower() for name in names] if names else None
        return await self.repo.get_roles(ids=ids, names=names, date_from=date_from, date_to=date_to)

    async def get_permissions(self, ids: List[UUID] | None, names: List[str] | None):
        return await self.repo.get_permissions(ids=ids, names=names)

    async def add_permissions_to_role(self, role_id: UUID, permission_ids: List[UUID]):
        return await self.repo.add_permissions_to_role(role_id=role_id, permission_ids=permission_ids)
