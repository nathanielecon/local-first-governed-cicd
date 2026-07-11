.PHONY: bootstrap status issues phase1 validate

bootstrap:
	python scripts/project_cli.py bootstrap --skip-docker

status:
	python scripts/project_cli.py status

issues:
	python scripts/project_cli.py issues

phase1:
	python scripts/project_cli.py phase 1 --dry-run

validate:
	python scripts/project_cli.py validate phase-1
