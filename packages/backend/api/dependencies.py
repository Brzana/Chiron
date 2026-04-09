from collections.abc import AsyncIterator, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.backend.core.database import async_session
from packages.backend.core.security import decode_token
from packages.backend.models.models import Course, RoleEnum, User, course_enrollment

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncIterator[AsyncSession]:
	async with async_session() as session:
		yield session


def _unauthorized_exception() -> HTTPException:
	return HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials.",
		headers={"WWW-Authenticate": "Bearer"},
	)


def _forbidden_exception(detail: str) -> HTTPException:
	return HTTPException(
		status_code=status.HTTP_403_FORBIDDEN,
		detail=detail,
	)


def _normalize_role(role_name: RoleEnum | str) -> RoleEnum:
	if isinstance(role_name, RoleEnum):
		return role_name

	try:
		return RoleEnum(role_name.lower())
	except ValueError as exc:
		raise ValueError(f"Unsupported role: {role_name}") from exc


async def get_current_user(
	credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
	db: AsyncSession = Depends(get_db),
) -> User:
	if credentials is None or credentials.scheme.lower() != "bearer":
		raise _unauthorized_exception()

	token_payload = decode_token(credentials.credentials)
	if token_payload is None:
		raise _unauthorized_exception()

	try:
		user_id = int(token_payload.sub)
	except ValueError as exc:
		raise _unauthorized_exception() from exc

	user_result = await db.execute(select(User).where(User.id == user_id))
	user = user_result.scalar_one_or_none()

	if user is None:
		raise _unauthorized_exception()

	return user


def require_role(role_name: RoleEnum | str) -> Callable[..., User]:
	required_role = _normalize_role(role_name)

	async def dependency(current_user: User = Depends(get_current_user)) -> User:
		if current_user.role == RoleEnum.ADMIN or current_user.role == required_role:
			return current_user

		raise _forbidden_exception(f"Role '{required_role.value}' is required.")

	return dependency


async def verify_course_access(
	course_id: int,
	current_user: User = Depends(get_current_user),
	db: AsyncSession = Depends(get_db),
) -> Course:
	course_result = await db.execute(select(Course).where(Course.id == course_id))
	course = course_result.scalar_one_or_none()

	if course is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Course not found.",
		)

	if current_user.role == RoleEnum.ADMIN:
		return course

	if current_user.role == RoleEnum.TEACHER and course.teacher_id == current_user.id:
		return course

	if current_user.role == RoleEnum.STUDENT:
		enrollment_result = await db.execute(
			select(course_enrollment.c.course_id).where(
				course_enrollment.c.course_id == course_id,
				course_enrollment.c.student_id == current_user.id,
			)
		)
		if enrollment_result.first() is not None:
			return course

	raise _forbidden_exception("You do not have access to this course.")
