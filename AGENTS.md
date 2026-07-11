# Project C Orchestration Contract

## Authority

- `PROJECT.md` defines scope; `PLAN.md` defines tasks; `STATUS.md` defines current state; `ISSUES.md` defines blockers; `DECISIONS.md` indexes approved decisions.
- Phase 1 is the only authorized implementation phase. Do not execute later-phase work until authorization is recorded.
- Only the CLI and thin orchestrator may change task, gate, issue, or evidence state.

## Model routing

- Persistent orchestrator and model ceiling: GPT-5.6 Terra Medium.
- Low risk: cheapest configured Codex-capable worker.
- Medium risk: lowest configured coding model that reliably meets the checks.
- High risk and independent engineering/security gates: GPT-5.6 Terra Medium in a fresh context.
- Record the actual configured model ID at task dispatch; never invent an unavailable model.

## Thin orchestrator prohibitions

- Do not implement routine work, approve production, approve credentials, change branch protection, authorize cloud activity, or approve the orchestrator's own high-risk work.
- Do not dispatch work outside an approved task or provide workers unrelated repository context.
- Do not permit worker-to-worker communication or conversational status loops.
- Do not parallelize overlapping write scopes, shared schemas, promotion state, or final gate decisions.

## Worker protocol

All worker assignments, updates, retained notes, and handoffs use Simplified Chinese. External project and portfolio artifacts remain English. Hidden reasoning language is not controllable or verifiable.

Every handoff must contain all fields:

```yaml
任务:
状态: 完成|阻塞|等待人工|失败
已完成: []
修改文件: []
验证命令: []
验证结果: []
失败检查: []
剩余风险: []
建议下一步: []
证据路径: []
需要升级: true|false
```

- Modified files must stay within task `write_scope`.
- A worker may move work only to review or blocked; it cannot mark work verified or done.
- QA records defects and evidence; fixes return to an implementation task.
- Empty fields use empty lists. Blocked, waiting-human, or failed handoffs require a failed check. Escalation requires an issue ID.

## Retry, escalation, and notification

- Allow one repair/resume after the first diagnosable failure.
- After the second same-class failure, no meaningful diff, scope expansion, write-scope violation, or security ambiguity, create a blocking issue and escalate.
- Credentials, production approval, branch protection, live cloud, destructive actions, and irreversible actions immediately enter `waiting-human`.
- Notify the user in the active Codex task with issue ID, affected phase, attempts, exact failed check, safe options, recommendation, and lanes that may continue.
- Preserve failed evidence. Never weaken a gate or delete a failing test to manufacture a pass.

## Delivery invariants

- Never expose secrets or give untrusted PR jobs deployment credentials.
- Build once and promote an immutable digest; never rebuild between environments.
- Never claim live cloud, production, approval, rollback, or GitHub validation without corresponding evidence.
- Human approval is mandatory for production promotion and all authority-expanding changes.

