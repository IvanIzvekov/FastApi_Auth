from pydantic import BaseModel, field_validator
from enum import Enum
from typing import List, Optional
from uuid import UUID


class EnumPermissionType(str, Enum):
    read = "get"
    update = "update"
    delete = "delete"
    create = "post"

class PermissionCreate(BaseModel):
    entity_name: str
    permission_type: EnumPermissionType
    is_all_attr: bool

    @field_validator("entity_name")
    def check_entity_name(cls, v):
        if ":" in v:
            raise ValueError("Название сущности не может содержать символ ':'")
        return v

class PermissionRead(BaseModel):
    ids: Optional[List[UUID]] = None
    names: Optional[List[str]] = None