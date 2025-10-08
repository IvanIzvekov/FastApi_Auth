from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional, List
from uuid import UUID

class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=3, max_length=20)
    last_name: str = Field(..., min_length=3, max_length=20)
    patronymic: Optional[str] = Field(None, min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=20)

    @field_validator("first_name", "last_name", "patronymic")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value.isalpha():
            raise ValueError("Name must contain only letters (A-Z or А-Я)")
        return value.title()

class UsersRead(BaseModel):
    ids: Optional[List[UUID]] = None
    emails: Optional[List[EmailStr]] = None

    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None

    updated_from: Optional[datetime] = None
    updated_to: Optional[datetime] = None

    is_active: Optional[bool] = None
    deleted_from: Optional[datetime] = None
    deleted_to: Optional[datetime] = None

    role_ids: Optional[List[UUID]] = None

    @model_validator(mode="after")
    def validate_date_ranges(self) -> "UsersRead":
        date_pairs = [
            ("created_from", "created_to"),
            ("updated_from", "updated_to"),
            ("deleted_from", "deleted_to"),
        ]

        for start_field, end_field in date_pairs:
            start = getattr(self, start_field)
            end = getattr(self, end_field)

            if start and end and start > end:
                raise ValueError(
                    f"{start_field.replace('_', ' ').capitalize()} "
                    f"не может быть позже {end_field.replace('_', ' ')}."
                )

        return self


class UpdateUser(BaseModel):
    first_name: Optional[str] = Field(None, min_length=3, max_length=20)
    last_name: Optional[str] = Field(None, min_length=3, max_length=20)
    patronymic: Optional[str] = Field(None, min_length=3, max_length=20)
    password: Optional[str] = Field(None, min_length=6, max_length=20)
    email: Optional[EmailStr] = None

    @field_validator("first_name", "last_name", "patronymic")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value.isalpha():
            raise ValueError("Name must contain only letters (A-Z or А-Я)")
        return value.title()

class UpdateAllUsers(BaseModel):
    first_name: Optional[str] = Field(None, min_length=3, max_length=20)
    last_name: Optional[str] = Field(None, min_length=3, max_length=20)
    patronymic: Optional[str] = Field(None, min_length=3, max_length=20)
    password: Optional[str] = Field(None, min_length=6, max_length=20)
    email: Optional[EmailStr] = None

    @field_validator("first_name", "last_name", "patronymic")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value.isalpha():
            raise ValueError("Name must contain only letters (A-Z or А-Я)")
        return value.title()
