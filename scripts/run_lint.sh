#!/bin/bash
#
# Run project through linting
#
# NOTE: This script expects to be run from the project root with
# ./scripts/run_lint.sh

function display_result {
  RESULT=$1
  EXIT_STATUS=$2
  TEST=$3

  if [ $RESULT -ne 0 ]; then
    echo -e "\033[31m$TEST failed\033[0m"
    exit $EXIT_STATUS
  else
    echo -e "\033[32m$TEST passed\033[0m"
  fi
}

flake8 --max-complexity 10 --count --ignore=C901,W503
display_result $? 1 "Flake 8 code style check"

pylint --reports=n --output-format=colorized --rcfile=.pylintrc -j 0 *.py tests/
display_result $? 2 "Pylint linting check"

isort --check . tests/
display_result $? 1 "isort linting check"

./scripts/run_mypy.sh
display_result $? 1 "Mypy type check"

black --check . tests/
display_result $? 1 "Python code formatting check"