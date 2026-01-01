pipeline {
  agent any

  environment {
    DOCKER_USER  = "mrlaw"
    DOCKER_IMAGE = "mrlaw/hello-app"
    IMAGE_TAG    = "snapshot-${BUILD_NUMBER}"
  }

  triggers {
    githubPush()
  }

  stages {

    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Build Docker Image') {
      steps {
        sh 'docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} .'
      }
    }

    stage('Docker Login') {
      steps {
        withCredentials([string(
          credentialsId: 'docker_hub_pw',
          variable: 'DOCKER_TOKEN'
        )]) {
          sh '''
            echo "$DOCKER_TOKEN" | docker login \
              -u ${DOCKER_USER} \
              --password-stdin
          '''
        }
      }
    }

    stage('Push Docker Image') {
      steps {
        sh '''
          docker push ${DOCKER_IMAGE}:${IMAGE_TAG}
          docker tag ${DOCKER_IMAGE}:${IMAGE_TAG} ${DOCKER_IMAGE}:latest
          docker push ${DOCKER_IMAGE}:latest
        '''
      }
    }

    stage('Deploy to Kubernetes') {
        steps {
            withCredentials([file(credentialsId: 'kubeconfig-minikube', variable: 'KUBECONFIG')]) {
                sh '''
                export KUBECONFIG=$KUBECONFIG
                kubectl get nodes
                sed -i "s|DOCKER_IMAGE|${DOCKER_IMAGE}:${IMAGE_TAG}|g" k8s/deployment.yaml
                kubectl apply -f k8s/deployment.yaml
                '''
            }
        }
    }
  }
}
