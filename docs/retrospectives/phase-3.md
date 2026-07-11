# Phase 3 Retrospective: Container and Local Runtime Delivery Cycle

Date: 2026-07-11
Scope: Phase 3 image, Compose, smoke-helper, runtime verification, review, QA, and integrated-evidence work.
Baseline: `7f0e2b9afd5a4bc66b6505da89073d8783e16e6a`

## Expected Versus Actual

| Area | Expected | Actual | Evidence |
| --- | --- | --- | --- |
| Engine-independent implementation | Complete the approved static Phase 3 slices without invoking Docker or Compose. | The image contract, Compose topology, smoke-helper contract, threat review, change review, security review, QA, and integrated evidence gate all completed with mutually consistent static-only conclusions. | `STATUS.md`; `evidence/phase-3/image-static.txt`; `evidence/phase-3/compose-static.txt`; `evidence/phase-3/smoke-static.txt`; `evidence/phase-3/qa.txt`; `evidence/phase-3/integrated-gate.txt` |
| Runtime recovery and verification | Resume runtime-dependent validation only after real Docker Linux engine evidence exists. | The first runtime attempts were correctly blocked by `PC-004`. After WSL installation and a clean Docker Desktop restart, the runtime lane completed image build, Compose startup, expected-SHA smoke success for staging and production, non-root inspection, and a confirmed not-ready negative path before restoring readiness. | `evidence/phase-3/runtime/repair-log.txt`; `evidence/phase-3/runtime/install-wsl-elevated.log`; `evidence/phase-3/runtime/build.txt`; `evidence/phase-3/runtime/compose-ps.txt`; `evidence/phase-3/runtime/staging-smoke.txt`; `evidence/phase-3/runtime/production-smoke.txt`; `evidence/phase-3/runtime/not-ready-smoke.txt`; `evidence/phase-3/runtime/staging-restored-smoke.txt`; `evidence/phase-3/runtime/summary.txt` |
| Authorization and QA consistency | The Phase 3 harness and full suite should match the newly authorized phase boundary. | An earlier regression (`PC-008`) was caught and repaired before it contaminated later gates. The retained harness report shows 7 passed, and the wider QA evidence shows 30 passed with the expected warnings only. | `ISSUES.md` (`PC-008`); `evidence/phase-3/harness.txt`; `evidence/phase-3/qa.txt` |

No GitHub-hosted validation, Jenkins startup, production approval, rollback recovery, or cloud activity occurred in this cycle, and none is inferred here.

## What Went Well

- The Phase 3 work was decomposed cleanly into engine-independent slices, which let image semantics, Compose topology, smoke-helper behavior, and review artifacts progress in parallel without overlapping write scope or requiring Docker availability.
- The retained evidence set is unusually coherent for a static wave: focused reports show `6 passed` for Dockerfile assertions, `6 passed` for Compose assertions, `4 passed` for smoke-helper assertions, and the broader QA suite records `30 passed`, which the independent reviews reused instead of restating unverified runtime claims.
- Review discipline held the boundary line. The threat review, change review, security review, and integrated gate all converged on the same narrow claim: Phase 3 engine-independent work is acceptable, while runtime proof remains out of scope until `PC-004` is cleared.
- The runtime repair path stayed evidence-backed. The lane did not pretend the Docker Linux engine worked until `docker info` succeeded, and once it did, the evidence captured both successful ready-state smoke and the deliberate not-ready negative path before restoring the service.

## Rework and Risks Found Early

### PC-008 — authorization harness drift was caught before downstream gates

- **Symptom:** the CLI regression still expected Phase 3 to be rejected after the plan had already authorized through Phase 3.
- **Why it mattered:** if this had survived into later QA and evidence gates, every passing claim would have been suspect for the same reason Phase 2 needed repair.
- **What limited the blast radius:** the narrow harness check was repaired early, and `evidence/phase-3/harness.txt` now records the intended contract: Phase 3 accepted, Phase 4 rejected with the human-gate exit code.

### Runtime recovery required real environment repair, not documentation

- **`PC-004` impact:** treating Docker Linux engine availability as a hard precondition prevented false runtime claims, but it also forced the phase to wait for a real host repair path. The successful fix required both WSL installation and a clean Docker Desktop restart before the engine became usable.
- **Smoke-helper defect found under real runtime churn:** the first negative-path runtime rerun exposed an uncaught `http.client.RemoteDisconnected` condition. Fixing that in `scripts/smoke_test.py` and covering it in `tests/test_smoke_tool.py` kept the runtime evidence readable instead of producing a traceback at exactly the wrong time.
- **`PC-003` and `PC-001` impact:** rollback verification and Jenkins authorization remain future-phase risk areas. Keeping those findings explicit in Phase 3 avoided accidental scope creep and prevented the runtime wave from being misread as promotion or authorization hardening success.

## Follow-up Actions

| Action | Owner | Acceptance criterion | Target phase |
| --- | --- | --- | --- |
| Keep the authorization-boundary regression paired with every future phase transition. | `future-phase-4-harness-worker` | The narrow CLI test explicitly proves the currently authorized phase succeeds and the next phase fails with the documented human-gate exit code, and fresh raw evidence is retained before integrated gates run. | Next authorization change |
| Reuse the runtime evidence pattern for GitHub-hosted proof. | `future-phase-4-workflow-worker` | Hosted validation evidence distinguishes local workflow hardening from real external execution and retains both a passing lane and a safe blocked-change demonstration without implying branch-protection changes. | Phase 4 |
| Turn the retained rollback boundary into a verifiable recovery contract. | `future-phase-6-recovery-worker` | Promotion cannot proceed without a verified rollback target or explicit first-release decision, and rollback evidence proves restored digest, health, version, and business behavior rather than only reverting a configured image reference. | Phase 6 |

## Evidence Index

- `evidence/phase-3/harness.txt` — repaired authorization boundary evidence: 7 passed.
- `evidence/phase-3/image-static.txt` — Dockerfile static contract evidence: 6 passed.
- `evidence/phase-3/compose-static.txt` — Compose topology static contract evidence: 6 passed.
- `evidence/phase-3/smoke-static.txt` — smoke-helper negative-path and release-identity evidence: 4 passed.
- `evidence/phase-3/qa.txt` — combined engine-independent QA suite: 30 passed.
- `evidence/phase-3/integrated-gate.txt` — integrated static-only gate preserving `PC-004` as the only active Phase 3 runtime blocker.
- `evidence/phase-3/runtime/summary.txt` — runtime completion summary including the repair path, build, Compose, smoke, and negative-path evidence.
- `docs/reviews/phase-3-threat-review.md` — boundary review retaining `PC-001`, `PC-003`, and `PC-004`.
- `docs/reviews/phase-3-change-review.md` — independent change review limited to engine-independent scope.
- `docs/reviews/phase-3-security-review.md` — independent security review limited to engine-independent scope.
