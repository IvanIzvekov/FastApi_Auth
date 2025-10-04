from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


from entities.entities import UserEntity, SessionEntity, RoleEntity

from repositories.role_perm_repo import RolePermissionRepository

from services.role_service import RolePermissionService

from schemas.role import RoleCreate, RoleRead, RolePermissionCreate
from schemas.permission import PermissionCreate, PermissionRead

from dependencies import get_db, get_current_user

from exceptions.custom_exceptions import RoleAlreadyExistsError, PermissionAlreadyExistsError, RoleGetError, \
    PermissionGetError

router = APIRouter(prefix="/roles")

@router.post("")
async def create_role(data: RoleCreate, data_user: dict[str, UserEntity | SessionEntity] = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        service = RolePermissionService(repo=RolePermissionRepository(db=db))

        role = RoleEntity(
            name=data.name
        )
        await service.create_role(role=role)
        return {
            "detail": "Role created",
            "id": role.id,
            "created_at": role.created_at
        }
    except RoleAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/permissions")
async def create_permission(data: PermissionCreate, data_user: dict[str, UserEntity | SessionEntity] = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        service = RolePermissionService(repo=RolePermissionRepository(db=db))
        new_permission = await service.create_permission(entity_name=data.entity_name, permission_type=data.permission_type.value, is_all_attr=data.is_all_attr)
        return {
            "detail": f"Permission {new_permission.name} created",
            "id": new_permission.id,
        }
    except PermissionAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
async def get_roles(roles: RoleRead, data_user: dict[str, UserEntity | SessionEntity] = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = RolePermissionService(repo=RolePermissionRepository(db=db))

    roles = await service.get_roles(ids=roles.ids if roles.ids else None,
                                    names=roles.names if roles.names else None,
                                    date_from=roles.date_from if roles.date_from else None,
                                    date_to=roles.date_to if roles.date_to else None)
    return roles

@router.get("/permissions")
async def get_permissions(perms: PermissionRead, data_user: dict[str, UserEntity | SessionEntity] = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = RolePermissionService(repo=RolePermissionRepository(db=db))
    permissions = await service.get_permissions(ids=perms.ids, names=perms.names)
    return permissions

# ADMIN ROUTERS
@router.post("/add-permissions")
async def add_permissions_to_role(data: RolePermissionCreate, data_user: dict[str, UserEntity | SessionEntity] = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        service = RolePermissionService(repo=RolePermissionRepository(db=db))
        result = await service.add_permissions_to_role(role_id=data.role_id, permission_ids=data.permission_ids)
        return result
    except (RoleGetError, PermissionGetError) as e:
        raise HTTPException(status_code=404, detail=str(e))
