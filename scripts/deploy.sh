#!/usr/bin/env bash
set -euo pipefail

environment="${1:?usage: deploy.sh <staging|production> <image> [expected-sha]}"
image="${2:?image is required}"
expected_sha="${3:-}"
case "$environment" in
  staging) variable=STAGING_IMAGE; port=8081 ;;
  production) variable=PRODUCTION_IMAGE; port=8082 ;;
  *) echo "invalid environment: $environment" >&2; exit 2 ;;
esac

mkdir -p deploy/state
state="deploy/state/${environment}.env"
previous="deploy/state/${environment}.previous.env"
[[ -f "$state" ]] && cp "$state" "$previous"
printf '%s=%s\n' "$variable" "$image" > "$state"

rollback() {
  if [[ -f "$previous" ]]; then
    cp "$previous" "$state"
    docker compose --profile deploy --env-file "$state" up -d "$environment"
  fi
}
trap rollback ERR
docker compose --profile deploy --env-file "$state" up -d "$environment"
args=(scripts/smoke_test.py --base-url "http://localhost:${port}")
[[ -n "$expected_sha" ]] && args+=(--expected-sha "$expected_sha")
python3 "${args[@]}"
trap - ERR

