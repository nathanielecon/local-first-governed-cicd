import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update a release evidence manifest")
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--image-ref", default="")
    parser.add_argument("--image-digest", default="")
    parser.add_argument("--rollback-digest", default="")
    parser.add_argument("--environment", default="local")
    args = parser.parse_args()

    directory = Path("evidence") / args.release_id
    directory.mkdir(parents=True, exist_ok=True)
    manifest_path = directory / "manifest.json"
    existing = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest = {
        **existing,
        "schema_version": "1.0",
        "release_id": args.release_id,
        "status": args.status,
        "commit_sha": args.commit_sha,
        "image": {"reference": args.image_ref, "digest": args.image_digest},
        "environment": args.environment,
        "rollback_digest": args.rollback_digest,
        "pipeline": {
            "provider": os.getenv("CI_PROVIDER", "local"),
            "run_id": os.getenv("BUILD_TAG", os.getenv("GITHUB_RUN_ID", "manual")),
        },
        "approvals": existing.get("approvals", []),
        "reports": existing.get("reports", []),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(manifest_path)


if __name__ == "__main__":
    main()
