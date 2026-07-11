---
name: review
description: Review a Project C diff for correctness, security, maintainability, regression risk, missing tests, and missing evidence. Use after implementation and before QA.
---

# Review the Change

1. Read the issue, diff, acceptance criteria, relevant decisions, and test output.
2. Prioritize exploitable credential exposure, incorrect promotion identity, rollback defects, and false evidence.
3. Verify the implementation does not grant deployment credentials to PR jobs.
4. Verify tests exercise behavior rather than only implementation details.
5. Report actionable findings with file and line references, ordered by severity.
6. Record a clear or blocked verdict in `docs/reviews/change-review.md`; send state changes to the orchestrator.

Do not edit implementation during a review-only request.
Review the current diff; leave full trust-boundary certification to `security-review`.
