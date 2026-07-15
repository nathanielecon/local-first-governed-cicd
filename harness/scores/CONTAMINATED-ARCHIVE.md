# Contaminated scoreboard archive (pre-blind-reloop)

**Archived:** 2026-07-14T21:06:00Z  
**Reason:** Advance threshold (`≥ 9.5`) was disclosed in frozen rubrics 1–7, Slice 4 `S4-10-02`, judge prompts, and SCOREBOARD advance wording. Scores below are **non-authoritative** for pass claims. Live SCOREBOARD reset to `reloop pending`.

---

# Slice scoreboard (contaminated original)

## Slice 1 — core-harness
| Round | Judge | Score | Must-haves |
|---|---|---:|---|
| R1 | B (`c51e07c3`) | 9.0 | PASS |
| R2 | Orchestrator after residual + score log | 9.7 | PASS |
| R3 | Final (`fc617aa1`) | 10.0 | PASS |
| **Average** | | **9.57** | PASS |

## Slice 2 — phase5-jenkins-auth
| Judge | Score | Must-haves |
|---|---:|---|
| #1 (`7613f19a`) | 10.0 | PASS |
| #2 (`953b1c12`) | 10.0 | PASS |
| #3 (`a1bf60a1`) | 9.7 | PASS |
| **Average** | **9.90** | PASS |

## Slice 3 — phase67-promote-verify
| Judge | Score | Must-haves |
|---|---:|---|
| #1 (`d0d2e46a`) | 10.0 | PASS |
| #2 (`bc4e2979`) | 10.0 | PASS |
| #3 (`dc3e4f1c`) | 10.0 | PASS |
| **Average** | **10.00** | PASS |

## Slice 4 — final-delivery
| Judge | Score | Notes |
|---|---:|---|
| Final (`af80ce56`) | 9.5 | S4-10-01 was dirty scoreboard; closing commit addresses |
| Remote gate | PASS | `gh pr checks 2` all green |

## Slice 5 — app-api (accuracy partition)
| Judge | Score | Must-haves | Log |
|---|---|---:|---|---|
| #1 (`7624d7d2`) | 10.0 | PASS | harness/logs/s5j1.md |
| #2 (`fe36570a`) | 10.0 | PASS | harness/logs/s5j2.md |
| #3 (`007f68d9`) | 10.0 | PASS | harness/logs/s5j3.md |
| **Average** | **10.00** | PASS | |

## Slice 6 — smoke-harness (accuracy partition)
| Judge | Score | Must-haves | Log |
|---|---|---:|---|---|
| #1 (`f1c254e7`) | 10.0 | PASS | harness/logs/s6j1.md |
| #2 (`ee7c49f2`) | 10.0 | PASS | harness/logs/s6j2.md |
| #3 (`ab003d05`) | 10.0 | PASS | harness/logs/s6j3.md |
| **Average** | **10.00** | PASS | |

## Slice 7 — skills-ci-meta (accuracy partition)
| Judge | Score | Must-haves | Log |
|---|---|---:|---|---|
| #1 (`32f021e3`) | 10.0 | PASS | harness/logs/s7j1.md |
| #2 (`c4fbb28f`) | 10.0 | PASS | harness/logs/s7j2.md |
| #3 (`9aa08c87`) | 10.0 | PASS | harness/logs/s7j3.md |
| **Average** | **10.00** | PASS | |

## Local + remote verification commands
```
python -m ruff format --check .
python -m ruff check .
python -m mypy src
python -m pytest -q
python scripts/validate_jenkinsfile.py Jenkinsfile
python scripts/project_cli.py validate state
python scripts/project_cli.py validate skills
gh pr checks 2
```
