import argparse
import http.client
import json
import sys
import urllib.error
import urllib.request


def get_json(target: str | urllib.request.Request) -> tuple[int | None, object | None, str | None]:
    try:
        with urllib.request.urlopen(target, timeout=5) as response:
            return response.status, json.load(response), None
    except urllib.error.HTTPError as error:
        try:
            payload = json.load(error)
        except json.JSONDecodeError:
            payload = None
        return error.code, payload, str(error)
    except urllib.error.URLError as error:
        return None, None, str(error.reason)
    except http.client.RemoteDisconnected as error:
        return None, None, str(error)


def validate_version_contract(version: object) -> list[str]:
    if not isinstance(version, dict):
        return [f"version payload is not an object: {version!r}"]

    failures = []
    if version.get("name") != "delivery-api":
        failures.append(f"version name failed: {version.get('name')!r}")

    for field in ("version", "git_sha", "environment"):
        value = version.get(field)
        if not isinstance(value, str) or not value.strip():
            failures.append(f"version field {field} failed: {value!r}")

    return failures


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--expected-sha")
    parser.add_argument("--expected-environment")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    live_status, live, live_error = get_json(f"{args.base_url}/health/live")
    ready_status, ready, ready_error = get_json(f"{args.base_url}/health/ready")
    version_status, version, version_error = get_json(f"{args.base_url}/version")
    request = urllib.request.Request(
        f"{args.base_url}/quotes",
        data=json.dumps({"units": 2, "unit_price": 10, "discount_percent": 5}).encode(),
        headers={"content-type": "application/json", "x-request-id": "smoke-test"},
    )
    quote_status, quote, quote_error = get_json(request)

    failures = []
    if live_status != 200 or live != {"status": "live"}:
        failures.append(f"liveness failed: {live_status} {live}")
    if live_error:
        failures.append(f"liveness error: {live_error}")
    if ready_status != 200 or ready != {"status": "ready"}:
        failures.append(f"readiness failed: {ready_status} {ready}")
    if ready_error:
        failures.append(f"readiness error: {ready_error}")
    if version_status != 200:
        failures.append(f"version failed: {version_status}")
    if version_error:
        failures.append(f"version error: {version_error}")
    failures.extend(validate_version_contract(version))
    version_sha = version.get("git_sha") if isinstance(version, dict) else None
    version_environment = version.get("environment") if isinstance(version, dict) else None
    if args.expected_sha and version_sha != args.expected_sha:
        failures.append(f"expected SHA {args.expected_sha}, got {version_sha}")
    if args.expected_environment and version_environment != args.expected_environment:
        failures.append(
            f"expected environment {args.expected_environment}, got {version_environment}"
        )
    if quote_status != 200:
        failures.append(f"quote failed: {quote_status}")
    if quote_error:
        failures.append(f"quote error: {quote_error}")
    if not isinstance(quote, dict) or quote.get("total") != 19.0:
        failures.append(f"quote contract failed: {quote}")

    health_pass = not any(
        item.startswith("liveness ") or item.startswith("readiness ") for item in failures
    )
    version_pass = not any(
        item.startswith("version ")
        or item.startswith("expected SHA ")
        or item.startswith("expected environment ")
        for item in failures
    )
    business_pass = not any(item.startswith("quote ") for item in failures)

    print(
        json.dumps(
            {
                "live": live,
                "ready": ready,
                "version": version,
                "quote": quote,
                "failures": failures,
                "checks": {
                    "health": "pass" if health_pass else "fail",
                    "version": "pass" if version_pass else "fail",
                    "business_behavior": "pass" if business_pass else "fail",
                },
                "statuses": {
                    "live": live_status,
                    "ready": ready_status,
                    "version": version_status,
                    "quote": quote_status,
                },
            }
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
