---
name: security-review
description: Audit Project C CI/CD changes for secret exposure, excessive permissions, untrusted execution, dependency and image risk, provenance gaps, and unsafe deployment controls. Use before shipping and after credential or pipeline changes.
---

# Review CI/CD Security

1. Map every identity, credential, trust boundary, and privileged operation.
2. Confirm PR jobs have read-only repository access and no deployment credentials.
3. Inspect source, history, images, logs, artifacts, and evidence for secrets.
4. Verify pinned dependencies/actions, non-root runtime, scan thresholds, and digest promotion.
5. Test unauthorized promotion only in an isolated local fixture; never probe a live environment without human authorization.
6. Record findings and accepted exceptions in `docs/reviews/security-review.md` with owner and expiry.
7. Block shipping for critical/high unaccepted findings and create issue IDs through the orchestrator.
