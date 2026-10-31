from app.core.database import get_session
from app.core.security import get_current_user, require_role, TokenData
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
    current_user: TokenData = Depends(get_current_user),
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
    type: ObservationType | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_session),
    current_user: TokenData = Depends(get_current_user),
):
    import uuid

    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID"
        )
    observations = await ObservationService.list(db, sid, type=type, limit=limit, offset=offset)
    return [ObservationService._obs_to_read(o).model_dump() for o in observations]


@router.get("/observations/search", response_model=list[dict])
async def search_observations(
    project: str | None = Query(default=None, max_length=255),
    q: str | None = Query(default=None, min_length=1, max_length=500),
    type: ObservationType | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_session),
    current_user: TokenData = Depends(get_current_user),
):
    """Search observations by project, title keyword, or type."""
    if not q and not project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Query or project required"
        )
    observations = await ObservationService.search(
        db, query=q, project=project, type=type, limit=limit, offset=offset
    )
    return [ObservationService._obs_to_read(o).model_dump() for o in observations]


@router.get("/observations/{observation_id}", response_model=dict)
async def get_observation(
    observation_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: TokenData = Depends(get_current_user),
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
    session_id: str,
    items: list[ObservationCreate],
    db: AsyncSession = Depends(get_session),
    current_user: TokenData = Depends(require_role("operator")),
):
    import uuid

    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID"
        )
    created = await ObservationService.bulk_create(db, sid, items)
    return [ObservationService._obs_to_read(o).model_dump() for o in created]


@router.delete("/observations/{observation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_observation(
    observation_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: TokenData = Depends(require_role("operator")),
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
