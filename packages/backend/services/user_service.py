from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.backend.core.security import hash_password, verify_password
from packages.backend.models.models import RoleEnum, User


async def register_user(
    username: str,
    email: str,
    password: str,
    role: RoleEnum,
    db: AsyncSession,
) -> User:
    existing = await db.execute(
        select(User).where((User.username == username) | (User.email == email))
    )
    conflict = existing.scalar_one_or_none()

    if conflict is not None:
        field = "Username" if conflict.username == username else "Email"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "duplicate_field", "message": f"{field} is already taken."},
        )

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(email: str, password: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials", "message": "Invalid email or password."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
