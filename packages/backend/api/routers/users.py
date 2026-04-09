from fastapi import APIRouter, Depends

from packages.backend.api.dependencies import get_current_user
from packages.backend.models.models import User
from packages.backend.schemas.auth import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
