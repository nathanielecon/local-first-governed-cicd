# CLI-First Gstack Orchestration

The GPT-5.6 Terra Medium orchestrator reads the five authoritative project surfaces, selects ready tasks, checks dependencies and write scopes, assigns the cheapest suitable worker, validates the Mandarin handoff, and advances work only after the required independent gate.

Maximum concurrency is three workers plus the orchestrator. Unrelated lanes may continue when one lane blocks. Shared interface changes, critical security findings, and baseline-invalidating failures freeze dependent lanes.

Lifecycle mapping:

| CLI/gstack step | Responsibility |
|---|---|
| discovery | Scope and claim boundaries |
| spec | Testable tasks and evidence requirements |
| engineering review | Architecture, trust, failure, rollout, and test gate |
| implement slice | One bounded write scope |
| change review | Diff correctness and regression risk |
| QA | Read-only verification and defect capture |
| security review | Full trust-boundary gate |
| ship | Evidence and release readiness, never approval |
| retro | Evidence-based improvement returned through spec/review |

All state changes use the project CLI's atomic replacement and revision checks. Workers do not edit authoritative JSON blocks.

