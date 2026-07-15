# Resume paste block — Project C

Honest bullets for a Cloud / Platform / DevOps resume. Scope is local-first governed delivery plus optional evidenced AWS staging—not sustained production cloud SRE.

1. Built a local-first CI/CD path where PR checks run without deploy keys, Jenkins builds one sealed image digest, staging must pass, a named human approves, evidence is kept, and failed verify rolls back to the last good image.
2. Enforced fail-closed promotion: immutable digest identity, unauthorized approval denial in a local Jenkins fixture, and recovery verification recorded in release evidence.
3. Hardened PR CI with pinned Actions, read-only job permissions, Jenkinsfile contract checks, and no deploy credentials on untrusted PR jobs.
4. Retained phase evidence and portfolio artifacts under an explicit claim boundary; residuals (Docker-socket/root controller, operator-attested rollback parameters) disclosed rather than cleared by narrative.
5. Validated an optional owner-authorized AWS staging path in `us-east-1` (ECR → ECS/Fargate → ALB) with smoke evidence; OIDC least-privilege apply and TLS hostname remain follow-ons.

**Links:** [Delivery diagram](screenshots/project-c-delivery-infographic.png) · [AWS staging architecture](screenshots/phase9-architecture.png) · [Public naming](public-naming.md) · [Portfolio walkthrough](portfolio-walkthrough.md) · [README](../README.md)

**Do not claim:** continuous production AWS ops, org-wide Jenkins admin, or zero-risk security.
