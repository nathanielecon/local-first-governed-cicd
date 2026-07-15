# Portfolio screenshots and evidence substitutes

**Policy:** Do not fabricate UI. Prefer real captures from local or GitHub surfaces, or substitute with retained evidence paths and hosted run URLs. No AWS console, production traffic, or fabricated user-analytics images.

**Claim boundary:** local-first / production-like for S1–S6. Phase 9 AWS staging is staging-validated with retained evidence — not a sustained-production claim.

---

## Primary portfolio infographic (Slice 9c)

| Asset | Path | Notes |
| --- | --- | --- |
| Primary landscape poster (Image2) | `docs/screenshots/project-c-delivery-infographic.png` | Exactly one primary 16:9 asset (2048×1152). TOP: architecture flowchart (Developer → GitHub PR → Actions → Jenkins digest → staging verify → named approval → evidence/rollback; ECR→ECS/Fargate→ALB staging strip). BOTTOM: story chapter cards. Embedded first in root `README.md` with ELI5 walkthrough. |
| Phase 9 staging architecture (Image2) | `docs/screenshots/phase9-architecture.png` | Polished 16:9 Image2 render of staging-validated AWS path (aligned to `docs/project-c-phase9-staging-architecture.drawio`). Embedded on README under AWS staging architecture. Force-tracked via `.gitignore` exception. Canonical editable source remains the draw.io file. |

---

## Phase 9 architecture (AWS staging diagram)

| Asset | Path | Notes |
| --- | --- | --- |
| draw.io source | `docs/project-c-phase9-staging-architecture.drawio` | Canonical: ECR digest → ECS/Fargate behind ALB in `us-east-1` |
| Architecture / SRE write-up | `docs/architecture/phase-9-aws.md` | Digest orientation, GitOps apply boundary, OIDC path, residuals, tear-down |
| Governing evidence | `evidence/phase-9/governing-manifest.json` | Digest + smoke PASS + claim residuals |
| Validation notes | `docs/aws-validation.md` | Procedure and cost posture |

Do not fabricate AWS console screenshots. Prefer the draw.io diagram and retained `evidence/phase-9/` paths.

---

## Delivery evidence index (S1–S6)

| ID | Subject | Prefer | Acceptable substitute (used for P8-T01) |
| --- | --- | --- | --- |
| S1 | Hosted PR validation success | Actions UI for run `29166389732` | [Run 29166389732](https://github.com/nathanielecon/project-c-cloud/actions/runs/29166389732); `docs/change-records/phase-4-github-validation.md`; `evidence/phase-4/integrated-gate.txt` |
| S2 | Blocked change failure | PR `#1` / run `29166442925` quality failure | [PR #1](https://github.com/nathanielecon/project-c-cloud/pull/1); [Run 29166442925](https://github.com/nathanielecon/project-c-cloud/actions/runs/29166442925); intentional Ruff F401 note in `docs/portfolio-walkthrough.md` §3.1 |
| S3 | Architecture | Rendered `PROJECT.md` flowchart | Mermaid retained in `docs/portfolio-walkthrough.md` §1 and `PROJECT.md` |
| S4 | Named approval evidence | Redacted view of `local-approver` + timestamp | Quote: approver `local-approver`, `2026-07-13T17:15:00Z`, event `p6-local-approval` — `docs/change-records/phase-6-local.md`; `evidence/phase-6/manifest.json`; `evidence/phase-6/events.jsonl` |
| S5 | Recovery evidence | Redacted `recovery_verified` / digest match | Event `p6-local-recovery`; manifest `status=recovery_verified` with four checks pass — `evidence/phase-6/events.jsonl`; `evidence/phase-6/manifest.json`; change-record Recovery section |
| S6 | Unauthorized denial (recommended) | Local fixture / Jenkins denial header | `evidence/phase-5/p5-t04-manual-verify2-unauthorized-proof.txt` (`unauthorized_status=400`; `X-Error=You need to be local-approver to submit this.`) |

No PNG captures were fabricated for S1–S6 during assembly. Substitutes above are the governing portfolio proofs until authentic UI captures are added under this directory with matching captions.

---

## Optional tooling-context appendix (not delivery proofs)

Root repository PNGs may be copied here later for authoring-environment context only. If referenced, captions **must** state tooling-context limitation.

| File (repo root) | Observed content | Allowed portfolio use |
| --- | --- | --- |
| `codex-landing.png` | Codex landing / task prompt UI | Appendix: authoring environment only |
| `codex-cloud-current.png` | Codex UI with `/plan` prompt | Appendix: same |
| `github-connect.png` | GitHub sign-in for ChatGPT Codex Connector | Appendix: tooling auth friction only — **not** Project C Actions proof |
| `env-create-after-auth.png` | Codex Environments → New | Appendix: tooling setup only — **not** Phase 4 blocked-change proof |

**Forbidden:** presenting any of the above as GitHub PR validation, Jenkins approval, recovery, unauthorized denial, or cloud evidence.
