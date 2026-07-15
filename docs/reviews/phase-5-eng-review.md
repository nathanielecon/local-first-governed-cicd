# Phase 5 Engineering Review

Date: 2026-07-12

**Verdict: approved for bounded local Phase 5 implementation of `PC-001` only; `PC-002` and `PC-003` remain hard blockers for Phase 6 evidence and rollback claims.** This review clears local-only remediation design work for externally supplied Jenkins credentials, least-privilege authorization, named production approvers, trusted release-input binding, and an unauthorized-promotion denial proof. It does not approve live production, real cloud, organizational Jenkins administration, append-only release evidence, verified rollback recovery, or closure of the Docker-socket/root exposure.

Reviewed baseline: `PLAN.md`, `STATUS.md`, `ISSUES.md`, `PROJECT.md`, `DECISIONS.md`, `AGENTS.md`, `docs/orchestration.md`, `docs/reviews/eng-review.md`, `docs/TERRA_ORCHESTRATOR_PROMPT.md`, the current `Jenkinsfile`, `compose.yaml`, `infra/jenkins/casc.yaml`, `infra/jenkins/Dockerfile`, `scripts/validate_jenkinsfile.py`, `tests/test_jenkinsfile_contract.py`, `tests/test_compose_static.py`, `README.md`, `docs/runbook.md`, and the retained Phase 3-4 review artifacts. `PLAN.md` and `STATUS.md` were already modified in the working tree when inspected and are outside this task's write scope.

## Scope and dependency boundary

- `PC-001` is the only Phase 5 remediation target in scope. The approved design problem is split into three bounded obligations:
  1. externalize Jenkins credentials and replace administrator-for-all authorization with named least-privilege roles;
  2. remove default administrator credentials from Compose and repository docs so the local stack requires explicit injection;
  3. gate production-like approval to named submitters and a trusted commit input, then prove that unauthorized promotion is denied in a local fixture.
- `PC-002` remains out of scope for Phase 5 implementation. Phase 5 may record local control-test evidence, but it must not claim that staging, approval, and production are durably proven together until Phase 6 introduces append-only release events and approver persistence.
- `PC-003` remains out of scope for Phase 5 implementation. Phase 5 may block unauthorized approval and preserve current rollback limitations, but it must not claim a verified rollback target or restored-state verification until the Phase 6 recovery contract is implemented.
- The current local-only claim boundary remains mandatory: every artifact must describe the result as a production-like local Jenkins exercise, not as real production authority, real cloud validation, or organizational Jenkins governance.

## Findings

| Severity | Finding | Required disposition |
|---|---|---|
| Major | `compose.yaml` still exposes fallback Jenkins administrator values and `README.md` still advertises `admin / change-me-locally`, so the repository currently teaches an insecure shared-default path. | `P5-T02` must remove default credential fallbacks from Compose and documentation, require explicit external injection, and restate the local-only fake-credential boundary. |
| Major | `infra/jenkins/casc.yaml` still uses `loggedInUsersCanDoAnything`, provisions only one repository-controlled administrator, and defines the job checkout as `branch('*/master')`, so neither least-privilege authorization nor trusted commit binding exists yet. | `P5-T01` must define externally supplied placeholder identities and least-privilege roles; `P5-T03` must replace the wildcard branch trust with an explicit trusted commit or controlled reference contract. |
| Major | `Jenkinsfile` records `APPROVED_BY` but does not restrict approval to named submitters, so any authenticated Jenkins user could currently satisfy the production gate if authentication exists. | `P5-T03` must add named-approver restriction and keep approver capture as evidence for the local fixture. |
| Advisory | The Jenkins controller still runs with `user: root`, installs Docker tooling as `root` during image build, and mounts `/var/run/docker.sock` from the host. Even after `PC-001` remediation, this remains a powerful local-control-plane risk. | Preserve this as residual risk in Phase 5 implementation and Phase 5 security review. Phase 5 may constrain scope and document the boundary, but it must not claim controller isolation or safe multi-tenant operation. |
| Validation | `.venv\\Scripts\\python.exe -m pytest -q` currently fails because `tests/test_project_cli.py` still expects Phase 5 to be unauthorized even though `PLAN.md` authorizes through Phase 8. | Do not treat the current full-suite result as passing gate evidence for `P5-T00`. Recommend a narrow harness follow-up or issue entry before any gate that requires the full suite to pass. |

## Approved implementation contract

- Placeholder Jenkins identity strategy:
  - Use placeholder local-only identities and fake credentials only.
  - Keep administrator and production-approver identities distinct.
  - Inject credential values externally; repository source may define required variable names and validation rules, but not usable fallback secrets.
  - Prefer an authorization model that can express named approvers or an explicit approver group without granting blanket administrative power to every authenticated user.
- Named approver requirement:
  - The production approval stage must restrict who may approve, not merely record who clicked approve.
  - Static contract checks must fail if the Jenkinsfile omits submitter restriction, uses only `submitterParameter`, or falls back to an unrestricted `input`.
- Trusted commit input requirement:
  - The delivery job must no longer treat `master`, implicit `HEAD`, or whatever the workspace already contains as a trusted production input.
  - Phase 5 must bind the release candidate to an explicit trusted commit SHA or a controlled reference whose provenance is defined in the local fixture and validator contract.
  - This is a Phase 5 requirement because approval without trusted input still leaves production-like promotion open to the wrong code, even before Phase 6 evidence and rollback work begins.
- Unauthorized promotion denial test:
  - The local fixture must use placeholder accounts only.
  - The proof must show that an unauthorized user cannot advance the production-like stage and that no production deployment step continues after the rejected approval attempt.
  - Evidence may be local logs, local test output, or fixture output only; it must not imply real production or cloud authority.
- Docker socket and root boundary:
  - The controller may remain a local-only privileged fixture in Phase 5 if that is required to preserve the delivery demo.
  - If retained, every review and evidence artifact must say the authorization fix does not eliminate root or Docker-socket risk.
  - Any attempt to claim hardened controller isolation, safe shared-host tenancy, or production-ready host privilege separation is out of scope and would require a later security-focused design review.

## Dispatch recommendation

Implementation may proceed once one short design checkpoint freezes the shared Phase 5 identity contract: external variable names, placeholder admin identity, placeholder named approver identities or group, and the trusted commit/reference shape. After that checkpoint:

1. `P5-T01` should start first because it defines the Jenkins identity and authorization contract that the other slices must consume.
2. `P5-T02` may run in parallel with `P5-T01` after the external variable names are frozen; its scope is non-overlapping and should mirror the exact credential-injection contract established by `P5-T01`.
3. `P5-T03` should begin only after `P5-T01` freezes the approver and trusted-input contract. It may overlap with the later part of `P5-T02`, but it must not invent different approver names, different trust inputs, or different local-only claims.
4. `P5-T04` must remain strictly sequential after `P5-T01`, `P5-T02`, and `P5-T03`, because the unauthorized-promotion fixture depends on the final credential, approver, and trusted-input contract.

## Checks

- `project validate state` - passed.
- `.venv\\Scripts\\python.exe -m pytest -q` - failed: `tests/test_project_cli.py::test_phase_authorization_boundary` still expects Phase 5 dry-run rejection, but the current plan authorizes through Phase 8. This is a harness-alignment defect, not a new Phase 5 architecture blocker, but it prevents the full suite from serving as passing gate evidence for this task until repaired.
