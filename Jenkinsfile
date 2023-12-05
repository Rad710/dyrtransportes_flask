
pipeline {
    agent any
    
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
                    echo "WORKSPACE is: ${WORKSPACE}"

                    // createGitHubRelease(
                    //         credentialId: 'jenkgit',
                    //         repository: 'Rad710/dyrtransportes_flask',
                    //         tag: '0.0.0',
                    //         commitish: 'main',
                    //         // bodyFile: 'test.md',
                    //         // draft: true
                    // )
                }
            }
        }

        
        stage('Tag GIT Repo') {
            steps {
                script {       
                    echo "GIT TAG: 0.0.9"             
                    sshagent (credentials: ["jenkins-app-secret"]) {
                        sh 'git tag -a 0.0.9 -m "aaaaa"'
                        sh "git push git@github.com:Rad710/dyrtransportes_flask.git 0.0.9"
                        sh "git tag -d 0.0.9"
                    }
                }
            }
        }

        
    stage('Check run') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'jenkins-github-app',
                                          usernameVariable: 'GITHUB_APP',
                                          passwordVariable: 'GITHUB_ACCESS_TOKEN')]) {
            sh '''            
            curl -L \
                  -X POST \
                  -H "Accept: application/vnd.github+json" \
                  -H "Authorization: Bearer ${GITHUB_ACCESS_TOKEN}" \
                  -H "X-GitHub-Api-Version: 2022-11-28" \
                  https://api.github.com/repos/Rad710/dyrtransportes_flask/releases \
                  -d '{"tag_name":"v1.0.0", \
                          "target_commitish":"main", \
                          "name":"v1.0.0", \
                          "body":"Description of the release", \
                          "draft":false, \
                          "prerelease":false, \
                          "generate_release_notes":false}'
            '''
        }
      }
    }
//         // stage('Checkout') {
//         //     steps {
//         //         script {
//         //             //                     //Send build result to Github
//         //             // publishChecks name: 'Checkout', 
//         //             //     title: 'Cloning repository', 
//         //             //     conclusion: 'NONE',
//         //             //     status: 'IN_PROGRESS'
                    
//         //             // echo "Cloning rep..."
//         //             checkout scm
//         //         }
//         //     }

//         // //     post {
//         // //         success {
//         // //             //Send build result to Github
//         // //             publishChecks name: 'Checkout', 
//         // //                 title: 'Cloning repository', 
//         // //                 summary: 'Cloning repository from source',
//         // //                 text: 'Texto',
//         // //                 detailsURL: 'https://google.com',
//         // //                 conclusion: 'SUCCESS'
//         // //         }
//         // //         failure {
//         // //             //Send build result to Github
//         // //             publishChecks name: 'Cloning Repo1', 
//         // //                 title: 'Cloning Repo2', 
//         // //                 summary: 'Cloning Repo3',
//         // //                 text: 'Cloning Repo4',
//         // //                 detailsURL: 'https://google.com',
//         // //                 conclusion: 'FAILURE'
//         // //         }
//         // //     }
//         // }
        
//         stage('Build project') {
//             steps {
//                 script {
//                     echo "Building..."
//                     // if (env.CHANGE_ID) {
//                     //     echo "This build is associated with a pull request ${env.BRANCH_NAME}: #${env.CHANGE_ID}"
//                     // } else {
//                     //     echo "This build is associated with a branch: ${env.BRANCH_NAME}"
//                     // }

//                     sh """
//                         git status
//                         git branch -r
//                         """
//                 }
//             }
//         }
    }
    
    post {
        // always {
            // script {

//                 commit = sh(returnStdout: true, script: 'git log -1 --oneline').trim()
//                 // echo "$commit"

//                 author = sh(script: "git show -s --pretty=%an", returnStdout: true).trim()
//                 email = sh(script: "git show -s --pretty=%ae", returnStdout: true).trim()

//                 echo "Author: ${author}. Email: ${email}"
//                 // sh "git show"
//                 // user = currentBuild.getBuildCauses() //initiated from Jenkins
//                 // echo "User: ${user}"

//                 // git rev-list --count 39745114e1b606a918981c6b334138c9eb0c4e8a..c1c56a398774daac8aefd4100ff4cdf98122ff15
//                 // git log --oneline 39745114e1b606a918981c6b334138c9eb0c4e8a..c1c56a398774daac8aefd4100ff4cdf98122ff15
                

//                     // sh "git rev-list --count aaa..bbb"

//                 githubData = [:]
//                 githubData['commit'] = GIT_COMMIT

//                 // Check if the input string matches the pattern
//                 if (env.CHANGE_ID) {
//                     echo "Pull Request!"
//                     githubData['authorUsername'] = env.CHANGE_AUTHOR.toLowerCase()
//                     githubData['authorName'] = env.CHANGE_AUTHOR_DISPLAY_NAME
//                 } else {
//                     echo "Push!"
//                     githubData['authorUsername'] = email.split("\\+")[1].split("@")[0].toLowerCase()
//                     githubData['authorName'] = author
//                 }

//                 def customMeasurementFields = [:]
//                 customMeasurementFields['github_data'] = githubData
                
//                 echo "${customMeasurementFields}"
//                 influxDbPublisher(selectedTarget: 'InfluxDB', customDataMap: customMeasurementFields)
//             }
//         }
        success {
            echo "Success!"
        }
        failure {
            echo "Failure!"
        }
    }
}
