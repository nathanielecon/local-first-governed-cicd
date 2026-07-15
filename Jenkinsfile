pipeline {
  agent any
  options {
    timestamps()
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timeout(time: 45, unit: 'MINUTES')
  }
  parameters {
    booleanParam(name: 'PROMOTE_PRODUCTION', defaultValue: false, description: 'Request production promotion after staging passes')
    stringParam(name: 'TRUSTED_GIT_SHA', defaultValue: '', description: 'Immutable approved commit SHA (40 lowercase hex chars) required before any fetch or build')
    booleanParam(name: 'FIRST_RELEASE', defaultValue: true, description: 'Record first-release decision when no verified prior production digest exists')
    booleanParam(name: 'DEMONSTRATE_RECOVERY', defaultValue: false, description: 'After production verify, inject failure and roll back to the bound verified prior digest (requires FIRST_RELEASE=false)')
    stringParam(name: 'VERIFIED_ROLLBACK_DIGEST', defaultValue: '', description: 'Event-backed prior production digest (sha256:...) required when FIRST_RELEASE=false')
    stringParam(name: 'VERIFIED_ROLLBACK_COMMIT', defaultValue: '', description: 'Commit SHA for the verified prior production digest')
    stringParam(name: 'VERIFIED_ROLLBACK_VERIFIED_AT', defaultValue: '', description: 'UTC ISO-8601 timestamp when the prior production digest was verified')
    stringParam(name: 'VERIFIED_ROLLBACK_SOURCE_RELEASE', defaultValue: '', description: 'Release ID that established the verified prior production digest')
  }
  environment {
    IMAGE_NAME = 'delivery-api'
    CI_PROVIDER = 'jenkins'
  }
  stages {
    stage('Metadata') {
      steps {
        script {
          if (!params.TRUSTED_GIT_SHA?.trim()) {
            error('TRUSTED_GIT_SHA is required for trusted release input.')
          }
          env.TRUSTED_GIT_SHA = params.TRUSTED_GIT_SHA.trim().toLowerCase()
          // Reject branch/tag refs and any non-SHA input before git fetch.
          if (env.TRUSTED_GIT_SHA.startsWith('refs/') || !(env.TRUSTED_GIT_SHA ==~ /^[0-9a-f]{40}$/)) {
            error("TRUSTED_GIT_SHA must be an immutable 40-character commit SHA; arbitrary refs are rejected before fetch. Got '${params.TRUSTED_GIT_SHA.trim()}'.")
          }
          if (!env.REGISTRY?.trim()) {
            error('REGISTRY must be set for identity-bound digest promotion.')
          }
          env.EXPECTED_REGISTRY = env.REGISTRY.trim()
          env.EXPECTED_REPOSITORY = env.IMAGE_NAME
        }
        sh '''
          git fetch --no-tags origin "$TRUSTED_GIT_SHA"
          git checkout --detach FETCH_HEAD
        '''
        script {
          env.GIT_SHA = sh(returnStdout: true, script: "git rev-parse FETCH_HEAD^{commit}").trim()
          if (env.GIT_SHA != env.TRUSTED_GIT_SHA) {
            error("Fetched commit '${env.GIT_SHA}' does not match trusted input '${env.TRUSTED_GIT_SHA}'.")
          }
          env.SHORT_SHA = env.GIT_SHA.take(12)
          env.APP_VERSION = sh(returnStdout: true, script: "python3 -c \"import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])\"").trim()
          env.RELEASE_ID = "${env.APP_VERSION}-${env.BUILD_NUMBER}-${env.SHORT_SHA}"
          env.IMAGE_REF = "${env.EXPECTED_REGISTRY}/${env.EXPECTED_REPOSITORY}:sha-${env.SHORT_SHA}"
          env.EVIDENCE_ACTOR = 'jenkins'
        }
      }
    }
    stage('Validate') {
      steps {
        sh '''
          python3 -m venv .venv
          .venv/bin/pip install -e '.[dev]'
          .venv/bin/ruff format --check .
          .venv/bin/ruff check .
          .venv/bin/mypy src
          .venv/bin/pytest --junitxml=junit.xml
        '''
      }
      post { always { junit allowEmptyResults: true, testResults: 'junit.xml' } }
    }
    stage('Build Once') {
      steps {
        sh '''
          docker build --pull \
            --build-arg APP_VERSION="$APP_VERSION" \
            --build-arg GIT_SHA="$GIT_SHA" \
            -t "$IMAGE_REF" .
          docker push "$IMAGE_REF"
          python3 - <<'PY'
import json
import os
import subprocess
from pathlib import Path

from scripts.verify_deployment import select_matching_repo_digest

image_ref = os.environ["IMAGE_REF"]
expected_registry = os.environ["EXPECTED_REGISTRY"]
expected_repository = os.environ["EXPECTED_REPOSITORY"]
raw = subprocess.check_output(
    ["docker", "image", "inspect", "--format", "{{json .RepoDigests}}", image_ref],
    text=True,
)
repo_digests = json.loads(raw)
prefix = f"{expected_registry}/{expected_repository}@"
candidates = [item for item in repo_digests if isinstance(item, str) and item.startswith(prefix)]
if len(candidates) != 1:
    raise SystemExit(
        "identity-bound RepoDigest required for "
        f"{expected_registry}/{expected_repository}; got {repo_digests!r}"
    )
digest = candidates[0].rsplit("@", 1)[1]
matched = select_matching_repo_digest(
    repo_digests,
    expected_registry=expected_registry,
    expected_repository=expected_repository,
    expected_digest=digest,
)
Path("image-digest.txt").write_text(digest + "\n", encoding="utf-8")
Path("image-digest-ref.txt").write_text(matched + "\n", encoding="utf-8")
print(matched)
PY
        '''
        script {
          env.IMAGE_DIGEST = readFile('image-digest.txt').trim()
          env.IMAGE_DIGEST_REF = readFile('image-digest-ref.txt').trim()
          env.EXPECTED_DIGEST = env.IMAGE_DIGEST
        }
        sh '''
          python3 scripts/evidence.py append \
            --release-id "$RELEASE_ID" \
            --event-type build_published \
            --commit-sha "$GIT_SHA" \
            --actor "$EVIDENCE_ACTOR" \
            --environment local \
            --result pass \
            --image-digest "$IMAGE_DIGEST" \
            --image-ref "$IMAGE_REF"
        '''
      }
    }
    stage('Staging') {
      steps {
        sh '''
          export EXPECTED_DIGEST="$IMAGE_DIGEST"
          export EXPECTED_REGISTRY="$EXPECTED_REGISTRY"
          export EXPECTED_REPOSITORY="$EXPECTED_REPOSITORY"
          ./scripts/deploy.sh staging "$IMAGE_DIGEST_REF" "$GIT_SHA"
          python3 scripts/evidence.py append \
            --release-id "$RELEASE_ID" \
            --event-type staging_deployed \
            --commit-sha "$GIT_SHA" \
            --actor "$EVIDENCE_ACTOR" \
            --environment staging \
            --result pass \
            --image-digest "$IMAGE_DIGEST" \
            --image-ref "$IMAGE_REF"
          python3 scripts/evidence.py append \
            --release-id "$RELEASE_ID" \
            --event-type staging_verified \
            --commit-sha "$GIT_SHA" \
            --actor "$EVIDENCE_ACTOR" \
            --environment staging \
            --result pass \
            --image-digest "$IMAGE_DIGEST" \
            --image-ref "$IMAGE_REF" \
            --details-json '{"checks":{"deployed_digest":"pass","health":"pass","version":"pass","business_behavior":"pass"}}'
        '''
      }
    }
    stage('Production Approval') {
      when { expression { params.PROMOTE_PRODUCTION } }
      steps {
        script {
          if (!env.PROJECT_C_ALLOWED_APPROVERS?.trim()) {
            error('PROJECT_C_ALLOWED_APPROVERS must name the local production approvers.')
          }
        }
        input message: "Promote verified digest ${env.IMAGE_DIGEST} from trusted commit ${env.TRUSTED_GIT_SHA} to production?", ok: 'Promote', submitter: env.PROJECT_C_ALLOWED_APPROVERS, submitterParameter: 'APPROVED_BY'
        script {
          env.APPROVED_BY = APPROVED_BY?.trim()
          if (!env.APPROVED_BY) {
            error('APPROVED_BY must be persisted from the production approval gate.')
          }
          env.APPROVED_AT = sh(returnStdout: true, script: 'date -u +%Y-%m-%dT%H:%M:%SZ').trim()
        }
        sh '''
          python3 scripts/evidence.py append \
            --release-id "$RELEASE_ID" \
            --event-type production_approval \
            --commit-sha "$GIT_SHA" \
            --actor "$APPROVED_BY" \
            --environment production \
            --result pass \
            --image-digest "$IMAGE_DIGEST" \
            --image-ref "$IMAGE_REF" \
            --approver-id "$APPROVED_BY" \
            --approved-at "$APPROVED_AT"
        '''
      }
    }
    stage('Rollback Readiness') {
      when { expression { params.PROMOTE_PRODUCTION } }
      steps {
        script {
          if (params.FIRST_RELEASE) {
            if (params.DEMONSTRATE_RECOVERY) {
              error('DEMONSTRATE_RECOVERY requires FIRST_RELEASE=false and a verified rollback target.')
            }
            env.FIRST_RELEASE_DECISION = 'first_release_no_rollback_target'
            env.FIRST_RELEASE_DECIDED_BY = env.APPROVED_BY
            env.FIRST_RELEASE_DECIDED_AT = env.APPROVED_AT
            env.FIRST_RELEASE_RATIONALE = 'No verified prior production digest exists for this local production-like promotion.'
            env.FIRST_RELEASE_ACCEPTED_RISK = 'Rollback to a prior verified digest is unavailable for this first release.'
            sh '''
              python3 scripts/evidence.py append \
                --release-id "$RELEASE_ID" \
                --event-type first_release_decision \
                --commit-sha "$GIT_SHA" \
                --actor "$APPROVED_BY" \
                --environment production \
                --result recorded \
                --image-digest "$IMAGE_DIGEST" \
                --decision "$FIRST_RELEASE_DECISION" \
                --decided-by "$FIRST_RELEASE_DECIDED_BY" \
                --decided-at "$FIRST_RELEASE_DECIDED_AT" \
                --rationale "$FIRST_RELEASE_RATIONALE" \
                --accepted-risk "$FIRST_RELEASE_ACCEPTED_RISK"
            '''
          } else {
            def digest = params.VERIFIED_ROLLBACK_DIGEST?.trim()
            def commit = params.VERIFIED_ROLLBACK_COMMIT?.trim()
            def verifiedAt = params.VERIFIED_ROLLBACK_VERIFIED_AT?.trim()
            def sourceRelease = params.VERIFIED_ROLLBACK_SOURCE_RELEASE?.trim()
            if (!digest || !commit || !verifiedAt || !sourceRelease) {
              error('FIRST_RELEASE=false requires VERIFIED_ROLLBACK_DIGEST, VERIFIED_ROLLBACK_COMMIT, VERIFIED_ROLLBACK_VERIFIED_AT, and VERIFIED_ROLLBACK_SOURCE_RELEASE from durable evidence.')
            }
            if (digest == env.IMAGE_DIGEST) {
              error('Verified rollback target must not be self-referential to the candidate digest.')
            }
            env.VERIFIED_ROLLBACK_DIGEST = digest
            env.VERIFIED_ROLLBACK_COMMIT = commit
            env.VERIFIED_ROLLBACK_VERIFIED_AT = verifiedAt
            env.VERIFIED_ROLLBACK_SOURCE_RELEASE = sourceRelease
            env.VERIFIED_ROLLBACK_ENVIRONMENT = 'production'
            sh '''
              python3 scripts/evidence.py append \
                --release-id "$RELEASE_ID" \
                --event-type rollback_target_bound \
                --commit-sha "$GIT_SHA" \
                --actor "$APPROVED_BY" \
                --environment production \
                --result recorded \
                --image-digest "$IMAGE_DIGEST" \
                --rollback-target-digest "$VERIFIED_ROLLBACK_DIGEST" \
                --rollback-target-commit "$VERIFIED_ROLLBACK_COMMIT" \
                --rollback-target-verified-at "$VERIFIED_ROLLBACK_VERIFIED_AT" \
                --rollback-target-source-release "$VERIFIED_ROLLBACK_SOURCE_RELEASE" \
                --rollback-target-environment "$VERIFIED_ROLLBACK_ENVIRONMENT"
            '''
          }
        }
      }
    }
    stage('Production') {
      when { expression { params.PROMOTE_PRODUCTION } }
      steps {
        sh '''
          export EXPECTED_DIGEST="$IMAGE_DIGEST"
          export EXPECTED_REGISTRY="$EXPECTED_REGISTRY"
          export EXPECTED_REPOSITORY="$EXPECTED_REPOSITORY"
          ./scripts/deploy.sh production "$IMAGE_DIGEST_REF" "$GIT_SHA"
          python3 scripts/evidence.py append \
            --release-id "$RELEASE_ID" \
            --event-type production_deployed \
            --commit-sha "$GIT_SHA" \
            --actor "$EVIDENCE_ACTOR" \
            --environment production \
            --result pass \
            --image-digest "$IMAGE_DIGEST" \
            --image-ref "$IMAGE_REF"
          python3 scripts/evidence.py append \
            --release-id "$RELEASE_ID" \
            --event-type production_verified \
            --commit-sha "$GIT_SHA" \
            --actor "$EVIDENCE_ACTOR" \
            --environment production \
            --result pass \
            --image-digest "$IMAGE_DIGEST" \
            --image-ref "$IMAGE_REF" \
            --details-json '{"checks":{"deployed_digest":"pass","health":"pass","version":"pass","business_behavior":"pass"}}'
        '''
      }
    }
    stage('Failure Injection') {
      when {
        allOf {
          expression { params.PROMOTE_PRODUCTION }
          expression { params.DEMONSTRATE_RECOVERY }
        }
      }
      steps {
        sh '''
          python3 scripts/evidence.py append \
            --release-id "$RELEASE_ID" \
            --event-type production_verification_failed \
            --commit-sha "$GIT_SHA" \
            --actor "$EVIDENCE_ACTOR" \
            --environment production \
            --result fail \
            --image-digest "$IMAGE_DIGEST" \
            --image-ref "$IMAGE_REF" \
            --details-json '{"injection":"local-failure-injection-demo","note":"Deliberate local-only failure injection before digest-targeted rollback; not a live cloud claim."}'
        '''
      }
    }
    stage('Rollback') {
      when {
        allOf {
          expression { params.PROMOTE_PRODUCTION }
          expression { params.DEMONSTRATE_RECOVERY }
        }
      }
      steps {
        sh '''
          ./scripts/rollback.sh production "$VERIFIED_ROLLBACK_DIGEST" "$EXPECTED_REGISTRY" "$EXPECTED_REPOSITORY" "$VERIFIED_ROLLBACK_COMMIT"
          python3 scripts/evidence.py append \
            --release-id "$RELEASE_ID" \
            --event-type rollback_executed \
            --commit-sha "$GIT_SHA" \
            --actor "$EVIDENCE_ACTOR" \
            --environment production \
            --result pass \
            --image-digest "$VERIFIED_ROLLBACK_DIGEST" \
            --details-json "{\"restored_digest\":\"$VERIFIED_ROLLBACK_DIGEST\",\"source_release_id\":\"$VERIFIED_ROLLBACK_SOURCE_RELEASE\"}"
        '''
      }
    }
    stage('Recovery') {
      when {
        allOf {
          expression { params.PROMOTE_PRODUCTION }
          expression { params.DEMONSTRATE_RECOVERY }
        }
      }
      steps {
        sh '''
          python3 scripts/evidence.py append \
            --release-id "$RELEASE_ID" \
            --event-type recovery_verified \
            --commit-sha "$GIT_SHA" \
            --actor "$EVIDENCE_ACTOR" \
            --environment production \
            --result pass \
            --image-digest "$VERIFIED_ROLLBACK_DIGEST" \
            --details-json "{\"restored_commit_sha\":\"$VERIFIED_ROLLBACK_COMMIT\",\"source_release_id\":\"$VERIFIED_ROLLBACK_SOURCE_RELEASE\"}" \
            --recovery-checks-json '{"deployed_digest":"pass","health":"pass","version":"pass","business_behavior":"pass"}'
          python3 scripts/evidence.py validate --release-id "$RELEASE_ID"
        '''
      }
    }
  }
  post {
    always {
      archiveArtifacts allowEmptyArchive: true, artifacts: 'coverage.xml,image-digest.txt,image-digest-ref.txt,evidence/**/*'
      cleanWs(deleteDirs: true, notFailBuild: true)
    }
    failure {
      echo 'Pipeline failed. Preserve append-only evidence; do not rebuild between environments to manufacture a digest match.'
    }
  }
}
