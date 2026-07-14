#!/usr/bin/env python3
"""Single CLI control surface for the Project C gstack harness."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

EXIT_OK = 0
EXIT_SCHEMA = 2
EXIT_GATE = 3
EXIT_ENVIRONMENT = 4
EXIT_BLOCKED = 5
EXIT_HUMAN = 6
EXIT_VALIDATION = 7
EXIT_POLICY = 8
EXIT_CONFLICT = 9

ROOT = Path(os.getenv("PROJECT_C_ROOT", Path(__file__).resolve().parents[1]))
JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)
REQUIRED_SKILLS = (
    "project-discovery",
    "spec",
    "plan-eng-review",
    "implement-slice",
    "review",
    "qa",
    "security-review",
    "ship",
    "retro",
)


class ProjectError(Exception):
    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def read_json_block(name: str) -> dict[str, Any]:
    path = ROOT / name
    if not path.exists():
        raise ProjectError(f"missing authoritative file: {name}", EXIT_SCHEMA)
    match = JSON_BLOCK.search(path.read_text(encoding="utf-8"))
    if not match:
        raise ProjectError(f"missing JSON authority block: {name}", EXIT_SCHEMA)
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError as error:
        raise ProjectError(f"invalid JSON in {name}: {error}", EXIT_SCHEMA) from error
    if not isinstance(value, dict):
        raise ProjectError(f"authority block must be an object: {name}", EXIT_SCHEMA)
    return value


def emit(payload: dict[str, Any], human: str | None = None, json_only: bool = False) -> None:
    if human and not json_only:
        print(human)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def validate_state() -> list[str]:
    errors: list[str] = []
    for name, required in (
        ("PLAN.md", ("schema_version", "revision", "authorized_through_phase", "tasks")),
        ("STATUS.md", ("schema_version", "revision", "current_phase", "current_gate")),
        ("ISSUES.md", ("schema_version", "revision", "issues")),
    ):
        try:
            data = read_json_block(name)
            errors.extend(f"{name}: missing {field}" for field in required if field not in data)
        except ProjectError as error:
            errors.append(str(error))

    if errors:
        return errors
    plan = read_json_block("PLAN.md")
    issues = read_json_block("ISSUES.md")
    task_ids = {task.get("id") for task in plan["tasks"]}
    issue_ids = {issue.get("id") for issue in issues["issues"]}
    required_task_fields = {
        "id",
        "phase",
        "state",
        "depends_on",
        "model_tier",
        "write_scope",
        "acceptance_criteria",
        "evidence_paths",
        "gate",
        "attempts",
    }
    for task in plan["tasks"]:
        missing = required_task_fields - set(task)
        errors.extend(f"{task.get('id', '?')}: missing {field}" for field in sorted(missing))
        errors.extend(
            f"{task.get('id')}: unknown dependency {dependency}"
            for dependency in task.get("depends_on", [])
            if dependency not in task_ids
        )
        errors.extend(
            f"{task.get('id')}: unknown issue {issue_id}"
            for issue_id in task.get("issue_ids", [])
            if issue_id not in issue_ids
        )
    return errors


def validate_skills() -> list[str]:
    errors: list[str] = []
    for skill in REQUIRED_SKILLS:
        path = ROOT / ".codex" / "skills" / skill / "SKILL.md"
        if not path.exists():
            errors.append(f"missing skill: {skill}")
            continue
        content = path.read_text(encoding="utf-8")
        if not content.startswith("---\n") or f"name: {skill}" not in content:
            errors.append(f"invalid skill frontmatter: {skill}")
        if "description:" not in content:
            errors.append(f"missing skill description: {skill}")
    return errors


def command_status(args: argparse.Namespace) -> int:
    status = read_json_block("STATUS.md")
    plan = read_json_block("PLAN.md")
    tasks = plan["tasks"]
    if args.phase is not None:
        tasks = [task for task in tasks if task["phase"] == args.phase]
    if args.task:
        tasks = [task for task in tasks if task["id"] == args.task]
    emit(
        {"status": status, "tasks": tasks},
        f"Phase {status['current_phase']}: {status['current_gate']}",
        args.json,
    )
    return EXIT_OK


def command_issues(args: argparse.Namespace) -> int:
    issues = read_json_block("ISSUES.md")["issues"]
    if args.status:
        issues = [issue for issue in issues if issue["status"] == args.status]
    if args.severity:
        issues = [issue for issue in issues if issue["severity"] == args.severity]
    emit({"count": len(issues), "issues": issues}, f"{len(issues)} matching issue(s)", args.json)
    return EXIT_OK


def command_phase(args: argparse.Namespace) -> int:
    plan = read_json_block("PLAN.md")
    if args.phase > plan["authorized_through_phase"]:
        authorized = plan["authorized_through_phase"]
        raise ProjectError(
            f"phase {args.phase} is not authorized; authorized through phase {authorized}",
            EXIT_HUMAN,
        )
    tasks = [task for task in plan["tasks"] if task["phase"] == args.phase]
    if args.task:
        tasks = [task for task in tasks if task["id"] == args.task]
    emit(
        {"phase": args.phase, "dry_run": args.dry_run, "tasks": tasks},
        f"Phase {args.phase} task plan",
        args.json,
    )
    return EXIT_OK


def run_check(command: list[str]) -> tuple[int, str]:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    output = (result.stdout + result.stderr).strip()
    return result.returncode, output


def command_validate(args: argparse.Namespace) -> int:
    checks: dict[str, list[str]] = {}
    if args.scope in {"state", "phase-1", "all"}:
        checks["state"] = validate_state()
    if args.scope in {"skills", "phase-1", "all"}:
        checks["skills"] = validate_skills()
    if args.scope in {"phase-1", "all"}:
        required = (
            "AGENTS.md",
            "DECISIONS.md",
            "docs/scaffold-audit.md",
            "docs/reviews/eng-review.md",
        )
        checks["phase-1-files"] = [
            f"missing {path}" for path in required if not (ROOT / path).exists()
        ]
        test_code, test_output = run_check(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_project_cli.py",
                "-q",
                "-o",
                "addopts=",
            ]
        )
        checks["cli-tests"] = [] if test_code == 0 else [test_output]
        current_phase = read_json_block("STATUS.md")["current_phase"]
        critical = [
            issue["id"]
            for issue in read_json_block("ISSUES.md")["issues"]
            if issue["severity"] == "critical"
            and issue["status"] == "open"
            and issue["phase"] <= current_phase
        ]
        checks["engineering-gate"] = [f"unresolved critical issue: {issue}" for issue in critical]
        waiting_human = [
            issue["id"]
            for issue in read_json_block("ISSUES.md")["issues"]
            if issue["phase"] == 1 and issue["status"] == "waiting-human"
        ]
        checks["human-gate"] = [f"waiting for human decision: {issue}" for issue in waiting_human]
    if args.scope == "app":
        code, output = run_check([sys.executable, "-m", "pytest", "tests", "-q"])
        checks["app"] = [] if code == 0 else [output]
    if args.scope not in {
        "state",
        "skills",
        "phase-1",
        "app",
        "container",
        "github",
        "jenkins",
        "promotion",
        "security",
        "evidence",
        "all",
    }:
        raise ProjectError(f"unknown validation scope: {args.scope}", EXIT_SCHEMA)
    if args.scope in {"container", "github", "jenkins", "promotion", "security", "evidence"}:
        raise ProjectError(
            f"scope {args.scope} belongs to an unauthorized or unimplemented phase gate", EXIT_HUMAN
        )
    failures = {name: errors for name, errors in checks.items() if errors}
    emit(
        {"scope": args.scope, "passed": not failures, "checks": checks},
        f"Validation {'passed' if not failures else 'blocked'}: {args.scope}",
        args.json,
    )
    return EXIT_GATE if failures else EXIT_OK


def command_resume(args: argparse.Namespace) -> int:
    plan = read_json_block("PLAN.md")
    matches = [task for task in plan["tasks"] if task["id"] == args.task_id]
    if not matches:
        raise ProjectError(f"unknown task: {args.task_id}", EXIT_SCHEMA)
    task = matches[0]
    if task["state"] not in {"blocked", "waiting-human"}:
        raise ProjectError(
            f"task {args.task_id} is not resumable from {task['state']}", EXIT_CONFLICT
        )
    issues = read_json_block("ISSUES.md")["issues"]
    unresolved = [
        issue["id"]
        for issue in issues
        if issue["id"] in task.get("issue_ids", [])
        and issue["status"] not in {"resolved", "accepted-risk"}
    ]
    if unresolved:
        raise ProjectError(
            f"task {args.task_id} remains blocked by {', '.join(unresolved)}", EXIT_BLOCKED
        )
    emit(
        {"task": task, "resumable": True},
        f"Task {args.task_id} is eligible for orchestrator dispatch",
        args.json,
    )
    return EXIT_OK


def command_evidence(args: argparse.Namespace) -> int:
    try:
        from scripts.evidence import validate_release_evidence
    except ModuleNotFoundError:  # running as scripts/project_cli.py
        from evidence import validate_release_evidence

    directory = ROOT / "evidence" / args.release_id
    manifest = directory / "manifest.json"
    events = directory / "events.jsonl"
    if not directory.exists() and not manifest.exists():
        raise ProjectError(
            f"evidence manifest not found: evidence/{args.release_id}/manifest.json",
            EXIT_VALIDATION,
        )
    errors = validate_release_evidence(ROOT, args.release_id)
    payload = {
        "path": (
            manifest.relative_to(ROOT).as_posix()
            if manifest.exists()
            else f"evidence/{args.release_id}/manifest.json"
        ),
        "events_path": (
            events.relative_to(ROOT).as_posix()
            if events.exists()
            else f"evidence/{args.release_id}/events.jsonl"
        ),
        "valid": not errors,
        "errors": errors,
    }
    emit(payload, None, args.json)
    return EXIT_VALIDATION if errors else EXIT_OK


def command_bootstrap(args: argparse.Namespace) -> int:
    errors = validate_state() + validate_skills()
    tools = {name: run_check([name, "--version"])[0] == 0 for name in ("git", "python")}
    docker_available = False if args.skip_docker else run_check(["docker", "info"])[0] == 0
    payload = {
        "state_errors": errors,
        "tools": tools,
        "docker_available": docker_available,
        "docker_required": False,
    }
    emit(payload, "Bootstrap inspection complete", args.json)
    return EXIT_SCHEMA if errors or not all(tools.values()) else EXIT_OK


def phase_arg_choices() -> range:
    """CLI phase numbers include at least one slot above PLAN authorization."""
    try:
        authorized = int(read_json_block("PLAN.md")["authorized_through_phase"])
    except (ProjectError, KeyError, TypeError, ValueError):
        authorized = 9
    # Always accept authorized+1 so auth can return EXIT_HUMAN; floor at 11.
    return range(1, max(authorized + 1, 11) + 1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="project")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap = subparsers.add_parser("bootstrap")
    bootstrap.add_argument("--skip-docker", action="store_true")
    bootstrap.add_argument("--json", action="store_true")
    bootstrap.set_defaults(handler=command_bootstrap)

    status = subparsers.add_parser("status")
    status.add_argument("--phase", type=int)
    status.add_argument("--task")
    status.add_argument("--json", action="store_true")
    status.set_defaults(handler=command_status)

    issues = subparsers.add_parser("issues")
    issues.add_argument("--status", choices=("open", "waiting-human", "resolved", "accepted-risk"))
    issues.add_argument("--severity", choices=("advisory", "blocking", "critical"))
    issues.add_argument("--json", action="store_true")
    issues.set_defaults(handler=command_issues)

    phase = subparsers.add_parser("phase")
    phase.add_argument("phase", type=int, choices=phase_arg_choices())
    phase.add_argument("--task")
    phase.add_argument("--dry-run", action="store_true")
    phase.add_argument("--json", action="store_true")
    phase.set_defaults(handler=command_phase)

    validate = subparsers.add_parser("validate")
    validate.add_argument("scope")
    validate.add_argument("--json", action="store_true")
    validate.set_defaults(handler=command_validate)

    resume = subparsers.add_parser("resume")
    resume.add_argument("task_id")
    resume.add_argument("--json", action="store_true")
    resume.set_defaults(handler=command_resume)

    evidence = subparsers.add_parser("evidence")
    evidence.add_argument("release_id")
    evidence.add_argument("--json", action="store_true")
    evidence.set_defaults(handler=command_evidence)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        return int(args.handler(args))
    except ProjectError as error:
        print(json.dumps({"error": str(error), "exit_code": error.exit_code}), file=sys.stderr)
        return error.exit_code


if __name__ == "__main__":
    sys.exit(main())
