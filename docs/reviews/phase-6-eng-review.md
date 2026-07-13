# Phase 6 Engineering Review

Date: 2026-07-13

Reviewer role: independent Phase 6 engineering gate (`P6-T01`), fresh context.

**Verdict: CLEAR for bounded Phase 6 implementation of the shared `PC-002` + `PC-003` design.** This review approves the frozen contract in `docs/phase-6-spec.md` (plus aligned `docs/change-records/TEMPLATE.md` and `docs/runbook.md`) as the implementation baseline, with the explicit constraints below. It does **not** resolve, close, or weaken `PC-002` or `PC-003`. It does **not** authorize live cloud, AWS, organizational Jenkins administration, sustained production operation, or any claim beyond local-only / production-like evidence.

Reviewed baseline: `PROJECT.md`, `PLAN.md`, `STATUS.md`, `ISSUES.md` (`PC-002`, `PC-003`), `DECISIONS.md`, `AGENTS.md`, `docs/phase-6-spec.md`, `docs/change-records/TEMPLATE.md`, `docs/runbook.md`, `scripts/evidence.py`, `Jenkinsfile`, `scripts/deploy.ps1`, `scripts/deploy.sh`, `scripts/rollback.ps1`, `scripts/rollback.sh`, `scripts/smoke_test.py`, prior `docs/reviews/eng-review.md` / `docs/reviews/phase-5-eng-review.md`.

---

## Scope

`PC-002` and `PC-003` are one shared design problem:

| Issue | Design obligation approved here |
| --- | --- |
| `PC-002` | Append-only release events + derived summary; persist named approver identity and approval timestamp so staging, approval, and production are jointly auditable. |
| `PC-003` | Production promotion blocked unless a verified rollback target is bound **or** an explicit first-release decision is recorded; any claimed rollback must fully verify restored digest, health, version, and business behavior. |

Implementation slices `P6-T02` / `P6-T03` / `P6-T04` may proceed only against this approved baseline. Do not start them by redefining digest identity, inventing a second rollback SoT, or treating Phase 5 local approval fixtures as Phase 6 release-evidence proof.

---

## Trace: commit → digest → staging → approval → production → rollback

Approved end-to-end identity chain for a local production-like claim:

1. **Trusted commit** — immutable `TRUSTED_GIT_SHA` (already Phase 5 local contract); release events carry the same `commit_sha`.
2. **Build once** — single image build; record `build_published` with canonical immutable `image_digest`.
3. **Staging** — deploy and verify that **same** digest; record `staging_deployed` / `staging_verified` with matching digest proof.
4. **Approval** — named human approver; append `production_approval` with `approver_id`, `approved_at`, `commit_sha`, and approved `image_digest`. Transient Jenkins UI state alone is insufficient.
5. **Rollback readiness gate** — before production deploy, append exactly one of:
   - `rollback_target_bound` (verified prior production digest from durable evidence), or
   - `first_release_decision` (explicit named decision when no verified prior exists).
6. **Production** — promote the **same** digest; record `production_deployed` / `production_verified`.
7. **Rollback / recovery (when claimed)** — restore the bound verified digest; record `rollback_executed` then `recovery_verified` only after digest, health, version, and business checks all pass.

Tags, Compose image strings, and `deploy/state/*.env` values are **aliases or operational caches**, never promotion or rollback identity.

---

## Approved baseline (must not be reinterpreted by implementers)

### Digest identity

- Accepted decision remains: **one build, digest promotion** (`DECISIONS.md`).
- Canonical promotion / rollback / recovery identity is the immutable image digest recorded in append-only events.
- Rebuild between staging and production is forbidden.
- Floating tags alone are forbidden as promotion or rollback identity.
- Digest selection and deployed-digest proof **MUST** bind expected registry/repository identity where local evidence can observe it. Selecting an arbitrary first `RepoDigest` without that identity check is insufficient for a verified Phase 6 claim (this hardens the freeze text’s “SHOULD” for implementation gates; it matches `P6-T03` acceptance).

### Rollback-target source of truth

- **Source of truth:** the last digest that completed mandatory **production** verification (or a later successful `recovery_verified` restoring that production identity) and remains recorded in durable append-only release evidence / derived summary fields required by the freeze.
- Required bound fields remain those in `docs/phase-6-spec.md` §4: `digest`, `commit_sha`, `verified_at`, `source_release_id`, `environment`.
- **`deploy/state/<env>.previous.env` is not a verified rollback target.** It may be used only as a non-authoritative operational restore helper. Gates, change records, and recovery claims MUST bind the event-backed verified digest, not merely the previous env-file contents.
- **Self-referential, empty, unknown, only-staged, only-approved, or only-partially-deployed digests do not qualify.**

### First-release decision

- When no verified production rollback target exists, promotion may proceed only after an explicit first-release decision event with the freeze-required fields (`decision`, `decided_by`, `decided_at`, `rationale`, `accepted_risk`).
- First-release waives **only** the missing-target gate. It does not waive staging verification, named approval persistence, production verification, or later recovery requirements once a verified prior digest exists.

### Staging-as-prior (freeze ambiguity closed by this review)

- The freeze phrase “or staging-as-prior when contractually allowed” is **not approved** for production rollback claims in Phase 6.
- For production promotion and production recovery claims, only a **verified prior production** digest (or a valid first-release decision) satisfies the gate.
- Implementers must not invent a staging-digest rollback path for production without a new engineering review.

### Evidence model

- `events.jsonl` (or equivalent append-only log) is the event source of truth; `manifest.json` is a regenerable derived summary.
- Overwriting summary/environment fields without a corresponding appended event remains forbidden (current `scripts/evidence.py` behavior is the defect `PC-002` targets).
- Approver identity and approval timestamp MUST appear in `production_approval` events and derived `approvals[]`, and MUST be cited by change records.
- Secrets must never appear in events, manifests, change records, or retained evidence logs.

### Recovery

- Restoring an env file or restarting a container is not recovery.
- Any path that claims successful rollback/recovery (including pipeline failure-injection demos) MUST emit `rollback_executed` + `recovery_verified` and pass digest, health, version, and business checks against the bound target.
- Failed evidence must be preserved; rebuilding/retagging to manufacture a matching digest is forbidden.

### Claim boundary

- Local-only / production-like only.
- Phase 5 residual risks (Docker socket / root controller, `cpsScm` tip) remain outside this evidence/recovery contract and are not cleared here.

---

## Challenges and findings

| Severity | Finding | Affected artifact | Disposition |
| --- | --- | --- | --- |
| Critical (known open) | Manifest overwrite + missing durable approval persistence prevent joint staging/approval/production proof. | `scripts/evidence.py`, `Jenkinsfile` | Remains `PC-002`. Design freeze addresses it; implementation in `P6-T02`/`P6-T04`. **Do not close.** |
| Critical (known open) | First promotion may lack verified rollback digest; rollback restores env file without proving restored digest/health/version/business behavior. | `Jenkinsfile`, `scripts/deploy.*`, `scripts/rollback.*` | Remains `PC-003`. Design freeze addresses it; implementation in `P6-T03`/`P6-T04`. **Do not close.** |
| Major (scaffold, in-scope for Phase 6) | Production stage currently derives `ROLLBACK_DIGEST` from `deploy/state/production.env` and can promote with an empty prior digest and no first-release decision. | `Jenkinsfile` | Must be replaced by event-backed bind **or** first-release decision before production deploy (`P6-T04` after `P6-T02`/`P6-T03`). |
| Major (scaffold, in-scope) | `APPROVED_BY` is captured by Jenkins `input` but never appended into release evidence. | `Jenkinsfile`, `scripts/evidence.py` | Must persist into `production_approval` events (`P6-T02`/`P6-T04`). |
| Major (scaffold, in-scope) | Build digest capture uses first `RepoDigest` without registry/repository identity binding. | `Jenkinsfile` | Must satisfy approved digest-identity rule above (`P6-T03`/`P6-T04`). |
| Major (design ambiguity, closed here) | Freeze §2.3 mentions “staging-as-prior when contractually allowed” without rules. | `docs/phase-6-spec.md` §2.3 | **Rejected for production claims** by this review’s approved baseline. No new issue required unless a later change proposes reopening it. |
| Advisory | Local deploy/evidence paths lack cross-process locking; concurrent non-Jenkins writers could race appends or state files. | `scripts/deploy.*`, future `events.jsonl` writers | Acceptable for local-only demo while Jenkins keeps `disableConcurrentBuilds()`. Document residual race risk; do not claim multi-writer safety. |
| Advisory | Workspace `cleanWs` after archive can still lose unarchived local evidence on archive failure. | `Jenkinsfile` `post` | Preserve/fail closed on missing required evidence artifacts; do not weaken gates. |
| Advisory | Controller still runs privileged with host Docker socket. | `compose.yaml`, Jenkins image | Residual Phase 5 risk; out of Phase 6 evidence/recovery scope; keep local-only claims honest. |

No **new** critical finding and no remaining undecided architecture path that blocks `P6-T02`/`P6-T03` after the staging-as-prior and rollback-SoT constraints above. No new issue is recommended for orchestrator open at this gate.

---

## Required tests (implementation gates)

Implementers and later QA must fail closed on at least:

1. **Append-only evidence** — rewriting/truncating prior events, or summary fields that cannot be derived from the event log, fails validation.
2. **Missing/inconsistent digest** — disagreement across build, staging, approval, production, or recovery events fails.
3. **Missing approval persistence** — production claim without `production_approval` approver identity + timestamp fails.
4. **Missing target + decision** — production deploy/claim with neither verified rollback target nor first-release decision fails.
5. **Invalid rollback target** — empty, self-referential, staging-only, or env-file-only “previous” image rejected as verified production rollback target.
6. **Recovery incompleteness** — rollback claim without deployed-digest, health, version, and business checks fails; skipped checks fail.
7. **Registry/repository-bound digest proof** — arbitrary first `RepoDigest` / unbound digest proof fails verified claims.
8. **Secret leakage** — credentials in events/manifests/change records fail.
9. **Claim boundary** — artifacts must not assert live cloud / AWS / org-production authority from this local path.

Minimum automated coverage expected by slice:

- `P6-T02`: evidence append + summary derivation + CLI/validator negatives for missing events, digest mismatch, missing approval.
- `P6-T03`: promotion gate for target-or-decision; recovery suite negatives; deployed digest identity binding.
- `P6-T04`: Jenkins contract/integration emitting the required event sequence, same digest promotion, and agreeing change-record / events / summary fields.

---

## Dispatch recommendation

1. Keep `PC-002` and `PC-003` **open** until integrated Phase 6 evidence proves the contract end to end.
2. After this gate is recorded clear by the orchestrator, `P6-T02` and `P6-T03` may proceed in parallel because write scopes do not overlap; both must consume this approved baseline (especially event-backed rollback SoT and rejected staging-as-prior).
3. `P6-T04` remains sequential after both implementation slices.
4. Do not reopen Phase 5 authorization work to “solve” evidence/recovery; do not treat Phase 5 unauthorized-approval fixtures as Phase 6 append-only or rollback proof.

---

## Validation executed by this review

| Command | Result |
| --- | --- |
| `project validate state` (via `.venv\Scripts\python.exe scripts\project_cli.py validate state`) | Passed |
| `.venv\Scripts\python.exe -m pytest -q` | Passed — 75 tests |

These checks confirm harness/state health for the review lane. They do **not** prove Phase 6 evidence or recovery implementation.

---

## Final gate statement

**CLEAR** for Phase 6 shared-design implementation under the approved baseline above.

- Approved freeze artifacts: `docs/phase-6-spec.md`, `docs/change-records/TEMPLATE.md`, `docs/runbook.md`.
- Approved identities: immutable image digest; event-backed verified production rollback target **or** explicit first-release decision.
- Unresolved issues that remain mandatory blockers until evidenced: `PC-002`, `PC-003`.
- Continue lanes after orchestrator records this gate: `P6-T02`, `P6-T03` (then `P6-T04`).
- Blocked lanes: none for design reasons; live-cloud / AWS / Phase 9 remain unauthorized.
