import pytest
from httpx import AsyncClient

from app.config import settings


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test the /health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Application is running normally."}


@pytest.mark.asyncio
async def test_get_version(client: AsyncClient):
    """Test the /version endpoint."""
    response = await client.get("/version")
    assert response.status_code == 200
    assert response.json()["app_name"] == settings.APP_NAME
    assert response.json()["version"] == settings.APP_VERSION
