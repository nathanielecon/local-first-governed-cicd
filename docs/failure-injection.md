# Failure-Injection Matrix

Run only in the local demonstration environment. Preserve raw output under the release evidence directory.

| Scenario | Injection | Expected gate or response |
|---|---|---|
| Lint/test defect | Introduce a temporary failing test on a throwaway branch | GitHub/Python quality blocks merge |
| Fake credential | Commit a documented Gitleaks test signature on a throwaway branch, then remove it | Gitleaks blocks merge; no real secret is used |
| Vulnerable component | Test a known-vulnerable fixture branch | Trivy blocks at high/critical threshold |
| Not ready | Set `STAGING_READY=false` | Staging smoke test fails; production gate is unreachable |
| Dependency unreachable | Point a fixture service at an invalid host | Readiness or contract verification identifies connectivity failure |
| Missing provenance | Build fixture without expected SHA | Smoke test rejects `/version` mismatch |
| Production regression | Deploy a fixture with `APP_READY=false` | Deployment script restores previous production image |
| Unauthorized promotion | Attempt Jenkins production step without authenticated approval | Jenkins denies or pauses the operation |
| Docker permission failure | Remove agent access to Docker in a disposable controller | Runbook isolates socket/permission failure |
| Mutable-tag drift | Move a test tag after recording a digest | Digest deployment continues to select the recorded artifact |

Never place real credentials in failure fixtures or repository history.

