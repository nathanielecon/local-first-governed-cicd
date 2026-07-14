# Cloud Agents environment pin (orchestrator)

**Recorded:** 2026-07-14T21:10:00Z  
**Repo:** `nathanielecon/project-c-cloud` (this workspace)

## Policy

1. Prefer this repo’s `.cursor/environment.json` for Cloud Agent sessions on Project C.
2. Install is a **version check only** (Python/git/gh + optional terraform/aws/docker). Do not bake secrets, AWS keys, or GitHub tokens into the image or install script.
3. Prefer Cursor **snapshot reuse** over cold reinstalls when the env hash is unchanged.
4. Cloud Agents **edit the repo**; they are **not** the AWS/GitOps apply control plane. Live applies stay on CI / human-gated workflows.
5. Related shared harness repo `nathanielecon/cloud`: Cloud Agent toolchain baseline commit `6a8be570831b2a5e599452105e1422fb4adf508e` is an ancestor of `main` (verified 2026-07-14). Do not start Cloud Agent work on that repo from commits older than `6a8be57`.
