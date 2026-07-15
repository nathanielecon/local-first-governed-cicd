#!/usr/bin/env python3
"""Validate the local Jenkinsfile delivery contract without starting Jenkins."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TRUSTED_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ARBITRARY_REF_RE = re.compile(r"^refs/(heads|tags)/[0-9A-Za-z._/-]+$")

REQUIRED_PHASE6_EVENT_TYPES = (
    "build_published",
    "staging_deployed",
    "staging_verified",
    "production_approval",
    "production_deployed",
    "production_verified",
    "production_verification_failed",
    "rollback_executed",
    "recovery_verified",
)


def is_trusted_release_input(value: str) -> bool:
    """Return True only for an immutable 40-character lowercase commit SHA.

    Syntactically valid branch/tag refs are intentionally rejected so release
    input cannot be an arbitrary operator-chosen ref.
    """
    candidate = value.strip().lower()
    if candidate.startswith("refs/"):
        return False
    if ARBITRARY_REF_RE.fullmatch(value.strip()):
        return False
    return bool(TRUSTED_GIT_SHA_RE.fullmatch(candidate))


def strip_strings(text: str) -> str:
    result: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        chunk = text[index : index + 3]
        if chunk in {"'''", '"""'}:
            quote = chunk
            result.extend(" " * 3)
            index += 3
            while index < length and text[index : index + 3] != quote:
                result.append("\n" if text[index] == "\n" else " ")
                index += 1
            if index < length:
                result.extend(" " * 3)
                index += 3
            continue
        char = text[index]
        if char in {"'", '"'}:
            quote = char
            result.append(" ")
            index += 1
            while index < length:
                current = text[index]
                if current == "\\" and index + 1 < length:
                    result.extend("  ")
                    index += 2
                    continue
                result.append("\n" if current == "\n" else " ")
                index += 1
                if current == quote:
                    break
            continue
        result.append(char)
        index += 1
    return "".join(result)


def validate_braces(text: str) -> list[str]:
    stripped = strip_strings(text)
    depth = 0
    errors: list[str] = []
    for number, char in enumerate(stripped, start=1):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                errors.append(f"unexpected closing brace near character {number}")
                depth = 0
    if depth != 0:
        errors.append("unbalanced braces in Jenkinsfile")
    return errors


def require(pattern: str, text: str, errors: list[str], message: str) -> None:
    if not re.search(pattern, text, re.MULTILINE | re.DOTALL):
        errors.append(message)


def forbid(pattern: str, text: str, errors: list[str], message: str) -> None:
    if re.search(pattern, text, re.MULTILINE | re.DOTALL):
        errors.append(message)


def validate_text(text: str) -> list[str]:
    errors = validate_braces(text)
    require(r"^\s*pipeline\s*\{", text, errors, "missing top-level declarative pipeline block")
    require(r"\boptions\s*\{", text, errors, "missing options block")
    require(r"\btimestamps\s*\(\s*\)", text, errors, "missing timestamps() option")
    require(
        r"\bdisableConcurrentBuilds\s*\(\s*\)",
        text,
        errors,
        "missing disableConcurrentBuilds() option",
    )
    require(r"\bparameters\s*\{", text, errors, "missing parameters block")
    require(
        r"booleanParam\s*\(\s*name:\s*'PROMOTE_PRODUCTION'",
        text,
        errors,
        "missing PROMOTE_PRODUCTION boolean parameter",
    )
    require(
        r"stringParam\s*\(\s*name:\s*'TRUSTED_GIT_SHA'",
        text,
        errors,
        "missing TRUSTED_GIT_SHA immutable commit parameter",
    )
    require(
        r"booleanParam\s*\(\s*name:\s*'FIRST_RELEASE'",
        text,
        errors,
        "missing FIRST_RELEASE parameter for first-release decision gating",
    )
    require(
        r"booleanParam\s*\(\s*name:\s*'DEMONSTRATE_RECOVERY'",
        text,
        errors,
        "missing DEMONSTRATE_RECOVERY parameter for failure-injection rollback demo",
    )
    require(r"\benvironment\s*\{", text, errors, "missing environment block")
    require(r"\bIMAGE_NAME\s*=\s*'delivery-api'", text, errors, "missing IMAGE_NAME contract")
    require(r"\bCI_PROVIDER\s*=\s*'jenkins'", text, errors, "missing CI_PROVIDER contract")
    require(r"\bstages\s*\{", text, errors, "missing stages block")
    for stage in (
        "Metadata",
        "Validate",
        "Build Once",
        "Staging",
        "Production Approval",
        "Rollback Readiness",
        "Production",
        "Failure Injection",
        "Rollback",
        "Recovery",
    ):
        require(
            rf"stage\s*\(\s*'{re.escape(stage)}'\s*\)",
            text,
            errors,
            f"missing required stage: {stage}",
        )
    require(r"docker build --pull", text, errors, "Build Once stage must build with --pull")
    require(r"docker push", text, errors, "Build Once stage must push the built image")
    require(r"image-digest\.txt", text, errors, "Build Once stage must retain image-digest.txt")
    require(
        r"select_matching_repo_digest",
        text,
        errors,
        "Build Once stage must bind RepoDigest to expected registry/repository identity",
    )
    forbid(
        r"index\s+\.RepoDigests\s+0",
        text,
        errors,
        "Build Once must not select an arbitrary first RepoDigest",
    )
    require(
        r"TRUSTED_GIT_SHA\s*==~\s*/\^\[0-9a-f\]\{40\}\$/",
        text,
        errors,
        "Metadata stage must validate TRUSTED_GIT_SHA as an immutable 40-character commit SHA",
    )
    require(
        r"startsWith\s*\(\s*'refs/'\)",
        text,
        errors,
        "Metadata stage must reject refs/ inputs before git fetch",
    )
    require(
        r'git fetch --no-tags origin "\$TRUSTED_GIT_SHA"',
        text,
        errors,
        "Metadata stage must fetch the explicit TRUSTED_GIT_SHA before validation or build",
    )
    require(
        r"git checkout --detach FETCH_HEAD",
        text,
        errors,
        "Metadata stage must detach to the fetched trusted input",
    )
    require(
        r"git rev-parse FETCH_HEAD\^\{commit\}",
        text,
        errors,
        "Metadata stage must resolve a trusted commit SHA from FETCH_HEAD",
    )
    require(
        r"env\.GIT_SHA\s*!=\s*env\.TRUSTED_GIT_SHA",
        text,
        errors,
        "Metadata stage must reject a fetched commit that does not match TRUSTED_GIT_SHA",
    )
    if re.search(r"git rev-parse HEAD", text):
        errors.append("Metadata stage must not trust the implicit workspace HEAD")
    if re.search(
        r"TRUSTED_GIT_REF\s*==~\s*/\^refs\\/\(heads\|tags\)\\/",
        text,
    ):
        errors.append(
            "Metadata stage must not accept arbitrary refs/heads/* or refs/tags/* as trusted input"
        )
    if re.search(r"stringParam\s*\(\s*name:\s*'TRUSTED_GIT_REF'", text):
        errors.append("Jenkinsfile must bind release input to TRUSTED_GIT_SHA, not TRUSTED_GIT_REF")
    require(
        (
            r'input\s+message:\s*"Promote verified digest\s+'
            r"\$\{env\.IMAGE_DIGEST\}\s+from trusted commit\s+"
            r"\$\{env\.TRUSTED_GIT_SHA\}\s+to production\?"
        ),
        text,
        errors,
        (
            "Production Approval stage must request human approval "
            "for the verified digest and trusted commit"
        ),
    )
    require(
        r"submitter:\s*(?:env\.PROJECT_C_ALLOWED_APPROVERS|\"\$\{env\.PROJECT_C_ALLOWED_APPROVERS\}\")",
        text,
        errors,
        "Production Approval stage must restrict approval to PROJECT_C_ALLOWED_APPROVERS",
    )
    require(
        r"submitterParameter:\s*'APPROVED_BY'",
        text,
        errors,
        "Production Approval stage must record APPROVED_BY",
    )
    require(
        r"scripts/evidence\.py\s+append",
        text,
        errors,
        "Jenkinsfile must append release events via scripts/evidence.py append",
    )
    forbid(
        r"scripts/evidence\.py[^\n]*--status",
        text,
        errors,
        "Jenkinsfile must not use legacy evidence.py --status overwrite path",
    )
    require(
        r"--approver-id\s+\"\$APPROVED_BY\"",
        text,
        errors,
        "Production Approval must persist APPROVED_BY into production_approval evidence",
    )
    require(
        r"--approved-at\s+\"\$APPROVED_AT\"",
        text,
        errors,
        "Production Approval must persist APPROVED_AT into production_approval evidence",
    )
    require(
        r"EXPECTED_DIGEST",
        text,
        errors,
        "Pipeline must export EXPECTED_DIGEST for identity-bound deploy verification",
    )
    require(
        r"EXPECTED_REGISTRY",
        text,
        errors,
        "Pipeline must export EXPECTED_REGISTRY for identity-bound deploy verification",
    )
    require(
        r"EXPECTED_REPOSITORY",
        text,
        errors,
        "Pipeline must export EXPECTED_REPOSITORY for identity-bound deploy verification",
    )
    require(
        r"IMAGE_DIGEST_REF",
        text,
        errors,
        "Pipeline must promote the same immutable digest reference built once",
    )
    require(
        r"first_release_decision",
        text,
        errors,
        "Rollback Readiness must support first_release_decision evidence",
    )
    require(
        r"rollback_target_bound",
        text,
        errors,
        "Rollback Readiness must support rollback_target_bound evidence",
    )
    require(
        r"scripts/rollback\.sh",
        text,
        errors,
        "Rollback stage must invoke digest-targeted scripts/rollback.sh",
    )
    forbid(
        r"sed -n 's/\^PRODUCTION_IMAGE=",
        text,
        errors,
        "Jenkinsfile must not treat production.env as the verified rollback-target source of truth",
    )
    for event_type in REQUIRED_PHASE6_EVENT_TYPES:
        require(
            rf"--event-type\s+{re.escape(event_type)}\b",
            text,
            errors,
            f"Jenkinsfile must append {event_type} events",
        )
    require(
        r"(first_release_decision|rollback_target_bound)",
        text,
        errors,
        "Jenkinsfile must append first_release_decision or rollback_target_bound before production",
    )
    require(r"archiveArtifacts\b", text, errors, "post always must archive evidence artifacts")
    require(r"cleanWs\s*\(", text, errors, "post always must clean the workspace")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="Jenkinsfile")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    path = Path(args.path)
    text = path.read_text(encoding="utf-8")
    errors = validate_text(text)
    payload = {"path": str(path), "valid": not errors, "errors": errors}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        if errors:
            print(f"Jenkinsfile contract invalid: {path}")
            for error in errors:
                print(f"- {error}")
        else:
            print(f"Jenkinsfile contract valid: {path}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
