# Phase 3 Engineering Review

**Verdict: approved for bounded daemon-independent implementation; runtime
verification remains blocked by PC-004.**  This is not approval to run Docker,
Compose, a registry, Jenkins, a deployment, or any cloud service.  The review was
performed against commit `7f0e2b9afd5a4bc66b6505da89073d8783e16e6a` plus the
authoritative Phase 3 plan state.  `PLAN.md` and `STATUS.md` were already modified
by the orchestrator when inspected and are outside this review's write scope.

## Scope and identity

- `Dockerfile` defines a two-stage Python 3.12.11 image, passes `APP_VERSION` and
  `GIT_SHA` through build arguments into OCI labels and runtime environment, and
  selects UID/GID 10001 before the service command.  Phase 3 must prove, with a
  built image rather than source inspection, that `/version` reports the supplied
  SHA and version and that the process has no root privileges.
- The base-image tags and `registry:2.8.3` are version-pinned but not immutable
  digest references.  The Phase 3 reproducibility evidence must record the
  resolved base and final image digests; a later implementation decision must not
  claim byte-for-byte reproducibility merely from these mutable tags.
- `compose.yaml` separates the registry from `deploy`-profile staging and
  production services on the `delivery` network, with distinct host ports.  The
  application services accept image references through environment substitution;
  no tag is to become the promotion identity.  Runtime evidence must record the
  exact image digest actually used by each service.

## Security, failure, and evidence boundaries

- The application runtime is non-root.  The existing Jenkins service is explicitly
  excluded from Phase 3 remediation: its root user, Docker socket mount, and
  default administrator fallback remain PC-001 / Phase 5 concerns.  Nothing in
  Phase 3 may start or harden Jenkins as a substitute for that remediation.
- The readiness health check calls `/health/ready`; smoke must additionally assert
  `/version`, a successful quote calculation, expected SHA when supplied, and a
  negative not-ready path.  `scripts/smoke_test.py` currently exposes connection
  failures directly and deployment wrappers restore only the previous configured
  image; neither behavior may be called a verified rollback.  Phase 3 may record
  the failure evidence and restore attempt, while PC-003 continues to govern a
  proven rollback target and restored-service verification in Phase 6.
- Retained Phase 3 evidence must include raw build output, image inspect identity
  and user, resolved digests, Compose configuration, service/log inspection,
  smoke output, and negative-path output.  It must exclude credentials, request
  bodies beyond the synthetic smoke payload, and unsupported staging, production,
  GitHub, Jenkins, registry-publication, rollback, or cloud success claims.

## Execution boundary

The following work is safe without a Docker Linux engine and may be dispatched in
non-overlapping scopes after PC-008 is repaired: static Dockerfile/Compose
hardening and corresponding source-level tests; smoke-script unit/negative-path
tests; and a read-only container configuration/threat review.  Their scopes must
not overlap `Dockerfile`, `compose.yaml`, smoke scripts/tests, or the review file.

The following work **must wait for PC-004**: `docker build`; Compose syntax or
topology execution through Docker; image inspection; non-root execution proof;
health-check execution; registry interaction; staging/production service startup;
runtime logs; smoke execution against a container; and any runtime evidence or
claim.  PC-004 remains open and requires a functioning Docker Desktop Linux
engine; this review did not invoke Docker or Compose.

## Findings

| Severity | Finding | Required disposition |
|---|---|---|
| Major | Versioned image tags do not themselves provide immutable build inputs or promotion identity (`Dockerfile:2,9`; `compose.yaml:4`). | Capture resolved base/final digests and use a final immutable digest in runtime evidence. |
| Major | Smoke and deployment restoration do not verify restored health/version/business behavior (`scripts/smoke_test.py`, `scripts/deploy.ps1`, `scripts/deploy.sh`). | Exercise and retain Phase 3 smoke/negative behavior once PC-004 clears; retain PC-003 for the complete rollback proof. |
| Resolved validation | The Phase-authorization regression test was stale after Phase 3 authorization. | PC-008 now accepts Phase 3, rejects Phase 4 with the human-gate exit code, and is covered by the fresh full-suite result below. |

## Checks

- `project validate state` — passed.
- `python -m pytest -q` — not used as passing evidence: the shell Python lacks
  `pytest-cov`, so it cannot load the declared coverage parameters.
- `.venv\\Scripts\\python.exe -m pytest -q` — passed: 14 passed, 96.59% coverage.
  The repaired authorization test accepts Phase 3 and confirms that Phase 4 is
  rejected with the documented human-gate exit code.  FastAPI emitted 32 known
  coroutine deprecation warnings; they are non-blocking and retain the Phase 2
  retrospective follow-up boundary.

No critical architectural finding was identified.  PC-008 is resolved and this
review is ready for the orchestrator's review transition.  The orchestrator may
now dispatch the following non-overlapping daemon-independent slices: (1) static
Dockerfile hardening plus source-level assertions, with exclusive `Dockerfile` and
its tests; (2) Compose topology and configuration validation, with exclusive
`compose.yaml` and its tests; (3) smoke-script negative-path tests, with exclusive
`scripts/smoke_test.py` and its tests; and (4) read-only container
configuration/threat review in its own review artifact.  No slice may invoke
Docker or Compose, mutate Jenkins assets, or claim runtime success.  PC-004 still
blocks every container-runtime lane.
