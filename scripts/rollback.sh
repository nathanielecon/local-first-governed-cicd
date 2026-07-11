#!/usr/bin/env bash
set -euo pipefail
environment="${1:?usage: rollback.sh <staging|production>}"
state="deploy/state/${environment}.env"
previous="deploy/state/${environment}.previous.env"
[[ -f "$previous" ]] || { echo "No rollback target for $environment" >&2; exit 1; }
cp "$previous" "$state"
docker compose --profile deploy --env-file "$state" up -d "$environment"

