.PHONY: help build format lint test test-unit

help:
	@echo "[Usage] available commands:"
	@echo " * make install ... install required packages and create a requirements.txt"
	@echo " * make install-dev ... install packages required for development"
	@echo " * make deploy ... deploy the function to a GCP project"
	@echo " * make format ... format python code"
	@echo " * make lint ... lint python code"
	@echo " * make test ... test python code"
	@echo " * make run-debug ... run locally using functions-framework"

install:
	poetry install
	poetry export --without-hashes --format=requirements.txt > requirements.txt

install-dev:
	poetry install

deploy_function: install
	./scripts/deploy_function.sh

delete_function:
	poetry run ./scripts/delete_function.sh

format:
	poetry run black . tests
	poetry run isort . tests

lint:
	poetry run ./scripts/run_lint.sh

test:
	NOTIFY_API_KEY=$$(cat ./dev-notify-api-key) poetry run ./scripts/run_tests.sh


run-debug:
	poetry run functions-framework --target=send_email --debug
