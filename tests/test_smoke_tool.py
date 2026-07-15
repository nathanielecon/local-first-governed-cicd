import http.client
import json
import urllib.error

import pytest
from scripts import smoke_test


class FakeResponse:
    def __init__(self, status: int, payload: object) -> None:
        self.status = status
        self._payload = json.dumps(payload).encode()

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = len(self._payload)
        data = self._payload[:size]
        self._payload = self._payload[size:]
        return data

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
        return False

    def close(self) -> None:
        return None


def _ok_responses() -> dict[str, FakeResponse]:
    return {
        "http://example.test/health/live": FakeResponse(200, {"status": "live"}),
        "http://example.test/health/ready": FakeResponse(200, {"status": "ready"}),
        "http://example.test/version": FakeResponse(
            200,
            {
                "name": "delivery-api",
                "version": "1.2.3",
                "git_sha": "abc123",
                "environment": "staging",
            },
        ),
        "http://example.test/quotes": FakeResponse(
            200,
            {"subtotal": 20.0, "discount": 1.0, "total": 19.0, "currency": "USD"},
        ),
    }


def test_main_passes_when_contract_matches(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    responses = _ok_responses()

    def fake_urlopen(target: str | object, timeout: int = 5) -> FakeResponse:
        url = getattr(target, "full_url", target)
        assert timeout == 5
        return responses[url]

    monkeypatch.setattr(smoke_test.urllib.request, "urlopen", fake_urlopen)

    result = smoke_test.main(
        [
            "--base-url",
            "http://example.test",
            "--expected-sha",
            "abc123",
            "--expected-environment",
            "staging",
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["failures"] == []
    assert payload["checks"] == {
        "health": "pass",
        "version": "pass",
        "business_behavior": "pass",
    }
    assert payload["statuses"] == {
        "live": 200,
        "ready": 200,
        "version": 200,
        "quote": 200,
    }


def test_main_reports_release_identity_and_expected_sha_failures(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    responses = {
        "http://example.test/health/live": FakeResponse(200, {"status": "live"}),
        "http://example.test/health/ready": FakeResponse(200, {"status": "ready"}),
        "http://example.test/version": FakeResponse(
            200,
            {"name": "wrong-name", "version": "", "git_sha": "def456", "environment": None},
        ),
        "http://example.test/quotes": FakeResponse(
            200,
            {"subtotal": 20.0, "discount": 1.0, "total": 19.0, "currency": "USD"},
        ),
    }

    def fake_urlopen(target: str | object, timeout: int = 5) -> FakeResponse:
        url = getattr(target, "full_url", target)
        assert timeout == 5
        return responses[url]

    monkeypatch.setattr(smoke_test.urllib.request, "urlopen", fake_urlopen)

    result = smoke_test.main(["--base-url", "http://example.test", "--expected-sha", "abc123"])

    assert result == 1
    payload = json.loads(capsys.readouterr().out)
    assert "version name failed: 'wrong-name'" in payload["failures"]
    assert "version field version failed: ''" in payload["failures"]
    assert "version field environment failed: None" in payload["failures"]
    assert "expected SHA abc123, got def456" in payload["failures"]
    assert payload["checks"]["version"] == "fail"


def test_main_reports_not_ready_and_http_errors(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    errors = {
        "http://example.test/health/live": urllib.error.HTTPError(
            "http://example.test/health/live",
            500,
            "Internal Server Error",
            hdrs=None,
            fp=FakeResponse(500, {"detail": "boom-live"}),
        ),
        "http://example.test/health/ready": urllib.error.HTTPError(
            "http://example.test/health/ready",
            503,
            "Service Unavailable",
            hdrs=None,
            fp=FakeResponse(503, {"detail": "service is not ready"}),
        ),
        "http://example.test/version": urllib.error.HTTPError(
            "http://example.test/version",
            500,
            "Internal Server Error",
            hdrs=None,
            fp=FakeResponse(500, {"detail": "boom"}),
        ),
    }
    quote_response = FakeResponse(200, {"total": 19.0})

    def fake_urlopen(target: str | object, timeout: int = 5) -> FakeResponse:
        url = getattr(target, "full_url", target)
        assert timeout == 5
        if url in errors:
            raise errors[url]
        return quote_response

    monkeypatch.setattr(smoke_test.urllib.request, "urlopen", fake_urlopen)

    result = smoke_test.main(["--base-url", "http://example.test"])

    assert result == 1
    payload = json.loads(capsys.readouterr().out)
    assert "liveness failed: 500 {'detail': 'boom-live'}" in payload["failures"]
    assert "readiness failed: 503 {'detail': 'service is not ready'}" in payload["failures"]
    assert "readiness error: HTTP Error 503: Service Unavailable" in payload["failures"]
    assert "version failed: 500" in payload["failures"]
    assert "version error: HTTP Error 500: Internal Server Error" in payload["failures"]
    assert payload["checks"]["health"] == "fail"
    assert payload["statuses"] == {"live": 500, "ready": 503, "version": 500, "quote": 200}


def test_main_reports_connection_failure_for_quote_request(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    responses = {
        "http://example.test/health/live": FakeResponse(200, {"status": "live"}),
        "http://example.test/health/ready": FakeResponse(200, {"status": "ready"}),
        "http://example.test/version": FakeResponse(
            200,
            {
                "name": "delivery-api",
                "version": "1.2.3",
                "git_sha": "abc123",
                "environment": "staging",
            },
        ),
    }

    def fake_urlopen(target: str | object, timeout: int = 5) -> FakeResponse:
        url = getattr(target, "full_url", target)
        assert timeout == 5
        if url == "http://example.test/quotes":
            raise urllib.error.URLError("connection refused")
        return responses[url]

    monkeypatch.setattr(smoke_test.urllib.request, "urlopen", fake_urlopen)

    result = smoke_test.main(["--base-url", "http://example.test"])

    assert result == 1
    payload = json.loads(capsys.readouterr().out)
    assert "quote failed: None" in payload["failures"]
    assert "quote error: connection refused" in payload["failures"]
    assert "quote contract failed: None" in payload["failures"]
    assert payload["checks"]["business_behavior"] == "fail"
    assert payload["statuses"] == {"live": 200, "ready": 200, "version": 200, "quote": None}


def test_main_reports_remote_disconnect_without_traceback(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    responses = {
        "http://example.test/health/live": FakeResponse(200, {"status": "live"}),
        "http://example.test/version": FakeResponse(
            200,
            {
                "name": "delivery-api",
                "version": "1.2.3",
                "git_sha": "abc123",
                "environment": "staging",
            },
        ),
        "http://example.test/quotes": FakeResponse(
            200,
            {"subtotal": 20.0, "discount": 1.0, "total": 19.0, "currency": "USD"},
        ),
    }

    def fake_urlopen(target: str | object, timeout: int = 5) -> FakeResponse:
        url = getattr(target, "full_url", target)
        assert timeout == 5
        if url == "http://example.test/health/ready":
            raise http.client.RemoteDisconnected("Remote end closed connection without response")
        return responses[url]

    monkeypatch.setattr(smoke_test.urllib.request, "urlopen", fake_urlopen)

    result = smoke_test.main(["--base-url", "http://example.test"])

    assert result == 1
    payload = json.loads(capsys.readouterr().out)
    assert "readiness failed: None None" in payload["failures"]
    assert "readiness error: Remote end closed connection without response" in payload["failures"]
    assert payload["statuses"] == {"live": 200, "ready": None, "version": 200, "quote": 200}


def test_main_reports_expected_environment_mismatch(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    responses = _ok_responses()

    def fake_urlopen(target: str | object, timeout: int = 5) -> FakeResponse:
        url = getattr(target, "full_url", target)
        return responses[url]

    monkeypatch.setattr(smoke_test.urllib.request, "urlopen", fake_urlopen)
    result = smoke_test.main(
        ["--base-url", "http://example.test", "--expected-environment", "production"]
    )
    assert result == 1
    payload = json.loads(capsys.readouterr().out)
    assert "expected environment production, got staging" in payload["failures"]
