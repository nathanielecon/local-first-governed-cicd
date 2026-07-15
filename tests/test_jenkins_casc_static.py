from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE_PATH = REPO_ROOT / "infra" / "jenkins" / "Dockerfile"
PLUGINS_PATH = REPO_ROOT / "infra" / "jenkins" / "plugins.txt"
CASC_PATH = REPO_ROOT / "infra" / "jenkins" / "casc.yaml"
REJECTED_PHASE_FIVE_PARAMETER_DECLARATIONS = (
    "stringParam('REGISTRY', 'localhost:5000', 'Local registry for Project C delivery images')",
    "stringParam('PROJECT_C_LOCAL_ADMIN_ID', '${JENKINS_LOCAL_ADMIN_ID}', "
    "'Local Jenkins administrator identity')",
    "stringParam('PROJECT_C_ALLOWED_APPROVERS', '${JENKINS_LOCAL_APPROVER_ID}', "
    "'Comma-separated local Jenkins approver identities')",
    "stringParam('PROJECT_C_READONLY_OBSERVER_ID', '${JENKINS_LOCAL_VIEWER_ID}', "
    "'Local Jenkins read-only observer identity')",
)


def _dockerfile_text() -> str:
    return DOCKERFILE_PATH.read_text(encoding="utf-8")


def _plugins_lines() -> list[str]:
    return [
        line.strip()
        for line in PLUGINS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _casc_text() -> str:
    return CASC_PATH.read_text(encoding="utf-8")


def _job_block(job_name: str) -> str:
    text = _casc_text()
    start = text.index(f"      pipelineJob('{job_name}') {{")
    return text[start:]


def test_casc_requires_external_placeholder_identities_without_legacy_admin_fallback() -> None:
    text = _casc_text()

    for expected in (
        "${JENKINS_LOCAL_ADMIN_ID}",
        "${JENKINS_LOCAL_ADMIN_PASSWORD}",
        "${JENKINS_LOCAL_APPROVER_ID}",
        "${JENKINS_LOCAL_APPROVER_PASSWORD}",
        "${JENKINS_LOCAL_VIEWER_ID}",
        "${JENKINS_LOCAL_VIEWER_PASSWORD}",
    ):
        assert expected in text

    assert "JENKINS_ADMIN_ID" not in text
    assert "JENKINS_ADMIN_PASSWORD" not in text
    assert "change-me-locally" not in text
    assert "${VAR:-default}" not in text


def test_casc_defines_distinct_local_users_for_admin_approver_and_viewer() -> None:
    text = _casc_text()

    expected = """  securityRealm:
    local:
      allowsSignup: false
      users:
        - id: "${JENKINS_LOCAL_ADMIN_ID}"
          password: "${JENKINS_LOCAL_ADMIN_PASSWORD}"
        - id: "${JENKINS_LOCAL_APPROVER_ID}"
          password: "${JENKINS_LOCAL_APPROVER_PASSWORD}"
        - id: "${JENKINS_LOCAL_VIEWER_ID}"
          password: "${JENKINS_LOCAL_VIEWER_PASSWORD}"
"""
    assert expected in text


def test_casc_uses_role_based_authorization_instead_of_blanket_logged_in_admin() -> None:
    text = _casc_text()

    assert "loggedInUsersCanDoAnything" not in text
    assert "allowAnonymousRead" not in text
    assert 'name: "project-admin"' in text
    assert 'permissions:\n              - "Overall/Administer"' in text
    assert 'name: "project-readonly"' in text
    for expected in ('"Overall/Read"', '"Job/Read"', '"View/Read"'):
        assert expected in text
    assert 'group: "authenticated"' not in text


def test_casc_matches_runtime_proven_global_node_properties_shape() -> None:
    text = _casc_text()
    expected = """  globalNodeProperties:
    - envVars:
        env:
          - key: "PROJECT_C_ALLOWED_APPROVERS"
            value: "${JENKINS_LOCAL_APPROVER_ID}"
          - key: "PROJECT_C_LOCAL_ADMIN_ID"
            value: "${JENKINS_LOCAL_ADMIN_ID}"
          - key: "PROJECT_C_READONLY_OBSERVER_ID"
            value: "${JENKINS_LOCAL_VIEWER_ID}"
          - key: "REGISTRY"
            value: "localhost:5000"
"""

    assert expected in text
    assert 'PROJECT_C_ALLOWED_APPROVERS: "${JENKINS_LOCAL_APPROVER_ID}"' not in text
    assert 'PROJECT_C_LOCAL_ADMIN_ID: "${JENKINS_LOCAL_ADMIN_ID}"' not in text
    assert 'PROJECT_C_READONLY_OBSERVER_ID: "${JENKINS_LOCAL_VIEWER_ID}"' not in text
    assert 'REGISTRY: "localhost:5000"' not in text


def test_casc_does_not_reintroduce_phase_five_job_parameter_workaround() -> None:
    delivery_block = _job_block("project-c-delivery")

    assert "parameters {" not in delivery_block
    for rejected_parameter in REJECTED_PHASE_FIVE_PARAMETER_DECLARATIONS:
        assert rejected_parameter not in delivery_block


def test_casc_does_not_define_parameter_probe_workaround_job() -> None:
    text = _casc_text()

    assert "project-c-parameter-probe" not in text
    assert "PARAMETER_RUNTIME_START" not in text
    assert "PARAMETER_RUNTIME_END" not in text


def test_casc_scopes_named_approver_permissions_to_the_delivery_job() -> None:
    text = _casc_text()

    start = text.index('          - name: "project-c-approver"')
    end = text.index("  crumbIssuer:", start)
    approver_block = text[start:end]

    for expected in (
        'description: "Named build operators for the delivery pipeline"',
        'pattern: "^project-c-delivery$"',
        '"Job/Build"',
        '"Job/Cancel"',
        '"Job/Read"',
        '"Job/Workspace"',
        'user: "${JENKINS_LOCAL_ADMIN_ID}"',
        'user: "${JENKINS_LOCAL_APPROVER_ID}"',
    ):
        assert expected in approver_block

    assert 'user: "${JENKINS_LOCAL_VIEWER_ID}"' not in approver_block


def test_plugins_manifest_is_fully_pinned_and_includes_role_strategy() -> None:
    lines = _plugins_lines()

    role_strategy_lines = [line for line in lines if line.startswith("role-strategy:")]
    assert role_strategy_lines == ["role-strategy:848.va_a_ea_673cf0b_c"]
    assert "configuration-as-code:2099.ve3a_6e23f4960" in lines
    assert "credentials-binding:717.v951d49b_5f3a_a_" in lines
    assert all(re.fullmatch(r"[a-z0-9-]+:[^\s]+", line) for line in lines)


def test_dockerfile_keeps_jcasc_path_and_does_not_reintroduce_legacy_admin_contract() -> None:
    text = _dockerfile_text()

    assert "FROM jenkins/jenkins:2.541.3-lts-jdk21" in text
    assert "ENV CASC_JENKINS_CONFIG=/var/jenkins_home/casc.yaml" in text
    assert "COPY plugins.txt /usr/share/jenkins/ref/plugins.txt" in text
    assert "RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt" in text
    assert "COPY casc.yaml /usr/share/jenkins/ref/casc.yaml" in text
    assert "JENKINS_ADMIN_ID" not in text
    assert "JENKINS_ADMIN_PASSWORD" not in text
