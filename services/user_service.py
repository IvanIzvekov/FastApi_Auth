from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy.util import await_only

from entities.entities import UserEntity, RoleEntity, UserWithRolesEntity
from services.auth_service import AuthService
from repositories.role_perm_repo import RolePermissionRepository
from repositories.user_repo import UserRepository
from exceptions.custom_exceptions import (
    UserEmailExistsError,
    UserCreateError,
    UserGetError,
    UserDeleteError,
    UserUpdateError, NotFoundError,
    RoleGetError, UserNotHaveRoles
)


class UserService:
    def __init__(self, repo: UserRepository, role_perm_repo: RolePermissionRepository):
        self.repo = repo
        self.role_perm_repo = role_perm_repo

    async def update_user(
        self,
        user: UserEntity,
    ) -> UserWithRolesEntity:
        """Обновить данные пользователя"""
        try:
            hash_password = await AuthService.hash_password(user.hash_password) if user.hash_password else None

            user.email = user.email.lower().strip() if user.email else None
            exist_user = await self.get_user_by_email(user.email) if user.email else None
            if exist_user and exist_user.id != user.id:
                raise UserEmailExistsError("Пользователь с таким email уже существует")

            user = await self.repo.update(user=user)
            return user
        except UserEmailExistsError as e:
            raise ValueError(str(e))
        except UserUpdateError as e:
            raise ValueError(f"Невозможно обновить пользователя: {e}") from e
        except Exception as e:
            raise Exception(f"Неизвестная ошибка при обновлении пользователя: {e}") from e

    async def create_user(self, user: UserEntity) -> UserWithRolesEntity:
        """
        Создать нового пользователя
        """
        try:
            user.email = user.email.lower().strip()

            exist_user = await self.get_user_by_email(user.email)
            if exist_user:
                raise UserEmailExistsError(f"Пользователь с email={user.email} уже существует")

            old_exist_user = await self.repo.check_re_registration(user.email)
            if old_exist_user:
                return old_exist_user


            new_user = await self.repo.create(user=user)

            user_role = await self.role_perm_repo.get_roles(names=["user"])
            if not user_role:
                raise RoleGetError("Роль user не найдена")

            user_role = user_role[0].role
            usr = await self.role_perm_repo.set_user_roles(user, [user_role])

            return usr

        except RoleGetError as e:
            raise e
        except UserGetError as e:
            raise e
        except UserEmailExistsError as e:
            raise e
        except UserCreateError as e:
            raise ValueError(f"Невозможно создать пользователя: {e}")
        except Exception as e:
            raise Exception(f"Неизвестная ошибка при создании пользователя: {e}")

    async def get_user_by_email(self, email: str):
        """Получить активного пользователя по email"""
        try:
            normalized_email = email.lower().strip()
            user = await self.repo.get_by_email(normalized_email)
            return user
        except UserGetError as e:
            raise e

    async def get_user_by_id(self, user_id: UUID):
        """Получить активного пользователя по ID"""
        try:
            user = await self.repo.get_by_id(user_id)
            return user
        except UserGetError as e:
            raise e

    async def delete_user(self, user: UserEntity):
        """Мягкое удаление пользователя"""
        try:
            await self.repo.soft_delete(user)
        except NotFoundError:
            raise Exception(f"User {user.id} not found")
        except UserDeleteError as e:
            raise Exception(f"Ошибка при удалении пользователя id={user.id}: {e}") from e

    async def add_roles_to_user(self, user_id: UUID, role_ids: List[UUID]) -> UserWithRolesEntity:
        usr = await self.repo.get_by_id(user_id)
        if usr is None:
            raise UserGetError(f"Пользователь с id = {str(user_id)} не найден")

        roles = await self.role_perm_repo.get_roles(ids=role_ids)

        return await self.role_perm_repo.set_user_roles(user=usr, roles=[r.role for r in roles])

    async def get_user_roles(self, user: UserEntity) -> UserWithRolesEntity:
        user_roles = await self.role_perm_repo.get_users_roles(users=[user])
        if not user_roles:
            raise UserNotHaveRoles

        user_roles = user_roles[0]

        return user_roles

    async def remove_roles_from_user(self, user_id: UUID, role_ids: List[UUID]) -> UserWithRolesEntity:
        usr = await self.repo.get_by_id(user_id)
        if usr is None:
            raise UserGetError(f"Пользователь с id = {str(user_id)} не найден")

        roles = await self.role_perm_repo.get_roles(ids=role_ids)

        return await self.role_perm_repo.delete_user_roles(user=usr, roles=[r.role for r in roles])

    async def get_all_users(self,
                            ids: List[UUID] | None,
                            emails: List[str] | None,
                            created_from: datetime | None,
                            created_to: datetime | None,
                            updated_from: datetime | None,
                            updated_to: datetime | None,
                            is_active: bool | None,
                            deleted_from: datetime | None,
                            deleted_to: datetime | None,
                            role_ids: List[UUID] | None) -> List[UserWithRolesEntity]:
        return await self.repo.get(ids=ids,
                                   emails=emails,
                                   created_from=created_from,
                                   created_to=created_to,
                                   updated_from=updated_from,
                                   updated_to=updated_to,
                                   is_active=is_active,
                                   deleted_from=deleted_from,
                                   deleted_to=deleted_to,
                                   role_ids=role_ids)

