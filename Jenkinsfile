pipeline {
  environment {
    imagename = "niharpatil123/nihargit.git"
    registryCredential = 'docker-hub'
    dockerImage = ''
  }
  agent any
  stages {
    stage('Cloning Git') {
      steps {
		  git([url: 'https://github.com/niharpatil123/nihargit.git', branch: 'main', passwordVariable: 'Chakuli@11', usernameVariable: 'niharpatil123' ])

      }
    }
    stage('Building image') {
      steps{
        script {
          dockerImage = docker.build imagename
        }
      }
    }
    stage('Push Image') {
      steps{
        script {
          docker.withRegistry( '', registryCredential ) {
            dockerImage.push("$BUILD_NUMBER")
             dockerImage.push('latest')

          }
        }
      }
    }
    stage('Deploy image and Remove Unused  image') {
      steps{
        sh "docker stop myimage"
        sh "docker rm myimage"
        sh "docker run -d -p 80:80 --name myimage $imagename:$BUILD_NUMBER"
        sh "docker rmi $imagename:$BUILD_NUMBER"

      }
    }
  }
}
