from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


from entities.entities import UserEntity, SessionEntity

from repositories.session_repo import SessionRepository
from repositories.role_perm_repo import RolePermissionRepository
from repositories.user_repo import UserRepository

from schemas.user import UserCreate, UpdateUser
from schemas.role import RoleAdd

from dependencies import get_db, get_current_user

from services.auth_service import AuthService
from services.user_service import UserService

from exceptions.custom_exceptions import UserEmailExistsError, SessionDeactivateError, NotFoundError, RoleGetError, \
    UserGetError

router = APIRouter(prefix="/user")

@router.post("")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        # В идеале пароль уже хешируется на клиенте, а мы видим только хеш, но для удобства будем находить хеш уже на бэке
        hashed = await AuthService.hash_password(password=user.password)
        service = UserService(repo=UserRepository(db=db), role_perm_repo=RolePermissionRepository(db=db))
        user.password = hashed
        usr_ent = UserEntity(
            first_name=user.first_name,
            last_name=user.last_name,
            patronymic=user.patronymic,
            email=str(user.email),
            hash_password=user.password
        )
        user =  await service.create_user(user=usr_ent)
        return {
            "detail": "User created",
            "id": user.id,
            "created_at": user.created_at,
        }
    except UserGetError as e:
        raise HTTPException(status_code=50, detail=str(e))
    except RoleGetError as e:
        raise HTTPException(status_code=201, detail=str(e))
    except UserEmailExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.patch("/")
async def update_user(data: UpdateUser, info: dict[str, UserEntity | SessionEntity] = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        service = UserService(UserRepository(db), RolePermissionRepository(db))
        user = UserEntity(
            id=info.get("user").id,
            first_name=data.first_name,
            last_name=data.last_name,
            patronymic=data.patronymic,
            email=data.email,
            hash_password=data.password
        )
        user =  await service.update_user(user=user)
        return {
            "detail": "User updated",
            "id": user.id,
            "updated_at": user.updated_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.get("/")
async def get_current_user_route(
    data: dict[str, UserEntity | SessionEntity] = Depends(get_current_user)
):
    user = data.get("user")
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "patronymic": user.patronymic,
        "role_id": user.role_id,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


@router.delete("/")
async def delete_user(data: dict[str, UserEntity | SessionEntity] = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        service = UserService(UserRepository(db=db), RolePermissionRepository(db=db))
        sess_service = AuthService(SessionRepository(db=db), UserRepository(db=db))

        session = data.get("session")

        await sess_service.deactivate_session(session=session)
        user = data.get("user")
        await service.delete_user(user=user)
        return {"detail": "User deleted"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SessionDeactivateError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ADMIN ROUTS
@router.post("/add-role")
async def add_role(roles: RoleAdd, data: dict[str, UserEntity | SessionEntity] = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        service = UserService(UserRepository(db=db), RolePermissionRepository(db=db))

        result = await service.add_role_to_user(user_id=roles.user_id, role_ids=roles.role_ids)
        return result
    except (RoleGetError, UserGetError) as e:
        raise HTTPException(status_code=404, detail=str(e))

