from pydantic import BaseModel

from packages.backend.models.models import RoleEnum


class TokenPayload(BaseModel):
    sub: str
    role: RoleEnum
    exp: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"