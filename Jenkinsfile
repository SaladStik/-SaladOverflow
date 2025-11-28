pipeline {
    agent any
    
    environment {
        COMPOSE_PROJECT_NAME = 'saladoverflow'
        DOCKER_COMPOSE_FILE = 'backend/docker-compose.yml'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code...'
                checkout scm
            }
        }
        
        stage('Build') {
            steps {
                echo 'Building Docker images...'
                script {
                    dir('backend') {
                        sh 'docker-compose build --no-cache'
                    }
                }
            }
        }
        
        stage('Stop Old Containers') {
            steps {
                echo 'Stopping old containers...'
                script {
                    dir('backend') {
                        sh 'docker-compose down || true'
                    }
                }
            }
        }
        
        stage('Deploy') {
            steps {
                echo 'Deploying new containers...'
                script {
                    dir('backend') {
                        sh 'docker-compose up -d'
                    }
                }
            }
        }
        
        stage('Health Check') {
            steps {
                echo 'Waiting for services to be healthy...'
                script {
                    sleep(time: 15, unit: 'SECONDS')
                    dir('backend') {
                        sh 'docker-compose ps'
                    }
                }
            }
        }
        
        stage('Cleanup') {
            steps {
                echo 'Cleaning up unused Docker resources...'
                sh 'docker system prune -f --volumes || true'
            }
        }
    }
    
    post {
        success {
            echo 'Deployment successful! 🎉'
        }
        failure {
            echo 'Deployment failed! ❌'
            script {
                dir('backend') {
                    sh 'docker-compose logs --tail=50'
                }
            }
        }
        always {
            echo 'Pipeline completed.'
        }
    }
}
