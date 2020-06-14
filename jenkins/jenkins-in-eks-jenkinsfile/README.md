# README

https://medium.com/containerum/how-to-setup-ci-cd-workflow-for-node-js-apps-with-jenkins-and-kubernetes-360fd0499556

## Create service account
```
kubectl create sa jenkins-deployer
kubectl create clusterrolebinding jenkins-deployer-role — clusterrole=cluster-admin — serviceaccount=jenkins-deployer

kubectl get secrets
kubectl describe secret jenkins-deployer-token-jvdmf
```

## Add secret to Jenkins

Go to Credentials in the left menu of the main page, then choose System, and Add domain. You can add the name of your company for example. Then click on Add credentials in the left menu.
Fill in the form as follows:
* Kind: Secret text
* Scope: Global
* Secret: the token copied from jenkins-deployer-token-jvdmf (long string)
* ID: jenkins-deployer-credentials (same as indicated in the function withKubeConfig in the Jenkinsfile)

