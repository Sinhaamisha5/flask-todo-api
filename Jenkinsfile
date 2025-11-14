pipeline {
    agent {
        docker {
            image 'python:3.11-slim'
            args '-v /var/run/docker.sock:/var/run/docker.sock -u root'
        }
    }
    
    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
        IMAGE_NAME = "devopsbootcampdh/flask-todo-api"
        IMAGE_TAG = "${BUILD_NUMBER}"
    }
    
    stages {
        stage('Debug') {
            steps {
                echo 'Checking Jenkinsfile contents...'
                sh 'head -20 Jenkinsfile'
                sh 'pwd'
                sh 'ls -la'
            }
        }

        stage('Setup') {
            steps {
                echo 'Installing Docker CLI inside container...'
                sh '''
                    apt-get update -qq
                    apt-get install -y docker.io
                '''
            }
        }
        
        stage('Test') {
            steps {
                echo 'Running tests...'
                sh '''
                    pip install --no-cache-dir -r requirements.txt
                    pytest -v --cov=app tests/
                '''
            }
        }
        
        stage('Build') {
            steps {
                echo 'Building Docker image...'
                sh """
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:latest
                """
            }
        }
        
        stage('Push') {
            steps {
                echo 'Pushing to DockerHub...'
                sh """
                    echo \${DOCKERHUB_CREDENTIALS_PSW} | docker login -u \${DOCKERHUB_CREDENTIALS_USR} --password-stdin
                    docker push ${IMAGE_NAME}:${IMAGE_TAG}
                    docker push ${IMAGE_NAME}:latest
                    docker logout
                """
            }
        }
        
        stage('Cleanup') {
            steps {
                echo 'Cleaning up...'
                sh """
                    docker rmi ${IMAGE_NAME}:${IMAGE_TAG} || true
                    docker rmi ${IMAGE_NAME}:latest || true
                """
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline succeeded! ✅'
        }
        failure {
            echo 'Pipeline failed! ❌'
        }
        always {
            echo 'Cleaning workspace...'
            cleanWs()
        }
    }
}