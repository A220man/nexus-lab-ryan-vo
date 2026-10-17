import uuid
from datetime import UTC, datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.observation import Observation
    from app.models.summary import SessionSummary


class SessionStatus(PyEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class Session(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sessions"

    project: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, native_enum=False),
        default=SessionStatus.ACTIVE,
        nullable=False,
    )
    platform_source: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    platform_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    observations: Mapped[list["Observation"]] = relationship(
        "Observation",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    summaries: Mapped[list["SessionSummary"]] = relationship(
        "SessionSummary",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_sessions_project_status", "project", "status"),
        Index("ix_sessions_platform", "platform_source", "platform_session_id"),
    )


class ObservationType(PyEnum):
    BUGFIX = "bugfix"
    FEATURE = "feature"
    REFACTOR = "refactor"
    VERIFICATION = "verification"
    INVESTIGATION = "investigation"
    NEUTRAL = "neutral"


class Observation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "observations"

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[ObservationType] = mapped_column(
        Enum(ObservationType, native_enum=False),
        default=ObservationType.NEUTRAL,
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    narrative: Mapped[str | None] = mapped_column(Text, nullable=True)
    files_read: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    files_edited: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    tools_used: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    occurrence_count: Mapped[int] = mapped_column(default=1, nullable=False)
    raw_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    session: Mapped["Session"] = relationship("Session", back_populates="observations")

    __table_args__ = (
        Index("ix_observations_session_type", "session_id", "type"),
    )


class SummaryFormat(PyEnum):
    MARKDOWN = "markdown"
    PLAIN = "plain"
    JSON = "json"


class SessionSummary(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "session_summaries"

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    format: Mapped[SummaryFormat] = mapped_column(
        Enum(SummaryFormat, native_enum=False),
        default=SummaryFormat.MARKDOWN,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    files_read: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    files_edited: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    relevance_count: Mapped[int] = mapped_column(default=0, nullable=False)
    discovery_tokens: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    session: Mapped["Session"] = relationship("Session", back_populates="summaries")

    __table_args__ = (
        Index("ix_session_summaries_session_format", "session_id", "format"),
    )