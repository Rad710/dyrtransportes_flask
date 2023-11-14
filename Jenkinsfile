pipeline {
    agent any
    
    tools {
        nodejs '21.1.0'
    }
    stages {
        stage ('Prepare')
        {
            steps {
                script {
                    sh 'printenv'
                    script {
                        params.each() { param, value ->
                            print "Parameter: ${param}, Value: ${value}"
                        }
                    }
                    echo "PATH is: $PATH"
                }
            }
        }
        stage('Checkout') {
            steps {
                script {
                                        //Send build result to Github
                    publishChecks name: 'Cloning Repo', 
                        title: 'Cloning Repo', 
                        summary: 'Cloning Repo',
                        text: 'The Jenkins Pipeline...',
                        detailsURL: 'https://jenkins.roshka.com/job/rshkap-model-build-test',
                        conclusion: 'NONE',
                        status: 'IN_PROGRESS'
                    
                    echo "Cloning rep..."
                    checkout scm
                }
            }

            post {
                success {
                                //Send build result to Github
                    publishChecks name: 'Cloning Repo', 
                        title: 'Cloning Repo', 
                        summary: 'Cloning Repo',
                        text: 'The Jenkins Pipeline...',
                        detailsURL: 'https://google.com',
                        conclusion: 'SUCCESS'
                }

            }
        }
        
        stage('Build project') {
            steps {
                script {
                    echo "Building..."
                    if (env.CHANGE_ID) {
                        echo "This build is associated with a pull request ${env.BRANCH_NAME}: #${env.CHANGE_ID}"
                    } else {
                        echo "This build is associated with a branch: ${env.BRANCH_NAME}"
                    }

                    sh """
                        git status
                        git branch -r
                        """
                }
            }
        }
    }
    
    post {
        success {
            echo "Success!"
        }
        failure {
            echo "Failure!"
        }
    }
}
