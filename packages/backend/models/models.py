from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    JSON,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.backend.core.database import Base


class RoleEnum(str, PyEnum):
    ADMIN = "admin"
    STUDENT = "student"
    TEACHER = "teacher"


class DifficultyLevelEnum(str, PyEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionTypeEnum(str, PyEnum):
    MULTIPLE_CHOICE = "multiple_choice"
    ESSAY = "essay"


class ProgressStatusEnum(str, PyEnum):
    UNKNOWN = "unknown"
    LEARNING = "learning"
    LEARNED = "learned"


class ChatMessageRoleEnum(str, PyEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# Association table for many-to-many relationship between courses and enrolled students
course_enrollment = Table(
    "course_enrollment",
    Base.metadata,
    Column("course_id", ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
    Column("student_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)

# Association table for concept prerequisite dependencies
concept_dependencies = Table(
    "concept_dependencies",
    Base.metadata,
    Column("concept_id", Integer, ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True),
    Column("requires_concept_id", Integer, ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True),
)


# Stores system users (admins, students, teachers) with authentication credentials
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(SQLEnum(RoleEnum, name="role_enum"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    taught_courses: Mapped[list["Course"]] = relationship(
        "Course",
        back_populates="teacher",
        foreign_keys="Course.teacher_id",
    )
    enrolled_courses: Mapped[list["Course"]] = relationship(
        secondary=course_enrollment,
        back_populates="students",
    )
    test_attempts: Mapped[list["TestAttempt"]] = relationship(
        "TestAttempt",
        back_populates="user",
        passive_deletes=True,
    )
    progress_records: Mapped[list["UserProgress"]] = relationship(
        "UserProgress",
        back_populates="user",
        passive_deletes=True,
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="user",
        passive_deletes=True,
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="user",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint("id", "role", name="uq_user_id_role"),
    )


# Stores courses with teacher ownership and enrolled students
class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    teacher_id: Mapped[int] = mapped_column(Integer, nullable=False)
    teacher_role: Mapped[RoleEnum] = mapped_column(
        SQLEnum(RoleEnum, name="role_enum"),
        default=RoleEnum.TEACHER,
        server_default=RoleEnum.TEACHER.name,
        nullable=False,
    )

    teacher: Mapped["User"] = relationship(
        "User",
        back_populates="taught_courses",
        foreign_keys="Course.teacher_id",
    )
    students: Mapped[list["User"]] = relationship(
        secondary=course_enrollment,
        back_populates="enrolled_courses",
        passive_deletes=True,
    )
    concepts: Mapped[list["Concept"]] = relationship(
        "Concept",
        back_populates="course",
        passive_deletes=True,
    )
    test_attempts: Mapped[list["TestAttempt"]] = relationship(
        "TestAttempt",
        back_populates="course",
        passive_deletes=True,
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["teacher_id", "teacher_role"],
            ["users.id", "users.role"],
            ondelete="CASCADE",
        ),
        CheckConstraint("teacher_role = 'TEACHER'", name="check_teacher_role_is_teacher"),
    )


# Stores course concepts/topics with optional dependencies on other concepts
class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    course: Mapped["Course"] = relationship("Course", back_populates="concepts")
    prerequisites: Mapped[list["Concept"]] = relationship(
        "Concept",
        secondary=concept_dependencies,
        primaryjoin=id == concept_dependencies.c.concept_id,
        secondaryjoin=id == concept_dependencies.c.requires_concept_id,
        back_populates="dependents",
        passive_deletes=True,
    )
    dependents: Mapped[list["Concept"]] = relationship(
        "Concept",
        secondary=concept_dependencies,
        primaryjoin=id == concept_dependencies.c.requires_concept_id,
        secondaryjoin=id == concept_dependencies.c.concept_id,
        back_populates="prerequisites",
        passive_deletes=True,
    )
    materials: Mapped[list["Material"]] = relationship("Material", back_populates="concept", passive_deletes=True)
    chunks: Mapped[list["MaterialChunk"]] = relationship("MaterialChunk", back_populates="concept", passive_deletes=True)
    questions: Mapped[list["Question"]] = relationship("Question", back_populates="concept", passive_deletes=True)
    progress_records: Mapped[list["UserProgress"]] = relationship(
        "UserProgress",
        back_populates="concept",
        passive_deletes=True,
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="concept",
        passive_deletes=True,
    )


# Stores materials linked to a specific concept
class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    concept_id: Mapped[int] = mapped_column(Integer, ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    content_url: Mapped[str] = mapped_column(String(255), nullable=False)
    material_type: Mapped[str] = mapped_column(String(50), nullable=False)

    concept: Mapped["Concept"] = relationship("Concept", back_populates="materials")
    chunks: Mapped[list["MaterialChunk"]] = relationship("MaterialChunk", back_populates="material", passive_deletes=True)


# Stores chunks of material content for retrieval and vectorization
class MaterialChunk(Base):
    __tablename__ = "material_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    material_id: Mapped[int] = mapped_column(Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    concept_id: Mapped[int] = mapped_column(Integer, ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)

    material: Mapped["Material"] = relationship("Material", back_populates="chunks")
    concept: Mapped["Concept"] = relationship("Concept", back_populates="chunks")


# Stores assessment questions tied to a concept
class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    concept_id: Mapped[int] = mapped_column(Integer, ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    difficulty_level: Mapped[DifficultyLevelEnum] = mapped_column(
        SQLEnum(DifficultyLevelEnum, name="difficulty_level_enum"),
        nullable=False,
    )
    type: Mapped[QuestionTypeEnum] = mapped_column(
        SQLEnum(QuestionTypeEnum, name="question_type_enum"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    concept: Mapped["Concept"] = relationship("Concept", back_populates="questions")
    attempt_responses: Mapped[list["TestAttemptResponse"]] = relationship(
        "TestAttemptResponse",
        back_populates="question",
        passive_deletes=True,
    )


# Stores a user's attempt to answer a set of course questions
class TestAttempt(Base):
    __tablename__ = "test_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="test_attempts")
    course: Mapped["Course"] = relationship("Course", back_populates="test_attempts")
    responses: Mapped[list["TestAttemptResponse"]] = relationship(
        "TestAttemptResponse",
        back_populates="test_attempt",
        passive_deletes=True,
    )


# Stores a per-question answer within a test attempt
class TestAttemptResponse(Base):
    __tablename__ = "test_attempt_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    test_attempt_id: Mapped[int] = mapped_column(Integer, ForeignKey("test_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    user_answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    question_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    test_attempt: Mapped["TestAttempt"] = relationship("TestAttempt", back_populates="responses")
    question: Mapped["Question"] = relationship("Question", back_populates="attempt_responses")

    __table_args__ = (
        UniqueConstraint("test_attempt_id", "question_id", name="uq_test_attempt_question"),
    )


# Tracks a user's mastery state for a concept
class UserProgress(Base):
    __tablename__ = "users_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    concept_id: Mapped[int] = mapped_column(Integer, ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[ProgressStatusEnum] = mapped_column(
        SQLEnum(ProgressStatusEnum, name="progress_status_enum"),
        default=ProgressStatusEnum.UNKNOWN,
        server_default=ProgressStatusEnum.UNKNOWN.name,
        nullable=False,
    )
    mastery_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="progress_records")
    concept: Mapped["Concept"] = relationship("Concept", back_populates="progress_records")

    __table_args__ = (
        UniqueConstraint("user_id", "concept_id", name="uq_user_concept_progress"),
        CheckConstraint("mastery_score >= 0 AND mastery_score <= 100", name="check_mastery_score_range"),
    )


# Stores a chat thread for a user working on a concept
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    concept_id: Mapped[int] = mapped_column(Integer, ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")
    concept: Mapped["Concept"] = relationship("Concept", back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        passive_deletes=True,
        order_by="ChatMessage.created_at",
    )


# Stores each message inside a chat session, including AI responses
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    chat_session_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    role: Mapped[ChatMessageRoleEnum] = mapped_column(
        SQLEnum(ChatMessageRoleEnum, name="chat_message_role_enum"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")
    user: Mapped["User | None"] = relationship("User", back_populates="chat_messages")

    __table_args__ = (
        CheckConstraint(
            "(role = 'USER' AND user_id IS NOT NULL) OR (role IN ('ASSISTANT', 'SYSTEM') AND user_id IS NULL)",
            name="check_chat_message_role_user_id",
        ),
    )