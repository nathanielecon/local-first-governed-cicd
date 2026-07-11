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
  }
  environment {
    IMAGE_NAME = 'delivery-api'
    CI_PROVIDER = 'jenkins'
  }
  stages {
    stage('Metadata') {
      steps {
        script {
          env.GIT_SHA = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
          env.SHORT_SHA = env.GIT_SHA.take(12)
          env.APP_VERSION = sh(returnStdout: true, script: "python3 -c \"import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])\"").trim()
          env.RELEASE_ID = "${env.APP_VERSION}-${env.BUILD_NUMBER}-${env.SHORT_SHA}"
          env.IMAGE_REF = "${env.REGISTRY}/${env.IMAGE_NAME}:sha-${env.SHORT_SHA}"
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
          docker image inspect --format='{{index .RepoDigests 0}}' "$IMAGE_REF" > image-digest.txt
        '''
        script { env.IMAGE_DIGEST = readFile('image-digest.txt').trim() }
      }
    }
    stage('Staging') {
      steps {
        sh './scripts/deploy.sh staging "$IMAGE_DIGEST" "$GIT_SHA"'
        sh '''python3 scripts/evidence.py --release-id "$RELEASE_ID" --status staging_verified --commit-sha "$GIT_SHA" --image-ref "$IMAGE_REF" --image-digest "$IMAGE_DIGEST" --environment staging'''
      }
    }
    stage('Production Approval') {
      when { expression { params.PROMOTE_PRODUCTION } }
      steps {
        input message: "Promote verified digest ${env.IMAGE_DIGEST} to production?", ok: 'Promote', submitterParameter: 'APPROVED_BY'
      }
    }
    stage('Production') {
      when { expression { params.PROMOTE_PRODUCTION } }
      steps {
        script {
          env.ROLLBACK_DIGEST = sh(returnStdout: true, script: "sed -n 's/^PRODUCTION_IMAGE=//p' deploy/state/production.env 2>/dev/null || true").trim()
        }
        sh './scripts/deploy.sh production "$IMAGE_DIGEST" "$GIT_SHA"'
        sh '''python3 scripts/evidence.py --release-id "$RELEASE_ID" --status production_verified --commit-sha "$GIT_SHA" --image-ref "$IMAGE_REF" --image-digest "$IMAGE_DIGEST" --rollback-digest "$ROLLBACK_DIGEST" --environment production'''
      }
    }
  }
  post {
    always {
      archiveArtifacts allowEmptyArchive: true, artifacts: 'coverage.xml,image-digest.txt,evidence/**/*'
      cleanWs(deleteDirs: true, notFailBuild: true)
    }
    failure {
      echo 'Pipeline failed. Deployment scripts automatically restore the previous recorded image when verification fails.'
    }
  }
}

