# Dispatch handoff — Phase 10: serverless runtime for `delivery-api`

**For the owner. Read this before dispatching; the worker reads the Chinese block.**

## Why

Phase 9's staging stack — ALB `project-c-stg` + Fargate service `project-c-delivery-api` —
measured **~$25/month** in AWS Cost Explorer (ALB $0.540/day, Fargate $0.296/day, plus
$0.12/day per public IPv4). It was torn down on 2026-08-08 after a final live capture
(`evidence/phase-9/20260808T191039Z-*`).

Rebuilding it to keep a demo URL alive costs $25/month. Running the same image on
Lambda behind a Function URL costs **≈$0** — Lambda's 1M requests / 400,000 GB-seconds
monthly free tier is perpetual, not a 12-month trial.

The outcome is a permanently reachable URL at no cost, and a stronger delivery story:
the same governed artifact on two runtimes.

## Why this is small

`Dockerfile` already runs `uvicorn` on port **8080** — the AWS Lambda Web Adapter's
default. The adapter is one `COPY` line and needs **no application code change**, so
`src/` stays untouched and `write_scope` stays tight. The alternative, Mangum, would
require editing `src/delivery_api/main.py`.

## Two governance points the worker must not get wrong

**1. The digest invariant.** `AGENTS.md` says *"Build once and promote an immutable
digest; never rebuild between environments."* Adding the adapter produces a **new
image and a new digest**. That is a new release artifact for a new runtime — it is
**not** a rebuild of the phase-9 image for a different environment, which the
invariant forbids. It must be recorded as its own digest with its own evidence. The
phase-9 digest `sha256:bffa93ad…` stays valid for what it evidences and must not be
overwritten or reused.

**2. No live cloud.** `AGENTS.md`: *"Credentials, production approval, branch
protection, live cloud, destructive actions, and irreversible actions immediately
enter `waiting-human`."* The worker therefore does **not** run `terraform apply`, does
**not** push to ECR, and does **not** create the Lambda function. It produces the
Dockerfile change, the Terraform, the tests and the evidence scaffold, then hands off
at `waiting-human`. The owner performs the build, push and apply.

That split is deliberate: an ECR push and a Lambda apply are the only steps that cost
money or mutate the account.

## Owner decision before dispatch

**Function URL or API Gateway HTTP API.**

- **Function URL** (default in this task): simplest, no per-request charge, gives
  `<id>.lambda-url.us-east-1.on.aws`. A custom domain later needs CloudFront in front.
- **API Gateway HTTP API**: ~30 minutes more work, $1/million requests (negligible
  here), but native custom-domain support.

If `api.<yourdomain>` is plausibly in your future, say so at dispatch and have the
worker use API Gateway. Changing later is rework.

## Estimate

1.5–2.5 hours of worker time, plus ~20 minutes of owner time for build/push/apply.

---

## 任务派发（Simplified Chinese — worker block）

```json
{
  "id": "P10-T01",
  "phase": 10,
  "title": "为 delivery-api 增加 Lambda 无服务器运行时（不执行云端变更）",
  "outcome": "同一治理镜像可在 Lambda 上运行，提供长期免费的公开 URL；ECS/ALB 证据保持不变。",
  "state": "ready",
  "depends_on": ["P9-T-final"],
  "model_tier": "implementation",
  "owner": "phase-10-implementation",
  "write_scope": [
    "Dockerfile",
    "infra/lambda/main.tf",
    "infra/lambda/variables.tf",
    "infra/lambda/outputs.tf",
    "infra/lambda/versions.tf",
    "infra/lambda/README.md",
    "tests/test_lambda_contract.py",
    "docs/runbook.md",
    "PLAN.md",
    "STATUS.md"
  ],
  "acceptance_criteria": [
    "Dockerfile 通过一行 COPY 引入 aws-lambda-adapter；src/ 目录零改动",
    "容器仍可本地以 uvicorn 方式运行，端口 8080 不变，四个既有端点行为不变",
    "infra/lambda 使用远程 S3 后端并配置 DynamoDB 锁，不得使用本地 state",
    "Terraform 定义：Lambda（容器镜像）、执行角色、Function URL（AuthType=NONE）、CloudWatch 日志组（保留 7 天）",
    "Lambda 执行角色仅授予 AWSLambdaBasicExecutionRole，不得附加任何数据面权限",
    "新镜像 digest 单独记录，绝不覆盖或复用 phase-9 的 sha256:bffa93ad…",
    "worker 不执行 terraform apply、不推送 ECR、不创建任何云资源",
    "证据目录 evidence/phase-10/ 已创建并包含本地验证输出"
  ],
  "validation_commands": [
    "docker build -t delivery-api:lambda .",
    "docker run --rm -p 8080:8080 delivery-api:lambda &  curl -sf localhost:8080/health/ready",
    "terraform -chdir=infra/lambda init -backend=false",
    "terraform -chdir=infra/lambda validate",
    "terraform fmt -check -recursive infra",
    "pytest tests/test_lambda_contract.py -q",
    "project validate state",
    "git diff --check"
  ],
  "evidence_paths": [
    "evidence/phase-10/local-container-smoke.txt",
    "evidence/phase-10/terraform-validate.txt"
  ],
  "gate": "phase-10-serverless-ready",
  "issue_ids": [],
  "attempts": 0,
  "last_error_class": null
}
```

### 关键实现细节

适配器一行（版本请核对最新 tag）：

```dockerfile
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter
```

- 现有 `CMD ["uvicorn", "delivery_api.main:app", "--host", "0.0.0.0", "--port", "8080"]`
  **保持不变**。适配器默认端口即 8080，无需额外环境变量。
- `USER 10001:10001` 保持不变，Lambda 容器镜像允许非 root 运行。
- 镜像大小远低于 Lambda 10GB 限制。
- 容器冷启动约 1–2 秒，属可接受范围；**不要**启用预置并发，那会产生费用并抵消本任务目的。

### 必须遵守的边界

- **不要**修改 `src/` 下任何文件。若认为必须修改，停止并升级。
- **不要**删除或改写 `evidence/phase-9/**`，其中包含拆除前的最终取证。
- **不要**在 Terraform 中使用本地 state：phase-9 的 state 仅存在于操作者机器上，
  导致 `terraform destroy` 从克隆运行时为空操作（详见 ContinuityOps BF-2026-033）。
  本次必须配置远程后端。
- 遇到凭证、实时云、破坏性或不可逆操作，立即转入 `waiting-human` 并附 issue ID。

### 交接格式（必填全部字段）

```yaml
任务: P10-T01
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

---

## Owner steps after the worker hands off

1. Review the diff — confirm `src/` is untouched and `infra/lambda` uses a remote backend.
2. `docker build` and push to ECR; **record the new digest**.
3. `terraform -chdir=infra/lambda apply` with the new digest.
4. Smoke the Function URL against the same four endpoints, and confirm `/version`
   still returns `git_sha 376b7e18c5cc94e67ff180ca2f42b8eb05535be3`.
5. Update `app-contract/release-contract.json` in **ContinuityOps** — it pins the
   phase-9 digest and will otherwise disagree with the running artifact.
6. Confirm in Cost Explorer after 2–3 days that no ELB or ECS line has reappeared.
