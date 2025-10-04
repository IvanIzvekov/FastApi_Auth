from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID

class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=3, max_length=20)
    last_name: str = Field(..., min_length=3, max_length=20)
    patronymic: Optional[str] = Field(None, min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=20)

class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    patronymic: Optional[str] = None
    role: UUID


class UpdateUser(BaseModel):
    first_name: Optional[str] = Field(None, min_length=3, max_length=20)
    last_name: Optional[str] = Field(None, min_length=3, max_length=20)
    patronymic: Optional[str] = Field(None, min_length=3, max_length=20)
    password: Optional[str] = Field(None, min_length=6, max_length=20)
    email: Optional[EmailStr] = None
