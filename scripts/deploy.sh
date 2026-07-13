#!/usr/bin/env bash
set -euo pipefail

usage='usage: deploy.sh <staging|production> <image> [expected-sha]
  Production also requires either verified rollback-target env vars or first-release env vars.
  Optional identity: EXPECTED_DIGEST EXPECTED_REGISTRY EXPECTED_REPOSITORY
  Verified target: VERIFIED_ROLLBACK_DIGEST VERIFIED_ROLLBACK_COMMIT
                   VERIFIED_ROLLBACK_VERIFIED_AT VERIFIED_ROLLBACK_SOURCE_RELEASE
                   VERIFIED_ROLLBACK_ENVIRONMENT (must be production)
  First release: FIRST_RELEASE_DECISION FIRST_RELEASE_DECIDED_BY FIRST_RELEASE_DECIDED_AT
                 FIRST_RELEASE_RATIONALE FIRST_RELEASE_ACCEPTED_RISK'

environment="${1:?$usage}"
image="${2:?image is required}"
expected_sha="${3:-}"
expected_digest="${EXPECTED_DIGEST:-}"
expected_registry="${EXPECTED_REGISTRY:-}"
expected_repository="${EXPECTED_REPOSITORY:-}"

case "$environment" in
  staging) variable=STAGING_IMAGE; port=8081 ;;
  production) variable=PRODUCTION_IMAGE; port=8082 ;;
  *) echo "invalid environment: $environment" >&2; exit 2 ;;
esac

resolve_python() {
  if [[ -x .venv/Scripts/python.exe ]]; then
    echo .venv/Scripts/python.exe
  elif [[ -x .venv/bin/python ]]; then
    echo .venv/bin/python
  else
    echo python3
  fi
}

parse_image_identity() {
  local ref="$1"
  local name digest=""
  if [[ "$ref" =~ ^(.+)@(sha256:[0-9a-f]{64})$ ]]; then
    name="${BASH_REMATCH[1]}"
    digest="${BASH_REMATCH[2]}"
  elif [[ "$ref" =~ ^(.+):([^:/]+)$ ]]; then
    name="${BASH_REMATCH[1]}"
  else
    name="$ref"
  fi
  local registry="" repository="$name"
  if [[ "$name" == */* ]]; then
    registry="${name%%/*}"
    repository="${name#*/}"
  fi
  PARSED_REGISTRY="$registry"
  PARSED_REPOSITORY="$repository"
  PARSED_DIGEST="$digest"
}

parse_image_identity "$image"
[[ -z "$expected_digest" ]] && expected_digest="$PARSED_DIGEST"
[[ -z "$expected_registry" ]] && expected_registry="$PARSED_REGISTRY"
[[ -z "$expected_repository" ]] && expected_repository="$PARSED_REPOSITORY"

python_bin="$(resolve_python)"

if [[ "$environment" == production ]]; then
  if [[ -z "$expected_digest" ]]; then
    echo "production deploy requires EXPECTED_DIGEST or image pinned as registry/repo@sha256:..." >&2
    exit 1
  fi
  "$python_bin" scripts/verify_deployment.py promotion-gate \
    --candidate-digest "$expected_digest" \
    --verified-rollback-digest "${VERIFIED_ROLLBACK_DIGEST:-}" \
    --verified-rollback-commit "${VERIFIED_ROLLBACK_COMMIT:-}" \
    --verified-rollback-verified-at "${VERIFIED_ROLLBACK_VERIFIED_AT:-}" \
    --verified-rollback-source-release "${VERIFIED_ROLLBACK_SOURCE_RELEASE:-}" \
    --verified-rollback-environment "${VERIFIED_ROLLBACK_ENVIRONMENT:-production}" \
    --first-release-decision "${FIRST_RELEASE_DECISION:-}" \
    --first-release-decided-by "${FIRST_RELEASE_DECIDED_BY:-}" \
    --first-release-decided-at "${FIRST_RELEASE_DECIDED_AT:-}" \
    --first-release-rationale "${FIRST_RELEASE_RATIONALE:-}" \
    --first-release-accepted-risk "${FIRST_RELEASE_ACCEPTED_RISK:-}"
fi

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

if [[ -n "$expected_digest" && -n "$expected_registry" && -n "$expected_repository" ]]; then
  verify_args=(
    scripts/verify_deployment.py verify
    --base-url "http://localhost:${port}"
    --compose-service "$environment"
    --expected-digest "$expected_digest"
    --expected-registry "$expected_registry"
    --expected-repository "$expected_repository"
    --expected-environment "$environment"
    --mode verify
  )
  [[ -n "$expected_sha" ]] && verify_args+=(--expected-sha "$expected_sha")
  "$python_bin" "${verify_args[@]}"
else
  smoke_args=(scripts/smoke_test.py --base-url "http://localhost:${port}" --expected-environment "$environment")
  [[ -n "$expected_sha" ]] && smoke_args+=(--expected-sha "$expected_sha")
  "$python_bin" "${smoke_args[@]}"
fi
trap - ERR
