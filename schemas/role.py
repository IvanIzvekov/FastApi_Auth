from pydantic import BaseModel, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from fastapi import Query


class RoleCreate(BaseModel):
    name: str
    @field_validator('name')
    def check_name(cls, v):
        return v.strip().lower()

class RoleRead(BaseModel):
    ids: Optional[List[UUID]] = Query(None)
    names: Optional[List[str]] = Query(None)
    date_from: Optional[datetime] = Query(None)
    date_to: Optional[datetime] = Query(None)

    @field_validator("names")
    def check_names(cls, v):
        return [name.strip().lower() for name in v]


class RoleAdd(BaseModel):
    user_id: UUID
    role_ids: List[UUID]

class RolePermissionCreate(BaseModel):
    role_id: UUID
    permission_ids: List[UUID]