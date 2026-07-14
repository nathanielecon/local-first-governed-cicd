# Phase 8 Portfolio Evidence Package Plan

Authority: `PROJECT.md` claim boundaries, `STATUS.md` verified baseline, Phases 2–7 retained evidence, Phase 9 staging evidence under `evidence/phase-9/`, and `docs/TERRA_ORCHESTRATOR_PROMPT.md` Phase 8. This plan approves narrative labels and artifact inventory before assembly (`P8-T01`). It does not authorize organizational Jenkins administration, sustained production AWS, or production-promotion claims.

Claim boundary for the Phase 8 package: **local-first / production-like**. Core portfolio arcs stay local + retained GitHub Actions. Phase 9 `us-east-1` staging smoke is an **evidenced optional strip** (not “AWS deferred / never done,” and not “completed production cloud”). Every portfolio sentence must map to one taxonomy label below. Fabricating users, production traffic, metrics, screenshots, or promotion authority is forbidden.

---

## Claim taxonomy

Use exactly these labels. Do not upgrade a claim by implication.

### Implemented

Source and contracts exist in-repo and were accepted by the corresponding phase gates. Implementation alone is never enough for a “verified” portfolio claim.

| Claim | Source of truth |
| --- | --- |
| Delivery API + CLI harness (Phase 2) | Application/tests at verified commits `5c00056` / `7f0e2b9` |
| Multi-stage image, Compose topology, smoke helpers (Phase 3) | Dockerfile, `compose.yaml`, smoke scripts, static/runtime contracts |
| GitHub PR validation workflow + Jenkinsfile local contract (Phase 4) | `.github/workflows/pr-validation.yml`, local validators |
| Jenkins authz: external creds, least-privilege roles, named approvers, `TRUSTED_GIT_SHA` (Phase 5) | `infra/jenkins/casc.yaml`, `Jenkinsfile`, Compose identity wiring |
| Append-only events + derived summary manifest (Phase 6) | `scripts/evidence.py` and related validators |
| Digest-bound promote / rollback / recovery verification contract (Phase 6) | deploy/rollback/verify scripts + Jenkinsfile gates |
| Failure-injection scenario harness (Phase 7) | `docs/failure-injection.md` + Phase 7 lane fixtures |

### Locally verified

Retained local evidence under `evidence/phase-*/` (and agreeing reviews/retrospectives) supports the claim. Prefer integrated-gate files as the phase summary pointer.

| Claim | Governing evidence |
| --- | --- |
| Phase 2 application contract (14 tests, 96.59% coverage) | `evidence/phase-2/`; `evidence/phase-2/integrated-gate.txt` |
| Phase 3 Docker runtime: build, Compose, expected-SHA smoke, not-ready negative | `evidence/phase-3/`; `evidence/phase-3/integrated-gate.txt` |
| Phase 4 local workflow hardening (pinned actions, RO permissions, Jenkinsfile contract, pytest) | `evidence/phase-4/`; `evidence/phase-4/integrated-gate.txt` |
| Phase 5 unauthorized approval denial (`unauthorized_status=400`, named-approver denial, ABORTED, no production continuation) | `evidence/phase-5/p5-t04-manual-verify2-unauthorized-proof.txt`; `evidence/phase-5/integrated-gate.txt` |
| Phase 5 end-to-end local Jenkins authorization remediation (`PC-001` resolved locally) | Phase 5 integrated gate + retrospective |
| Phase 6 append-only evidence + approver/timestamp persistence (`PC-002`) | `evidence/phase-6/events.jsonl`; `evidence/phase-6/manifest.json`; integrated gate |
| Phase 6 rollback-target / first-release gating + recovery verification (`PC-003`) | `evidence/phase-6/` promotion-gate negatives + recovery events; `docs/change-records/phase-6-local.md` |
| Phase 7 failure-injection lanes (12/12 scenarios) with residual advisories retained | `evidence/phase-7/`; `evidence/phase-7/integrated-gate.txt` |

### GitHub-verified

Only claims backed by retained hosted GitHub Actions / PR evidence for `nathanielecon/project-c-cloud`.

| Claim | Governing evidence |
| --- | --- |
| Hosted PR validation pass on `main` | Actions run `29166389732` at commit `e82f4a2` |
| Safe blocked-change demonstration | Closed draft PR `#1`; failing run `29166442925` (Python quality only; intentional Ruff F401) |
| Phase 4 hosted boundary record | `docs/change-records/phase-4-github-validation.md` |

Do not invent new GitHub-verified claims (branch protection, required-check enforcement beyond retained runs, or additional PR failures) without new retained hosted evidence.

### Human-approved

Named approval or explicit human authority events that are retained and correctly scoped.

| Claim | Event | Scope label |
| --- | --- | --- |
| **Required portfolio approval event** — production-like approval by named fixture identity `local-approver` at `2026-07-13T17:15:00Z` | `docs/change-records/phase-6-local.md`; matching Phase 6 events/manifest | Human-approved **local fixture**; not organizational production |
| Named-approver enforcement (denial path) | Phase 5 unauthorized proof (`X-Error=You need to be local-approver to submit this.`) | Locally verified authorization control; **not** an approval |
| Project-owner Phase 1 conditional close (`PC-005`) | `ISSUES.md` resolution: owner removed Phase 1 administrative human gate; `PC-001`–`PC-003` remained hard blockers | Real human authority over harness gating; not a delivery promotion |

Portfolio assembly must surface the Phase 6 `local-approver` event as the **named human approval event** required by `P8-T01`, with the local-fixture scope label mandatory in prose.

### Evidenced optional strip (Phase 9 staging)

Owner-authorized ephemeral AWS staging validation retained under `evidence/phase-9/`. Cite only what the governing manifest records. Do **not** upgrade this strip into sustained production, org multi-account GitOps, or cleared residuals.

| Claim | Governing evidence |
| --- | --- |
| Phase 9 `us-east-1` staging smoke PASS (ECR digest on ECS/Fargate behind ALB) | `evidence/phase-9/governing-manifest.json` (`smoke: PASS`); `docs/aws-validation.md`; `docs/architecture/phase-9-aws.md` |

Non-claims for this strip: production cloud completion; GitHub OIDC already enabled; TLS-terminated public hostname; least-privilege operator principal already in use; cost tear-down already executed as a verified gate.

### Deferred claims

Still out of scope or unverified. Label as deferred; never imply completion. Do **not** re-label the evidenced Phase 9 staging strip as “Live AWS Deferred.”

| Deferred claim | Pointer |
| --- | --- |
| Sustained / production AWS operation | `PROJECT.md`; Phase 9 is ephemeral staging only |
| GitHub OIDC short-lived AWS credentials (not used for retained smoke) | `STATUS.md` unverified; `docs/architecture/phase-9-aws.md` |
| TLS-terminated public staging hostname | `STATUS.md` unverified; `docs/architecture/phase-9-aws.md` |
| Least-privilege non-root AWS operator principal | `STATUS.md` unverified; `docs/architecture/phase-9-aws.md` |
| Cost tear-down / destroy after proof window | `docs/architecture/phase-9-aws.md` (teardown); `evidence/phase-9/governing-manifest.json` `teardown` |
| Digest promotion beyond local fixture evidence (org production) | Phase 6/8 local boundary |
| Production approval beyond the local Phase 5/6 fixture | Local fixture scope only |
| Live Jenkins E2E promotion and recovery | Phase 6/7 residuals; synthetic `pipeline.run_id: manual` fixtures are not E2E |
| Organizational-scale Jenkins administration | `PROJECT.md` |
| Sustained production use / production traffic | `PROJECT.md` |
| Zero-risk security / clearance of residual advisories | Phase 5 Docker-socket/root; Phase 6 operator-attested rollback + hardcoded verify maps; Phase 7 retained advisories; Phase 9 residuals above |

---

## Required narratives

Assemble English narrative artifacts in `P8-T01` (`docs/portfolio-walkthrough.md` and change records). Each narrative must cite taxonomy labels and evidence paths.

### Core walkthrough arcs (mandatory)

1. **Architecture / authorship** — Controlled delivery path: GitHub PR validation → immutable digest → staging verify → human approval → production verify → rollback target. Cite `PROJECT.md` mermaid; keep **local-first** for the Phase 8 package; mention Phase 9 only as an evidenced optional strip with `evidence/phase-9/governing-manifest.json`.
2. **Blocked change** — Phase 4 intentional quality failure stopped the PR lane without deployment credentials or cloud activity. Cite PR `#1` / run `29166442925`.
3. **Authorization and unauthorized denial** — Phase 5 named approvers + immutable `TRUSTED_GIT_SHA`; unauthorized submitter denied; no production continuation.
4. **Named human approval** — Phase 6 event-backed approval by `local-approver` with timestamps in append-only evidence (local fixture scope).
5. **Recovery** — Phase 6 rollback to prior verified digest with digest/health/version/business recovery checks recorded.
6. **Failure pressure** — Phase 7 local failure-injection lanes; residual advisories remain accepted, not cleared.
7. **Rejected alternatives / incident learning** — Short callouts from retrospectives: Phase 5 attempt-scoped evidence and `TRUSTED_GIT_REF` rejection (`PC-014`); Phase 6 shared design freeze for `PC-002`/`PC-003`; staging-as-prior rejected for production rollback claims.

### Change-record inventory for assembly

| Record | Status entering Phase 8 | Assembly action |
| --- | --- | --- |
| `docs/change-records/phase-2-local.md` | Exists | Reuse; keep Phase 2 local claim boundary |
| `docs/change-records/phase-4-github-validation.md` | Exists | Reuse as GitHub-verified + blocked-change pointer |
| `docs/change-records/phase-6-local.md` | Exists | **Mandatory** — named approval + recovery binding |
| Phase 3 / 5 / 7 change records | Missing or incomplete vs walkthrough needs | Create only if assembly needs a phase-local pointer; do not invent digests/approvers; bind to existing integrated gates |
| `docs/change-records/TEMPLATE.md` | Template only | Not a portfolio claim |

### Retrospectives to cite (not rewrite unless gaps block assembly)

- `docs/retrospectives/phase-2.md` … `phase-6.md` (Phase 7 retrospective may be absent; cite `evidence/phase-7/integrated-gate.txt` + reviews instead)

---

## Required metrics

`docs/metrics.md` is currently a draft schema only (“do not fabricate an initial baseline”). Assembly may populate **only** metrics extractable from retained evidence. Prefer ranges/counts with evidence paths over marketing single numbers.

| Metric (candidate) | Allowed source | Disallowed |
| --- | --- | --- |
| PR validation outcome (pass / intentional fail) | GitHub runs `29166389732`, `29166442925` | Invented durations unless retained in run metadata/evidence files |
| Local pytest / coverage counts | Phase 2 (and later) retained pytest evidence | Rounding up or inventing coverage |
| Failed-change detection stage | Phase 4 blocked demo (Python quality); Phase 5 unauthorized denial stage; Phase 6 promotion-gate negatives | Claiming production incident detection |
| High/critical findings opened→resolved | `ISSUES.md` (`PC-001`–`PC-014` as applicable) | Claiming zero residual risk |
| Evidence completeness per phase | Presence of integrated-gate + declared evidence sets | Marking incomplete sets complete |
| Manual / fixture steps | Phase 5 retrospective (P5-T04 loop); Phase 6 fixture note (`pipeline.run_id: manual`) | Hiding fixture nature |
| Recovery verification result | Phase 6 recovery checks (all four pass in fixture) | Claiming live E2E recovery time without timed evidence |
| Lead time across phases | Only if dated gate/review timestamps in retained docs support it | Fabricated baseline trends |

Trend language across releases is allowed only as “schema ready; initial points are phase-local evidence extracts,” not as multi-release operational history.

---

## Required screenshots

### Policy

- Do not fabricate UI. Capture only from real local or GitHub surfaces during assembly, or omit and rely on linked evidence.
- Root `*.png` files are **tooling-context candidates only** (Codex / ChatGPT connector UI). They must **not** be presented as Project C PR validation, Jenkins approval, recovery, unauthorized denial, or cloud proofs.

### Existing candidates (inventory — not delivery proofs)

| File | Observed content | Portfolio use |
| --- | --- | --- |
| `codex-landing.png` | Codex landing / task prompt UI | Optional appendix: authoring environment context only |
| `codex-cloud-current.png` | Codex UI with `/plan` prompt | Optional appendix: same |
| `github-connect.png` | GitHub sign-in for ChatGPT Codex Connector | Optional appendix: tooling auth context only; not Project C GitHub Actions proof |
| `env-create-after-auth.png` | Codex Environments → New, GitHub org not connected | Optional appendix: tooling setup friction only; **not** the Phase 4 blocked-change proof |

If used, copy into `docs/screenshots/` with captions that state the tooling-context limitation.

### Delivery screenshots to obtain or substitute in `P8-T01`

| ID | Subject | Prefer | Acceptable substitute if capture blocked |
| --- | --- | --- | --- |
| S1 | Hosted PR validation success | Actions UI for run `29166389732` | Run URL + `docs/change-records/phase-4-github-validation.md` |
| S2 | Blocked change failure | PR `#1` / run `29166442925` quality failure | Same URLs + intentional F401 note in walkthrough |
| S3 | Architecture | Rendered `PROJECT.md` flowchart or static export | Keep mermaid in walkthrough |
| S4 | Named approval evidence | Redacted local evidence view showing `local-approver` + timestamp (no secrets) | Quote from `phase-6-local.md` / manifest fields |
| S5 | Recovery evidence | Redacted recovery_verified / digest match excerpt | `evidence/phase-6/events.jsonl` + change record recovery section |
| S6 | Unauthorized denial (optional but recommended) | Local fixture proof excerpt / Jenkins denial header | `p5-t04-manual-verify2-unauthorized-proof.txt` |

No AWS console, production traffic, or fabricated user-analytics screenshots.

---

## Source evidence map

| Portfolio theme | Primary evidence | Supporting narrative |
| --- | --- | --- |
| Objective & boundaries | `PROJECT.md` | `docs/aws-validation.md` (Phase 9 optional strip) |
| Verified baseline index | `STATUS.md` `verified_baseline` / `unverified` | `ISSUES.md` resolutions |
| Phase 2 local app | `evidence/phase-2/integrated-gate.txt` | `docs/change-records/phase-2-local.md`; retrospective |
| Phase 3 runtime | `evidence/phase-3/integrated-gate.txt` | Phase 3 retrospective |
| Phase 4 GitHub | Runs `29166389732`, `29166442925`; PR `#1` | `docs/change-records/phase-4-github-validation.md`; `docs/retrospectives/phase-4.md` |
| Phase 5 authz + denial | `evidence/phase-5/integrated-gate.txt`; unauthorized proof | `docs/retrospectives/phase-5.md`; Phase 5 reviews |
| Phase 6 approval + recovery | `evidence/phase-6/integrated-gate.txt`; `events.jsonl`; `manifest.json` | `docs/change-records/phase-6-local.md`; `docs/retrospectives/phase-6.md` |
| Phase 7 failure injection | `evidence/phase-7/integrated-gate.txt`; lane index | `docs/reviews/phase-7-*.md` |
| Phase 9 staging smoke (optional strip) | `evidence/phase-9/governing-manifest.json` | `docs/aws-validation.md`; `docs/architecture/phase-9-aws.md` |
| Metrics schema | `docs/metrics.md` | Populate only from rows above |
| Runbook / operator path | `docs/runbook.md` | Local promote path + Phase 9 GitOps residuals; no production-promotion authority |

---

## Assembly constraints

`P8-T01` must satisfy all of the following:

1. **Mandatory trio (non-negotiable)**
   - **One blocked change:** Phase 4 draft PR `#1` / run `29166442925` (GitHub-verified).
   - **One recovery:** Phase 6 rollback + `recovery_verified` (locally verified; non-E2E).
   - **One named human approval event:** Phase 6 `local-approver` at `2026-07-13T17:15:00Z` (human-approved local fixture).
2. Every claim is traceable to a path or hosted run ID listed in this plan.
3. Preserve **local-first** wording for the Phase 8 package headline and metrics preamble; if Phase 9 appears, label it **evidenced optional strip** and cite `evidence/phase-9/governing-manifest.json`.
4. Label deferred / unverified residuals explicitly (OIDC, TLS hostname, least-privilege operator, cost tear-down); do not soft-imply production AWS completion; do not restate Phase 9 staging as “Deferred / never done.”
5. Do not fabricate users, production traffic, screenshots, or promotion authority.
6. Root Codex PNGs, if included, stay captioned as tooling context only.
7. Residual advisories (Docker socket/root; operator-attested rollback params; hardcoded verify maps; Phase 9 OIDC/TLS/least-privilege/tear-down) remain disclosed, not cleared.
8. Write scope for assembly remains `docs/portfolio-walkthrough.md`, `docs/metrics.md`, `docs/change-records/`, `docs/screenshots/` — authority files (`STATUS.md`, `PLAN.md`, `ISSUES.md`) stay orchestrator-owned.
9. Do not invent promotion authority or sustained-production claims from the Phase 9 strip.

Suggested assembly order: claim table in walkthrough → mandatory trio sections → phase evidence map → optional Phase 9 strip → metrics extract → screenshots/substitutes → deferred/residuals close.

---

## Out of scope / deferred

- Sustained production AWS, org multi-account GitOps, or production-promotion authority (Phase 9 strip is ephemeral staging smoke only)
- Enabling GitHub OIDC, TLS hostname, least-privilege operator, or evidenced cost tear-down as completed claims (`STATUS.md` unverified; `docs/architecture/phase-9-aws.md`)
- Live Jenkins controller E2E promotion/recovery beyond synthetic fixtures
- Organizational production approval, branch-protection administration claims beyond retained Phase 4 hosted runs
- Clearing Phase 5/6/7/9 residual advisories
- Any statement that Project C proves sustained production use or zero-risk security

This planning document (`P8-T00`) approves the package shape and claim labels only. Assembly and verification remain subsequent Phase 8 tasks (Phase 9 staging evidence is cited when present under `evidence/phase-9/`).
