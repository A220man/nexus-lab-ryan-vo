from __future__ import annotations

import hashlib
import json
import uuid

import structlog
from app.core.database import get_session
from app.models.session import Observation, ObservationType
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ObservationCreate(BaseModel):
    type: ObservationType = ObservationType.NEUTRAL
    title: str = Field(..., max_length=500)
    narrative: str | None = None
    files_read: list[str] | None = None
    files_edited: list[str] | None = None
    tools_used: list[str] | None = None
    raw_output: str | None = None
    metadata: dict | None = None


class ObservationRead(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    type: ObservationType
    title: str
    narrative: str | None = None
    files_read: list[str] | None = None
    files_edited: list[str] | None = None
    tools_used: list[str] | None = None
    content_hash: str
    occurrence_count: int
    raw_output: str | None = None
    metadata: dict | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ObservationService:
    """Service for managing observations within sessions."""

    @staticmethod
    def _compute_hash(title: str, narrative: str | None) -> str:
        raw = f"{title}\n{narrative or ''}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _serialize_list(items: list[str] | None) -> list[str] | None:
        # With JSON column type, no serialization needed
        return items

    @staticmethod
    def _deserialize_list(val: list[str] | None) -> list[str] | None:
        # With JSON column type, no deserialization needed
        return val
    @staticmethod
    async def create(
        db: AsyncSession, session_id: uuid.UUID, data: ObservationCreate
    ) -> Observation:
        content_hash = ObservationService._compute_hash(data.title, data.narrative)

        # Check for near-duplicate by title (normalized)
        exact = await db.execute(
            select(Observation).where(
                Observation.session_id == session_id,
                Observation.content_hash == content_hash,
            )
        )
        existing = exact.scalar_one_or_none()
        if existing:
            existing.occurrence_count += 1
            await db.commit()
            await db.refresh(existing)
            logger.info(
                "observation_dedup",
                session_id=str(session_id),
                title=data.title[:80],
                occurrence_count=existing.occurrence_count,
            )
            return existing

        obs = Observation(
            session_id=session_id,
            type=data.type,
            title=data.title,
            narrative=data.narrative,
            files_read=ObservationService._serialize_list(data.files_read),
            files_edited=ObservationService._serialize_list(data.files_edited),
            tools_used=ObservationService._serialize_list(data.tools_used),
            content_hash=content_hash,
            occurrence_count=1,
            raw_output=data.raw_output,
            metadata_json=json.dumps(data.metadata) if data.metadata else None,
        )
        db.add(obs)
        await db.commit()
        await db.refresh(obs)
        logger.info(
            "observation_created",
            session_id=str(session_id),
            observation_id=str(obs.id),
            type=data.type.value,
        )
        return obs

    @staticmethod
    async def list(
        db: AsyncSession,
        session_id: uuid.UUID,
        obs_type: ObservationType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Observation]:
        stmt = select(Observation).where(Observation.session_id == session_id)
        if obs_type:
            stmt = stmt.where(Observation.type == obs_type)
        stmt = stmt.order_by(Observation.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get(db: AsyncSession, observation_id: uuid.UUID) -> Observation | None:
        result = await db.execute(select(Observation).where(Observation.id == observation_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_404(db: AsyncSession, observation_id: uuid.UUID) -> Observation:
        obs = await ObservationService.get(db, observation_id)
        if not obs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found"
            )
        return obs

    @staticmethod
    async def delete(db: AsyncSession, observation_id: uuid.UUID) -> None:
        obs = await ObservationService.get_or_404(db, observation_id)
        await db.delete(obs)
        await db.commit()
        logger.info("observation_deleted", observation_id=str(observation_id))

    @staticmethod
    async def bulk_create(
        db: AsyncSession, session_id: uuid.UUID, observations: list[ObservationCreate]
    ) -> list[Observation]:
        created: list[Observation] = []
        for obs_data in observations:
            obs = await ObservationService.create(db, session_id, obs_data)
            created.append(obs)
        return created

    @staticmethod
    def _obs_to_read(obs: Observation) -> ObservationRead:
        return ObservationRead(
            id=obs.id,
            session_id=obs.session_id,
            type=obs.type,
            title=obs.title,
            narrative=obs.narrative,
            files_read=ObservationService._deserialize_list(obs.files_read),
            files_edited=ObservationService._deserialize_list(obs.files_edited),
            tools_used=ObservationService._deserialize_list(obs.tools_used),
            content_hash=obs.content_hash,
            occurrence_count=obs.occurrence_count,
            raw_output=obs.raw_output,
            metadata=json.loads(obs.metadata_json) if obs.metadata_json else None,
            created_at=obs.created_at.isoformat() if obs.created_at else None,
            updated_at=obs.updated_at.isoformat() if obs.updated_at else None,
        )


def get_observation_service(db: AsyncSession = Depends(get_session)) -> ObservationService:
    return ObservationService()
