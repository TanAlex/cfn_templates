REGION ?= us-east-1
STACK_NAME ?= trend-mirco-dssc
ECR_STACK_NAME ?= ${STACK_NAME}-ecr
WEBHOOK_STACK_NAME ?= ${STACK_NAME}-webhook
PIPELINE_STACK_NAME ?= ${STACK_NAME}-pipeline
DSSC_SSM_STACK_NAME ?= ${STACK_NAME}-ssm

ECR_REPOSITORY_IMAGE_URI := $$(aws ecr describe-repositories --query "repositories[?repositoryName=='${ECR_STACK_NAME}'].repositoryUri" --output text)
ARTIFACT_BUCKET_NAME=$$(aws ssm get-parameter --name /pipeline/example/trendmicro/artifactbucket/name --query "Parameter.Value" --output text)
PIPELINE_EXECUTION_ID := $$(aws codepipeline get-pipeline-state --name ${PIPELINE_STACK_NAME} --query "stageStates[?stageName=='Source'].latestExecution.pipelineExecutionId" --output text)

DSSC_URL := $$(kubectl get svc proxy -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
DSSC_USER := $$(kubectl get secrets -o jsonpath='{ .data.userName }' deepsecurity-smartcheck-auth | base64 --decode)
DSSC_DEFAULT_PASSWORD := $$(kubectl get secrets -o jsonpath='{ .data.password }' deepsecurity-smartcheck-auth | base64 --decode)
DSSC_SECRET := $$(aws kms generate-random --number-of-bytes 32 --query 'Plaintext' --output text)
DSSC_NEW_PASSWORD := $$(aws kms generate-random --number-of-bytes 32 --query 'Plaintext' --output text)
DSSC_SESSION := $$(curl -s -k https://${DSSC_URL}/api/sessions --data "{\"user\":{ \"userID\":\"${DSSC_USER}\",\"password\":\"${DSSC_DEFAULT_PASSWORD}\"}}" -H 'Content-type:application/json')

SSM_URL := $$(aws ssm get-parameter --name /pipeline/example/trendmicro/dssc/url --query "Parameter.Value" --output text)
SSM_USER := $$(aws ssm get-parameter --name /pipeline/example/trendmicro/dssc/username --query "Parameter.Value" --output text)
SSM_PASSWORD := $$(aws ssm get-parameter --name /pipeline/example/trendmicro/dssc/password --query "Parameter.Value" --output text)

TOKEN := $$(curl -s -k ${SSM_URL}/api/sessions --data "{\"user\":{ \"userID\":\"${SSM_USER}\",\"password\":\"${SSM_PASSWORD}\"}}" -H 'Content-type:application/json' | jq -r '.token')

deploy-cluster:
	@echo "=== Creating EKS Cluster ${STACK_NAME} ==="
	eksctl create cluster --name ${STACK_NAME} --region ${REGION}
	aws eks update-kubeconfig --name ${STACK_NAME} --region ${REGION}

deploy-dssc:
	@echo "=== Installing Trend Micro Deep Security Smart Check ==="
	helm install --values ./dssc/overrides.yaml \
		deepsecurity-smartcheck https://github.com/deep-security/smartcheck-helm/archive/1.2.45.tar.gz
	sleep 10s

	@echo "=== Storing DSSC Variables in SSM ==="
	aws cloudformation deploy \
		--stack-name ${DSSC_SSM_STACK_NAME} \
		--no-fail-on-empty-changeset \
		--template-file ./cloudformation/dssc_ssm.yaml \
		--capabilities CAPABILITY_NAMED_IAM \
		--region ${REGION} \
		--parameter-overrides DeepSecuritySmartCheckURL=https://${DSSC_URL} \
			DeepSecuritySmartCheckUser=${DSSC_USER} \
			DeepSecuritySmartCheckPassword=${DSSC_NEW_PASSWORD} \
			DeepSecuritySmartCheckSecret=${DSSC_SECRET}

	@echo "=== Waiting for ${SSM_URL} to become available ==="
	@while [ $$(curl -w "%{http_code}" -k ${SSM_URL} -o /dev/null -s) -ne 200 ]; do echo ".\c"; sleep 10s; done;
	@echo ""

	@echo "=== Changing DSSC Password ==="
	@USER_INFO=${DSSC_SESSION} \
	SESSION_TOKEN=$$(echo $${USER_INFO} | jq -r '.token') \
	USER_ID=$$(echo $${USER_INFO} | jq -r '.user.id'); \
	curl -k -H "Authorization:Bearer $${SESSION_TOKEN}" ${SSM_URL}/api/users/$${USER_ID}/password --data "{\"oldPassword\":\"${DSSC_DEFAULT_PASSWORD}\", \"newPassword\":\"${SSM_PASSWORD}\"}" -H 'Content-type: application/json'

deploy-ecr:
	@echo "=== Creating stack ${ECR_STACK_NAME} ==="
	aws cloudformation deploy \
	--stack-name ${ECR_STACK_NAME} \
	--no-fail-on-empty-changeset \
	--template-file ./cloudformation/ecr.yaml \
	--capabilities CAPABILITY_NAMED_IAM \
	--region ${REGION}

build-and-push-docker-image:
	@echo "=== Building and pushing sample image to ${ECR_REPOSITORY_IMAGE_URI} ==="
	$$(aws ecr get-login --no-include-email --region us-east-1)
	docker build -t ${ECR_REPOSITORY_IMAGE_URI}:latest ./sample_app/
	docker push ${ECR_REPOSITORY_IMAGE_URI}:latest

deploy-webhook:
	@echo "=== Creating stack ${WEBHOOK_STACK_NAME} ==="
	aws cloudformation deploy \
		--stack-name ${WEBHOOK_STACK_NAME} \
		--no-fail-on-empty-changeset \
		--template-file ./cloudformation/webhook.yaml \
		--capabilities CAPABILITY_NAMED_IAM \
		--region ${REGION} \
		--parameter-overrides PipelineName=${PIPELINE_STACK_NAME}

deploy-pipeline:
	@echo "=== Creating stack ${PIPELINE_STACK_NAME} ==="
	aws cloudformation deploy \
		--stack-name ${PIPELINE_STACK_NAME} \
		--no-fail-on-empty-changeset \
		--template-file ./cloudformation/pipeline.yaml \
		--capabilities CAPABILITY_NAMED_IAM \
		--region ${REGION} \
		--parameter-overrides RepositoryUri=${ECR_REPOSITORY_IMAGE_URI} \
			TagName=latest

teardown-cluster:
	@echo "=== Tearing down EKS cluster ${STACK_NAME} ==="
	eksctl delete cluster --name ${STACK_NAME} --region ${REGION}

teardown-ecr:
	@echo "=== Tearing down ${ECR_STACK_NAME} ==="
	aws ecr delete-repository --repository-name ${ECR_STACK_NAME} --force --region ${REGION}
	aws cloudformation delete-stack --stack-name ${ECR_STACK_NAME} --region ${REGION}

teardown-dssc-ssm:
	@echo "=== Tearing down stack ${DSSC_SSM_STACK_NAME} ==="
	aws cloudformation delete-stack --stack-name ${DSSC_SSM_STACK_NAME} --region ${REGION}

teardown-webhook:
	@echo "=== Tearing down stack ${WEBHOOK_STACK_NAME} ==="
	aws cloudformation delete-stack --stack-name ${WEBHOOK_STACK_NAME} --region ${REGION}

teardown-pipeline:
	@echo "=== Tearing down stack ${PIPELINE_STACK_NAME} ==="
	./scripts/delete_all_object_versions.sh ${ARTIFACT_BUCKET_NAME}
	aws s3 rm s3://${ARTIFACT_BUCKET_NAME} --recursive
	aws cloudformation delete-stack --stack-name ${PIPELINE_STACK_NAME} --region ${REGION}

adjust-error-tolerance:
	@echo "=== Adjusting Webhook Lambda Error Tolerance ==="
	@aws lambda update-function-configuration --function-name ${WEBHOOK_STACK_NAME} \
		--region ${REGION} \
		--environment Variables="{CRITICAL_ERRORS_THRESHOLD=100,DSSC_SECRET_SSM=/pipeline/example/trendmicro/dssc/secret}"

add-eicar-test-malware:
	cp ./eicar/eicar_test_file.com ./sample_app/src/eicar.com

retrigger-pipeline:
	@echo "=== Retrigging Pipeline ${PIPELINE_STACK_NAME} ==="
	@aws codepipeline start-pipeline-execution --name ${PIPELINE_STACK_NAME} \
		--region ${REGION}

get-pipeline-status:
	@echo "=== Getting ${PIPELINE_STACK_NAME} Status ==="
	@aws codepipeline get-pipeline-state --name ${PIPELINE_STACK_NAME} \
		--query "stageStates[][stageName,latestExecution.status]" \
		--output table \
		--region ${REGION}

get-pipeline-stage-result:
	@echo "=== Getting ${PIPELINE_STACK_NAME} stage 'ApproveDeployment' Summary ==="
	@aws codepipeline list-action-executions --pipeline-name trend-mirco-dssc-pipeline \
		--filter pipelineExecutionId=${PIPELINE_EXECUTION_ID} \
		--query "actionExecutionDetails[?stageName=='ApproveDeployment'][output.executionResult.externalExecutionSummary]" \
		--output text \
		--region ${REGION}

get-scan-status:
	@echo "=== Getting DSSC Scan Status ==="
	@RESOLVED_TOKEN=${TOKEN} \
	RESOLVED_PIPELINE_EXECUTION_ID=${PIPELINE_EXECUTION_ID}; \
	curl -s -k ${SSM_URL}/api/scans -H "Authorization:Bearer $${RESOLVED_TOKEN}" | jq -r ".scans[] | select(.context.pipeline_execution_id==\"$${RESOLVED_PIPELINE_EXECUTION_ID}\") | \"\(.id): \(.status)\""

get-scan-results:
	@echo "=== Getting DSSC Scan Results ==="
	@RESOLVED_TOKEN=${TOKEN} \
	RESOLVED_PIPELINE_EXECUTION_ID=${PIPELINE_EXECUTION_ID}; \
	curl -s -k ${SSM_URL}/api/scans -H "Authorization:Bearer $${RESOLVED_TOKEN}" | jq -r ".scans[] | select(.context.pipeline_execution_id==\"$${RESOLVED_PIPELINE_EXECUTION_ID}\")"

teardown: teardown-pipeline teardown-webhook teardown-dssc-ssm teardown-ecr teardown-cluster

deploy: deploy-cluster deploy-dssc deploy-ecr build-and-push-docker-image deploy-webhook deploy-pipeline
