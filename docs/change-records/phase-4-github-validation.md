# Phase 4 GitHub Validation Boundary

Date: 2026-07-11
Status: hosted validation captured; this record defines the boundary and points to retained evidence

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

Phase 4 required the repository to retain:

- a real GitHub-hosted workflow run showing the approved checks;
- a safe blocked-change demonstration that fails for an intentional, non-destructive reason;
- a clear record of any required GitHub authority, such as authenticated repository access or branch-protection administration.

Retained evidence:

- Passing hosted run: `https://github.com/nathanielecon/project-c-cloud/actions/runs/29166389732`
- Safe blocked-change demonstration: closed draft PR `#1` at `https://github.com/nathanielecon/project-c-cloud/pull/1`
- Intentional failing hosted run: `https://github.com/nathanielecon/project-c-cloud/actions/runs/29166442925`

The Phase 4 evidence proves GitHub-hosted validation and blocked-change behavior only. It does not prove Jenkins runtime execution, production approval, rollback recovery, or cloud activity.
