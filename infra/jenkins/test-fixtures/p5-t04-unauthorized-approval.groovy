pipeline {
  agent any
  options {
    disableConcurrentBuilds()
    timeout(time: 10, unit: 'MINUTES')
  }
  parameters {
    booleanParam(name: 'PROMOTE_PRODUCTION', defaultValue: true, description: 'Exercise the production-style approval gate')
  }
  stages {
    stage('Fixture Metadata') {
      steps {
        script {
          if (!env.PROJECT_C_ALLOWED_APPROVERS?.trim()) {
            error('PROJECT_C_ALLOWED_APPROVERS must name the local production approvers.')
          }
        }
        echo "FIXTURE_ALLOWED_APPROVERS=${env.PROJECT_C_ALLOWED_APPROVERS}"
        echo 'FIXTURE_LOCAL_ONLY_IDENTITIES=admin,approver,viewer'
      }
    }
    stage('Production Approval') {
      when { expression { params.PROMOTE_PRODUCTION } }
      steps {
        echo 'FIXTURE_AWAITING_APPROVAL'
        input(
          id: 'production-approval',
          message: 'Promote placeholder release in the local Jenkins fixture?',
          ok: 'Promote',
          submitter: env.PROJECT_C_ALLOWED_APPROVERS,
          submitterParameter: 'APPROVED_BY'
        )
      }
    }
    stage('Production') {
      when { expression { params.PROMOTE_PRODUCTION } }
      steps {
        echo 'FIXTURE_PRODUCTION_CONTINUED'
      }
    }
  }
}
