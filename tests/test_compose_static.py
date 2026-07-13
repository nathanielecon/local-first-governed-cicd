from __future__ import annotations

from pathlib import Path

COMPOSE_PATH = Path(__file__).resolve().parents[1] / "compose.yaml"


def _compose_text() -> str:
    return COMPOSE_PATH.read_text(encoding="utf-8")


def test_compose_declares_expected_project_and_top_level_sections() -> None:
    text = _compose_text()

    assert text.startswith("name: project-c\nservices:\n")
    assert "\nnetworks:\n  delivery:\n    name: project-c-delivery\n" in text
    assert "\nvolumes:\n  registry-data:\n  jenkins-data:\n" in text


def test_registry_contract_is_pinned_and_isolated_to_delivery_network() -> None:
    text = _compose_text()

    expected = """  registry:
    image: registry:2.8.3
    restart: unless-stopped
    ports: ["5000:5000"]
    volumes: ["registry-data:/var/lib/registry"]
    networks: [delivery]
"""
    assert expected in text


def test_staging_contract_uses_image_reference_and_deploy_profile() -> None:
    text = _compose_text()

    expected = """  staging:
    # Promotion identity is injected as an image reference and resolved to a digest at runtime.
    image: ${STAGING_IMAGE:-delivery-api:local}
    profiles: [deploy]
    restart: unless-stopped
    environment:
      APP_ENVIRONMENT: staging
      APP_READY: ${STAGING_READY:-true}
    ports: ["8081:8080"]
    networks: [delivery]
"""
    assert expected in text
    assert "STAGING_TAG" not in text
    assert "build: infra/jenkins" in text


def test_production_contract_uses_image_reference_and_deploy_profile() -> None:
    text = _compose_text()

    expected = """  production:
    # Promotion identity is injected as an image reference and resolved to a digest at runtime.
    image: ${PRODUCTION_IMAGE:-delivery-api:local}
    profiles: [deploy]
    restart: unless-stopped
    environment:
      APP_ENVIRONMENT: production
      APP_READY: ${PRODUCTION_READY:-true}
    ports: ["8082:8080"]
    networks: [delivery]
"""
    assert expected in text
    assert "PRODUCTION_TAG" not in text


def test_jenkins_contract_exposes_expected_ports_workspace_and_network() -> None:
    text = _compose_text()

    expected = (
        "  jenkins:\n"
        "    build: infra/jenkins\n"
        "    restart: unless-stopped\n"
        "    user: root\n"
        "    environment:\n"
        "      CASC_JENKINS_CONFIG: /var/jenkins_home/casc.yaml\n"
        "      JENKINS_LOCAL_ADMIN_ID: "
        "${JENKINS_LOCAL_ADMIN_ID:?Set JENKINS_LOCAL_ADMIN_ID "
        "in the local environment.}\n"
        "      JENKINS_LOCAL_ADMIN_PASSWORD: "
        "${JENKINS_LOCAL_ADMIN_PASSWORD:?Set JENKINS_LOCAL_ADMIN_PASSWORD "
        "in the local environment.}\n"
        "      JENKINS_LOCAL_APPROVER_ID: "
        "${JENKINS_LOCAL_APPROVER_ID:?Set JENKINS_LOCAL_APPROVER_ID "
        "in the local environment.}\n"
        "      JENKINS_LOCAL_APPROVER_PASSWORD: "
        "${JENKINS_LOCAL_APPROVER_PASSWORD:?Set JENKINS_LOCAL_APPROVER_PASSWORD "
        "in the local environment.}\n"
        "      JENKINS_LOCAL_VIEWER_ID: "
        "${JENKINS_LOCAL_VIEWER_ID:?Set JENKINS_LOCAL_VIEWER_ID "
        "in the local environment.}\n"
        "      JENKINS_LOCAL_VIEWER_PASSWORD: "
        "${JENKINS_LOCAL_VIEWER_PASSWORD:?Set JENKINS_LOCAL_VIEWER_PASSWORD "
        "in the local environment.}\n"
        '    ports: ["8080:8080", "50000:50000"]\n'
        "    volumes:\n"
        "      - jenkins-data:/var/jenkins_home\n"
        "      - /var/run/docker.sock:/var/run/docker.sock\n"
        "      - ./:/workspace:ro\n"
        "    networks: [delivery]\n"
    )
    assert expected in text
    assert "JENKINS_ADMIN_ID" not in text
    assert "JENKINS_ADMIN_PASSWORD" not in text
    assert "change-me-locally" not in text
    assert ":-admin" not in text
    assert ":-change-me-locally" not in text


def test_deploy_services_remain_image_reference_driven_in_source() -> None:
    text = _compose_text()

    assert "image: ${STAGING_IMAGE:-delivery-api:local}" in text
    assert "image: ${PRODUCTION_IMAGE:-delivery-api:local}" in text
    assert "tag:" not in text
