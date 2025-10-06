from fastapi import APIRouter, Depends
from dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import User, Role, Permission
from database import engine, Base
from repositories.session_repo import SessionRepository
from services.auth_service import AuthService
from repositories.user_repo import UserRepository
from repositories.session_repo import SessionRepository

router = APIRouter()


@router.get("/test")
async def test(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    if users:
        Base.metadata.drop_all(bind=engine)

    role = Role(name="admin")
    role_2 = Role(name="user")
    role_3 = Role(name="seller")
    db.add(role)
    db.add(role_2)
    db.add(role_3)
    await db.flush()

    await db.refresh(role)
    await db.refresh(role_2)
    await db.refresh(role_3)

    hash_pass = await AuthService.hash_password("admin")
    user = User(first_name="admin", last_name="admin", patronymic="admin", email="admin@admin.com", hash_password=hash_pass, roles=[role])
    db.add(user)
    await db.flush()
    await db.refresh(user)

    perms = [Permission(name="product:get_all"),
             Permission(name="product:get"),
             Permission(name="product:update"),
             Permission(name="product:update_all"),
             Permission(name="product:delete_all"),
             Permission(name="product:delete"),
             Permission(name="product:post"),
             Permission(name="product:post_all"),
             Permission(name="user:delete"),
             Permission(name="user:delete_all"),
             Permission(name="user:update_all"),
             Permission(name="user:update"),
             Permission(name="user:get"),
             Permission(name="user:get_all"),
             Permission(name="role:get"),
             Permission(name="role:update"),
             Permission(name="role:update_all"),
             Permission(name="role:delete_all"),
             Permission(name="role:delete"),
             Permission(name="role:post_all"),
             Permission(name="role:post"),
             Permission(name="permission:get"),
             Permission(name="permission:update"),
             Permission(name="permission:update_all"),
             Permission(name="permission:delete_all"),
             Permission(name="permission:delete"),
             Permission(name="permission:post"),
             Permission(name="user.remove_role:start:start"),
             Permission(name="user.add_role:start:start"),
             Permission(name="role.add_permissions:start"),
             Permission(name="role.delete_permissions:start")]

    for perm in perms:
        db.add(perm)
        await db.refresh(perm)

    role.permissions = perms

    await db.flush()
    await db.refresh(role)

    role_2.permissions = [perms[8], perms[11], perms[12]]
    await db.flush()
    await db.refresh(role_2)

    user.roles = role
    await db.flush()

    return {"detail": "Admin created, Roles created, perms created.",
            "email": "admin@admin.com",
            "password": "admin"}
