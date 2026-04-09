from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from packages.backend.models.models import RoleEnum


class TokenPayload(BaseModel):
    sub: str
    role: RoleEnum
    exp: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: RoleEnum

    @field_validator("role")
    @classmethod
    def role_must_be_student_or_teacher(cls, v: RoleEnum) -> RoleEnum:
        if v == RoleEnum.ADMIN:
            raise ValueError("Cannot self-register as ADMIN.")
        return v

    @field_validator("username")
    @classmethod
    def username_min_length(cls, v: str) -> str:
        if len(v.strip()) < 3:
            raise ValueError("Username must be at least 3 characters.")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: RoleEnum
    created_at: datetime

    model_config = {"from_attributes": True}
