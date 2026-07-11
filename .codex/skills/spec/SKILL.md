---
name: spec
description: Convert an approved Project C outcome into executable requirements, acceptance criteria, risks, dependencies, and evidence-producing backlog slices. Use before implementation or when requirements change.
---

# Specify Delivery Work

1. Read `PROJECT.md`, `PLAN.md`, `STATUS.md`, and applicable decisions.
2. Define observable behavior, negative paths, security constraints, and rollback behavior.
3. Split work into independently verifiable slices using the GitHub issue template fields.
4. Give every slice acceptance criteria, risk, dependencies, model tier, write scope, required checks, and evidence paths.
5. Return the proposed task records to the orchestrator. Only it may update the authoritative plan and next gate.

Do not accept "pipeline succeeds" as sufficient evidence; specify artifact identity, environment state, verification, and recovery.
