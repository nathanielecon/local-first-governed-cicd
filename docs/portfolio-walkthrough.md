# Reviewer Walkthrough

1. Show the architecture and GitHub/Jenkins responsibility boundary.
2. Open a PR and show formatting, types, tests, secrets, dependency, Dockerfile, and container-contract checks.
3. Merge an approved commit and show Jenkins building one SHA-tagged image and recording its digest.
4. Show staging reporting the same commit and passing smoke/negative tests.
5. Show the human production approval and the identical digest in production.
6. Inject a readiness failure and show automatic restoration of the previous image.
7. Open the release manifest, change record, scan/test reports, and retrospective.
8. State the claim boundary: production-like local proof; AWS is unclaimed until separately exercised.

