from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


from entities.entities import UserEntity, SessionEntity, RoleEntity, CurrentUser

from repositories.role_perm_repo import RolePermissionRepository

from services.role_service import RolePermissionService

from schemas.role import RoleCreate, RoleRead, RolePermissionCreate
from schemas.permission import PermissionCreate, PermissionRead

from dependencies import get_db, get_current_user, get_permission_user

from exceptions.custom_exceptions import RoleAlreadyExistsError, PermissionAlreadyExistsError, RoleGetError, \
    PermissionGetError

router = APIRouter(prefix="/roles")

@router.post("/")
async def create_role(data: RoleCreate,
                      data_user: CurrentUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    try:
        service = RolePermissionService(repo=RolePermissionRepository(db=db))

        role = RoleEntity(
            name=data.name
        )
        role = await service.create_role(role=role)
        role = role.to_dict()
        return {
            "detail": "Role created",
            "data": role
        }
    except RoleAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/permissions")
async def create_permission(data: PermissionCreate,
                            data_user: CurrentUser = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db),
                            permission_user = Depends(get_permission_user(permission_name="permission:post"))):
    try:
        service = RolePermissionService(repo=RolePermissionRepository(db=db))
        new_permission = await service.create_permission(entity_name=data.entity_name, permission_type=data.permission_type.value, is_all_attr=data.is_all_attr)
        permission = new_permission.to_dict()

        return {
            "detail": "Permission created",
            "data": permission
        }
    except PermissionAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
async def get_roles(roles: RoleRead,
                    data_user: CurrentUser = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db),
                    permission_user = Depends(get_permission_user(permission_name="role:get"))):
    service = RolePermissionService(repo=RolePermissionRepository(db=db))

    roles = await service.get_roles(ids=roles.ids if roles.ids else None,
                                    names=roles.names if roles.names else None,
                                    date_from=roles.date_from if roles.date_from else None,
                                    date_to=roles.date_to if roles.date_to else None)

    return [role.to_dict() for role in roles]

@router.get("/permissions")
async def get_permissions(perms: PermissionRead,
                          data_user: CurrentUser = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db),
                          permission_user = Depends(get_permission_user(permission_name="permission:get"))):
    service = RolePermissionService(repo=RolePermissionRepository(db=db))
    permissions = await service.get_permissions(ids=perms.ids, names=perms.names)
    response = [permission.to_dict() for permission in permissions]
    return response

# ADMIN ROUTERS
@router.post("/add-permissions")
async def add_permissions_to_role(data: RolePermissionCreate,
                                  data_user: CurrentUser = Depends(get_current_user),
                                  db: AsyncSession = Depends(get_db),
                                  permission_user = Depends(get_permission_user(permission_name="role.add_permissions:start"))):
    try:
        service = RolePermissionService(repo=RolePermissionRepository(db=db))
        result = await service.add_permissions_to_role(role_id=data.role_id, permission_ids=data.permission_ids)
        return result.to_dict()
    except (RoleGetError, PermissionGetError) as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/delete-permissions")
async def delete_permissions_from_role(data: RolePermissionCreate,
                                       data_user: CurrentUser = Depends(get_current_user),
                                       db: AsyncSession = Depends(get_db),
                                       permission_user = Depends(get_permission_user(permission_name="role.delete_permissions:start"))):
    try:
        service = RolePermissionService(repo=RolePermissionRepository(db=db))
        result = await service.delete_permissions_from_role(role_id=data.role_id, permission_ids=data.permission_ids)
        return result.to_dict()
    except (RoleGetError, PermissionGetError) as e:
        raise HTTPException(status_code=404, detail=str(e))
