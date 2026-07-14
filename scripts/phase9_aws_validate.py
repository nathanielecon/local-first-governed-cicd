#!/usr/bin/env python3
"""Phase 9 AWS validation helper: ECR bootstrap → build/push digest → ECS service → smoke."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TF_DIR = ROOT / "infra" / "terraform"
EVIDENCE = ROOT / "evidence" / "phase-9"


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=check,
        text=True,
        capture_output=True,
    )


def run_live(cmd: list[str], *, cwd: Path | None = None) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def tf_output(name: str) -> str:
    proc = run(["terraform", "output", "-raw", name], cwd=TF_DIR)
    return proc.stdout.strip()


def write_evidence(name: str, body: str) -> Path:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE / name
    path.write_text(body if body.endswith("\n") else body + "\n", encoding="utf-8")
    return path


def main() -> int:
    git_sha = run(["git", "rev-parse", "HEAD"], cwd=ROOT).stdout.strip()
    short = git_sha[:12]
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    region = "us-east-1"

    write_evidence(
        f"{stamp}-authorization.txt",
        "\n".join(
            [
                "phase=9",
                "authorization=human-explicit-2026-07-14",
                "region=us-east-1",
                f"git_sha={git_sha}",
                "claim_boundary=live-aws-validation-in-progress",
                "auth_mode=operator-aws-session (OIDC role optional; enable_github_oidc=false)",
            ]
        ),
    )

    run_live(["terraform", "init", "-input=false"], cwd=TF_DIR)
    run_live(
        [
            "terraform",
            "apply",
            "-input=false",
            "-auto-approve",
            "-var",
            f"git_sha={git_sha}",
            "-var",
            "create_service=false",
            "-var",
            f"aws_region={region}",
        ],
        cwd=TF_DIR,
    )
    ecr_url = tf_output("ecr_repository_url")
    account = tf_output("account_id")
    write_evidence(
        f"{stamp}-terraform-bootstrap.txt",
        f"ecr_repository_url={ecr_url}\naccount_id={account}\nregion={region}\n",
    )

    password = run(
        ["aws", "ecr", "get-login-password", "--region", region], cwd=ROOT
    ).stdout.strip()
    login = subprocess.run(
        [
            "docker",
            "login",
            "--username",
            "AWS",
            "--password-stdin",
            f"{account}.dkr.ecr.{region}.amazonaws.com",
        ],
        input=password,
        text=True,
        check=True,
        capture_output=True,
    )
    write_evidence(f"{stamp}-ecr-login.txt", login.stdout + login.stderr)

    local_tag = f"delivery-api:{short}"
    remote_tag = f"{ecr_url}:{short}"
    run_live(
        [
            "docker",
            "build",
            "--build-arg",
            "APP_VERSION=0.1.0",
            "--build-arg",
            f"GIT_SHA={git_sha}",
            "-t",
            local_tag,
            str(ROOT),
        ]
    )
    run_live(["docker", "tag", local_tag, remote_tag])
    run_live(["docker", "push", remote_tag])

    inspect = run(
        [
            "aws",
            "ecr",
            "describe-images",
            "--repository-name",
            "project-c-delivery-api",
            "--image-ids",
            f"imageTag={short}",
            "--region",
            region,
            "--query",
            "imageDetails[0].imageDigest",
            "--output",
            "text",
        ]
    )
    digest = inspect.stdout.strip()
    image_ref = f"{ecr_url}@{digest}"
    write_evidence(
        f"{stamp}-image-digest.txt",
        f"git_sha={git_sha}\nimage_tag={short}\nimage_digest={digest}\nimage_ref={image_ref}\n",
    )

    run_live(
        [
            "terraform",
            "apply",
            "-input=false",
            "-auto-approve",
            "-var",
            f"git_sha={git_sha}",
            "-var",
            "create_service=true",
            "-var",
            f"container_image={image_ref}",
            "-var",
            f"aws_region={region}",
        ],
        cwd=TF_DIR,
    )
    base_url = tf_output("service_base_url")
    write_evidence(f"{stamp}-service-url.txt", f"service_base_url={base_url}\n")

    # Wait for target health / ready
    deadline = time.time() + 300
    last_err = ""
    while time.time() < deadline:
        try:
            probe = run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "smoke_test.py"),
                    "--base-url",
                    base_url,
                    "--expected-sha",
                    git_sha,
                    "--expected-environment",
                    "staging",
                ],
                check=False,
            )
            write_evidence(
                f"{stamp}-smoke-attempt.txt",
                f"exit={probe.returncode}\nstdout=\n{probe.stdout}\nstderr=\n{probe.stderr}\n",
            )
            if probe.returncode == 0:
                write_evidence(
                    f"{stamp}-smoke-pass.txt",
                    f"PASS\nbase_url={base_url}\nexpected_sha={git_sha}\nimage_ref={image_ref}\n",
                )
                manifest = {
                    "phase": 9,
                    "region": region,
                    "git_sha": git_sha,
                    "image_ref": image_ref,
                    "service_base_url": base_url,
                    "smoke": "PASS",
                    "auth_mode": "operator-aws-session",
                    "teardown": "terraform destroy -var git_sha=<sha> -var create_service=true "
                    f"-var container_image={image_ref}",
                    "recorded_at": datetime.now(UTC).isoformat(),
                }
                write_evidence(f"{stamp}-manifest.json", json.dumps(manifest, indent=2))
                print(json.dumps(manifest, indent=2))
                return 0
            last_err = probe.stdout + probe.stderr
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
        time.sleep(15)

    write_evidence(f"{stamp}-smoke-fail.txt", f"FAIL after timeout\n{last_err}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
