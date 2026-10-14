import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
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
    assert data["version"] == "1.0.0"
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
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_cors_headers(client):
    response = await client.options(
        "/api/health",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers