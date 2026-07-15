#!/usr/bin/env bash
set -euo pipefail

usage='usage: rollback.sh <staging|production> <verified-rollback-digest> <expected-registry> <expected-repository> [expected-sha]
  previous.env is not a verified rollback target; recovery always re-runs full verification.'

environment="${1:?$usage}"
verified_digest="${2:?verified rollback digest is required}"
expected_registry="${3:?expected registry is required}"
expected_repository="${4:?expected repository is required}"
expected_sha="${5:-}"
image_reference="${IMAGE_REFERENCE:-}"

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

digest="$verified_digest"
if [[ "$digest" =~ ^[0-9a-f]{64}$ ]]; then
  digest="sha256:${digest}"
fi
if [[ ! "$digest" =~ ^sha256:[0-9a-f]{64}$ ]]; then
  echo "invalid verified rollback digest: $verified_digest" >&2
  exit 1
fi

if [[ -z "$image_reference" ]]; then
  if [[ -n "$expected_registry" ]]; then
    image_reference="${expected_registry}/${expected_repository}@${digest}"
  else
    image_reference="${expected_repository}@${digest}"
  fi
fi

mkdir -p deploy/state
state="deploy/state/${environment}.env"
previous="deploy/state/${environment}.previous.env"
# previous.env remains a non-authoritative operational cache only.
[[ -f "$state" ]] && cp "$state" "$previous"
printf '%s=%s\n' "$variable" "$image_reference" > "$state"
docker compose --profile deploy --env-file "$state" up -d "$environment"

python_bin="$(resolve_python)"
verify_args=(
  scripts/verify_deployment.py verify
  --base-url "http://localhost:${port}"
  --compose-service "$environment"
  --expected-digest "$digest"
  --expected-registry "$expected_registry"
  --expected-repository "$expected_repository"
  --expected-environment "$environment"
  --mode recovery
)
[[ -n "$expected_sha" ]] && verify_args+=(--expected-sha "$expected_sha")
"$python_bin" "${verify_args[@]}"
