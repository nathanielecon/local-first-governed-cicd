# Phase 4 GitHub Validation Boundary

Date: 2026-07-11
Status: local Phase 4 workflow hardening in progress; this document is not GitHub-hosted validation evidence

## Scope

This record defines the approved boundary for Phase 4 GitHub PR validation work.

- Local repository work may harden `.github/workflows/pr-validation.yml`, add local validation scripts, add static tests, and retain local evidence.
- Local repository work may not claim a real GitHub Actions pass, required-check enforcement, branch-protection changes, Jenkins runtime execution, production approval, rollback recovery, or cloud activity.

## Required local workflow controls

- Third-party actions must be pinned to full commit SHAs.
- Each job must declare least-privilege read-only permissions and remain free of deployment credentials.
- Python quality, secret scanning, filesystem vulnerability scanning, Dockerfile validation, and local container contract checks must remain in the PR lane.
- Jenkinsfile validation must use a contract-aware local validator rather than grep-only text assertions.

## Hosted evidence boundary

Phase 4 is not complete until the repository retains:

- a real GitHub-hosted workflow run showing the approved checks;
- a safe blocked-change demonstration that fails for an intentional, non-destructive reason;
- a clear record of any required GitHub authority, such as authenticated repository access or branch-protection administration.

If that hosted evidence cannot be collected from the current environment, the orchestrator must record the exact missing authority as a blocker instead of implying success from local-only workflow preparation.
