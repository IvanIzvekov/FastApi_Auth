from fastapi import APIRouter, Depends
from dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy import select
from models import User, Role, Permission
from database import engine, Base
from services.auth_service import AuthService

router = APIRouter()


async def recreate_all_async(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

@router.get("/test")
async def test(db: AsyncSession = Depends(get_db)):
    await recreate_all_async(engine)

    perms = [Permission(name=n) for n in [
        "product:get_all", "product:get", "product:update", "product:update_all",
        "product:delete_all", "product:delete", "product:post", "product:post_all",
        "user:delete", "user:delete_all", "user:update_all", "user:update",
        "user:get", "user:get_all", "role:get", "role:update", "role:update_all",
        "role:delete_all", "role:delete", "role:post_all", "role:post",
        "permission:get", "permission:update", "permission:update_all",
        "permission:delete_all", "permission:delete", "permission:post",
        "user.remove_role:start:start", "user.add_role:start:start",
        "role.add_permissions:start", "role.delete_permissions:start",
    ]]
    db.add_all(perms)
    await db.flush()

    role = Role(name="admin", permissions=perms)
    role_2 = Role(name="user", permissions=[perms[8], perms[11], perms[12]])
    role_3 = Role(name="seller")

    db.add_all([role, role_2, role_3])
    await db.flush()

    hash_pass = await AuthService.hash_password("admin")
    user = User(
        first_name="admin",
        last_name="admin",
        patronymic="admin",
        email="admin@admin.com",
        hash_password=hash_pass,
        roles=[role]
    )
    db.add(user)

    await db.commit()

    return {"detail": "Admin created, Roles created, perms created.",
            "email": "admin@admin.com",
            "password": "admin"}

