from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from packages.backend.api.dependencies import get_current_user, get_db, require_role
from packages.backend.models.models import RoleEnum, User
from packages.backend.schemas.courses import CourseCreateRequest, CourseResponse, CourseUpdateRequest
from packages.backend.services import course_service

router = APIRouter()


@router.get("", response_model=list[CourseResponse])
async def get_courses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CourseResponse]:
    courses = await course_service.get_courses_by_role(user=current_user, db=db)
    return [CourseResponse.model_validate(c) for c in courses]


@router.post("", response_model=CourseResponse, status_code=201)
async def create_course(
    body: CourseCreateRequest,
    current_user: User = Depends(require_role(RoleEnum.TEACHER)),
    db: AsyncSession = Depends(get_db),
) -> CourseResponse:
    course = await course_service.create_course(
        title=body.title,
        description=body.description,
        is_published=body.is_published,
        teacher=current_user,
        db=db,
    )
    return CourseResponse.model_validate(course)


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    body: CourseUpdateRequest,
    current_user: User = Depends(require_role(RoleEnum.TEACHER)),
    db: AsyncSession = Depends(get_db),
) -> CourseResponse:
    course = await course_service.update_course(
        course_id=course_id,
        title=body.title,
        description=body.description,
        is_published=body.is_published,
        user=current_user,
        db=db,
    )
    return CourseResponse.model_validate(course)
