# Phase 4 Retrospective

Date: 2026-07-11
Phase outcome: verified

## What went well

- The local workflow hardening work translated cleanly into a passing hosted GitHub Actions run once the repository remote existed.
- Hosted validation failures were isolated quickly because each lane had a narrow contract and clear job names.
- The safe blocked-change demonstration proved that a harmless quality failure is enough to stop the PR lane without touching deployment, Jenkins runtime, or cloud boundaries.

## Rework and root causes

- The first hosted failure came from local formatting drift that had not yet been exercised in GitHub-hosted validation.
- The second hosted failure came from the original secret-scan path assuming a usable Git history range on an initial push.
- The longest rework cycle came from Trivy installer instability on hosted runners; switching to the maintained container image removed that infrastructure-specific failure mode.

## Follow-up actions

- Keep the security scan on the pinned Trivy container path unless a simpler hosted path is re-verified with evidence.
- Preserve the blocked-change demonstration pattern as an isolated lint-only PR so future phases can collect failure evidence without contaminating release lanes.
- Treat new repository bootstrap as a first-class checklist item before any future hosted-validation gate opens.
