from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

import structlog
from app.core.database import get_session
from app.models.session import Session, SessionStatus
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class SessionCreate(BaseModel):
    project: str = Field(..., max_length=255)
    name: str = Field(..., max_length=500)
    description: str | None = None
    platform_source: str | None = None
    platform_session_id: str | None = None
    metadata: dict | None = None


class SessionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: SessionStatus | None = None
    metadata: dict | None = None


class SessionRead(BaseModel):
    id: uuid.UUID
    project: str
    name: str
    description: str | None = None
    status: SessionStatus
    platform_source: str | None = None
    platform_session_id: str | None = None
    metadata: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionService:
    """Service for managing session lifecycle and queries."""

    @staticmethod
    async def create(db: AsyncSession, data: SessionCreate) -> Session:
        session = Session(
            project=data.project,
            name=data.name,
            description=data.description,
            status=SessionStatus.ACTIVE,
            platform_source=data.platform_source,
            platform_session_id=data.platform_session_id,
            metadata_json=json.dumps(data.metadata) if data.metadata else None,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        logger.info("session_created", session_id=str(session.id), project=data.project)
        return session

    @staticmethod
    async def get(db: AsyncSession, session_id: uuid.UUID) -> Session | None:
        result = await db.execute(select(Session).where(Session.id == session_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_404(db: AsyncSession, session_id: uuid.UUID) -> Session:
        session = await SessionService.get(db, session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return session

    @staticmethod
    async def list(
        db: AsyncSession,
        project: str | None = None,
        status: SessionStatus | None = None,
        platform_source: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Session]:
        stmt = select(Session)
        if project:
            stmt = stmt.where(Session.project == project)
        if status:
            stmt = stmt.where(Session.status == status)
        if platform_source:
            stmt = stmt.where(Session.platform_source == platform_source)
        stmt = stmt.order_by(Session.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def update(
        db: AsyncSession, session_id: uuid.UUID, data: SessionUpdate
    ) -> Session:
        session = await SessionService.get_or_404(db, session_id)
        update_data = data.model_dump(exclude_unset=True)
        if "metadata" in update_data and update_data["metadata"] is not None:
            session.metadata_json = json.dumps(update_data.pop("metadata"))
            update_data.pop("metadata", None)
        for key, value in update_data.items():
            setattr(session, key, value)
        if not update_data:
            return session
        await db.commit()
        await db.refresh(session)
        return session
    @staticmethod
    async def delete(db: AsyncSession, session_id: uuid.UUID) -> None:
        session = await SessionService.get_or_404(db, session_id)
        await db.delete(session)
        await db.commit()
        logger.info("session_deleted", session_id=str(session_id))

    @staticmethod
    def _session_to_read(session: Session) -> SessionRead:
        metadata = json.loads(session.metadata_json) if session.metadata_json else None
        return SessionRead(
            id=session.id,
            project=session.project,
            name=session.name,
            description=session.description,
            status=session.status,
            platform_source=session.platform_source,
            platform_session_id=session.platform_session_id,
            metadata=metadata,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )


def get_session_service(db: AsyncSession = Depends(get_session)) -> SessionService:
    return SessionService()
