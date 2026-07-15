# Project C — CLI Demo Script (P8-T02)

**Claim boundary:** local-first / production-like for this Phase 8 rehearsal. Exercises the project CLI, local pytest, and retained evidence pointers. Phase 9 `us-east-1` staging may be mentioned only as **staging-validated** with evidence (`evidence/phase-9/governing-manifest.json`) — do not re-run AWS, and do not claim sustained production cloud. This demo does **not** claim organizational production approval, live Jenkins E2E promotion, sustained production traffic, or clearance of residual advisories.

**Audience:** resume / portfolio walkthrough operators.  
**Authority:** `docs/portfolio-plan.md`, `docs/portfolio-walkthrough.md`, `docs/metrics.md`.  
**Rehearsal evidence:** `evidence/phase-8/` (raw outputs from this task).

---

## Preconditions

1. Work from the repository root on Windows PowerShell.
2. Use the project virtualenv: `.venv\Scripts\python.exe`.
3. Do not start live cloud apply/destroy, AWS CLI mutations, or organizational Jenkins changes during the demo. Phase 9 is pointer-only if mentioned.
4. Optional deep dives (Compose / local Jenkins) stay read-only against retained Phase 5–7 evidence unless a later authorized task says otherwise.

---

## Demo flow (reproducible)

### Step 0 — Orient (about 30 seconds)

State the boundary out loud:

> This Phase 8 package is local-first / production-like. Hosted claims are limited to retained GitHub Actions runs. Approval and recovery shown here are local fixtures. Phase 9 staging smoke is an optional evidenced strip, not this demo's runtime.

Point at:

| Artifact | Role |
| --- | --- |
| `docs/portfolio-walkthrough.md` | Narrative + mandatory trio |
| `docs/metrics.md` | Headline metrics with evidence sources |
| `docs/change-records/phase-8-portfolio-index.md` | Assembly index |

### Step 1 — Project state (CLI)

```powershell
.venv\Scripts\python.exe scripts\project_cli.py validate state
.venv\Scripts\python.exe scripts\project_cli.py status --json
```

**Expect:**

- `Validation passed: state` with `"passed": true`
- Status shows Phase 8 / `phase-8-demo` (or later completed Phase 8 gate after `P8-T03`)
- No fabricated production or AWS fields

**Retained rehearsal:** `evidence/phase-8/p8-t02-validate-state.txt`, `evidence/phase-8/p8-t02-cli-status.txt`

### Step 2 — Local application verification (pytest)

```powershell
.venv\Scripts\python.exe -m pytest -q
```

**Expect:**

- Full suite passes under current tree
- Coverage meets the configured `delivery_api` threshold (term report shows **96.59%** total when the suite matches the retained coverage contract)

**Note:** Headline metrics in `docs/metrics.md` cite **phase-local** counts (Phase 2: 14 passed; Phase 4 QA: 38 passed). Do not overwrite those extracts with today’s suite size. Current rehearsal proves the harness still runs; historical counts remain bound to phase integrated gates.

**Retained rehearsal:** `evidence/phase-8/p8-t02-pytest.txt`

### Step 3 — Phase 6 release evidence contract (local fixture)

```powershell
.venv\Scripts\python.exe scripts\project_cli.py evidence phase-6
```

**Expect:** `"valid": true` for `evidence/phase-6/manifest.json` + `events.jsonl`.

Then open (read-only):

- Named approval: `approvals[].approver_id=local-approver` @ `2026-07-13T17:15:00Z`
- Recovery: `status=recovery_verified`; checks `deployed_digest`, `health`, `version`, `business_behavior` all `pass`
- Fixture disclosure: `pipeline.run_id: manual`

**Retained rehearsal:** `evidence/phase-8/p8-t02-evidence-phase-6.txt`

### Step 4 — Mandatory trio (pointer walk, no new claims)

Walk these three retained proofs only:

1. **Blocked change (GitHub-verified)** — draft PR `#1`, Actions run `29166442925` (intentional Ruff F401). Contrast pass run `29166389732` @ `e82f4a2`.  
   Pointers: `docs/change-records/phase-4-github-validation.md`; `evidence/phase-4/integrated-gate.txt`
2. **Named approval (Human-approved local fixture)** — `local-approver` event `p6-local-approval`.  
   Pointers: `docs/change-records/phase-6-local.md`; `evidence/phase-6/events.jsonl`; `manifest.json`
3. **Recovery (Locally verified, non-E2E)** — event `p6-local-recovery`; manifest `recovery_verified`.  
   Same Phase 6 pointers; not live Jenkins E2E

### Step 5 — Authorization denial (related, not an approval)

Show Phase 5 unauthorized proof: HTTP 400 / named-approver denial / final `ABORTED` / no production continuation.

Pointer: `evidence/phase-5/p5-t04-manual-verify2-unauthorized-proof.txt`

### Step 6 — Failure-injection pressure (Phase 7)

Show lane index: twelve scenarios with `ok=True` and `all_scenarios_ok=True`.

Pointers: `evidence/phase-7/P7-T01-lane-index.txt`; `evidence/phase-7/integrated-gate.txt`

State residual advisories remain (Docker socket/root; operator-attested rollback; hardcoded verify maps). Do not claim they are cleared.

### Step 7 — Metrics cross-check

Open `docs/metrics.md` and the rehearsal trace:

```text
evidence/phase-8/metrics-trace.txt
```

Confirm every headline row has an existing source path and matching retained value. Do not invent durations, users, traffic, or live-cloud SLOs.

### Step 8 — Close the claim boundary

Optional one-liner (pointer only, no AWS commands): Phase 9 `us-east-1` staging smoke is an **evidenced optional strip** — cite `evidence/phase-9/governing-manifest.json` / `docs/aws-validation.md`. Do **not** call it “Live AWS Deferred” and do **not** call it completed production cloud.

Explicitly label **Deferred / unverified residuals**:

- GitHub OIDC not enabled for the retained smoke
- TLS-terminated public staging hostname
- Least-privilege non-root AWS operator principal
- Cost tear-down after the proof window
- Organizational production approval beyond the local fixture
- Live Jenkins E2E promotion and recovery
- Sustained production traffic / zero residual risk

Pointers: `STATUS.md` unverified; `docs/architecture/phase-9-aws.md`.

---

## Commands operators should not run in this demo

- Any AWS CLI / Terraform apply or destroy / live registry push (Phase 9 stays pointer-only)
- Changing branch protection, credentials, or production promotion authority
- Rebuilding and re-tagging as if it were a new production promotion between environments
- Treating Codex / connector PNGs as GitHub Actions, Jenkins, or cloud proofs

---

## Timing guide (about 8–12 minutes)

| Block | Minutes |
| --- | --- |
| Boundary + portfolio pointers | 1 |
| CLI validate / status | 1 |
| Pytest | 1–2 |
| Phase 6 evidence + trio | 3–4 |
| Authz denial + Phase 7 lanes | 2 |
| Metrics trace + optional Phase 9 strip + residuals close | 1–2 |

---

## Success criteria for this rehearsal

- [x] Demo script stays inside local / GitHub-retained / fixture claims
- [x] `project validate state` passes and raw output is retained
- [x] Pytest (or equivalent project verification) raw output is retained
- [x] Every `docs/metrics.md` headline metric traces to retained evidence in `evidence/phase-8/metrics-trace.txt`
