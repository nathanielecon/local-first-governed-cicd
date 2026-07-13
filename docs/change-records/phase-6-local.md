# Change phase-6-local

Authority: fields below MUST obey `docs/phase-6-spec.md` (Phase 6 shared evidence and recovery contract). Do not invent digests, approvers, or rollback targets that are absent from the append-only event log and derived summary manifest. Never record secrets.

## Identity

- Commit SHA: `bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`
- Image digest (immutable promotion identity): `sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`
- Image reference (alias only; not promotion identity): `localhost:5000/delivery-api:sha-bbbbbbbbbbbb`
- Release ID: `phase-6`
- Claim boundary: local-only / production-like (no live cloud / AWS claim unless separately authorized evidence exists)

## Change intent

- Reason: Integrate the Phase 6 Jenkins flow with append-only evidence, identity-bound digest promotion, approval persistence, rollback-target gating, failure injection, and recovery verification (`P6-T04`).
- Expected impact: Local production-like Jenkins contract emits the required event sequence and retains agreeing change-record / events / summary fields.
- Blast radius: Jenkinsfile contract, local evidence under `evidence/phase-6/`, and this change record only. No live cloud, AWS, or organizational Jenkins administration claim.

## Evidence binding (event-backed)

- Append-only event log path: `evidence/phase-6/events.jsonl`
- Derived summary manifest path: `evidence/phase-6/manifest.json`
- Staging verified at (UTC): `2026-07-13T17:10:00Z`
- Production approval:
  - Approver identity: `local-approver`
  - Approved at (UTC): `2026-07-13T17:15:00Z`
- Production verified at (UTC): `2026-07-13T17:25:00Z`

## Rollback / first release

Choose exactly one:

- [x] Verified rollback target bound
  - Previous verified digest: `sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
  - Source release ID: `phase-6-prior-fixture`
  - Verified at (UTC): `2026-07-12T18:00:00Z`
- [ ] First-release decision recorded (no prior verified target)
  - Decided by:
  - Decided at (UTC):
  - Rationale / accepted risk:

## Recovery (if rollback claimed)

- Rollback executed at (UTC): `2026-07-13T17:35:00Z`
- Recovery verification:
  - Deployed digest match: pass
  - Health: pass
  - Version: pass
  - Business behavior: pass
- Recovery evidence path: `evidence/phase-6/events.jsonl` (`recovery_verified` event `p6-local-recovery`); summary `evidence/phase-6/manifest.json`

## Validation evidence

- Paths:
  - `evidence/phase-6/p6-t04-pytest.txt`
  - `evidence/phase-6/p6-t04-validate-jenkinsfile.txt`
  - `evidence/phase-6/p6-t04-validate-state.txt`
  - `evidence/phase-6/p6-t04-evidence-validate.txt`

## Outcome

- Outcome: Local Phase 6 Jenkins integration fixture retained. Contract tests and Jenkinsfile validator pass. Append-only events, derived manifest, and this change record agree on commit, candidate digest, approver, timestamps, and rollback target. This is a local-only / production-like evidence record; it does not claim live cloud, AWS, or sustained production operation. `PC-002` and `PC-003` remain open pending integrated Phase 6 gates.
- Failed checks (if any; preserve evidence, do not weaken gates): none for this local fixture validation set
- Rollback command (digest-targeted; no rebuild between environments): `./scripts/rollback.sh production 'sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' 'localhost:5000' 'delivery-api' 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'`
