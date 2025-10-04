from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from fastapi import Query


class RoleCreate(BaseModel):
    name: str

class RoleRead(BaseModel):
    ids: Optional[List[UUID]] = Query(None)
    names: Optional[List[str]] = Query(None)
    date_from: Optional[datetime] = Query(None)
    date_to: Optional[datetime] = Query(None)

class RoleAdd(BaseModel):
    user_id: UUID
    role_ids: List[UUID]

class RolePermissionCreate(BaseModel):
    role_id: UUID
    permission_ids: List[UUID]