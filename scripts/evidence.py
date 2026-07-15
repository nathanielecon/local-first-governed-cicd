#!/usr/bin/env python3
"""Append-only release evidence and derived summary manifest (Phase 6)."""

from __future__ import annotations

import argparse
import json
import os
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0"
EVENTS_FILENAME = "events.jsonl"
MANIFEST_FILENAME = "manifest.json"
CLAIM_BOUNDARY = "local-only / production-like"

ALLOWED_EVENT_TYPES = frozenset(
    {
        "build_published",
        "staging_deployed",
        "staging_verified",
        "production_approval",
        "rollback_target_bound",
        "first_release_decision",
        "production_deployed",
        "production_verified",
        "production_verification_failed",
        "rollback_executed",
        "recovery_verified",
    }
)
ALLOWED_RESULTS = frozenset({"pass", "fail", "blocked", "recorded"})
ALLOWED_ENVIRONMENTS = frozenset({"staging", "production", "local"})

REQUIRED_EVENT_FIELDS = (
    "event_id",
    "event_type",
    "release_id",
    "commit_sha",
    "environment",
    "recorded_at",
    "actor",
    "result",
    "details",
)

PRODUCTION_CLAIM_EVENTS = frozenset(
    {"production_deployed", "production_verified", "rollback_executed", "recovery_verified"}
)
DIGEST_PROMOTION_EVENTS = frozenset(
    {
        "build_published",
        "staging_deployed",
        "staging_verified",
        "production_approval",
        "production_deployed",
        "production_verified",
    }
)

SECRET_PATTERNS = (
    re.compile(
        r'(?i)["\']?(password|passwd|secret|token|api[_-]?key|private[_-]?key)["\']?\s*[:=]'
    ),
    re.compile(r"(?i)-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)AKIA[0-9A-Z]{16}"),
)


class EvidenceError(ValueError):
    """Raised when evidence cannot be appended or derived."""


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def release_dir(root: Path, release_id: str) -> Path:
    return root / "evidence" / release_id


def events_path(directory: Path) -> Path:
    return directory / EVENTS_FILENAME


def manifest_path(directory: Path) -> Path:
    return directory / MANIFEST_FILENAME


def _contains_secrets(payload: Any) -> list[str]:
    text = json.dumps(payload, ensure_ascii=False)
    return [pattern.pattern for pattern in SECRET_PATTERNS if pattern.search(text)]


def _require_nonempty(value: str, field: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise EvidenceError(f"{field} must be non-empty")
    return cleaned


def normalize_event(event: dict[str, Any], *, release_id: str) -> dict[str, Any]:
    missing = [field for field in REQUIRED_EVENT_FIELDS if field not in event]
    if missing:
        raise EvidenceError(f"event missing required fields: {', '.join(missing)}")

    event_type = _require_nonempty(str(event["event_type"]), "event_type")
    if event_type not in ALLOWED_EVENT_TYPES:
        raise EvidenceError(f"unsupported event_type: {event_type}")

    result = _require_nonempty(str(event["result"]), "result")
    if result not in ALLOWED_RESULTS:
        raise EvidenceError(f"unsupported result: {result}")

    environment = _require_nonempty(str(event["environment"]), "environment")
    if environment not in ALLOWED_ENVIRONMENTS:
        raise EvidenceError(f"unsupported environment: {environment}")

    details = event["details"]
    if not isinstance(details, dict):
        raise EvidenceError("details must be an object")

    normalized = {
        "event_id": _require_nonempty(str(event["event_id"]), "event_id"),
        "event_type": event_type,
        "release_id": _require_nonempty(str(event.get("release_id", release_id)), "release_id"),
        "commit_sha": _require_nonempty(str(event["commit_sha"]), "commit_sha"),
        "environment": environment,
        "recorded_at": _require_nonempty(str(event["recorded_at"]), "recorded_at"),
        "actor": _require_nonempty(str(event["actor"]), "actor"),
        "result": result,
        "details": details,
    }
    if normalized["release_id"] != release_id:
        raise EvidenceError(
            f"event release_id {normalized['release_id']} does not match directory {release_id}"
        )

    image_digest = event.get("image_digest", details.get("image_digest", ""))
    if image_digest:
        normalized["image_digest"] = str(image_digest).strip()

    if event_type == "production_approval":
        approver_id = str(details.get("approver_id", "")).strip()
        approved_at = str(details.get("approved_at", "")).strip()
        if not approver_id or not approved_at:
            raise EvidenceError("production_approval requires details.approver_id and approved_at")
        if not normalized.get("image_digest"):
            raise EvidenceError("production_approval requires image_digest")

    if event_type == "rollback_target_bound":
        required = ("digest", "commit_sha", "verified_at", "source_release_id", "environment")
        missing_target = [field for field in required if not str(details.get(field, "")).strip()]
        if missing_target:
            raise EvidenceError(
                "rollback_target_bound missing details fields: " + ", ".join(missing_target)
            )
        if details["digest"] == normalized.get("image_digest"):
            raise EvidenceError("rollback target digest must not be self-referential")

    if event_type == "first_release_decision":
        required = ("decision", "decided_by", "decided_at", "rationale", "accepted_risk")
        missing_decision = [field for field in required if not str(details.get(field, "")).strip()]
        if missing_decision:
            raise EvidenceError(
                "first_release_decision missing details fields: " + ", ".join(missing_decision)
            )

    if event_type == "recovery_verified":
        checks = details.get("checks")
        if not isinstance(checks, dict):
            raise EvidenceError("recovery_verified requires details.checks object")
        for name in ("deployed_digest", "health", "version", "business_behavior"):
            if checks.get(name) != "pass":
                raise EvidenceError(f"recovery_verified requires checks.{name}=pass")

    secret_hits = _contains_secrets(normalized)
    if secret_hits:
        raise EvidenceError("event appears to contain secrets; refused")

    return normalized


def load_events(directory: Path) -> list[dict[str, Any]]:
    path = events_path(directory)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            raise EvidenceError(f"invalid JSONL at {path.name}:{line_no}: {error}") from error
        if not isinstance(payload, dict):
            raise EvidenceError(f"event at {path.name}:{line_no} must be an object")
        events.append(payload)
    return events


def append_event(
    root: Path,
    release_id: str,
    event: dict[str, Any],
    *,
    regenerate_manifest: bool = True,
) -> dict[str, Any]:
    """Append one event. Existing event lines are never rewritten or truncated."""
    release_id = _require_nonempty(release_id, "release_id")
    directory = release_dir(root, release_id)
    directory.mkdir(parents=True, exist_ok=True)

    existing = load_events(directory)
    existing_ids = {str(item.get("event_id", "")) for item in existing}
    normalized = normalize_event(event, release_id=release_id)
    if normalized["event_id"] in existing_ids:
        raise EvidenceError(f"duplicate event_id: {normalized['event_id']}")

    path = events_path(directory)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(normalized, ensure_ascii=False, separators=(",", ":")) + "\n")

    if regenerate_manifest:
        write_derived_manifest(directory, release_id=release_id)
    return normalized


def _latest(events: list[dict[str, Any]], event_type: str) -> dict[str, Any] | None:
    for event in reversed(events):
        if event.get("event_type") == event_type:
            return event
    return None


def _promotion_digest(events: list[dict[str, Any]]) -> str:
    for event_type in (
        "build_published",
        "staging_verified",
        "production_approval",
        "production_verified",
    ):
        event = _latest(events, event_type)
        if event and event.get("image_digest"):
            return str(event["image_digest"])
    for event in events:
        if event.get("image_digest"):
            return str(event["image_digest"])
    return ""


def _image_reference(events: list[dict[str, Any]]) -> str:
    for event in reversed(events):
        details = event.get("details") or {}
        reference = details.get("image_reference") or details.get("image_ref")
        if reference:
            return str(reference)
    return ""


def _derive_status(events: list[dict[str, Any]]) -> str:
    priority = (
        "recovery_verified",
        "rollback_executed",
        "production_verification_failed",
        "production_verified",
        "production_deployed",
        "first_release_decision",
        "rollback_target_bound",
        "production_approval",
        "staging_verified",
        "staging_deployed",
        "build_published",
    )
    for event_type in priority:
        event = _latest(events, event_type)
        if event:
            return event_type
    return "recorded"


def derive_manifest(
    events: list[dict[str, Any]],
    *,
    release_id: str,
    updated_at: str | None = None,
    pipeline: dict[str, Any] | None = None,
    reports: list[Any] | None = None,
) -> dict[str, Any]:
    if not events:
        raise EvidenceError("cannot derive manifest without events")

    for event in events:
        normalize_event(event, release_id=release_id)

    commit_shas = {str(event["commit_sha"]) for event in events}
    if len(commit_shas) != 1:
        raise EvidenceError(f"inconsistent commit_sha values: {sorted(commit_shas)}")
    commit_sha = next(iter(commit_shas))

    image_digest = _promotion_digest(events)
    staging_deployed = _latest(events, "staging_deployed")
    staging_verified = _latest(events, "staging_verified")
    production_deployed = _latest(events, "production_deployed")
    production_verified = _latest(events, "production_verified")
    rollback_bound = _latest(events, "rollback_target_bound")
    first_release = _latest(events, "first_release_decision")
    recovery = _latest(events, "recovery_verified")
    rollback_executed = _latest(events, "rollback_executed")

    approvals: list[dict[str, Any]] = []
    for event in events:
        if event.get("event_type") != "production_approval":
            continue
        details = event["details"]
        approvals.append(
            {
                "approver_id": details["approver_id"],
                "approved_at": details["approved_at"],
                "commit_sha": event["commit_sha"],
                "image_digest": event.get("image_digest", ""),
                "event_id": event["event_id"],
            }
        )

    staging_status = "pending"
    if staging_verified and staging_verified.get("result") == "pass":
        staging_status = "verified"
    elif staging_deployed:
        staging_status = "deployed"

    production_status = "pending"
    if production_verified and production_verified.get("result") == "pass":
        production_status = "verified"
    elif production_deployed:
        production_status = "deployed"

    rollback_target = None
    if rollback_bound:
        details = rollback_bound["details"]
        rollback_target = {
            "digest": details["digest"],
            "commit_sha": details["commit_sha"],
            "verified_at": details["verified_at"],
            "source_release_id": details["source_release_id"],
            "environment": details["environment"],
        }

    first_release_decision = None
    if first_release:
        details = first_release["details"]
        first_release_decision = {
            "decision": details["decision"],
            "decided_by": details["decided_by"],
            "decided_at": details["decided_at"],
            "rationale": details["rationale"],
            "accepted_risk": details["accepted_risk"],
        }

    recovery_summary = None
    if recovery:
        recovery_summary = {
            "verified_at": recovery["recorded_at"],
            "image_digest": recovery.get("image_digest", ""),
            "checks": recovery["details"].get("checks", {}),
            "rollback_event_id": (rollback_executed or {}).get("event_id", ""),
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "release_id": release_id,
        "status": _derive_status(events),
        "commit_sha": commit_sha,
        "claim_boundary": CLAIM_BOUNDARY,
        "image": {
            "reference": _image_reference(events),
            "digest": image_digest,
        },
        "staging": {
            "status": staging_status,
            "deployed_at": (staging_deployed or {}).get("recorded_at"),
            "verified_at": (staging_verified or {}).get("recorded_at"),
        },
        "approvals": approvals,
        "production": {
            "status": production_status,
            "deployed_at": (production_deployed or {}).get("recorded_at"),
            "verified_at": (production_verified or {}).get("recorded_at"),
        },
        "rollback_target": rollback_target,
        "first_release_decision": first_release_decision,
        "recovery": recovery_summary,
        "pipeline": pipeline
        or {
            "provider": os.getenv("CI_PROVIDER", "local"),
            "run_id": os.getenv("BUILD_TAG", os.getenv("GITHUB_RUN_ID", "manual")),
        },
        "reports": reports or [],
        "event_count": len(events),
        "updated_at": updated_at or utc_now(),
    }


def write_derived_manifest(directory: Path, *, release_id: str | None = None) -> dict[str, Any]:
    release_id = release_id or directory.name
    events = load_events(directory)
    existing_pipeline = None
    existing_reports = None
    path = manifest_path(directory)
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(existing, dict):
                existing_pipeline = existing.get("pipeline")
                existing_reports = existing.get("reports")
        except json.JSONDecodeError:
            pass
    manifest = derive_manifest(
        events,
        release_id=release_id,
        pipeline=existing_pipeline if isinstance(existing_pipeline, dict) else None,
        reports=existing_reports if isinstance(existing_reports, list) else None,
    )
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def _gate_fields(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": manifest.get("schema_version"),
        "release_id": manifest.get("release_id"),
        "commit_sha": manifest.get("commit_sha"),
        "image": manifest.get("image"),
        "staging": manifest.get("staging"),
        "approvals": manifest.get("approvals"),
        "production": manifest.get("production"),
        "rollback_target": manifest.get("rollback_target"),
        "first_release_decision": manifest.get("first_release_decision"),
        "recovery": manifest.get("recovery"),
        "event_count": manifest.get("event_count"),
        "claim_boundary": manifest.get("claim_boundary"),
    }


def validate_release_evidence(root: Path, release_id: str) -> list[str]:
    """Fail-closed validation for append-only events and derived summary."""
    errors: list[str] = []
    directory = release_dir(root, release_id)
    events_file = events_path(directory)
    manifest_file = manifest_path(directory)

    if not directory.exists():
        return [f"evidence directory not found: evidence/{release_id}"]
    if not events_file.exists():
        errors.append(f"missing append-only event log: evidence/{release_id}/{EVENTS_FILENAME}")
    if not manifest_file.exists():
        errors.append(f"missing summary manifest: evidence/{release_id}/{MANIFEST_FILENAME}")
        return errors

    try:
        events = load_events(directory)
    except EvidenceError as error:
        return [str(error)]

    if not events:
        errors.append("event log is empty")
        return errors

    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [f"invalid manifest JSON: {error}"]
    if not isinstance(manifest, dict):
        return ["manifest must be a JSON object"]

    secret_hits = _contains_secrets({"events": events, "manifest": manifest})
    if secret_hits:
        errors.append("secrets detected in evidence artifacts")

    event_ids: list[str] = []
    for index, event in enumerate(events, start=1):
        try:
            normalize_event(event, release_id=release_id)
        except EvidenceError as error:
            errors.append(f"event[{index}]: {error}")
            continue
        event_ids.append(str(event["event_id"]))
    if len(event_ids) != len(set(event_ids)):
        errors.append("duplicate event_id values are not allowed")

    present = {str(event.get("event_type")) for event in events}
    claimed_production = bool(present & PRODUCTION_CLAIM_EVENTS) or str(
        manifest.get("production", {}).get("status", "")
    ) in {"deployed", "verified"}

    if claimed_production:
        for required in (
            "build_published",
            "staging_deployed",
            "staging_verified",
            "production_approval",
            "production_deployed",
        ):
            if required not in present:
                errors.append(f"missing required event for production claim: {required}")
        production_claimed_verified = (
            "production_verified" in present
            or manifest.get("production", {}).get("status") == "verified"
        )
        if production_claimed_verified and "production_verified" not in present:
            errors.append("missing required event for production claim: production_verified")
        if "rollback_target_bound" not in present and "first_release_decision" not in present:
            errors.append(
                "production claim requires rollback_target_bound or first_release_decision"
            )
        approvals = [event for event in events if event.get("event_type") == "production_approval"]
        if not approvals:
            errors.append("missing production_approval event")
        else:
            for event in approvals:
                details = event.get("details") or {}
                if not str(details.get("approver_id", "")).strip():
                    errors.append("production_approval missing approver_id")
                if not str(details.get("approved_at", "")).strip():
                    errors.append("production_approval missing approved_at")

    if "recovery_verified" in present or "rollback_executed" in present:
        if "rollback_executed" not in present:
            errors.append("recovery claim missing rollback_executed")
        if "recovery_verified" not in present:
            errors.append("recovery claim missing recovery_verified")
        if "rollback_target_bound" not in present:
            errors.append("recovery claim missing rollback_target_bound")

    digests = {
        str(event["image_digest"])
        for event in events
        if event.get("event_type") in DIGEST_PROMOTION_EVENTS and event.get("image_digest")
    }
    if len(digests) > 1:
        errors.append(f"inconsistent image_digest across promotion events: {sorted(digests)}")

    commit_shas = {str(event.get("commit_sha", "")) for event in events}
    if len(commit_shas) > 1:
        errors.append(f"inconsistent commit_sha across events: {sorted(commit_shas)}")

    try:
        derived = derive_manifest(
            events,
            release_id=release_id,
            updated_at=str(manifest.get("updated_at") or utc_now()),
            pipeline=(
                manifest.get("pipeline") if isinstance(manifest.get("pipeline"), dict) else None
            ),
            reports=(
                manifest.get("reports") if isinstance(manifest.get("reports"), list) else None
            ),
        )
    except EvidenceError as error:
        errors.append(f"manifest derivation failed: {error}")
        return errors

    if _gate_fields(manifest) != _gate_fields(derived):
        errors.append("summary manifest gate fields are not derived from the event log")

    claim_boundary = str(manifest.get("claim_boundary", ""))
    if claim_boundary and "local-only" not in claim_boundary.lower():
        errors.append("claim_boundary must remain local-only / production-like for this contract")

    return errors


def build_event_from_args(args: argparse.Namespace) -> dict[str, Any]:
    details: dict[str, Any] = {}
    if args.details_json:
        try:
            loaded = json.loads(args.details_json)
        except json.JSONDecodeError as error:
            raise EvidenceError(f"invalid --details-json: {error}") from error
        if not isinstance(loaded, dict):
            raise EvidenceError("--details-json must be a JSON object")
        details.update(loaded)

    if args.image_ref:
        details.setdefault("image_reference", args.image_ref)
    if args.approver_id:
        details["approver_id"] = args.approver_id
    if args.approved_at:
        details["approved_at"] = args.approved_at
    if args.rollback_target_digest:
        details.update(
            {
                "digest": args.rollback_target_digest,
                "commit_sha": args.rollback_target_commit or args.commit_sha,
                "verified_at": args.rollback_target_verified_at or args.recorded_at or utc_now(),
                "source_release_id": args.rollback_target_source_release or "prior-release",
                "environment": args.rollback_target_environment or "production",
            }
        )
    if args.decision:
        details.update(
            {
                "decision": args.decision,
                "decided_by": args.decided_by or args.actor,
                "decided_at": args.decided_at or args.recorded_at or utc_now(),
                "rationale": args.rationale or "No verified prior production digest exists.",
                "accepted_risk": args.accepted_risk
                or "Rollback to a prior verified digest is unavailable for this first release.",
            }
        )
    if args.recovery_checks_json:
        try:
            checks = json.loads(args.recovery_checks_json)
        except json.JSONDecodeError as error:
            raise EvidenceError(f"invalid --recovery-checks-json: {error}") from error
        if not isinstance(checks, dict):
            raise EvidenceError("--recovery-checks-json must be a JSON object")
        details["checks"] = checks

    recorded_at = args.recorded_at or utc_now()
    event: dict[str, Any] = {
        "event_id": args.event_id or f"{args.event_type}-{uuid.uuid4().hex[:12]}",
        "event_type": args.event_type,
        "release_id": args.release_id,
        "commit_sha": args.commit_sha,
        "environment": args.environment,
        "recorded_at": recorded_at,
        "actor": args.actor,
        "result": args.result,
        "details": details,
    }
    if args.image_digest:
        event["image_digest"] = args.image_digest
    return event


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Append-only release evidence and derived summary manifest"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    append = subparsers.add_parser("append", help="Append one event and refresh summary")
    append.add_argument("--release-id", required=True)
    append.add_argument("--event-type", required=True, choices=sorted(ALLOWED_EVENT_TYPES))
    append.add_argument("--commit-sha", required=True)
    append.add_argument("--actor", required=True)
    append.add_argument("--environment", default="local", choices=sorted(ALLOWED_ENVIRONMENTS))
    append.add_argument("--result", default="pass", choices=sorted(ALLOWED_RESULTS))
    append.add_argument("--image-digest", default="")
    append.add_argument("--image-ref", default="")
    append.add_argument("--event-id", default="")
    append.add_argument("--recorded-at", default="")
    append.add_argument("--details-json", default="")
    append.add_argument("--approver-id", default="")
    append.add_argument("--approved-at", default="")
    append.add_argument("--rollback-target-digest", default="")
    append.add_argument("--rollback-target-commit", default="")
    append.add_argument("--rollback-target-verified-at", default="")
    append.add_argument("--rollback-target-source-release", default="")
    append.add_argument(
        "--rollback-target-environment", default="production", choices=sorted(ALLOWED_ENVIRONMENTS)
    )
    append.add_argument("--decision", default="")
    append.add_argument("--decided-by", default="")
    append.add_argument("--decided-at", default="")
    append.add_argument("--rationale", default="")
    append.add_argument("--accepted-risk", default="")
    append.add_argument("--recovery-checks-json", default="")
    append.set_defaults(handler="append")

    derive = subparsers.add_parser("derive", help="Regenerate summary from events")
    derive.add_argument("--release-id", required=True)
    derive.set_defaults(handler="derive")

    validate = subparsers.add_parser("validate", help="Validate events and derived summary")
    validate.add_argument("--release-id", required=True)
    validate.set_defaults(handler="validate")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(os.getenv("PROJECT_C_ROOT", Path.cwd()))

    try:
        if args.handler == "append":
            event = build_event_from_args(args)
            normalized = append_event(root, args.release_id, event)
            path = manifest_path(release_dir(root, args.release_id))
            print(
                json.dumps(
                    {"event": normalized, "manifest_path": path.as_posix()},
                    indent=2,
                    ensure_ascii=False,
                )
            )
            print(path)
            return 0
        if args.handler == "derive":
            manifest = write_derived_manifest(
                release_dir(root, args.release_id), release_id=args.release_id
            )
            path = manifest_path(release_dir(root, args.release_id))
            print(json.dumps(manifest, indent=2, ensure_ascii=False))
            print(path)
            return 0
        if args.handler == "validate":
            errors = validate_release_evidence(root, args.release_id)
            payload = {
                "release_id": args.release_id,
                "valid": not errors,
                "errors": errors,
            }
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return 0 if not errors else 1
    except EvidenceError as error:
        print(json.dumps({"error": str(error)}, indent=2, ensure_ascii=False))
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
