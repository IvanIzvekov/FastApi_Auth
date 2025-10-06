from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from entities.entities import CurrentUser
from services.auth_service import AuthService
from repositories.user_repo import UserRepository
from repositories.session_repo import SessionRepository
from repositories.role_perm_repo import RolePermissionRepository
from exceptions.custom_exceptions import UnauthorizedException, UserNotHaveRoles
from services.role_service import RolePermissionService
from services.user_service import UserService


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
        result = CurrentUser(user=user, session=session)
        return result
    except UnauthorizedException as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_permission_user(permission_name: str):
    async def dependency(
            authorization: str = Header(...),
            db: AsyncSession = Depends(get_db)
            ):
        token = await extract_token(authorization)
        auth_service = AuthService(SessionRepository(db), UserRepository(db))
        user , session = await auth_service.get_current_user(token)

        user_service = UserService(UserRepository(db), RolePermissionRepository(db))
        user_with_roles = await user_service.get_user_roles(user)

        permission_service = RolePermissionService(RolePermissionRepository(db))
        roles_with_permissions = await permission_service.get_roles(
            ids=[role.id for role in user_with_roles.roles]
        )

        user_permissions = {p.name for r in roles_with_permissions for p in r.permissions}

        if permission_name not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав"
            )

        return None

    return dependency

