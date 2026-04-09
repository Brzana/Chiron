from pydantic import BaseModel

from packages.backend.schemas.auth import UserResponse


class CourseResponse(BaseModel):
    id: int
    title: str
    description: str | None
    is_published: bool
    teacher: UserResponse

    model_config = {"from_attributes": True}


class CourseCreateRequest(BaseModel):
    title: str
    description: str | None = None
    is_published: bool = False


class CourseUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    is_published: bool | None = None
