import httpx
import structlog
from app.core.config import get_settings
from app.core.database import get_session
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()
router = APIRouter(tags=["health"])
settings = get_settings()


class HealthResponse(BaseModel):
    status: str
    version: str
    app_name: str
    database: str
    chroma: str | None = None
    keycloak: str | None = None


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_session)):
    """Health check endpoint for service monitoring."""
    db_status = "ok"
    chroma_status = None
    keycloak_status = None

    # Check database
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error("health_check_db_failed", error=str(e))
        db_status = "failed"

    # Check ChromaDB (optional)
    if settings.chroma_url:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{settings.chroma_url.rstrip('/')}/api/v1/heartbeat")
                chroma_status = "ok" if resp.status_code == 200 else "degraded"
        except Exception as e:
            logger.warning("health_check_chroma_failed", error=str(e))
            chroma_status = "unavailable"

    # Check Keycloak (optional)
    if settings.keycloak_url:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{settings.keycloak_url.rstrip('/')}/health/ready")
                keycloak_status = "ok" if resp.status_code == 200 else "degraded"
        except Exception as e:
            logger.warning("health_check_keycloak_failed", error=str(e))
            keycloak_status = "unavailable"

    overall_status = "ok" if db_status == "ok" else "degraded"

    return HealthResponse(
        status=overall_status,
        version=settings.version,
        app_name=settings.app_name,
        database=db_status,
        chroma=chroma_status,
        keycloak=keycloak_status,
    )


@router.get("/readiness")
async def readiness_check(db: AsyncSession = Depends(get_session), response: Response = None):
    """Readiness check for Kubernetes/load balancer."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        if response:
            response.status_code = 503
        return {"status": "not_ready", "error": str(e)}
