---
name: ship
description: Gate a Project C change for release by checking branch state, required reviews, tests, evidence, immutable artifact metadata, approval, and rollback readiness. Use only after implementation, review, QA, and security review are complete.
---

# Ship the Change

1. Verify the engineering, change, QA, and security gates are clear.
2. Verify the branch contains only approved scope and required checks pass.
3. Confirm commit SHA, image reference, digest, SBOM/scan reports, staging result, and rollback target agree.
4. Ensure the change record states reason, impact, blast radius, validation, approval, and rollback.
5. Prepare the PR or release; never self-approve a production promotion.
6. Return readiness to the orchestrator. Only an independent gate with inspectable external evidence may record verified state.

Do not claim production deployment when only the local environment was exercised.
Do not treat file presence, scaffold definitions, or pending external checks as release evidence.
