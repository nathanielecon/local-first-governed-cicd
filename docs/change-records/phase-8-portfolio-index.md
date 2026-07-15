# Change phase-8-portfolio-index

Authority: `docs/portfolio-plan.md` (P8-T00). This is an **assembly index** for the Phase 8 portfolio package (`P8-T01`). It does not rewrite verified phase evidence facts and does not authorize Phase 9, live AWS, or organizational production claims.

## Identity

- Release ID: `phase-8-portfolio-assembly`
- Claim boundary: local-only / production-like / non-AWS
- Assembly task: `P8-T01`
- Commit / digest: none claimed by this index (points to prior phase records only)

## Change intent

- Reason: Assemble resume-safe portfolio narratives (walkthrough, metrics, change-record map, screenshot/evidence index) from retained Phases 2–7 evidence and GitHub-hosted Phase 4 runs.
- Expected impact: Reviewers can locate the mandatory trio (blocked change, named local-fixture approval, recovery) and every taxonomy-labeled claim without inventing users, traffic, or cloud operation.
- Blast radius: `docs/portfolio-walkthrough.md`, `docs/metrics.md`, `docs/change-records/*` (index + phase pointers), `docs/screenshots/` only.

## Mandatory trio binding

| Requirement | Binding | Label |
| --- | --- | --- |
| One blocked change | Draft PR `#1`; Actions run `29166442925` | GitHub-verified |
| One named human approval | `local-approver` @ `2026-07-13T17:15:00Z` (event `p6-local-approval`) | Human-approved **local fixture** (not org production) |
| One recovery | `recovery_verified` event `p6-local-recovery`; manifest status `recovery_verified` | Locally verified / non-E2E |

## Change-record inventory (assembly)

| Record | Role |
| --- | --- |
| `phase-2-local.md` | Reused — Phase 2 local app readiness |
| `phase-3-local.md` | Assembly pointer — Phase 3 runtime gate |
| `phase-4-github-validation.md` | Reused — hosted pass + blocked change |
| `phase-5-local.md` | Assembly pointer — authz + unauthorized denial |
| `phase-6-local.md` | Reused — **mandatory** approval + recovery |
| `phase-7-local.md` | Assembly pointer — failure-injection 12/12 |
| `phase-8-portfolio-index.md` | This index |
| `TEMPLATE.md` | Template only — not a portfolio claim |

## Narrative and metrics artifacts

- Walkthrough: `docs/portfolio-walkthrough.md`
- Metrics: `docs/metrics.md`
- Screenshot / substitute index: `docs/screenshots/README.md`
- Plan / taxonomy: `docs/portfolio-plan.md`

## Outcome

- Outcome: Phase 8 portfolio package assembled from retained evidence under the local-only / non-AWS claim boundary. Mandatory trio cited with evidence paths. Deferred claims listed; residual advisories disclosed. No fabricated screenshots, users, production traffic, or live-cloud operation.
- Failed checks: none for assembly write scope; validation command `git diff --check` expected after write.
- Explicitly unverified by this record alone: Phase 8 integrated gate (`P8-T03`), demo rehearsal (`P8-T02`), Phase 9 / AWS.
