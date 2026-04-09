import sys
from pathlib import Path

# Add the root directory to the Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

"""
Pytest configuration and fixtures for all tests.
"""
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Set up test environment variables before importing app
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_EXPIRATION_MINUTES"] = "60"

from packages.backend.core.database import Base
from packages.backend.core.security import create_access_token, hash_password
from packages.backend.main import app
from packages.backend.api.dependencies import get_db
from packages.backend.models.models import User, RoleEnum, Course


# Test database setup
@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create an in-memory SQLite database for testing."""
    # Use SQLite with asyncio support for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_factory() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
def override_get_db(test_db):
    """Override the get_db dependency."""
    async def _override_get_db():
        yield test_db
    
    return _override_get_db


@pytest.fixture
def client(override_get_db):
    """Create a test client with overridden database dependency."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# User fixtures
@pytest_asyncio.fixture
async def test_student_user(test_db: AsyncSession) -> User:
    """Create a test student user."""
    user = User(
        username="testuser",
        email="student@example.com",
        hashed_password=hash_password("TestPassword123"),
        role=RoleEnum.STUDENT,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_teacher_user(test_db: AsyncSession) -> User:
    """Create a test teacher user."""
    user = User(
        username="testteacher",
        email="teacher@example.com",
        hashed_password=hash_password("TeacherPass123"),
        role=RoleEnum.TEACHER,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin_user(test_db: AsyncSession) -> User:
    """Create a test admin user."""
    user = User(
        username="testadmin",
        email="admin@example.com",
        hashed_password=hash_password("AdminPass123"),
        role=RoleEnum.ADMIN,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


# Token fixtures
@pytest.fixture
def student_token(test_student_user) -> str:
    """Create a JWT token for a student user."""
    return create_access_token({"sub": str(test_student_user.id), "role": test_student_user.role.value})


@pytest.fixture
def teacher_token(test_teacher_user) -> str:
    """Create a JWT token for a teacher user."""
    return create_access_token({"sub": str(test_teacher_user.id), "role": test_teacher_user.role.value})


@pytest.fixture
def admin_token(test_admin_user) -> str:
    """Create a JWT token for an admin user."""
    return create_access_token({"sub": str(test_admin_user.id), "role": test_admin_user.role.value})


# Course fixtures
@pytest_asyncio.fixture
async def test_course(test_db: AsyncSession, test_teacher_user: User) -> Course:
    """Create a test course."""
    course = Course(
        title="Python Basics",
        description="Learn Python fundamentals",
        is_published=True,
        teacher_id=test_teacher_user.id,
        teacher_role=test_teacher_user.role,
    )
    test_db.add(course)
    await test_db.commit()
    await test_db.refresh(course)
    return course


@pytest_asyncio.fixture
async def test_unpublished_course(test_db: AsyncSession, test_teacher_user: User) -> Course:
    """Create an unpublished test course."""
    course = Course(
        title="Advanced Python",
        description="Advanced Python topics",
        is_published=False,
        teacher_id=test_teacher_user.id,
        teacher_role=test_teacher_user.role,
    )
    test_db.add(course)
    await test_db.commit()
    await test_db.refresh(course)
    return course
