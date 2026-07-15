# Public naming

**Status:** Orchestrator applied recruiter-facing rename after Slice 9 gate + owner direction to signal what the project does on the GitHub surface.

## Applied identity

| Field | Value | Notes |
| --- | --- | --- |
| Public display title | **Local-First Governed CI/CD** | Hero-level name in README and About |
| Repository slug | `local-first-governed-cicd` | Renamed from `project-c-cloud` so the URL itself reads clearly to recruiters |
| Full GitHub identity | `nathanielecon/local-first-governed-cicd` | GitHub keeps redirects from the old slug |
| About description | Local-first governed CI/CD: credential-free PR checks, one sealed image digest, staging verify, named approval, evidence, and rollback. Optional AWS staging evidenced—not sustained production. | ≤350 characters; claim-boundary honest |

## Why this name

- `project-c-cloud` sounded like an internal label and over-implied “cloud project done.”
- The new slug and title say the product job in plain words: local-first proof, governed promotion, digest identity, approval, evidence, rollback.
- Optional AWS staging stays in the description as evidenced smoke, not the primary claim.

## Commands used

```bash
gh repo rename local-first-governed-cicd
gh repo edit nathanielecon/local-first-governed-cicd \
  --description "Local-first governed CI/CD: credential-free PR checks, one sealed image digest, staging verify, named approval, evidence, and rollback. Optional AWS staging evidenced—not sustained production."
```

## Claim boundary for naming surfaces

Any public title or About blurb must stay consistent with README claim language: local-first primary proof; AWS staging only with evidence pointers (`docs/aws-validation.md`, `evidence/phase-9/`); never imply organizational production or sustained cloud SRE.
