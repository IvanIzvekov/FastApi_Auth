from pydantic import BaseModel, EmailStr
from enum import Enum
from datetime import datetime
from uuid import UUID

class DeviceType(str, Enum):
    MOBILE_APP = "MOBILE_APP"
    DESKTOP_APP = "DESKTOP_APP"
    WEB_APP = "WEB"
    TV = "TV"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device: DeviceType

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    session: UUID
    session_expire_at: datetime
    device: DeviceType

class RefreshRequest(BaseModel):
    refresh_token: str
