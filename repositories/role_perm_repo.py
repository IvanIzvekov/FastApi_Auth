from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from datetime import datetime
from uuid import UUID

from entities.entities import UserEntity, RoleEntity, PermissionEntity, UserWithRolesEntity, RolesWithPermissionsEntity
from models import Role, User, Permission
from exceptions.custom_exceptions import UserGetError, RoleGetError, RoleAlreadyExistsError, \
    PermissionAlreadyExistsError, PermissionGetError


class RolePermissionRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create_permission(self, permission: PermissionEntity):
        try:
            permission_orm = Permission(
                name=permission.name
            )

            self._db.add(permission_orm)
            await self._db.flush()

            permission.id = permission_orm.id

            return permission
        except IntegrityError:
            raise PermissionAlreadyExistsError(f"Права на сущность с именем {permission.name} уже существует")

    async def create_role(self, role: RoleEntity) -> RoleEntity:
        try:
            role_orm = Role(
                name=role.name
            )

            self._db.add(role_orm)
            await self._db.flush()

            role.id = role_orm.id
            role.created_at = role_orm.created_at
            role.updated_at = role_orm.updated_at

            return role
        except IntegrityError:
            raise RoleAlreadyExistsError(f"Роль с именем {role.name} уже существует")

    async def add_permissions_to_role(self, role_id: UUID, permission_ids: List[UUID]) -> RolesWithPermissionsEntity:
        stmt = select(Role).where(Role.id == role_id).options(selectinload(Role.permissions))
        result = await self._db.execute(stmt)
        role_orm = result.scalar_one_or_none()
        if not role_orm:
            raise RoleGetError(f"Роль с id {role_id} не найдена")

        stmt = select(Permission).where(Permission.id.in_(permission_ids))
        result = await self._db.execute(stmt)
        permissions_orm = result.scalars().all()
        if not permissions_orm:
            raise PermissionGetError(f"Указанные права не найдены")

        for permission_orm in permissions_orm:
            if permission_orm not in role_orm.permissions:
                role_orm.permissions.append(permission_orm)

        await self._db.flush()
        await self._db.refresh(role_orm)

        return RolesWithPermissionsEntity(
            role=RoleEntity(
                id=role_orm.id,
                name=role_orm.name,
                created_at=role_orm.created_at,
                updated_at=role_orm.updated_at
            ),
            permissions=[PermissionEntity(
                id=perm.id,
                name=perm.name
            ) for perm in role_orm.permissions]
        )

    async def delete_permissions_from_role(self, role_id: UUID, permission_ids: List[UUID]) -> RolesWithPermissionsEntity:
        stmt = select(Role).where(Role.id == role_id).options(selectinload(Role.permissions))
        result = await self._db.execute(stmt)
        role_orm = result.scalar_one_or_none()
        if not role_orm:
            raise RoleGetError(f"Роль с id {role_id} не найдена")

        stmt = select(Permission).where(Permission.id.in_(permission_ids))
        result = await self._db.execute(stmt)
        permissions_orm = result.scalars().all()
        if not permissions_orm:
            raise PermissionGetError(f"Указанные права не найдены")

        for permission_orm in permissions_orm:
            if permission_orm not in role_orm.permissions:
                role_orm.permissions.remove(permission_orm)

        await self._db.flush()
        await self._db.refresh(role_orm)

        return RolesWithPermissionsEntity(
            role=RoleEntity(
                id=role_orm.id,
                name=role_orm.name,
                created_at=role_orm.created_at,
                updated_at=role_orm.updated_at
            ),
            permissions=[PermissionEntity(
                id=perm.id,
                name=perm.name
            ) for perm in role_orm.permissions]
        )

    async def set_user_roles(self, user: UserEntity, roles: List[RoleEntity]) -> UserWithRolesEntity:
        result = await self._db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user.id)
        )

        user_orm = result.scalar_one_or_none()
        if not user_orm:
            raise UserGetError(f"Пользователь {user.email} не найден")

        stmt = select(Role).where(Role.id.in_([role.id for role in roles]))
        result = await self._db.execute(stmt)
        roles_orm = result.scalars().all()
        if not roles_orm:
            raise RoleGetError(f"Не удалось найти указанные роли в базе данных")

        existing_role_ids = {r.id for r in user_orm.roles}
        for role_orm in roles_orm:
            if role_orm.id not in existing_role_ids:
                user_orm.roles.append(role_orm)

        await self._db.flush()
        await self._db.refresh(user_orm)

        return UserWithRolesEntity(
            user=UserEntity(
                id=user_orm.id,
                first_name=user_orm,
                last_name=user_orm.last_name,
                patronymic=user_orm.patronymic,
                email=user_orm.email,
                created_at=user_orm.created_at,
                updated_at=user_orm.updated_at,
                is_active=user_orm.is_active,
                deleted_at=user_orm.deleted_at
            ),
            roles=[RoleEntity(
                id=role.id,
                name=role.name,
                created_at=role.created_at,
                updated_at=role.updated_at
            ) for role in user_orm.roles]
        )

    async def delete_user_roles(self, user: UserEntity, roles: List[RoleEntity]):
        result = await self._db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user.id)
        )

        user_orm = result.scalar_one_or_none()
        if not user_orm:
            raise UserGetError(f"Пользователь {user.email} не найден")

        stmt = select(Role).where(Role.id.in_([role.id for role in roles]))
        result = await self._db.execute(stmt)
        roles_orm = result.scalars().all()
        if not roles_orm:
            raise RoleGetError(f"Не удалось найти указанные роли в базе данных")

        existing_role_ids = {r.id for r in user_orm.roles}
        for role_orm in roles_orm:
            if role_orm.id not in existing_role_ids:
                user_orm.roles.remove(role_orm)

        await self._db.flush()
        await self._db.refresh(user_orm)

        return UserWithRolesEntity(
            user=UserEntity(
                id=user_orm.id,
                first_name=user_orm,
                last_name=user_orm.last_name,
                patronymic=user_orm.patronymic,
                email=user_orm.email,
                created_at=user_orm.created_at,
                updated_at=user_orm.updated_at,
                is_active=user_orm.is_active,
                deleted_at=user_orm.deleted_at
            ),
            roles=[RoleEntity(
                id=role.id,
                name=role.name,
                created_at=role.created_at,
                updated_at=role.updated_at
            ) for role in user_orm.roles]
        )

    async def get_roles(self,
                        ids: list[UUID] | None = None,
                        names: list[str] | None = None,
                        date_from: datetime | None = None,
                        date_to: datetime | None = None) -> List[RolesWithPermissionsEntity]:
        stmt = select(Role)

        if date_from:
            stmt = stmt.where(
                Role.created_at >= date_from
            )

        if date_to:
            stmt = stmt.where(
                Role.created_at <= date_to
            )

        if ids and names:
            stmt = stmt.where(
                or_(
                    Role.id.in_(ids),
                    Role.name.in_(names)
                )
            )
        elif ids:
            stmt = stmt.where(
                Role.id.in_(ids)
            )
        elif names:
            stmt = stmt.where(
                Role.name.in_(names)
            )

        stmt = stmt.options(selectinload(Role.permissions))

        result = await self._db.execute(stmt)
        roles = result.scalars().all()

        return [RolesWithPermissionsEntity(
            role=RoleEntity(
                    id=role.id,
                    name=role.name,
                    created_at=role.created_at,
                    updated_at=role.updated_at
            ),
            permissions=[PermissionEntity(
                id=permission.id,
                name=permission.name
            ) for permission in role.permissions]
        ) for role in roles]

    async def get_permissions(self, ids: list[UUID] | None = None, names: list[str] | None = None) -> List[PermissionEntity]:
        stmt = select(Permission)

        if ids and names:
            stmt = stmt.where(
                or_(Permission.id.in_(ids), Permission.name.in_(names))
            )
        elif ids:
            stmt = stmt.where(
                Permission.id.in_(ids)
            )
        elif names:
            stmt = stmt.where(
                Permission.name.in_(names)
            )

        result = await self._db.execute(stmt)
        permissions = result.scalars().all()
        return [PermissionEntity(
            id=permission.id,
            name=permission.name
        ) for permission in permissions]

    async def get_users_roles(self, users: list[UserEntity]) -> list[UserWithRolesEntity]:
        user_ids = [user.id for user in users]

        if not user_ids:
            return []

        stmt = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.id.in_(user_ids))
        )

        result = await self._db.execute(stmt)
        users_with_roles = result.scalars().unique().all()

        return [
            UserWithRolesEntity(
                user=UserEntity(
                    id=user.id,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    email=user.email,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                    patronymic=user.patronymic
                ),
                roles=[RoleEntity(
                    id=role.id,
                    name=role.name,
                    created_at=role.created_at,
                    updated_at=role.updated_at
                ) for role in user.roles]
            )
         for user in users_with_roles]


