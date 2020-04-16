https://github.com/aws-quickstart/quickstart-examples/tree/develop/samples/hugo-pipeline/templates

https://aws.amazon.com/blogs/infrastructure-and-automation/building-a-ci-cd-pipeline-for-hugo-websites/

CodeCommit to hold the git repo
Any PR push trigger CW Event then target a CodePipeline run
Codepipeline has a Project with Phases to build and push to s3