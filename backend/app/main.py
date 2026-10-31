from contextlib import asynccontextmanager

import structlog
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.observations import router as observations_router
from app.api.sessions import router as sessions_router
from app.core.config import get_settings
from app.core.database import close_db, init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application_starting", version=settings.version)
    await init_db()
    logger.info("application_started")
    yield
    logger.info("application_shutting_down")
    await close_db()
    logger.info("application_stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="Persistent Context Across Sessions for Every Agent",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.demo_mode else None,
        redoc_url="/api/redoc" if settings.demo_mode else None,
        openapi_url="/api/openapi.json" if settings.demo_mode else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(auth_router, prefix="/api")
    app.include_router(health_router, prefix="/api")
    app.include_router(sessions_router, prefix="/api")
    app.include_router(observations_router, prefix="/api")

    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.version,
            "docs": "/api/docs" if settings.demo_mode else "disabled",
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.demo_mode,
        log_level=settings.log_level.lower(),
    )
