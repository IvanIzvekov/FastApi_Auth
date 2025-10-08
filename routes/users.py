from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from functools import partial

from entities.entities import UserEntity, CurrentUser

from repositories.session_repo import SessionRepository
from repositories.role_perm_repo import RolePermissionRepository
from repositories.user_repo import UserRepository

from schemas.user import UserCreate, UpdateUser, UsersRead, UpdateAllUsers
from schemas.role import RoleAdd

from dependencies import get_db, get_current_user, get_permission_user

from services.auth_service import AuthService
from services.user_service import UserService

from exceptions.custom_exceptions import UserEmailExistsError, SessionDeactivateError, NotFoundError, RoleGetError, \
    UserGetError

router = APIRouter(prefix="/user")

@router.post("/")
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
        user = user.to_dict()
        user.pop("hash_password")

        resp = {}
        resp["detail"] = "User created"
        resp['data'] = user
        return resp
    except UserGetError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RoleGetError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UserEmailExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.patch("/")
async def update_user(data: UpdateUser,
                      info: CurrentUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db),
                      permission_user = Depends(get_permission_user(permission_name="user:update"))
                      ):
    try:
        service = UserService(UserRepository(db), RolePermissionRepository(db))
        user = UserEntity(
            first_name=data.first_name,
            last_name=data.last_name,
            patronymic=data.patronymic,
            email=str(data.email),
            hash_password=data.password
        )
        user_w_r = await service.update_user(user=user)
        user_w_r = user_w_r.to_dict()
        user_w_r["user"].pop("hash_password")

        return user_w_r
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.get("/me")
async def get_current_user_route(
    data: CurrentUser = Depends(get_current_user),
    permission_user = Depends(get_permission_user(permission_name="user:get"))
):
    user = data.user.to_dict()
    user.pop("hash_password")
    return user

@router.get("/role")
async def get_current_user_route(
    data: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    permission_user = Depends(get_permission_user(permission_name="user:get"))
):
    service = UserService(UserRepository(db), RolePermissionRepository(db))
    user = await service.get_user_roles(data.user)
    user = user.to_dict()
    user.get('user').pop("hash_password")
    return user


@router.delete("/")
async def delete_user(data: CurrentUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db),
                      permission_user = Depends(get_permission_user(permission_name="user:delete"))):
    try:
        service = UserService(UserRepository(db=db), RolePermissionRepository(db=db))
        sess_service = AuthService(SessionRepository(db=db), UserRepository(db=db))

        session = data.session

        await sess_service.deactivate_session(session=session)
        user = data.user
        await service.delete_user(user=user)
        return {"detail": "User deleted"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SessionDeactivateError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ADMIN ROUTS
@router.get("/all", description="ADMIN")
async def get_user(filters: UsersRead = Depends(),
                   token_data: CurrentUser = Depends(get_current_user),
                   db: AsyncSession = Depends(get_db),
                   permission_user = Depends(get_permission_user(permission_name="user:get_all"))):
    try:
        del token_data
        service = UserService(UserRepository(db=db), RolePermissionRepository(db=db))
        users = await service.get_all_users(
            ids=filters.ids,
            emails=[str(email) for email in filters.emails] if filters.emails else None,
            created_from=filters.created_from,
            created_to=filters.created_to,
            updated_from=filters.updated_from,
            updated_to=filters.updated_to,
            is_active=filters.is_active,
            deleted_from=filters.deleted_from,
            deleted_to=filters.deleted_to,
            role_ids=filters.role_ids,
        )
        return [user.to_dict() for user in users]
    except UserGetError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/remove-role", description="ADMIN")
async def remove_role(roles: RoleAdd,
                      data: CurrentUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db),
                      permission_user = Depends(get_permission_user(permission_name="user.remove_role:start"))
                      ):
    try:
        service = UserService(UserRepository(db=db), RolePermissionRepository(db=db))

        result = await service.remove_roles_from_user(user_id=roles.user_id, role_ids=roles.role_ids)
        return result.to_dict()
    except (RoleGetError, UserGetError) as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/add-role", description="ADMIN")
async def add_role(roles: RoleAdd,
                   data: CurrentUser = Depends(get_current_user),
                   db: AsyncSession = Depends(get_db),
                   permission_user=Depends(get_permission_user(permission_name="user.add_role:start"))
                   ):
    try:
        service = UserService(UserRepository(db=db), RolePermissionRepository(db=db))

        result = await service.add_roles_to_user(user_id=roles.user_id, role_ids=roles.role_ids)
        return result.to_dict()
    except (RoleGetError, UserGetError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{user_id}", description="ADMIN")
async def update_user(user_id: str,
                      info_user: UpdateAllUsers,
                      data: CurrentUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db),
                      permission_user=Depends(get_permission_user(permission_name="user:update_all"))
                      ):
    try:
        service = UserService(UserRepository(db), RolePermissionRepository(db))
        user = UserEntity(
            first_name=info_user.first_name,
            last_name=info_user.last_name,
            patronymic=info_user.patronymic,
            email=str(info_user.email),
            hash_password=info_user.password
        )
        user_w_r = await service.update_user(user=user)
        user_w_r = user_w_r.to_dict()
        user_w_r["user"].pop("hash_password")

        return user_w_r
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
