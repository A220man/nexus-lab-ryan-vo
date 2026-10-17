import pytest
import pytest_asyncio
from app.core.config import get_settings
from app.main import create_app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def app():
    return create_app()


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    settings = get_settings()
    assert data["version"] == settings.version
    assert data["app_name"] == "nexus-lab-ryan-vo"
    assert data["database"] in ("ok", "failed")


@pytest.mark.asyncio
async def test_readiness_endpoint(client):
    response = await client.get("/api/readiness")
    assert response.status_code in (200, 503)
    data = response.json()
    assert data["status"] in ("ready", "not_ready")


@pytest.mark.asyncio
async def test_root_endpoint(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "nexus-lab-ryan-vo"
    settings = get_settings()
    assert data["version"] == settings.version


@pytest.mark.asyncio
async def test_cors_headers(client):
    response = await client.options(
        "/api/health",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
