import httpx

from devlens.config.settings import get_settings
from devlens.interface.api.app import create_app


async def test_allowed_origin_gets_cors_header_echoed_back() -> None:
    get_settings.cache_clear()
    try:
        app = create_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/health", headers={"Origin": "http://localhost:5173"}
            )

        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    finally:
        get_settings.cache_clear()


async def test_disallowed_origin_gets_no_cors_header() -> None:
    get_settings.cache_clear()
    try:
        app = create_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/health", headers={"Origin": "http://evil.invalid"}
            )

        assert "access-control-allow-origin" not in response.headers
    finally:
        get_settings.cache_clear()
