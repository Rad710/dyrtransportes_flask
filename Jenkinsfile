pipeline {
    agent any
    
    tools {
        nodejs '21.1.0'
    }
    stages {
        stage('Prepare') {
            steps {
                echo "Preparing..."
                echo "Environment variables: ${env}"
            }
        }
        stage('Checkout') {
            steps {
                echo "Cloning repo...."
                checkout scm
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
                        ls
                        """
                }
            }
            post {
                success {
                    //Send build result to Github
                    publishChecks name: 'Preview Build', 
                        title: 'Pipeline Check', 
                        summary: 'Checking merge',
                        text: 'The Jenkins Pipeline...',
                        detailsURL: 'url.url',
                        conclusion: 'SUCCESS'
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
