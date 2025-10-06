import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from uuid import UUID

from sqlalchemy.orm import selectinload
from sqlalchemy.testing.suite.test_reflection import users

from models import User as DBUser, Role as DBRole
from entities.entities import UserEntity, UserWithRolesEntity, RoleEntity
from exceptions.custom_exceptions import UserEmailExistsError, UserCreateError, UserGetError, UserDeleteError, \
    UserUpdateError


class UserRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def check_re_registration(self, email) -> UserWithRolesEntity | None:
        try:
            result = await self._db.execute(
                select(DBUser).options(selectinload(DBUser.roles)).where(
                    and_(
                        DBUser.email == email,
                        DBUser.is_active == False
                    )
                )
            )

            user = result.scalar_one_or_none()
            if not user:
                return None

            user.is_active = True
            user.deleted_at = None

            await self._db.flush()
            await self._db.refresh(user)

            return UserWithRolesEntity(
                user=UserEntity(
                    id=user.id,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    patronymic=user.patronymic,
                    is_active=user.is_active,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                    hash_password=user.hash_password,
                    deleted_at=user.deleted_at
                ),
                roles=[RoleEntity(
                    id=role.id,
                    name=role.name,
                    created_at=role.created_at,
                    updated_at=role.updated_at
                ) for role in user.roles]
            )

        except IntegrityError as e:
            raise UserEmailExistsError(e) from e
        except SQLAlchemyError as e:
            raise UserUpdateError(e) from e

    async def update(self, user: UserEntity) -> UserWithRolesEntity:
        try:
            stmt = select(DBUser).options(selectinload(DBUser.roles)).where(
                and_(
                    DBUser.id == user.id,
                    DBUser.is_active == True
                )
            )
            result = await self._db.execute(stmt)
            user_orm = result.scalar_one_or_none()
            if not user:
                raise UserGetError(f"Пользователь с id={user.id} не найден")
            if user.first_name:
                user_orm.first_name = user.first_name
            if user.last_name:
                user_orm.last_name = user.last_name
            if user.patronymic is not None:
                user_orm.patronymic = user.patronymic
            if user.hash_password:
                user_orm.hash_password = user.hash_password
            if user.email:
                user_orm.email = user.email

            await self._db.flush()
            await self._db.refresh(user_orm)

            return UserWithRolesEntity(
                user=UserEntity(
                    id=user_orm.id,
                    email=user_orm.email,
                    first_name=user_orm.first_name,
                    last_name=user_orm.last_name,
                    patronymic=user_orm.patronymic,
                    is_active=user_orm.is_active,
                    created_at=user_orm.created_at,
                    updated_at=user_orm.updated_at,
                    hash_password=user_orm.hash_password,
                    deleted_at=user_orm.deleted_at
                ),
                roles=[RoleEntity(
                    id=role.id,
                    name=role.name,
                    created_at=role.created_at,
                    updated_at=role.updated_at
                ) for role in user_orm.roles]
            )

        except IntegrityError as e:
            raise UserEmailExistsError(e) from e
        except SQLAlchemyError as e:
            raise UserUpdateError(e) from e

    async def get_by_email(self, email: str) -> UserEntity | None:
        try:
            result = await self._db.execute(
                select(DBUser).where(
                    and_(
                        DBUser.email == email,
                        DBUser.is_active == True
                    )
                )
            )
            user = result.scalar_one_or_none()
            if user is None:
                return None
            else:
                return UserEntity(
                    id=user.id,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    patronymic=user.patronymic,
                    is_active=user.is_active,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                    hash_password=user.hash_password
                )
        except SQLAlchemyError as e:
            raise UserGetError(f"Ошибка при получении пользователя с email={email}: {e}")

    async def create(self, user: UserEntity) -> UserEntity:
        user_orm = DBUser(
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            patronymic=user.patronymic,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            hash_password=user.hash_password
        )
        self._db.add(user_orm)
        try:
            await self._db.flush()
            await self._db.refresh(user_orm)

            user.id = user_orm.id
            user.email = user_orm.email
            user.first_name = user_orm.first_name
            user.last_name = user_orm.last_name
            user.patronymic = user_orm.patronymic
            user.is_active = user_orm.is_active
            user.created_at = user_orm.created_at
            user.updated_at = user_orm.updated_at
            user.hash_password = user_orm.hash_password
            return user

        except SQLAlchemyError as e:
            raise UserCreateError(f"Не удалось создать пользователя {user.email}: {e}")

    async def get_by_id(self, user_id: UUID) -> UserEntity | None:
        try:
            result = await self._db.execute(
                select(DBUser).where(
                    and_(
                        DBUser.id == user_id,
                        DBUser.is_active == True
                    )
                )
            )
            user = result.scalar_one_or_none()
            if not user:
                return None
            return UserEntity(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                patronymic=user.patronymic,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at,
                hash_password=user.hash_password
            )
        except SQLAlchemyError as e:
            raise UserGetError(f"Ошибка при получении пользователя id={user_id}: {e}") from e

    async def soft_delete(self, user: UserEntity):
        try:
            user = await self._db.get(DBUser, user.id)
            if not user:
                raise ValueError(f"Пользователь id={user.id} не найден")

            user.is_active = False
            user.deleted_at = datetime.datetime.now()

            await self._db.flush()
        except SQLAlchemyError as e:
            raise UserDeleteError(f"Ошибка при деактивации пользователя id={user.id}: {e}") from e

    async def get(self,
                  ids: List[UUID] | None,
                  emails: List[str] | None,
                  created_from: datetime.datetime | None,
                  created_to: datetime.datetime | None,
                  updated_from: datetime.datetime | None,
                  updated_to: datetime.datetime | None,
                  is_active: bool | None,
                  deleted_from: datetime.datetime | None,
                  deleted_to: datetime.datetime | None,
                  role_ids: List[UUID] | None):

        stmt = select(DBUser).options(selectinload(DBUser.roles))

        if ids:
            stmt = stmt.where(DBUser.id.in_(ids))
        if emails:
            stmt = stmt.where(DBUser.email.in_(emails))

        if created_from:
            stmt = stmt.where(DBUser.created_at >= created_from)
        if created_to:
            stmt = stmt.where(DBUser.created_at <= created_to)

        if updated_from:
            stmt = stmt.where(DBUser.updated_at >= updated_from)
        if updated_to:
            stmt = stmt.where(DBUser.updated_at <= updated_to)

        if is_active is not None:
            stmt = stmt.where(DBUser.is_active == is_active)

        if is_active == False and deleted_from:
            stmt = stmt.where(DBUser.deleted_at >= deleted_from)
        if is_active == False and deleted_to:
            stmt = stmt.where(DBUser.deleted_at <= deleted_to)

        if role_ids:
            stmt = stmt.where(DBUser.roles.any(DBRole.id.in_(role_ids)))

        results = await self._db.execute(stmt)
        users_orm = results.scalars().all()

        return [
            UserWithRolesEntity(
                user=UserEntity(
                    id=user_orm.id,
                    email=user_orm.email,
                    first_name=user_orm.first_name,
                    last_name=user_orm.last_name,
                    patronymic=user_orm.patronymic,
                    is_active=user_orm.is_active,
                    created_at=user_orm.created_at,
                    updated_at=user_orm.updated_at,
                    deleted_at=user_orm.deleted_at,
                ),
                roles=[RoleEntity(
                    id=role_orm.id,
                    name=role_orm.name,
                    created_at=role_orm.created_at,
                    updated_at=role_orm.updated_at
                ) for role_orm in user_orm.roles]
            ) for user_orm in users_orm]




