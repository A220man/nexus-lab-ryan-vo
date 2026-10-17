from app.core.database import get_session
from app.models.session import Observation, ObservationType
from app.services.observation_service import (
    ObservationCreate,
    ObservationService,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["observations"])


@router.post("/sessions/{session_id}/observations", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_observation(
    session_id: str,
    data: ObservationCreate,
    db: AsyncSession = Depends(get_session),
):
    import uuid

    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID"
        )
    obs = await ObservationService.create(db, sid, data)
    read = ObservationService._obs_to_read(obs)
    return read.model_dump()


@router.get("/sessions/{session_id}/observations", response_model=list[dict])
async def list_observations(
    session_id: str,
    obs_type: ObservationType | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_session),
):
    import uuid

    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID"
        )
    from app.services.session_service import SessionService
    await SessionService.get_or_404(db, sid)
    observations = await ObservationService.list(db, sid, obs_type=obs_type, limit=limit, offset=offset)
    return [ObservationService._obs_to_read(o).model_dump() for o in observations]


@router.get("/observations/search", response_model=list[dict])
async def search_observations(
    project: str | None = Query(default=None, max_length=255),
    q: str | None = Query(default=None, max_length=200),
    obs_type: ObservationType | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_session),
):
    """Search observations by project, title keyword, or type."""
    from sqlalchemy import func, select

    import uuid

    stmt = (
        select(Observation)
        .join(Session, Observation.session_id == Session.id)
        .where(Observation.session_id == Session.id)
    )
    if project:
        stmt = stmt.where(Session.project == project)
    if q:
        stmt = stmt.where(func.lower(Observation.title).like(f"%{q.lower()}%"))
    if obs_type:
        stmt = stmt.where(Observation.type == obs_type)
    stmt = stmt.order_by(Observation.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    observations = result.scalars().all()
    return [ObservationService._obs_to_read(o).model_dump() for o in observations]


@router.get("/observations/{observation_id}", response_model=dict)
async def get_observation(
    observation_id: str,
    db: AsyncSession = Depends(get_session),
):
    import uuid

    try:
        oid = uuid.UUID(observation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid observation ID"
        )
    obs = await ObservationService.get_or_404(db, oid)
    return ObservationService._obs_to_read(obs).model_dump()


@router.post("/observations/bulk-import", response_model=list[dict], status_code=status.HTTP_201_CREATED)
async def bulk_import_observations(
    session_id: str = Query(...),
    observations: list[ObservationCreate] = ...,
    db: AsyncSession = Depends(get_session),
):
    import uuid

    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID"
        )
    created = await ObservationService.bulk_create(db, sid, observations)
    return [ObservationService._obs_to_read(o).model_dump() for o in created]


@router.delete("/observations/{observation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_observation(
    observation_id: str,
    db: AsyncSession = Depends(get_session),
):
    import uuid

    try:
        oid = uuid.UUID(observation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid observation ID"
        )
    await ObservationService.delete(db, oid)
    return None


# Import after use to avoid circular import
from app.models.session import Session  # noqa: E402
