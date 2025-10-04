from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from entities.entities import UserEntity, SessionEntity
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_db, extract_token
from repositories.user_repo import UserRepository
from repositories.session_repo import SessionRepository
from services.auth_service import AuthService
from exceptions.custom_exceptions import UnauthorizedException
from dependencies import get_current_user

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(SessionRepository(db), UserRepository(db))
    try:
        return await service.login(str(data.email), data.password, data.device)
    except UnauthorizedException as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(SessionRepository(db=db), UserRepository(db=db))
    try:
        return await service.refresh(refresh_token=data.refresh_token)
    except UnauthorizedException as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout(
    data: dict[str, UserEntity | SessionEntity] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(SessionRepository(db=db), UserRepository(db=db))
    try:
        await service.logout(session=data.get("session"))
        return JSONResponse(status_code=204, content={"detail": "Logged out"})
    except UnauthorizedException as e:
        raise HTTPException(status_code=401, detail=str(e))
