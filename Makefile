.PHONY: help build format lint test test-unit

help:
	@echo "[Usage] available commands:"
	@echo " * make install ... install required packages and create a requirements.txt"
	@echo " * make install-dev ... install packages reuired for development"
	@echo " * make deploy ... deploy the function to a GCP project"
	@echo " * make format ... format python code"
	@echo " * make lint ... lint python code"
	@echo " * make test ... test python code"
	@echo " * make run-debug ... run locally using functions-framework"

install:
	pipenv install
	pipenv lock -r > requirements.txt

install-dev:
	ln -fs .development.env .env
	pipenv install --dev

deploy:
	./scripts/deploy.sh

format:
	pipenv run black .
	pipenv run isort .

lint:
	pipenv run ./scripts/run_lint.sh

test:
	pipenv run ./scripts/run_tests.sh

run-debug:
	pipenv run functions-framework --target=notify --debug