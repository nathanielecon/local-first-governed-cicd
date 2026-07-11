---
name: plan-eng-review
description: Perform the required pre-implementation engineering gate for Project C, covering architecture, data flow, credentials, failure modes, rollout, rollback, and tests. Use after specification and after any material architecture change.
---

# Review the Engineering Plan

1. Read `PROJECT.md`, `PLAN.md`, all active decisions, and the proposed test plan.
2. Trace commit to image digest to staging to production to rollback target.
3. Challenge untrusted PR access, secret scope, mutable tags, concurrency, partial failure, evidence loss, and recovery.
4. Classify findings as critical, major, or advisory. Cite the exact affected artifact.
5. Block implementation while any critical finding or undecided architecture path remains.
6. Record the result under `docs/reviews/eng-review.md`; send state and issue changes to the orchestrator for CLI recording.

Use a fresh GPT-5.6 Terra Medium context independent from the implementing worker. A blocked review must name issue IDs and the lanes that may continue.

A clear result must name the approved baseline and required tests; silence is not approval.
