---
name: qa
description: Execute Project C's approved test plan, capture raw evidence, diagnose defects, add regression coverage, and re-verify fixes. Use after change review and before security review or shipping.
---

# Verify Delivery

1. Read the approved engineering test plan and current release metadata.
2. Run static checks, unit tests, container contract tests, staging verification, negative paths, and recovery tests applicable to the slice.
3. Preserve commands, timestamps, versions, exit codes, and raw reports in `evidence/<release-id>/`.
4. For defects, record reproduction and evidence, then return work to an implementation task. Do not fix code inside the QA role.
5. Reject screenshots or summaries without corresponding machine-readable evidence when automation is possible.
6. Return the result to the orchestrator for atomic evidence and status recording.
