# Change <release-id>

Authority: fields below MUST obey `docs/phase-6-spec.md` (Phase 6 shared evidence and recovery contract). Do not invent digests, approvers, or rollback targets that are absent from the append-only event log and derived summary manifest. Never record secrets.

## Identity

- Commit SHA:
- Image digest (immutable promotion identity):
- Image reference (alias only; not promotion identity):
- Release ID:
- Claim boundary: local-only / production-like (no live cloud / AWS claim unless separately authorized evidence exists)

## Change intent

- Reason:
- Expected impact:
- Blast radius:

## Evidence binding (event-backed)

- Append-only event log path:
- Derived summary manifest path:
- Staging verified at (UTC):
- Production approval:
  - Approver identity:
  - Approved at (UTC):
- Production verified at (UTC):

## Rollback / first release

Choose exactly one:

- [ ] Verified rollback target bound
  - Previous verified digest:
  - Source release ID:
  - Verified at (UTC):
- [ ] First-release decision recorded (no prior verified target)
  - Decided by:
  - Decided at (UTC):
  - Rationale / accepted risk:

## Recovery (if rollback claimed)

- Rollback executed at (UTC):
- Recovery verification:
  - Deployed digest match:
  - Health:
  - Version:
  - Business behavior:
- Recovery evidence path:

## Validation evidence

- Paths:

## Outcome

- Outcome:
- Failed checks (if any; preserve evidence, do not weaken gates):
- Rollback command (digest-targeted; no rebuild between environments):
