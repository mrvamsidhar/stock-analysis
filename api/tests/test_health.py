"""Tests for the /health endpoint."""


async def test_health_returns_200_when_db_reachable(client):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "reachable"


async def test_root_endpoint_returns_service_info(client):
    response = await client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "stock-analysis-api"