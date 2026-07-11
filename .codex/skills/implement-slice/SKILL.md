---
name: implement-slice
description: Implement one approved Project C issue while preserving scope, validation integrity, rollback behavior, and evidence traceability. Use only after the engineering review is clear.
---

# Implement One Slice

1. Confirm the issue is approved, unblocked, and represented in `PLAN.md`.
2. Confirm the orchestrator set the task running through the CLI before changing files.
3. Make the smallest coherent change satisfying all acceptance criteria.
4. Add or update positive, negative, and recovery tests with the implementation.
5. Run slice-relevant checks and preserve raw reports under the declared evidence location.
6. Record new tradeoffs in a decision record; never silently expand scope.
7. Return the required Simplified Chinese handoff. The orchestrator may move the task to review, never directly to done.

Never weaken a gate or delete a failing test merely to obtain a pass.
Never modify outside the declared `write_scope` or communicate directly with another worker.
