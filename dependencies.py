from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.auth_service import AuthService
from repositories.user_repo import UserRepository
from repositories.session_repo import SessionRepository
from exceptions.custom_exceptions import UnauthorizedException


async def extract_token(authorization: str) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    return parts[1]


async def get_current_user(authorization: str = Header(...), db: AsyncSession = Depends(get_db)):
    try:
        token = await extract_token(authorization)
        service = AuthService(SessionRepository(db), UserRepository(db))

        user , session = await service.get_current_user(token)
        return {
            "user": user,
            "session": session
        }
    except UnauthorizedException as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

