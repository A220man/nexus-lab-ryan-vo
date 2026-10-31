from app.core.database import get_session as get_db
from app.core.security import get_current_user, require_role, TokenData
from app.models.session import Session, SessionStatus
from app.services.session_service import (
    SessionCreate,
    SessionRead,
    SessionService,
    SessionUpdate,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    session = await SessionService.create(db, data)
    return SessionService._session_to_read(session)


@router.get("", response_model=list[SessionRead])
async def list_sessions(
    project: str | None = Query(default=None, max_length=255),
    status: SessionStatus | None = Query(default=None),
    platform_source: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    sessions = await SessionService.list(
        db,
        project=project,
        status=status,
        platform_source=platform_source,
        limit=limit,
        offset=offset,
    )
    return [SessionService._session_to_read(s) for s in sessions]


@router.get("/{session_id}", response_model=SessionRead)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    import uuid

    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID"
        )
    session = await SessionService.get_or_404(db, sid)
    return SessionService._session_to_read(session)


@router.patch("/{session_id}", response_model=SessionRead)
async def update_session(
    session_id: str,
    data: SessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    import uuid

    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID"
        )
    session = await SessionService.update(db, sid, data)
    return SessionService._session_to_read(session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(require_role("operator")),
):
    import uuid

    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID"
        )
    await SessionService.delete(db, sid)
    return None
