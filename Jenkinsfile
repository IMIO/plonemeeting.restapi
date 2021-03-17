pipeline {
    agent any

    triggers {
        upstream(upstreamProjects: "IMIO-github-Jenkinsfile/Products.MeetingCommunes/4.1.x", threshold: hudson.model.Result.SUCCESS)
    }

    options {
        disableConcurrentBuilds()
        parallelsAlwaysFailFast()
    }

    stages {
        stage('Build') {
            steps {
                cache(maxCacheSize: 850, caches: [[$class: 'ArbitraryFileCache', excludes: '', path: "${WORKSPACE}/eggs"]]){
                    script {
                        sh "make buildout buildout_file=jenkins.cfg"
                    }
                }
            }
        }
        stage('Code Analysis') {
            steps {
		        script {
		            sh "bin/python bin/code-analysis"
		            warnings canComputeNew: false, canResolveRelativePaths: false, parserConfigurations: [[parserName: 'Pep8', pattern: '**/parts/code-analysis/flake8.log']]
                }
            }
        }
        stage('Test Coverage') {
            steps {
                script {
                    def zServerPort = new Random().nextInt(10000) + 30000
                    sh "env ZSERVER_PORT=${zServerPort} bin/python bin/coverage run bin/test"
                    sh 'bin/python bin/coverage xml -i'
                }
            }
        }
        stage('Publish Coverage') {
            steps {
                catchError(buildResult: null, stageResult: 'FAILURE') {
                    cobertura (
                        coberturaReportFile: '**/coverage.xml',
                        conditionalCoverageTargets: '70, 50, 20',
                        lineCoverageTargets: '80, 50, 20',
                        maxNumberOfBuilds: 1,
                        methodCoverageTargets: '80, 50, 20',
                        onlyStable: false,
                        sourceEncoding: 'ASCII'
                    )
                }
            }
        }
    }
    post{
        always{
            chuckNorris()
	    sh "rm -rf src/"
        }
        aborted{
            mail to: 'pm-interne@imio.be',
                 subject: "Aborted Pipeline: ${currentBuild.fullDisplayName}",
                 body: "The pipeline ${env.JOB_NAME} ${env.BUILD_NUMBER} was aborted (${env.BUILD_URL})"

            slackSend channel: "#jenkins",
                      color: "#C0C0C0",
                      message: "Aborted ${env.JOB_NAME} ${env.BUILD_NUMBER} (<${env.BUILD_URL}|Open>)"
        }
        regression{
            mail to: 'pm-interne@imio.be',
                 subject: "Broken Pipeline: ${currentBuild.fullDisplayName}",
                 body: "The pipeline ${env.JOB_NAME} ${env.BUILD_NUMBER} is broken (${env.BUILD_URL})"

            slackSend channel: "#jenkins",
                      color: "#ff0000",
                      message: "Broken ${env.JOB_NAME} ${env.BUILD_NUMBER} (<${env.BUILD_URL}|Open>)"
        }
        fixed{
            mail to: 'pm-interne@imio.be',
                 subject: "Fixed Pipeline: ${currentBuild.fullDisplayName}",
                 body: "The pipeline ${env.JOB_NAME} ${env.BUILD_NUMBER} is back to normal (${env.BUILD_URL})"

            slackSend channel: "#jenkins",
                      color: "#00cc44",
                      message: "Fixed ${env.JOB_NAME} ${env.BUILD_NUMBER} (<${env.BUILD_URL}|Open>)"
        }
        failure{
            mail to: 'pm-interne@imio.be',
                 subject: "Failed Pipeline: ${currentBuild.fullDisplayName}",
                 body: "The pipeline${env.JOB_NAME} ${env.BUILD_NUMBER} failed (${env.BUILD_URL})"

            slackSend channel: "#jenkins",
                      color: "#ff0000",
                      message: "Failed ${env.JOB_NAME} ${env.BUILD_NUMBER} (<${env.BUILD_URL}|Open>)"
        }
    }
}
