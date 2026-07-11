from __future__ import annotations

import re
from pathlib import Path

DOCKERFILE = Path(__file__).resolve().parents[1] / "Dockerfile"


def _instructions() -> list[str]:
    merged: list[str] = []
    current = ""
    for raw_line in DOCKERFILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith("\\"):
            current += f"{line[:-1].rstrip()} "
            continue
        merged.append(f"{current}{line}".strip())
        current = ""
    if current:
        merged.append(current.strip())
    return merged


def _instruction(prefix: str) -> str:
    for entry in _instructions():
        if entry.startswith(prefix):
            return entry
    raise AssertionError(f"missing Dockerfile instruction starting with {prefix!r}")


def _instructions_by_prefix(prefix: str) -> list[str]:
    return [entry for entry in _instructions() if entry.startswith(prefix)]


def test_uses_pinned_multi_stage_python_images() -> None:
    from_lines = [line for line in _instructions() if line.startswith("FROM ")]
    assert from_lines == [
        "FROM python:3.12.11-slim-bookworm AS builder",
        "FROM python:3.12.11-slim-bookworm AS runtime",
    ]


def test_builder_stage_creates_wheels_for_runtime_install() -> None:
    instructions = _instructions()
    assert "WORKDIR /build" in instructions
    assert "COPY pyproject.toml ./" in instructions
    assert "COPY src ./src" in instructions
    assert "RUN python -m pip wheel --wheel-dir /wheels ." in instructions
    assert "COPY --from=builder /wheels /wheels" in instructions
    assert (
        "RUN python -m pip install --no-cache-dir /wheels/* && rm -rf /wheels" in instructions
    )


def test_runtime_release_identity_is_exposed_via_oci_labels_and_env() -> None:
    labels = _instruction("LABEL ")
    assert 'org.opencontainers.image.title="delivery-api"' in labels
    assert 'org.opencontainers.image.description="Governed delivery API runtime image"' in labels
    assert 'org.opencontainers.image.version="$APP_VERSION"' in labels
    assert 'org.opencontainers.image.revision="$GIT_SHA"' in labels

    env = _instructions_by_prefix("ENV ")[1]
    for expected in (
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONUNBUFFERED=1",
        "APP_VERSION=$APP_VERSION",
        "APP_GIT_SHA=$GIT_SHA",
    ):
        assert expected in env


def test_runtime_stage_uses_dedicated_non_root_identity() -> None:
    run_line = _instruction("RUN groupadd")
    assert "--gid 10001 app" in run_line
    assert "--uid 10001 --gid app app" in run_line
    assert _instruction("USER ") == "USER 10001:10001"


def test_healthcheck_targets_readiness_endpoint_with_expected_policy() -> None:
    healthcheck = _instruction("HEALTHCHECK ")
    for expected in (
        "--interval=10s",
        "--timeout=3s",
        "--start-period=5s",
        "--retries=3",
        "urllib.request.urlopen('http://127.0.0.1:8080/health/ready', timeout=2)",
    ):
        assert expected in healthcheck


def test_runtime_shutdown_and_entrypoint_contract() -> None:
    assert _instruction("STOPSIGNAL ") == "STOPSIGNAL SIGTERM"
    assert _instruction("EXPOSE ") == "EXPOSE 8080"

    cmd = _instruction("CMD ")
    assert cmd == (
        'CMD ["uvicorn", "delivery_api.main:app", "--host", "0.0.0.0", "--port", "8080"]'
    )
    assert not re.search(r"\broot\b", cmd, re.IGNORECASE)
