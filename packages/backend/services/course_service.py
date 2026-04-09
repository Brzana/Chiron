from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from packages.backend.models.models import Course, RoleEnum, User


async def get_courses_by_role(user: User, db: AsyncSession) -> list[Course]:
    if user.role == RoleEnum.ADMIN:
        result = await db.execute(
            select(Course).options(selectinload(Course.teacher))
        )
        return list(result.scalars().all())

    if user.role == RoleEnum.TEACHER:
        result = await db.execute(
            select(Course)
            .where(Course.teacher_id == user.id)
            .options(selectinload(Course.teacher))
        )
        return list(result.scalars().all())

    result = await db.execute(
        select(User)
        .where(User.id == user.id)
        .options(selectinload(User.enrolled_courses).selectinload(Course.teacher))
    )
    loaded_user = result.scalar_one()
    return loaded_user.enrolled_courses


async def create_course(
    title: str,
    description: str | None,
    is_published: bool,
    teacher: User,
    db: AsyncSession,
) -> Course:
    existing = await db.execute(select(Course).where(Course.title == title))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "duplicate_title", "message": "A course with this title already exists."},
        )

    course = Course(
        title=title,
        description=description,
        is_published=is_published,
        teacher_id=teacher.id,
        teacher_role=teacher.role,
    )
    db.add(course)
    await db.commit()
    await db.refresh(course, ["teacher"])
    return course


async def update_course(
    course_id: int,
    title: str | None,
    description: str | None,
    is_published: bool | None,
    user: User,
    db: AsyncSession,
) -> Course:
    result = await db.execute(
        select(Course)
        .where(Course.id == course_id)
        .options(selectinload(Course.teacher))
    )
    course = result.scalar_one_or_none()

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "course_not_found", "message": "Course not found."},
        )

    if user.role != RoleEnum.ADMIN and course.teacher_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "not_course_owner", "message": "You can only update courses you teach."},
        )

    if title is not None:
        course.title = title
    if description is not None:
        course.description = description
    if is_published is not None:
        course.is_published = is_published

    await db.commit()
    await db.refresh(course, ["teacher"])
    return course
