pipeline {
    agent any
    
    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
        IMAGE_NAME = "devopsbootcampdh/flask-todo-api"
        IMAGE_TAG = "${BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code...'
                checkout scm
            }
        }
        
        stage('Test') {
            steps {
                echo 'Running tests...'
                sh '''
                    pip3 install -r requirements.txt
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
                    echo ${DOCKERHUB_CREDENTIALS_PSW} | docker login -u ${DOCKERHUB_CREDENTIALS_USR} --password-stdin
                    docker push ${IMAGE_NAME}:${IMAGE_TAG}
                    docker push ${IMAGE_NAME}:latest
                """
            }
        }
        
        stage('Cleanup') {
            steps {
                echo 'Cleaning up...'
                sh """
                    docker rmi ${IMAGE_NAME}:${IMAGE_TAG} || true
                    docker logout
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