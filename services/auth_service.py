from enum import Enum
from fastapi.concurrency import run_in_threadpool

import jwt
import bcrypt
from uuid import UUID
from datetime import datetime, timedelta

from entities.entities import SessionEntity
from repositories.user_repo import UserRepository
from repositories.session_repo import SessionRepository
from exceptions.custom_exceptions import (
    UnauthorizedException,
    SessionCreateError,
    SessionGetError,
    SessionDeactivateError,
)
from core.config import settings


class AuthService:
    def __init__(self, repo: SessionRepository, user_repo: UserRepository):
        self.repo = repo
        self.user_repo = user_repo

    @staticmethod
    def create_jwt(session_id: UUID, scope: str, minutes: int = None, expire_at=None) -> str:
        """Создать JWT сессии"""
        payload = {"session_id": str(session_id), "scope": scope}
        if minutes:
            payload["exp"] = int((datetime.now() + timedelta(minutes=minutes)).timestamp())
        if expire_at:
            payload["exp"] = int(expire_at.timestamp())
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    async def hash_password(password: str) -> str:
        return await run_in_threadpool(lambda: bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode())

    @staticmethod
    async def verify_password(plain: str, hashed: str) -> bool:
        return await run_in_threadpool(lambda: bcrypt.checkpw(plain.encode(), hashed.encode()))

    async def login(self, email: str, password: str, device: Enum) -> dict:
        """Авторизация пользователя и создание сессии"""
        try:
            user = await self.user_repo.get_by_email(email.strip().lower())
        except Exception as e:
            raise UnauthorizedException(f"Ошибка при получении пользователя: {e}") from e
        if not user or not await self.verify_password(password, user.hash_password):
            raise UnauthorizedException("Неверные учетные данные")

        expire_at = datetime.now() + timedelta(days=settings.REFRESH_EXPIRE_DAYS)
        unclosed_sessions = await self.repo.get_active_by_user_id(user, device)
        for session in unclosed_sessions:
            await self.repo.deactivate(session)
        try:
            session = await self.repo.create(user, expire_at, device)
        except SessionCreateError as e:
            raise UnauthorizedException(f"Ошибка при создании сессии: {e}") from e
        access_token = self.create_jwt(session.id, "access", minutes=settings.ACCESS_EXPIRE_MINUTES)
        refresh_token = self.create_jwt(session.id, "refresh", expire_at=expire_at)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "session": session.id,
            "session_expire_at": session.expire_at,
            "device": session.device
        }

    async def get_current_user(self, token: str):
        """Получить текущего пользователя по access"""
        try:
            token = token.strip()
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            print(payload)
            session_id = payload.get("session_id")
            scope = payload.get("scope")
            if scope != "access":
                raise UnauthorizedException("Требуется access token")
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException("Токен истек")
        except Exception as e:
            raise UnauthorizedException(f"Неверный токен, {e}")

        try:
            session = SessionEntity(id=UUID(session_id))
            session = await self.repo.get_active_by_id(session)
        except (SessionGetError, SessionDeactivateError) as e:
            raise UnauthorizedException(f"Ошибка при проверке сессии: {e}") from e

        if not session or session.expire_at < datetime.now():
            raise UnauthorizedException("Сессия закрыта или истекла")

        try:
            user = await self.user_repo.get_by_id(session.user_id)
        except Exception as e:
            raise UnauthorizedException(f"Ошибка при получении пользователя: {e}") from e

        if not user:
            raise UnauthorizedException("Пользователь не найден")

        return user, session


    async def deactivate_session(self, session: SessionEntity):
        try:
            await self.repo.deactivate(session)
        except (SessionDeactivateError, SessionGetError) as e:
            raise SessionDeactivateError(f"Ошибка при деактивации сессии: {e}") from e

    async def logout(self, session: SessionEntity):
        """Закрыть текущую сессию"""
        try:
            await self.repo.deactivate(session)
        except (SessionDeactivateError, SessionGetError) as e:
            raise UnauthorizedException(f"Ошибка при деактивации сессии: {e}") from e
        except Exception:
            raise UnauthorizedException("Неверный токен")

    async def refresh(self, refresh_token: str) -> dict:
        """Обновить access и refresh токены"""
        try:
            refresh_token = refresh_token.strip()

            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"verify_exp": False}
            )
            session = SessionEntity(
                id=payload.get("session_id", "")
            )
            scope = payload.get("scope", "")
        except Exception:
            raise UnauthorizedException("Неверный refresh токен")

        if scope != "refresh":
            raise UnauthorizedException("Неверный тип токена для refresh")

        session = await self.repo.get_active_by_id(session)
        if not session:
            raise UnauthorizedException("Refresh токен недействителен")

        if session.expire_at < datetime.now():
            await self.repo.deactivate(session)
            raise UnauthorizedException("Refresh токен истёк")

        access_token = self.create_jwt(session.id, "access", minutes=settings.ACCESS_EXPIRE_MINUTES)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "session": session.id,
            "session_expire_at": session.expire_at,
            "device": session.device
        }