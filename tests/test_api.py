import json
import logging

from fastapi.testclient import TestClient

from delivery_api.config import Settings
from delivery_api.logging import JsonFormatter
from delivery_api.main import create_app


def client(**overrides: object) -> TestClient:
    return TestClient(create_app(Settings(**overrides)))


def test_liveness_and_request_id() -> None:
    with client() as api:
        response = api.get("/health/live", headers={"x-request-id": "test-request"})
    assert response.status_code == 200
    assert response.json() == {"status": "live"}
    assert response.headers["x-request-id"] == "test-request"


def test_readiness_success_and_failure() -> None:
    with client() as ready_api:
        assert ready_api.get("/health/ready").status_code == 200
    with client(ready=False) as unavailable_api:
        response = unavailable_api.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["detail"] == "service is not ready"


def test_version_is_release_traceable() -> None:
    with client(version="1.2.3", git_sha="abc123", environment="staging") as api:
        response = api.get("/version")
    assert response.json() == {
        "name": "delivery-api",
        "version": "1.2.3",
        "git_sha": "abc123",
        "environment": "staging",
    }


def test_quote_calculation_and_validation() -> None:
    with client() as api:
        response = api.post(
            "/quotes", json={"units": 4, "unit_price": 25.50, "discount_percent": 10}
        )
        invalid = api.post("/quotes", json={"units": 0, "unit_price": 25})
    assert response.json() == {
        "subtotal": 102.0,
        "discount": 10.2,
        "total": 91.8,
        "currency": "USD",
    }
    assert invalid.status_code == 422


def test_json_formatter_includes_context() -> None:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "hello", (), None)
    record.request_id = "request-1"  # type: ignore[attr-defined]
    payload = json.loads(JsonFormatter().format(record))
    assert payload["message"] == "hello"
    assert payload["request_id"] == "request-1"
    assert payload["level"] == "INFO"
