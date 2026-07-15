# Change phase-5-local

Authority: Phase 5 integrated evidence and unauthorized-denial fixture. This assembly pointer does not invent digests or production approvals. Prefer `evidence/phase-5/integrated-gate.txt` as the governing local summary. Named production-like approval with persisted timestamps belongs to Phase 6 (`phase-6-local.md`), not this record.

## Identity

- Release ID: `phase-5-local`
- Claim boundary: local-only (no live production, cloud, digest promotion beyond Phase 5 authz scope, or Phase 6 recovery claim)
- Record role: Phase 8 portfolio pointer (`P8-T01`)

## Change intent

- Reason: Local Jenkins authorization remediation (`PC-001`): external credentials, least-privilege roles, named approvers, immutable `TRUSTED_GIT_SHA`, unauthorized denial without production continuation.
- Expected impact: Portfolio can cite authorization and denial path under Locally verified taxonomy.
- Blast radius: Phase 5 Casc/Jenkinsfile/Compose identity wiring and retained fixture proofs.

## Evidence binding

- Governing gate: `evidence/phase-5/integrated-gate.txt`
- Unauthorized denial proof: `evidence/phase-5/p5-t04-manual-verify2-unauthorized-proof.txt`
  - Markers: `unauthorized_status=400`; `X-Error=You need to be local-approver to submit this.`; final `ABORTED`; no production-continuation success after denial
- Supporting narrative: `docs/retrospectives/phase-5.md`; `docs/reviews/phase-5-change-review.md`; `docs/reviews/phase-5-security-review.md`
- Taxonomy: Locally verified authorization control; denial path is **not** a human approval event

## Learning retained (not rewritten)

- Attempt-scoped evidence required after fixture ambiguity (`PC-011`–`PC-013`)
- `TRUSTED_GIT_REF` rejected in favor of immutable `TRUSTED_GIT_SHA` (`PC-014`)

## Explicit non-claims

This record does not claim organizational production approval, live Jenkins E2E promotion, append-only multi-environment evidence closure (that is Phase 6 / `PC-002`), or verified rollback recovery (Phase 6 / `PC-003`). Residual Docker-socket/root advisories remain disclosed.

## Outcome

- Outcome: Pointer retained for portfolio walkthrough authorization / denial arc. `PC-001` resolution remains local-only per `ISSUES.md` and the Phase 5 integrated gate.
- Failed checks: none introduced by this pointer record.
