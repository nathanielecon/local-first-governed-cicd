import argparse
import json
import sys
import urllib.error
import urllib.request


def get_json(url: str) -> tuple[int, dict[str, object]]:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--expected-sha")
    args = parser.parse_args()

    ready_status, ready = get_json(f"{args.base_url}/health/ready")
    version_status, version = get_json(f"{args.base_url}/version")
    request = urllib.request.Request(
        f"{args.base_url}/quotes",
        data=json.dumps({"units": 2, "unit_price": 10, "discount_percent": 5}).encode(),
        headers={"content-type": "application/json", "x-request-id": "smoke-test"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        quote = json.load(response)

    failures = []
    if ready_status != 200 or ready != {"status": "ready"}:
        failures.append(f"readiness failed: {ready_status} {ready}")
    if version_status != 200:
        failures.append(f"version failed: {version_status}")
    if args.expected_sha and version.get("git_sha") != args.expected_sha:
        failures.append(f"expected SHA {args.expected_sha}, got {version.get('git_sha')}")
    if quote.get("total") != 19.0:
        failures.append(f"quote contract failed: {quote}")
    print(json.dumps({"ready": ready, "version": version, "quote": quote, "failures": failures}))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
