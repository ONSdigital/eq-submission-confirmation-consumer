.PHONY: help build format lint test test-unit

help:
	@echo "[Usage] available commands:"
	@echo " * make install ... install required packages"
	@echo " * make build ... install required packages and create a requirements.txt"
	@echo " * make deploy ... deploy the function to a GCP project"
	@echo " * make format ... format python code"
	@echo " * make lint ... lint python code"
	@echo " * make test ... test python code"
	@echo " * make test-unit ... run unit tests"
	@echo " * make run-debug ... run locally using functions-framework"

install:
	pipenv install --dev

build: install
	ln -fs .development.env .env
	pipenv lock -r > requirements.txt

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