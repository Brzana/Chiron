from sqlalchemy import CheckConstraint, Column, ForeignKeyConstraint, Integer, String, ForeignKey, Table, Text, Enum, Boolean, ARRAY, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.db import Base

class RoleEnum(str, Enum):
    ADMIN = "admin"
    STUDENT = "student"
    TEACHER = "teacher"

course_enrollment = Table(
    "course_enrollment",
    Base.metadata,
    Column("course_id", ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
    Column("student_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False)

    __table_args__ = (
        UniqueConstraint('id', 'role', name='uq_user_id_role'),
    )

class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    teacher_id: Mapped[int] = mapped_column(Integer, nullable=False)
    teacher_role: Mapped[RoleEnum] = mapped_column(
        Enum(RoleEnum), 
        default=RoleEnum.TEACHER, 
        server_default="TEACHER",
        nullable=False
    )

    students: Mapped[list["User"]] = relationship(
        secondary=course_enrollment,
        passive_deletes=True
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["teacher_id", "teacher_role"],
            ["users.id", "users.role"],
            ondelete="CASCADE"
        ),
        CheckConstraint("teacher_role = 'TEACHER'", name="check_teacher_role_is_teacher"),
    )