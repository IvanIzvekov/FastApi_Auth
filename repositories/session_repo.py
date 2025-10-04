from enum import Enum
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from entities.entities import SessionEntity, UserEntity

from models import Session as DBSess
from exceptions.custom_exceptions import SessionCreateError, SessionGetError, SessionDeactivateError

class SessionRepository:
    def __init__(self, db: AsyncSession):
        self._db = db


    async def create(self, user: UserEntity, expire_at: datetime, device: Enum) -> SessionEntity:
        """Создать новую сессию"""
        session = DBSess(user_id=user.id, expire_at=expire_at, device=device)
        self._db.add(session)
        try:
            await self._db.flush()
            await self._db.refresh(session)
            return SessionEntity(
                id=session.id,
                user_id=session.user_id,
                is_active=session.is_active,
                created_at=session.created_at,
                expire_at=session.expire_at,
                device=session.device,
            )
        except SQLAlchemyError as e:
            raise SessionCreateError(f"Не удалось создать сессию для user_id={user.id}: {e}") from e


    async def get_active_by_user_id(self, user: UserEntity, device: Enum) -> SessionEntity | List:
        """Получить активную сессию по ID Пользователя"""
        try:
            result = await self._db.execute(
                select(DBSess).where(
                        and_(
                            DBSess.user_id == user.id,
                            DBSess.is_active == True,
                            DBSess.device == device.value
                        )
                    )
            )
            session = result.scalars().all()
            if not session:
                return []
            return [
                SessionEntity(
                    id=s.id,
                    user_id=s.user_id,
                    is_active=s.is_active,
                    created_at=s.created_at,
                    expire_at=s.expire_at,
                    device=s.device,
                ) for s in session
            ]
        except SQLAlchemyError as e:
            raise SessionGetError(f"Ошибка при получении активной сессии: {e}") from e


    async def get_active_by_id(self, session: SessionEntity) -> SessionEntity | None:
        """Получить активную сессию по ID"""
        try:
            session_orm = await self._db.execute(
                select(DBSess).where(
                    and_(
                        DBSess.id == session.id,
                        DBSess.is_active == True
                    )
                )
            )
            session_orm = session_orm.scalar_one_or_none()
            if not session_orm:
                return None

            return SessionEntity(
                id=session_orm.id,
                user_id=session_orm.user_id,
                is_active=session_orm.is_active,
                created_at=session_orm.created_at,
                expire_at=session_orm.expire_at,
                device=session_orm.device,
            )
        except SQLAlchemyError as e:
            raise SessionGetError(f"Ошибка при получении сессии id={session.id}: {e}") from e


    async def deactivate(self, session: SessionEntity) -> SessionEntity | None:
        """Деактивировать активную сессию"""
        try:
            session_entity = await self.get_active_by_id(session)
            if not session_entity:
                return None
            else:
                orm_session = await self._db.get(DBSess, session.id)
                orm_session.is_active = False
                await self._db.flush()
                await self._db.refresh(orm_session)

                session_entity.is_active = False

                return session_entity
        except SQLAlchemyError as e:
            raise SessionDeactivateError(f"Ошибка при деактивации сессии id={session.id}: {e}") from e