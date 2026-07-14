# Public naming proposal

**Status:** Proposal for orchestrator apply after remaining Slice 9 gates clear.  
**Do not run** live `gh repo edit` from this slice—orchestration-owned.

## Recommendation

| Field | Value | Notes |
| --- | --- | --- |
| Public display title | **Project C — Governed CI/CD Delivery** | Hero-level name for README, portfolio, and About text |
| Repository slug | `project-c-cloud` | Keep URL and clone path stable |
| Full GitHub identity | `nathanielecon/project-c-cloud` | Unchanged |
| Suggested About description | Local-first governed CI/CD: credential-free PR validation, digest promotion, approval, evidence, and rollback. Optional AWS staging evidenced—not sustained production. | ≤350 characters; claim-boundary honest |

## Why this split

- Recruiters and reviewers need a readable **product/platform title**; `project-c-cloud` alone reads like an internal slug.
- Renaming the GitHub repository slug would break existing clone URLs, Actions history links, and portfolio citations that already use `project-c-cloud`.
- The public title matches `README.md` and aligns with `PROJECT.md` (“Gstack-Governed CI/CD Delivery Platform”) without requiring “Gstack” in the GitHub surface name.

## Orchestrator apply (after full gate)

When authorized, set description (and optional homepage) without renaming the slug:

```bash
gh repo edit nathanielecon/project-c-cloud \
  --description "Local-first governed CI/CD: credential-free PR validation, digest promotion, approval, evidence, and rollback. Optional AWS staging evidenced—not sustained production."
```

Optional homepage (only if a stable public doc URL is chosen later): omit until a canonical portfolio URL exists.

**Do not** use `gh repo rename` unless a separate, explicit authority records a slug change. This proposal assumes the slug remains `project-c-cloud`.

## Rejected alternatives

| Candidate | Why not |
| --- | --- |
| Rename slug to `project-c-governed-cicd` | Breaks retained GitHub / evidence links |
| Title “Project C Cloud” alone | Over-implies production cloud completion |
| Title “Gstack Platform” | Tooling brand overshadows the delivery product story |

## Claim boundary for naming surfaces

Any public title or About blurb must stay consistent with README claim language: local-first primary proof; AWS staging only with evidence pointers (`docs/aws-validation.md`, `evidence/phase-9/`); never imply organizational production or sustained cloud SRE.
