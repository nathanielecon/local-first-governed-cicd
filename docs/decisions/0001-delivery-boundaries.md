# ADR 0001: Separate validation from controlled delivery

Status: accepted

GitHub Actions validates untrusted pull requests without deployment credentials. Jenkins runs only approved branch commits and owns image publication, promotion, approval, deployment, and rollback. This duplicates a small set of critical checks intentionally so a compromised or misconfigured PR lane cannot substitute for release verification.

