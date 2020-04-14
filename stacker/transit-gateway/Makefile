SHELL = /bin/bash
install:
	pipenv sync

test: install
	pipenv run runway test

deploy: deploy-shared deploy-dev deploy-prod

deploy-shared:
	@pushd ./runway && \
	DEPLOY_ENVIRONMENT=shared pipenv run runway deploy && \
	popd

deploy-dev:
	@pushd ./runway && \
	DEPLOY_ENVIRONMENT=dev pipenv run runway deploy && \
	popd

deploy-prod:
	@pushd ./runway && \
	DEPLOY_ENVIRONMENT=prod pipenv run runway deploy && \
	popd

plan: plan-shared plan-dev plan-prod

plan-shared:
	@pushd ./runway && \
	DEPLOY_ENVIRONMENT=shared pipenv run runway plan && \
	popd

plan-dev:
	@pushd ./runway && \
	DEPLOY_ENVIRONMENT=dev pipenv run runway plan && \
	popd

plan-prod:
	@pushd ./runway && \
	DEPLOY_ENVIRONMENT=prod pipenv run runway plan && \
	popd
