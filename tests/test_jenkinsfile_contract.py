from __future__ import annotations

from pathlib import Path

from scripts.validate_jenkinsfile import is_trusted_release_input, validate_text

ROOT = Path(__file__).resolve().parents[1]
APPROVED_SHA = "0123456789abcdef0123456789abcdef01234567"


def test_repository_jenkinsfile_satisfies_contract() -> None:
    text = (ROOT / "Jenkinsfile").read_text(encoding="utf-8")
    assert validate_text(text) == []


def test_missing_submitter_parameter_is_rejected() -> None:
    text = (
        (ROOT / "Jenkinsfile")
        .read_text(encoding="utf-8")
        .replace("submitterParameter: 'APPROVED_BY'", "submitterParameter: ''")
    )
    assert "Production Approval stage must record APPROVED_BY" in validate_text(text)


def test_missing_named_approver_restriction_is_rejected() -> None:
    text = (
        (ROOT / "Jenkinsfile")
        .read_text(encoding="utf-8")
        .replace("submitter: env.PROJECT_C_ALLOWED_APPROVERS, ", "")
    )
    assert (
        "Production Approval stage must restrict approval to PROJECT_C_ALLOWED_APPROVERS"
        in validate_text(text)
    )


def test_missing_trusted_sha_parameter_is_rejected() -> None:
    text = (
        (ROOT / "Jenkinsfile")
        .read_text(encoding="utf-8")
        .replace(
            (
                "    stringParam(name: 'TRUSTED_GIT_SHA', defaultValue: '', "
                "description: 'Immutable approved commit SHA "
                "(40 lowercase hex chars) required before any fetch or build')\n"
            ),
            "",
        )
    )
    assert "missing TRUSTED_GIT_SHA immutable commit parameter" in validate_text(text)


def test_implicit_head_is_rejected_as_trusted_input() -> None:
    text = (
        (ROOT / "Jenkinsfile")
        .read_text(encoding="utf-8")
        .replace("git rev-parse FETCH_HEAD^{commit}", "git rev-parse HEAD")
    )
    errors = validate_text(text)
    assert "Metadata stage must resolve a trusted commit SHA from FETCH_HEAD" in errors
    assert "Metadata stage must not trust the implicit workspace HEAD" in errors


def test_arbitrary_branch_and_tag_refs_are_rejected_as_trusted_input() -> None:
    assert is_trusted_release_input(APPROVED_SHA)
    assert is_trusted_release_input(APPROVED_SHA.upper())
    assert not is_trusted_release_input("refs/heads/main")
    assert not is_trusted_release_input("refs/heads/feature/unapproved")
    assert not is_trusted_release_input("refs/tags/v1.2.3")
    assert not is_trusted_release_input("refs/tags/release-1")
    assert not is_trusted_release_input("main")
    assert not is_trusted_release_input("deadbeef")
    assert not is_trusted_release_input("")


def test_loose_ref_syntax_gate_is_rejected_by_contract() -> None:
    """Regression: syntax-only refs/heads|tags acceptance must fail the contract."""
    text = (
        (ROOT / "Jenkinsfile")
        .read_text(encoding="utf-8")
        .replace(
            (
                "stringParam(name: 'TRUSTED_GIT_SHA', defaultValue: '', "
                "description: 'Immutable approved commit SHA "
                "(40 lowercase hex chars) required before any fetch or build')"
            ),
            (
                "stringParam(name: 'TRUSTED_GIT_REF', "
                "defaultValue: 'refs/heads/main', "
                "description: 'Controlled Git reference')"
            ),
        )
        .replace(
            (
                "if (!params.TRUSTED_GIT_SHA?.trim()) {\n"
                "            error('TRUSTED_GIT_SHA is required for trusted release input.')\n"
                "          }\n"
                "          env.TRUSTED_GIT_SHA = params.TRUSTED_GIT_SHA.trim().toLowerCase()\n"
                "          // Reject branch/tag refs and any non-SHA input before git fetch.\n"
                "          if (env.TRUSTED_GIT_SHA.startsWith('refs/') "
                "|| !(env.TRUSTED_GIT_SHA ==~ /^[0-9a-f]{40}$/)) {\n"
                '            error("TRUSTED_GIT_SHA must be an immutable '
                "40-character commit SHA; arbitrary refs are rejected before fetch. "
                "Got '${params.TRUSTED_GIT_SHA.trim()}'.\")\n"
                "          }"
            ),
            (
                "if (!params.TRUSTED_GIT_REF?.trim()) {\n"
                "            error('TRUSTED_GIT_REF is required.')\n"
                "          }\n"
                "          env.TRUSTED_GIT_REF = params.TRUSTED_GIT_REF.trim()\n"
                "          if (!(env.TRUSTED_GIT_REF ==~ "
                "/^refs\\/(heads|tags)\\/[0-9A-Za-z._\\/-]+$/)) {\n"
                '            error("TRUSTED_GIT_REF must be a controlled full ref")\n'
                "          }"
            ),
        )
        .replace(
            'git fetch --no-tags origin "$TRUSTED_GIT_SHA"',
            'git fetch --no-tags origin "$TRUSTED_GIT_REF"',
        )
        .replace(
            (
                "env.GIT_SHA = sh(returnStdout: true, "
                'script: "git rev-parse FETCH_HEAD^{commit}").trim()\n'
                "          if (env.GIT_SHA != env.TRUSTED_GIT_SHA) {\n"
                "            error(\"Fetched commit '${env.GIT_SHA}' does not match "
                "trusted input '${env.TRUSTED_GIT_SHA}'.\")\n"
                "          }"
            ),
            (
                "env.TRUSTED_GIT_SHA = sh(returnStdout: true, "
                'script: "git rev-parse FETCH_HEAD^{commit}").trim()\n'
                "          env.GIT_SHA = env.TRUSTED_GIT_SHA"
            ),
        )
        .replace(
            "from trusted commit ${env.TRUSTED_GIT_SHA} to production?",
            "from ${env.TRUSTED_GIT_REF}@${env.GIT_SHA} to production?",
        )
    )
    errors = validate_text(text)
    assert "missing TRUSTED_GIT_SHA immutable commit parameter" in errors
    assert (
        "Metadata stage must not accept arbitrary refs/heads/* or refs/tags/* as trusted input"
        in errors
    )
    assert "Jenkinsfile must bind release input to TRUSTED_GIT_SHA, not TRUSTED_GIT_REF" in errors
    assert (
        "Metadata stage must validate TRUSTED_GIT_SHA as an immutable 40-character commit SHA"
        in errors
    )
    assert "Metadata stage must reject refs/ inputs before git fetch" in errors


def test_missing_fetched_sha_mismatch_guard_is_rejected() -> None:
    text = (
        (ROOT / "Jenkinsfile")
        .read_text(encoding="utf-8")
        .replace(
            (
                "          if (env.GIT_SHA != env.TRUSTED_GIT_SHA) {\n"
                "            error(\"Fetched commit '${env.GIT_SHA}' does not match "
                "trusted input '${env.TRUSTED_GIT_SHA}'.\")\n"
                "          }\n"
            ),
            "",
        )
    )
    assert (
        "Metadata stage must reject a fetched commit that does not match TRUSTED_GIT_SHA"
        in validate_text(text)
    )


def test_unbalanced_braces_are_rejected() -> None:
    text = (ROOT / "Jenkinsfile").read_text(encoding="utf-8").replace("\n  }\n}\n", "\n  }\n", 1)
    assert "unbalanced braces in Jenkinsfile" in validate_text(text)


def test_legacy_status_evidence_path_is_rejected() -> None:
    text = (
        (ROOT / "Jenkinsfile")
        .read_text(encoding="utf-8")
        .replace(
            (
                "python3 scripts/evidence.py append \\\n"
                '            --release-id "$RELEASE_ID" \\\n'
                "            --event-type staging_verified \\"
            ),
            (
                'python3 scripts/evidence.py --release-id "$RELEASE_ID" '
                "--status staging_verified \\\n"
                "            --event-type staging_verified \\"
            ),
        )
    )
    errors = validate_text(text)
    assert "Jenkinsfile must not use legacy evidence.py --status overwrite path" in errors


def test_arbitrary_first_repodigest_is_rejected() -> None:
    text = (
        (ROOT / "Jenkinsfile")
        .read_text(encoding="utf-8")
        .replace(
            "python3 - <<'PY'",
            (
                "docker image inspect --format='{{index .RepoDigests 0}}' "
                '"$IMAGE_REF" > image-digest.txt\n'
                "          python3 - <<'PY'"
            ),
            1,
        )
    )
    errors = validate_text(text)
    assert "Build Once must not select an arbitrary first RepoDigest" in errors


def test_missing_identity_bound_digest_helper_is_rejected() -> None:
    text = (
        (ROOT / "Jenkinsfile")
        .read_text(encoding="utf-8")
        .replace("select_matching_repo_digest", "not_the_identity_helper")
    )
    assert (
        "Build Once stage must bind RepoDigest to expected registry/repository identity"
        in validate_text(text)
    )


def test_missing_approver_persistence_is_rejected() -> None:
    text = (
        (ROOT / "Jenkinsfile")
        .read_text(encoding="utf-8")
        .replace('--approver-id "$APPROVED_BY" \\\n            --approved-at "$APPROVED_AT"', "")
    )
    errors = validate_text(text)
    assert (
        "Production Approval must persist APPROVED_BY into production_approval evidence" in errors
    )
    assert (
        "Production Approval must persist APPROVED_AT into production_approval evidence" in errors
    )


def test_missing_failure_injection_stage_is_rejected() -> None:
    text = (
        (ROOT / "Jenkinsfile")
        .read_text(encoding="utf-8")
        .replace("stage('Failure Injection')", "stage('Skipped Injection')")
    )
    assert "missing required stage: Failure Injection" in validate_text(text)


def test_missing_rollback_target_or_first_release_append_is_rejected() -> None:
    text = (
        (ROOT / "Jenkinsfile")
        .read_text(encoding="utf-8")
        .replace("--event-type first_release_decision", "--event-type staging_verified")
        .replace("--event-type rollback_target_bound", "--event-type staging_verified")
    )
    errors = validate_text(text)
    assert "Rollback Readiness must support first_release_decision evidence" in errors
    assert "Rollback Readiness must support rollback_target_bound evidence" in errors
