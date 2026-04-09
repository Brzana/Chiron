from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from packages.backend.api.dependencies import get_db
from packages.backend.core.security import create_access_token
from packages.backend.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest
from packages.backend.services import user_service

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await user_service.register_user(
        username=body.username,
        email=body.email,
        password=body.password,
        role=body.role,
        db=db,
    )
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await user_service.authenticate_user(
        email=body.email,
        password=body.password,
        db=db,
    )
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(access_token=token)
