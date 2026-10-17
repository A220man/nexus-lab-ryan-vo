import pytest
import pytest_asyncio
from app.main import create_app
from httpx import ASGITransport, AsyncClient

import uuid


@pytest.fixture
def app():
    return create_app()


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_session(client):
    response = await client.post(
        "/api/sessions",
        json={
            "project": "test-project",
            "name": "Test Session",
            "description": "A test session",
            "platform_source": "claude-code",
            "platform_session_id": "abc123",
            "metadata": {"key": "value"},
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["project"] == "test-project"
    assert data["name"] == "Test Session"
    assert data["description"] == "A test session"
    assert data["status"] == "active"
    assert data["platform_source"] == "claude-code"
    assert data["platform_session_id"] == "abc123"
    assert data["metadata"] == {"key": "value"}
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_session_minimal(client):
    response = await client.post(
        "/api/sessions",
        json={"project": "minimal", "name": "Minimal Session"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["project"] == "minimal"
    assert data["name"] == "Minimal Session"
    assert data["description"] is None
    assert data["status"] == "active"
    assert data["platform_source"] is None
    assert data["metadata"] is None


@pytest.mark.asyncio
async def test_list_sessions(client):
    # Create a few sessions
    await client.post("/api/sessions", json={"project": "proj1", "name": "Session 1"})
    await client.post("/api/sessions", json={"project": "proj1", "name": "Session 2"})
    await client.post("/api/sessions", json={"project": "proj2", "name": "Session 3"})

    # List all
    response = await client.get("/api/sessions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # Filter by project
    response = await client.get("/api/sessions?project=proj1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(s["project"] == "proj1" for s in data)

    # Filter by status
    response = await client.get("/api/sessions?status=active")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # Pagination
    response = await client.get("/api/sessions?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    response = await client.get("/api/sessions?limit=2&offset=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_session(client):
    create_resp = await client.post(
        "/api/sessions", json={"project": "test", "name": "Get Test"}
    )
    session_id = create_resp.json()["id"]

    response = await client.get(f"/api/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["name"] == "Get Test"


@pytest.mark.asyncio
async def test_get_session_not_found(client):
    fake_id = str(uuid.uuid4())
    response = await client.get(f"/api/sessions/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_session(client):
    create_resp = await client.post(
        "/api/sessions", json={"project": "test", "name": "Original Name"}
    )
    session_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/sessions/{session_id}",
        json={"name": "Updated Name", "description": "New description"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "New description"
    assert data["project"] == "test"  # unchanged


@pytest.mark.asyncio
async def test_update_session_status(client):
    create_resp = await client.post(
        "/api/sessions", json={"project": "test", "name": "Status Test"}
    )
    session_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/sessions/{session_id}", json={"status": "completed"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_delete_session(client):
    create_resp = await client.post(
        "/api/sessions", json={"project": "test", "name": "Delete Test"}
    )
    session_id = create_resp.json()["id"]

    response = await client.delete(f"/api/sessions/{session_id}")
    assert response.status_code == 204

    # Verify deleted
    get_resp = await client.get(f"/api/sessions/{session_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_invalid_session_id(client):
    response = await client.get("/api/sessions/invalid-id")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_session_with_observations_cascade_delete(client):
    # Create session with observation
    create_resp = await client.post(
        "/api/sessions", json={"project": "test", "name": "Cascade Test"}
    )
    session_id = create_resp.json()["id"]

    await client.post(
        f"/api/sessions/{session_id}/observations",
        json={"title": "Test observation", "type": "feature"},
    )

    # Delete session - observations should cascade
    response = await client.delete(f"/api/sessions/{session_id}")
    assert response.status_code == 204

    # Verify observations gone
    obs_resp = await client.get(f"/api/sessions/{session_id}/observations")
    assert obs_resp.status_code == 404


class TestObservations:
    """Tests for observation CRUD operations."""

    @pytest_asyncio.fixture
    async def session_id(self, client):
        create_resp = await client.post(
            "/api/sessions", json={"project": "obs-test", "name": "Obs Session"}
        )
        return create_resp.json()["id"]

    @pytest.mark.asyncio
    async def test_create_observation(self, client, session_id):
        response = await client.post(
            f"/api/sessions/{session_id}/observations",
            json={
                "title": "Fixed bug in login",
                "type": "bugfix",
                "narrative": "The login flow had a race condition",
                "files_read": ["auth.py", "models.py"],
                "files_edited": ["auth.py"],
                "tools_used": ["Read", "Edit"],
                "metadata": {"severity": "high"},
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Fixed bug in login"
        assert data["type"] == "bugfix"
        assert data["narrative"] == "The login flow had a race condition"
        assert data["files_read"] == ["auth.py", "models.py"]
        assert data["files_edited"] == ["auth.py"]
        assert data["tools_used"] == ["Read", "Edit"]
        assert data["occurrence_count"] == 1
        assert "content_hash" in data
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_observation_dedup(self, client, session_id):
        # Create same observation twice
        obs_data = {"title": "Duplicate test", "type": "feature"}
        await client.post(f"/api/sessions/{session_id}/observations", json=obs_data)
        response = await client.post(
            f"/api/sessions/{session_id}/observations", json=obs_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["occurrence_count"] == 2

    @pytest.mark.asyncio
    async def test_list_observations(self, client, session_id):
        await client.post(
            f"/api/sessions/{session_id}/observations", json={"title": "Obs 1", "type": "bugfix"}
        )
        await client.post(
            f"/api/sessions/{session_id}/observations", json={"title": "Obs 2", "type": "feature"}
        )
        await client.post(
            f"/api/sessions/{session_id}/observations", json={"title": "Obs 3", "type": "refactor"}
        )

        response = await client.get(f"/api/sessions/{session_id}/observations")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # Filter by type
        response = await client.get(f"/api/sessions/{session_id}/observations?obs_type=bugfix")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["type"] == "bugfix"

    @pytest.mark.asyncio
    async def test_search_observations(self, client, session_id):
        await client.post(
            f"/api/sessions/{session_id}/observations",
            json={"title": "Fixed login bug", "type": "bugfix"},
        )
        await client.post(
            f"/api/sessions/{session_id}/observations",
            json={"title": "Added new feature", "type": "feature"},
        )

        # Search by query
        response = await client.get("/api/observations/search?q=login")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "login" in data[0]["title"].lower()

        # Search by project
        response = await client.get("/api/observations/search?project=obs-test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Search by type
        response = await client.get("/api/observations/search?obs_type=bugfix")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["type"] == "bugfix"

    @pytest.mark.asyncio
    async def test_bulk_import_observations(self, client, session_id):
        observations = [
            {"title": "Bulk 1", "type": "verification"},
            {"title": "Bulk 2", "type": "investigation"},
            {"title": "Bulk 3", "type": "neutral"},
        ]
        response = await client.post(
            f"/api/observations/bulk-import?session_id={session_id}",
            json=observations,
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_delete_observation(self, client, session_id):
        create_resp = await client.post(
            f"/api/sessions/{session_id}/observations",
            json={"title": "To delete", "type": "bugfix"},
        )
        obs_id = create_resp.json()["id"]

        response = await client.delete(f"/api/observations/{obs_id}")
        assert response.status_code == 204

        # Verify deleted
        get_resp = await client.get(f"/api/observations/{obs_id}")
        assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_session_summary_relationship(client):
    """Test that session summaries can be queried through relationships."""
    from app.core.database import get_session
    from app.models.session import SessionSummary, SummaryFormat

    create_resp = await client.post(
        "/api/sessions", json={"project": "summary-test", "name": "Summary Session"}
    )
    session_id = create_resp.json()["id"]

    # Manually add a summary to test relationship loading
    async for db in get_session():
        from sqlalchemy import select
        from app.models.session import Session

        session = (await db.execute(select(Session).where(Session.id == uuid.UUID(session_id)))).scalar_one()
        summary = SessionSummary(
            session_id=session.id,
            format=SummaryFormat.MARKDOWN,
            content="# Session Summary\n\nWork was done.",
            files_read=["file1.py"],
            files_edited=["file2.py"],
        )
        db.add(summary)
        await db.commit()
        break

    # Verify through API would require a summary endpoint (future feature)
    # For now just verify the relationship works at model level
    async for db in get_session():
        from sqlalchemy import select
        from app.models.session import Session

        session = (await db.execute(select(Session).where(Session.id == uuid.UUID(session_id)))).scalar_one()
        await db.refresh(session, ["summaries"])
        assert len(session.summaries) == 1
        assert session.summaries[0].content == "# Session Summary\n\nWork was done."
        break