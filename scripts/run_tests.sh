#!/bin/bash
#
# Run all project tests
#

set -o pipefail

echo "Running unit tests"

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

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

pytest --cov=main --cov-report html --cov-fail-under=100 "$@"
display_result $? 3 "Unit tests"