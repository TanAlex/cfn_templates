# README

Key points:

- When runway run deploy, it automatically use the git-branch name $BITBUCKET_BRANCH as 'stage'
  https://docs.onica.com/projects/runway/en/release/serverless/configuration.html  
  runway's 'deploy environment' has 1-to-1 relationship with serverless 'stage'  
  *  To use this feature, the git branch has to start with ENV-, like ENV-bal-prod, ENV-ong-dev  
     These tells runway to use bal-prod or ong-dev as its Environment (then it pass to serverless as sls's stage)
  *  To avoid using this git-branch lookup, you have to put ignore_git_branch in runway config.  
     Using DEPLOY_ENVIRONMENT will automatically set ignore_git_branch  
- apiGateway will use the 'stage' to create URL like https://xxxx.excecute-api.xxx/${stage}/your_lambda_function
- in your lambda function, use `event['requestContext']['stage']` and `os.environ['Customer_Name']` to get data you want
```
def hello(event, context):
    """Respond to incoming phone calls with a brief message."""
    stage = event['requestContext']['stage']
    # Read a message aloud to the caller
    processPress1Action = "/" + stage + "/processPress1Action"
    print("processPinActionURI:", processPress1Action)
    Name = os.environ['Customer_Name']
```