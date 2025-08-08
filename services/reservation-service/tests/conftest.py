import pytest
import pytest_asyncio
import httpx
from httpx import ASGITransport

from app.main import app

@pytest_asyncio.fixture(scope="function")
async def client():
    """
    Provides an httpx.AsyncClient for making requests to the test app.
    """
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
