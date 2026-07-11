# Delivery Runbook

## First five minutes

1. Record time, release ID, commit, environment, reported symptom, and last known-good digest.
2. Do not rebuild, retag, delete containers, rotate credentials, or prune Docker yet.
3. Check `docker compose ps`, `docker ps --format '{{.Names}} {{.Image}} {{.Status}}'`, and `docker compose logs --tail 100 <service>`.
4. Probe `/health/live`, `/health/ready`, and `/version`; compare the returned SHA to the evidence manifest.
5. Inspect the environment state file and registry digest. If user impact persists and a verified previous image exists, roll back.

## Jenkins failure

- Check controller health and logs: `docker compose ps jenkins` and `docker compose logs --tail 200 jenkins`.
- Confirm checkout commit and archived reports before retrying.
- For Docker failures, inspect `/var/run/docker.sock`, controller user/group access, host Docker health, and disk space.
- For credential failures, verify the credential ID and scope; never print its value.
- Resume from a clean Jenkins run. Do not manually skip failed stages.

## Application or connectivity failure

- `docker inspect <container>` confirms image digest, user, health, environment, and network.
- `docker exec <container> getent hosts <dependency>` distinguishes DNS from application failure when the image provides the command.
- Compare listening ports, Compose networks, and service names before changing security boundaries.
- Liveness success plus readiness failure indicates the process runs but cannot safely receive traffic.

## Rollback

```powershell
./scripts/rollback.ps1 -Environment production
```

```bash
./scripts/rollback.sh production
```

After recovery, verify health, version, digest, logs, and the business endpoint. Record start/end times and preserve failed-release evidence.

