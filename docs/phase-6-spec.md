# Phase 6 Shared Evidence and Recovery Contract

Status: frozen for `P6-T00` (spec only). Implementation, Jenkinsfile changes, and issue closure are out of scope for this document.

Authority: addresses open issues `PC-002` (append-only release evidence + approver persistence) and `PC-003` (verified rollback target + recovery verification) as **one shared design problem**. This freeze does not resolve, close, or weaken either issue.

Claim boundary: local-only / production-like. This contract defines how a local Jenkins promotion path must prove build-once digest identity, approval, rollback readiness, and recovery. It does **not** authorize or claim live cloud, AWS, organizational Jenkins administration, or sustained production operation.

---

## 1. Purpose

Phase 6 must make the following jointly auditable for one release:

1. Immutable image digest identity used for staging and production promotion.
2. Append-only staging, approval, production, failure, rollback, and recovery events.
3. Named human approver identity and approval timestamp persistence.
4. A verified rollback target, or an explicit first-release decision when none exists.
5. Post-rollback recovery verification of digest, health, version, and business behavior.

Current scaffold gaps this contract freezes against:

- `scripts/evidence.py` overwrites `manifest.json` environment/status fields and does not append durable event history (`PC-002`).
- Jenkins approval identity is not required to persist into release evidence (`PC-002`).
- First production promotion may lack a verified prior digest, and rollback restores a prior env file without proving restored health, version, business behavior, or deployed digest (`PC-003`).

---

## 2. Artifact model

Every release identified by `release_id` MUST retain these artifacts under `evidence/<release_id>/` (or an equivalent retained path recorded by the change record):

| Artifact | Role | Mutability |
| --- | --- | --- |
| `events.jsonl` (or equivalent append-only event log) | Source of truth for what happened | Append-only. Existing lines MUST NOT be edited, rewritten, truncated, or reordered. |
| `manifest.json` (summary) | Derived audit summary for operators and gates | Regenerable from the event log. MUST NOT be treated as an independent source of truth that silently discards history. |
| Change record (`docs/change-records/<release-id>.md`) | Human-readable narrative bound to the same identities | May be written once per release attempt; MUST cite event-backed fields, not invented digests/approvers. |

### 2.1 Append-only release events

Each event is one JSON object per line and MUST include at least:

| Field | Requirement |
| --- | --- |
| `event_id` | Unique within the release event log. |
| `event_type` | One of the allowed types in §2.2. |
| `release_id` | Matches the release directory / change record. |
| `commit_sha` | Trusted release commit identity for this attempt. |
| `image_digest` | Canonical immutable digest for the artifact under discussion, when applicable. |
| `environment` | `staging`, `production`, or `local` as appropriate. |
| `recorded_at` | UTC ISO-8601 timestamp when the event was appended. |
| `actor` | System or human identity responsible for the action (never a secret). |
| `result` | `pass`, `fail`, `blocked`, or `recorded` as applicable. |
| `details` | Structured non-secret context needed to audit the event. |

Events MAY include report paths, probe outputs, and decision references. Events MUST NOT contain credentials, tokens, passwords, or private keys.

### 2.2 Required event sequence (happy path)

A production-like local promotion that claims success MUST be reconstructible from events including, in order of occurrence:

1. `build_published` — image built once; digest resolved and recorded.
2. `staging_deployed` — identical digest deployed to staging.
3. `staging_verified` — staging health, version, business behavior, and deployed digest checks passed.
4. `production_approval` — named approver identity and approval timestamp recorded.
5. `rollback_target_bound` **or** `first_release_decision` — see §4 and §5.
6. `production_deployed` — identical digest deployed to production.
7. `production_verified` — production verification suite passed.

A recovery claim additionally requires:

8. `production_verification_failed` or equivalent failure-injection / failure event (when demonstrating recovery).
9. `rollback_executed` — previous verified digest restored.
10. `recovery_verified` — full recovery verification suite passed against the restored digest.

Missing required events for a claimed outcome is a validation failure (§8).

### 2.3 Derived summary manifest

`manifest.json` MUST be derived from the append-only event log (plus immutable release metadata) and MUST expose at least:

| Summary field | Derivation rule |
| --- | --- |
| `schema_version` | Contract schema identifier for validators. |
| `release_id` | From release metadata / events. |
| `commit_sha` | From trusted build/promotion events; MUST be consistent across events. |
| `image.digest` | Canonical digest from `build_published` / promotion events. |
| `image.reference` | Alias only; NEVER the promotion identity. |
| `staging.status` / timestamps | From staging deploy/verify events. |
| `approvals[]` | From `production_approval` events: approver identity + timestamp required. |
| `production.status` / timestamps | From production deploy/verify events. |
| `rollback_target.digest` | From verified prior production (or staging-as-prior when contractually allowed) state; empty only when a valid first-release decision exists. |
| `first_release_decision` | Present only when no verified rollback target exists and an explicit decision was recorded. |
| `recovery` | Latest recovery verification fields when rollback was claimed. |
| `updated_at` | Derivation time. |

Rules:

- Regenerating the summary from the same event log MUST yield the same semantic content for gate fields.
- Overwriting summary fields without a corresponding appended event is forbidden.
- A summary that disagrees with its event log fails validation.

---

## 3. Digest identity as promotion and rollback source of truth

Accepted decision: **one build, digest promotion**. Tags and Compose image references are aliases only.

### 3.1 Canonical identity

- The immutable container image digest is the sole identity used to prove what was built, staged, approved, promoted, rolled back to, and recovered.
- Promotion from staging to production MUST use the **same** digest recorded at build/staging verification. Rebuilding between environments is forbidden.
- Rollback MUST restore a previously **verified** digest identity, not merely a mutable tag or an unverified prior env-file reference.

### 3.2 Digest consistency rules

Across events and the derived summary for one release attempt:

- All promotion-path events that carry `image_digest` for the candidate release MUST agree on that digest.
- Deployed-digest proof collected during verification MUST match the expected digest for that environment.
- Digest comparison SHOULD bind expected registry/repository identity where local evidence can observe it; selecting an arbitrary first `RepoDigest` without identity checks is insufficient for a verified claim.

### 3.3 Non-identities

The following are **not** acceptable substitutes for digest identity in promotion, approval prompts, rollback targets, or recovery proofs:

- Floating tags alone (`latest`, unpinned branch tags).
- Rebuild of the same commit between staging and production.
- Env-file or Compose reference changes without digest proof.
- Operator verbal claims without event-backed digest fields.

---

## 4. Verified rollback target semantics

A **verified rollback target** is the last image digest that previously completed mandatory verification in the target environment (production for production rollback) and remains recorded in durable evidence.

Minimum fields for a bound rollback target:

| Field | Requirement |
| --- | --- |
| `digest` | Immutable digest of the prior verified release. |
| `commit_sha` | Commit associated with that prior verified release. |
| `verified_at` | Timestamp of the prior successful verification event. |
| `source_release_id` | Release that established the verified state. |
| `environment` | Environment the target is valid for (normally `production`). |

Binding rules:

1. Production promotion is **blocked** unless either:
   - a verified rollback target is bound and recorded (`rollback_target_bound`), or
   - an explicit first-release decision is recorded (§5).
2. A digest that was only built, only staged, only approved, or only partially deployed is **not** a verified rollback target for production recovery claims.
3. Binding an empty, unknown, or self-referential “previous” digest does not satisfy this section.
4. After a successful production verification, that digest becomes eligible to serve as the rollback target for a subsequent release.

---

## 5. First-release decision record

When no verified rollback target exists (typical first production-like promotion), promotion may proceed **only** if an explicit first-release decision is recorded before production deploy.

Required decision fields:

| Field | Requirement |
| --- | --- |
| `decision` | Explicit value such as `first_release_no_rollback_target`. |
| `decided_by` | Named human identity (non-secret). |
| `decided_at` | UTC ISO-8601 timestamp. |
| `rationale` | Short non-secret reason acknowledging absence of a verified prior digest. |
| `accepted_risk` | Explicit acknowledgment that rollback to a prior verified digest is unavailable. |

Rules:

- Absence of both a verified rollback target **and** a first-release decision is a hard promotion failure (§8).
- A first-release decision does **not** waive recovery verification after later releases that do have a prior verified digest.
- First-release is a recorded exception for the missing-target gate only; it is not a blanket approval to skip production verification.

---

## 6. Approver identity and timestamp persistence

`PC-002` requires that staging, approval, and production be jointly provable. Therefore:

1. Production promotion MUST capture the named human approver identity used for the Jenkins (or equivalent) approval gate.
2. The approval MUST be appended as a `production_approval` event containing at least:
   - `approver_id` (or equivalent named identity),
   - `approved_at` (UTC ISO-8601),
   - `commit_sha`,
   - `image_digest` being approved,
   - `result: pass` for a successful approval path.
3. The derived summary `approvals[]` MUST include those identities and timestamps.
4. Change records MUST cite the same approver identity and timestamp; they MUST NOT invent or omit them when a production claim is made.
5. Credentials and passwords MUST never appear in events, manifests, change records, logs retained as evidence, or runbook examples beyond env-var **names**.

An approval that exists only in transient Jenkins UI state and is not persisted into the append-only evidence path does not satisfy this contract.

---

## 7. Mandatory recovery verification

Restoring a previous env file or restarting a container is **not** recovery. After `rollback_executed`, a `recovery_verified` claim requires all of the following checks to pass against the restored target:

| Check | Observable requirement |
| --- | --- |
| Deployed digest | Actual running image digest matches the bound rollback target digest. |
| Health | Liveness and readiness (or project-equivalent health probes) succeed. |
| Version | `/version` (or equivalent) agrees with the restored release identity expectations. |
| Business behavior | Required business endpoint/smoke contract succeeds. |
| Evidence linkage | Recovery event references the rollback target digest and records pass/fail per check. |

### 7.1 Failure boundaries

Treat as a **critical recovery failure** (must fail the release/recovery claim and preserve evidence):

- Any mandatory recovery check fails or is skipped.
- Restored digest does not match the verified rollback target.
- Recovery is claimed without `rollback_executed` + `recovery_verified` events.
- Promotion proceeds with neither verified rollback target nor first-release decision.
- Summary manifest or change record asserts success while required events are missing or contradictory.

On critical recovery failure:

1. Do not destroy failed-release evidence.
2. Do not rebuild or retag to manufacture a matching digest.
3. Record the failing recovery event with failing check names.
4. Escalate per project incident/runbook practice; restored-state verification failure is not a soft warning.

---

## 8. Validation gates and negative examples

Validators and independent reviews MUST fail closed on at least these negatives:

| Negative | Required outcome |
| --- | --- |
| Missing required events for a claimed stage (e.g., production verified without staging verified / approval) | Reject the claim. |
| Digest inconsistency across build, staging, approval, production, or recovery events | Reject the claim. |
| Missing approval event or missing approver identity/timestamp when production promotion is claimed | Reject the claim. |
| No verified rollback target **and** no first-release decision before production deploy | Block promotion / reject the claim. |
| Rollback without recovery verification fields/results | Reject recovery claim. |
| Summary manifest fields that cannot be derived from the event log | Reject the evidence set. |
| Secrets present in events, manifests, or change records | Reject; remediate without weakening gates. |
| Live cloud / AWS / production-org claims without corresponding authorized evidence | Out of scope; do not accept under this Phase 6 local contract. |

Passing CI or a green Jenkins stage alone is insufficient. Artifact identity, environment state, approval persistence, verification, and recovery must all be evidenced.

---

## 9. Operator and change-record obligations

- `docs/change-records/TEMPLATE.md` and release change records MUST bind commit, digest, approver/time, rollback target or first-release decision, validation evidence paths, and outcome to this contract.
- `docs/runbook.md` MUST instruct operators to use digest identity, preserve append-only evidence, refuse promotion without target/decision, and fully verify recovery.
- Implementation slices (`P6-T02`–`P6-T04`) MUST implement against this freeze; they MUST NOT redefine digest identity or weaken the negative gates above.
- Independent eng review (`P6-T01`) reviews this shared design before implementation.

---

## 10. Explicit non-goals for this freeze

- No implementation of `scripts/evidence.py`, deploy/rollback scripts, or `Jenkinsfile` in `P6-T00`.
- No resolution of `PC-002` / `PC-003` in the issue ledger from this document alone.
- No change to Phase 5 residual risks (Docker socket/root, `cpsScm` tip) beyond acknowledging they remain outside this evidence/recovery contract.
- No live registry, AWS, or production-org operational claims.

---

## 11. Acceptance mapping

| `P6-T00` acceptance criterion | Contract section |
| --- | --- |
| Append-only events and a derived summary manifest | §2 |
| Verified rollback target and explicit first-release decision record | §4, §5 |
| Mandatory recovery verification fields and failure boundaries | §7, §8 |
| Digest identity as promotion/rollback source of truth | §3 |
| Approver identity / timestamp persistence | §6 |
| Negatives: missing events, digest mismatch, missing approval, missing target+decision | §8 |
| Local-only / production-like claim boundary | header, §10 |
